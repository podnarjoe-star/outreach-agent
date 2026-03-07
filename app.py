import os
from flask import Flask, request, render_template_string, redirect, url_for
from markupsafe import Markup
from datetime import datetime, timedelta
from database import get_db, init_db
from email_utils import get_gmail_service, send_email
from places import search_places
from ai import draft_outreach_email, draft_followup_email
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

STYLES = """
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700&family=Nunito+Sans:wght@300;400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
    --cream: #FAF7F2;
    --warm-white: #FFFDF9;
    --tan: #E8DDD0;
    --brown: #8B6F5C;
    --dark-brown: #3D2B1F;
    --accent: #C4956A;
    --accent-hover: #B07D52;
    --green: #5A8A6A;
    --green-light: #EAF2EC;
    --yellow-light: #FDF8E8;
    --red-light: #FDECEA;
    --blue-light: #EBF3FB;
    --purple-light: #F3EEF8;
    --text: #2C1A0E;
    --text-muted: #7A6255;
    --border: #E0D4C8;
    --shadow: 0 2px 12px rgba(61,43,31,0.08);
    --shadow-lg: 0 8px 32px rgba(61,43,31,0.12);
    --radius: 12px;
    --radius-sm: 8px;
}

body {
    font-family: 'Nunito Sans', sans-serif;
    background: var(--cream);
    color: var(--text);
    min-height: 100vh;
    line-height: 1.6;
}

.nav {
    background: var(--warm-white);
    border-bottom: 1px solid var(--border);
    padding: 0 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 64px;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 1px 8px rgba(61,43,31,0.06);
}

.nav-brand {
    font-family: 'Nunito', sans-serif;
    font-size: 22px;
    font-weight: 600;
    color: var(--dark-brown);
    text-decoration: none;
    letter-spacing: -0.3px;
}

.nav-brand span {
    color: var(--accent);
}

.nav-links {
    display: flex;
    gap: 8px;
    align-items: center;
}

.nav-link {
    font-size: 14px;
    font-weight: 500;
    color: var(--text-muted);
    text-decoration: none;
    padding: 8px 16px;
    border-radius: var(--radius-sm);
    transition: all 0.2s;
}

.nav-link:hover {
    background: var(--tan);
    color: var(--dark-brown);
}

.nav-link.active {
    background: var(--accent);
    color: white;
}

.container {
    max-width: 1100px;
    margin: 0 auto;
    padding: 40px 24px;
}

.container-sm {
    max-width: 620px;
    margin: 0 auto;
    padding: 40px 24px;
}

.page-header {
    margin-bottom: 32px;
}

.page-header h1 {
    font-family: 'Nunito', sans-serif;
    font-size: 32px;
    font-weight: 600;
    color: var(--dark-brown);
    letter-spacing: -0.5px;
    margin-bottom: 6px;
}

.page-header p {
    color: var(--text-muted);
    font-size: 15px;
}

.card {
    background: var(--warm-white);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 28px;
    box-shadow: var(--shadow);
    margin-bottom: 24px;
}

.card-title {
    font-family: 'Nunito', sans-serif;
    font-size: 18px;
    font-weight: 600;
    color: var(--dark-brown);
    margin-bottom: 20px;
    padding-bottom: 14px;
    border-bottom: 1px solid var(--border);
}

.form-group {
    margin-bottom: 18px;
}

label {
    display: block;
    font-size: 13px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}

input[type="text"], input[type="email"], textarea, select {
    width: 100%;
    padding: 11px 14px;
    border: 1.5px solid var(--border);
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-size: 15px;
    color: var(--text);
    background: var(--warm-white);
    transition: border-color 0.2s, box-shadow 0.2s;
    outline: none;
}

input[type="text"]:focus, input[type="email"]:focus, textarea:focus, select:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(196,149,106,0.12);
}

textarea {
    resize: vertical;
    min-height: 260px;
    line-height: 1.7;
}

.btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 12px 24px;
    border-radius: var(--radius-sm);
    font-family: 'DM Sans', sans-serif;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    border: none;
    transition: all 0.2s;
    text-decoration: none;
}

.btn-primary {
    background: var(--accent);
    color: white;
}

.btn-primary:hover {
    background: var(--accent-hover);
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(196,149,106,0.3);
}

.btn-secondary {
    background: var(--tan);
    color: var(--dark-brown);
}

.btn-secondary:hover {
    background: var(--border);
}

.btn-blue {
    background: #4A90C4;
    color: white;
}

.btn-blue:hover {
    background: #3A7AB0;
    transform: translateY(-1px);
}

.btn-sm {
    padding: 7px 14px;
    font-size: 13px;
}

.grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
}

.divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 32px 0;
}

/* Dashboard table */
.table-wrap {
    overflow-x: auto;
    border-radius: var(--radius);
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
}

table {
    width: 100%;
    border-collapse: collapse;
    background: var(--warm-white);
    font-size: 14px;
}

thead th {
    background: var(--dark-brown);
    color: rgba(255,255,255,0.85);
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 14px 16px;
    text-align: left;
    white-space: nowrap;
}

tbody tr {
    border-bottom: 1px solid var(--border);
    transition: background 0.15s;
}

tbody tr:last-child { border-bottom: none; }
tbody tr:hover { background: var(--cream); }

td {
    padding: 13px 16px;
    vertical-align: middle;
}

td a {
    color: var(--accent);
    text-decoration: none;
    font-weight: 500;
}

td a:hover { text-decoration: underline; }

.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    text-transform: capitalize;
}

.badge-contacted { background: var(--yellow-light); color: #8A6F00; }
.badge-responded { background: var(--green-light); color: #2D6A3F; }
.badge-not_interested { background: var(--red-light); color: #A33030; }
.badge-converted { background: var(--blue-light); color: #1A5C9A; }
.badge-pending { background: var(--purple-light); color: #5A3D8A; }

.followup-due { color: #C0392B; font-weight: 700; }

.status-select {
    padding: 5px 10px;
    font-size: 13px;
    border-radius: 6px;
    border: 1.5px solid var(--border);
    background: var(--warm-white);
    cursor: pointer;
}

.dashboard-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 12px;
}

.action-group {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.stats-row {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 16px;
    margin-bottom: 28px;
}

.stat-card {
    background: var(--warm-white);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 18px 20px;
    text-align: center;
}

.stat-number {
    font-family: 'Nunito', sans-serif;
    font-size: 28px;
    font-weight: 600;
    color: var(--dark-brown);
    line-height: 1;
    margin-bottom: 4px;
}

.stat-label {
    font-size: 12px;
    color: var(--text-muted);
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}

.success-icon {
    width: 64px;
    height: 64px;
    background: var(--green-light);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 20px;
    font-size: 28px;
}

.success-card {
    text-align: center;
    padding: 48px 28px;
}

.success-card h2 {
    font-family: 'Nunito', sans-serif;
    font-size: 26px;
    color: var(--dark-brown);
    margin-bottom: 10px;
}

.success-card p {
    color: var(--text-muted);
    margin-bottom: 6px;
}

.success-links {
    display: flex;
    gap: 12px;
    justify-content: center;
    margin-top: 28px;
}

.to-field {
    background: var(--cream);
    border: 1.5px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 11px 14px;
    font-size: 15px;
    color: var(--text-muted);
    margin-bottom: 18px;
}

.to-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}
"""

