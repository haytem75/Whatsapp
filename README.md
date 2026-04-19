# WhatsApp Group Message Reader

A simple Python script that opens WhatsApp Web and reads all messages from a group, showing who sent each one.

---

## Requirements

- Python 3.8+
- Google Chrome installed

---

## Setup

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. Set your group name**

Open `app.py` and change this line near the top:

```python
GROUP_NAME = "My Group Name"   # <-- put your group's exact name here
```

---

## Running the app

```bash
python app.py
```

**What happens:**

1. Chrome opens automatically and loads WhatsApp Web
2. **First run:** scan the QR code with your phone (WhatsApp → Linked Devices → Link a Device)
3. **Next runs:** session is saved in `chrome_session/` — no QR scan needed
4. The script opens your group and prints every message with the sender's name

**Example output:**
```
Logged in successfully!

Opened group: 'Project Team'

Reading messages...
============================================================
[Alice]  Hey everyone!
[Bob]    What time is the meeting?
[Alice]  At 3pm
============================================================

Total messages shown: 3
```

---

## How it works (code overview)

| Method | What it does |
|---|---|
| `__init__` | Launches Chrome with a saved session folder |
| `login()` | Waits for WhatsApp Web to load (handles QR scan) |
| `open_group()` | Types the group name in the search box and clicks it |
| `read_messages()` | Finds all message elements and prints sender + text |
| `_parse_sender()` | Extracts the sender name from WhatsApp's built-in metadata |
| `_get_text()` | Reads the visible text from the message bubble |

---

## Notes

- Only **visible** messages are read (WhatsApp Web loads older ones as you scroll up)
- The `chrome_session/` folder stores your login — keep it private
- This is built on **WhatsApp Web automation** using Selenium
