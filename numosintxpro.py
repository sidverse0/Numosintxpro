import logging
import requests
import json
import time
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from telegram.constants import ParseMode

# Bot Configuration - UPDATED WITH YOUR BOT TOKEN
BOT_TOKEN = "8116705267:AAFYOj0Rv-dCTCS-vnFsBq5PoKSfNg2X-_8"
PHONE_API_URL = "https://decryptkarnrwalebkl.wasmer.app/?key=lodalelobaby&term="
VEHICLE_API1_URL = "https://revangevichelinfo.vercel.app/api/rc?number="
VEHICLE_API2_URL = "https://caller.hackershub.shop/info.php?type=address&registration="
IFSC_API_URL = "https://ifsc.razorpay.com/"

# Channel and Admin Configuration
REQUIRED_CHANNEL = "@zarkoworld"
ADMIN_USER_IDS = [7708009915, 7975903577]

# Keep Alive Server Configuration
KEEP_ALIVE_PORT = 8080

# Bot state
bot_active = True
bot_stop_reason = "Bot is currently active"

# Enhanced logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store user data
user_sessions = {}
user_ids = set()

# Style class with emojis
class Style:
    PHONE = "📱"
    CAR = "🚗"
    BANK = "🏦"
    HELP = "❓"
    ADMIN = "👨‍💼"
    HOME = "🏠"
    SEARCH = "🔍"
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    LOADING = "⏳"
    USER = "👤"
    FATHER = "👨‍👦"
    SHIELD = "🛡️"
    ROCKET = "🚀"
    CLOCK = "⏰"
    INFO = "ℹ️"
    CHANNEL = "📢"
    BROADCAST = "📣"
    MEMBERS = "👥"
    DOCUMENT = "📄"
    LOCATION = "📍"
    NETWORK = "📡"
    RELOAD = "🔄"

# Create Flask app for keep-alive
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 OSINT Pro Bot is Running!"

@app.route('/health')
def health():
    return {"status": "healthy", "timestamp": time.time()}

def run_keep_alive():
    """Run the keep-alive server"""
    print(f"🔄 Starting keep-alive server on port {KEEP_ALIVE_PORT}...")
    app.run(host='0.0.0.0', port=KEEP_ALIVE_PORT, debug=False, use_reloader=False)

