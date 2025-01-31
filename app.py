import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request
import time
import random

app = Flask(__name__)

# List of different User-Agents to rotate
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
]

# Proxy list (Use if site blocks your IP)
PROXIES = [
    "http://user:password@proxy1.com:port",
    "http://user:password@proxy2.com:port",
    "http://user:password@proxy3.com:port"
]

# Function to generate URL for the search page based on MMSI
def generate_search_url(mmsi):
    return f"https://www.marinevesseltraffic.com/2013/06/imo-number-search.html?imo={mmsi}"

# Function to scrape vessel info from the final redirected page
def scrape_vessel_info(url, session):
    # Select a random User-Agent to avoid detection
    headers = {
        'User-Agent': random.choice(USER_AGENTS)
    }
    
    # Optionally select a random proxy
    proxy = random.choice(PROXIES) if PROXIES else None
    proxies = {"http": proxy, "https": proxy} if proxy else None

    # Retry logic for handling 403 errors
    for _ in range(3):  # Try up to 3 times
        response = session.get(url, headers=headers, proxies=proxies, allow_redirects=True)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the <div> with the ship history info by its ID
            ship_history_div = soup.find("div", id="ship-history-info")

            if ship_history_div:
                return {
                    "Name": ship_history_div.get("data-name", "Not found"),
                    "IMO": ship_history_div.get("data-imo", "Not found"),
                    "MMSI": ship_history_div.get("data-mmsi", "Not found"),
                    "Flag": ship_history_div.get("data-flag-code", "Not found"),
                    "Country": ship_history_div.get("data-country", "Not found"),
                    "Company": ship_history_div.get("data-company", "Not found")
                }
            else:
                return {"error": "Ship history info not found on the page."}
        elif response.status_code == 403:
            print("403 Forbidden - Retrying with a new User-Agent...")
            time.sleep(random.randint(2, 5))  # Wait before retrying
        else:
            return {"error": f"Error: {response.status_code}"}

    return {"error": "Failed after multiple attempts (403 Forbidden)"}

@app.route('/get_vessel_info', methods=['POST'])
def get_vessel_info():
    data = request.json
    mmsi_number = data.get('mmsi', None)

    if not mmsi_number:
        return jsonify({"error": "MMSI number is required."}), 400

    search_url = generate_search_url(mmsi_number)

    # Use a session to persist cookies and headers
    session = requests.Session()

    headers = {'User-Agent': random.choice(USER_AGENTS)}
    proxy = random.choice(PROXIES) if PROXIES else None
    proxies = {"http": proxy, "https": proxy} if proxy else None

    response = session.get(search_url, headers=headers, proxies=proxies, allow_redirects=True)

    if response.status_code == 200:
        vessel_info = scrape_vessel_info(response.url, session)
        return jsonify(vessel_info)
    else:
        return jsonify({"error": f"Error accessing the search URL: {response.status_code}"}), 400

if __name__ == '__main__':
    app.run(debug=True)
