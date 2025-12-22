"""
Database connection and utility functions
"""
import pymysql
from pymysql.cursors import DictCursor
from config import Config
from contextlib import contextmanager

class Database:
    """Database connection manager"""
    
    @staticmethod
    @contextmanager
    def get_connection():
        """
        Context manager for database connections
        Automatically handles connection closing
        """
        connection = None
        try:
            # Create connection config - set to Asia/Bangkok timezone (GMT+7)
            db_config = Config.DB_CONFIG.copy()
            
            connection = pymysql.connect(
                **db_config,
                cursorclass=DictCursor,
                init_command="SET time_zone='+07:00'"  # Match local timezone
            )
            yield connection
        except pymysql.Error as e:
            print(f"Database error: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                connection.close()
    
    @staticmethod
    def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
        """
        Execute a database query
        
        Args:
            query: SQL query string
            params: Query parameters (tuple or dict)
            fetch_one: Return single row
            fetch_all: Return all rows
            commit: Commit transaction
            
        Returns:
            Query results or lastrowid for INSERT operations
        """
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                
                if commit:
                    conn.commit()
                    return cursor.lastrowid if query.strip().upper().startswith('INSERT') else cursor.rowcount
                
                if fetch_one:
                    return cursor.fetchone()
                
                if fetch_all:
                    return cursor.fetchall()
                
                return None
    
    @staticmethod
    def call_procedure(proc_name, params=()):
        """
        Call a stored procedure
        
        Args:
            proc_name: Stored procedure name
            params: Procedure parameters
            
        Returns:
            Procedure results
        """
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.callproc(proc_name, params)
                conn.commit()
                return cursor.fetchall()
    
    @staticmethod
    def test_connection():
        """Test database connection"""
        try:
            with Database.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    return result is not None
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

# Test connection on module import
if __name__ == "__main__":
    if Database.test_connection():
        print("✓ Database connection successful!")
    else:
        print("✗ Database connection failed!")
