import requests
import re
from bs4 import BeautifulSoup
import cloudscraper

def get_exchange_rate():
    url = 'https://www.bportugal.pt/page/conversor-de-moeda'  # Replace with actual URL
    # response = requests.get(url)
    # soup = BeautifulSoup(response.content, 'html.parser')
    
    # print(soup)

    # Attempt to fetch the page content with a normal session
    headers = {"User-Agent": "Mozilla/5.0"}  # Identify as a browser
    session = requests.Session()
    session.headers.update(headers)
    # try:
    # If the site supports a direct query parameter for date (if discovered via network inspection), 
    # you could append it here, e.g.: converter_url += f"?date={target_date}"
        # response = session.get(url, timeout=10)
    #     response = scraper.get(url, timeout=10)
    #     if response.status_code != 200:
    #         raise Exception(f"HTTP {response.status_code}")
    # except Exception as e:
        # If Cloudflare blocks the request or another error occurs, use cloudscraper as a fallback
    scraper = cloudscraper.create_scraper()  # This creates a session object that handles Cloudflare
    response = scraper.get(url, timeout=15)
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve data: HTTP {response.status_code}")
    
    html = response.text

    # Parse the HTML content to find the EUR->USD rate
    soup = BeautifulSoup(html, "html.parser")

    # Look for the specific text pattern in the page for "1 EUR = ... USD"
    rate_text = None
    result_text = soup.find(string=re.compile(r"1\s*EUR\s*=\s*[0-9.,]+\s*USD"))
    if result_text:
        rate_text = result_text.strip()  # e.g. "1 EUR = 1.1185 USD"
    else:
        # Fallback: search the table for the United States dollar entry
        # Find the row/cell that contains 'United States dollar'
        usd_cell = soup.find(lambda tag: tag.name in ["td", "p", "div"] and "United States dollar" in tag.get_text())
        if usd_cell:
            text = usd_cell.get_text()
            # That cell might contain the currency name; the rate is likely after it
            # So combine text of that cell and maybe some next siblings to extract the number
            combined = text + " " + usd_cell.find_next(text=True, recursive=False)
            match = re.search(r"United States dollar\s*([0-9.]+)", combined)
            if match:
                rate_text = "1 EUR = " + match.group(1) + " USD"

    if not rate_text:
        raise ValueError("Could not find EUR->USD rate on the page.")

    # Extract the numeric value from the rate_text
    # rate_text is like "1 EUR = 1.1185 USD"
    rate_value = float(re.findall(r"=\s*([0-9.]+)\s*USD", rate_text)[0])
    print(rate_value) 

    # # Prepare data payload for the ERP API
    # payload = {
    #     "date": "2025-05-16",
    #     "EUR_to_USD": rate_value
    # }

    # Post the data to the ERP API (dummy endpoint)
    # resp = requests.post(erp_api_url, json=payload)
    # if resp.status_code == 200:
    #     print(f"Posted exchange rate {rate_value} for {target_date} to ERP API successfully.")
    # else:
    #     print(f"Failed to post data to ERP API. HTTP status: {resp.status_code}")

get_exchange_rate()