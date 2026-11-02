import os
import time
import asyncio
import sqlite3
import aiohttp
from aiohttp import web

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

def get_settings():
    cursor.execute("SELECT admin_id, s1_site, s1_api, s2_site, s2_api, fsub_ch1, fsub_ch2, fsub_link1, fsub_link2 FROM settings WHERE id = 1")
    return cursor.fetchone()

def is_admin(user):
    sett = get_settings()
    stored_admin_id = sett[0] if sett else 1557553087
    if user.id == 1557553087 or user.id == stored_admin_id:
        return True
    if user.username and user.username.lower() == ADMIN_USERNAME.lower():
        return True
    return False

async def is_subscribed(client, user_id):
    sett = get_settings()
    if not sett:
        return True
    ch1, ch2 = sett[5], sett[6]
    for ch_id in [ch1, ch2]:
        if ch_id != 0:
            try:
                await client.get_chat_member(ch_id, user_id)
            except UserNotParticipant:
                return False
            except Exception:
                pass
    return True

async def shorten_url(url, site, api_key):
    api_endpoint = f"https://{site}/api?api={api_key}&url={url}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_endpoint, timeout=10) as resp:
                data = await resp.json()
                return data.get("shortenedUrl", url)
    except Exception:
        return url

# ================= Start & Referral =================
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    user_id = message.from_user.id
    if user_id == 1557553087:
        cursor.execute("UPDATE settings SET admin_id = ? WHERE id = 1", (user_id,))
        conn.commit()

    user = get_user(user_id)
    text_parts = message.text.split()
    
    if not user:
        referred_by = None
        if len(text_parts) > 1 and text_parts[1].startswith("ref_"):
            try:
                r_id = int(text_parts[1].split("_")[1])
                if r_id != user_id:
                    referred_by = r_id
            except Exception:
                pass

        cursor.execute("INSERT INTO users (user_id, referrals, premium_until, token_pass_until) VALUES (?, 0, 0, 0)", (user_id,))
        conn.commit()

        if referred_by:
            ref_data = get_user(referred_by)
            if ref_data:
                new_refs = ref_data[0] + 1
                prem_until = ref_data[1]
                if new_refs % 2 == 0:
                    prem_until = max(int(time.time()), prem_until) + 86400
                    try:
                        await client.send_message(referred_by, "🎉 Badhai ho! 2 referrals poore hone par 24h VIP pass mil gaya!")
                    except Exception:
                        pass
                cursor.execute("UPDATE users SET referrals = ?, premium_until = ? WHERE user_id = ?", (new_refs, prem_until, referred_by))
                conn.commit()

    subbed = await is_subscribed(client, user_id)
    sett = get_settings()
    if not subbed:
        buttons = []
        if sett[5] != 0:
            buttons.append([InlineKeyboardButton("📢 Channel 1", url=sett[7])])
        if sett[6] != 0:
            buttons.append([InlineKeyboardButton("📢 Channel 2", url=sett[8])])
        buttons.append([InlineKeyboardButton("🔄 Verify Join", url=f"https://t.me/{(await client.get_me()).username}?start=check")])
        return await message.reply_text("⚠️ Bot use karne ke liye pehle channel join karein:", reply_markup=InlineKeyboardMarkup(buttons))

    if len(text_parts) > 1 and text_parts[1].startswith("verify2_"):
        cursor.execute("UPDATE users SET token_pass_until = ? WHERE user_id = ?", (int(time.time()) + 86400, user_id))
        conn.commit()
        return await message.reply_text("✅ Verification successful! 24 ghante ka pass active ho gaya. Ab Diskwala link bhejein.")

    bot_uname = (await client.get_me()).username
    ref_link = f"https://t.me/{bot_uname}?start=ref_{user_id}"
    
    welcome_text = (
        f"👋 Namaste {message.from_user.first_name}!\n\n"
        "Diskwala link bhejo, instant Online Stream & Direct Fast Download link mil jayega.\n\n"
        f"🔗 Referral Link: `{ref_link}`\n"
        "👉 2 referrals = 1 din VIP Free!"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Buy VIP Premium", callback_data="buy_premium")],
        [InlineKeyboardButton("📊 My Status", callback_data="my_status"), InlineKeyboardButton("💬 Support Bot", url=SUPPORT_BOT_LINK)]
    ])
    await message.reply_text(welcome_text, reply_markup=kb)

