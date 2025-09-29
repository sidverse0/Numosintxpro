import os
import logging
import re
import json
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Bot configuration
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8116705267:AAHuwa5tUK2sErOtTf64StZ4STOQUv2Abp4')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# API endpoint
PHONE_API_URL = "https://decryptkarnrwalebkl.wasmer.app/?key=lodalelobaby&term="

def normalize_phone_number(phone_number):
    """Normalize phone number to 10 digits"""
    normalized = re.sub(r'\D', '', phone_number)
    
    if len(normalized) == 10:
        return normalized, "✅ Valid phone number"
    elif len(normalized) > 10:
        return normalized[-10:], "✅ Using last 10 digits"
    else:
        return None, "❌ Phone number must be 10 digits"

def escape_markdown(text):
    """Escape special Markdown characters"""
    if not text:
        return ""
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + char if char in escape_chars else char for char in str(text)])

def clean_text(text):
    """Clean and format text"""
    if not text:
        return "N/A"
    return re.sub(r'\s+', ' ', str(text).strip())

def format_address(address):
    """Format address by replacing ! with commas"""
    if not address:
        return "N/A"
    
    formatted = address.replace('!', ', ')
    formatted = re.sub(r'\s+', ' ', formatted)
    formatted = re.sub(r',\s*,', ',', formatted)
    formatted = re.sub(r',', ', ', formatted)
    formatted = re.sub(r'\s*,\s*', ', ', formatted)
    
    return formatted.strip()

def safe_json_parse(response_text):
    """Safely parse JSON response"""
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        try:
            # Try to extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                cleaned_json = response_text[start_idx:end_idx]
                return json.loads(cleaned_json)
            else:
                return {"error": "Invalid JSON response"}
        except Exception as e:
            return {"error": f"JSON parsing failed: {str(e)}"}

def get_all_relevant_results(data, searched_number):
    """Get ALL relevant results that match the searched mobile number"""
    if not data or 'data' not in data:
        return []
    
    seen = set()
    relevant_results = []
    
    for item in data['data']:
        mobile = item.get('mobile', '')
        alt = item.get('alt', '')
        
        # Include if mobile matches searched number OR alt matches searched number
        if mobile == searched_number or alt == searched_number:
            # Create a unique key based on mobile, name, and address to avoid exact duplicates
            name = clean_text(item.get('name', ''))
            address = clean_text(item.get('address', ''))
            unique_key = f"{mobile}_{name}_{address}"
            
            if unique_key not in seen:
                seen.add(unique_key)
                relevant_results.append(item)
    
    return relevant_results

