import os
import asyncio

# Python 3.12+ / 3.14 Render event loop fix (Pyrogram import se pehle zaroori hai)
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

import time
import sqlite3
import aiohttp
from aiohttp import web
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ================= Credentials =================
API_ID = 37940634
API_HASH = "6c9bf207b1eba747bb4ae29d8b8fa8e8"
BOT_TOKEN = "9065470430:AAG0qzVJMcFCAlAPA4NAEyS4XEIGjkKU3eU"
ADMIN_ID = 1557553087
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
conn.commit()

app = Client("diskwala_stream_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# ================= Start Command =================
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    user_id = message.from_user.id
    cursor.execute("SELECT premium_until FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id, referrals, premium_until, token_pass_until) VALUES (?, 0, 0, 0)", (user_id,))
        conn.commit()

    bot_uname = (await client.get_me()).username
    ref_link = f"https://t.me/{bot_uname}?start=ref_{user_id}"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Buy VIP Premium", callback_data="buy_premium")],
        [InlineKeyboardButton("📊 My Status", callback_data="my_status"), InlineKeyboardButton("💬 Support Bot", url=SUPPORT_BOT_LINK)]
    ])

    await message.reply_text(
        f"Namaste {message.from_user.first_name}!\n\n"
        "Diskwala link bhejo, direct stream aur download button milega.\n\n"
        f"Referral Link: `{ref_link}`",
        reply_markup=kb
    )

# ================= Callbacks =================
@app.on_callback_query()
async def cb_handler(client, query):
    user_id = query.from_user.id
    if query.data == "my_status":
        cursor.execute("SELECT premium_until FROM users WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        now = int(time.time())
        is_active = (user_id == ADMIN_ID) or (res and res[0] > now)
        status = "VIP Active (Admin)" if user_id == ADMIN_ID else ("VIP Active" if is_active else "Inactive")
        
        await query.message.edit_text(
            f"User ID: `{user_id}`\nVIP Status: {status}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back_home")]])
        )
    elif query.data == "buy_premium":
        await query.message.edit_text(
            "VIP Premium Plans:\n\n1 Week = Rs 29\n1 Month = Rs 89\n\nDirect link bina kisi ad ke!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Support Bot", url=SUPPORT_BOT_LINK)],
                [InlineKeyboardButton("Back", callback_data="back_home")]
            ])
        )
    elif query.data == "back_home":
        await query.message.delete()

# ================= Diskwala Link Handler =================
@app.on_message(filters.text & filters.private & ~filters.command(["start", "admin", "add_prem", "broadcast"]))
async def handle_link(client, message):
    text = message.text.strip()
    if "diskwala" not in text.lower():
        return await message.reply_text("Kripya valid Diskwala video link bhejein.")

    clean_url = text.split("?")[0].rstrip("/")
    file_id = clean_url.split("/")[-1]

    # Direct fallback URL
    direct_link = f"https://www.diskwala.com/app/{file_id}"

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Play / Stream", url=direct_link),
            InlineKeyboardButton("Download", url=direct_link)
        ],
        [
            InlineKeyboardButton("Support Bot", url=SUPPORT_BOT_LINK)
        ]
    ])

    await message.reply_text(
        f"Diskwala Link Ready!\n\nFile ID: `{file_id}`\n\nNiche diye button par tap karein:",
        reply_markup=kb
    )

# ================= Web Ping Server for Render =================
async def ping_handler(request):
    return web.Response(text="Diskwala Bot Live Hai!")

async def start_server():
    server = web.Application()
    server.router.add_get("/", ping_handler)
    runner = web.AppRunner(server)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    await start_server()
    await app.start()
    print(">>> Diskwala Bot Live! <<<")
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop.run_until_complete(main())
