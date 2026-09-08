"""
Run this ONCE, locally or on your VPS, to generate the SESSION_STRING
for your ASSISTANT account (a normal Telegram user account, NOT a bot).

This assistant account is the one that will actually join the group's
video chat and stream the video. It must be added as a member
(preferably admin) of every group where you want /vplay to work.

Usage:
    python generate_session.py
"""

from pyrogram import Client

API_ID = int(input("Enter your API_ID: "))
API_HASH = input("Enter your API_HASH: ").strip()

with Client(name="assistant_session_gen", api_id=API_ID, api_hash=API_HASH, in_memory=True) as app:
    session_string = app.export_session_string()
    print("\n=================================================")
    print("Your SESSION_STRING (copy this into your .env file):\n")
    print(session_string)
    print("=================================================\n")
