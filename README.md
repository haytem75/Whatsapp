# WhatsApp Group Message Reader

A Python script that opens WhatsApp Web in Chrome or Chromium, restores your saved browser session, opens a group chat, and prints the visible text messages with their senders.

---

## Requirements

- Python 3.8+
- Google Chrome or Chromium installed
- A desktop session that can open the browser window

---

## Setup

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. Set your variables**

Open `variables.py` and change the values you want to configure. The main one is:

```python
GROUP_NAME = "My Group Name"
```

You can also adjust these shared values in `variables.py`:

```python
WHATSAPP_WEB_URL = "https://web.whatsapp.com"
CHROME_SESSION_DIR = "./chrome_session"
CHROME_BINARY_PATH = ""
DEFAULT_WAIT_TIMEOUT = 60
QR_LOGIN_WAIT_TIMEOUT = 300
SEARCH_RESULTS_DELAY_SECONDS = 2
CHAT_LOAD_DELAY_SECONDS = 2
```

`CHROME_BINARY_PATH` is optional. Leave it empty to let the script auto-detect a compatible browser binary. Set it manually if Chrome or Chromium is installed in a non-standard location.

---

## Running the app

```bash
python3 app.py
```

**What happens:**

1. The script detects Chrome or Chromium and starts Selenium with your local browser profile in `chrome_session/`
2. WhatsApp Web opens automatically
3. **First run:** scan the QR code with your phone (WhatsApp → Linked Devices → Link a Device)
4. **Next runs:** the saved session is reused, so you usually skip the QR code
5. The script uses the WhatsApp sidebar search field to find `GROUP_NAME`, then opens the matching chat result
6. The browser stays open until you press Enter in the terminal

**Browser startup behavior:**

- The script auto-detects these browser commands on Linux: `google-chrome`, `google-chrome-stable`, `chromium`, `chromium-browser`
- On Windows, it also checks common Chrome and Chromium install paths
- Selenium handles driver resolution automatically, so you do not need `webdriver-manager`

**Example output:**

```text
Opening WhatsApp Web...
Waiting for login — scan the QR code if prompted (60 sec timeout)...
Logged in successfully!

Searching for group: 'Project Team'...
Opened group: 'Project Team'

Reading messages...
============================================================
[Alice]  Hey everyone!
[Bob]  What time is the meeting?
[Alice]  At 3pm
============================================================

Total messages shown: 3

Press Enter to close the browser...
```

---

## Configuration Reference

| Variable | Purpose |
|---|---|
| `GROUP_NAME` | Exact group or chat title to search for in WhatsApp Web |
| `WHATSAPP_WEB_URL` | URL opened by Selenium |
| `CHROME_SESSION_DIR` | Folder used to persist your WhatsApp login session |
| `CHROME_BINARY_PATH` | Optional explicit path to the Chrome/Chromium executable |
| `DEFAULT_WAIT_TIMEOUT` | Max seconds to wait for WhatsApp elements to appear |
| `QR_LOGIN_WAIT_TIMEOUT` | Extra wait time after a QR code is detected so you can complete manual login |
| `SEARCH_RESULTS_DELAY_SECONDS` | Delay after typing the group name before clicking the result |
| `CHAT_LOAD_DELAY_SECONDS` | Delay after opening the chat before reading messages |
| `MESSAGE_SEPARATOR` | Separator printed around the output |
| `PRESS_ENTER_PROMPT` | Prompt shown before the browser closes |

---

## How it works

| Method | What it does |
|---|---|
| `_resolve_browser_binary()` | Finds Chrome or Chromium automatically, or uses `CHROME_BINARY_PATH` if provided |
| `_find_first_visible()` | Returns the first visible element matching any selector in a fallback list |
| `_wait_for_any_visible()` | Waits until one of several possible WhatsApp UI selectors becomes visible |
| `_replace_search_text()` | Replaces existing text in the WhatsApp search field before typing the target chat name |
| `_find_chat_result()` | Locates a visible chat result using several matching strategies |
| `__init__()` | Starts Selenium with the saved session directory and browser options |
| `login()` | Opens WhatsApp Web, detects QR-login state, and waits for the chat UI to become ready |
| `open_group()` | Searches for the configured group name and opens the first visible matching chat result |
| `read_messages()` | Finds visible message elements and prints sender plus text |
| `_parse_sender()` | Extracts the sender name from the `data-pre-plain-text` attribute |
| `_get_text()` | Reads text content from a text message bubble |
| `close()` | Quits the browser cleanly |

---

## Notes

- Only visible text messages are printed. Non-text content such as images or stickers is skipped.
- Only currently loaded messages are read. Older messages require scrolling in WhatsApp Web first.
- The `chrome_session/` folder contains your saved login session and should be kept private.
- If no compatible browser is found, the script raises an error asking you to install Chrome/Chromium or set `CHROME_BINARY_PATH`.
- The current WhatsApp Web build uses an input-based chat search field, and the script includes fallback selectors for UI variations.
- If the browser opens but you cannot see it from your environment, the issue is usually the desktop/display setup rather than the Python code.

---

## Troubleshooting

- If the script cannot start the browser, verify that Chrome or Chromium is installed and available on your system `PATH`.
- If auto-detection fails, set `CHROME_BINARY_PATH` in `variables.py` to the full browser executable path.
- If login times out on a first run, increase `QR_LOGIN_WAIT_TIMEOUT` in `variables.py`.
- If the target chat is not opened, confirm that `GROUP_NAME` exactly matches the WhatsApp chat title.
- If Chromium is already open with the same `chrome_session/` profile, close the existing browser window before starting another run.
- If your Python editor reports missing imports but the script runs, your VS Code Python interpreter is probably not set to the environment where `selenium` is installed.
