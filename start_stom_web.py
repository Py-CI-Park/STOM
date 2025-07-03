#!/usr/bin/env python3
"""
STOM Trading System Web Interface Startup Script

This script provides an easy way to start the STOM web interface with proper
configuration and error handling.
"""

import sys
import os
import argparse
import asyncio
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging(log_level="INFO"):
    """Setup logging configuration"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "stom.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'fastapi', 'uvicorn', 'aiosqlite', 'pandas', 'numpy',
        'passlib', 'python-jose', 'websockets'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All required packages are installed")
    return True

def check_database():
    """Check if database directory exists"""
    db_dir = project_root / "_database"
    
    if not db_dir.exists():
        print("⚠️  Database directory not found. Creating...")
        db_dir.mkdir(exist_ok=True)
        print("✅ Database directory created")
    else:
        print("✅ Database directory exists")
    
    return True

def main():
    """Main startup function"""
    parser = argparse.ArgumentParser(
        description="STOM Trading System Web Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_stom_web.py                    # Start in development mode
  python start_stom_web.py --production       # Start in production mode
  python start_stom_web.py --cli              # Start CLI interface
  python start_stom_web.py --port 8080        # Custom port
  python start_stom_web.py --host 0.0.0.0     # Listen on all interfaces
        """
    )
    
    parser.add_argument('--host', default='127.0.0.1', 
                       help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8000,
                       help='Port to bind to (default: 8000)')
    parser.add_argument('--production', action='store_true',
                       help='Run in production mode')
    parser.add_argument('--cli', action='store_true',
                       help='Start CLI interface instead of web server')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level (default: INFO)')
    parser.add_argument('--reload', action='store_true',
                       help='Enable auto-reload (development only)')
    parser.add_argument('--workers', type=int, default=1,
                       help='Number of worker processes (production only)')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    print("🚀 Starting STOM Trading System")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check database
    if not check_database():
        sys.exit(1)
    
    # Set environment variables
    os.environ['STOM_HOST'] = args.host
    os.environ['STOM_PORT'] = str(args.port)
    os.environ['STOM_LOG_LEVEL'] = args.log_level
    
    if args.production:
        os.environ['STOM_ENVIRONMENT'] = 'production'
        os.environ['STOM_DEBUG'] = 'false'
        print("🏭 Starting in PRODUCTION mode")
    else:
        os.environ['STOM_ENVIRONMENT'] = 'development'
        os.environ['STOM_DEBUG'] = 'true'
        print("🔧 Starting in DEVELOPMENT mode")
    
    try:
        if args.cli:
            # Start CLI interface
            print("💻 Starting CLI interface...")
            from web_app.cli.cli_main import main as cli_main
            asyncio.run(cli_main())
        else:
            # Start web server
            print(f"🌐 Starting web server on http://{args.host}:{args.port}")
            print("📚 API documentation: http://{}:{}/docs".format(args.host, args.port))
            print("🎮 Web interface: http://{}:{}".format(args.host, args.port))
            print("\nPress Ctrl+C to stop the server")
            
            import uvicorn
            from web_app.core.config import get_settings
            
            # Configure uvicorn
            config = {
                "app": "web_app.main:app",
                "host": args.host,
                "port": args.port,
                "log_level": args.log_level.lower(),
            }
            
            if args.production:
                config.update({
                    "workers": args.workers,
                    "access_log": True,
                    "use_colors": False,
                })
            else:
                config.update({
                    "reload": args.reload,
                    "reload_dirs": [str(project_root / "web_app")],
                    "use_colors": True,
                })
            
            uvicorn.run(**config)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Shutdown requested by user")
        logger.info("Application shutdown requested")
    except Exception as e:
        print(f"\n❌ Error starting STOM: {e}")
        logger.exception("Failed to start application")
        sys.exit(1)
    
    print("👋 STOM has been stopped")

if __name__ == "__main__":
    main()