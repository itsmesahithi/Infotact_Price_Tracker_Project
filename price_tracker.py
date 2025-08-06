import requests
from bs4 import BeautifulSoup
import json
import smtplib
from email.message import EmailMessage
import schedule
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get environment variables
URL = os.getenv("PRODUCT_URL")
threshold_str = os.getenv("PRICE_THRESHOLD")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

# Check for missing environment variables
if not all([URL, threshold_str, EMAIL_USER, EMAIL_PASS, EMAIL_TO]):
    raise ValueError("Missing one or more required environment variables. Check your .env file.")

# Convert to float safely
try:
    PRICE_THRESHOLD = float(threshold_str)
except ValueError:
    raise ValueError("PRICE_THRESHOLD must be a numeric value.")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_product_data():
    try:
        response = requests.get(URL, headers=HEADERS)
        soup = BeautifulSoup(response.content, "html.parser")

        title_tag = soup.find("h1")
        price_tag = soup.find("p", class_="price_color")

        if not title_tag:
            raise ValueError("Product title not found.")
        if not price_tag:
            raise ValueError("Product price not found.")

        title = title_tag.get_text(strip=True)
        price_str = price_tag.get_text(strip=True).replace("£", "")
        price = float(price_str)

        return {"title": title, "price": price, "url": URL}

    except Exception as e:
        print(f"[Error] Failed to fetch product data: {e}")
        return None

def send_email_alert(title, price, url):
    """Sends an email alert."""
    try:
        msg = EmailMessage()
        msg['Subject'] = f"Price Alert: {title}"
        msg['From'] = EMAIL_USER
        msg['To'] = EMAIL_TO
        msg.set_content(f"Price dropped to ₹{price}!\nCheck the product here: {url}")

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg)
            print("[Success] Email alert sent!")

    except Exception as e:
        print(f"[Error] Failed to send email: {e}")

def check_price():
    product = fetch_product_data()
    if product:  # Only save if data is valid
        print(f"[Info] Current price of '{product['title']}': ₹{product['price']}")
        save_data(product)

        if product['price'] <= PRICE_THRESHOLD:
            send_email_alert(product["title"], product["price"], product["url"])
    else:
        print("[Warning] Product data not fetched. Skipping save.")
        
def save_data(data, filename="data.json"):
    try:
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        print("[Info] data.json saved.")
    except Exception as e:
        print(f"[Error] Failed to save data: {e}")

# Schedule to run every day at 8 AM
schedule.every().day.at("08:00").do(check_price)

if __name__ == "__main__":
    print("[Info] Price Tracker Started. Monitoring...")
    check_price()  # Initial check
    while True:
        schedule.run_pending()
        time.sleep(60)