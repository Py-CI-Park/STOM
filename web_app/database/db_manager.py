import aiosqlite
import sqlite3
import pandas as pd
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from utility.setting import (
    DB_SETTING, DB_TRADELIST, DB_STRATEGY, DB_BACKTEST,
    DB_STOCK_TICK, DB_STOCK_MIN, DB_COIN_TICK, DB_COIN_MIN,
    DB_STOCK_BACK_TICK, DB_STOCK_BACK_MIN, DB_COIN_BACK_TICK, DB_COIN_BACK_MIN,
    DICT_SET
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages all SQLite database connections and operations"""
    
    def __init__(self):
        self.databases = {
            'setting': DB_SETTING,
            'tradelist': DB_TRADELIST,
            'strategy': DB_STRATEGY,
            'backtest': DB_BACKTEST,
            'stock_tick': DB_STOCK_TICK,
            'stock_min': DB_STOCK_MIN,
            'coin_tick': DB_COIN_TICK,
            'coin_min': DB_COIN_MIN,
            'stock_back_tick': DB_STOCK_BACK_TICK,
            'stock_back_min': DB_STOCK_BACK_MIN,
            'coin_back_tick': DB_COIN_BACK_TICK,
            'coin_back_min': DB_COIN_BACK_MIN
        }
        
        self.connections: Dict[str, aiosqlite.Connection] = {}
        self.connection_locks: Dict[str, asyncio.Lock] = {}
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize database connections"""
        try:
            # Create database directory if it doesn't exist
            db_path = Path('./_database')
            db_path.mkdir(exist_ok=True)
            
            # Initialize connection locks
            for db_name in self.databases:
                self.connection_locks[db_name] = asyncio.Lock()
            
            # Test connections
            for db_name, db_path in self.databases.items():
                await self._test_connection(db_name, db_path)
            
            self.is_initialized = True
            logger.info("Database manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}")
            raise
    
    async def _test_connection(self, db_name: str, db_path: str):
        """Test database connection"""
        try:
            async with aiosqlite.connect(db_path) as conn:
                await conn.execute("SELECT 1")
                logger.debug(f"Database connection test successful: {db_name}")
        except Exception as e:
            logger.warning(f"Database connection test failed for {db_name}: {e}")
    
    @asynccontextmanager
    async def get_connection(self, db_name: str):
        """Get database connection with automatic connection management"""
        if db_name not in self.databases:
            raise ValueError(f"Unknown database: {db_name}")
        
        db_path = self.databases[db_name]
        
        async with self.connection_locks[db_name]:
            conn = aiosqlite.connect(db_path)
            try:
                async with conn as connection:
                    yield connection
            finally:
                await conn.close()
    
    async def execute_query(self, db_name: str, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """Execute a SELECT query and return results as list of dictionaries"""
        async with self.get_connection(db_name) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(query, params or ())
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def execute_update(self, db_name: str, query: str, params: Optional[Tuple] = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows"""
        async with self.get_connection(db_name) as conn:
            cursor = await conn.execute(query, params or ())
            await conn.commit()
            return cursor.rowcount
    
    async def execute_many(self, db_name: str, query: str, params_list: List[Tuple]) -> int:
        """Execute multiple queries with different parameters"""
        async with self.get_connection(db_name) as conn:
            cursor = await conn.executemany(query, params_list)
            await conn.commit()
            return cursor.rowcount
    
    async def get_dataframe(self, db_name: str, query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """Execute query and return as pandas DataFrame"""
        # Use synchronous connection for pandas compatibility
        db_path = self.databases[db_name]
        with sqlite3.connect(db_path) as conn:
            return pd.read_sql_query(query, conn, params=params)
    
    async def save_dataframe(self, db_name: str, df: pd.DataFrame, table_name: str, 
                           if_exists: str = 'replace', index: bool = True) -> None:
        """Save pandas DataFrame to database table"""
        db_path = self.databases[db_name]
        with sqlite3.connect(db_path) as conn:
            df.to_sql(table_name, conn, if_exists=if_exists, index=index, chunksize=1000)
    
    async def get_table_info(self, db_name: str, table_name: str) -> List[Dict]:
        """Get table schema information"""
        query = f"PRAGMA table_info({table_name})"
        return await self.execute_query(db_name, query)
    
    async def get_tables(self, db_name: str) -> List[str]:
        """Get list of tables in database"""
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        results = await self.execute_query(db_name, query)
        return [row['name'] for row in results]
    
    async def table_exists(self, db_name: str, table_name: str) -> bool:
        """Check if table exists in database"""
        tables = await self.get_tables(db_name)
        return table_name in tables
    
    # STOM-specific database operations
    
    async def get_settings(self) -> Dict[str, Any]:
        """Get all system settings"""
        try:
            settings = {}
            
            # Get main settings
            main_settings = await self.execute_query('setting', 'SELECT * FROM main')
            if main_settings:
                settings['main'] = {row['index']: row for row in main_settings}
            
            # Get other setting tables
            for table in ['stock', 'coin', 'sacc', 'cacc', 'telegram', 'etc', 'back']:
                if await self.table_exists('setting', table):
                    table_data = await self.execute_query('setting', f'SELECT * FROM {table}')
                    settings[table] = {row['index']: row for row in table_data}
            
            return settings
            
        except Exception as e:
            logger.error(f"Failed to get settings: {e}")
            return {}
    
    async def update_setting(self, table: str, index: str, column: str, value: Any) -> bool:
        """Update a specific setting value"""
        try:
            query = f"UPDATE {table} SET {column} = ? WHERE `index` = ?"
            rows_affected = await self.execute_update('setting', query, (value, index))
            return rows_affected > 0
        except Exception as e:
            logger.error(f"Failed to update setting: {e}")
            return False
    
    async def get_trading_data(self, market: str, table_type: str, code: str = None, 
                             limit: int = None) -> pd.DataFrame:
        """Get trading data from market databases"""
        db_name = f"{market}_{table_type}"
        
        if code:
            query = f"SELECT * FROM `{code}`"
            if limit:
                query += f" ORDER BY `index` DESC LIMIT {limit}"
        else:
            # Get available tables
            tables = await self.get_tables(db_name)
            return pd.DataFrame({'tables': tables})
        
        return await self.get_dataframe(db_name, query)
    
    async def save_trading_data(self, market: str, table_type: str, code: str, 
                              df: pd.DataFrame) -> bool:
        """Save trading data to market databases"""
        try:
            db_name = f"{market}_{table_type}"
            await self.save_dataframe(db_name, df, code, if_exists='append', index=True)
            return True
        except Exception as e:
            logger.error(f"Failed to save trading data: {e}")
            return False
    
    async def get_strategies(self, strategy_type: str = None) -> List[Dict]:
        """Get trading strategies"""
        query = "SELECT * FROM strategy"
        if strategy_type:
            query += f" WHERE 전략구분 = '{strategy_type}'"
        
        return await self.execute_query('strategy', query)
    
    async def save_strategy(self, strategy_data: Dict) -> bool:
        """Save trading strategy"""
        try:
            # Build INSERT query dynamically
            columns = list(strategy_data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            query = f"INSERT INTO strategy ({', '.join(columns)}) VALUES ({placeholders})"
            
            values = list(strategy_data.values())
            await self.execute_update('strategy', query, tuple(values))
            return True
        except Exception as e:
            logger.error(f"Failed to save strategy: {e}")
            return False
    
    async def get_backtest_results(self, strategy_name: str = None, limit: int = 100) -> List[Dict]:
        """Get backtesting results"""
        query = "SELECT * FROM backtest"
        params = None
        
        if strategy_name:
            query += " WHERE 전략명 = ?"
            params = (strategy_name,)
        
        query += f" ORDER BY 일시 DESC LIMIT {limit}"
        
        return await self.execute_query('backtest', query, params)
    
    async def save_backtest_result(self, result_data: Dict) -> bool:
        """Save backtesting result"""
        try:
            columns = list(result_data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            query = f"INSERT INTO backtest ({', '.join(columns)}) VALUES ({placeholders})"
            
            values = list(result_data.values())
            await self.execute_update('backtest', query, tuple(values))
            return True
        except Exception as e:
            logger.error(f"Failed to save backtest result: {e}")
            return False
    
    async def get_trade_history(self, market: str = None, limit: int = 1000) -> List[Dict]:
        """Get trading history"""
        query = "SELECT * FROM tradelist"
        params = None
        
        if market:
            query += " WHERE 시장구분 = ?"
            params = (market,)
        
        query += f" ORDER BY 체결시간 DESC LIMIT {limit}"
        
        return await self.execute_query('tradelist', query, params)
    
    async def save_trade(self, trade_data: Dict) -> bool:
        """Save trade record"""
        try:
            columns = list(trade_data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            query = f"INSERT INTO tradelist ({', '.join(columns)}) VALUES ({placeholders})"
            
            values = list(trade_data.values())
            await self.execute_update('tradelist', query, tuple(values))
            return True
        except Exception as e:
            logger.error(f"Failed to save trade: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if database manager is connected"""
        return self.is_initialized
    
    async def close(self):
        """Close all database connections"""
        try:
            for connection in self.connections.values():
                await connection.close()
            self.connections.clear()
            self.is_initialized = False
            logger.info("Database manager closed")
        except Exception as e:
            logger.error(f"Error closing database manager: {e}")
    
    async def backup_database(self, db_name: str, backup_path: str) -> bool:
        """Create database backup"""
        try:
            import shutil
            original_path = self.databases[db_name]
            shutil.copy2(original_path, backup_path)
            logger.info(f"Database backup created: {db_name} -> {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup database {db_name}: {e}")
            return False
    
    async def optimize_database(self, db_name: str) -> bool:
        """Optimize database (VACUUM)"""
        try:
            async with self.get_connection(db_name) as conn:
                await conn.execute("VACUUM")
                await conn.commit()
            logger.info(f"Database optimized: {db_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to optimize database {db_name}: {e}")
            return False