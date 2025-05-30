import requests
import re
from bs4 import BeautifulSoup
import cloudscraper
import random
import time
import json
import sys

# sys.stdout = open('output.txt', 'w', encoding='utf-8')

def get_exchange_rate():
    # Try using the API endpoint directly
    url = 'https://www.bportugal.pt/en/page/currency-converter'
    
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
    
    params = {
        "currency_converter_date": "2025-01-01"
    }

    # Add random delay to mimic human behavior
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
                    response = scraper.get(url, headers=headers, params=params, proxies=proxy_dict, timeout=15)
                    if response.status_code == 200:
                        print(response.json())
                        break
                except:
                    continue
        
        if response.status_code != 200:
            raise Exception(f"Failed to retrieve data: HTTP {response.status_code}")
        
        # Try to parse as JSON first
        try:
            data = response.json()
            print(data)
            # Extract the EUR/USD rate from the JSON response
            # You'll need to adjust this based on the actual JSON structure
            rate_value = float(data['rates']['USD'])
            print(f"Exchange rate: {rate_value}")
            return rate_value
        except json.JSONDecodeError:
            # If not JSON, fall back to HTML parsing
            html = response.text
            soup = BeautifulSoup(html, "html.parser")
            
            # Look for the specific text pattern in the page for "1 EUR = ... USD"
            rate_text = None
            result_text = soup.find(string=re.compile(r"1\s*EUR\s*=\s*[0-9.,]+\s*USD"))
            search_text = soup.find(string=re.compile(r""))
            # print(soup)
            if result_text:
                rate_text = result_text.strip()
            else:
                usd_cell = soup.find(lambda tag: tag.name in ["td", "p", "div"] and "United States dollar" in tag.get_text())
                if usd_cell:
                    text = usd_cell.get_text()
                    combined = text + " " + usd_cell.find_next(text=True, recursive=False)
                    match = re.search(r"United States dollar\s*([0-9.]+)", combined)
                    if match:
                        rate_text = "1 EUR = " + match.group(1) + " USD"

            if not rate_text:
                raise ValueError("Could not find EUR->USD rate on the page.")

            rate_value = float(re.findall(r"=\s*([0-9.]+)\s*USD", rate_text)[0])
            print(f"Exchange rate: {rate_value}")
            return rate_value

    except Exception as e:
        print(f"Error retrieving exchange rate: {e}")
        return None

def get_eur_usd_rate(date_str):
    url = "https://www.bportugal.pt/en/page/currency-converter"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    params = {
        "currency_converter_date": date_str  # e.g., "2025-05-22"
    }
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        }
    )
    response = scraper.get(url, headers=headers, params=params, timeout=15)
    if response.status_code != 200:
        print(f"Failed to fetch data: HTTP {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    # Look for the text pattern "1 EUR = ... USD"
    result_text = soup.find(string=re.compile(r"1\\s*EUR\\s*=\\s*[0-9.,]+\\s*USD"))
    if result_text:
        print(f"{date_str}: {result_text.strip()}")
        return result_text.strip()
    else:
        print(f"Could not find EUR→USD rate for {date_str}")
        return None

if __name__ == "__main__":
    # with open('output_1.txt', 'w', encoding='utf-8') as f:
        # original_stdout = sys.stdout
        # sys.stdout = f
        # All prints here go to the file
        # ("This will go to the file.")
        # Call your function
    get_eur_usd_rate("2025-05-22")
        # sys.stdout = original_stdout  # Restore normal printing
