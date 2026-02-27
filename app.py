import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

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

if __name__ == "__main__":
    business_name = input("Business name: ")
    business_website = input("Business website: ")
    business_type = input("Business type (e.g. hair salon, spa, esthetician): ")
    
    print("\nDrafting email...\n")
    email = draft_outreach_email(business_name, business_website, business_type)
    print(email)