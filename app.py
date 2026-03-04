import os
import json
import base64
import anthropic
import mysql.connector
import requests
from flask import Flask, request, render_template_string, redirect, url_for
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from datetime import datetime, timedelta

app = Flask(__name__)
client = anthropic.Anthropic(api_key=os.environ.get("anthropic_api_key"))

def get_db():
    return mysql.connector.connect(
        host=os.environ.get("MYSQLHOST"),
        user=os.environ.get("MYSQLUSER"),
        password=os.environ.get("MYSQLPASSWORD"),
        database=os.environ.get("MYSQLDATABASE"),
        port=int(os.environ.get("MYSQLPORT", 3306))
    )

def init_db():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS businesses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            website VARCHAR(255),
            email VARCHAR(255),
            type VARCHAR(255),
            status VARCHAR(50) DEFAULT 'contacted',
            date_first_contacted DATE,
            date_last_contacted DATE,
            followup_due DATE,
            outreach_count INT DEFAULT 1,
            notes TEXT
        )
    """)
    db.commit()
    cursor.close()
    db.close()

def get_gmail_service():
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

def send_email(to, subject, body):
    service = get_gmail_service()
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()

FORM_PAGE = """
<!DOCTYPE html>
<html>
<head><title>Outreach Agent</title></head>
<body style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px;">
    <h2>Draft Outreach Email</h2>
    <a href="/dashboard" style="float:right;">View Dashboard</a>
    <form method="POST" action="/draft">
        <label>Business Name:</label><br>
        <input type="text" name="business_name" style="width:100%; padding:8px; margin:8px 0;"><br>
        <label>Business Website:</label><br>
        <input type="text" name="business_website" style="width:100%; padding:8px; margin:8px 0;"><br>
        <label>Business Type:</label><br>
        <input type="text" name="business_type" placeholder="e.g. hair salon, spa, esthetician" style="width:100%; padding:8px; margin:8px 0;"><br>
        <label>Business Email:</label><br>
        <input type="text" name="business_email" style="width:100%; padding:8px; margin:8px 0;"><br>
        <button type="submit" style="padding:10px 20px; background:#4CAF50; color:white; border:none; cursor:pointer;">Draft Email</button>
    </form>

    <hr style="margin: 40px 0;">

    <h2>Find Businesses</h2>
    <form method="POST" action="/find_businesses">
        <label>City:</label><br>
        <input type="text" name="city" placeholder="e.g. Cincinnati, OH" style="width:100%; padding:8px; margin:8px 0;"><br>
        <label>Business Type:</label><br>
        <input type="text" name="business_type" placeholder="e.g. hair salon, spa, esthetician" style="width:100%; padding:8px; margin:8px 0;"><br>
        <button type="submit" style="padding:10px 20px; background:#2196F3; color:white; border:none; cursor:pointer;">Find Businesses</button>
    </form>
</body>
</html>
"""

DRAFT_PAGE = """
<!DOCTYPE html>
<html>
<head><title>Review Draft</title></head>
<body style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px;">
    <h2>Review & Edit Draft</h2>
    <form method="POST" action="/approve">
        <input type="hidden" name="business_email" value="{{ business_email }}">
        <input type="hidden" name="business_name" value="{{ business_name }}">
        <input type="hidden" name="business_website" value="{{ business_website }}">
        <input type="hidden" name="business_type" value="{{ business_type }}">
        <label><strong>To:</strong> {{ business_email }}</label><br><br>
        <label><strong>Subject:</strong></label><br>
        <input type="text" name="subject" value="{{ subject }}" style="width:100%; padding:8px; margin:8px 0;"><br>
        <label><strong>Email Body:</strong></label><br>
        <textarea name="email_body" style="width:100%; height:300px; padding:8px; margin:8px 0;">{{ email_body }}</textarea><br>
        <button type="submit" style="padding:10px 20px; background:#4CAF50; color:white; border:none; cursor:pointer;">Send Email</button>
    </form>
</body>
</html>
"""

SENT_PAGE = """
<!DOCTYPE html>
<html>
<head><title>Sent!</title></head>
<body style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px;">
    <h2>Email Sent!</h2>
    <p>Your outreach email to <strong>{{ business_name }}</strong> has been sent successfully.</p>
    <p>Follow-up scheduled for 3 days from now if no response.</p>
    <a href="/">Draft another email</a> | <a href="/dashboard">View Dashboard</a>
