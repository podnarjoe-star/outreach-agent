import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("anthropic_api_key"))

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

def draft_followup_email(business_name, business_type, followup_number):
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Draft a short friendly follow-up email to a beauty/wellness business that hasn't responded to our first outreach.

Business Name: {business_name}
Business Type: {business_type}
This is follow-up number {followup_number}.

- Keep it under 100 words
- Be friendly, not pushy
- Reference that we reached out before
- End with a simple call to action

Return only the email body, no subject line."""
            }
        ]
    )
    return message.content[0].text