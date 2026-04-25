"""
WhatsApp Group Message Reader
==============================
How it works:
  1. Opens WhatsApp Web in Chrome
  2. You scan the QR code once (session is saved for next time)
  3. The script opens your group and prints every message + who sent it
"""

import time
import os
from shutil import which
from typing import Optional, Sequence
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from variables import (
    CHAT_LIST_SEARCH_SELECTOR,
    CHAT_LIST_SELECTOR,
    CHAT_LOAD_DELAY_SECONDS,
    CHROME_BINARY_PATH,
    CHROME_SESSION_DIR,
    DEFAULT_WAIT_TIMEOUT,
    GROUP_NAME,
    MESSAGE_SELECTOR,
    MESSAGE_SEPARATOR,
    MESSAGE_TEXT_SELECTOR,
    PRESS_ENTER_PROMPT,
    QR_LOGIN_WAIT_TIMEOUT,
    SEARCH_RESULTS_DELAY_SECONDS,
    WHATSAPP_WEB_URL,
)


class WhatsAppReader:

    LOGIN_READY_SELECTORS = (
        CHAT_LIST_SELECTOR,
        CHAT_LIST_SEARCH_SELECTOR,
        '#pane-side',
        '[aria-label="Chat list"]',
    )

    LOGIN_QR_SELECTORS = (
        'canvas[aria-label="Scan this QR code to link a device!"]',
        '[data-testid="qrcode"] canvas',
        '[data-ref] canvas',
    )

    CHAT_SEARCH_FALLBACK_SELECTORS = (
        CHAT_LIST_SEARCH_SELECTOR,
        'input[role="textbox"]',
        'input[placeholder="Search or start a new chat"]',
        'input[aria-label="Search or start a new chat"]',
        '[role="textbox"][contenteditable="true"]',
        '[contenteditable="true"][data-tab="3"]',
        '[aria-label="Search input textbox"]',
    )

    MESSAGE_CONTAINER_SELECTORS = (
        '#main',
        '[data-testid="conversation-panel-body"]',
        '[aria-label="Message list"]',
    )

    MESSAGE_TEXT_FALLBACK_SELECTORS = (
        MESSAGE_TEXT_SELECTOR,
        '[data-testid="msg-text"]',
        'div.copyable-text',
        'span[dir="auto"]',
    )

