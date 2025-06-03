import requests
import re
from bs4 import BeautifulSoup
import cloudscraper
import random
import time
import json
import sys
import pandas as pd
from datetime import datetime, timezone, timedelta

PT_ERP_API_BASE = "https://Vintech-PT.on.plex.com/api/datasources/"
CZ_ERP_API_BASE = "https://Vintech-CZ.on.plex.com/api/datasources/"
MX_ERP_API_BASE = "https://Vintech-MX.on.plex.com/api/datasources/"

PT_headers = {
  'Authorization': 'Basic VmludGVjaFBUV1NAcGxleC5jb206NDU2MDVjNS1mNDEyLTQ=',
  'Content-Type': 'application/json'
}
CZ_headers = {
  'Authorization': 'Basic VmludGVjaENaV1NAcGxleC5jb206MDljMTFlZC00MGIzLTQ=',
  'Content-Type': 'application/json'
}
MX_headers = {
  'Authorization': 'Basic VmludGVjaE1YV1NAcGxleC5jb206MjY5MjA0ZC00MmIyLTQ=',
  'Content-Type': 'application/json'
}

PT_url = 'https://www.bportugal.pt/en/page/currency-converter'
CZ_url = 'https://www.cnb.cz/en/financial-markets/foreign-exchange-market/central-bank-exchange-rate-fixing/central-bank-exchange-rate-fixing/'
MX_url = 'https://dof.gob.mx/indicadores.php#gsc.tab=0'

dollar_key = 1
euro_key = 2

# Start of today (UTC)
start_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

# End of today (UTC)
end_time = start_time + timedelta(days=1) - timedelta(milliseconds=1)

# Format as ISO 8601 with milliseconds and Z
start_iso = start_time.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
end_iso = end_time.isoformat(timespec='milliseconds').replace('+00:00', 'Z')

print("Start of today:", start_iso)
print("End of today:", end_iso)
sys.stdout = open('output.txt', 'w', encoding='utf-8')

def get_exchange_rate(url, location):
    # Try using the API endpoint directly
    
    
    # More realistic browser headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://www.bportugal.pt/",
        "Origin": "https://www.bportugal.pt",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }

    # List of free proxies (you should replace these with working proxies)
    proxies = [
        "http://proxy1.example.com:8080",
        "http://proxy2.example.com:8080",
        # Add more proxies here
    ]

    # Create scraper with browser-like settings
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        }
    )
    
    time.sleep(random.uniform(1, 3))
    
    try:
        # Try without proxy first
        response = scraper.get(url, headers=headers, timeout=15)
        
        # If that fails, try with proxies
        if response.status_code == 403:
            for proxy in proxies:
                try:
                    proxy_dict = {
                        "http": proxy,
                        "https": proxy
                    }
                    response = scraper.get(url, headers=headers, proxies=proxy_dict, timeout=15)
                    if response.status_code == 200:
                        # print(response.json())
                        break
                except:
                    continue
        
        if response.status_code != 200:
            raise Exception(f"Failed to retrieve data: HTTP {response.status_code}")
        
        # Try to parse as JSON first
        try:
            data = response.json()
        except json.JSONDecodeError:
            # If not JSON, fall back to HTML parsing
            html = response.text
            if location == 'PT':
                result_text = find_rate_pt(html)
            elif location == 'CZ':
                result_text = find_rate_cz(html)
            elif location == 'MX':
                result_text = find_rate_mx(html)
            return result_text
    except Exception as e:
        print(f"Error retrieving exchange rate: {e}")
        return None

def find_rate_pt(html):
    soup = BeautifulSoup(html, "html.parser")
    result_text = soup.find(string=re.compile(r"1\s*EUR\s*=\s*[0-9.,]+\s*USD"))
    
    if result_text:
        result_text = float(re.findall(r"=\s*([0-9.]+)\s*USD", str(result_text))[0])
        rate = 1/result_text
        return rate
    else:
        print("No EUR row found")
        return None
    
def find_rate_mx(html):
    soup = BeautifulSoup(html, "html.parser")
    result_text = soup.get_text()

    # Pattern to find DOLLAR followed by a number
    dollar_pattern = r'DOLAR\s*[\s\n]*(\d+\.?\d*)'
    match = re.search(dollar_pattern, result_text, re.IGNORECASE | re.MULTILINE)
    if match:
        rate = 1/float(match.group(1))
        return rate
    else:
        print("No rate found")
        return None

def find_rate_cz(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find('table')
    if table:
        # Convert table to pandas DataFrame
        df = pd.read_html(str(table))[0]
        
        # Look for EUR row (case insensitive)
        eur_mask = df['Currency'].str.contains('euro', case=False, na=False) | \
                    df['Code'].str.contains('EUR', case=False, na=False) | \
                    df['Country'].str.contains('EMU', case=False, na=False)
        
        eur_row = df[eur_mask]
        if not eur_row.empty:
            res = float(eur_row['Rate'].iloc[0])
            rate = 1/res
            return rate
        else:
            print("No EUR row found")


def update_erp_data(headers, ERP_API_BASE, key, rate):
    database_id = "5292"
    url = f"{ERP_API_BASE}{database_id}/execute"
    payload = json.dumps({
        "inputs": {
            "Add_By": 16746621,
            "Currency_Key": key,
            "Date_Start": start_iso,
            "Date_End": end_iso,
            "Exchange_Rate": rate
        }
    })
    # print("[update_container_location] payload: ", payload)
    response = requests.request("POST", url=url, headers=headers, data=payload)
    print("[update_container_location] response: ", response.json())
    return response.status_code == 200


if __name__ == "__main__":
    with open('output.txt', 'w', encoding='utf-8') as f:
        original_stdout = sys.stdout
        sys.stdout = f
        # All prints here go to the file
        print("This will go to the file.")
        # Call your function
        pt_rate = get_exchange_rate(PT_url, 'PT')
        cz_rate = get_exchange_rate(CZ_url, 'CZ')
        # mx_rate = get_exchange_rate(MX_url, 'MX')
        print("pt_rate: ", pt_rate)
        print("cz_rate: ", cz_rate)
        # print("mx_rate: ", mx_rate)
        # print(update_erp_data(PT_headers, PT_ERP_API_BASE, dollar_key, pt_rate))
        print(update_erp_data(CZ_headers, CZ_ERP_API_BASE, euro_key, cz_rate))
        sys.stdout = original_stdout  # Restore normal printing