NAV = """
<nav class="nav">
    <a href="/" class="nav-brand">Outreach <span>Agent</span></a>
    <div class="nav-links">
        <a href="/" class="nav-link">New Outreach</a>
        <a href="/dashboard" class="nav-link">Dashboard</a>
        <a href="/check_replies" class="nav-link">Check Replies</a>
        <a href="/check_followups" class="nav-link">Check Follow-ups</a>
    </div>
</nav>
"""

FORM_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Outreach Agent</title>
<style>{{ styles }}</style>
</head>
<body>
{{ nav }}
<div class="container">
    <div class="page-header">
        <h1>Outreach Agent</h1>
        <p>Draft personalized emails or discover new businesses to contact.</p>
    </div>

    <div class="grid-2">
        <div class="card">
            <div class="card-title">✉️ Draft Outreach Email</div>
            <form method="POST" action="/draft">
                <div class="form-group">
                    <label>Business Name</label>
                    <input type="text" name="business_name" placeholder="e.g. Glow Studio">
                </div>
                <div class="form-group">
                    <label>Business Website</label>
                    <input type="text" name="business_website" placeholder="e.g. glowstudio.com">
                </div>
                <div class="form-group">
                    <label>Business Type</label>
                    <input type="text" name="business_type" placeholder="e.g. hair salon, spa, esthetician">
                </div>
                <div class="form-group">
                    <label>Business Email</label>
                    <input type="text" name="business_email" placeholder="e.g. hello@glowstudio.com">
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%; justify-content:center;">
                    Draft Email →
                </button>
            </form>
        </div>

        <div class="card">
            <div class="card-title">🔍 Find Businesses</div>
            <form method="POST" action="/find_businesses">
                <div class="form-group">
                    <label>City</label>
                    <input type="text" name="city" placeholder="e.g. Cincinnati, OH">
                </div>
                <div class="form-group">
                    <label>Business Type</label>
                    <input type="text" name="business_type" placeholder="e.g. hair salon, spa, esthetician">
                </div>
                <button type="submit" class="btn btn-blue" style="width:100%; justify-content:center; margin-top: 108px;">
                    Find Businesses →
                </button>
            </form>
        </div>
    </div>
