"""Centralized configuration values for the WhatsApp reader."""

GROUP_NAME = "سهرية القهوة - شيكاغو" #"My Group Name"
WHATSAPP_WEB_URL = "https://web.whatsapp.com"
CHROME_SESSION_DIR = "./chrome_session"
CHROME_BINARY_PATH = ""
DEFAULT_WAIT_TIMEOUT = 60
QR_LOGIN_WAIT_TIMEOUT = 300
SEARCH_RESULTS_DELAY_SECONDS = 2
CHAT_LOAD_DELAY_SECONDS = 2
MESSAGE_SEPARATOR = "=" * 60
PRESS_ENTER_PROMPT = "\nPress Enter to close the browser..."

CHAT_LIST_SELECTOR = '[data-testid="chat-list"]'
CHAT_LIST_SEARCH_SELECTOR = '[data-testid="chat-list-search"]'
MESSAGE_SELECTOR = "[data-pre-plain-text]"
MESSAGE_TEXT_SELECTOR = "span.selectable-text"