# ================= Callbacks =================
@app.on_callback_query()
async def cb_handler(client, query):
    user_id = query.from_user.id
    user = get_user(user_id) or (0, 0, 0)
    if query.data == "my_status":
        prem_until = user[1]
        now = int(time.time())
        status = f"✅ Active ({int((prem_until - now)/3600)}h)" if prem_until > now else "❌ Inactive"
        await query.message.edit_text(
            f"👤 User ID: `{user_id}`\n👥 Referrals: `{user[0]}`\n💎 Premium: {status}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_home")]])
        )
    elif query.data == "buy_premium":
        await query.message.edit_text(
            f"💎 VIP Premium Plans:\n\n• 1 Week = ₹29\n• 1 Month = ₹89\n\n⚡ Bina shortener direct fast links!\nContact: @{ADMIN_USERNAME}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Support Bot", url=SUPPORT_BOT_LINK)],
                [InlineKeyboardButton("🔙 Back", callback_data="back_home")]
            ])
        )
    elif query.data == "back_home":
        await query.message.delete()

# ================= Diskwala Link Processing =================
@app.on_message(filters.text & filters.private & ~filters.command(["start", "admin", "set_s1", "set_s2", "set_ch1", "set_ch2", "add_prem", "broadcast"]))
async def process_link(client, message):
    text = message.text.strip()
    if "diskwala" not in text.lower():
        return await message.reply_text("⚠️ Kripya valid Diskwala video link bhejein.")

    user_id = message.from_user.id
    if not (await is_subscribed(client, user_id)):
        return await message.reply_text("⚠️ Pehle channel join karein.")

    user = get_user(user_id) or (0, 0, 0)
    now = int(time.time())
    is_prem = user[1] > now
    token_valid = user[2] > now

    # Double Shortener Check
    if not is_prem and not token_valid:
        sett = get_settings()
        s1_site, s1_api, s2_site, s2_api = sett[1], sett[2], sett[3], sett[4]
        bot_uname = (await client.get_me()).username
        step2_link = f"https://t.me/{bot_uname}?start=verify2_{user_id}"
        
        if s2_site and s2_api and s2_site != s1_site and s2_site != 'none':
            s2_short = await shorten_url(step2_link, s2_site, s2_api)
            final_short = await shorten_url(s2_short, s1_site, s1_api)
        else:
            final_short = await shorten_url(step2_link, s1_site, s1_api)

        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔓 24h Access Unlock Karein", url=final_short)],
            [InlineKeyboardButton("💎 Buy VIP (No Ads)", callback_data="buy_premium")],
            [InlineKeyboardButton("💬 Support Bot", url=SUPPORT_BOT_LINK)]
        ])
        return await message.reply_text("⚠️ **Link access karne ke liye task verify karein:**\n\nNiche button se verification complete karke 24h pass unlock karein.", reply_markup=btn)

    status = await message.reply_text("⚡ Generating Stream & Download links...")
    
    # Extract ID
    clean = text.split("?")[0].rstrip("/")
    file_id = clean.split("/")[-1]

    stream_url = f"https://www.diskwala.com/app/{file_id}"
    download_url = f"https://diskwala.com/download/{file_id}"

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("▶️ Watch Online", url=stream_url),
            InlineKeyboardButton("⬇️ Fast Download", url=download_url)
        ],
        [
            InlineKeyboardButton("💬 Support Bot", url=SUPPORT_BOT_LINK)
        ]
    ])

    await status.delete()
    await message.reply_text(
        f"🎬 **Diskwala Video Ready**\n\n"
        f"🆔 **File ID:** `{file_id}`\n\n"
        "Niche diye buttons se video stream ya download karein:",
        reply_markup=kb
    )

