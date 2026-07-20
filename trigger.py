import json
import os

from dotenv import load_dotenv

from CEACStatusBot import (
    EmailNotificationHandle,
    NotificationManager,
    TelegramNotificationHandle,
)

# --- Load .env if present, else fallback to system env ---
if os.path.exists(".env"):
    load_dotenv(dotenv_path=".env")  # loads into os.environ
else:
    print(".env not found, using system environment only")


# Status record is downloaded by actions/download-artifact in the workflow.
# If no previous artifact exists, create a fresh one.
if not os.path.exists("status_record.json"):
    print("No previous status record, starting fresh")
    with open("status_record.json", "w") as f:
        json.dump({"statuses": []}, f)

try:
    LOCATION = os.environ["LOCATION"]
    NUMBER = os.environ["NUMBER"]
    PASSPORT_NUMBER = os.environ["PASSPORT_NUMBER"]
    SURNAME = os.environ["SURNAME"]
    notificationManager = NotificationManager(LOCATION, NUMBER, PASSPORT_NUMBER, SURNAME)
except KeyError as e:
    raise RuntimeError(f"Missing required env var: {e}") from e


# --- Optional: Email notifications ---
FROM = os.getenv("FROM")
TO = os.getenv("TO")
PASSWORD = os.getenv("PASSWORD")
SMTP = os.getenv("SMTP", "")

if FROM and TO and PASSWORD:
    emailNotificationHandle = EmailNotificationHandle(FROM, TO, PASSWORD, SMTP)
    notificationManager.addHandle(emailNotificationHandle)
else:
    print("Email notification config missing or incomplete")


# --- Optional: Telegram notifications ---
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

if BOT_TOKEN and CHAT_ID:
    tgNotif = TelegramNotificationHandle(BOT_TOKEN, CHAT_ID)
    notificationManager.addHandle(tgNotif)
else:
    print("Telegram bot notification config missing or incomplete")


# --- Send notifications ---
notificationManager.send()
