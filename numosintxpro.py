import os
import logging
import re
import json
import asyncio
from flask import Flask
import requests

# Bot configuration
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
PORT = int(os.environ.get('PORT', 5000))

app = Flask(__name__)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# API endpoint
PHONE_API_URL = "https://decryptkarnrwalebkl.wasmer.app/?key=lodalelobaby&term="

# Try to import telegram with compatibility
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError as e:
    logger.error(f"Telegram import error: {e}")
    TELEGRAM_AVAILABLE = False

def normalize_phone_number(phone_number):
    """
    Normalize phone number by:
    - Removing spaces, special characters
    - Ensuring 10 digits
    - Validating Indian format
    """
    # Remove all non-digit characters
    normalized = re.sub(r'\D', '', phone_number)
    
    # Check if it's 10 digits
    if len(normalized) == 10:
        return normalized, "✅ Valid phone number"
    elif len(normalized) > 10:
        # Take last 10 digits if more than 10
        if len(normalized) >= 10:
            return normalized[-10:], "✅ Using last 10 digits"
    else:
        return None, "❌ Phone number must be 10 digits"
    
    return None, "❌ Invalid phone number format"

def escape_markdown(text):
    """Escape special Markdown characters"""
    if not text:
        return ""
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + char if char in escape_chars else char for char in str(text)])

def clean_text(text):
    """Clean and format text by removing extra spaces and special characters"""
    if not text:
        return "N/A"
    # Remove extra spaces and clean the text
    cleaned = re.sub(r'\s+', ' ', str(text).strip())
    return cleaned

def format_address(address):
    """Format address by replacing ! with commas and cleaning"""
    if not address:
        return "N/A"
    
    # Replace ! with commas and clean
    formatted = address.replace('!', ', ')
    # Remove extra spaces and clean
    formatted = re.sub(r'\s+', ' ', formatted)
    # Remove duplicate commas
    formatted = re.sub(r',\s*,', ',', formatted)
    # Add space after commas
    formatted = re.sub(r',', ', ', formatted)
    # Remove extra spaces around commas
    formatted = re.sub(r'\s*,\s*', ', ', formatted)
    
    return formatted.strip()

def safe_json_parse(response_text):
    """Safely parse JSON response and handle errors"""
    try:
        # First try direct JSON parsing
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        
        # Try to fix common JSON issues
        try:
            # Remove extra data after the main JSON
            if '}{' in response_text:
                # Take only the first JSON object
                response_text = response_text.split('}{')[0] + '}'
            
            # Try to find valid JSON structure
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                cleaned_json = response_text[start_idx:end_idx]
                return json.loads(cleaned_json)
            else:
                return {"error": "Invalid JSON response from API"}
                
        except Exception as e2:
            logger.error(f"JSON cleanup failed: {e2}")
            return {"error": f"JSON parsing failed: {str(e2)}"}

def get_relevant_results(data, searched_number):
    """Get relevant results that match the searched mobile number"""
    if not data or 'data' not in data:
        return []
    
    seen = set()
    relevant_results = []
    
    for item in data['data']:
        # Check if this item is relevant to the searched number
        mobile = item.get('mobile', '')
        alt = item.get('alt', '')
        
        # Include if mobile matches searched number OR alt matches searched number
        if mobile == searched_number or alt == searched_number:
            # Create a unique key based on mobile and cleaned name
            name = clean_text(item.get('name', ''))
            unique_key = f"{mobile}_{name}"
            
            if unique_key not in seen:
                seen.add(unique_key)
                relevant_results.append(item)
                
                # Stop when we have 2 unique results
                if len(relevant_results) >= 2:
                    break
    
    return relevant_results

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with inline keyboard"""
    keyboard = [
        [InlineKeyboardButton("📱 Phone Search", callback_data='search_phone')],
        [InlineKeyboardButton("ℹ️ Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = """
📱 *Welcome to Phone Info Bot* 📱

I can help you get detailed information about any phone number.

*Features:*
• 👤 Name & Father Name
• 🏠 Complete Address
• 📞 Alternative Numbers
• 🌐 Telecom Circle

