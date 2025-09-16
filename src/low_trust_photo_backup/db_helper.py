"""
Simple SQLite Database Module

A lightweight, easy-to-use wrapper around SQLite3 for common database operations.
No threading or connection pooling - just simple, clean database interactions.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
from contextlib import contextmanager
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Container for query results with metadata."""
    rows: List[Dict[str, Any]]
    row_count: int
    columns: List[str]
    
    def __len__(self) -> int:
        return self.row_count
    
    def __iter__(self):
        return iter(self.rows)
    
    def first(self) -> Optional[Dict[str, Any]]:
        """Get the first row or None."""
        return self.rows[0] if self.rows else None


class SQLiteDB:
    """
    Simple SQLite database wrapper with clean, easy-to-use methods.
    """
    
    def __init__(self, db_path: Union[str, Path], timeout: float = 30.0):
        """
        Initialize SQLite database connection.
        
        Args:
            db_path: Path to SQLite database file (':memory:' for in-memory)
            timeout: Connection timeout in seconds
        """
        self.db_path = str(db_path)
        self.timeout = timeout
        self.connection = None
        
        # Create database directory if it doesn't exist
        if db_path != ':memory:':
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self._connect()
        logger.info(f"Connected to SQLite database: {self.db_path}")
    
    def _connect(self):
        """Establish database connection."""
        self.connection = sqlite3.connect(self.db_path, timeout=self.timeout)
        # Enable row factory for dict-like access
        self.connection.row_factory = sqlite3.Row
        # Enable foreign key constraints
        self.connection.execute("PRAGMA foreign_keys = ON")
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        try:
            self.connection.execute("BEGIN")
            yield self.connection
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise
    
    def execute(self, query: str, params: Union[Dict, Tuple, List] = None) -> QueryResult:
        """
        Execute a SQL query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters (dict, tuple, or list)
        
        Returns:
            QueryResult object with rows, count, and columns
        """
        try:
            if params:
                cursor = self.connection.execute(query, params)
            else:
                cursor = self.connection.execute(query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch all rows and convert to dictionaries
            rows = [dict(row) for row in cursor.fetchall()]
            
            # Commit if it's a write operation
            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER')):
                self.connection.commit()
            
            return QueryResult(rows=rows, row_count=len(rows), columns=columns)
            
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
    
    def execute_many(self, query: str, params_list: List[Union[Dict, Tuple]]) -> int:
        """
        Execute a query multiple times with different parameters.
        
        Args:
            query: SQL query string
            params_list: List of parameter sets
        
        Returns:
            Number of affected rows
        """
        try:
            cursor = self.connection.executemany(query, params_list)
            self.connection.commit()
            return cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"Database error in execute_many: {e}")
            raise
    
    def fetch_one(self, query: str, params: Union[Dict, Tuple, List] = None) -> Optional[Dict[str, Any]]:
        """Fetch a single row."""
        result = self.execute(query, params)
        return result.first()
    
    def fetch_all(self, query: str, params: Union[Dict, Tuple, List] = None) -> List[Dict[str, Any]]:
        """Fetch all rows."""
        result = self.execute(query, params)
        return result.rows
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        Insert a single row into a table.
        
        Args:
            table: Table name
            data: Dictionary of column:value pairs
        
        Returns:
            ID of inserted row (if table has INTEGER PRIMARY KEY)
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        cursor = self.connection.execute(query, list(data.values()))
        self.connection.commit()
        
        return cursor.lastrowid
    
    def insert_many(self, table: str, data_list: List[Dict[str, Any]]) -> int:
        """
        Insert multiple rows into a table.
        
        Args:
            table: Table name
            data_list: List of dictionaries with column:value pairs
        
        Returns:
            Number of inserted rows
        """
        if not data_list:
            return 0
        
        # Use first row to determine columns
        columns = list(data_list[0].keys())
        column_names = ', '.join(columns)
        placeholders = ', '.join(['?' for _ in columns])
        query = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"
        
        # Convert to list of tuples in correct order
        params_list = [[row[col] for col in columns] for row in data_list]
        
        return self.execute_many(query, params_list)
    
    def update(self, table: str, data: Dict[str, Any], where_clause: str, 
               where_params: Union[Dict, Tuple, List] = None) -> int:
        """
        Update rows in a table.
        
        Args:
            table: Table name
            data: Dictionary of column:value pairs to update
            where_clause: WHERE clause (without 'WHERE' keyword)
            where_params: Parameters for WHERE clause
        
        Returns:
            Number of affected rows
        """
        set_clause = ', '.join([f"{col} = ?" for col in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        # Combine data values and where parameters
        params = list(data.values())
        if where_params:
            if isinstance(where_params, dict):
                params.extend(where_params.values())
            else:
                params.extend(where_params if isinstance(where_params, (list, tuple)) else [where_params])
        
        cursor = self.connection.execute(query, params)
        self.connection.commit()
        
        return cursor.rowcount
    
    def delete(self, table: str, where_clause: str, 
               where_params: Union[Dict, Tuple, List] = None) -> int:
        """
        Delete rows from a table.
        
        Args:
            table: Table name
            where_clause: WHERE clause (without 'WHERE' keyword)
            where_params: Parameters for WHERE clause
        
        Returns:
            Number of deleted rows
        """
        query = f"DELETE FROM {table} WHERE {where_clause}"
        
        cursor = self.connection.execute(query, where_params or [])
        self.connection.commit()
        
        return cursor.rowcount
    
    def create_table(self, table: str, schema: str) -> None:
        """
        Create a table with given schema.
        
        Args:
            table: Table name
            schema: Column definitions (e.g., "id INTEGER PRIMARY KEY, name TEXT")
        """
        query = f"CREATE TABLE IF NOT EXISTS {table} ({schema})"
        self.execute(query)
        logger.info(f"Created table: {table}")
    
    def drop_table(self, table: str) -> None:
        """Drop a table."""
        query = f"DROP TABLE IF EXISTS {table}"
        self.execute(query)
        logger.info(f"Dropped table: {table}")
    
    def table_exists(self, table: str) -> bool:
        """Check if a table exists."""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.execute(query, (table,))
        return len(result.rows) > 0
    
    def get_table_info(self, table: str) -> List[Dict[str, Any]]:
        """Get table schema information."""
        query = f"PRAGMA table_info({table})"
        result = self.execute(query)
        return result.rows
    
    def get_tables(self) -> List[str]:
        """Get list of all tables."""
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        result = self.execute(query)
        return [row['name'] for row in result.rows]
    
    def backup(self, backup_path: Union[str, Path]) -> None:
        """
        Backup database to another file.
        
        Args:
            backup_path: Path for backup file
        """
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        backup_conn = sqlite3.connect(str(backup_path))
        
        try:
            self.connection.backup(backup_conn)
            logger.info(f"Database backed up to: {backup_path}")
        finally:
            backup_conn.close()
    
    def vacuum(self) -> None:
        """Optimize database by rebuilding it."""
        self.execute("VACUUM")
        logger.info("Database vacuumed")
    
    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience functions for common operations
def quick_query(db_path: str, query: str, params=None) -> List[Dict[str, Any]]:
    """Execute a quick query without keeping connection open."""
    with SQLiteDB(db_path) as db:
        return db.fetch_all(query, params)


def create_sample_database(db_path: str = "sample.db") -> SQLiteDB:
    """Create a sample database for testing."""
    db = SQLiteDB(db_path)
    
    # Create users table
    db.create_table("users", """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    """)
    
    # Create posts table
    db.create_table("posts", """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    """)
    
    return db


if __name__ == "__main__":
    pass