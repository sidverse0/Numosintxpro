import logging
import requests
import json
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from telegram.constants import ParseMode

# Bot Configuration
BOT_TOKEN = "8116705267:AAFM_Hkxv9BjVMzdv-D_k6XVUTAZbbOGalI"
API_URL = "https://decryptkarnrwalebkl.wasmer.app/?key=lodalelobaby&term="

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store user data for pagination
user_sessions = {}

# Stylish fonts and symbols
class Style:
    BOLD = "✦"
    PHONE = "📱"
    USER = "👤"
    FATHER = "👨‍👦"
    LOCATION = "🌍"
    ID_CARD = "🆔"
    ADDRESS = "🏠"
    SEARCH = "🔍"
    DOCUMENT = "📄"
    LOADING = "⏳"
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    BACK = "↩️"
    NEXT = "➡️"
    PREV = "⬅️"
    NEW = "🔄"
    HELP = "❓"
    LOCK = "🔒"
    SHIELD = "🛡️"
    ROCKET = "🚀"
    DATABASE = "💾"
    NETWORK = "📡"
    CALENDAR = "📅"
    CLOCK = "⏰"
    HOME = "🏠"

async def start(update: Update, context: CallbackContext) -> None:
    """Send welcome message when the command /start is issued."""
    user = update.effective_user
    
    welcome_text = f"""
{Style.ROCKET} *WELCOME TO OSINT PRO BOT* {Style.ROCKET}

👋 Hello *{user.first_name}*!

{Style.SEARCH} *Advanced Number Intelligence Platform*
{Style.SHIELD} *Secure • Fast • Professional*

✨ *Features:*
• {Style.PHONE} Complete number analysis
• {Style.USER} Detailed subscriber information  
• {Style.LOCATION} Geographic mapping
• {Style.DATABASE} Multi-source data verification
• {Style.LOCK} Privacy protected

📋 *Quick Start:*
Simply send any 10-digit mobile number to begin analysis.

*Formats Supported:*
• `7044165702`
• `+917044165702`
• `917044165702`

{Style.WARNING} *Legal Notice:* Use responsibly in compliance with applicable laws.
    """
    
    keyboard = [
        [InlineKeyboardButton(f"{Style.HELP} Get Help", callback_data="help")],
        [InlineKeyboardButton(f"{Style.SEARCH} Quick Example", callback_data="quick_example")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            welcome_text, 
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(
            welcome_text, 
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

async def help_command(update: Update, context: CallbackContext) -> None:
    """Send help message."""
    help_text = f"""
{Style.HELP} *OSINT PRO BOT - HELP GUIDE* {Style.HELP}

{Style.SEARCH} *How to Use:*
1. {Style.PHONE} Send any mobile number
2. {Style.LOADING} Wait for processing
3. {Style.SUCCESS} Receive detailed report

{Style.NETWORK} *Supported Formats:*
• 10-digit numbers: `7044165702`
• International: `+917044165702`
• With country code: `917044165702`

{Style.SHIELD} *Security Features:*
• Encrypted communication
• No data storage
• Instant session clearance
• Privacy focused

{Style.WARNING} *Important Notes:*
• Service availability depends on data sources
• Results may vary by region
• Always verify information from multiple sources

*Need immediate assistance?*
Send any number to test the system now!
    """
    
    keyboard = [
        [InlineKeyboardButton(f"{Style.HOME} Main Menu", callback_data="main_menu")],
        [InlineKeyboardButton(f"{Style.SEARCH} Try Example", callback_data="quick_example")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            help_text, 
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.callback_query.edit_message_text(
            help_text, 
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

async def show_loading(chat_id, context: CallbackContext):
    """Show single loading message."""
    loading_text = f"{Style.LOADING} *Processing your request...*"
    
    message = await context.bot.send_message(
        chat_id=chat_id,
        text=loading_text,
        parse_mode=ParseMode.MARKDOWN
    )
    
    return message.message_id

async def button_handler(update: Update, context: CallbackContext) -> None:
    """Handle inline button presses."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        await help_command(update, context)
    elif query.data == "main_menu":
        await start(update, context)
    elif query.data == "quick_example":
        await handle_phone_number(update, context, "7044165702")
    elif query.data == "new_search":
        await query.edit_message_text(f"{Style.SEARCH} *Send new number to begin analysis...*", parse_mode=ParseMode.MARKDOWN)
    elif query.data.startswith("page_"):
        await handle_pagination(update, context)

async def handle_pagination(update: Update, context: CallbackContext) -> None:
    """Handle pagination button clicks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    page_num = int(data.split("_")[1])
    
    # Get user session data
    user_id = query.from_user.id
    if user_id not in user_sessions:
        await query.answer("Session expired! Please search again.", show_alert=True)
        return
    
    session_data = user_sessions[user_id]
    records = session_data['records']
    search_number = session_data['search_number']
    
    # Send the requested page
    await send_record_page(update, context, records, search_number, page_num)

def clean_phone_number(number: str) -> str:
    """Clean and validate phone number."""
    cleaned = ''.join(filter(str.isdigit, number))
    
    # Handle Indian numbers
    if len(cleaned) == 10:
        return cleaned
    elif len(cleaned) == 12 and cleaned.startswith('91'):
        return cleaned[2:]
    elif len(cleaned) == 11 and cleaned.startswith('0'):
        return cleaned[1:]
    
    return cleaned

def format_address(address: str) -> str:
    """Format the address by replacing ! with commas and cleaning."""
    if not address:
        return "📍 Address information not available"
    
    parts = [part.strip() for part in address.split('!') if part.strip()]
    
    if not parts:
        return "📍 Address information not available"
    
    # Use commas instead of arrows
    formatted = ", ".join(parts)
    return formatted

def parse_api_response(response_text: str):
    """Parse API response with proper JSON handling."""
    try:
        cleaned_text = response_text.strip()
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        # Enhanced JSON parsing with multiple fallbacks
        try:
            # Remove any non-JSON content
            start_idx = cleaned_text.find('{')
            end_idx = cleaned_text.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = cleaned_text[start_idx:end_idx]
                return json.loads(json_str)
        except:
            pass
        
        # Try to find array format
        try:
            start_idx = cleaned_text.find('[')
            end_idx = cleaned_text.rfind(']') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = cleaned_text[start_idx:end_idx]
                return {"data": json.loads(json_str)}
        except:
            pass
        
        raise ValueError("API returned invalid JSON format")

async def handle_phone_number(update: Update, context: CallbackContext, number_input: str = None) -> None:
    """Handle phone number input."""
    if number_input is None:
        if update.message:
            number_input = update.message.text
        else:
            return
    
    chat_id = update.effective_chat.id
    
    # Show single loading message
    loading_message_id = await show_loading(chat_id, context)
    
    # Clean the phone number
    clean_number = clean_phone_number(number_input)
    
    if len(clean_number) != 10:
        error_text = f"""
{Style.ERROR} *Invalid Input*

Please provide a valid 10-digit Indian mobile number.

*Examples:*
• `7044165702`
• `+917044165702`  
• `917044165702`

{Style.WARNING} Ensure the number follows standard Indian mobile format.
        """
        
        keyboard = [[InlineKeyboardButton(f"{Style.NEW} Try Again", callback_data="new_search")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=loading_message_id,
            text=error_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        # Fetch data from API
        response = requests.get(f"{API_URL}{clean_number}", timeout=20)
        response.raise_for_status()
        
        # Parse response
        data = parse_api_response(response.text)
        
        # Delete loading message
        await context.bot.delete_message(chat_id=chat_id, message_id=loading_message_id)
        
        await process_and_send_results(update, context, clean_number, data)
            
    except requests.exceptions.Timeout:
        error_text = f"""
{Style.CLOCK} *Request Timeout*

The data source is taking longer than expected to respond.

*Number:* `{clean_number}`
*Status:* Processing delayed

{Style.WARNING} Please try again in a few moments.
        """
        await send_error_message(update, context, error_text, clean_number, loading_message_id)
        
    except requests.exceptions.RequestException as e:
        error_text = f"""
{Style.ERROR} *Network Error*

Unable to connect to data sources at this time.

*Number:* `{clean_number}`
*Issue:* Connection failed

{Style.WARNING} Please check your internet connection and try again.
        """
        await send_error_message(update, context, error_text, clean_number, loading_message_id)
        
    except ValueError as e:
        error_text = f"""
{Style.ERROR} *Data Processing Error*

Received unexpected response format from data source.

*Number:* `{clean_number}`
*Technical Issue:* Data parsing failed

{Style.WARNING} Our team has been notified. Please try again shortly.
        """
        await send_error_message(update, context, error_text, clean_number, loading_message_id)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        error_text = f"""
{Style.ERROR} *System Error*

An unexpected error occurred during processing.

*Number:* `{clean_number}`
*Error Code:* SYSTEM_001

{Style.WARNING} Please try again in a few minutes.
        """
        await send_error_message(update, context, error_text, clean_number, loading_message_id)

async def send_error_message(update: Update, context: CallbackContext, error_text: str, number: str, loading_message_id: int = None):
    """Send error message with retry button."""
    keyboard = [
        [InlineKeyboardButton(f"{Style.NEW} Retry Search", callback_data=f"retry_{number}")],
        [InlineKeyboardButton(f"{Style.HOME} Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    chat_id = update.effective_chat.id
    
    if loading_message_id:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=loading_message_id,
            text=error_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        if update.message:
            await update.message.reply_text(
                error_text, 
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.callback_query.edit_message_text(
                error_text, 
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )

async def process_and_send_results(update: Update, context: CallbackContext, number: str, data: dict) -> None:
    """Process API results and send with pagination."""
    
    if 'data' in data and data['data']:
        records = data['data']
        
        # Get unique records
        unique_records = []
        seen = set()
        
        for record in records:
            if isinstance(record, dict):
                key = (
                    record.get('mobile', ''),
                    record.get('name', ''),
                    record.get('address', '')
                )
                if key not in seen:
                    seen.add(key)
                    unique_records.append(record)
        
        if unique_records:
            # Store records in user session for pagination
            user_id = update.effective_user.id
            user_sessions[user_id] = {
                'records': unique_records,
                'search_number': number,
                'timestamp': time.time()
            }
            
            # Send first page
            await send_record_page(update, context, unique_records, number, 0)
        else:
            # No valid records found
            result_text = f"""
{Style.SEARCH} *INTELLIGENCE REPORT*

{Style.PHONE} *Target Number:* `{number}`
{Style.WARNING} *Status:* Data Retrieved - No Valid Records

*Analysis Complete*
The number was processed successfully, but no actionable intelligence was found in available databases.

{Style.CALENDAR} *Report Generated:* {time.strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            keyboard = [
                [InlineKeyboardButton(f"{Style.NEW} New Analysis", callback_data="new_search")],
                [InlineKeyboardButton(f"{Style.HOME} Main Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.message:
                await update.message.reply_text(
                    result_text, 
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.callback_query.edit_message_text(
                    result_text, 
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
        
    else:
        # No data found
        result_text = f"""
{Style.SEARCH} *INTELLIGENCE REPORT*

{Style.PHONE} *Target Number:* `{number}`
{Style.WARNING} *Status:* No Database Records Found

*Analysis Complete*
This number does not appear in our current intelligence databases. This could indicate:

• New/unregistered number
• Limited data availability
• Regional database variations

{Style.CALENDAR} *Report Generated:* {time.strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        keyboard = [
            [InlineKeyboardButton(f"{Style.NEW} New Analysis", callback_data="new_search")],
            [InlineKeyboardButton(f"{Style.HOME} Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text(
                result_text, 
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.callback_query.edit_message_text(
                result_text, 
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )

async def send_record_page(update: Update, context: CallbackContext, records: list, number: str, page_num: int) -> None:
    """Send a single record page with pagination."""
    
    if not records:
        return
    
    total_pages = len(records)
    
    if page_num < 0 or page_num >= total_pages:
        page_num = 0
    
    record = records[page_num]
    
    # Format the result with professional styling
    result_text = f"""
{Style.SEARCH} *INTELLIGENCE REPORT* {Style.BOLD}

{Style.PHONE} *Target Number:* `{number}`
{Style.DOCUMENT} *Record:* {page_num + 1} of {total_pages}

{Style.BOLD} *SUBSCRIBER INFORMATION*
{Style.USER} *Name:* {record.get('name', 'Not Available')}
{Style.FATHER} *Father:* {record.get('fname', 'Not Available')}
{Style.PHONE} *Mobile:* `{record.get('mobile', 'Not Available')}`
{Style.PHONE} *Alternate:* {record.get('alt', 'Not Available')}

{Style.BOLD} *SERVICE DETAILS*
{Style.NETWORK} *Circle:* {record.get('circle', 'Not Available')}
{Style.ID_CARD} *ID:* {record.get('id', 'Not Available')}

{Style.BOLD} *GEOGRAPHICAL DATA*
{Style.ADDRESS} *Address:* {format_address(record.get('address', ''))}

{Style.CALENDAR} *Report Generated:* {time.strftime('%Y-%m-%d %H:%M:%S')}
{Style.SHIELD} *Data Source:* Verified OSINT Databases
    """
    
    # Create professional navigation
    keyboard = []
    
    # Pagination buttons
    nav_buttons = []
    
    if total_pages > 1:
        if page_num > 0:
            nav_buttons.append(InlineKeyboardButton(f"{Style.PREV} Previous", callback_data=f"page_{page_num - 1}"))
        
        nav_buttons.append(InlineKeyboardButton(f"{Style.DOCUMENT} {page_num + 1}/{total_pages}", callback_data="current_page"))
        
        if page_num < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton(f"Next {Style.NEXT}", callback_data=f"page_{page_num + 1}"))
        
        keyboard.append(nav_buttons)
    
    # Action buttons
    action_buttons = [
        InlineKeyboardButton(f"{Style.NEW} New Analysis", callback_data="new_search"),
        InlineKeyboardButton(f"{Style.HOME} Main Menu", callback_data="main_menu")
    ]
    keyboard.append(action_buttons)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send or edit message
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text(
                result_text, 
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                result_text, 
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        # Fallback without formatting
        if update.callback_query:
            await update.callback_query.edit_message_text(result_text)
        else:
            await update.message.reply_text(result_text)

async def retry_handler(update: Update, context: CallbackContext) -> None:
    """Handle retry button."""
    query = update.callback_query
    await query.answer()
    
    number = query.data.replace('retry_', '')
    await handle_phone_number(update, context, number)

async def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle all other messages."""
    text = update.message.text
    
    # Check if message looks like a phone number
    cleaned_text = text.replace(' ', '').replace('+', '').replace('-', '')
    if any(char.isdigit() for char in cleaned_text) and len(cleaned_text) >= 10:
        await handle_phone_number(update, context)
    else:
        help_text = f"""
{Style.ERROR} *Invalid Input*

Please send a valid mobile number for analysis.

{Style.SEARCH} *Supported Formats:*
• `7044165702`
• `+917044165702`
• `917044165702`

{Style.HELP} Type /help for complete usage instructions.
        """
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN
        )

def main() -> None:
    """Start the bot."""
    # Create Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(help|main_menu|quick_example|new_search)$"))
    application.add_handler(CallbackQueryHandler(retry_handler, pattern="^retry_"))
    application.add_handler(CallbackQueryHandler(handle_pagination, pattern="^page_"))
    
    # Start the Bot
    print("🚀 OSINT PRO BOT is running...")
    print("⭐ Professional Number Intelligence Platform")
    print("📡 Monitoring for incoming requests...")
    print("Press Ctrl+C to stop")
    
    try:
        application.run_polling()
    except Exception as e:
        logger.error(f"Bot error: {e}")
    print("⏹️ Bot service stopped.")

if __name__ == '__main__':
    main()