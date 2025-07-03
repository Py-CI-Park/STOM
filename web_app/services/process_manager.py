import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import signal
import os

from web_app.services.trading_service import TradingService
from web_app.services.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class BackgroundService:
    """Represents a background service"""
    
    def __init__(self, name: str, target_function, args: tuple = (), kwargs: dict = None):
        self.name = name
        self.target_function = target_function
        self.args = args
        self.kwargs = kwargs or {}
        self.process: Optional[mp.Process] = None
        self.task: Optional[asyncio.Task] = None
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.restart_count = 0
        self.max_restarts = 5
    
    async def start(self):
        """Start the service"""
        if self.is_running:
            return
        
        try:
            if asyncio.iscoroutinefunction(self.target_function):
                # Async function - run as task
                self.task = asyncio.create_task(
                    self.target_function(*self.args, **self.kwargs)
                )
            else:
                # Sync function - run in process
                self.process = mp.Process(
                    target=self.target_function,
                    args=self.args,
                    kwargs=self.kwargs,
                    name=self.name
                )
                self.process.start()
            
            self.is_running = True
            self.start_time = datetime.now()
            logger.info(f"Service started: {self.name}")
            
        except Exception as e:
            logger.error(f"Failed to start service {self.name}: {e}")
            raise
    
    async def stop(self):
        """Stop the service"""
        if not self.is_running:
            return
        
        try:
            if self.task:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
                self.task = None
            
            if self.process:
                if self.process.is_alive():
                    self.process.terminate()
                    self.process.join(timeout=5)
                    
                    if self.process.is_alive():
                        self.process.kill()
                        self.process.join()
                
                self.process = None
            
            self.is_running = False
            logger.info(f"Service stopped: {self.name}")
            
        except Exception as e:
            logger.error(f"Error stopping service {self.name}: {e}")
    
    async def restart(self):
        """Restart the service"""
        await self.stop()
        await asyncio.sleep(1)  # Brief delay
        
        if self.restart_count >= self.max_restarts:
            logger.error(f"Service {self.name} exceeded max restarts ({self.max_restarts})")
            return False
        
        self.restart_count += 1
        await self.start()
        return True
    
    def is_alive(self) -> bool:
        """Check if service is alive"""
        if not self.is_running:
            return False
        
        if self.task:
            return not self.task.done()
        
        if self.process:
            return self.process.is_alive()
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "name": self.name,
            "is_running": self.is_running,
            "is_alive": self.is_alive(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "restart_count": self.restart_count,
            "process_id": self.process.pid if self.process else None
        }