def get_phone_info(phone_number):
    """Fetch phone information from API"""
    try:
        logger.info(f"Fetching info for number: {phone_number}")
        response = requests.get(f"{PHONE_API_URL}{phone_number}", timeout=15)
        logger.info(f"API Response status: {response.status_code}")
        
        if response.status_code != 200:
            return {"error": f"API returned status code: {response.status_code}"}
        
        data = safe_json_parse(response.text)
        logger.info(f"Parsed data keys: {list(data.keys()) if data else 'No data'}")
        return data
        
    except requests.exceptions.Timeout:
        return {"error": "API request timeout"}
    except requests.exceptions.ConnectionError:
        return {"error": "Connection error - please try again"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def format_phone_result(result, result_number):
    """Format single phone result with beautiful emojis"""
    message = f"🔢 **RESULT {result_number}:**\n\n"
    
    message += f"📱 **Mobile:** `{escape_markdown(result.get('mobile', 'N/A'))}`\n"
    message += f"👨‍💼 **Name:** {escape_markdown(clean_text(result.get('name', 'N/A')))}\n"
    message += f"👨‍👦 **Father:** {escape_markdown(clean_text(result.get('fname', 'N/A')))}\n"
    
    address = format_address(result.get('address', ''))
    message += f"🏡 **Address:** {escape_markdown(address)}\n"
    
    if result.get('alt'):
        message += f"📞 **Alt Number:** `{escape_markdown(result.get('alt', 'N/A'))}`\n"
    
    message += f"🌍 **Circle:** {escape_markdown(result.get('circle', 'N/A'))}\n"
    
    if result.get('id'):
        message += f"🆔 **ID:** {escape_markdown(result.get('id', 'N/A'))}\n"
    
    if result.get('email'):
        message += f"📧 **Email:** {escape_markdown(result.get('email', 'N/A'))}\n"
    
    return message

def format_phone_results(searched_number, data):
    """Format all phone results with beautiful formatting"""
    message = f"🔍 **Phone Intelligence Report** 📱\n\n"
    message += f"📊 **Search Query:** `{escape_markdown(searched_number)}`\n\n"
    message += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
    
    if 'error' in data:
        message += f"❌ **API Error:** {escape_markdown(data['error'])}\n"
        return message
    
    if not data.get('data'):
        message += "🚫 **No Data Found**\n\n"
        message += "**Possible Reasons:**\n"
        message += "• 📵 Number not in database\n"
        message += "• 🔄 Try different number\n"
        message += "• 🆕 Number might be new/unregistered\n"
        return message
    
    relevant_results = get_all_relevant_results(data, searched_number)
    
    if not relevant_results:
        message += "🤷‍♂️ **No Relevant Results Found**\n\n"
        message += "No records found matching the searched number\n"
        return message
    
    # Add result count info with emojis
    total_results = len(data.get('data', []))
    relevant_count = len(relevant_results)
    message += f"📈 **Database Scan Complete**\n"
    message += f"• 📋 Total Records: {total_results}\n"
    message += f"• ✅ Relevant Found: {relevant_count}\n\n"
    message += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
    
    # Format each relevant result
    for i, result in enumerate(relevant_results, 1):
        message += format_phone_result(result, i)
        if i < len(relevant_results):
            message += "\n" + "─" * 35 + "\n\n"
    
    message += "\n" + "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
    message += "🔄 **Want to search again?**\n"
    message += "📱 Use the buttons below!"
    
    return message

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with beautiful inline keyboard"""
    keyboard = [
        [InlineKeyboardButton("🔍 Phone Search", callback_data='search_phone')],
        [InlineKeyboardButton("ℹ️ Help Guide", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = """
🎯 **Welcome to Phone Intelligence Bot** 🔍

I can help you get detailed information about any phone number with precision and speed.

✨ **Features:**
• 👨‍💼 Name & Family Details
• 🏡 Complete Address Information  
• 📞 Alternative Contact Numbers
• 🌍 Telecom Circle & Operator

🚀 **Get started by clicking the search button below!**
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message with detailed instructions"""
    keyboard = [
        [InlineKeyboardButton("🔍 Start Search", callback_data='search_phone')],
        [InlineKeyboardButton("🏠 Main Menu", callback_data='home')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    help_text = """
📖 **How to Use This Bot:** 🤖

1️⃣ **Click** *"Phone Search"* button
2️⃣ **Enter** 10-digit phone number:
   📝 **Examples:**
   • `9525416053`
   • `9142647674`  
   • `9876543290`
3️⃣ **Receive** detailed intelligence report

⚡ **Smart Features:**
• 🔄 Auto number normalization
• 👨‍💼 Comprehensive name details
• 🏡 Complete address mapping
• 📞 Alternative number tracking
    """
    
    await update.message.reply_text(
        help_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button clicks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'search_phone':
        await query.edit_message_text(
            "🔍 **Phone Number Search** 📱\n\nPlease enter the 10-digit phone number:\n\n**Examples:** \n• `9525416052`\n• `9142647694`\n• `9876543210`",
            parse_mode='Markdown'
        )
        context.user_data['waiting_for_phone'] = True
        
    elif query.data == 'help':
        keyboard = [
            [InlineKeyboardButton("🔍 Start Search", callback_data='search_phone')],
            [InlineKeyboardButton("🏠 Main Menu", callback_data='home')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        help_text = """
📖 **How to Use This Bot:** 🤖

1️⃣ **Click** *"Phone Search"* button
2️⃣ **Enter** 10-digit phone number:
   📝 **Examples:**
   • `9525413052`
   • `9142647894`  
   • `9876546210`
3️⃣ **Receive** detailed intelligence report

⚡ **Smart Features:**
• 🔄 Auto number normalization
• 👨‍💼 Comprehensive name details
• 🏡 Complete address mapping
• 📞 Alternative number tracking
        """
        
        await query.edit_message_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    elif query.data == 'home':
        keyboard = [
            [InlineKeyboardButton("🔍 Phone Search", callback_data='search_phone')],
            [InlineKeyboardButton("ℹ️ Help Guide", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = """
🎯 **Welcome to Phone Intelligence Bot** 🔍

I can help you get detailed information about any phone number with precision and speed.

✨ **Features:**
• 👨‍💼 Name & Family Details
• 🏡 Complete Address Information  
• 📞 Alternative Contact Numbers
• 🌍 Telecom Circle & Operator

🚀 **Get started by clicking the search button below!**
        """
        
        await query.edit_message_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def handle_phone_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle phone number input from user"""
    
    if not context.user_data.get('waiting_for_phone'):
        # If user sends a number without clicking button first
        phone_number = update.message.text.strip()
        if re.search(r'\d', phone_number) and len(re.sub(r'\D', '', phone_number)) >= 10:
            # Process it directly
            await process_phone_search(update, context, phone_number)
        else:
            keyboard = [
                [InlineKeyboardButton("🔍 Phone Search", callback_data='search_phone')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "🤔 I'm not sure what you want to do. Please click the button below to start phone search!",
                reply_markup=reply_markup
            )
        return
    
    phone_number = update.message.text.strip()
    await process_phone_search(update, context, phone_number)

async def process_phone_search(update: Update, context: ContextTypes.DEFAULT_TYPE, phone_number: str):
    """Process phone number search with enhanced UX"""
    # Clear waiting state
    context.user_data['waiting_for_phone'] = False
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        f"🕵️‍♂️ **Launching Investigation** 🔍\n\n**Target:** `{escape_markdown(phone_number)}`\n\n⏳ Scanning databases...",
        parse_mode='MarkdownV2'
    )
    
    # Normalize phone number
    normalized_number, message = normalize_phone_number(phone_number)
    
    if normalized_number is None:
        await context.bot.delete_message(
            chat_id=processing_msg.chat_id,
            message_id=processing_msg.message_id
        )
        await update.message.reply_text(
            f"❌ **Invalid Input** 🚫\n\n{message}\n\n**Please enter a valid 10-digit phone number.**",
            parse_mode='Markdown'
        )
        return
    
    # Show normalization info if needed
    if phone_number != normalized_number:
        await context.bot.delete_message(
            chat_id=processing_msg.chat_id,
            message_id=processing_msg.message_id
        )
        normalization_msg = await update.message.reply_text(
            f"🔄 **Number Normalized** ✅\n\n`{phone_number}` → `{normalized_number}`",
            parse_mode='Markdown'
        )
        processing_msg = await update.message.reply_text(
            f"🔍 **Searching for** `{escape_markdown(normalized_number)}`...",
            parse_mode='MarkdownV2'
        )
    
    # Get phone information
    data = get_phone_info(normalized_number)
    
    # Check if API returned error
    if 'error' in data:
        await context.bot.delete_message(
            chat_id=processing_msg.chat_id,
            message_id=processing_msg.message_id
        )
        error_text = f"❌ **API Error** 🔌\n\n{escape_markdown(data['error'])}"
        keyboard = [
            [InlineKeyboardButton("🔄 Try Again", callback_data='search_phone')],
            [InlineKeyboardButton("🏠 Main Menu", callback_data='home')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            error_text,
            reply_markup=reply_markup,
            parse_mode='MarkdownV2'
        )
        return
    
    # Check if no data found
    if not data.get('data'):
        await context.bot.delete_message(
            chat_id=processing_msg.chat_id,
            message_id=processing_msg.message_id
        )
        error_text = f"🔍 **No Data Found** 🕵️‍♂️\n\nNumber: `{escape_markdown(normalized_number)}`"
        keyboard = [
            [InlineKeyboardButton("🔄 Try Different Number", callback_data='search_phone')],
            [InlineKeyboardButton("🏠 Main Menu", callback_data='home')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            error_text,
            reply_markup=reply_markup,
            parse_mode='MarkdownV2'
        )
        return
    
    # Format and send results
    result_message = format_phone_results(normalized_number, data)
    
    # Delete processing message
    await context.bot.delete_message(
        chat_id=processing_msg.chat_id,
        message_id=processing_msg.message_id
    )
    
    keyboard = [
        [InlineKeyboardButton("🔍 New Search", callback_data='search_phone')],
        [InlineKeyboardButton("🏠 Main Menu", callback_data='home')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        result_message,
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )

def main() -> None:
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler, pattern='^(search_phone|help|home)$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_input))
    
    # Start the Bot
    print("🤖 Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()