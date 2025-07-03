import asyncio
import json
import uuid
from typing import Dict, List, Optional, Set, Any
from fastapi import WebSocket
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """Represents a WebSocket connection with metadata"""
    
    def __init__(self, websocket: WebSocket, user: Optional[Dict] = None):
        self.id = str(uuid.uuid4())
        self.websocket = websocket
        self.user = user
        self.subscriptions: Set[str] = set()
        self.connected_at = datetime.now()
        self.last_heartbeat = datetime.now()
        self.is_alive = True
    
    async def send_message(self, message: Dict[str, Any]):
        """Send message to WebSocket client"""
        try:
            await self.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to {self.id}: {e}")
            self.is_alive = False
    
    async def send_heartbeat(self):
        """Send heartbeat ping to client"""
        try:
            await self.send_message({
                "type": "heartbeat",
                "timestamp": datetime.now().isoformat()
            })
            self.last_heartbeat = datetime.now()
        except Exception as e:
            logger.error(f"Heartbeat failed for {self.id}: {e}")
            self.is_alive = False


class WebSocketManager:
    """Manages WebSocket connections and real-time data distribution"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # channel -> connection_ids
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self.running = False
    
    async def start(self):
        """Start background tasks"""
        if self.running:
            return
        
        self.running = True
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("WebSocket manager started")
    
    async def stop(self):
        """Stop background tasks and close all connections"""
        self.running = False
        
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        # Close all connections
        for connection in list(self.connections.values()):
            await self._close_connection(connection)
        
        logger.info("WebSocket manager stopped")
    
    async def connect(self, websocket: WebSocket, user: Optional[Dict] = None) -> str:
        """Register new WebSocket connection"""
        connection = WebSocketConnection(websocket, user)
        self.connections[connection.id] = connection
        
        # Send welcome message
        await connection.send_message({
            "type": "connected",
            "connection_id": connection.id,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"WebSocket connected: {connection.id} (total: {len(self.connections)})")
        
        # Start background tasks if not running
        if not self.running:
            await self.start()
        
        return connection.id
    
    async def disconnect(self, connection_id: str):
        """Unregister WebSocket connection"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            await self._close_connection(connection)
            del self.connections[connection_id]
            
            # Remove from all subscriptions
            for channel, subscribers in self.subscriptions.items():
                subscribers.discard(connection_id)
            
            logger.info(f"WebSocket disconnected: {connection_id} (total: {len(self.connections)})")
    
    async def _close_connection(self, connection: WebSocketConnection):
        """Close WebSocket connection safely"""
        try:
            await connection.websocket.close()
        except Exception as e:
            logger.debug(f"Error closing connection {connection.id}: {e}")
    
    async def handle_message(self, connection_id: str, message: Dict[str, Any]):
        """Handle incoming message from WebSocket client"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        message_type = message.get("type")
        
        try:
            if message_type == "subscribe":
                await self._handle_subscribe(connection, message)
            elif message_type == "unsubscribe":
                await self._handle_unsubscribe(connection, message)
            elif message_type == "heartbeat":
                await self._handle_heartbeat(connection)
            elif message_type == "trading_command":
                await self._handle_trading_command(connection, message)
            elif message_type == "data_request":
                await self._handle_data_request(connection, message)
            else:
                logger.warning(f"Unknown message type: {message_type}")
        
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
            await connection.send_message({
                "type": "error",
                "message": str(e)
            })
    
    async def _handle_subscribe(self, connection: WebSocketConnection, message: Dict[str, Any]):
        """Handle subscription request"""
        channels = message.get("channels", [])
        
        for channel in channels:
            if channel not in self.subscriptions:
                self.subscriptions[channel] = set()
            
            self.subscriptions[channel].add(connection.id)
            connection.subscriptions.add(channel)
        
        await connection.send_message({
            "type": "subscribed",
            "channels": channels
        })
        
        logger.debug(f"Connection {connection.id} subscribed to: {channels}")
    
    async def _handle_unsubscribe(self, connection: WebSocketConnection, message: Dict[str, Any]):
        """Handle unsubscription request"""
        channels = message.get("channels", [])
        
        for channel in channels:
            if channel in self.subscriptions:
                self.subscriptions[channel].discard(connection.id)
            connection.subscriptions.discard(channel)
        
        await connection.send_message({
            "type": "unsubscribed",
            "channels": channels
        })
        
        logger.debug(f"Connection {connection.id} unsubscribed from: {channels}")
    
    async def _handle_heartbeat(self, connection: WebSocketConnection):
        """Handle heartbeat from client"""
        connection.last_heartbeat = datetime.now()
        await connection.send_message({
            "type": "heartbeat_ack"
        })
    
    async def _handle_trading_command(self, connection: WebSocketConnection, message: Dict[str, Any]):
        """Handle trading command from client"""
        # Implement trading command handling
        command = message.get("command")
        params = message.get("params", {})
        
        # TODO: Implement trading command processing
        await connection.send_message({
            "type": "command_result",
            "command": command,
            "status": "received",
            "message": "Command processing not implemented yet"
        })
    
    async def _handle_data_request(self, connection: WebSocketConnection, message: Dict[str, Any]):
        """Handle data request from client"""
        request_type = message.get("request_type")
        params = message.get("params", {})
        
        # TODO: Implement data request processing
        await connection.send_message({
            "type": "data_response",
            "request_type": request_type,
            "data": {},
            "message": "Data request processing not implemented yet"
        })
    
    async def broadcast_to_channel(self, channel: str, data: Dict[str, Any]):
        """Broadcast data to all subscribers of a channel"""
        if channel not in self.subscriptions:
            return
        
        message = {
            "type": "channel_data",
            "channel": channel,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all subscribers
        subscribers = self.subscriptions[channel].copy()
        tasks = []
        
        for connection_id in subscribers:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                if connection.is_alive:
                    tasks.append(connection.send_message(message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def send_to_connection(self, connection_id: str, data: Dict[str, Any]):
        """Send data to specific connection"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            if connection.is_alive:
                await connection.send_message(data)
    
    async def broadcast_to_all(self, data: Dict[str, Any]):
        """Broadcast data to all connected clients"""
        if not self.connections:
            return
        
        tasks = []
        for connection in self.connections.values():
            if connection.is_alive:
                tasks.append(connection.send_message(data))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _heartbeat_loop(self):
        """Background task to send heartbeats"""
        while self.running:
            try:
                tasks = []
                for connection in self.connections.values():
                    if connection.is_alive:
                        tasks.append(connection.send_heartbeat())
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
                await asyncio.sleep(5)
    
    async def _cleanup_loop(self):
        """Background task to clean up dead connections"""
        while self.running:
            try:
                dead_connections = []
                current_time = datetime.now()
                
                for connection_id, connection in self.connections.items():
                    # Check if connection is dead (no heartbeat for 2 minutes)
                    if not connection.is_alive or \
                       (current_time - connection.last_heartbeat).seconds > 120:
                        dead_connections.append(connection_id)
                
                # Remove dead connections
                for connection_id in dead_connections:
                    await self.disconnect(connection_id)
                
                await asyncio.sleep(60)  # Clean up every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(30)
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.connections)
    
    def get_subscription_count(self, channel: str) -> int:
        """Get number of subscribers for a channel"""
        return len(self.subscriptions.get(channel, set()))
    
    def get_status(self) -> Dict[str, Any]:
        """Get WebSocket manager status"""
        return {
            "running": self.running,
            "total_connections": len(self.connections),
            "total_channels": len(self.subscriptions),
            "subscriptions": {
                channel: len(subscribers) 
                for channel, subscribers in self.subscriptions.items()
            }
        }
    
    # STOM-specific channel methods
    
    async def broadcast_market_data(self, market: str, symbol: str, data: Dict[str, Any]):
        """Broadcast market data to subscribers"""
        channel = f"market_data_{market}_{symbol}"
        await self.broadcast_to_channel(channel, data)
    
    async def broadcast_trade_update(self, trade_data: Dict[str, Any]):
        """Broadcast trade update to subscribers"""
        await self.broadcast_to_channel("trade_updates", trade_data)
    
    async def broadcast_order_update(self, order_data: Dict[str, Any]):
        """Broadcast order update to subscribers"""
        await self.broadcast_to_channel("order_updates", order_data)
    
    async def broadcast_system_alert(self, alert_data: Dict[str, Any]):
        """Broadcast system alert to all clients"""
        message = {
            "type": "system_alert",
            "data": alert_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_all(message)
    
    async def broadcast_backtest_progress(self, progress_data: Dict[str, Any]):
        """Broadcast backtesting progress to subscribers"""
        await self.broadcast_to_channel("backtest_progress", progress_data)