import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
import json
import logging

from web_app.database.db_manager import DatabaseManager
from web_app.services.trading_service import TradingService
from web_app.services.websocket_manager import WebSocketManager
from web_app.services.process_manager import ProcessManager
from web_app.api import auth, trading, database, settings, backtesting
from web_app.core.config import get_settings
from web_app.core.security import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global managers
db_manager: Optional[DatabaseManager] = None
trading_service: Optional[TradingService] = None
websocket_manager: Optional[WebSocketManager] = None
process_manager: Optional[ProcessManager] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global db_manager, trading_service, websocket_manager, process_manager
    
    # Startup
    logger.info("Starting STOM Web Application...")
    
    # Initialize managers
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    websocket_manager = WebSocketManager()
    
    trading_service = TradingService(db_manager, websocket_manager)
    await trading_service.initialize()
    
    process_manager = ProcessManager(trading_service, websocket_manager)
    await process_manager.start_background_services()
    
    logger.info("STOM Web Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down STOM Web Application...")
    
    if process_manager:
        await process_manager.shutdown()
    if trading_service:
        await trading_service.shutdown()
    if db_manager:
        await db_manager.close()
    
    logger.info("STOM Web Application shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="STOM Trading System",
    description="Professional-grade high-frequency trading system with web interface",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(trading.router, prefix="/api/trading", tags=["trading"])
app.include_router(database.router, prefix="/api/database", tags=["database"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(backtesting.router, prefix="/api/backtesting", tags=["backtesting"])

# Dependency injection for services
@app.on_event("startup")
async def inject_dependencies():
    """Inject service dependencies into API routers"""
    global db_manager, trading_service
    
    # Inject dependencies into API modules
    from web_app.api import trading as trading_api
    from web_app.api import database as database_api
    from web_app.api import settings as settings_api
    from web_app.api import backtesting as backtesting_api
    
    if trading_service:
        trading_api.set_trading_service(trading_service)
    
    if db_manager:
        database_api.set_db_manager(db_manager)
        settings_api.set_db_manager(db_manager)
        backtesting_api.set_db_manager(db_manager)

# Mount static files
app.mount("/static", StaticFiles(directory="web_app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main application page"""
    try:
        with open("web_app/templates/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>STOM Trading System</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>STOM Trading System</h1>
            <p>Web interface is loading...</p>
            <p>Please ensure the web UI files are properly installed.</p>
        </body>
        </html>
        """)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """Main WebSocket endpoint for real-time data"""
    try:
        # Accept connection
        await websocket.accept()
        
        # Authenticate if token provided
        user = None
        if token:
            try:
                # Add authentication logic here
                pass
            except Exception as e:
                await websocket.close(code=1008, reason="Authentication failed")
                return
        
        # Register connection
        connection_id = await websocket_manager.connect(websocket, user)
        logger.info(f"WebSocket connection established: {connection_id}")
        
        try:
            while True:
                # Receive messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                await websocket_manager.handle_message(connection_id, message)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket connection closed: {connection_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await websocket.close(code=1011, reason="Internal error")
        finally:
            await websocket_manager.disconnect(connection_id)
            
    except Exception as e:
        logger.error(f"WebSocket endpoint error: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": db_manager.is_connected() if db_manager else False,
        "trading_service": trading_service.is_running() if trading_service else False,
        "websocket_connections": len(websocket_manager.connections) if websocket_manager else 0
    }

@app.get("/api/system/status")
async def system_status(current_user: dict = Depends(get_current_user)):
    """Get system status information"""
    if not trading_service:
        raise HTTPException(status_code=503, detail="Trading service not available")
    
    return await trading_service.get_system_status()

@app.post("/api/system/restart")
async def restart_system(current_user: dict = Depends(get_current_user)):
    """Restart system services"""
    if not process_manager:
        raise HTTPException(status_code=503, detail="Process manager not available")
    
    await process_manager.restart_services()
    return {"message": "System restart initiated"}

# CLI mode support
def run_cli_mode():
    """Run in CLI mode without web interface"""
    import asyncio
    from web_app.cli.cli_main import CLIRunner
    
    async def cli_main():
        global db_manager, trading_service
        
        # Initialize core services
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        trading_service = TradingService(db_manager, None)
        await trading_service.initialize()
        
        # Run CLI
        cli_runner = CLIRunner(trading_service)
        await cli_runner.run()
    
    asyncio.run(cli_main())

if __name__ == "__main__":
    import sys
    
    if "--cli" in sys.argv:
        # Run in CLI mode
        run_cli_mode()
    else:
        # Run web server
        config = get_settings()
        uvicorn.run(
            "web_app.main:app",
            host=config.host,
            port=config.port,
            reload=config.debug,
            log_level="info"
        )