def get_main_keyboard():
    """Get the main reply keyboard"""
    keyboard = [
        [KeyboardButton(f"{Style.PHONE} Num Info"), KeyboardButton(f"{Style.CAR} RTO Info")],
        [KeyboardButton(f"{Style.BANK} IFSC Info"), KeyboardButton(f"{Style.HELP} Help")],
        [KeyboardButton(f"{Style.ADMIN} Admin")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, persistent=True)

def get_admin_keyboard():
    """Get the admin reply keyboard"""
    keyboard = [
        [KeyboardButton(f"{Style.ROCKET} Start Bot"), KeyboardButton(f"{Style.ERROR} Stop Bot")],
        [KeyboardButton(f"{Style.BROADCAST} Broadcast"), KeyboardButton(f"{Style.MEMBERS} User Count")],
        [KeyboardButton(f"{Style.HOME} Main Menu")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, persistent=True)

def get_search_keyboard():
    """Get search options keyboard"""
    keyboard = [
        [KeyboardButton(f"{Style.PHONE} Phone Search"), KeyboardButton(f"{Style.CAR} Vehicle Search")],
        [KeyboardButton(f"{Style.BANK} IFSC Search"), KeyboardButton(f"{Style.HOME} Main Menu")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, persistent=True)

async def is_user_member(context: CallbackContext, user_id: int) -> bool:
    """Check if user is a member of the required channel"""
    try:
        logger.info(f"Checking membership for user {user_id} in channel {REQUIRED_CHANNEL}")
        chat_member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        is_member = chat_member.status in ['member', 'administrator', 'creator']
        logger.info(f"User {user_id} membership status: {is_member}")
        return is_member
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        return False

async def check_channel_membership(update: Update, context: CallbackContext):
    """Check channel membership and handle accordingly"""
    user_id = update.effective_user.id
    user_ids.add(user_id)
    
    try:
        is_member = await is_user_member(context, user_id)
        if is_member:
            return True
        else:
            await send_channel_join_message(update)
            return False
    except Exception as e:
        logger.error(f"Membership check failed: {e}")
        await send_channel_join_message(update)
        return False

async def send_channel_join_message(update: Update):
    """Send channel join requirement message"""
    channel_message = f"""
{Style.CHANNEL} *CHANNEL MEMBERSHIP REQUIRED* {Style.CHANNEL}

📢 To use this bot, you must join our official channel first!

*Channel:* {REQUIRED_CHANNEL}

{Style.WARNING} *Steps:*
1. Click the button below to join our channel
2. After joining, click 'I've Joined' button
3. Enjoy all bot features!

🔐 *Note:* We only verify membership, no personal data stored.
    """
    
    keyboard = [
        [InlineKeyboardButton(f"{Style.CHANNEL} Join Channel", url=f"https://t.me/zarkoworld")],
        [InlineKeyboardButton(f"{Style.RELOAD} I've Joined", callback_data="check_membership")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(channel_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.callback_query.edit_message_text(channel_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def start(update: Update, context: CallbackContext) -> None:
    """Send welcome message when /start is issued"""
    logger.info(f"🚀 Start command received from user: {update.effective_user.id}")
    
    # Check channel membership
    if not await check_channel_membership(update, context):
        return
    
    # Check bot active status
    if not bot_active:
        await send_bot_stopped_message(update, context)
        return
    
    user = update.effective_user
    
    welcome_text = f"""
{Style.ROCKET} *WELCOME TO ZARKO OSINT BOT* {Style.ROCKET}

👋 Hello *{user.first_name}*!

{Style.SHIELD} *Advanced Intelligence Platform*

✨ *Available Features:*

{Style.PHONE} *Phone Intelligence*
• Complete number analysis
• Carrier information
• Location details

{Style.CAR} *Vehicle Intelligence*  
• Complete RC Information
• Owner details
• Vehicle specifications

{Style.BANK} *Bank IFSC Lookup*
• Bank branch details
• Address information
• Service availability

📋 *How to Use:*
Simply use the buttons below to select your search type!

{Style.WARNING} *Legal Notice:* Use responsibly for legitimate purposes only.
Unauthorized access to information is prohibited.
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )
    logger.info(f"✅ Welcome message sent to user: {update.effective_user.id}")

async def help_command(update: Update, context: CallbackContext) -> None:
    """Send help message"""
    if not await check_channel_membership(update, context):
        return
    
    if not bot_active:
        await send_bot_stopped_message(update, context)
        return
    
    help_text = f"""
{Style.HELP} *HELP GUIDE* {Style.HELP}

{Style.PHONE} *Phone Search:*
1. Click 'Num Info' button
2. Enter 10-digit mobile number
3. Get detailed information including carrier and location

{Style.CAR} *Vehicle Search:*
1. Click 'RTO Info' button  
2. Enter vehicle registration number
3. Get complete RC information and owner details

{Style.BANK} *IFSC Search:*
1. Click 'IFSC Info' button
2. Enter IFSC code
3. Get bank branch details and address

{Style.NETWORK} *Supported Formats:*
• Phone: 7044165702, 9876543210
• Vehicle: UP32AB1234, DL1CAB1234
• IFSC: SBIN0003010, HDFC0000001

{Style.WARNING} *Important:*
• Use only for legitimate purposes
• Respect privacy laws
• Data accuracy depends on external sources
    """
    
    await update.message.reply_text(
        help_text,
        reply_markup=get_main_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_USER_IDS

async def admin_panel(update: Update, context: CallbackContext) -> None:
    """Show admin panel"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text(
            f"{Style.ERROR} *Access Denied* - Admin only feature",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard()
        )
        return
    
    admin_text = f"""
{Style.ADMIN} *ADMIN PANEL* {Style.ADMIN}

🤖 *Bot Status:* {'🟢 ACTIVE' if bot_active else '🔴 STOPPED'}
📝 *Reason:* {bot_stop_reason}
👥 *Total Users:* {len(user_ids)}
⏰ *Last Updated:* {time.strftime('%Y-%m-%d %H:%M:%S')}

🛠️ *Admin Controls:*
• Start/Stop Bot operations
• Broadcast messages to all users
• View user statistics
• Access all search features
    """
    
    await update.message.reply_text(
        admin_text,
        reply_markup=get_admin_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

async def start_bot(update: Update, context: CallbackContext) -> None:
    """Start the bot for all users"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return
    
    global bot_active, bot_stop_reason
    bot_active = True
    bot_stop_reason = "Bot is currently active"
    
    await update.message.reply_text(
        f"{Style.SUCCESS} *Bot Started Successfully!*\n\nAll features are now available to users.",
        reply_markup=get_admin_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

async def stop_bot(update: Update, context: CallbackContext) -> None:
    """Stop the bot with reason"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return
    
    if context.args:
        reason = ' '.join(context.args)
    else:
        await update.message.reply_text(
            f"{Style.WARNING} Usage: /stop [reason]",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    global bot_active, bot_stop_reason
    bot_active = False
    bot_stop_reason = reason
    
    await update.message.reply_text(
        f"{Style.SUCCESS} *Bot Stopped!*\n\nReason: {reason}\n\nUsers will be notified that the bot is temporarily unavailable.",
        reply_markup=get_admin_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

async def broadcast_message(update: Update, context: CallbackContext) -> None:
    """Broadcast message to all users"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return
    
    if not context.args:
        await update.message.reply_text(
            f"{Style.WARNING} Usage: /broadcast [message]",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    message = ' '.join(context.args)
    success_count = 0
    failed_count = 0
    
    processing_msg = await update.message.reply_text(
        f"{Style.LOADING} Broadcasting to {len(user_ids)} users...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    for uid in list(user_ids):
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=f"📢 *BROADCAST MESSAGE*\n\n{message}\n\n*From:* Admin",
                parse_mode=ParseMode.MARKDOWN
            )
            success_count += 1
            time.sleep(0.1)  # Rate limiting
        except Exception as e:
            logger.error(f"Broadcast failed for {uid}: {e}")
            failed_count += 1
    
    await processing_msg.edit_text(
        f"📊 *Broadcast Complete*\n\n✅ Success: {success_count}\n❌ Failed: {failed_count}\n📊 Total: {len(user_ids)}",
        parse_mode=ParseMode.MARKDOWN
    )

async def user_count(update: Update, context: CallbackContext) -> None:
    """Show user count"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return
    
    await update.message.reply_text(
        f"📊 *USER STATISTICS*\n\n👥 Total Users: {len(user_ids)}\n⏰ Last Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        reply_markup=get_admin_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

async def send_bot_stopped_message(update: Update, context: CallbackContext):
    """Send bot stopped message"""
    stop_message = f"""
{Style.ERROR} *BOT TEMPORARILY UNAVAILABLE*

🚫 Bot is currently stopped.

📝 *Reason:* {bot_stop_reason}

🔔 Please check back later or contact admin.

We apologize for the inconvenience.
    """
    await update.message.reply_text(
        stop_message,
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.MARKDOWN
    )

async def check_membership_handler(update: Update, context: CallbackContext) -> None:
    """Handle membership check button"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    is_member = await is_user_member(context, user_id)
    
    if is_member:
        await query.edit_message_text(
            f"{Style.SUCCESS} *Membership Verified!* Welcome to Zarko OSINT Bot.",
            parse_mode=ParseMode.MARKDOWN
        )
        # Send welcome message with keyboard
        user = query.from_user
        welcome_text = f"""
{Style.SUCCESS} *Welcome {user.first_name}!*

You now have full access to all OSINT features.

Use the buttons below to get started:
• 📱 Num Info - Phone number lookup
• 🚗 RTO Info - Vehicle information  
• 🏦 IFSC Info - Bank details
• ❓ Help - Usage guide
        """
        await context.bot.send_message(
            chat_id=user_id,
            text=welcome_text,
            reply_markup=get_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await query.edit_message_text(
            f"{Style.ERROR} *Not Joined Yet* - Please join the channel first and then click 'I've Joined'.",
            parse_mode=ParseMode.MARKDOWN
        )

# Search Handlers
async def phone_search_handler(update: Update, context: CallbackContext) -> None:
    """Handle phone search"""
    if not await check_channel_membership(update, context):
        return
    
    if not bot_active:
        await send_bot_stopped_message(update, context)
        return
    
    await update.message.reply_text(
        f"{Style.PHONE} *PHONE NUMBER LOOKUP*\n\nPlease send the 10-digit mobile number:\n\nExample: `7044165702`",
        reply_markup=get_search_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )
    context.user_data['expecting_phone'] = True

async def vehicle_search_handler(update: Update, context: CallbackContext) -> None:
    """Handle vehicle search"""
    if not await check_channel_membership(update, context):
        return
    
    if not bot_active:
        await send_bot_stopped_message(update, context)
        return
    
    await update.message.reply_text(
        f"{Style.CAR} *VEHICLE INFORMATION LOOKUP*\n\nPlease send the vehicle registration number:\n\nExample: `UP32AB1234`",
        reply_markup=get_search_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )
    context.user_data['expecting_vehicle'] = True

async def ifsc_search_handler(update: Update, context: CallbackContext) -> None:
    """Handle IFSC search"""
    if not await check_channel_membership(update, context):
        return
    
    if not bot_active:
        await send_bot_stopped_message(update, context)
        return
    
    await update.message.reply_text(
        f"{Style.BANK} *IFSC CODE LOOKUP*\n\nPlease send the IFSC code:\n\nExample: `SBIN0003010`",
        reply_markup=get_search_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )
    context.user_data['expecting_ifsc'] = True

# Core functionality functions
def clean_phone_number(number: str) -> str:
    """Clean phone number"""
    cleaned = ''.join(filter(str.isdigit, number))
    if len(cleaned) == 10:
        return cleaned
    elif len(cleaned) == 12 and cleaned.startswith('91'):
        return cleaned[2:]
    return cleaned

def fetch_phone_info(phone_number: str) -> dict:
    """Fetch phone information from API"""
    try:
        response = requests.get(f"{PHONE_API_URL}{phone_number}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return {"error": "API request failed"}
    except Exception as e:
        return {"error": f"API error: {str(e)}"}

def fetch_vehicle_info(vehicle_number: str) -> dict:
    """Fetch vehicle information from APIs"""
    try:
        # Try first API
        response1 = requests.get(f"{VEHICLE_API1_URL}{vehicle_number}", timeout=10)
        if response1.status_code == 200:
            return response1.json()
        
        # Try second API if first fails
        response2 = requests.get(f"{VEHICLE_API2_URL}{vehicle_number}", timeout=10)
        if response2.status_code == 200:
            return response2.json()
            
        return {"error": "Both vehicle APIs failed"}
    except Exception as e:
        return {"error": f"Vehicle API error: {str(e)}"}

def fetch_ifsc_info(ifsc_code: str) -> dict:
    """Fetch IFSC information from API"""
    try:
        response = requests.get(f"{IFSC_API_URL}{ifsc_code}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return {"error": "IFSC not found or invalid"}
    except Exception as e:
        return {"error": f"IFSC API error: {str(e)}"}

async def handle_phone_number(update: Update, context: CallbackContext) -> None:
    """Handle phone number input with actual API integration"""
    number_input = update.message.text
    clean_number = clean_phone_number(number_input)
    
    if len(clean_number) != 10:
        await update.message.reply_text(
            f"{Style.ERROR} *Invalid Number Format*\n\nPlease send a valid 10-digit mobile number.\nExample: `7044165702`",
            reply_markup=get_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    processing_msg = await update.message.reply_text(
        f"{Style.LOADING} Searching for phone number: `{clean_number}`...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Fetch actual data from API
    phone_data = fetch_phone_info(clean_number)
    
    if "error" in phone_data:
        await processing_msg.edit_text(
            f"{Style.ERROR} *Search Failed*\n\nNumber: `{clean_number}`\nError: {phone_data['error']}",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Format the response
        response_text = f"""
{Style.PHONE} *PHONE INFORMATION FOUND*

📱 *Number:* `{clean_number}`
🏢 *Carrier:* {phone_data.get('carrier', 'N/A')}
📍 *Location:* {phone_data.get('location', 'N/A')}
📞 *Type:* {phone_data.get('type', 'N/A')}
🌍 *Country:* {phone_data.get('country', 'India')}

📊 *Additional Details:*
• Status: {phone_data.get('status', 'Active')}
• Ported: {phone_data.get('ported', 'N/A')}

*Data Source:* External API
        """
        await processing_msg.edit_text(response_text, parse_mode=ParseMode.MARKDOWN)
    
    context.user_data['expecting_phone'] = False

async def handle_vehicle_search(update: Update, context: CallbackContext) -> None:
    """Handle vehicle search with actual API integration"""
    vehicle_input = update.message.text.upper().strip()
    
    processing_msg = await update.message.reply_text(
        f"{Style.LOADING} Searching for vehicle: `{vehicle_input}`...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Fetch actual data from API
    vehicle_data = fetch_vehicle_info(vehicle_input)
    
    if "error" in vehicle_data:
        await processing_msg.edit_text(
            f"{Style.ERROR} *Search Failed*\n\nVehicle: `{vehicle_input}`\nError: {vehicle_data['error']}",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Format the response
        response_text = f"""
{Style.CAR} *VEHICLE INFORMATION FOUND*

🚗 *Registration:* `{vehicle_input}`
👤 *Owner:* {vehicle_data.get('owner_name', 'N/A')}
📇 *Father/Husband:* {vehicle_data.get('father_name', 'N/A')}
📍 *Address:* {vehicle_data.get('address', 'N/A')}

🚘 *Vehicle Details:*
• Make: {vehicle_data.get('make', 'N/A')}
• Model: {vehicle_data.get('model', 'N/A')}
• Year: {vehicle_data.get('year', 'N/A')}
• Fuel: {vehicle_data.get('fuel_type', 'N/A')}

📄 *Registration Info:*
• RTO: {vehicle_data.get('rto', 'N/A')}
• Date: {vehicle_data.get('reg_date', 'N/A')}

*Data Source:* External API
        """
        await processing_msg.edit_text(response_text, parse_mode=ParseMode.MARKDOWN)
    
    context.user_data['expecting_vehicle'] = False

async def handle_ifsc_search(update: Update, context: CallbackContext) -> None:
    """Handle IFSC search with actual API integration"""
    ifsc_input = update.message.text.upper().strip()
    
    processing_msg = await update.message.reply_text(
        f"{Style.LOADING} Searching for IFSC: `{ifsc_input}`...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Fetch actual data from API
    ifsc_data = fetch_ifsc_info(ifsc_input)
    
    if "error" in ifsc_data:
        await processing_msg.edit_text(
            f"{Style.ERROR} *Search Failed*\n\nIFSC: `{ifsc_input}`\nError: {ifsc_data['error']}",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Format the response
        response_text = f"""
{Style.BANK} *BANK INFORMATION FOUND*

🏦 *Bank:* {ifsc_data.get('BANK', 'N/A')}
🏢 *Branch:* {ifsc_data.get('BRANCH', 'N/A')}
📍 *Address:* {ifsc_data.get('ADDRESS', 'N/A')}
📞 *Contact:* {ifsc_data.get('CONTACT', 'N/A')}
🏙️ *City:* {ifsc_data.get('CITY', 'N/A')}
📮 *District:* {ifsc_data.get('DISTRICT', 'N/A')}
🏛️ *State:* {ifsc_data.get('STATE', 'N/A')}

💳 *Services:*
• RTGS: {ifsc_data.get('RTGS', 'No')}
• NEFT: {ifsc_data.get('NEFT', 'No')}
• IMPS: {ifsc_data.get('IMPS', 'No')}
• UPI: {ifsc_data.get('UPI', 'No')}

*Data Source:* Razorpay IFSC API
        """
        await processing_msg.edit_text(response_text, parse_mode=ParseMode.MARKDOWN)
    
    context.user_data['expecting_ifsc'] = False

# Main message handler
async def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle all messages"""
    user_ids.add(update.effective_user.id)
    
    if not bot_active:
        await send_bot_stopped_message(update, context)
        return
    
    text = update.message.text
    
    # Handle button presses
    if text == f"{Style.PHONE} Num Info":
        await phone_search_handler(update, context)
        return
    elif text == f"{Style.CAR} RTO Info":
        await vehicle_search_handler(update, context)
        return
    elif text == f"{Style.BANK} IFSC Info":
        await ifsc_search_handler(update, context)
        return
    elif text == f"{Style.HELP} Help":
        await help_command(update, context)
        return
    elif text == f"{Style.ADMIN} Admin":
        await admin_panel(update, context)
        return
    elif text == f"{Style.ROCKET} Start Bot":
        await start_bot(update, context)
        return
    elif text == f"{Style.ERROR} Stop Bot":
        await update.message.reply_text("Use: /stop [reason]")
        return
    elif text == f"{Style.BROADCAST} Broadcast":
        await update.message.reply_text("Use: /broadcast [message]")
        return
    elif text == f"{Style.MEMBERS} User Count":
        await user_count(update, context)
        return
    elif text == f"{Style.HOME} Main Menu":
        await start(update, context)
        return
    elif text == f"{Style.PHONE} Phone Search":
        await phone_search_handler(update, context)
        return
    elif text == f"{Style.CAR} Vehicle Search":
        await vehicle_search_handler(update, context)
        return
    elif text == f"{Style.BANK} IFSC Search":
        await ifsc_search_handler(update, context)
        return
    
    # Check for expected inputs
    if context.user_data.get('expecting_phone'):
        await handle_phone_number(update, context)
        return
    elif context.user_data.get('expecting_vehicle'):
        await handle_vehicle_search(update, context)
        return
    elif context.user_data.get('expecting_ifsc'):
        await handle_ifsc_search(update, context)
        return
    
    # Auto-detect input type
    cleaned_phone = clean_phone_number(text)
    if len(cleaned_phone) == 10:
        await handle_phone_number(update, context)
        return
    
    # Check if it might be a vehicle number (basic pattern)
    if len(text) >= 8 and len(text) <= 12 and any(c.isalpha() for c in text) and any(c.isdigit() for c in text):
        await handle_vehicle_search(update, context)
        return
    
    # Check if it might be an IFSC code (typically 11 characters)
    if len(text) == 11 and text[:4].isalpha() and text[4:].isalnum():
        await handle_ifsc_search(update, context)
        return
    
    # Default response
    await update.message.reply_text(
        f"{Style.INFO} *ZARKO OSINT BOT*\n\nPlease use the buttons below to select your search type:\n\n• 📱 Phone number lookup\n• 🚗 Vehicle information\n• 🏦 Bank IFSC details\n• ❓ Help guide\n• 👨‍💼 Admin panel",
        reply_markup=get_main_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

def main() -> None:
    """Start the bot"""
    # Start keep-alive server
    keep_alive_thread = threading.Thread(target=run_keep_alive, daemon=True)
    keep_alive_thread.start()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stop", stop_bot))
    application.add_handler(CommandHandler("broadcast", broadcast_message))
    application.add_handler(CallbackQueryHandler(check_membership_handler, pattern="^check_membership$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start bot
    print("🚀 Starting Zarko OSINT Bot...")
    print(f"📊 Bot Token: {BOT_TOKEN[:10]}...")
    print(f"📢 Required Channel: {REQUIRED_CHANNEL}")
    print(f"👑 Admin Users: {ADMIN_USER_IDS}")
    print(f"🌐 Keep-alive server running on port {KEEP_ALIVE_PORT}")
    print("✅ Bot is ready and polling for messages...")
    
    try:
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Bot failed: {e}")
        print(f"❌ Bot error: {e}")

if __name__ == '__main__':

    main()
