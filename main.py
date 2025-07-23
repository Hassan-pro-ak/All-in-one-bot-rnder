import logging import aiohttp import os from telegram import ( Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputFile ) from telegram.ext import ( Application, CommandHandler, MessageHandler, CallbackContext, CallbackQueryHandler, filters, ContextTypes ) from datetime import datetime from typing import Dict, Set

=== CONFIG ===

ADMIN_ID = 6920443520 FORCE_JOIN_CHANNELS = ['@learnWithUs_3', '@lwu_backup'] TOKEN = os.getenv("BOT_TOKEN") or "PUT_YOUR_TOKEN_HERE"

=== Globals ===

users_db: Set[int] = set() blocked_users: Set[int] = set() broadcast_queue: Dict[int, str] = {}

=== Logging ===

logging.basicConfig(level=logging.INFO) logger = logging.getLogger(name)

=== Images ===

WELCOME_IMG = 'https://i.imgur.com/LjV8B6X.jpg' FORCE_IMG = 'https://i.imgur.com/7XvP2cR.jpg' TOOLS_IMG = 'https://i.imgur.com/JWZ9Nf1.jpeg'

=== START ===

async def start(update: Update, context: CallbackContext): user = update.effective_user if user.id in blocked_users: return users_db.add(user.id) if user.id == ADMIN_ID or await check_joined(context, user.id): await show_main_menu(update, context) else: await show_force_join(update, context)

async def check_joined(context, user_id): for channel in FORCE_JOIN_CHANNELS: try: member = await context.bot.get_chat_member(channel, user_id) if member.status not in ["member", "administrator", "creator"]: return False except: return False return True

=== Force Join ===

async def show_force_join(update: Update, context: CallbackContext): buttons = [[InlineKeyboardButton(f"Join {ch}", url=f"https://t.me/{ch[1:]}")] for ch in FORCE_JOIN_CHANNELS] buttons.append([InlineKeyboardButton("✅ I Joined", callback_data="verify")]) await update.message.reply_photo(photo=FORCE_IMG, caption="🚨 Please join all channels to use this bot:", reply_markup=InlineKeyboardMarkup(buttons))

async def verify(update: Update, context: CallbackContext): query = update.callback_query await query.answer() if query.from_user.id == ADMIN_ID or await check_joined(context, query.from_user.id): await show_main_menu(update, context) else: await query.edit_message_caption("❌ You're still not subscribed to all channels.")

=== Main Menu ===

async def show_main_menu(update: Update, context: CallbackContext): buttons = [ [InlineKeyboardButton("👤 Who We Are", callback_data="who"), InlineKeyboardButton("🆘 Help", callback_data="help")], [InlineKeyboardButton("📢 Channels", url="https://t.me/learnWithUs_3")], [InlineKeyboardButton("🧰 Tools", callback_data="tools")] ] if update.effective_user.id == ADMIN_ID: buttons.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin")]) await context.bot.send_photo(chat_id=update.effective_chat.id, photo=WELCOME_IMG, caption="🎉 Welcome! Choose an option below:", reply_markup=InlineKeyboardMarkup(buttons))

=== Menu Navigation ===

async def button_handler(update: Update, context: CallbackContext): query = update.callback_query await query.answer() data = query.data

if data == "who":
    await query.edit_message_text("👥 We are a team providing useful APIs and tools to the public.")
elif data == "help":
    await query.edit_message_text("📩 For help, contact @learnWithUs_3")
elif data == "tools":
    await show_tools_menu(query, context)
elif data.startswith("tool:"):
    await handle_tool_request(data, query, context)
elif data == "back":
    await show_main_menu(update, context)
elif data == "admin":
    await show_admin_panel(query, context)

=== Tools Menu ===

async def show_tools_menu(query, context): tools = [ ("tts", "🔊 Text-to-Speech"), ("insta", "📸 Instagram Downloader"), ("tiktok", "🎵 TikTok Downloader"), ("yt", "📽️ YouTube Downloader"), ("sim", "📞 SIM Info"), ("vehicle", "🚗 Vehicle Info") ] buttons = [[InlineKeyboardButton(label, callback_data=f"tool:{cmd}")] for cmd, label in tools] buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back")]) await query.edit_message_media(media=InputMediaPhoto(media=TOOLS_IMG, caption="🧰 Choose a tool to use:"), reply_markup=InlineKeyboardMarkup(buttons))

=== Tool Pages ===

