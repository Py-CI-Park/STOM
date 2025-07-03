from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import asyncio
import uuid

from web_app.core.security import get_current_user, require_permission
from web_app.database.db_manager import DatabaseManager

router = APIRouter()

# This will be injected via dependency
db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get database manager instance"""
    global db_manager
    if db_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database manager not available"
        )
    return db_manager


# Global storage for running backtests
running_backtests: Dict[str, Dict[str, Any]] = {}


# Pydantic models
class BacktestRequest(BaseModel):
    strategy_name: str
    market: str = "stock"  # stock or coin
    timeframe: str = "min"  # tick or min
    start_date: date
    end_date: date
    initial_capital: float = 10000000  # 10M KRW
    commission_rate: float = 0.0015
    slippage: float = 0.001
    symbols: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None


class OptimizationRequest(BaseModel):
    strategy_name: str
    market: str = "stock"
    timeframe: str = "min"
    start_date: date
    end_date: date
    optimization_params: Dict[str, Dict[str, Any]]  # param_name: {min, max, step}
    objective: str = "total_return"  # total_return, sharpe_ratio, max_drawdown
    population_size: int = 50
    generations: int = 100


class BacktestResult(BaseModel):
    backtest_id: str
    strategy_name: str
    status: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    created_at: str


class BacktestStatus(BaseModel):
    backtest_id: str
    status: str
    progress: float
    message: str
    created_at: str
    estimated_completion: Optional[str] = None


# Backtesting endpoints

@router.post("/run", response_model=Dict[str, str])
async def run_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_permission("backtest")),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Start a new backtest"""
    try:
        # Generate unique backtest ID
        backtest_id = str(uuid.uuid4())
        
        # Validate strategy exists
        strategies = await db.get_strategies()
        strategy = next((s for s in strategies if s.get('전략명') == request.strategy_name), None)
        
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy '{request.strategy_name}' not found"
            )
        
        # Initialize backtest status
        running_backtests[backtest_id] = {
            "status": "initializing",
            "progress": 0.0,
            "message": "Preparing backtest...",
            "created_at": datetime.now().isoformat(),
            "request": request.dict(),
            "user": current_user["username"]
        }
        
        # Start backtest in background
        background_tasks.add_task(_run_backtest_async, backtest_id, request, db)
        
        return {
            "backtest_id": backtest_id,
            "status": "started",
            "message": "Backtest started successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/status/{backtest_id}", response_model=BacktestStatus)
async def get_backtest_status(
    backtest_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("backtest"))
):
    """Get backtest status"""
    if backtest_id not in running_backtests:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest not found"
        )
    
    backtest_info = running_backtests[backtest_id]
    
    return BacktestStatus(
        backtest_id=backtest_id,
        status=backtest_info["status"],
        progress=backtest_info["progress"],
        message=backtest_info["message"],
        created_at=backtest_info["created_at"],
        estimated_completion=backtest_info.get("estimated_completion")
    )


@router.get("/results/{backtest_id}")
async def get_backtest_results(
    backtest_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("backtest")),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get backtest results"""
    try:
        # Check if backtest is still running
        if backtest_id in running_backtests:
            backtest_info = running_backtests[backtest_id]
            if backtest_info["status"] != "completed":
                return {
                    "backtest_id": backtest_id,
                    "status": backtest_info["status"],
                    "message": "Backtest is still running"
                }
        
        # Get results from database
        results = await db.get_backtest_results(limit=1000)
        backtest_result = next((r for r in results if r.get('백테스트ID') == backtest_id), None)
        
        if not backtest_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backtest results not found"
            )
        
        return {
            "backtest_id": backtest_id,
            "status": "completed",
            "results": backtest_result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/history")
async def get_backtest_history(
    limit: int = 100,
    strategy_name: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(require_permission("backtest")),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get backtest history"""
    try:
        results = await db.get_backtest_results(strategy_name, limit)
        
        return {
            "backtests": results,
            "count": len(results),
            "strategy_filter": strategy_name
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/cancel/{backtest_id}")
async def cancel_backtest(
    backtest_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("backtest"))
):
    """Cancel running backtest"""
    if backtest_id not in running_backtests:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest not found"
        )
    
    backtest_info = running_backtests[backtest_id]
    
    if backtest_info["status"] in ["completed", "failed", "cancelled"]:
        return {"message": f"Backtest already {backtest_info['status']}"}
    
    # Mark as cancelled
    backtest_info["status"] = "cancelled"
    backtest_info["message"] = "Backtest cancelled by user"
    
    return {"message": "Backtest cancellation requested"}


