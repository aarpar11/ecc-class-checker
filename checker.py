import os
import requests
from playwright.sync_api import sync_playwright

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
COURSE_URL = "https://selfservice.elgin.edu:8173/Student/Courses/Search?keyword=SPN-101"
COURSE_CODE = "SPN-101"

# Pulls the webhook safely from GitHub Secrets
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")


def send_discord_notification(course_name, message_text):
    """Sends an embedded alert to your Discord channel."""
    if not DISCORD_WEBHOOK_URL:
        print("❌ Error: DISCORD_WEBHOOK secret is not set.")
        return

    payload = {
        "content": "@everyone 🚨 **Class Spot Alert!**",
        "embeds": [
            {
                "title": f"Open Spot Found for {course_name}!",
                "description": (
                    f"Status: {message_text}\n\n"
                    "[Click here to log into AccessECC and Register](https://www.elgin.edu/accessecc)"
                ),
                "color": 5814783  # Purple/Cyan highlight
            }
        ]
    }
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code in [200, 204]:
            print("✅ Discord alert sent successfully!")
        else:
            print(f"⚠️ Discord API returned status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to send Discord message: {e}")


def check_course_status():
    print(f"🔍 Checking availability for {COURSE_CODE} on public Self-Service...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(COURSE_URL, wait_until="networkidle", timeout=30000)
            page.wait_for_selector(".esg-section", timeout=10000)
            content = page.content()
            
            if "Seats Available" in content or "Open" in content:
                print("🎉 Potential spot detected!")
                send_discord_notification(
                    COURSE_CODE, 
                    "A seat appears to be available! Log into AccessECC immediately to claim it."
                )
            else:
                print("🔒 Section is currently full or waitlisted.")
                
        except Exception as e:
            print(f"⚠️ Error checking course page: {e}")
        finally:
            browser.close()


if __name__ == "__main__":
    check_course_status()