Click the button below to start searching!
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button clicks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'search_phone':
        await query.edit_message_text(
            "📱 *Phone Number Search*\n\nPlease enter the 10-digit phone number:\n\n*Examples:* \n• `9525416052`\n• `9142647694`\n• `9876543210`",
            parse_mode='Markdown'
        )
        context.user_data['waiting_for_phone'] = True
        
    elif query.data == 'help':
        help_text = """
*🤖 How to Use This Bot:*

1. 📱 Click *"Phone Search"* button
2. 🔢 Enter 10-digit phone number in *any format*:
   - 9525416052
   - 91 9525 416052
   - +919525416052
   - 09525416052
3. 📊 Get detailed information with relevant results

*⚡ Smart Features:*
• 🔄 Auto number normalization
• 👤 Name & Family Details
• 🏠 Complete Address
• 📞 Alternative Numbers
• 🎯 Only relevant results
        """
        await query.edit_message_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📱 Start Search", callback_data='search_phone')]
            ])
        )
    elif query.data == 'home':
        await home_handler(update, context)

def get_phone_info(phone_number):
    """Fetch phone information from API with better error handling"""
    try:
        response = requests.get(f"{PHONE_API_URL}{phone_number}", timeout=15)
        
        if response.status_code != 200:
            return {"error": f"API returned status code: {response.status_code}"}
        
        # Use safe JSON parsing
        data = safe_json_parse(response.text)
        
        if 'error' in data:
            return data
            
        return data
        
    except requests.exceptions.Timeout:
        return {"error": "API request timeout"}
    except requests.exceptions.ConnectionError:
        return {"error": "Connection error - please try again"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def format_phone_result(result, result_number):
    """Format single phone result with emojis"""
    message = f"📊 *RESULT {result_number}:*\n\n"
    
    message += f"📞 *Mobile:* `{escape_markdown(result.get('mobile', 'N/A'))}`\n"
    message += f"👤 *Name:* {escape_markdown(clean_text(result.get('name', 'N/A')))}\n"
    message += f"👨‍👦 *Father:* {escape_markdown(clean_text(result.get('fname', 'N/A')))}\n"
    
    # Format address properly with commas
    address = format_address(result.get('address', ''))
    message += f"🏠 *Address:* {escape_markdown(address)}\n"
    
    if result.get('alt'):
        message += f"📞 *Alt Number:* `{escape_markdown(result.get('alt', 'N/A'))}`\n"
    
    message += f"🌐 *Circle:* {escape_markdown(result.get('circle', 'N/A'))}\n"
    
    if result.get('id'):
        message += f"🆔 *ID:* {escape_markdown(result.get('id', 'N/A'))}\n"
    
    if result.get('email'):
        message += f"📧 *Email:* {escape_markdown(result.get('email', 'N/A'))}\n"
    
    return message

def format_phone_results(searched_number, data):
    """Format all phone results"""
    message = f"📱 *Phone Information for {escape_markdown(searched_number)}*\n\n"
    message += "═" * 40 + "\n\n"
    
    if 'error' in data:
        message += f"❌ *Error:* {escape_markdown(data['error'])}\n"
        return message
    
    if not data.get('data'):
        message += "❌ *No data found for this number*\n\n"
        message += "*Possible reasons:*\n"
        message += "• Number not in database\n"
        message += "• Try different number\n"
        message += "• Number might be new/unregistered\n"
        return message
    
    relevant_results = get_relevant_results(data, searched_number)
    
    if not relevant_results:
        message += "❌ *No relevant results found*\n\n"
        message += "No records found matching the searched number\n"
        return message
    
    # Add result count info
    total_results = len(data.get('data', []))
    relevant_count = len(relevant_results)
    message += f"📈 *Found {total_results} total results, showing {relevant_count} relevant*\n\n"
    
    # Format each relevant result
    for i, result in enumerate(relevant_results, 1):
        message += format_phone_result(result, i)
        if i < len(relevant_results):  # Don't add separator after last result
            message += "\n" + "─" * 30 + "\n\n"
    
    message += "\n" + "═" * 40 + "\n"
    message += "🔄 *Search again\\? Use the button below\\!*"
    
    return message

def split_long_message(message, max_length=4096):
    """Split long messages into multiple parts"""
    if len(message) <= max_length:
        return [message]
    
    parts = []
    while len(message) > max_length:
        # Find the last newline before max_length
        split_index = message.rfind('\n', 0, max_length)
        if split_index == -1:
            split_index = max_length
        
        parts.append(message[:split_index])
        message = message[split_index:].lstrip()
    
    if message:
        parts.append(message)
    
    return parts

async def handle_phone_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle phone number input from user"""
    
    if not context.user_data.get('waiting_for_phone'):
        return
    
    phone_number = update.message.text.strip()
    
    # Normalize phone number
    normalized_number, message = normalize_phone_number(phone_number)
    
    if normalized_number is None:
        await update.message.reply_text(
            f"{message}\n\n*Please enter a valid 10-digit phone number:*\n\n*Examples:* \n• `9525416052`\n• `9142647694`\n• `9876543210`",
            parse_mode='Markdown'
        )
        return
    
    # Show normalization info
    if phone_number != normalized_number:
        await update.message.reply_text(
            f"🔄 *Number Normalized:*\n`{phone_number}` → `{normalized_number}`",
            parse_mode='Markdown'
        )
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        f"🔍 *Searching for {escape_markdown(normalized_number)}\\.\\.\\.*\n\n⏳ Please wait while we fetch the information\\.\\.\\.",
        parse_mode='MarkdownV2'
    )
    
    try:
        # Get phone information
        data = get_phone_info(normalized_number)
        
        # Check if API returned error
        if 'error' in data:
            error_text = f"❌ *API Error\\!*\n\n{escape_markdown(data['error'])}\n\nPlease try again later\\."
            
            await context.bot.edit_message_text(
                chat_id=processing_msg.chat_id,
                message_id=processing_msg.message_id,
                text=error_text,
                parse_mode='MarkdownV2',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Try Again", callback_data='search_phone')],
                    [InlineKeyboardButton("🏠 Home", callback_data='home')]
                ])
            )
            return
        
        # Check if no data found
        if not data.get('data'):
            error_text = f"❌ *No Data Found\\!*\n\nNo information found for `{escape_markdown(normalized_number)}`\n\n*Possible reasons:*\n• Number not in database\n• Try different number\n• Number might be new"
            
            await context.bot.edit_message_text(
                chat_id=processing_msg.chat_id,
                message_id=processing_msg.message_id,
                text=error_text,
                parse_mode='MarkdownV2',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Try Again", callback_data='search_phone')],
                    [InlineKeyboardButton("🏠 Home", callback_data='home')]
                ])
            )
            return
        
        # Format and send results
        result_message = format_phone_results(normalized_number, data)
        
        # Split message if too long
        message_parts = split_long_message(result_message)
        
        # Create keyboard for new search
        keyboard = [
            [InlineKeyboardButton("🔄 Search Again", callback_data='search_phone')],
            [InlineKeyboardButton("🏠 Home", callback_data='home')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Delete processing message
        await context.bot.delete_message(
            chat_id=processing_msg.chat_id,
            message_id=processing_msg.message_id
        )
        
        # Send message parts
        for i, part in enumerate(message_parts):
            if i == len(message_parts) - 1:
                # Last part gets the buttons
                await update.message.reply_text(
                    part,
                    parse_mode='MarkdownV2',
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    part,
                    parse_mode='MarkdownV2'
                )
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        error_text = f"❌ *Unexpected Error\\!*\n\nPlease try again later\\.\n\n⚡ Error: {escape_markdown(str(e))}"
        await context.bot.edit_message_text(
            chat_id=processing_msg.chat_id,
            message_id=processing_msg.message_id,
            text=error_text,
            parse_mode='MarkdownV2'
        )
    
    # Reset the waiting state
    context.user_data['waiting_for_phone'] = False

async def home_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle home button"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📱 Phone Search", callback_data='search_phone')],
        [InlineKeyboardButton("ℹ️ Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = """
📱 *Welcome to Phone Info Bot* 📱

I can help you get detailed information about any phone number\\.

*Smart Features:*
• 🔄 Auto number normalization
• 👤 Name & Family Details
• 🏠 Complete Address
• 📞 Alternative Numbers
• 🎯 Only relevant results

Click the button below to start searching\\!
    """
    
    await query.edit_message_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )

def start_bot():
    """Start the bot"""
    if not TELEGRAM_AVAILABLE:
        logger.error("Telegram library not available. Bot cannot start.")
        return
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CallbackQueryHandler(button_handler, pattern='^(search_phone|help|home)$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_input))
    
    # Start the Bot
    application.run_polling()

@app.route('/')
def index():
    return "📱 Phone Info Bot is running!"

@app.route('/health')
def health():
    return "✅ Bot is healthy"

def main():
    """Main function to start both Flask app and Telegram bot"""
    # Start bot in a separate thread
    import threading
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start Flask app
    app.run(host='0.0.0.0', port=PORT, debug=False)

if __name__ == '__main__':
    main()