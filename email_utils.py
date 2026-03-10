import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to, subject, body):
    email = os.environ.get("ZOHO_EMAIL")
    password = os.environ.get("ZOHO_PASSWORD")
    
    msg = MIMEMultipart()
    msg["From"] = email
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    
    with smtplib.SMTP("smtp.zoho.com", 587) as server:
        server.starttls()
        server.login(email, password)
        server.sendmail(email, to, msg.as_string())

def get_gmail_service():
    import json
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    
    token_json = os.environ.get("GMAIL_TOKEN")
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