# ================= Admin Commands =================
@app.on_message(filters.command("admin") & filters.private)
async def admin_ctrl(client, message):
    if not is_admin(message.from_user): return
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    sett = get_settings()
    await message.reply_text(
        f"⚙️ **Admin Panel**\n\nTotal Users: `{total_users}`\nShortener 1: `{sett[1]}`\nShortener 2: `{sett[3]}`\n\n"
        "Commands:\n"
        "`/set_s1 site apikey`\n"
        "`/set_s2 site apikey`\n"
        "`/set_ch1 -100id link`\n"
        "`/set_ch2 -100id link`\n"
        "`/add_prem userid days`\n"
        "`/broadcast` (reply to message)"
    )

@app.on_message(filters.command("set_s1") & filters.private)
async def set_s1(client, message):
    if not is_admin(message.from_user): return
    try:
        _, site, api_key = message.text.split()
        cursor.execute("UPDATE settings SET s1_site = ?, s1_api = ? WHERE id = 1", (site, api_key))
        conn.commit()
        await message.reply_text("✅ Shortener 1 set ho gaya!")
    except Exception:
        await message.reply_text("❌ Format: `/set_s1 droplink.co apikey`")

@app.on_message(filters.command("set_s2") & filters.private)
async def set_s2(client, message):
    if not is_admin(message.from_user): return
    try:
        _, site, api_key = message.text.split()
        cursor.execute("UPDATE settings SET s2_site = ?, s2_api = ? WHERE id = 1", (site, api_key))
        conn.commit()
        await message.reply_text("✅ Shortener 2 set ho gaya!")
    except Exception:
        await message.reply_text("❌ Format: `/set_s2 shorturllink.in apikey`")

@app.on_message(filters.command("set_ch1") & filters.private)
async def set_ch1(client, message):
    if not is_admin(message.from_user): return
    try:
        _, ch_id, link = message.text.split()
        cursor.execute("UPDATE settings SET fsub_ch1 = ?, fsub_link1 = ? WHERE id = 1", (int(ch_id), link))
        conn.commit()
        await message.reply_text("✅ Channel 1 set!")
    except Exception:
        await message.reply_text("❌ Format: `/set_ch1 -100123456789 https://t.me/link`")

@app.on_message(filters.command("set_ch2") & filters.private)
async def set_ch2(client, message):
    if not is_admin(message.from_user): return
    try:
        _, ch_id, link = message.text.split()
        cursor.execute("UPDATE settings SET fsub_ch2 = ?, fsub_link2 = ? WHERE id = 1", (int(ch_id), link))
        conn.commit()
        await message.reply_text("✅ Channel 2 set!")
    except Exception:
        await message.reply_text("❌ Format: `/set_ch2 -100123456789 https://t.me/link`")

@app.on_message(filters.command("add_prem") & filters.private)
async def add_prem(client, message):
    if not is_admin(message.from_user): return
    try:
        parts = message.text.split()
        uid = int(parts[1])
        days = int(parts[2])
        sec = days * 86400
        user = get_user(uid)
        curr = max(int(time.time()), user[1] if user else 0)
        cursor.execute("""
            INSERT INTO users (user_id, referrals, premium_until, token_pass_until) 
            VALUES (?, 0, ?, 0) 
            ON CONFLICT(user_id) DO UPDATE SET premium_until = ?
        """, (uid, curr + sec, curr + sec))
        conn.commit()
        await message.reply_text(f"✅ User `{uid}` ko `{days}` din ka VIP pass diya gaya.")
    except Exception as e:
        await message.reply_text(f"❌ Format: `/add_prem 123456789 30`")

@app.on_message(filters.command("broadcast") & filters.private)
async def bcast(client, message):
    if not is_admin(message.from_user): return
    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply karke `/broadcast` likhein.")
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    success, failed = 0, 0
    status = await message.reply_text("📢 Broadcast ja raha hai...")
    for u in users:
        try:
            await message.reply_to_message.copy(u[0])
            success += 1
            await asyncio.sleep(0.04)
        except Exception:
            failed += 1
    await status.edit_text(f"✅ Sent: `{success}` | Failed: `{failed}`")

# ================= Web Server & Runner =================
async def handle_ping(request):
    return web.Response(text="Diskwala Stream Bot is Running!")

async def start_web_server():
    server = web.Application()
    server.router.add_get("/", handle_ping)
    runner = web.AppRunner(server)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    await start_web_server()
    await app.start()
    print("Diskwala Stream Bot Started!")
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop.run_until_complete(main())