</div>
</body>
</html>
"""

DRAFT_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Review Draft</title>
<style>{{ styles }}</style>
</head>
<body>
{{ nav }}
<div class="container-sm">
    <div class="page-header">
        <h1>Review & Edit Draft</h1>
        <p>Edit the email below then send when ready.</p>
    </div>
    <div class="card">
        <form method="POST" action="/approve">
            <input type="hidden" name="business_email" value="{{ business_email }}">
            <input type="hidden" name="business_name" value="{{ business_name }}">
            <input type="hidden" name="business_website" value="{{ business_website }}">
            <input type="hidden" name="business_type" value="{{ business_type }}">
            <div class="form-group">
                <div class="to-label">To</div>
                <div class="to-field">{{ business_email }}</div>
            </div>
            <div class="form-group">
                <label>Subject</label>
                <input type="text" name="subject" value="{{ subject }}">
            </div>
            <div class="form-group">
                <label>Email Body</label>
                <textarea name="email_body">{{ email_body }}</textarea>
            </div>
            <button type="submit" class="btn btn-primary" style="width:100%; justify-content:center;">
                Send Email →
            </button>
        </form>
    </div>
</div>
</body>
</html>
"""

SENT_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Email Sent</title>
<style>{{ styles }}</style>
</head>
<body>
{{ nav }}
<div class="container-sm">
    <div class="card success-card">
        <div class="success-icon">✓</div>
        <h2>Email Sent!</h2>
        <p>Your outreach email to <strong>{{ business_name }}</strong> has been sent.</p>
        <p style="font-size:13px; margin-top:8px;">A follow-up will be queued in 3 days if there's no response.</p>
        <div class="success-links">
            <a href="/" class="btn btn-secondary">New Outreach</a>
            <a href="/dashboard" class="btn btn-primary">View Dashboard</a>
        </div>
    </div>
</div>
</body>
</html>
"""

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard</title>
<style>{{ styles }}</style>
</head>
<body>
{{ nav }}
<div class="container">
    <div class="page-header">
        <h1>Outreach Dashboard</h1>
        <p>Track and manage all your business outreach in one place.</p>
    </div>

    <div class="stats-row">
        <div class="stat-card">
            <div class="stat-number">{{ total }}</div>
            <div class="stat-label">Total</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" style="color:#8A6F00;">{{ contacted }}</div>
            <div class="stat-label">Contacted</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" style="color:#2D6A3F;">{{ responded }}</div>
            <div class="stat-label">Responded</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" style="color:#1A5C9A;">{{ converted }}</div>
            <div class="stat-label">Converted</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" style="color:#5A3D8A;">{{ pending }}</div>
            <div class="stat-label">Pending</div>
        </div>
    </div>

    <div class="dashboard-actions">
        <div class="action-group">
            <a href="/" class="btn btn-primary btn-sm">+ New Outreach</a>
            <a href="/check_replies" class="btn btn-secondary btn-sm">Check Replies</a>
            <a href="/check_followups" class="btn btn-secondary btn-sm">Check Follow-ups</a>
        </div>
    </div>

    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>Business</th>
                    <th>Type</th>
                    <th>Email</th>
                    <th>Status</th>
                    <th>First Contacted</th>
                    <th>Last Contacted</th>
                    <th>Follow-up Due</th>
                    <th>Outreach #</th>
                    <th>Update</th>
                </tr>
            </thead>
            <tbody>
                {% for b in businesses %}
                <tr>
                    <td><a href="{{ b['website'] }}" target="_blank">{{ b['name'] }}</a></td>
                    <td>{{ b['type'] }}</td>
                    <td style="font-size:13px;">{{ b['email'] }}</td>
                    <td><span class="badge badge-{{ b['status'] }}">{{ b['status'] }}</span></td>
                    <td style="font-size:13px;">{{ b['date_first_contacted'] }}</td>
                    <td style="font-size:13px;">{{ b['date_last_contacted'] }}</td>
                    <td style="font-size:13px;" class="{{ 'followup-due' if b['followup_due'] and b['followup_due'] <= today else '' }}">
                        {{ b['followup_due'] or '—' }}
                    </td>
                    <td style="text-align:center;">{{ b['outreach_count'] }}</td>
                    <td>
                        <form method="POST" action="/update_status" style="display:flex; gap:6px; align-items:center;">
                            <input type="hidden" name="business_id" value="{{ b['id'] }}">
                            <select name="status" class="status-select">
                                <option value="pending" {{ 'selected' if b['status'] == 'pending' }}>Pending</option>
                                <option value="contacted" {{ 'selected' if b['status'] == 'contacted' }}>Contacted</option>
                                <option value="responded" {{ 'selected' if b['status'] == 'responded' }}>Responded</option>
                                <option value="not_interested" {{ 'selected' if b['status'] == 'not_interested' }}>Not Interested</option>
                                <option value="converted" {{ 'selected' if b['status'] == 'converted' }}>Converted</option>
                            </select>
                            <button type="submit" class="btn btn-secondary btn-sm">Save</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
</body>
</html>
"""