async def handle_tool_request(data, query, context): tool = data.split(":")[1] usage = { "tts": ("Send me any text and I'll reply with voice.", "https://i.imgur.com/xzOmJG6.jpeg"), "insta": ("Send an Instagram post/reel link.", "https://i.imgur.com/B7h2zkl.jpeg"), "tiktok": ("Send a TikTok video link.", "https://i.imgur.com/W0LBKDR.jpeg"), "yt": ("Send a YouTube video link.", "https://i.imgur.com/d2F6y5s.jpeg"), "sim": ("Send a Pakistani mobile number.", "https://i.imgur.com/19Y1MfN.jpeg"), "vehicle": ("Send vehicle number (e.g., LEX-123).", "https://i.imgur.com/V8reL5p.jpeg") } context.user_data['tool'] = tool await query.edit_message_media( media=InputMediaPhoto(media=usage[tool][1], caption=f"📘 {usage[tool][0]}"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="tools")]]) )

=== Message Handler ===

async def handle_message(update: Update, context: CallbackContext): user_id = update.effective_user.id if user_id in blocked_users: return users_db.add(user_id) text = update.message.text tool = context.user_data.get("tool")

if tool == "tts":
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://text-to-speech.manzoor76b.workers.dev/?text={text}") as resp:
            data = await resp.read()
            await update.message.reply_voice(voice=data)

elif tool == "insta":
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://insta-dl.hazex.workers.dev/?url={text}") as resp:
            result = await resp.json()
            for item in result.get('media', []):
                await update.message.reply_video(video=item)

elif tool == "yt":
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://ochinpo-helper.hf.space/yt?query={text}") as resp:
            result = await resp.json()
            if 'video' in result:
                await update.message.reply_video(result['video'])

elif tool == "sim":
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://ahmadmodstools.online/Apis/Simdata.php?num={text}") as resp:
            sim_data = await resp.text()
            await update.message.reply_text(sim_data)

elif tool == "vehicle":
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://showcase1.bmcci.org.bd/test/vehicleinfo.php?key=test_key&info={text}") as resp:
            result = await resp.text()
            await update.message.reply_text(result)

=== Admin Panel ===

async def show_admin_panel(query, context): if query.from_user.id != ADMIN_ID: return buttons = [ [InlineKeyboardButton("👥 Users Count", callback_data="admin_users")], [InlineKeyboardButton("📣 Broadcast", callback_data="admin_broadcast")], [InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban")], [InlineKeyboardButton("✅ Unban User", callback_data="admin_unban")], [InlineKeyboardButton("🔙 Back", callback_data="back")] ] await query.edit_message_text("👑 Admin Panel:", reply_markup=InlineKeyboardMarkup(buttons))

=== Admin Callbacks ===

async def admin_handler(update: Update, context: CallbackContext): query = update.callback_query await query.answer() data = query.data

if data == "admin_users":
    await query.edit_message_text(f"📊 Total users: {len(users_db)}")

elif data == "admin_broadcast":
    context.user_data['admin_mode'] = 'broadcast'
    await query.edit_message_text("📢 Send message to broadcast to all users:")

elif data == "admin_ban":
    context.user_data['admin_mode'] = 'ban'
    await query.edit_message_text("🚫 Send user ID to ban:")

elif data == "admin_unban":
    context.user_data['admin_mode'] = 'unban'
    await query.edit_message_text("✅ Send user ID to unban:")

=== Admin Text Actions ===

async def handle_admin_text(update: Update, context: CallbackContext): mode = context.user_data.get("admin_mode") user_id = update.effective_user.id if user_id != ADMIN_ID: return

text = update.message.text.strip()

if mode == 'broadcast':
    success = 0
    for uid in users_db:
        try:
            await context.bot.send_message(uid, text)
            success += 1
        except:
            pass
    await update.message.reply_text(f"📣 Broadcast sent to {success} users.")

elif mode == 'ban':
    try:
        blocked_users.add(int(text))
        await update.message.reply_text("🚫 User banned.")
    except:
        await update.message.reply_text("❌ Invalid ID.")

elif mode == 'unban':
    try:
        blocked_users.discard(int(text))
        await update.message.reply_text("✅ User unbanned.")
    except:
        await update.message.reply_text("❌ Invalid ID.")

context.user_data['admin_mode'] = None

=== Init ===

def main(): app = Application.builder().token(TOKEN).build() app.add_handler(CommandHandler("start", start)) app.add_handler(CallbackQueryHandler(verify, pattern="^verify$")) app.add_handler(CallbackQueryHandler(button_handler)) app.add_handler(CallbackQueryHandler(admin_handler, pattern="^admin_")) app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_text)) app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)) print("🤖 Bot is running...") app.run_polling()

if name == 'main': main()