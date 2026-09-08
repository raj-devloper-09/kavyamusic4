# 🎬 VILLAIN-style Video Chat Player Bot

Isme **kaam** wahi karta hai jo `kavya-music-main` karta tha (`/start` +
`/vplay` — video ko group ke video chat me stream karna, using an
assistant account + PyTgCalls). Sirf **dikhne ka style** (fonts, emoji,
boxed design, inline buttons, `/help` menu) `VILLAIN_MUSIC` jaisa kar diya
gaya hai.

## Kya actually kaam karta hai

| Command | Status |
|---|---|
| `/start` | ✅ Working — VILLAIN_MUSIC-style welcome card + buttons |
| `/vplay` (reply to a video) | ✅ Working — streams the video in the group's video chat |
| `/help` | ✅ Working — sirf ek menu hai, categories dikhata hai (design purposes) |
| Har baaki command (200+, jaise `/ping`, `/ban`, `/settings`, `/vstop`, etc.) | 🚧 Naam dikhta hai `/help` menu me, lekin use karne par bot reply karta hai: **"this feature is available soon"** |

`plugins/commands_data.py` me har category aur command ke naam hain — bas
UI/menu ke liye, koi bhi unme se real function nahi karta abhi. Naya
feature actually implement karne ke liye, us command ko
`plugins/commands_data.py` ki list se hata do aur apna real handler
`plugins/` me likh do.

## Setup

Same as before — `.env.example` ko `.env` bana ke fill karo
(`API_ID`, `API_HASH`, `BOT_TOKEN`, `SESSION_STRING`), phir:

```bash
pip install -r requirements.txt
python generate_session.py   # one-time, assistant account ke liye
python main.py
```

Assistant account (jiska session generate kiya) group me member/admin
hona chahiye, aur `/vplay` use karne se pehle group me video chat
manually start karo.

## File Structure

```
.
├── main.py                    # Entry point
├── config.py                  # .env loader (+ branding links for buttons)
├── clients.py                 # Bot + Assistant + PyTgCalls setup
├── generate_session.py        # One-time assistant session generator
├── utils/
│   └── font.py                 # VILLAIN_MUSIC small-caps text helper (design only)
└── plugins/
    ├── vplay.py                 # /vplay — the only real streaming logic
    ├── basic.py                 # /start, /help, stream-end cleanup
    ├── commands_data.py         # Names of every "coming soon" command, by category
    └── soon.py                  # Catch-all "this feature is available soon" reply
```
