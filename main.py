import os
import asyncio

# Render Python 3.12+ loop fix
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
        s1_site TEXT DEFAULT 'droplink.co',
        s1_api TEXT DEFAULT '',
        s2_site TEXT DEFAULT 'shorturllink.in',
        s2_api TEXT DEFAULT ''
    )
''')
conn.commit()

cursor.execute("SELECT * FROM settings WHERE id = 1")
if not cursor.fetchone():
    cursor.execute("INSERT INTO settings (id, s1_site, s1_api, s2_site, s2_api) VALUES (1, 'droplink.co', '', 'shorturllink.in', '')")
    conn.commit()

app = Client("diskwala_stream_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

def is_admin(user_id):
    return user_id == ADMIN_ID

# ================= Start Command =================
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    user_id = message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO users (user_id, referrals, premium_until, token_pass_until) VALUES (?, 0, 0, 0)", (user_id,))
    conn.commit()

    bot_uname = (await client.get_me()).username
    ref_link = f"https://t.me/{bot_uname}?start=ref_{user_id}"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Buy VIP Premium", callback_data="buy_premium")],
        [InlineKeyboardButton("📊 My Status", callback_data="my_status"), InlineKeyboardButton("💬 Support Bot", url=SUPPORT_BOT_LINK)]
    ])

    await message.reply_text(
        f"👋 Namaste {message.from_user.first_name}!\n\n"
        "Diskwala link bhejo, direct streaming aur download link mil jayega.\n\n"
        f"🔗 Referral Link: `{ref_link}`",
        reply_markup=kb
    )

# ================= Admin Commands =================
@app.on_message(filters.command("admin") & filters.private)
async def admin_panel(client, message):
    if not is_admin(message.from_user.id):
        return
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT s1_site, s2_site FROM settings WHERE id = 1")
    sett = cursor.fetchone()
    
    text = (
        f"⚙️ **Admin Control Panel**\n\n"
        f"👥 Total Users: `{total_users}`\n"
        f"🔗 Shortener 1: `{sett[0]}`\n"
        f"🔗 Shortener 2: `{sett[1]}`\n\n"
        "Commands:\n"
        "`/add_prem <userid> <days>`\n"
        "`/set_s1 <site> <api_key>`\n"
        "`/set_s2 <site> <api_key>`\n"
        "`/broadcast` (reply to message)"
    )
    await message.reply_text(text)

@app.on_message(filters.command("add_prem") & filters.private)
async def add_prem_cmd(client, message):
    if not is_admin(message.from_user.id):
        return
    try:
        parts = message.text.split()
        uid = int(parts[1])
        days = int(parts[2])
        expiry = int(time.time()) + (days * 86400)
        cursor.execute("INSERT OR REPLACE INTO users (user_id, referrals, premium_until, token_pass_until) VALUES (?, 0, ?, ?)", (uid, expiry, expiry))
        conn.commit()
        await message.reply_text(f"✅ User `{uid}` ko `{days}` din ka VIP diya gaya!")
    except Exception:
        await message.reply_text("❌ Format: `/add_prem 123456789 30`")

@app.on_message(filters.command("broadcast") & filters.private)
async def broadcast_cmd(client, message):
    if not is_admin(message.from_user.id):
        return
    if not message.reply_to_message:
        return await message.reply_text("⚠️ Kisi message par reply karke `/broadcast` likhein.")
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    sent = 0
    for u in users:
        try:
            await message.reply_to_message.copy(u[0])
            sent += 1
            await asyncio.sleep(0.04)
        except Exception:
            pass
    await message.reply_text(f"✅ Broadcast complete! Sent to `{sent}` users.")

# ================= Callbacks =================
@app.on_callback_query()
async def cb_handler(client, query):
    user_id = query.from_user.id
    if query.data == "my_status":
        cursor.execute("SELECT premium_until FROM users WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        now = int(time.time())
        is_active = (user_id == ADMIN_ID) or (res and res[0] > now)
        status = "✅ VIP Active (Admin)" if user_id == ADMIN_ID else ("✅ VIP Active" if is_active else "❌ Inactive")
        await query.message.edit_text(
            f"👤 User ID: `{user_id}`\n💎 VIP Status: {status}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_home")]])
        )
    elif query.data == "buy_premium":
        await query.message.edit_text(
            "💎 VIP Premium Plans:\n\n• 1 Week = ₹29\n• 1 Month = ₹89\n\n⚡ Bina ads direct video access!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Support Bot", url=SUPPORT_BOT_LINK)],
                [InlineKeyboardButton("🔙 Back", callback_data="back_home")]
            ])
        )
    elif query.data == "back_home":
        await query.message.delete()

# ================= Diskwala Link Handler =================
@app.on_message(filters.text & filters.private & ~filters.command(["start", "admin", "add_prem", "broadcast"]))
async def handle_diskwala_link(client, message):
    text = message.text.strip()
    if "diskwala" not in text.lower():
        return await message.reply_text("⚠️ Kripya valid Diskwala video link bhejein.")

    clean_text = text.split("?")[0].rstrip("/")
    file_id = clean_text.split("/")[-1]

    # Clean Web Player Bypass links (Ad-free direct web stream)
    web_player_url = f"https://diskwala.top/play/{file_id}"
    direct_dl_url = f"https://diskwala.top/download/{file_id}"
    official_view = f"https://www.diskwala.com/app/{file_id}"

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("▶️ Watch Online (Player)", url=web_player_url),
            InlineKeyboardButton("⬇️ Fast Download", url=direct_dl_url)
        ],
        [
            InlineKeyboardButton("🌐 Open in App/Site", url=official_view)
        ],
        [
            InlineKeyboardButton("💬 Support Bot", url=SUPPORT_BOT_LINK)
        ]
    ])

    await message.reply_text(
        f"🎬 **Diskwala Video Links Ready!**\n\n"
        f"🆔 **File ID:** `{file_id}`\n\n"
        "👉 **Watch Online** par tap karke bina ads video play karein ya **Fast Download** se download karein:",
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
    print(">>> Diskwala Bot Live and Ready! <<<")
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop.run_until_complete(main())
