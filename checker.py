import os
import requests
from playwright.sync_api import sync_playwright

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
# Search URL specifically targeting PHY 211
COURSE_URL = "https://selfservice.elgin.edu:8173/Student/Courses/Search?keyword=PHY-211"
COURSE_CODE = "PHY-211"
INSTRUCTOR_NAME = "Eltzroth"  # Filtering for Professor Eltzroth

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")


def send_discord_notification(course_name, details):
    """Sends an embedded alert to your Discord channel."""
    if not DISCORD_WEBHOOK_URL:
        print("❌ Error: DISCORD_WEBHOOK secret is not set.")
        return

    payload = {
        "content": "@everyone 🚨 **Physics Class Spot Alert!**",
        "embeds": [
            {
                "title": f"Open Spot Found for {course_name}!",
                "description": (
                    f"{details}\n\n"
                    "[Click here to log into AccessECC and Register](https://www.elgin.edu/accessecc)"
                ),
                "color": 3447003  # Blue highlight
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
    print(f"🔍 Checking PHY-211 sections for Instructor: {INSTRUCTOR_NAME}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Navigate to the public course search
            page.goto(COURSE_URL, wait_until="networkidle", timeout=30000)
            
            # Wait for search results container to populate
            page.wait_for_selector(".esg-section", timeout=15000)
            
            # Locate all individual section cards on the page
            sections = page.query_selector_all(".esg-section")
            
            found_open_section = False

            for section in sections:
                text = section.inner_text()
                
                # Check if this specific section belongs to Prof. Eltzroth
                if INSTRUCTOR_NAME.lower() in text.lower():
                    # Check seat availability status within this section card
                    if "Seats Available" in text or "Open" in text:
                        print(f"🎉 Open spot found in a section taught by {INSTRUCTOR_NAME}!")
                        send_discord_notification(
                            COURSE_CODE,
                            f"A seat opened in a PHY-211 section taught by **{INSTRUCTOR_NAME}**!"
                        )
                        found_open_section = True
                        break  # Stop checking once an open spot is found
            
            if not found_open_section:
                print(f"🔒 All PHY-211 sections for {INSTRUCTOR_NAME} are currently full.")
                
        except Exception as e:
            print(f"⚠️ Error checking course page: {e}")
        finally:
            browser.close()


if __name__ == "__main__":
    check_course_status()