def render(template, **kwargs):
    return render_template_string(template, styles=STYLES, nav=Markup(NAV), **kwargs)

@app.route("/")
def index():
    return render(FORM_PAGE)

@app.route("/draft", methods=["POST"])
def draft():
    business_name = request.form["business_name"]
    business_website = request.form["business_website"]
    business_type = request.form["business_type"]
    business_email = request.form.get("business_email", "")
    email_body = draft_outreach_email(business_name, business_website, business_type)
    subject = f"Quick question for {business_name}"
    return render(DRAFT_PAGE,
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
    return render(SENT_PAGE, business_name=business_name)

@app.route("/dashboard")
def dashboard():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM businesses ORDER BY followup_due ASC")
    businesses = cursor.fetchall()
    cursor.close()
    db.close()
    today = datetime.today().date()
    total = len(businesses)
    contacted = sum(1 for b in businesses if b['status'] == 'contacted')
    responded = sum(1 for b in businesses if b['status'] == 'responded')
    converted = sum(1 for b in businesses if b['status'] == 'converted')
    pending = sum(1 for b in businesses if b['status'] == 'pending')
    return render(DASHBOARD_PAGE, businesses=businesses, today=today,
                  total=total, contacted=contacted, responded=responded,
                  converted=converted, pending=pending)

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
    return redirect(url_for("dashboard"))

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
        return redirect(url_for("dashboard"))
    for business in businesses:
        followup_body = draft_followup_email(business["name"], business["type"], business["outreach_count"] + 1)
        subject = f"Following up - {business['name']}"
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
    return redirect(url_for("dashboard"))

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
    followup_body = draft_followup_email(business["name"], business["type"], business["outreach_count"])
    subject = f"Following up - {business['name']}"
    return render(DRAFT_PAGE,
                  email_body=followup_body,
                  business_name=business["name"],
                  business_email=business["email"],
                  business_website=business["website"],
                  business_type=business["type"],
                  subject=subject)

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
    return redirect(url_for("dashboard"))

def scheduled_check_replies():
    with app.app_context():
        try:
            service = get_gmail_service()
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM businesses WHERE status = 'contacted'")
            businesses = cursor.fetchall()
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
            cursor.close()
            db.close()
            print("Scheduled reply check complete.")
        except Exception as e:
            print(f"Error in scheduled_check_replies: {e}")

def scheduled_check_followups():
    with app.app_context():
        try:
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
            for business in businesses:
                followup_body = draft_followup_email(business["name"], business["type"], business["outreach_count"] + 1)
                subject = f"Following up - {business['name']}"
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
            print(f"Scheduled followup check complete. {len(businesses)} businesses processed.")
        except Exception as e:
            print(f"Error in scheduled_check_followups: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_check_replies, 'interval', hours=1)
scheduler.add_job(scheduled_check_followups, 'cron', hour=9, minute=0)
scheduler.start()

init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)