# Optimization endpoints

@router.post("/optimize")
async def run_optimization(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_permission("backtest")),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Start strategy optimization"""
    try:
        # Generate unique optimization ID
        optimization_id = str(uuid.uuid4())
        
        # Validate strategy exists
        strategies = await db.get_strategies()
        strategy = next((s for s in strategies if s.get('전략명') == request.strategy_name), None)
        
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy '{request.strategy_name}' not found"
            )
        
        # Initialize optimization status
        running_backtests[optimization_id] = {
            "status": "initializing",
            "progress": 0.0,
            "message": "Preparing optimization...",
            "created_at": datetime.now().isoformat(),
            "request": request.dict(),
            "user": current_user["username"],
            "type": "optimization"
        }
        
        # Start optimization in background
        background_tasks.add_task(_run_optimization_async, optimization_id, request, db)
        
        return {
            "optimization_id": optimization_id,
            "status": "started",
            "message": "Optimization started successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/optimize/results/{optimization_id}")
async def get_optimization_results(
    optimization_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("backtest"))
):
    """Get optimization results"""
    if optimization_id not in running_backtests:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Optimization not found"
        )
    
    optimization_info = running_backtests[optimization_id]
    
    return {
        "optimization_id": optimization_id,
        "status": optimization_info["status"],
        "progress": optimization_info["progress"],
        "message": optimization_info["message"],
        "results": optimization_info.get("results", [])
    }


# Strategy management endpoints

@router.get("/strategies")
async def get_strategies(
    current_user: Dict[str, Any] = Depends(require_permission("read")),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get available strategies"""
    try:
        strategies = await db.get_strategies()
        
        strategy_list = []
        for strategy in strategies:
            strategy_list.append({
                "name": strategy.get('전략명', 'Unknown'),
                "type": strategy.get('전략구분', 'Unknown'),
                "market": strategy.get('시장구분', 'Unknown'),
                "timeframe": strategy.get('타임프레임', 'Unknown'),
                "description": strategy.get('설명', ''),
                "created_at": strategy.get('생성일시', '')
            })
        
        return {
            "strategies": strategy_list,
            "count": len(strategy_list)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/strategies/{strategy_name}")
async def get_strategy_details(
    strategy_name: str,
    current_user: Dict[str, Any] = Depends(require_permission("read")),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get strategy details"""
    try:
        strategies = await db.get_strategies()
        strategy = next((s for s in strategies if s.get('전략명') == strategy_name), None)
        
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy '{strategy_name}' not found"
            )
        
        return {"strategy": strategy}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Data endpoints

@router.get("/data/symbols/{market}")
async def get_available_symbols(
    market: str,
    timeframe: str = "min",
    current_user: Dict[str, Any] = Depends(require_permission("read")),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get available symbols for backtesting"""
    try:
        # Get trading data to find available symbols
        df = await db.get_trading_data(market, timeframe)
        
        if 'tables' in df.columns:
            symbols = df['tables'].tolist()
        else:
            symbols = []
        
        return {
            "market": market,
            "timeframe": timeframe,
            "symbols": symbols,
            "count": len(symbols)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/data/range/{market}/{symbol}")
async def get_data_range(
    market: str,
    symbol: str,
    timeframe: str = "min",
    current_user: Dict[str, Any] = Depends(require_permission("read")),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get available data range for symbol"""
    try:
        # Get sample data to determine range
        df = await db.get_trading_data(market, timeframe, symbol, limit=1000)
        
        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for {symbol}"
            )
        
        # Assume index contains timestamp information
        first_date = df.index.min() if hasattr(df.index, 'min') else None
        last_date = df.index.max() if hasattr(df.index, 'max') else None
        
        return {
            "symbol": symbol,
            "market": market,
            "timeframe": timeframe,
            "first_date": str(first_date) if first_date else None,
            "last_date": str(last_date) if last_date else None,
            "total_records": len(df)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Background task functions

async def _run_backtest_async(backtest_id: str, request: BacktestRequest, db: DatabaseManager):
    """Run backtest in background"""
    try:
        backtest_info = running_backtests[backtest_id]
        
        # Update status
        backtest_info["status"] = "running"
        backtest_info["message"] = "Loading data..."
        backtest_info["progress"] = 10.0
        
        # Simulate backtest execution
        await asyncio.sleep(2)
        
        backtest_info["message"] = "Running strategy..."
        backtest_info["progress"] = 50.0
        
        await asyncio.sleep(3)
        
        backtest_info["message"] = "Calculating results..."
        backtest_info["progress"] = 80.0
        
        await asyncio.sleep(1)
        
        # Generate mock results
        results = {
            "백테스트ID": backtest_id,
            "전략명": request.strategy_name,
            "시작일": request.start_date.isoformat(),
            "종료일": request.end_date.isoformat(),
            "초기자본": request.initial_capital,
            "최종자본": request.initial_capital * 1.15,  # 15% return
            "총수익률": 15.0,
            "최대낙폭": -5.2,
            "샤프비율": 1.8,
            "승률": 68.5,
            "총거래횟수": 142,
            "생성일시": datetime.now().isoformat()
        }
        
        # Save results to database
        await db.save_backtest_result(results)
        
        # Update final status
        backtest_info["status"] = "completed"
        backtest_info["message"] = "Backtest completed successfully"
        backtest_info["progress"] = 100.0
        backtest_info["results"] = results
        
    except Exception as e:
        backtest_info["status"] = "failed"
        backtest_info["message"] = f"Backtest failed: {str(e)}"
        backtest_info["progress"] = 0.0


async def _run_optimization_async(optimization_id: str, request: OptimizationRequest, db: DatabaseManager):
    """Run optimization in background"""
    try:
        optimization_info = running_backtests[optimization_id]
        
        # Update status
        optimization_info["status"] = "running"
        optimization_info["message"] = "Initializing genetic algorithm..."
        optimization_info["progress"] = 5.0
        
        # Simulate optimization
        results = []
        
        for generation in range(request.generations):
            if optimization_info["status"] == "cancelled":
                break
            
            # Simulate generation
            await asyncio.sleep(0.1)
            
            # Update progress
            progress = 5.0 + (generation / request.generations) * 90.0
            optimization_info["progress"] = progress
            optimization_info["message"] = f"Generation {generation + 1}/{request.generations}"
            
            # Add mock result
            if generation % 10 == 0:
                results.append({
                    "generation": generation,
                    "best_fitness": 15.0 + generation * 0.1,
                    "parameters": {param: 1.0 for param in request.optimization_params.keys()}
                })
        
        if optimization_info["status"] != "cancelled":
            # Final results
            optimization_info["status"] = "completed"
            optimization_info["message"] = "Optimization completed successfully"
            optimization_info["progress"] = 100.0
            optimization_info["results"] = results
        
    except Exception as e:
        optimization_info["status"] = "failed"
        optimization_info["message"] = f"Optimization failed: {str(e)}"
        optimization_info["progress"] = 0.0


# Inject database manager instance
def set_db_manager(manager: DatabaseManager):
    """Set database manager instance"""
    global db_manager
    db_manager = manager