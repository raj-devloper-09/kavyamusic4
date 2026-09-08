import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", "31618924"))
API_HASH = os.getenv("API_HASH", "0e85b5d563724e29e1225dc344d2dba0")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")

SUDO_USERS = [
    int(x) for x in os.getenv("SUDO_USERS", "7861095748").split(",") if x.strip().isdigit()
]

LOG_GROUP_ID = os.getenv("LOG_GROUP_ID", "-1004317165206")
LOG_GROUP_ID = int(LOG_GROUP_ID) if LOG_GROUP_ID.strip().lstrip("-").isdigit() else None

DOWNLOADS_DIR = "downloads"

# ------------------------------------------------------------------
# Branding / UI only — used for the /start & /help buttons and text.
# Safe to leave as-is or change to your own links.
# ------------------------------------------------------------------
OWNER_ID = int(os.getenv("OWNER_ID", str(SUDO_USERS[0] if SUDO_USERS else 7861095748)))
SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "https://t.me/bot_support_raj")
SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL", "https://t.me/bot_support_raj")
SOURCE_URL = os.getenv("SOURCE_URL", "https://t.me/bot_support_raj")
START_IMG = os.getenv("START_IMG", "https://files.catbox.moe/dbh13g.jpg")

# Same start videos used by VILLAIN_MUSIC's /start (random.choice picks one).
# If all of these ever fail to load, the handler falls back to START_IMG,
# and if even that fails, to a plain text message — /start never breaks.
START_VID = [
    "https://telegra.ph/file/1a3c152717eb9d2e94dc2.mp4",
    "https://files.catbox.moe/ln00jb.mp4",
    "https://graph.org/file/83ebf52e8bbf138620de7.mp4",
    "https://files.catbox.moe/0fq20c.mp4",
    "https://graph.org/file/318eac81e3d4667edcb77.mp4",
    "https://graph.org/file/7c1aa59649fbf3ab422da.mp4",
    "https://files.catbox.moe/t0nepm.mp4",
]

if not all([API_ID, API_HASH, BOT_TOKEN, SESSION_STRING]):
    raise SystemExit(
        "ERROR: Please fill API_ID, API_HASH, BOT_TOKEN and SESSION_STRING "
        "in your .env file before starting the bot. See .env.example."
    )
