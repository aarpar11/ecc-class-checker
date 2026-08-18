import os
import requests
from playwright.sync_api import sync_playwright


# Configuration

COURSE_URL = "https://selfservice.elgin.edu:8173/Student/Courses/Search?keyword=PHY-211"
COURSE_CODE = "PHY-211"
INSTRUCTOR_NAME = "Eltzroth"

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")


def discNotif(course_name, details, is_open=True):
    """Sends an alert to discord"""
    if not DISCORD_WEBHOOK_URL:
        print("Error: DISCORD_WEBHOOK secret is not added")
        return

    # If open, ping @everyone with a loud color, if full, send quietly--aded
    content_tag = "@everyone **Class Spot Alert!**" if is_open else "**Class Status Update**"
    color_code = 3066993 if is_open else 10066329  # green if open, grey if full

    payload = {
        "content": content_tag,
        "embeds": [
            {
                "title": f"Status Update for {course_name} ({INSTRUCTOR_NAME})",
                "description": (
                    f"{details}\n\n"
                    "[Click here to check AccessECC](https://www.elgin.edu/accessecc)"
                ),
                "color": color_code
            }
        ]
    }
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code in [200, 204]:
            print("Discord status update sent successfully!")
        else:
            print(f"Discord API returned status code: {response.status_code}")
    except Exception as e:
        print(f"Failed to send Discord message: {e}")


def courseCheck():
    print(f"Checking PHY-211 sections for Instructor: {INSTRUCTOR_NAME}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(COURSE_URL, wait_until="networkidle", timeout=30000)
            page.wait_for_selector(".esg-section", timeout=15000)
            
            sections = page.query_selector_all(".esg-section")
            found_open_section = False

            for section in sections:
                text = section.inner_text()
# fix in cases w/ spanish
                if INSTRUCTOR_NAME.lower() in text.lower():
                    if "Seats Available" in text or "Open" in text:
                        print(f"Open spot found in a section taught by {INSTRUCTOR_NAME}!")
                        discNotif(
                            COURSE_CODE,
                            f"**A seat is OPEN** in a PHY-211 section taught by **{INSTRUCTOR_NAME}**!",
                            is_open=True
                        )
                        found_open_section = True
                        break

            if not found_open_section:
                print(f"All PHY-211 sections for {INSTRUCTOR_NAME} are currently full.")
                # Send notification when all sections remain full--fixed
                discNotif(
                    COURSE_CODE,
                    f"Checked sections for **{INSTRUCTOR_NAME}**. Currently **0 seats available**.",
                    is_open=False
                )
                
        except Exception as e:
            print(f"Error checking course page: {e}")
            discNotif(
                COURSE_CODE,
                f"Script ran into an error loading Self-Service: `{e}`",
                is_open=False
            )
        finally:
            browser.close()


if __name__ == "__main__":
    courseCheck()
