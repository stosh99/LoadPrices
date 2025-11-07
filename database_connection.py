"""
Database connection module for connecting to the newsdb PostgreSQL database
Uses the same connection settings as the news_three_tier project
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

class NewsDBConnection:
    """Handles connection to the newsdb PostgreSQL database"""

    def __init__(self):
        # Database connection parameters (same as news_three_tier project)
        self.connection_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'newsdb'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD')
        }
        self.connection = None

    def connect(self) -> bool:
        """Establish connection to the database"""
        if not self.connection_params['password']:
            print("❌ Database password not found. Please set the DB_PASSWORD environment variable.")
            return False
        try:
            self.connection = psycopg2.connect(**self.connection_params)
            print("✅ Successfully connected to newsdb database")
            return True
        except psycopg2.Error as e:
            print(f"❌ Error connecting to database: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("🔌 Database connection closed")

    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[List[Dict[Any, Any]]]:
        """Execute a SELECT query and return results"""
        if not self.connection:
            print("❌ No database connection")
            return None

        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except psycopg2.Error as e:
            print(f"❌ Error executing query: {e}")
            return None

    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> bool:
        """Execute INSERT, UPDATE, DELETE queries"""
        if not self.connection:
            print("❌ No database connection")
            return False

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
                print(f"✅ Query executed successfully. Rows affected: {cursor.rowcount}")
                return True
        except psycopg2.Error as e:
            print(f"❌ Error executing query: {e}")
            self.connection.rollback()
            return False

    def get_tables(self) -> Optional[List[str]]:
        """Get list of all tables in the database"""
        query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
        """
        results = self.execute_query(query)
        if results:
            return [row['table_name'] for row in results]
        return None

    def describe_table(self, table_name: str) -> Optional[List[Dict[str, Any]]]:
        """Get column information for a specific table"""
        query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position;
        """
        return self.execute_query(query, (table_name,))


def test_connection():
    """Test the database connection"""
    db = NewsDBConnection()

    if db.connect():
        # Get list of tables
        tables = db.get_tables()
        if tables:
            print(f"\n📋 Available tables in newsdb:")
            for table in tables:
                print(f"   • {table}")

            # Show structure of first table if available
            if tables:
                print(f"\n🔍 Structure of '{tables[0]}' table:")
                columns = db.describe_table(tables[0])
                if columns:
                    for col in columns:
                        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                        default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                        print(f"   • {col['column_name']}: {col['data_type']} {nullable}{default}")

        db.disconnect()


if __name__ == "__main__":
    test_connection()
