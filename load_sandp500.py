import requests
from bs4 import BeautifulSoup
import datetime
from database_connection import NewsDBConnection

def load_sandp500_constituents():
    """
    Fetches the S&P 500 constituents from Wikipedia and loads them into the newsdb database.
    """
    url = "https://en.wikipedia.org/wiki/List_of_S&P_500_companies"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers)
    
    

    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find('table', {'id': 'constituents'})
    
    if table is None:
        print("❌ Could not find the constituents table on the Wikipedia page.")
        return

    db = NewsDBConnection()
    if not db.connect():
        return

    try:
        # Create table if it doesn't exist
        create_table_query = """
        CREATE TABLE IF NOT EXISTS sandp500const (
            symbol VARCHAR(10) PRIMARY KEY,
            security VARCHAR(255),
            gics_sector VARCHAR(255),
            gics_sub_industry VARCHAR(255),
            headquartered_location VARCHAR(255),
            date_added VARCHAR(20),
            cik VARCHAR(20),
            founded VARCHAR(255),
            dateupdated DATE
        );
        """
        db.execute_non_query(create_table_query)

        # Clear existing data
        db.execute_non_query("TRUNCATE TABLE sandp500const;")

        # Insert new data
        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td')
            if len(cols) < 8:
                continue
            
            symbol = cols[0].text.strip()
            security = cols[1].text.strip()
            gics_sector = cols[2].text.strip()
            gics_sub_industry = cols[3].text.strip()
            headquartered_location = cols[4].text.strip()
            date_added = cols[5].text.strip()
            cik = cols[6].text.strip()
            founded = cols[7].text.strip()
            dateupdated = datetime.date.today()

            insert_query = """
            INSERT INTO sandp500const (symbol, security, gics_sector, gics_sub_industry, headquartered_location, date_added, cik, founded, dateupdated)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol) DO UPDATE SET
                security = EXCLUDED.security,
                gics_sector = EXCLUDED.gics_sector,
                gics_sub_industry = EXCLUDED.gics_sub_industry,
                headquartered_location = EXCLUDED.headquartered_location,
                date_added = EXCLUDED.date_added,
                cik = EXCLUDED.cik,
                founded = EXCLUDED.founded,
                dateupdated = EXCLUDED.dateupdated;
            """
            params = (symbol, security, gics_sector, gics_sub_industry, headquartered_location, date_added, cik, founded, dateupdated)
            db.execute_non_query(insert_query, params)

    finally:
        db.disconnect()

if __name__ == "__main__":
    load_sandp500_constituents()