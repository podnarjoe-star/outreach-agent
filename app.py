import os
import anthropic
from flask import Flask, request, render_template_string
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
api_key = os.getenv("ANTHROPIC_API_KEY")
print(f"API KEY FOUND: {bool(api_key)}")
client = anthropic.Anthropic(api_key=api_key)

FORM_PAGE = """
<!DOCTYPE html>
<html>
<head><title>Outreach Agent</title></head>
<body style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px;">
    <h2>Draft Outreach Email</h2>
    <form method="POST" action="/draft">
        <label>Business Name:</label><br>
        <input type="text" name="business_name" style="width:100%; padding:8px; margin:8px 0;"><br>
        <label>Business Website:</label><br>
        <input type="text" name="business_website" style="width:100%; padding:8px; margin:8px 0;"><br>
        <label>Business Type:</label><br>
        <input type="text" name="business_type" placeholder="e.g. hair salon, spa, esthetician" style="width:100%; padding:8px; margin:8px 0;"><br>
        <button type="submit" style="padding:10px 20px; background:#4CAF50; color:white; border:none; cursor:pointer;">Draft Email</button>
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
        <label>To: {{ business_email }}</label><br><br>
        <label>Email Body:</label><br>
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
    <p>Your outreach email to {{ business_name }} has been sent successfully.</p>
    <a href="/">Draft another email</a>
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
    
    return render_template_string(DRAFT_PAGE, 
                                   email_body=email_body,
                                   business_name=business_name,
                                   business_email=business_email)

@app.route("/approve", methods=["POST"])
def approve():
    business_name = request.form["business_name"]
    return render_template_string(SENT_PAGE, business_name=business_name)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