class ProcessManager:
    """Manages background processes and services"""
    
    def __init__(self, trading_service: TradingService, websocket_manager: WebSocketManager):
        self.trading_service = trading_service
        self.websocket_manager = websocket_manager
        
        self.services: Dict[str, BackgroundService] = {}
        self.is_running = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.executor: Optional[ProcessPoolExecutor] = None
    
    async def start_background_services(self):
        """Start all background services"""
        try:
            # Initialize process executor
            self.executor = ProcessPoolExecutor(max_workers=10)
            
            # Define services
            await self._register_services()
            
            # Start all services
            for service in self.services.values():
                await service.start()
            
            # Start monitoring task
            self.monitor_task = asyncio.create_task(self._monitor_services())
            
            self.is_running = True
            logger.info("Process manager started with all background services")
            
        except Exception as e:
            logger.error(f"Failed to start background services: {e}")
            await self.shutdown()
            raise
    
    async def _register_services(self):
        """Register all background services"""
        
        # Market data receiver service
        self.services["market_data_receiver"] = BackgroundService(
            name="market_data_receiver",
            target_function=self._market_data_receiver_loop
        )
        
        # Order execution service
        self.services["order_executor"] = BackgroundService(
            name="order_executor",
            target_function=self._order_execution_loop
        )
        
        # Risk monitor service
        self.services["risk_monitor"] = BackgroundService(
            name="risk_monitor",
            target_function=self._risk_monitor_loop
        )
        
        # Data persistence service
        self.services["data_persistence"] = BackgroundService(
            name="data_persistence",
            target_function=self._data_persistence_loop
        )
        
        # System health monitor
        self.services["health_monitor"] = BackgroundService(
            name="health_monitor",
            target_function=self._health_monitor_loop
        )
        
        # WebSocket manager service
        if self.websocket_manager:
            self.services["websocket_manager"] = BackgroundService(
                name="websocket_manager",
                target_function=self.websocket_manager.start
            )
    
    async def _monitor_services(self):
        """Monitor services and restart if needed"""
        while self.is_running:
            try:
                for service_name, service in self.services.items():
                    if service.is_running and not service.is_alive():
                        logger.warning(f"Service {service_name} died, attempting restart...")
                        
                        restart_success = await service.restart()
                        if not restart_success:
                            logger.error(f"Failed to restart service {service_name}")
                            # Notify via WebSocket
                            if self.websocket_manager:
                                await self.websocket_manager.broadcast_system_alert({
                                    "type": "service_failure",
                                    "service": service_name,
                                    "message": f"Service {service_name} failed and could not be restarted"
                                })
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Service monitor error: {e}")
                await asyncio.sleep(30)
    
    # Background service implementations
    
    async def _market_data_receiver_loop(self):
        """Background service for receiving market data"""
        logger.info("Market data receiver service started")
        
        while self.is_running:
            try:
                # TODO: Implement market data reception
                # This would connect to exchanges and receive real-time data
                
                # Simulate market data for now
                await asyncio.sleep(1)
                
                # Example: simulate price updates
                symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
                for symbol in symbols:
                    import random
                    price = random.uniform(100, 50000)
                    
                    if self.trading_service:
                        await self.trading_service.update_market_data(symbol, {
                            "price": price,
                            "volume": random.uniform(1000, 10000),
                            "timestamp": datetime.now().isoformat()
                        })
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Market data receiver error: {e}")
                await asyncio.sleep(5)
        
        logger.info("Market data receiver service stopped")
    
    async def _order_execution_loop(self):
        """Background service for order execution"""
        logger.info("Order execution service started")
        
        while self.is_running:
            try:
                # TODO: Implement order execution logic
                # This would handle pending orders and execute them
                
                await asyncio.sleep(0.1)  # High frequency checking
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Order execution error: {e}")
                await asyncio.sleep(1)
        
        logger.info("Order execution service stopped")
    
    async def _risk_monitor_loop(self):
        """Background service for risk monitoring"""
        logger.info("Risk monitor service started")
        
        while self.is_running:
            try:
                if self.trading_service:
                    # Check position sizes
                    positions = self.trading_service.get_positions()
                    for position in positions:
                        if abs(position["size"]) > self.trading_service.max_position_size:
                            logger.warning(f"Position size exceeded for {position['symbol']}")
                            # Alert via WebSocket
                            if self.websocket_manager:
                                await self.websocket_manager.broadcast_system_alert({
                                    "type": "risk_alert",
                                    "message": f"Position size exceeded for {position['symbol']}",
                                    "position": position
                                })
                    
                    # Check daily P&L
                    if self.trading_service.daily_pnl < -self.trading_service.max_daily_loss:
                        logger.warning("Daily loss limit exceeded")
                        if self.websocket_manager:
                            await self.websocket_manager.broadcast_system_alert({
                                "type": "risk_alert",
                                "message": "Daily loss limit exceeded",
                                "daily_pnl": self.trading_service.daily_pnl
                            })
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Risk monitor error: {e}")
                await asyncio.sleep(10)
        
        logger.info("Risk monitor service stopped")
    
    async def _data_persistence_loop(self):
        """Background service for data persistence"""
        logger.info("Data persistence service started")
        
        while self.is_running:
            try:
                # TODO: Implement data persistence logic
                # Save trading data, market data, etc. to database
                
                await asyncio.sleep(60)  # Save data every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Data persistence error: {e}")
                await asyncio.sleep(30)
        
        logger.info("Data persistence service stopped")
    
    async def _health_monitor_loop(self):
        """Background service for system health monitoring"""
        logger.info("Health monitor service started")
        
        while self.is_running:
            try:
                # Monitor system resources
                import psutil
                
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                disk_percent = psutil.disk_usage('/').percent
                
                # Alert if resources are high
                if cpu_percent > 90:
                    logger.warning(f"High CPU usage: {cpu_percent}%")
                
                if memory_percent > 90:
                    logger.warning(f"High memory usage: {memory_percent}%")
                
                if disk_percent > 90:
                    logger.warning(f"High disk usage: {disk_percent}%")
                
                # Broadcast system metrics
                if self.websocket_manager:
                    await self.websocket_manager.broadcast_to_channel("system_metrics", {
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory_percent,
                        "disk_percent": disk_percent,
                        "timestamp": datetime.now().isoformat()
                    })
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(60)
        
        logger.info("Health monitor service stopped")
    
    # Service management methods
    
    async def start_service(self, service_name: str) -> bool:
        """Start specific service"""
        if service_name not in self.services:
            return False
        
        service = self.services[service_name]
        if service.is_running:
            return True
        
        try:
            await service.start()
            return True
        except Exception as e:
            logger.error(f"Failed to start service {service_name}: {e}")
            return False
    
    async def stop_service(self, service_name: str) -> bool:
        """Stop specific service"""
        if service_name not in self.services:
            return False
        
        service = self.services[service_name]
        if not service.is_running:
            return True
        
        try:
            await service.stop()
            return True
        except Exception as e:
            logger.error(f"Failed to stop service {service_name}: {e}")
            return False
    
    async def restart_service(self, service_name: str) -> bool:
        """Restart specific service"""
        if service_name not in self.services:
            return False
        
        service = self.services[service_name]
        return await service.restart()
    
    async def restart_services(self):
        """Restart all services"""
        logger.info("Restarting all services...")
        
        for service_name in self.services:
            await self.restart_service(service_name)
        
        logger.info("All services restarted")
    
    def get_service_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get status of specific service"""
        if service_name not in self.services:
            return None
        
        return self.services[service_name].get_status()
    
    def get_all_service_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        status = {}
        for service_name, service in self.services.items():
            status[service_name] = service.get_status()
        
        return {
            "is_running": self.is_running,
            "total_services": len(self.services),
            "running_services": sum(1 for s in self.services.values() if s.is_running),
            "alive_services": sum(1 for s in self.services.values() if s.is_alive()),
            "services": status
        }
    
    async def shutdown(self):
        """Shutdown all services"""
        logger.info("Shutting down process manager...")
        
        self.is_running = False
        
        # Cancel monitor task
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        # Stop all services
        for service in self.services.values():
            await service.stop()
        
        # Shutdown executor
        if self.executor:
            self.executor.shutdown(wait=True)
        
        logger.info("Process manager shutdown complete")
    
    # Signal handling for graceful shutdown
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        if os.name == 'nt':  # Windows
            # Windows doesn't support SIGTERM in the same way
            import atexit
            atexit.register(lambda: asyncio.create_task(self.shutdown()))
        else:
            # Unix-like systems
            def signal_handler(signum, frame):
                logger.info(f"Received signal {signum}, shutting down...")
                asyncio.create_task(self.shutdown())
            
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)