from database_connection import NewsDBConnection

def alter_prices_table():
    db = NewsDBConnection()
    if db.connect():
        query = '''
        ALTER TABLE prices
        ADD COLUMN open NUMERIC,
        ADD COLUMN high NUMERIC,
        ADD COLUMN low NUMERIC,
        ADD COLUMN "Group" VARCHAR(20),
        ADD COLUMN subgroup VARCHAR(20);
        '''
        if db.execute_non_query(query):
            print("✅ Successfully altered the 'prices' table.")
        else:
            print("❌ Failed to alter the 'prices' table.")
        db.disconnect()

if __name__ == "__main__":
    alter_prices_table()