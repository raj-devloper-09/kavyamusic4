"""
Static data: the full VILLAIN_MUSIC-style command menu.

Only /start and /vplay are actually wired up to real logic (see basic.py
and vplay.py). Every command listed below is shown in the /help menu for
looks, but if someone actually runs one, plugins/soon.py replies with the
"this feature is available soon" message.
"""

CATEGORIES = {
    "🎬 Video / Stream": [
        "vplay", "vstop", "vpause", "vresume", "vend",
        "pause", "resume", "stop", "end", "skip", "next", "seek", "seekback",
        "speed", "slow", "loop", "shuffle", "queue", "playback", "playing",
        "player", "autoend", "channelplay",
    ],
    "🎵 Music": [
        "music", "song", "connect", "cookies",
        "cend", "cnext", "cpause", "cplayback", "cplayer", "cplaying",
        "cqueue", "cresume", "cseek", "cseekback", "cshuffle", "cskip",
        "cslow", "cspeed", "cstop",
    ],
    "🛡️ Admin & Moderation": [
        "ban", "unban", "mute", "unmute", "tmute", "pin", "unpin", "pinned",
        "block", "unblock", "blocked", "blockedusers", "blusers",
        "blacklistchat", "unblacklistchat", "blchat", "unblchat", "blchats",
        "blacklistedchats", "whitelistchat", "maintenance", "reload",
        "refresh", "admincache", "leaveall",
    ],
    "🌍 Global Ban & Sudo": [
        "gban", "ungban", "gbanlist", "gbannedusers", "globalban",
        "addsudo", "delsudo", "rmsudo", "delallsudo", "listsudo",
        "sudoers", "sudolist", "auth", "authlist", "authusers", "unauth",
    ],
    "⚙️ Settings & Profile": [
        "settings", "setting", "lang", "language", "setlang",
        "setname", "setbio", "setdiscription", "setpfp", "setphoto",
        "settitle", "removephoto", "delpfp", "delallpfp", "packkang",
        "kang", "userbotjoin", "userbotleave", "privacy",
    ],
    "📊 Owner & Stats": [
        "stats", "gstats", "ping", "alive", "logs", "logger", "getlogs",
        "get_log", "eval", "sh", "restart", "reboot", "update", "git",
        "github", "gitpull", "repo", "allrepo", "app", "apps",
        "broadcast", "gcast", "gadd",
    ],
    "🏷️ Tag Tools": [
        "tag", "tagall", "tagmember", "tagoff", "tagstop", "atag", "bstag",
        "eftag", "etag", "gmtag", "gmstop", "gn", "gnstop", "gntag",
        "hftag", "hitag", "histop", "lifetag", "lifestop", "mention",
        "utag", "stag", "tgm", "tgt",
    ],
    "🤖 AI & Fun": [
        "ai", "ask", "chatgpt", "google", "math", "quiz", "quizon",
        "quizoff", "uiz", "uizon", "uizoff", "cute", "love", "shayari",
        "shayarioff", "spam", "wish", "welcome", "brb", "afk", "couples",
        "raja", "oodnight", "all", "alloff",
    ],
    "🎨 Media & Misc": [
        "font", "fonts", "image", "img", "ig", "instagram", "reel",
        "telegraph", "qr", "stickerid", "stid", "get_sticker", "spg",
        "mmf", "ac", "cancel", "cancle", "n", "r", "q", "sg", "st",
        "tl", "tr", "up", "gle", "lg",
    ],
}

# Flat list of every "not implemented yet" command (used by the catch-all
# handler). /start, /vplay and /help are deliberately excluded here since
# those are actually implemented.
ALL_SOON_COMMANDS = sorted({cmd for group in CATEGORIES.values() for cmd in group})