</body>
</html>
"""

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html>
<head><title>Dashboard</title>
<style>
    body { font-family: Arial; max-width: 1000px; margin: 50px auto; padding: 20px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
    th { background: #f4f4f4; }
    .contacted { background: #fff9c4; }
    .responded { background: #c8e6c9; }
    .not_interested { background: #ffcdd2; }
    .converted { background: #bbdefb; }
    .followup-due { font-weight: bold; color: red; }
</style>
</head>
<body>
    <h2>Outreach Dashboard</h2>
    <a href="/">+ New Outreach</a>
    <br><br>
    <table>
        <tr>
            <th>Business</th>
            <th>Type</th>
            <th>Email</th>
            <th>Status</th>
            <th>First Contacted</th>
            <th>Last Contacted</th>
            <th>Follow-up Due</th>
            <th>Outreach Count</th>
            <th>Update Status</th>
        </tr>
        {% for b in businesses %}
        <tr class="{{ b['status'] }}">
            <td><a href="{{ b['website'] }}" target="_blank">{{ b['name'] }}</a></td>
            <td>{{ b['type'] }}</td>
            <td>{{ b['email'] }}</td>
            <td>{{ b['status'] }}</td>
            <td>{{ b['date_first_contacted'] }}</td>
            <td>{{ b['date_last_contacted'] }}</td>
            <td class="{{ 'followup-due' if b['followup_due'] and b['followup_due'] <= today else '' }}">{{ b['followup_due'] }}</td>
            <td>{{ b['outreach_count'] }}</td>
            <td>
                <form method="POST" action="/update_status">
                    <input type="hidden" name="business_id" value="{{ b['id'] }}">
                    <select name="status">
                        <option value="contacted" {{ 'selected' if b['status'] == 'contacted' }}>Contacted</option>
                        <option value="responded" {{ 'selected' if b['status'] == 'responded' }}>Responded</option>
                        <option value="not_interested" {{ 'selected' if b['status'] == 'not_interested' }}>Not Interested</option>
                        <option value="converted" {{ 'selected' if b['status'] == 'converted' }}>Converted</option>
                    </select>
                    <button type="submit">Update</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

def draft_outreach_email(business_name, business_website, business_type):
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are helping draft a personalized cold outreach email to a small beauty/wellness business.

Business Name: {business_name}
Business Website: {business_website}
Business Type: {business_type}

Draft a short, friendly, personalized outreach email introducing a service that creates a 24/7 online booking page for their clients.
- Keep it under 150 words
- Sound human, not salesy
- Reference something specific about their business
- End with a simple call to action

Return only the email body, no subject line."""
            }
        ]
    )
    return message.content[0].text

def search_places(city, business_type):
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    query = f"{business_type} in {city}"
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.websiteUri,places.formattedAddress,places.id"
    }
    data = {"textQuery": query}
    response = requests.post(url, headers=headers, json=data)
    print(f"Places API response: {response.json()}")
    results = response.json().get("places", [])
    businesses = []
    for place in results[:10]:
        name = place.get("displayName", {}).get("text", "")
        website = place.get("websiteUri", "")
        address = place.get("formattedAddress", "")
        businesses.append({
            "name": name,
            "address": address,
            "website": website,
            "type": business_type
        })
    return businesses

@app.route("/")
def index():
    return render_template_string(FORM_PAGE)

@app.route("/draft", methods=["POST"])
def draft():
    business_name = request.form["business_name"]
    business_website = request.form["business_website"]
    business_type = request.form["business_type"]
    business_email = request.form.get("business_email", "")
    email_body = draft_outreach_email(business_name, business_website, business_type)
    subject = f"Quick question for {business_name}"
    return render_template_string(DRAFT_PAGE,
                                   email_body=email_body,
                                   business_name=business_name,
                                   business_email=business_email,
                                   business_website=business_website,
                                   business_type=business_type,
                                   subject=subject)

@app.route("/approve", methods=["POST"])
def approve():
    business_name = request.form["business_name"]
    business_email = request.form["business_email"]
    business_website = request.form["business_website"]
    business_type = request.form["business_type"]
    email_body = request.form["email_body"]
    subject = request.form["subject"]
    send_email(business_email, subject, email_body)
    today = datetime.today().date()
    followup_due = today + timedelta(days=3)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO businesses (name, website, email, type, status, date_first_contacted, date_last_contacted, followup_due, outreach_count)
        VALUES (%s, %s, %s, %s, 'contacted', %s, %s, %s, 1)
    """, (business_name, business_website, business_email, business_type, today, today, followup_due))
    db.commit()
    cursor.close()
    db.close()
    return render_template_string(SENT_PAGE, business_name=business_name)

@app.route("/dashboard")
def dashboard():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM businesses ORDER BY followup_due ASC")
    businesses = cursor.fetchall()
    cursor.close()
    db.close()
    today = datetime.today().date()
    return render_template_string(DASHBOARD_PAGE, businesses=businesses, today=today)

@app.route("/check_followups")
def check_followups():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    today = datetime.today().date()
    cursor.execute("""
        SELECT * FROM businesses 
        WHERE status = 'contacted' 
        AND followup_due IS NOT NULL 
        AND followup_due <= %s
    """, (today,))
    businesses = cursor.fetchall()
    cursor.close()
    db.close()
    
    if not businesses:
        return "No follow-ups due today."
    
    for business in businesses:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"""Draft a short friendly follow-up email to a beauty/wellness business that hasn't responded to our first outreach.

