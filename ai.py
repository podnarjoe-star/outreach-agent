import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("anthropic_api_key"))

def draft_outreach_email(business_name, business_website, business_type):
    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"""Write a short cold outreach email to a small beauty or wellness business.

Use EXACTLY this format and do not deviate from it:

Hi [Name],

I help Hair Salons, Barber Shops and other businesses simplify the boring, repetitive stuff — so you can focus on clients instead of admin.

What's the one thing in your day-to-day that you wish you didn't have to deal with?

Joe

Rules:
- Replace [Name] with the actual business name: {business_name}
- Do not add any extra sentences, fluff, or pleasantries
- Do not mention the website or any specific details about their business
- Do not add a closing line like "looking forward to hearing from you"
- Return only the email body, no subject line"""
                }
            ]
        )
        return message.content[0].text
    except anthropic.AuthenticationError:
        raise Exception("Anthropic API key is invalid or expired. Please update it in Railway variables.")
    except anthropic.RateLimitError:
        raise Exception("Anthropic API rate limit reached. Please wait a moment and try again.")
    except Exception as e:
        raise Exception(f"Failed to draft email: {str(e)}")

def draft_followup_email(business_name, business_type, followup_number):
    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"""Write a short follow-up email to a beauty or wellness business that hasn't responded to our first email.

Use EXACTLY this format:

Hi [Name],

Quick thought — 47% of salon bookings happen while you're asleep or spending time with family.

If you're not set up to capture those, you're likely losing clients to whoever is.

Still curious what's taking up most of your time — worth a quick chat?

Joe

Rules:
- Replace [Name] with the actual business name: {business_name}
- Do not change any of the wording above
- Do not add extra sentences or fluff
- Return only the email body, no subject line"""
                }
            ]
        )
        return message.content[0].text
    except anthropic.AuthenticationError:
        raise Exception("Anthropic API key is invalid or expired. Please update it in Railway variables.")
    except anthropic.RateLimitError:
        raise Exception("Anthropic API rate limit reached. Please wait a moment and try again.")
    except Exception as e:
        raise Exception(f"Failed to draft follow-up email: {str(e)}")