from database_connection import NewsDBConnection

def alter_prices_subgroup():
    db = NewsDBConnection()
    if db.connect():
        query = 'ALTER TABLE prices ALTER COLUMN subgroup TYPE VARCHAR(255);'
        if db.execute_non_query(query):
            print("✅ Successfully altered the 'subgroup' column in the 'prices' table.")
        else:
            print("❌ Failed to alter the 'subgroup' column.")
        db.disconnect()

if __name__ == "__main__":
    alter_prices_subgroup()