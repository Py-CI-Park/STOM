import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd

from web_app.database.db_manager import DatabaseManager
from web_app.services.websocket_manager import WebSocketManager
from utility.setting import DICT_SET

logger = logging.getLogger(__name__)


class Position:
    """Represents a trading position"""
    
    def __init__(self, symbol: str, side: str, size: float, entry_price: float, 
                 timestamp: datetime = None):
        self.symbol = symbol
        self.side = side  # 'long' or 'short'
        self.size = size
        self.entry_price = entry_price
        self.timestamp = timestamp or datetime.now()
        self.unrealized_pnl = 0.0
        self.realized_pnl = 0.0
    
    def update_unrealized_pnl(self, current_price: float):
        """Update unrealized P&L based on current price"""
        if self.side == 'long':
            self.unrealized_pnl = (current_price - self.entry_price) * self.size
        else:
            self.unrealized_pnl = (self.entry_price - current_price) * self.size
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary"""
        return {
            'symbol': self.symbol,
            'side': self.side,
            'size': self.size,
            'entry_price': self.entry_price,
            'timestamp': self.timestamp.isoformat(),
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl
        }


class Order:
    """Represents a trading order"""
    
    def __init__(self, symbol: str, side: str, order_type: str, size: float, 
                 price: Optional[float] = None, timestamp: datetime = None):
        self.id = f"order_{datetime.now().timestamp()}"
        self.symbol = symbol
        self.side = side  # 'buy' or 'sell'
        self.type = order_type  # 'market', 'limit', 'stop'
        self.size = size
        self.price = price
        self.status = 'pending'  # 'pending', 'filled', 'cancelled', 'rejected'
        self.filled_size = 0.0
        self.filled_price = 0.0
        self.timestamp = timestamp or datetime.now()
        self.fill_timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert order to dictionary"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side,
            'type': self.type,
            'size': self.size,
            'price': self.price,
            'status': self.status,
            'filled_size': self.filled_size,
            'filled_price': self.filled_price,
            'timestamp': self.timestamp.isoformat(),
            'fill_timestamp': self.fill_timestamp.isoformat() if self.fill_timestamp else None
        }


class TradingService:
    """Core trading service that manages positions, orders, and market data"""
    
    def __init__(self, db_manager: DatabaseManager, websocket_manager: Optional[WebSocketManager] = None):
        self.db_manager = db_manager
        self.websocket_manager = websocket_manager
        
        # Trading state
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, Order] = {}
        self.market_data: Dict[str, Dict[str, Any]] = {}
        
        # Configuration
        self.settings = DICT_SET.copy()
        self.is_live_trading = False
        self.is_running = False
        
        # Risk management
        self.max_position_size = 1000000  # Max position size
        self.max_daily_loss = 100000      # Max daily loss
        self.daily_pnl = 0.0
        
        # Background tasks
        self.market_data_task: Optional[asyncio.Task] = None
        self.position_update_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """Initialize trading service"""
        try:
            # Load settings from database
            await self._load_settings()
            
            # Load existing positions
            await self._load_positions()
            
            # Load pending orders
            await self._load_orders()
            
            # Start background tasks
            await self._start_background_tasks()
            
            self.is_running = True
            logger.info("Trading service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize trading service: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown trading service"""
        self.is_running = False
        
        # Cancel background tasks
        if self.market_data_task:
            self.market_data_task.cancel()
        if self.position_update_task:
            self.position_update_task.cancel()
        
        # Save current state
        await self._save_positions()
        await self._save_orders()
        
        logger.info("Trading service shutdown complete")
    
    async def _load_settings(self):
        """Load settings from database"""
        try:
            settings = await self.db_manager.get_settings()
            if settings:
                # Update trading configuration based on database settings
                main_settings = settings.get('main', {})
                if main_settings:
                    self.is_live_trading = False  # Always start in paper trading mode
                    
        except Exception as e:
            logger.warning(f"Could not load settings: {e}")
    
    async def _load_positions(self):
        """Load existing positions from database"""
        try:
            # TODO: Load positions from database
            pass
        except Exception as e:
            logger.warning(f"Could not load positions: {e}")
    
    async def _load_orders(self):
        """Load pending orders from database"""
        try:
            # TODO: Load orders from database
            pass
        except Exception as e:
            logger.warning(f"Could not load orders: {e}")
    
    async def _save_positions(self):
        """Save current positions to database"""
        try:
            # TODO: Save positions to database
            pass
        except Exception as e:
            logger.error(f"Could not save positions: {e}")
    
    async def _save_orders(self):
        """Save current orders to database"""
        try:
            # TODO: Save orders to database
            pass
        except Exception as e:
            logger.error(f"Could not save orders: {e}")
    
    async def _start_background_tasks(self):
        """Start background tasks"""
        self.position_update_task = asyncio.create_task(self._position_update_loop())
    
    async def _position_update_loop(self):
        """Background task to update positions and P&L"""
        while self.is_running:
            try:
                # Update unrealized P&L for all positions
                for position in self.positions.values():
                    current_price = await self.get_current_price(position.symbol)
                    if current_price:
                        position.update_unrealized_pnl(current_price)
                
                # Broadcast position updates
                if self.websocket_manager:
                    positions_data = [pos.to_dict() for pos in self.positions.values()]
                    await self.websocket_manager.broadcast_to_channel("positions", {
                        "positions": positions_data,
                        "total_pnl": self.get_total_pnl()
                    })
                
                await asyncio.sleep(1)  # Update every second
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Position update loop error: {e}")
                await asyncio.sleep(5)
    
    # Trading operations
    
    async def place_order(self, symbol: str, side: str, order_type: str, 
                         size: float, price: Optional[float] = None) -> Dict[str, Any]:
        """Place a trading order"""
        try:
            # Risk checks
            if not await self._risk_check(symbol, side, size, price):
                return {"success": False, "error": "Risk check failed"}
            
            # Create order
            order = Order(symbol, side, order_type, size, price)
            self.orders[order.id] = order
            
            # Simulate order execution for paper trading
            if not self.is_live_trading:
                await self._simulate_order_execution(order)
            else:
                # TODO: Implement live order execution
                pass
            
            # Broadcast order update
            if self.websocket_manager:
                await self.websocket_manager.broadcast_order_update(order.to_dict())
            
            return {"success": True, "order_id": order.id, "order": order.to_dict()}
            
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return {"success": False, "error": str(e)}
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel a pending order"""
        try:
            if order_id not in self.orders:
                return {"success": False, "error": "Order not found"}
            
            order = self.orders[order_id]
            if order.status != 'pending':
                return {"success": False, "error": "Order cannot be cancelled"}
            
            order.status = 'cancelled'
            
            # Broadcast order update
            if self.websocket_manager:
                await self.websocket_manager.broadcast_order_update(order.to_dict())
            
            return {"success": True, "message": "Order cancelled"}
            
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return {"success": False, "error": str(e)}
    
    async def close_position(self, symbol: str) -> Dict[str, Any]:
        """Close a position"""
        try:
            if symbol not in self.positions:
                return {"success": False, "error": "Position not found"}
            
            position = self.positions[symbol]
            
            # Place opposing order to close position
            close_side = 'sell' if position.side == 'long' else 'buy'
            result = await self.place_order(symbol, close_side, 'market', abs(position.size))
            
            if result["success"]:
                # Remove position (will be handled by order execution)
                return {"success": True, "message": "Position close order placed"}
            else:
                return result
                
        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            return {"success": False, "error": str(e)}
    
    async def _risk_check(self, symbol: str, side: str, size: float, 
                         price: Optional[float] = None) -> bool:
        """Perform risk checks before placing order"""
        try:
            # Check position size limits
            current_position = self.positions.get(symbol)
            if current_position:
                new_size = current_position.size
                if (side == 'buy' and current_position.side == 'long') or \
                   (side == 'sell' and current_position.side == 'short'):
                    new_size += size
                elif (side == 'sell' and current_position.side == 'long') or \
                     (side == 'buy' and current_position.side == 'short'):
                    new_size -= size
                
                if abs(new_size) > self.max_position_size:
                    logger.warning(f"Position size limit exceeded for {symbol}")
                    return False
            
            # Check daily loss limit
            if self.daily_pnl < -self.max_daily_loss:
                logger.warning("Daily loss limit exceeded")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Risk check error: {e}")
            return False
    
    async def _simulate_order_execution(self, order: Order):
        """Simulate order execution for paper trading"""
        try:
            # Get current price
            current_price = await self.get_current_price(order.symbol)
            if not current_price:
                order.status = 'rejected'
                return
            
            # Simulate fill
            if order.type == 'market':
                order.filled_price = current_price
                order.filled_size = order.size
                order.status = 'filled'
                order.fill_timestamp = datetime.now()
            elif order.type == 'limit':
                # Simple limit order logic
                if (order.side == 'buy' and current_price <= order.price) or \
                   (order.side == 'sell' and current_price >= order.price):
                    order.filled_price = order.price
                    order.filled_size = order.size
                    order.status = 'filled'
                    order.fill_timestamp = datetime.now()
            
            # Update position if order is filled
            if order.status == 'filled':
                await self._update_position_from_order(order)
                
                # Save trade to database
                await self._save_trade(order)
            
        except Exception as e:
            logger.error(f"Order simulation error: {e}")
            order.status = 'rejected'
    
    async def _update_position_from_order(self, order: Order):
        """Update position based on filled order"""
        try:
            symbol = order.symbol
            
            if symbol in self.positions:
                position = self.positions[symbol]
                
                if order.side == 'buy':
                    if position.side == 'long':
                        # Add to long position
                        new_size = position.size + order.filled_size
                        new_price = ((position.entry_price * position.size) + 
                                   (order.filled_price * order.filled_size)) / new_size
                        position.size = new_size
                        position.entry_price = new_price
                    else:
                        # Reduce short position or flip to long
                        position.size -= order.filled_size
                        if position.size <= 0:
                            if position.size < 0:
                                # Flip to long position
                                position.side = 'long'
                                position.size = abs(position.size)
                                position.entry_price = order.filled_price
                            else:
                                # Position closed
                                del self.positions[symbol]
                
                elif order.side == 'sell':
                    if position.side == 'short':
                        # Add to short position
                        new_size = position.size + order.filled_size
                        new_price = ((position.entry_price * position.size) + 
                                   (order.filled_price * order.filled_size)) / new_size
                        position.size = new_size
                        position.entry_price = new_price
                    else:
                        # Reduce long position or flip to short
                        position.size -= order.filled_size
                        if position.size <= 0:
                            if position.size < 0:
                                # Flip to short position
                                position.side = 'short'
                                position.size = abs(position.size)
                                position.entry_price = order.filled_price
                            else:
                                # Position closed
                                del self.positions[symbol]
            else:
                # Create new position
                side = 'long' if order.side == 'buy' else 'short'
                self.positions[symbol] = Position(
                    symbol, side, order.filled_size, order.filled_price
                )
            
        except Exception as e:
            logger.error(f"Position update error: {e}")
    
    async def _save_trade(self, order: Order):
        """Save executed trade to database"""
        try:
            trade_data = {
                '체결시간': order.fill_timestamp.strftime('%Y%m%d%H%M%S'),
                '종목코드': order.symbol,
                '매수매도구분': order.side,
                '체결수량': order.filled_size,
                '체결가격': order.filled_price,
                '체결금액': order.filled_size * order.filled_price,
                '시장구분': 'paper_trading'
            }
            
            await self.db_manager.save_trade(trade_data)
            
        except Exception as e:
            logger.error(f"Failed to save trade: {e}")
    
    # Market data operations
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol"""
        try:
            if symbol in self.market_data:
                return self.market_data[symbol].get('price')
            
            # TODO: Fetch from market data source
            # For now, return a simulated price
            import random
            return random.uniform(100, 1000)
            
        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
            return None
    
    async def update_market_data(self, symbol: str, data: Dict[str, Any]):
        """Update market data for symbol"""
        self.market_data[symbol] = data
        
        # Broadcast market data update
        if self.websocket_manager:
            await self.websocket_manager.broadcast_market_data(
                data.get('market', 'unknown'), symbol, data
            )
    
    # Portfolio operations
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all current positions"""
        return [pos.to_dict() for pos in self.positions.values()]
    
    def get_orders(self) -> List[Dict[str, Any]]:
        """Get all orders"""
        return [order.to_dict() for order in self.orders.values()]
    
    def get_total_pnl(self) -> float:
        """Get total unrealized P&L"""
        total = 0.0
        for position in self.positions.values():
            total += position.unrealized_pnl
        return total
    
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary"""
        total_value = 0.0
        total_pnl = 0.0
        
        for position in self.positions.values():
            current_price = await self.get_current_price(position.symbol)
            if current_price:
                position.update_unrealized_pnl(current_price)
                total_value += abs(position.size) * current_price
                total_pnl += position.unrealized_pnl
        
        return {
            'total_positions': len(self.positions),
            'total_orders': len([o for o in self.orders.values() if o.status == 'pending']),
            'total_value': total_value,
            'total_pnl': total_pnl,
            'daily_pnl': self.daily_pnl
        }
    
    # System status
    
    def is_running(self) -> bool:
        """Check if trading service is running"""
        return self.is_running
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            'is_running': self.is_running,
            'is_live_trading': self.is_live_trading,
            'total_positions': len(self.positions),
            'total_orders': len(self.orders),
            'market_data_symbols': len(self.market_data),
            'daily_pnl': self.daily_pnl,
            'max_daily_loss': self.max_daily_loss,
            'max_position_size': self.max_position_size
        }