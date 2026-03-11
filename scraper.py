import re
import requests
from bs4 import BeautifulSoup

def scrape_email(website):
    try:
        if not website:
            return None

        # Make sure URL has http
        if not website.startswith("http"):
            website = "https://" + website

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        response = requests.get(website, headers=headers, timeout=8)
        soup = BeautifulSoup(response.text, "html.parser")

        # Look for mailto links first
        for tag in soup.find_all("a", href=True):
            href = tag["href"]
            if href.startswith("mailto:"):
                email = href.replace("mailto:", "").split("?")[0].strip()
                if email and "@" in email:
                    return email

        # Fall back to regex search in page text
        text = soup.get_text()
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        
        # Filter out common false positives
        excluded = ["example.com", "sentry.io", "wix.com", "squarespace.com",
                    "wordpress.com", "shopify.com", "gmail.com", "yahoo.com"]
        
        for email in emails:
            if not any(domain in email for domain in excluded):
                return email

        return None

    except Exception as e:
        print(f"Scrape failed for {website}: {str(e)}")
        return None