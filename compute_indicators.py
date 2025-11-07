import pandas as pd
import psycopg2.extras
from database_connection import NewsDBConnection

def get_tickers(db):
    """Fetches a list of all unique tickers from the prices table."""
    query = "SELECT DISTINCT ticker FROM prices;"
    tickers_list = db.execute_query(query)
    if tickers_list:
        return [item['ticker'] for item in tickers_list]
    return []

def calculate_indicators(prices_df):
    """Calculates technical indicators for a given DataFrame of prices."""
    df = prices_df.copy().sort_values(by='date')

    # SMAs
    df['sma7'] = df['close'].rolling(window=7).mean()
    df['sma10'] = df['close'].rolling(window=10).mean()
    df['sma20'] = df['close'].rolling(window=20).mean()
    df['sma50'] = df['close'].rolling(window=50).mean()
    df['sma100'] = df['close'].rolling(window=100).mean()
    df['sma200'] = df['close'].rolling(window=200).mean()

    # EMAs
    df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
    df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()

    # Bollinger Bands
    df['boll_mid'] = df['sma20']
    rolling_std_20 = df['close'].rolling(window=20).std()
    df['boll_up'] = df['boll_mid'] + (rolling_std_20 * 2)
    df['boll_dn'] = df['boll_mid'] - (rolling_std_20 * 2)

    # Z-Score
    df['zscore'] = (df['close'] - df['boll_mid']) / rolling_std_20

    return df

def save_indicators_to_db(db, indicators_df):
    """Saves the calculated indicators to the technical_indicators table."""
    
    # Prepare data for insert
    cols = [
        "ticker", "date", "Group", "subgroup", "sma7", "sma10", "sma20",
        "sma50", "sma100", "sma200", "ema12", "ema21", "ema26", "boll_up",
        "boll_dn", "boll_mid", "zscore"
    ]
    
    # Ensure dataframe has all columns, fill missing with None (or NaN)
    for col in cols:
        if col not in indicators_df.columns:
            indicators_df[col] = None
            
    insert_df = indicators_df[cols].dropna()
    
    if insert_df.empty:
        print("No new indicator data to save.")
        return

    # Create the INSERT query with ON CONFLICT clause
    # The "Group" column is a reserved keyword in SQL, so it needs to be double-quoted.
    insert_query = f"""
    INSERT INTO technical_indicators (
        ticker, date, "Group", subgroup, sma7, sma10, sma20, sma50, sma100, sma200,
        ema12, ema21, ema26, boll_up, boll_dn, boll_mid, zscore
    ) VALUES %s
    ON CONFLICT (ticker, date) DO UPDATE SET
        "Group" = EXCLUDED."Group",
        subgroup = EXCLUDED.subgroup,
        sma7 = EXCLUDED.sma7,
        sma10 = EXCLUDED.sma10,
        sma20 = EXCLUDED.sma20,
        sma50 = EXCLUDED.sma50,
        sma100 = EXCLUDED.sma100,
        sma200 = EXCLUDED.sma200,
        ema12 = EXCLUDED.ema12,
        ema21 = EXCLUDED.ema21,
        ema26 = EXCLUDED.ema26,
        boll_up = EXCLUDED.boll_up,
        boll_dn = EXCLUDED.boll_dn,
        boll_mid = EXCLUDED.boll_mid,
        zscore = EXCLUDED.zscore;
    """

    # Use execute_values for efficient bulk insert/update
    try:
        cursor = db.connection.cursor()
        psycopg2.extras.execute_values(
            cursor,
            insert_query,
            insert_df.to_records(index=False).tolist()
        )
        db.connection.commit()
        print(f"✅ Successfully saved {len(insert_df)} indicator records.")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"❌ Error saving indicators: {error}")
        db.connection.rollback()
    finally:
        cursor.close()


def main():
    """Main function to orchestrate the indicator calculation process."""
    db = NewsDBConnection()
    if not db.connect():
        return

    try:
        tickers = get_tickers(db)
        if not tickers:
            print("No tickers found in the 'prices' table.")
            return

        print(f"Found {len(tickers)} tickers to process.")

        for i, ticker in enumerate(tickers):
            print(f"Processing {ticker} ({i + 1}/{len(tickers)})...")
            
            # Fetch price data
            query = f"SELECT date, close, \"Group\", subgroup FROM prices WHERE ticker = '{ticker}' ORDER BY date;"
            prices_data = db.execute_query(query)

            if not prices_data or len(prices_data) < 20:
                print(f"  - Skipping {ticker}: not enough price data.")
                continue
            
            prices_df = pd.DataFrame(prices_data)
            prices_df['close'] = pd.to_numeric(prices_df['close'])
            prices_df['ticker'] = ticker

            # Calculate indicators
            indicators_df = calculate_indicators(prices_df)

            # Save to database
            save_indicators_to_db(db, indicators_df)

    finally:
        print("Disconnecting from database.")
        db.disconnect()

if __name__ == "__main__":
    main()