from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import pandas as pd

from web_app.core.security import get_current_user, require_permission, require_admin
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


# Pydantic models
class QueryRequest(BaseModel):
    query: str
    params: Optional[List] = None


class TableInfo(BaseModel):
    name: str
    columns: List[Dict[str, Any]]


class TradeRecord(BaseModel):
    symbol: str
    side: str
    size: float
    price: float
    timestamp: str
    market: str = "paper_trading"


# Database info endpoints

@router.get("/info")
async def get_database_info(
    current_user: Dict[str, Any] = Depends(require_permission("read")),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get database information"""
    try:
        databases = {}
        
        for db_name in db.databases:
            tables = await db.get_tables(db_name)
            databases[db_name] = {
                "path": db.databases[db_name],
                "tables": tables,
                "table_count": len(tables)
            }
        
        return {
            "databases": databases,
            "total_databases": len(db.databases),
            "is_connected": db.is_connected()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/tables/{db_name}")
async def get_tables(
    db_name: str,
    current_user: Dict[str, Any] = Depends(require_permission("read")),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get tables in database"""
    try:
        tables = await db.get_tables(db_name)
        
        table_info = []
        for table_name in tables:
            columns = await db.get_table_info(db_name, table_name)
            table_info.append({
                "name": table_name,
                "columns": columns
            })
        
        return {
            "database": db_name,
            "tables": table_info
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/table/{db_name}/{table_name}")
async def get_table_info(
    db_name: str,
    table_name: str,
    current_user: Dict[str, Any] = Depends(require_permission("read")),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get table information"""
    try:
        if not await db.table_exists(db_name, table_name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Table {table_name} not found in database {db_name}"
            )
        
        columns = await db.get_table_info(db_name, table_name)
        
        # Get row count
        count_query = f"SELECT COUNT(*) as count FROM `{table_name}`"
        count_result = await db.execute_query(db_name, count_query)
        row_count = count_result[0]["count"] if count_result else 0
        
        return {
            "database": db_name,
            "table": table_name,
            "columns": columns,
            "row_count": row_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Data query endpoints

@router.post("/query/{db_name}")
async def execute_query(
    db_name: str,
    query_request: QueryRequest,
    current_user: Dict[str, Any] = Depends(require_permission("read")),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Execute SQL query"""
    try:
        # Security check: only allow SELECT queries for read permission
        query_upper = query_request.query.upper().strip()
        if not query_upper.startswith("SELECT"):
            if not require_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only SELECT queries allowed for non-admin users"
                )
        
        if query_upper.startswith(("DROP", "DELETE", "TRUNCATE")):
            # Extra security for destructive operations
            if current_user.get("role") != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin privileges required for destructive operations"
                )
        
        params = tuple(query_request.params) if query_request.params else None
        
        if query_upper.startswith("SELECT"):
            results = await db.execute_query(db_name, query_request.query, params)
        else:
            rows_affected = await db.execute_update(db_name, query_request.query, params)
            results = {"rows_affected": rows_affected}
        
        return {
            "query": query_request.query,
            "results": results,
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Query execution failed: {str(e)}"
        )


@router.get("/data/{db_name}/{table_name}")
async def get_table_data(
    db_name: str,
    table_name: str,
    limit: int = Query(default=100, le=10000),
    offset: int = Query(default=0, ge=0),
    order_by: Optional[str] = Query(default=None),
    where: Optional[str] = Query(default=None),
    current_user: Dict[str, Any] = Depends(require_permission("read")),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get table data with pagination"""
    try:
        if not await db.table_exists(db_name, table_name):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Table {table_name} not found"
            )
        
        # Build query
        query = f"SELECT * FROM `{table_name}`"
        
        if where:
            query += f" WHERE {where}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        query += f" LIMIT {limit} OFFSET {offset}"
        
        results = await db.execute_query(db_name, query)
        
        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM `{table_name}`"
        if where:
            count_query += f" WHERE {where}"
        
        count_result = await db.execute_query(db_name, count_query)
        total_count = count_result[0]["count"] if count_result else 0
        
        return {
            "data": results,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total_count,
                "has_next": offset + limit < total_count,
                "has_prev": offset > 0
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Trading data endpoints

@router.get("/trading-data/{market}/{data_type}")
async def get_trading_data(
    market: str,
    data_type: str,
    symbol: Optional[str] = Query(default=None),
    limit: int = Query(default=1000, le=10000),
    current_user: Dict[str, Any] = Depends(require_permission("read")),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get trading data (tick/minute data)"""
    try:
        df = await db.get_trading_data(market, data_type, symbol, limit)
        
        if symbol and df.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data found for {symbol}"
            )
        
        # Convert DataFrame to dict for JSON response
        if 'tables' in df.columns:
            # List of available symbols
            return {"symbols": df['tables'].tolist()}
        else:
            # Actual trading data
            return {
                "symbol": symbol,
                "market": market,
                "data_type": data_type,
                "data": df.to_dict('records'),
                "count": len(df)
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/trades")
async def get_trade_history(
    market: Optional[str] = Query(default=None),
    limit: int = Query(default=1000, le=10000),
    current_user: Dict[str, Any] = Depends(require_permission("read")),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get trade history"""
    try:
        trades = await db.get_trade_history(market, limit)
        
        return {
            "trades": trades,
            "count": len(trades),
            "market_filter": market
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/trades")
async def save_trade(
    trade: TradeRecord,
    current_user: Dict[str, Any] = Depends(require_permission("trade")),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Save trade record"""
    try:
        trade_data = {
            '체결시간': trade.timestamp,
            '종목코드': trade.symbol,
            '매수매도구분': trade.side,
            '체결수량': trade.size,
            '체결가격': trade.price,
            '체결금액': trade.size * trade.price,
            '시장구분': trade.market
        }
        
        success = await db.save_trade(trade_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save trade"
            )
        
        return {"message": "Trade saved successfully", "trade": trade_data}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Settings endpoints

@router.get("/settings")
async def get_settings(
    current_user: Dict[str, Any] = Depends(require_permission("read")),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get system settings"""
    try:
        settings = await db.get_settings()
        return {"settings": settings}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/settings/{table}/{index}/{column}")
async def update_setting(
    table: str,
    index: str,
    column: str,
    value: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(require_admin),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Update specific setting (admin only)"""
    try:
        setting_value = value.get("value")
        if setting_value is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Value is required"
            )
        
        success = await db.update_setting(table, index, column, setting_value)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Setting not found or update failed"
            )
        
        return {
            "message": "Setting updated successfully",
            "table": table,
            "index": index,
            "column": column,
            "value": setting_value
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Database maintenance endpoints

@router.post("/optimize/{db_name}")
async def optimize_database(
    db_name: str,
    current_user: Dict[str, Any] = Depends(require_admin),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Optimize database (admin only)"""
    try:
        success = await db.optimize_database(db_name)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database optimization failed"
            )
        
        return {"message": f"Database {db_name} optimized successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/backup/{db_name}")
async def backup_database(
    db_name: str,
    backup_path: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(require_admin),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Backup database (admin only)"""
    try:
        if not backup_path:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"./_database/backup/{db_name}_{timestamp}.db"
        
        success = await db.backup_database(db_name, backup_path)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database backup failed"
            )
        
        return {
            "message": f"Database {db_name} backed up successfully",
            "backup_path": backup_path
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Inject database manager instance
def set_db_manager(manager: DatabaseManager):
    """Set database manager instance"""
    global db_manager
    db_manager = manager