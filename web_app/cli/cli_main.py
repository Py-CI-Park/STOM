import asyncio
import argparse
import json
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from web_app.services.trading_service import TradingService
from web_app.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class CLIRunner:
    """Command-line interface for STOM trading system"""
    
    def __init__(self, trading_service: TradingService):
        self.trading_service = trading_service
        self.db_manager = trading_service.db_manager
        
        # Available commands
        self.commands = {
            'status': self.cmd_status,
            'positions': self.cmd_positions,
            'orders': self.cmd_orders,
            'place_order': self.cmd_place_order,
            'cancel_order': self.cmd_cancel_order,
            'close_position': self.cmd_close_position,
            'backtest': self.cmd_backtest,
            'optimize': self.cmd_optimize,
            'strategies': self.cmd_strategies,
            'market_data': self.cmd_market_data,
            'portfolio': self.cmd_portfolio,
            'settings': self.cmd_settings,
            'export': self.cmd_export,
            'import': self.cmd_import,
            'help': self.cmd_help
        }
    
    async def run(self):
        """Run CLI interface"""
        parser = self.create_parser()
        
        # If no arguments provided, start interactive mode
        if len(sys.argv) == 1:
            await self.interactive_mode()
        else:
            args = parser.parse_args()
            await self.execute_command(args)
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            description="STOM Trading System CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python -m stom --cli status                    # Show system status
  python -m stom --cli positions                 # List positions
  python -m stom --cli place_order BTCUSDT buy market 0.1
  python -m stom --cli backtest --strategy my_strategy --start 20240101 --end 20240201
  python -m stom --cli export --type trades --output trades.csv
            """
        )
        
        parser.add_argument('command', choices=list(self.commands.keys()), 
                          help='Command to execute')
        
        # Trading arguments
        parser.add_argument('--symbol', type=str, help='Trading symbol')
        parser.add_argument('--side', choices=['buy', 'sell'], help='Order side')
        parser.add_argument('--type', choices=['market', 'limit', 'stop'], help='Order type')
        parser.add_argument('--size', type=float, help='Order size')
        parser.add_argument('--price', type=float, help='Order price')
        parser.add_argument('--order-id', type=str, help='Order ID')
        
        # Backtesting arguments
        parser.add_argument('--strategy', type=str, help='Strategy name')
        parser.add_argument('--start', type=str, help='Start date (YYYYMMDD)')
        parser.add_argument('--end', type=str, help='End date (YYYYMMDD)')
        parser.add_argument('--timeframe', choices=['tick', 'min'], default='min', help='Data timeframe')
        parser.add_argument('--market', choices=['stock', 'coin'], default='stock', help='Market type')
        
        # Data export/import arguments
        parser.add_argument('--output', type=str, help='Output file path')
        parser.add_argument('--input', type=str, help='Input file path')
        parser.add_argument('--format', choices=['csv', 'json', 'excel'], default='csv', help='File format')
        
        # General arguments
        parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        parser.add_argument('--json', action='store_true', help='JSON output format')
        
        return parser
    
    async def interactive_mode(self):
        """Interactive CLI mode"""
        print("STOM Trading System CLI - Interactive Mode")
        print("Type 'help' for available commands or 'exit' to quit")
        print("=" * 50)
        
        while True:
            try:
                command = input("\nstom> ").strip()
                
                if command.lower() in ['exit', 'quit', 'q']:
                    break
                
                if not command:
                    continue
                
                # Parse command
                parts = command.split()
                cmd_name = parts[0]
                
                if cmd_name not in self.commands:
                    print(f"Unknown command: {cmd_name}")
                    print("Type 'help' for available commands")
                    continue
                
                # Create mock args object
                args = argparse.Namespace()
                args.command = cmd_name
                args.verbose = False
                args.json = False
                
                # Parse additional arguments
                if len(parts) > 1:
                    self._parse_interactive_args(args, parts[1:])
                
                await self.execute_command(args)
                
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except Exception as e:
                print(f"Error: {e}")
        
        print("Goodbye!")
    
    def _parse_interactive_args(self, args: argparse.Namespace, parts: List[str]):
        """Parse interactive command arguments"""
        # Simple argument parsing for interactive mode
        for i, part in enumerate(parts):
            if part.startswith('--'):
                key = part[2:].replace('-', '_')
                if i + 1 < len(parts) and not parts[i + 1].startswith('--'):
                    value = parts[i + 1]
                    # Try to convert to appropriate type
                    try:
                        if '.' in value:
                            value = float(value)
                        elif value.isdigit():
                            value = int(value)
                    except:
                        pass
                    setattr(args, key, value)
                else:
                    setattr(args, key, True)
            elif not hasattr(args, 'positional_args'):
                args.positional_args = []
                args.positional_args.append(part)
            else:
                args.positional_args.append(part)
    
    async def execute_command(self, args: argparse.Namespace):
        """Execute a CLI command"""
        try:
            command_func = self.commands[args.command]
            result = await command_func(args)
            
            if result and not args.json:
                self._print_result(result, args.verbose)
            elif result and args.json:
                print(json.dumps(result, indent=2, default=str))
                
        except Exception as e:
            if args.verbose:
                logger.exception(f"Command failed: {args.command}")
            print(f"Error: {e}")
    
    def _print_result(self, result: Any, verbose: bool = False):
        """Print command result in human-readable format"""
        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, (list, dict)):
                    print(f"{key}:")
                    if isinstance(value, list):
                        for item in value:
                            print(f"  {item}")
                    else:
                        for k, v in value.items():
                            print(f"  {k}: {v}")
                else:
                    print(f"{key}: {value}")
        elif isinstance(result, list):
            for item in result:
                print(item)
        else:
            print(result)
    
    # Command implementations
    
    async def cmd_status(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Show system status"""
        status = await self.trading_service.get_system_status()
        return {
            "System Status": "Running" if status['is_running'] else "Stopped",
            "Trading Mode": "Live" if status['is_live_trading'] else "Paper",
            "Positions": status['total_positions'],
            "Orders": status['total_orders'],
            "Daily P&L": f"${status['daily_pnl']:.2f}",
            "Market Data Symbols": status['market_data_symbols']
        }
    
    async def cmd_positions(self, args: argparse.Namespace) -> List[Dict[str, Any]]:
        """List current positions"""
        positions = self.trading_service.get_positions()
        
        if not positions:
            print("No open positions")
            return []
        
        result = []
        for pos in positions:
            result.append({
                "Symbol": pos['symbol'],
                "Side": pos['side'],
                "Size": pos['size'],
                "Entry Price": f"${pos['entry_price']:.2f}",
                "Unrealized P&L": f"${pos['unrealized_pnl']:.2f}",
                "Timestamp": pos['timestamp']
            })
        
        return result
    
    async def cmd_orders(self, args: argparse.Namespace) -> List[Dict[str, Any]]:
        """List current orders"""
        orders = self.trading_service.get_orders()
        
        if not orders:
            print("No orders")
            return []
        
        result = []
        for order in orders:
            result.append({
                "ID": order['id'],
                "Symbol": order['symbol'],
                "Side": order['side'],
                "Type": order['type'],
                "Size": order['size'],
                "Price": f"${order['price']:.2f}" if order['price'] else "Market",
                "Status": order['status'],
                "Timestamp": order['timestamp']
            })
        
        return result
    
    async def cmd_place_order(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Place a trading order"""
        # Get required arguments
        symbol = getattr(args, 'symbol', None)
        side = getattr(args, 'side', None)
        order_type = getattr(args, 'type', 'market')
        size = getattr(args, 'size', None)
        price = getattr(args, 'price', None)
        
        # Check for positional arguments in interactive mode
        if hasattr(args, 'positional_args') and len(args.positional_args) >= 3:
            symbol = args.positional_args[0]
            side = args.positional_args[1]
            order_type = args.positional_args[2] if len(args.positional_args) > 2 else 'market'
            size = float(args.positional_args[3]) if len(args.positional_args) > 3 else None
            price = float(args.positional_args[4]) if len(args.positional_args) > 4 else None
        
        if not all([symbol, side, size]):
            return {"error": "Missing required arguments: symbol, side, size"}
        
        result = await self.trading_service.place_order(symbol, side, order_type, size, price)
        
        if result['success']:
            return {
                "Status": "Success",
                "Order ID": result['order_id'],
                "Message": f"Order placed: {side} {size} {symbol}"
            }
        else:
            return {"Status": "Failed", "Error": result['error']}
    
    async def cmd_cancel_order(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Cancel an order"""
        order_id = getattr(args, 'order_id', None)
        
        if hasattr(args, 'positional_args') and args.positional_args:
            order_id = args.positional_args[0]
        
        if not order_id:
            return {"error": "Order ID required"}
        
        result = await self.trading_service.cancel_order(order_id)
        
        if result['success']:
            return {"Status": "Success", "Message": f"Order {order_id} cancelled"}
        else:
            return {"Status": "Failed", "Error": result['error']}
    
    async def cmd_close_position(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Close a position"""
        symbol = getattr(args, 'symbol', None)
        
        if hasattr(args, 'positional_args') and args.positional_args:
            symbol = args.positional_args[0]
        
        if not symbol:
            return {"error": "Symbol required"}
        
        result = await self.trading_service.close_position(symbol)
        
        if result['success']:
            return {"Status": "Success", "Message": f"Position {symbol} closed"}
        else:
            return {"Status": "Failed", "Error": result['error']}
    
    async def cmd_backtest(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Run backtesting"""
        strategy = getattr(args, 'strategy', None)
        start_date = getattr(args, 'start', None)
        end_date = getattr(args, 'end', None)
        
        if not strategy:
            return {"error": "Strategy name required"}
        
        # TODO: Implement backtesting execution
        return {
            "Status": "Not Implemented",
            "Message": "Backtesting functionality will be implemented"
        }
    
    async def cmd_optimize(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Run strategy optimization"""
        # TODO: Implement optimization
        return {
            "Status": "Not Implemented",
            "Message": "Optimization functionality will be implemented"
        }
    
    async def cmd_strategies(self, args: argparse.Namespace) -> List[Dict[str, Any]]:
        """List available strategies"""
        try:
            strategies = await self.db_manager.get_strategies()
            
            if not strategies:
                print("No strategies found")
                return []
            
            result = []
            for strategy in strategies:
                result.append({
                    "Name": strategy.get('전략명', 'Unknown'),
                    "Type": strategy.get('전략구분', 'Unknown'),
                    "Market": strategy.get('시장구분', 'Unknown'),
                    "Created": strategy.get('생성일시', 'Unknown')
                })
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to load strategies: {e}"}
    
    async def cmd_market_data(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Show market data"""
        symbol = getattr(args, 'symbol', None)
        
        if symbol:
            price = await self.trading_service.get_current_price(symbol)
            if price:
                return {
                    "Symbol": symbol,
                    "Price": f"${price:.2f}",
                    "Timestamp": datetime.now().isoformat()
                }
            else:
                return {"error": f"No market data for {symbol}"}
        else:
            # Show all available market data
            market_data = self.trading_service.market_data
            if not market_data:
                return {"message": "No market data available"}
            
            result = {}
            for symbol, data in market_data.items():
                result[symbol] = f"${data.get('price', 0):.2f}"
            
            return result
    
    async def cmd_portfolio(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Show portfolio summary"""
        summary = await self.trading_service.get_portfolio_summary()
        
        return {
            "Total Positions": summary['total_positions'],
            "Total Orders": summary['total_orders'],
            "Total Value": f"${summary['total_value']:.2f}",
            "Total P&L": f"${summary['total_pnl']:.2f}",
            "Daily P&L": f"${summary['daily_pnl']:.2f}"
        }
    
    async def cmd_settings(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Show/update settings"""
        try:
            settings = await self.db_manager.get_settings()
            
            # Show main settings
            main_settings = settings.get('main', {})
            result = {}
            
            for key, value in main_settings.items():
                if isinstance(value, dict) and 'value' in value:
                    result[key] = value['value']
                else:
                    result[key] = value
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to load settings: {e}"}
    
    async def cmd_export(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Export data"""
        data_type = getattr(args, 'type', 'trades')
        output_file = getattr(args, 'output', None)
        file_format = getattr(args, 'format', 'csv')
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"stom_{data_type}_{timestamp}.{file_format}"
        
        try:
            if data_type == 'trades':
                trades = await self.db_manager.get_trade_history(limit=10000)
                
                if file_format == 'csv':
                    import pandas as pd
                    df = pd.DataFrame(trades)
                    df.to_csv(output_file, index=False)
                elif file_format == 'json':
                    with open(output_file, 'w') as f:
                        json.dump(trades, f, indent=2, default=str)
                
                return {
                    "Status": "Success",
                    "Message": f"Exported {len(trades)} trades to {output_file}"
                }
            else:
                return {"error": f"Unsupported data type: {data_type}"}
                
        except Exception as e:
            return {"error": f"Export failed: {e}"}
    
    async def cmd_import(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Import data"""
        input_file = getattr(args, 'input', None)
        
        if not input_file:
            return {"error": "Input file required"}
        
        # TODO: Implement data import
        return {
            "Status": "Not Implemented",
            "Message": "Import functionality will be implemented"
        }
    
    async def cmd_help(self, args: argparse.Namespace) -> None:
        """Show help information"""
        help_text = """
STOM Trading System CLI Commands:

Trading Commands:
  status                           Show system status
  positions                        List current positions
  orders                          List current orders
  place_order <symbol> <side> <type> <size> [price]
                                  Place a trading order
  cancel_order <order_id>         Cancel an order
  close_position <symbol>         Close a position

Analysis Commands:
  backtest --strategy <name> --start <date> --end <date>
                                  Run backtesting
  optimize --strategy <name>      Run strategy optimization
  strategies                      List available strategies
  portfolio                       Show portfolio summary

Data Commands:
  market_data [symbol]            Show market data
  export --type <type> --output <file>
                                  Export data
  import --input <file>           Import data
  settings                        Show system settings

General:
  help                           Show this help
  exit                           Exit CLI

Examples:
  place_order BTCUSDT buy market 0.1
  place_order ETHUSDT sell limit 1.0 --price 2000
  cancel_order order_123456789
  export --type trades --output my_trades.csv
        """
        print(help_text)


# Main CLI entry point
async def main():
    """Main CLI entry point"""
    # Initialize core services
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    trading_service = TradingService(db_manager, None)
    await trading_service.initialize()
    
    # Run CLI
    cli_runner = CLIRunner(trading_service)
    await cli_runner.run()
    
    # Cleanup
    await trading_service.shutdown()
    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())