Business Name: {business['name']}
Business Type: {business['type']}
This is follow-up number {business['outreach_count'] + 1}.

- Keep it under 100 words
- Be friendly, not pushy
- Reference that we reached out before
- End with a simple call to action

Return only the email body, no subject line."""
                }
            ]
        )
        followup_body = message.content[0].text
        subject = f"Following up - {business['name']}"
        
        # Send follow-up draft to YOU for approval
        approval_body = f"""A follow-up email is ready for your approval.

Business: {business['name']}
Email: {business['email']}
Subject: {subject}

--- DRAFT ---
{followup_body}
--- END DRAFT ---

To approve and send, visit:
https://outreach-agent-production.up.railway.app/approve_followup?id={business['id']}

"""
        send_email("podnarjoe@gmail.com", f"Follow-up ready for approval: {business['name']}", approval_body)
        
        # Update followup_due and outreach_count
        db = get_db()
        cursor = db.cursor()
        new_followup_due = today + timedelta(days=3)
        cursor.execute("""
            UPDATE businesses 
            SET followup_due = %s, outreach_count = outreach_count + 1, date_last_contacted = %s
            WHERE id = %s
        """, (new_followup_due, today, business["id"]))
        db.commit()
        cursor.close()
        db.close()

    return f"Follow-up emails sent for approval for {len(businesses)} businesses."


@app.route("/approve_followup")
def approve_followup():
    business_id = request.args.get("id")
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM businesses WHERE id = %s", (business_id,))
    business = cursor.fetchone()
    cursor.close()
    db.close()
    
    if not business:
        return "Business not found."
    
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Draft a short friendly follow-up email to a beauty/wellness business that hasn't responded to our first outreach.

Business Name: {business['name']}
Business Type: {business['type']}
This is follow-up number {business['outreach_count']}.

- Keep it under 100 words
- Be friendly, not pushy
- Reference that we reached out before
- End with a simple call to action

Return only the email body, no subject line."""
            }
        ]
    )
    followup_body = message.content[0].text
    subject = f"Following up - {business['name']}"
    
    return render_template_string(DRAFT_PAGE,
                                   email_body=followup_body,
                                   business_name=business["name"],
                                   business_email=business["email"],
                                   business_website=business["website"],
                                   business_type=business["type"],
                                   subject=subject)

@app.route("/check_replies")
def check_replies():
    service = get_gmail_service()
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM businesses WHERE status = 'contacted'")
    businesses = cursor.fetchall()
    updated = 0
    for business in businesses:
        if not business["email"]:
            continue
        query = f"from:{business['email']}"
        results = service.users().messages().list(userId="me", q=query).execute()
        messages = results.get("messages", [])
        if messages:
            cursor2 = db.cursor()
            cursor2.execute("UPDATE businesses SET status = 'responded' WHERE id = %s", (business["id"],))
            db.commit()
            cursor2.close()
            updated += 1
    cursor.close()
    db.close()
    return f"Checked replies. {updated} businesses updated to responded."

@app.route("/update_status", methods=["POST"])
def update_status():
    business_id = request.form["business_id"]
    status = request.form["status"]
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE businesses SET status = %s WHERE id = %s", (status, business_id))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("dashboard"))

@app.route("/find_businesses", methods=["POST"])
def find_businesses_route():
    city = request.form["city"]
    business_type = request.form["business_type"]
    businesses = search_places(city, business_type)
    db = get_db()
    cursor = db.cursor()
    added = 0
    for b in businesses:
        cursor.execute("SELECT id FROM businesses WHERE name = %s", (b["name"],))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO businesses (name, website, email, type, status, date_first_contacted, date_last_contacted, followup_due, outreach_count)
                VALUES (%s, %s, %s, %s, 'pending', NULL, NULL, NULL, 0)
            """, (b["name"], b["website"], "", b["type"]))
            added += 1
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("dashboard") + f"?found={added}&city={city}")

init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