# ── SETUP ──────────────────────────────────────────────────────────────────
    # Sets up the WhatsApp reader — opens Chrome with a saved session so you don't have to scan the QR code every single time.
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.binary_location = self._resolve_browser_binary()

        # Save the login session to a local folder.
        # This means you only need to scan the QR code once — future runs skip it.
        options.add_argument(f"--user-data-dir={CHROME_SESSION_DIR}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Let Selenium resolve a compatible driver for the installed browser.
        self.driver = webdriver.Chrome(options=options)

        # Default wait time for elements to appear (in seconds)
        self.wait = WebDriverWait(self.driver, DEFAULT_WAIT_TIMEOUT)

    # Looks through a list of page elements and returns the first one that is actually visible on screen.

    # [sub of SETUP] Figures out where Chrome (or Chromium) is installed on your computer so we can open it.
    def _resolve_browser_binary(self) -> str:
        """Return a Chrome-compatible browser binary path or raise a setup error."""
        if CHROME_BINARY_PATH:
            return CHROME_BINARY_PATH

        windows_candidates = [
            os.path.join(
                os.environ.get("PROGRAMFILES", ""),
                "Google",
                "Chrome",
                "Application",
                "chrome.exe",
            ),
            os.path.join(
                os.environ.get("PROGRAMFILES(X86)", ""),
                "Google",
                "Chrome",
                "Application",
                "chrome.exe",
            ),
            os.path.join(
                os.environ.get("LOCALAPPDATA", ""),
                "Google",
                "Chrome",
                "Application",
                "chrome.exe",
            ),
            os.path.join(
                os.environ.get("PROGRAMFILES", ""),
                "Chromium",
                "Application",
                "chrome.exe",
            ),
            os.path.join(
                os.environ.get("PROGRAMFILES(X86)", ""),
                "Chromium",
                "Application",
                "chrome.exe",
            ),
            os.path.join(
                os.environ.get("LOCALAPPDATA", ""),
                "Chromium",
                "Application",
                "chrome.exe",
            ),
        ]

        for binary_path in windows_candidates:
            if binary_path and os.path.exists(binary_path):
                return binary_path

        for binary_name in (
            "google-chrome",
            "google-chrome-stable",
            "chromium",
            "chromium-browser",
        ):
            binary_path = which(binary_name)
            if binary_path:
                return binary_path

        raise RuntimeError(
            "Chrome or Chromium is not installed. Install Google Chrome/Chromium "
            "or set CHROME_BINARY_PATH in variables.py to the browser executable."
        )

    # ── Initialization ─────────────────────────────────────────────────────────
    # Sets up the WhatsApp reader — opens Chrome with a saved session so you don't have to scan the QR code every single time.

    # ── STEP 1: Login ──────────────────────────────────────────────────────────
    # Opens WhatsApp Web in Chrome and waits for you to scan the QR code — or skips it if you already logged in before.
    def login(self):
        """Open WhatsApp Web and wait until you are logged in."""
        print("Opening WhatsApp Web...")
        self.driver.get(WHATSAPP_WEB_URL)
        print(
            f"Waiting for login — scan the QR code if prompted ({DEFAULT_WAIT_TIMEOUT} sec timeout)..."
        )

        try:
            self._wait_for_any_visible(
                self.LOGIN_READY_SELECTORS + self.LOGIN_QR_SELECTORS,
                timeout=DEFAULT_WAIT_TIMEOUT,
            )
        except TimeoutException as exc:
            raise TimeoutException(
                f"Timed out waiting for WhatsApp login. {self._describe_login_state()}"
            ) from exc

        if self._find_first_visible(self.LOGIN_QR_SELECTORS):
            print(
                "QR code detected. Waiting for you to finish login "
                f"({QR_LOGIN_WAIT_TIMEOUT} sec timeout)..."
            )
            try:
                self._wait_for_any_visible(
                    self.LOGIN_READY_SELECTORS,
                    timeout=QR_LOGIN_WAIT_TIMEOUT,
                )
            except TimeoutException as exc:
                raise TimeoutException(
                    "Timed out waiting for WhatsApp login after QR detection. "
                    "Scan the QR code and keep the browser window open until the chat list loads."
                ) from exc

        print("Logged in successfully!\n")

    # ── STEP 2: Open the Group ─────────────────────────────────────────────────
    # Types the group name into the WhatsApp search box and clicks on it to open that chat.

    # [sub of STEP 1, 2 & 3] Looks through a list of page elements and returns the first one that is actually visible on screen.
    def _find_first_visible(self, selectors: Sequence[str]):
        """Return the first visible element that matches any selector."""
        for selector in selectors:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                if element.is_displayed():
                    return element
        return None

    # Keeps checking the page until at least one of the listed things shows up, or gives up after a time limit.

    # [sub of STEP 1, 2 & 3] Keeps checking the page until at least one of the listed things shows up, or gives up after a time limit.
    def _wait_for_any_visible(self, selectors: Sequence[str], timeout: Optional[int] = None):
        """Wait until any selector resolves to a visible element."""
        wait = WebDriverWait(self.driver, timeout or DEFAULT_WAIT_TIMEOUT)
        return wait.until(lambda driver: self._find_first_visible(selectors))

    # Clears whatever is already typed in the search box and types in a new search word.

    # [sub of STEP 1 - login] Checks what the login page looks like right now and returns a helpful message explaining what went wrong.
    def _describe_login_state(self) -> str:
        """Provide a short page-state summary for login failures."""
        if self._find_first_visible(self.LOGIN_READY_SELECTORS):
            return "WhatsApp Web loaded, but the expected chat UI selector changed."
        if self._find_first_visible(self.LOGIN_QR_SELECTORS):
            return "WhatsApp Web is waiting for a QR code scan."
        return "WhatsApp Web did not expose a recognized login or chat-list element."

    # ── STEP 1: Login ──────────────────────────────────────────────────────────
    # Opens WhatsApp Web in Chrome and waits for you to scan the QR code — or skips it if you already logged in before.

    # ── STEP 2: Open the Group ─────────────────────────────────────────────────
    # Types the group name into the WhatsApp search box and clicks on it to open that chat.
    def open_group(self, group_name: str):
        """Search for and open a WhatsApp group by its exact name."""
        print(f"Searching for group: '{group_name}'...")

        # Click the search box at the top-left of WhatsApp Web
        search_box = self._wait_for_any_visible(self.CHAT_SEARCH_FALLBACK_SELECTORS)
        search_box.click()
        self._replace_search_text(search_box, group_name)

        time.sleep(SEARCH_RESULTS_DELAY_SECONDS)  # Wait for search results to appear

        # Click the group in the results list (matches by exact title)
        group_item = self.wait.until(lambda driver: self._find_chat_result(group_name))
        group_item.click()

        time.sleep(CHAT_LOAD_DELAY_SECONDS)  # Wait for the chat messages to load
        print(f"Opened group: '{group_name}'\n")

    # ── STEP 3: Read Messages ──────────────────────────────────────────────────
    # Goes through every visible message in the chat and prints who sent it and what they wrote.

    # [sub of STEP 2 - open_group] Clears whatever is already typed in the search box and types in a new search word.
    def _replace_search_text(self, element, value: str):
        """Replace any existing search text in the active WhatsApp search box."""
        element.send_keys(Keys.CONTROL, "a")
        element.send_keys(Keys.DELETE)
        element.send_keys(value)

    # Searches the page for a chat item whose title matches the group name you gave it.

    # [sub of STEP 2 - open_group] Searches the page for a chat item whose title matches the group name you gave it.
    def _find_chat_result(self, group_name: str):
        """Return the first clickable chat result that matches the group name."""
        result_xpaths = (
            f'//span[@title="{group_name}"]',
            f'//*[@title="{group_name}"]',
            f'//span[normalize-space()="{group_name}"]',
            f'//*[@aria-label="{group_name}"]',
        )

        for xpath in result_xpaths:
            matches = self.driver.find_elements(By.XPATH, xpath)
            for match in matches:
                if match.is_displayed():
                    return match
        return None

    # Finds the big box on the page that holds all the chat messages.

    # ── STEP 3: Read Messages ──────────────────────────────────────────────────
    # Goes through every visible message in the chat and prints who sent it and what they wrote.
    def read_messages(self):
        """
        Print all visible messages and their senders.

        WhatsApp Web stores sender + timestamp in a 'data-pre-plain-text' attribute
        on each message bubble. Its format looks like:
            "[07:30, 13/04/2026] John Doe: "
        We parse that to extract the sender's name.
        """
        print("Reading messages...\n")
        print(MESSAGE_SEPARATOR)

        messages = self._find_message_elements()
        printed_messages = 0
        seen_messages = set()

        if not messages:
            print("No messages found. Make sure the group name is correct.")
        else:
            for msg in messages:
                sender = self._parse_sender(msg)
                text = self._get_text(msg)
                if text:
                    message_key = (sender, text)
                    if message_key in seen_messages:
                        continue

                    seen_messages.add(message_key)
                    printed_messages += 1
                    print(f"[{sender}]  {text}")

            print(MESSAGE_SEPARATOR)
        print(f"\nTotal messages shown: {printed_messages}")

    # ── Helper: extract sender name ────────────────────────────────────────────
    # Reads the hidden label WhatsApp puts on each message bubble to figure out who sent it.

    # [sub of STEP 3 - read_messages] Collects every visible message bubble in the open chat and returns them as a list.
    def _find_message_elements(self):
        """Return visible message-like elements from the current conversation."""
        container = self._get_message_container()
        selectors = (
            '[data-pre-plain-text]',
            'div[role="row"]',
            '[data-testid="msg-container"]',
        )
        elements = []
        seen = set()

        for selector in selectors:
            for element in container.find_elements(By.CSS_SELECTOR, selector):
                if not element.is_displayed():
                    continue

                element_id = element.id
                if element_id in seen:
                    continue

                seen.add(element_id)
                elements.append(element)

        return elements

    # Cleans up a message by removing extra blank lines and squishing extra spaces into one.

    # [sub of _find_message_elements] Finds the big box on the page that holds all the chat messages.
    def _get_message_container(self):
        """Return the active conversation container."""
        return self._wait_for_any_visible(self.MESSAGE_CONTAINER_SELECTORS)

    # Collects every visible message bubble in the open chat and returns them as a list.

    # [sub of STEP 3 - read_messages] Reads the hidden label WhatsApp puts on each message bubble to figure out who sent it.
    def _parse_sender(self, msg_element) -> str:
        """
        Pull the sender name out of the data-pre-plain-text attribute.

        Attribute value example:  "[07:30, 13/04/2026] Alice: "
        We split on "] " to drop the timestamp, then drop the trailing ": ".
        """
        raw = msg_element.get_attribute("data-pre-plain-text") or ""

        if not raw:
            try:
                container = msg_element.find_element(
                    By.XPATH,
                    './ancestor-or-self::*[@data-pre-plain-text][1]',
                )
                raw = container.get_attribute("data-pre-plain-text") or ""
            except Exception:
                raw = ""

        if "] " in raw:
            after_bracket = raw.split("] ", 1)[1]   # e.g. "Alice: "
            sender = after_bracket.rsplit(": ", 1)[0]  # e.g. "Alice"
            return sender.strip()

        return "Unknown"

    # ── Helper: extract message text ───────────────────────────────────────────
    # Gets the actual words from a message bubble and throws away anything that looks like junk.

    # [sub of STEP 3 - read_messages] Gets the actual words from a message bubble and throws away anything that looks like junk.
    def _get_text(self, msg_element) -> str:
        """Get the plain text content of a message bubble."""
        candidates = self._extract_text_candidates(msg_element)
        if candidates:
            return max(candidates, key=len)

        text = self._normalize_message_text(msg_element.text)
        if not text:
            return ""

        if text in {"Message", "Type a message", "Search"}:
            return ""

        return text

    # ── Cleanup ────────────────────────────────────────────────────────────────
    # Shuts down the Chrome browser when we are completely done reading messages.

   # [sub of _get_text] Tries several different ways to grab the text out of a message bubble so we don't miss anything.
    def _extract_text_candidates(self, msg_element):
        """Collect text candidates from known message text nodes."""
        candidates = []
        seen = set()

        for selector in self.MESSAGE_TEXT_FALLBACK_SELECTORS:
            for node in msg_element.find_elements(By.CSS_SELECTOR, selector):
                text = self._normalize_message_text(node.text)
                if not text or text in seen:
                    continue

                seen.add(text)
                candidates.append(text)

        return candidates

    # Checks what the login page looks like right now and returns a helpful message explaining what went wrong.

    # [sub of _extract_text_candidates] Cleans up a message by removing extra blank lines and squishing extra spaces into one.
    def _normalize_message_text(self, text: str) -> str:
        """Collapse repeated whitespace while preserving message readability."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return " ".join(lines).strip()

    # Tries several different ways to grab the text out of a message bubble so we don't miss anything.

    # ── CLEANUP ────────────────────────────────────────────────────────────────
    # Shuts down the Chrome browser when we are completely done reading messages.
    def close(self):
        """Close the Chrome browser."""
        self.driver.quit()
        print("Browser closed.")

# ── MAIN ───────────────────────────────────────────────────────────────────────

# The starting point of the whole program — runs login, opens the group, and reads the messages, one step at a time.
def main():
    reader = WhatsAppReader()
    try:
        reader.login()                    # Step 1 — log in via QR code (or saved session)
        reader.open_group(GROUP_NAME)     # Step 2 — open the group
        reader.read_messages()            # Step 3 — print all messages with sender names
    finally:
        input(PRESS_ENTER_PROMPT)
        reader.close()


if __name__ == "__main__":
    main()
