from database_connection import NewsDBConnection

def load_sector_etfs():
    """
    Loads the S&P 500 SPDR sector ETFs into the newsdb database from a hardcoded list.
    """
    sector_etfs = [
        {'symbol': 'XLC', 'name': 'Communication Services'},
        {'symbol': 'XLY', 'name': 'Consumer Discretionary'},
        {'symbol': 'XLP', 'name': 'Consumer Staples'},
        {'symbol': 'XLE', 'name': 'Energy'},
        {'symbol': 'XLF', 'name': 'Financials'},
        {'symbol': 'XLV', 'name': 'Health Care'},
        {'symbol': 'XLI', 'name': 'Industrials'},
        {'symbol': 'XLB', 'name': 'Materials'},
        {'symbol': 'XLRE', 'name': 'Real Estate'},
        {'symbol': 'XLK', 'name': 'Technology'},
        {'symbol': 'XLU', 'name': 'Utilities'},
        {'symbol': 'SPY', 'name': 'SandP500'}
    ]

    db = NewsDBConnection()
    if not db.connect():
        return

    try:
        # Create table if it doesn't exist
        create_table_query = """
        CREATE TABLE IF NOT EXISTS sector_etfs (
            symbol VARCHAR(10) PRIMARY KEY,
            name VARCHAR(255)
        );
        """
        db.execute_non_query(create_table_query)

        # Clear existing data
        db.execute_non_query("TRUNCATE TABLE sector_etfs;")

        # Insert new data
        print(f"Inserting {len(sector_etfs)} sector ETFs into the database.")
        for etf in sector_etfs:
            insert_query = """
            INSERT INTO sector_etfs (symbol, name)
            VALUES (%s, %s)
            ON CONFLICT (symbol) DO UPDATE SET
                name = EXCLUDED.name;
            """
            params = (etf['symbol'], etf['name'])
            db.execute_non_query(insert_query, params)

    finally:
        db.disconnect()

if __name__ == "__main__":
    load_sector_etfs()