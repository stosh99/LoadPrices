from database_connection import NewsDBConnection

def create_indicators_table():
    db = NewsDBConnection()
    if not db.connect():
        return

    try:
        create_table_query = """
        CREATE TABLE IF NOT EXISTS technical_indicators (
            ticker TEXT NOT NULL,
            date DATE NOT NULL,
            "Group" VARCHAR(50),
            subgroup VARCHAR(50),
            sma7 DECIMAL(10, 4),
            sma10 DECIMAL(10, 4),
            sma20 DECIMAL(10, 4),
            sma50 DECIMAL(10, 4),
            sma100 DECIMAL(10, 4),
            sma200 DECIMAL(10, 4),
            ema12 DECIMAL(10, 4),
            ema21 DECIMAL(10, 4),
            ema26 DECIMAL(10, 4),
            boll_up DECIMAL(10, 4),
            boll_dn DECIMAL(10, 4),
            boll_mid DECIMAL(10, 4),
            zscore DECIMAL(10, 4),
            PRIMARY KEY (ticker, date)
        );
        """
        if db.execute_non_query(create_table_query):
            print("✅ Successfully created the 'technical_indicators' table.")
        else:
            print("❌ Failed to create the 'technical_indicators' table.")

    finally:
        db.disconnect()

if __name__ == "__main__":
    create_indicators_table()