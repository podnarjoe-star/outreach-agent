import os
import json
import urllib.request
from urllib.error import HTTPError

def send_email(to, subject, body):
    try:
        api_key = os.environ.get("SENDGRID_API_KEY")
        from_email = os.environ.get("ZOHO_EMAIL", "joe@tailoredbusiness.app")

        if not api_key:
            raise Exception("SendGrid API key is missing. Please add SENDGRID_API_KEY in Railway variables.")

        data = {
            "personalizations": [{"to": [{"email": to}]}],
            "from": {"email": from_email},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}]
        }

        req = urllib.request.Request(
            "https://api.sendgrid.com/v3/mail/send",
            data=json.dumps(data).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )

        with urllib.request.urlopen(req) as response:
            return response.status

    except HTTPError as e:
        raise Exception(f"SendGrid error {e.code}: Check your API key and sender verification.")
    except Exception as e:
        raise Exception(f"Failed to send email: {str(e)}")

def get_gmail_service():
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        token_json = os.environ.get("GMAIL_TOKEN")
        if not token_json:
            raise Exception("GMAIL_TOKEN is missing from Railway variables.")

        creds_data = json.loads(token_json)
        creds = Credentials(
            token=creds_data["token"],
            refresh_token=creds_data["refresh_token"],
            token_uri=creds_data["token_uri"],
            client_id=creds_data["client_id"],
            client_secret=creds_data["client_secret"],
            scopes=creds_data["scopes"]
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return build("gmail", "v1", credentials=creds)

    except Exception as e:
        raise Exception(f"Failed to connect to Gmail: {str(e)}")