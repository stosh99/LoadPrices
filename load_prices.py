import yfinance as yf
import psycopg2.extras
import argparse
from database_connection import NewsDBConnection
from typing import List, Dict

def get_securities_from_db(db: NewsDBConnection, source: str) -> List[Dict[str, str]]:
    """Fetches a list of securities to process from the database."""
    if source == 'etfs':
        print("Fetching ETF list from 'sector_etfs' table...")
        # The "Group" column is a reserved keyword, so it needs to be double-quoted in the query if aliased.
        # However, we are creating it as a static value here, so we just need to handle it in the Python dict.
        query = "SELECT symbol as ticker, 'ETF' as group_val, name as subgroup FROM sector_etfs;"
    elif source == 'equities':
        print("Fetching equity list from 'sandp500const' table...")
        query = "SELECT symbol as ticker, security as group_val, gics_sector as subgroup FROM sandp500const;"
    else:
        return []

    securities = db.execute_query(query)
    # Map 'group_val' to 'Group' to match the required dictionary key for the next function
    if securities:
        return [{'ticker': s['ticker'], 'Group': s['group_val'], 'subgroup': s['subgroup']} for s in securities]
    return []

def fetch_and_load_prices(db: NewsDBConnection, securities: List[Dict[str, str]]):
    """
    Fetches historical price data for a list of securities and bulk loads it into the prices table.
    """
    if not securities:
        print("No securities provided to fetch.")
        return

    tickers_list = [s['ticker'] for s in securities]
    print(f"Fetching 2 years of historical data for {len(tickers_list)} tickers...")

    # yfinance can download data for multiple tickers at once, which is much faster.
    hist_df = yf.download(tickers_list, period="2y", group_by='ticker', auto_adjust=False)

    if hist_df.empty:
        print("⚠️ No historical data returned from yfinance.")
        return

    # Process and format the data for bulk insert
    all_price_data = []
    for security in securities:
        ticker = security['ticker']
        group = security['Group']
        subgroup = security['subgroup']

        try:
            # For multiple tickers, data is in a multi-level column DataFrame.
            # We select the data for the current ticker and drop rows with NaNs.
            ticker_hist = hist_df[ticker].dropna()
        except KeyError:
            print(f"  - No data for {ticker} in downloaded batch (it may have been delisted or the ticker is incorrect).")
            continue

        if ticker_hist.empty:
            continue

        print(f"  - Processing {len(ticker_hist)} records for {ticker}...")
        for index, row in ticker_hist.iterrows():
            all_price_data.append((
                index.date(),
                ticker,
                group,
                subgroup,
                float(row['Open']),
                float(row['Close']),
                float(row['High']),
                float(row['Low']),
                int(row['Volume'])
            ))

    if not all_price_data:
        print("No price data to insert after processing.")
        return

    # Bulk insert using execute_values for high performance
    print(f"\nBulk inserting {len(all_price_data)} total price records...")
    insert_query = """
    INSERT INTO prices (date, ticker, \"Group\", subgroup, open, close, high, low, volume)
    VALUES %s
    ON CONFLICT (date, ticker) DO UPDATE SET
        "Group" = EXCLUDED."Group",
        subgroup = EXCLUDED.subgroup,
        open = EXCLUDED.open,
        close = EXCLUDED.close,
        high = EXCLUDED.high,
        low = EXCLUDED.low,
        volume = EXCLUDED.volume;
    """
    try:
        cursor = db.connection.cursor()
        psycopg2.extras.execute_values(
            cursor,
            insert_query,
            all_price_data
        )
        db.connection.commit()
        print(f"✅ Successfully inserted/updated {len(all_price_data)} records.")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"❌ Error during bulk insert: {error}")
        db.connection.rollback()
    finally:
        cursor.close()


def main():
    """Main function to parse arguments and orchestrate the data loading."""
    parser = argparse.ArgumentParser(description="Load historical price data for specific securities or from predefined sources.")
    
    # Arguments for loading from a source table (e.g., 'etfs', 'equities')
    parser.add_argument(
        '--source',
        type=str,
        choices=['etfs', 'equities'],
        required=False,  # Not required if loading a single ticker
        help="The source of securities to load ('etfs' or 'equities')."
    )
    
    # Arguments for loading a single ticker
    parser.add_argument('--ticker', type=str, help="A single ticker symbol to load (e.g., 'SPY').")
    parser.add_argument('--group', type=str, help="The 'Group' for the single ticker (e.g., 'etf').")
    parser.add_argument('--subgroup', type=str, help="The 'subgroup' for the single ticker (e.g., 'S&P 500').")

    args = parser.parse_args()

    db = NewsDBConnection()
    if not db.connect():
        return

    try:
        securities_to_load = []
        # Prioritize loading a single ticker if all its details are provided
        if args.ticker and args.group and args.subgroup:
            print(f"Processing single ticker: {args.ticker} with Group='{args.group}' and Subgroup='{args.subgroup}'")
            securities_to_load.append({'ticker': args.ticker, 'Group': args.group, 'subgroup': args.subgroup})
        
        # Fallback to loading from a source if a single ticker is not specified
        elif args.source:
            print(f"Loading all securities from source: {args.source}")
            securities_to_load = get_securities_from_db(db, args.source)
        
        # If neither is provided, show an error
        else:
            parser.error("You must specify either a --source OR all of --ticker, --group, and --subgroup.")

        if not securities_to_load:
            print("❌ No securities to process based on the provided arguments.")
            return

        fetch_and_load_prices(db, securities_to_load)

    finally:
        db.disconnect()

if __name__ == "__main__":
    main()
