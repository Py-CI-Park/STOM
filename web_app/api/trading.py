from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

from web_app.core.security import get_current_user, require_permission
from web_app.services.trading_service import TradingService

router = APIRouter()

# This will be injected via dependency
trading_service: Optional[TradingService] = None


def get_trading_service() -> TradingService:
    """Get trading service instance"""
    global trading_service
    if trading_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Trading service not available"
        )
    return trading_service


# Pydantic models
class OrderRequest(BaseModel):
    symbol: str
    side: str  # 'buy' or 'sell'
    order_type: str  # 'market', 'limit', 'stop'
    size: float
    price: Optional[float] = None


class OrderResponse(BaseModel):
    success: bool
    order_id: Optional[str] = None
    order: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class Position(BaseModel):
    symbol: str
    side: str
    size: float
    entry_price: float
    unrealized_pnl: float
    timestamp: str


class Order(BaseModel):
    id: str
    symbol: str
    side: str
    type: str
    size: float
    price: Optional[float]
    status: str
    filled_size: float
    filled_price: float
    timestamp: str


class PortfolioSummary(BaseModel):
    total_positions: int
    total_orders: int
    total_value: float
    total_pnl: float
    daily_pnl: float


class MarketDataUpdate(BaseModel):
    symbol: str
    price: float
    volume: Optional[float] = None
    timestamp: Optional[str] = None


# Trading endpoints

@router.post("/orders", response_model=OrderResponse)
async def place_order(
    order_request: OrderRequest,
    current_user: Dict[str, Any] = Depends(require_permission("trade")),
    service: TradingService = Depends(get_trading_service)
):
    """Place a trading order"""
    try:
        result = await service.place_order(
            symbol=order_request.symbol,
            side=order_request.side,
            order_type=order_request.order_type,
            size=order_request.size,
            price=order_request.price
        )
        
        return OrderResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/orders/{order_id}")
async def cancel_order(
    order_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("trade")),
    service: TradingService = Depends(get_trading_service)
):
    """Cancel a pending order"""
    try:
        result = await service.cancel_order(order_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/orders", response_model=List[Order])
async def get_orders(
    current_user: Dict[str, Any] = Depends(require_permission("read")),
    service: TradingService = Depends(get_trading_service)
):
    """Get all orders"""
    try:
        orders = service.get_orders()
        return [Order(**order) for order in orders]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/orders/{order_id}", response_model=Order)
async def get_order(
    order_id: str,
    current_user: Dict[str, Any] = Depends(require_permission("read")),
    service: TradingService = Depends(get_trading_service)
):
    """Get specific order"""
    try:
        orders = service.get_orders()
        order = next((o for o in orders if o["id"] == order_id), None)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        return Order(**order)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Position endpoints

@router.get("/positions", response_model=List[Position])
async def get_positions(
    current_user: Dict[str, Any] = Depends(require_permission("read")),
    service: TradingService = Depends(get_trading_service)
):
    """Get all positions"""
    try:
        positions = service.get_positions()
        return [Position(**position) for position in positions]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/positions/{symbol}", response_model=Position)
async def get_position(
    symbol: str,
    current_user: Dict[str, Any] = Depends(require_permission("read")),
    service: TradingService = Depends(get_trading_service)
):
    """Get position for specific symbol"""
    try:
        positions = service.get_positions()
        position = next((p for p in positions if p["symbol"] == symbol), None)
        
        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Position not found"
            )
        
        return Position(**position)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/positions/{symbol}")
async def close_position(
    symbol: str,
    current_user: Dict[str, Any] = Depends(require_permission("trade")),
    service: TradingService = Depends(get_trading_service)
):
    """Close position for specific symbol"""
    try:
        result = await service.close_position(symbol)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Portfolio endpoints

@router.get("/portfolio/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    current_user: Dict[str, Any] = Depends(require_permission("read")),
    service: TradingService = Depends(get_trading_service)
):
    """Get portfolio summary"""
    try:
        summary = await service.get_portfolio_summary()
        return PortfolioSummary(**summary)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/portfolio/pnl")
