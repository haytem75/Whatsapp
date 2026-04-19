"""
WhatsApp Group Message Reader
==============================
How it works:
  1. Opens WhatsApp Web in Chrome
  2. You scan the QR code once (session is saved for next time)
  3. The script opens your group and prints every message + who sent it
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


# ── CONFIGURE THIS ─────────────────────────────────────────────────────────────
GROUP_NAME = "My Group Name"   # <-- Replace with the exact name of your group
# ──────────────────────────────────────────────────────────────────────────────


class WhatsAppReader:

    def __init__(self):
        options = webdriver.ChromeOptions()

        # Save the login session to a local folder.
        # This means you only need to scan the QR code once — future runs skip it.
        options.add_argument("--user-data-dir=./chrome_session")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Automatically download and use the correct ChromeDriver version
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options,
        )

        # Default wait time for elements to appear (in seconds)
        self.wait = WebDriverWait(self.driver, 60)

    # ── STEP 1: Login ──────────────────────────────────────────────────────────

    def login(self):
        """Open WhatsApp Web and wait until you are logged in."""
        print("Opening WhatsApp Web...")
        self.driver.get("https://web.whatsapp.com")
        print("Waiting for login — scan the QR code if prompted (60 sec timeout)...")

        # We know we're logged in when the chat list appears on the left
        self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="chat-list"]'))
        )
        print("Logged in successfully!\n")

    # ── STEP 2: Open the Group ─────────────────────────────────────────────────

    def open_group(self, group_name: str):
        """Search for and open a WhatsApp group by its exact name."""
        print(f"Searching for group: '{group_name}'...")

        # Click the search box at the top-left of WhatsApp Web
        search_box = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="chat-list-search"]'))
        )
        search_box.click()
        search_box.send_keys(group_name)

        time.sleep(2)  # Wait for search results to appear

        # Click the group in the results list (matches by exact title)
        group_item = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, f'//span[@title="{group_name}"]'))
        )
        group_item.click()

        time.sleep(2)  # Wait for the chat messages to load
        print(f"Opened group: '{group_name}'\n")

    # ── STEP 3: Read Messages ──────────────────────────────────────────────────

    def read_messages(self):
        """
        Print all visible messages and their senders.

        WhatsApp Web stores sender + timestamp in a 'data-pre-plain-text' attribute
        on each message bubble. Its format looks like:
            "[07:30, 13/04/2026] John Doe: "
        We parse that to extract the sender's name.
        """
        print("Reading messages...\n")
        print("=" * 60)

        # Select every message element that has text (identified by data-pre-plain-text)
        messages = self.driver.find_elements(By.CSS_SELECTOR, "[data-pre-plain-text]")

        if not messages:
            print("No messages found. Make sure the group name is correct.")
        else:
            for msg in messages:
                sender = self._parse_sender(msg)
                text   = self._get_text(msg)
                if text:
                    print(f"[{sender}]  {text}")

        print("=" * 60)
        print(f"\nTotal messages shown: {len(messages)}")

    # ── Helper: extract sender name ────────────────────────────────────────────

    def _parse_sender(self, msg_element) -> str:
        """
        Pull the sender name out of the data-pre-plain-text attribute.

        Attribute value example:  "[07:30, 13/04/2026] Alice: "
        We split on "] " to drop the timestamp, then drop the trailing ": ".
        """
        raw = msg_element.get_attribute("data-pre-plain-text") or ""

        if "] " in raw:
            after_bracket = raw.split("] ", 1)[1]   # e.g. "Alice: "
            sender = after_bracket.rsplit(": ", 1)[0]  # e.g. "Alice"
            return sender.strip()

        return "Unknown"

    # ── Helper: extract message text ───────────────────────────────────────────

    def _get_text(self, msg_element) -> str:
        """Get the plain text content of a message bubble."""
        try:
            span = msg_element.find_element(By.CSS_SELECTOR, "span.selectable-text")
            return span.text.strip()
        except Exception:
            return ""  # Not a text message (e.g. image, sticker)

    # ── Cleanup ────────────────────────────────────────────────────────────────

    def close(self):
        """Close the Chrome browser."""
        self.driver.quit()
        print("Browser closed.")


# ── MAIN ───────────────────────────────────────────────────────────────────────

def main():
    reader = WhatsAppReader()
    try:
        reader.login()                    # Step 1 — log in via QR code (or saved session)
        reader.open_group(GROUP_NAME)     # Step 2 — open the group
        reader.read_messages()            # Step 3 — print all messages with sender names
    finally:
        input("\nPress Enter to close the browser...")
        reader.close()


if __name__ == "__main__":
    main()
