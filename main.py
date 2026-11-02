import os
import time
import asyncio
import sqlite3
import aiohttp
from aiohttp import web

# Loop setup for Render and Python runtimes
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import UserNotParticipant

# ================= Credentials =================
API_ID = 37940634
API_HASH = "6c9bf207b1eba747bb4ae29d8b8fa8e8"
BOT_TOKEN = "9065470430:AAG0qzVJMcFCAlAPA4NAEyS4XEIGjkKU3eU"
ADMIN_USERNAME = "Akdgak"
SUPPORT_BOT_LINK = "https://t.me/ak_helppper_bot"

# ================= Database Setup =================
conn = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        referrals INTEGER DEFAULT 0,
        premium_until INTEGER DEFAULT 0,
        token_pass_until INTEGER DEFAULT 0
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY,
        admin_id INTEGER DEFAULT 1557553087,
        s1_site TEXT,
        s1_api TEXT,
        s2_site TEXT,
        s2_api TEXT,
        fsub_ch1 INTEGER DEFAULT 0,
        fsub_ch2 INTEGER DEFAULT 0,
        fsub_link1 TEXT DEFAULT 'https://t.me/',
        fsub_link2 TEXT DEFAULT 'https://t.me/'
    )
''')
conn.commit()

cursor.execute("SELECT * FROM settings WHERE id = 1")
if not cursor.fetchone():
    cursor.execute("""
        INSERT INTO settings 
        (id, admin_id, s1_site, s1_api, s2_site, s2_api, fsub_ch1, fsub_ch2, fsub_link1, fsub_link2) 
        VALUES (1, 1557553087, 'droplink.co', 'your_api_1', 'shorturllink.in', 'your_api_2', 0, 0, 'https://t.me/', 'https://t.me/')
    """)
    conn.commit()

app = Client("diskwala_stream_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# ================= Helpers =================
def get_user(user_id):
    cursor.execute("SELECT referrals, premium_until, token_pass_until FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

def get
