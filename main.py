import os
import re
import time
import asyncio
import sqlite3
import aiohttp
from aiohttp import web
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Render event loop setup
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

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

# ================= Diskwala Bypass Scraper =================
async def resolve_diskwala(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.diskwala.com/"
    }
    
    clean_url = url.strip().split("?")[0].rstrip("/")
    file_id = clean_url.split("/")[-1]

    target_url = f"https://www.diskwala.com/app/{file_id}"
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(target_url, timeout=12) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    
                    # Page source se video streaming / download link dhoondhna
                    # 1. m3u8 ya direct mp4 pattern
                    mp4_matches = re.findall(r'(https?://[^\s"\']+\.(?:mp4|m3u8)[^\s"\']*)', html)
                    if mp4_matches:
                        return mp4_matches[0], file_id
                    
                    # 2. source src tag pattern
                    src_matches = re.findall(r'src=["\'](https?://[^\s"\']+)["\']', html)
                    for src in src_matches:
                        if "stream" in src or "video" in src or "download" in src:
                            return src, file_id
                    
                    # 3. Direct API call attempt
                    api_call = f"https://www.diskwala.com/api/v1/file/{file_id}"
                    async with session.get(api_call, timeout=8) as api_resp:
                        if api_resp.status == 200:
                            data = await api_resp.json()
                            direct = data.get("direct_link") or data.get("url") or data.get("stream_url")
                            if direct:
                                return direct, file_id
    except Exception:
        pass

    # Agar scrape na ho paye toh fallback direct endpoint
    fallback_link = f"https://diskwala.com/api/file/download/{file_id}"
    return fallback_link, file_id

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
        f"👋 Namaste {message.from_user.first_name}!\n\n"
        "Diskwala link bhejo, direct streaming aur fast download link mil jayega.\n\n"
        f"🔗 Referral Link: `{ref_link}`",
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
        status = "✅ VIP Active (Admin)" if user_id == ADMIN_ID else ("✅ VIP Active" if is_active else "❌ Inactive")
        
        await query.message.edit_text(
            f"👤 User ID: `{user_id}`\n💎 VIP Status: {status}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_home")]])
        )
    elif query.data == "buy_premium":
        await query.message.edit_text(
            "💎 **VIP Premium Plans:**\n\n• 1 Week = ₹29\n• 1 Month = ₹89\n\n⚡ Bina ads direct video access!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Support Bot", url=SUPPORT_BOT_LINK)],
                [InlineKeyboardButton("🔙 Back", callback_data="back_home")]
            ])
        )
    elif query.data == "back_home":
        await query.message.delete()

# ================= Diskwala Link Handler =================
@app.on_message(filters.text & filters.private & ~filters.command(["start", "admin", "add_prem", "broadcast"]))
async def handle_link(client, message):
    text = message.text.strip()
    if "diskwala" not in text.lower():
        return await message.reply_text("⚠️ Kripya valid Diskwala video link bhejein.")

    status = await message.reply_text("⚡ Extracting Direct Video Link...")

    direct_url, file_id = await resolve_diskwala(text)

    # MX Player / VLC stream URL format
    vlc_stream = f"vlc://{direct_url}" if direct_url.startswith("http") else direct_url

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("▶️ Watch Direct (Browser)", url=direct_url),
            InlineKeyboardButton("⬇️ Direct Download", url=direct_url)
        ],
        [
            InlineKeyboardButton("💬 Support Bot", url=SUPPORT_BOT_LINK)
        ]
    ])

    await status.delete()
    await message.reply_text(
        f"🎬 **Diskwala Video Extracted!**\n\n"
        f"🆔 **File ID:** `{file_id}`\n\n"
        "Direct link ready hai. Niche button par tap karke direct play karein ya download karein (bina Diskwala ad page ke):",
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
