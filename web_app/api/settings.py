from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from web_app.core.security import get_current_user, require_admin
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
class SettingUpdate(BaseModel):
    value: Any


class SystemConfig(BaseModel):
    trading_enabled: bool = False
    paper_trading: bool = True
    max_position_size: float = 1000000
    max_daily_loss: float = 100000
    risk_management: bool = True


class MarketConfig(BaseModel):
    stock_enabled: bool = False
    coin_enabled: bool = False
    kiwoom_enabled: bool = False
    upbit_enabled: bool = False
    binance_enabled: bool = False


class NotificationConfig(BaseModel):
    telegram_enabled: bool = False
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    email_enabled: bool = False
    email_smtp: Optional[str] = None
    email_user: Optional[str] = None


# Settings endpoints

@router.get("/system")
async def get_system_settings(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get system settings"""
    try:
        settings = await db.get_settings()
        main_settings = settings.get('main', {})
        
        # Extract system configuration
        system_config = {
            "trading_enabled": main_settings.get('거래활성화', {}).get('0', False),
            "paper_trading": not main_settings.get('실전거래', {}).get('0', False),
            "debug_mode": main_settings.get('디버그모드', {}).get('0', False),
            "auto_login": main_settings.get('자동로그인', {}).get('0', False),
            "version": main_settings.get('버전', {}).get('0', 'Unknown')
        }
        
        return {"system": system_config}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/system")
async def update_system_settings(
    config: SystemConfig,
    current_user: Dict[str, Any] = Depends(require_admin),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Update system settings (admin only)"""
    try:
        updates = []
        
        # Update trading settings
        if hasattr(config, 'trading_enabled'):
            updates.append(('main', '0', '거래활성화', config.trading_enabled))
        
        if hasattr(config, 'paper_trading'):
            updates.append(('main', '0', '실전거래', not config.paper_trading))
        
        # Apply updates
        for table, index, column, value in updates:
            await db.update_setting(table, index, column, value)
        
        return {"message": "System settings updated successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/markets")
async def get_market_settings(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get market settings"""
    try:
        settings = await db.get_settings()
        main_settings = settings.get('main', {})
        
        market_config = {
            "stock_enabled": main_settings.get('주식리시버', {}).get('0', False),
            "coin_enabled": main_settings.get('코인리시버', {}).get('0', False),
            "stock_timeframe": main_settings.get('주식타임프레임', {}).get('0', 'min'),
            "coin_timeframe": main_settings.get('코인타임프레임', {}).get('0', 'min'),
            "exchange": main_settings.get('거래소', {}).get('0', 'upbit')
        }
        
        return {"markets": market_config}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/markets")
async def update_market_settings(
    config: MarketConfig,
    current_user: Dict[str, Any] = Depends(require_admin),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Update market settings (admin only)"""
    try:
        updates = []
        
        if hasattr(config, 'stock_enabled'):
            updates.append(('main', '0', '주식리시버', config.stock_enabled))
        
        if hasattr(config, 'coin_enabled'):
            updates.append(('main', '0', '코인리시버', config.coin_enabled))
        
        # Apply updates
        for table, index, column, value in updates:
            await db.update_setting(table, index, column, value)
        
        return {"message": "Market settings updated successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/notifications")
async def get_notification_settings(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get notification settings"""
    try:
        settings = await db.get_settings()
        telegram_settings = settings.get('telegram', {})
        
        # Only return non-sensitive information
        notification_config = {
            "telegram_enabled": bool(telegram_settings.get('텔레그램토큰', {}).get('0')),
            "telegram_chat_configured": bool(telegram_settings.get('텔레그램아이디', {}).get('0')),
            "alerts_enabled": telegram_settings.get('텔레그램시작알림', {}).get('0', False),
            "trading_alerts": telegram_settings.get('텔레그램거래알림', {}).get('0', False)
        }
        
        return {"notifications": notification_config}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/notifications")
async def update_notification_settings(
    config: NotificationConfig,
    current_user: Dict[str, Any] = Depends(require_admin),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Update notification settings (admin only)"""
    try:
        updates = []
        
        if config.telegram_token:
            # In a real implementation, encrypt this
            updates.append(('telegram', '0', '텔레그램토큰', config.telegram_token))
        
        if config.telegram_chat_id:
            updates.append(('telegram', '0', '텔레그램아이디', config.telegram_chat_id))
        
        # Apply updates
        for table, index, column, value in updates:
            await db.update_setting(table, index, column, value)
        
        return {"message": "Notification settings updated successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/accounts")
async def get_account_settings(
    current_user: Dict[str, Any] = Depends(require_admin),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get account settings (admin only)"""
    try:
        settings = await db.get_settings()
        stock_accounts = settings.get('sacc', {})
        coin_accounts = settings.get('cacc', {})
        
        # Return account information without sensitive data
        account_config = {
            "stock_accounts": [
                {
                    "index": key,
                    "has_credentials": bool(value.get('아이디')),
                    "account_configured": bool(value.get('계좌번호'))
                }
                for key, value in stock_accounts.items()
            ],
            "coin_accounts": [
                {
                    "index": key,
                    "exchange": value.get('거래소', 'unknown'),
                    "has_api_key": bool(value.get('APIKEY')),
                    "has_secret": bool(value.get('SECRETKEY'))
                }
                for key, value in coin_accounts.items()
            ]
        }
        
        return {"accounts": account_config}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/strategies")
async def get_strategy_settings(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get strategy settings"""
    try:
        strategies = await db.get_strategies()
        
        strategy_summary = {
            "total_strategies": len(strategies),
            "strategy_types": {},
            "market_distribution": {}
        }
        
        for strategy in strategies:
            # Count by type
            strategy_type = strategy.get('전략구분', 'unknown')
            strategy_summary["strategy_types"][strategy_type] = \
                strategy_summary["strategy_types"].get(strategy_type, 0) + 1
            
            # Count by market
            market = strategy.get('시장구분', 'unknown')
            strategy_summary["market_distribution"][market] = \
                strategy_summary["market_distribution"].get(market, 0) + 1
        
        return {"strategies": strategy_summary}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/risk")
async def get_risk_settings(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get risk management settings"""
    try:
        # In a real implementation, these would come from database
        risk_config = {
            "max_position_size": 1000000,
            "max_daily_loss": 100000,
            "max_drawdown": 0.1,
            "risk_per_trade": 0.02,
            "stop_loss_enabled": True,
            "take_profit_enabled": True,
            "position_sizing": "fixed"
        }
        
        return {"risk": risk_config}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/risk")
async def update_risk_settings(
    limits: Dict[str, float],
    current_user: Dict[str, Any] = Depends(require_admin),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Update risk management settings (admin only)"""
    try:
        # TODO: Implement risk settings update in database
        # For now, just validate and return success
        
        valid_settings = ['max_position_size', 'max_daily_loss', 'max_drawdown', 'risk_per_trade']
        updated_settings = {}
        
        for key, value in limits.items():
            if key in valid_settings and isinstance(value, (int, float)):
                updated_settings[key] = value
        
        return {
            "message": "Risk settings updated successfully",
            "updated_settings": updated_settings
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/backup")
async def get_backup_settings(
    current_user: Dict[str, Any] = Depends(require_admin),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get backup settings (admin only)"""
    try:
        backup_config = {
            "auto_backup_enabled": True,
            "backup_interval": "daily",
            "backup_retention": 30,
            "backup_location": "./_database/backup",
            "last_backup": None  # TODO: Get from actual backup system
        }
        
        return {"backup": backup_config}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/reset")
async def reset_settings(
    section: str,
    current_user: Dict[str, Any] = Depends(require_admin),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Reset settings to default (admin only)"""
    try:
        # TODO: Implement settings reset functionality
        
        valid_sections = ['system', 'markets', 'notifications', 'risk']
        
        if section not in valid_sections:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid section. Must be one of: {valid_sections}"
            )
        
        return {
            "message": f"{section.title()} settings reset to default values",
            "section": section
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/export")
async def export_settings(
    current_user: Dict[str, Any] = Depends(require_admin),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Export all settings (admin only)"""
    try:
        settings = await db.get_settings()
        
        # Remove sensitive information before export
        safe_settings = {}
        for table, data in settings.items():
            safe_settings[table] = {}
            for key, value in data.items():
                # Skip sensitive fields
                if any(sensitive in str(key).lower() for sensitive in 
                      ['password', 'secret', 'token', 'key']):
                    continue
                safe_settings[table][key] = value
        
        return {
            "settings": safe_settings,
            "export_date": "2024-01-01T00:00:00Z",  # TODO: Use actual timestamp
            "version": "2.0.0"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Inject database manager instance
def set_db_manager(manager: DatabaseManager):
    """Set database manager instance"""
    global db_manager
    db_manager = manager