async def get_portfolio_pnl(
    current_user: Dict[str, Any] = Depends(require_permission("read")),
    service: TradingService = Depends(get_trading_service)
):
    """Get portfolio P&L breakdown"""
    try:
        total_pnl = service.get_total_pnl()
        positions = service.get_positions()
        
        pnl_breakdown = []
        for position in positions:
            pnl_breakdown.append({
                "symbol": position["symbol"],
                "unrealized_pnl": position["unrealized_pnl"],
                "realized_pnl": position.get("realized_pnl", 0.0)
            })
        
        return {
            "total_unrealized_pnl": total_pnl,
            "daily_pnl": service.daily_pnl,
            "breakdown": pnl_breakdown
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Market data endpoints

@router.get("/market-data/{symbol}")
async def get_market_data(
    symbol: str,
    current_user: Dict[str, Any] = Depends(require_permission("read")),
    service: TradingService = Depends(get_trading_service)
):
    """Get current market data for symbol"""
    try:
        current_price = await service.get_current_price(symbol)
        market_data = service.market_data.get(symbol, {})
        
        if current_price is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Market data not available for symbol"
            )
        
        return {
            "symbol": symbol,
            "price": current_price,
            "data": market_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/market-data/{symbol}")
async def update_market_data(
    symbol: str,
    market_data: MarketDataUpdate,
    current_user: Dict[str, Any] = Depends(require_permission("admin")),
    service: TradingService = Depends(get_trading_service)
):
    """Update market data for symbol (admin only)"""
    try:
        data = {
            "price": market_data.price,
            "volume": market_data.volume,
            "timestamp": market_data.timestamp or datetime.now().isoformat()
        }
        
        await service.update_market_data(symbol, data)
        
        return {"message": f"Market data updated for {symbol}"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Trading system control

@router.get("/system/status")
async def get_system_status(
    current_user: Dict[str, Any] = Depends(require_permission("read")),
    service: TradingService = Depends(get_trading_service)
):
    """Get trading system status"""
    try:
        return await service.get_system_status()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/system/enable-live-trading")
async def enable_live_trading(
    current_user: Dict[str, Any] = Depends(require_permission("admin")),
    service: TradingService = Depends(get_trading_service)
):
    """Enable live trading (admin only)"""
    try:
        service.is_live_trading = True
        return {"message": "Live trading enabled"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/system/disable-live-trading")
async def disable_live_trading(
    current_user: Dict[str, Any] = Depends(require_permission("admin")),
    service: TradingService = Depends(get_trading_service)
):
    """Disable live trading (admin only)"""
    try:
        service.is_live_trading = False
        return {"message": "Live trading disabled - switched to paper trading"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/system/reset-daily-pnl")
async def reset_daily_pnl(
    current_user: Dict[str, Any] = Depends(require_permission("admin")),
    service: TradingService = Depends(get_trading_service)
):
    """Reset daily P&L counter (admin only)"""
    try:
        service.daily_pnl = 0.0
        return {"message": "Daily P&L reset to zero"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Risk management

@router.get("/risk/limits")
async def get_risk_limits(
    current_user: Dict[str, Any] = Depends(require_permission("read")),
    service: TradingService = Depends(get_trading_service)
):
    """Get current risk limits"""
    return {
        "max_position_size": service.max_position_size,
        "max_daily_loss": service.max_daily_loss,
        "current_daily_pnl": service.daily_pnl
    }


@router.post("/risk/limits")
async def update_risk_limits(
    limits: Dict[str, float],
    current_user: Dict[str, Any] = Depends(require_permission("admin")),
    service: TradingService = Depends(get_trading_service)
):
    """Update risk limits (admin only)"""
    try:
        if "max_position_size" in limits:
            service.max_position_size = limits["max_position_size"]
        
        if "max_daily_loss" in limits:
            service.max_daily_loss = limits["max_daily_loss"]
        
        return {
            "message": "Risk limits updated",
            "max_position_size": service.max_position_size,
            "max_daily_loss": service.max_daily_loss
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Inject trading service instance
def set_trading_service(service: TradingService):
    """Set trading service instance"""
    global trading_service
    trading_service = service