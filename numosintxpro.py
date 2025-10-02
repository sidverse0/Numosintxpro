import logging
import requests
import json
import time
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from telegram.constants import ParseMode

# Bot Configuration
BOT_TOKEN = "8116705267:AAFYOj0Rv-dCTCS-vnFsBq5PoKSfNg2X-_8"
PHONE_API_URL = "https://decryptkarnrwalebkl.wasmer.app/?key=lodalelobaby&term="
VEHICLE_API1_URL = "https://revangevichelinfo.vercel.app/api/rc?number="
VEHICLE_API2_URL = "https://caller.hackershub.shop/info.php?type=address&registration="
IFSC_API_URL = "https://ifsc.razorpay.com/"

# Keep Alive Server Configuration
KEEP_ALIVE_PORT = 8080

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store user data for pagination
user_sessions = {}

# Comprehensive stylish fonts and symbols
class Style:
    # Common symbols
    BOLD = "✦"
    SEARCH = "🔍"
    HELP = "❓"
    HOME = "🏠"
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    LOADING = "⏳"
    DOCUMENT = "📄"
    LOCATION = "📍"
    CALENDAR = "📅"
    USER = "👤"
    FATHER = "👨‍👦"
    SHIELD = "🛡️"
    ROCKET = "🚀"
    DATABASE = "💾"
    NETWORK = "📡"
    CLOCK = "⏰"
    SERVER = "🌐"
    INFO = "ℹ️"
    RELOAD = "🔄"
    ID_CARD = "🆔"
    CITY = "🏙️"
    STATE = "🗺️"
    
    # Phone specific
    PHONE = "📱"
    ADDRESS = "🏠"
    
    # Vehicle specific
    CAR = "🚗"
    ENGINE = "🔧"
    FUEL = "⛽"
    FACTORY = "🏭"
    MONEY = "💰"
    PHONE_V = "📞"
    CERTIFICATE = "📜"
    BUILDING = "🏢"
    GEAR = "⚙️"
    CAR_DETAIL = "🚙"
    GAS = "💨"
    COMMERCIAL = "💼"
    INSURANCE = "🏥"
    
    # Bank/IFSC specific
    BANK = "🏦"
    IFSC = "💳"
    BRANCH = "🏢"
    MICR = "🖨️"
    SWIFT = "🌐"
    UPI = "📱"
    RTGS = "💸"
    NEFT = "💰"
    IMPS = "⚡"
    CONTACT = "📞"
    DISTRICT = "🗺️"
    CENTRE = "🏛️"
    
    # Navigation
    BACK = "↩️"
    NEXT = "➡️"
    PREV = "⬅️"
    NEW = "🔄"

# Create Flask app for keep-alive
app = Flask(__name__)

@app.route('/')
def home():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OSINT Pro Bot - Status</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}
            .container {{
                background: rgba(255, 255, 255, 0.1);
                padding: 30px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
            }}
            .status {{
                background: green;
                color: white;
                padding: 10px 20px;
                border-radius: 20px;
                display: inline-block;
                font-weight: bold;
            }}
            .info-box {{
                background: rgba(255, 255, 255, 0.2);
                padding: 15px;
                border-radius: 10px;
                margin: 10px 0;
            }}
            .feature-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 15px;
                margin: 20px 0;
            }}
            .feature-item {{
                background: rgba(255, 255, 255, 0.15);
                padding: 15px;
                border-radius: 8px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 OSINT Pro Master Bot</h1>
            <div class="status">🟢 ONLINE & RUNNING</div>
            
            <div class="info-box">
                <h3>📊 Bot Information</h3>
                <p><strong>Status:</strong> Active</p>
                <p><strong>Uptime:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Service:</strong> Advanced OSINT Intelligence Platform</p>
            </div>
            
            <div class="info-box">
                <h3>🌟 Available Features</h3>
                <div class="feature-grid">
                    <div class="feature-item">
                        <h4>📱 Phone Intelligence</h4>
                        <p>Complete mobile number analysis</p>
                    </div>
                    <div class="feature-item">
                        <h4>🚗 Vehicle Intelligence</h4>
                        <p>Detailed vehicle information</p>
                    </div>
                    <div class="feature-item">
                        <h4>🏦 Bank IFSC Lookup</h4>
                        <p>Bank branch details by IFSC</p>
                    </div>
                </div>
            </div>
            
            <div class="info-box">
                <h3>🌐 Keep Alive Server</h3>
                <p>This server keeps the bot running 24/7</p>
                <p><strong>Port:</strong> {KEEP_ALIVE_PORT}</p>
                <p><strong>Endpoint:</strong> / (this page)</p>
            </div>
            
            <div class="info-box">
                <h3>📞 Contact Bot</h3>
                <p>Search for <strong>@osint_pro_number_bot</strong> on Telegram</p>
                <p>Or click: <a href="https://t.me/osint_pro_number_bot" style="color: #4FC3F7;">Start Chat</a></p>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return {"status": "healthy", "timestamp": time.time(), "service": "osint_pro_master_bot"}

def run_keep_alive():
    """Run the keep-alive server in a separate thread"""
    print(f"{Style.SERVER} Starting keep-alive server on port {KEEP_ALIVE_PORT}...")
    app.run(host='0.0.0.0', port=KEEP_ALIVE_PORT, debug=False, use_reloader=False)

async def start(update: Update, context: CallbackContext) -> None:
    """Send welcome message when the command /start is issued."""
    user = update.effective_user
    
    welcome_text = f"""
{Style.ROCKET} *WELCOME TO OSINT PRO MASTER BOT* {Style.ROCKET}

👋 Hello *{user.first_name}*!

{Style.SEARCH} *Advanced Intelligence Platform*
{Style.SHIELD} *Secure • Fast • Professional*

✨ *Triple Intelligence Features:*

{Style.PHONE} *Phone Intelligence:*
• Complete number analysis
• Detailed subscriber information  
• Geographic mapping
• Multi-source data verification

{Style.CAR} *Vehicle Intelligence:*
• Complete RC Information
• Address Verification  
• Technical Specifications
• Insurance & Tax Details

{Style.BANK} *Bank IFSC Lookup:*
• Bank branch details
• Service availability
• Contact information
• Location mapping

📋 *Quick Start:*
Choose your search type below or simply send:
• *10-digit mobile number* for phone analysis
• *Vehicle registration* for vehicle info
• *IFSC code* for bank details

*Examples:*
Phone: `7044165702`, `+917044165702`
Vehicle: `UP32AB1234`, `DL1CAB1234`
IFSC: `SBIN0003010`, `HDFC0000001`

{Style.WARNING} *Legal Notice:* Use responsibly in compliance with applicable laws.
    """
    
    keyboard = [
        [InlineKeyboardButton(f"{Style.PHONE} Phone Search", callback_data="phone_search"),
         InlineKeyboardButton(f"{Style.CAR} Vehicle Search", callback_data="vehicle_search")],
        [InlineKeyboardButton(f"{Style.BANK} IFSC Search", callback_data="ifsc_search")],
        [InlineKeyboardButton(f"{Style.HELP} Get Help", callback_data="help")],
        [InlineKeyboardButton(f"{Style.SEARCH} Quick Examples", callback_data="quick_examples")]
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
{Style.HELP} *OSINT PRO MASTER BOT - HELP GUIDE* {Style.HELP}

{Style.SEARCH} *How to Use:*

{Style.PHONE} *Phone Intelligence:*
1. Send any mobile number
2. Wait for processing
3. Receive detailed report

{Style.CAR} *Vehicle Intelligence:*
1. Click Vehicle Search button
2. Enter registration number
3. Get instant results

{Style.BANK} *IFSC Lookup:*
1. Click IFSC Search button
2. Enter IFSC code
3. Get bank branch details

{Style.NETWORK} *Supported Formats:*
• *Phone:* 10-digit numbers, International format, With country code
• *Vehicle:* UP32AB1234, DL1CAB1234, HR26DK7890
• *IFSC:* SBIN0003010, HDFC0000001, ICIC0000001

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
Use the buttons below to start a search!
    """
    
    keyboard = [
        [InlineKeyboardButton(f"{Style.PHONE} Phone Search", callback_data="phone_search"),
         InlineKeyboardButton(f"{Style.CAR} Vehicle Search", callback_data="vehicle_search")],
        [InlineKeyboardButton(f"{Style.BANK} IFSC Search", callback_data="ifsc_search")],
        [InlineKeyboardButton(f"{Style.HOME} Main Menu", callback_data="main_menu")]
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

async def show_loading(chat_id, context: CallbackContext, search_type="request"):
    """Show single loading message."""
    if search_type == "phone":
        loading_text = f"{Style.LOADING} *Processing phone number...*"
    elif search_type == "vehicle":
        loading_text = f"{Style.LOADING} *Searching vehicle database...*"
    elif search_type == "ifsc":
        loading_text = f"{Style.LOADING} *Fetching bank details...*"
    else:
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
    elif query.data == "quick_examples":
        await show_quick_examples(update, context)
    elif query.data == "phone_search":
        await phone_search_handler(update, context)
    elif query.data == "vehicle_search":
        await vehicle_search_handler(update, context)
    elif query.data == "ifsc_search":
        await ifsc_search_handler(update, context)
    elif query.data == "new_search":
        await query.edit_message_text(f"{Style.SEARCH} *Choose search type or send input directly...*", parse_mode=ParseMode.MARKDOWN)
    elif query.data.startswith("page_"):
        await handle_pagination(update, context)
    elif query.data.startswith("retry_"):
        await retry_handler(update, context)

async def show_quick_examples(update: Update, context: CallbackContext) -> None:
    """Show quick examples for all services."""
    examples_text = f"""
{Style.SEARCH} *QUICK EXAMPLES*

{Style.PHONE} *Phone Number Examples:*
• `7044165702` - Standard 10-digit
• `+917044165702` - International format
• `917044165702` - With country code

{Style.CAR} *Vehicle Number Examples:*
• `UP32AB1234` - Uttar Pradesh
• `DL1CAB1234` - Delhi
• `HR26DK7890` - Haryana
• `KA01AB1234` - Karnataka

{Style.BANK} *IFSC Code Examples:*
• `SBIN0003010` - State Bank of India
• `HDFC0000001` - HDFC Bank
• `ICIC0000001` - ICICI Bank
• `PNB0012000` - Punjab National Bank

{Style.INFO} Simply send any of these formats to get started, or use the search buttons below.
    """
    
    keyboard = [
        [InlineKeyboardButton(f"{Style.PHONE} Try Phone Example", callback_data="try_phone_example"),
         InlineKeyboardButton(f"{Style.CAR} Try Vehicle Example", callback_data="try_vehicle_example")],
        [InlineKeyboardButton(f"{Style.BANK} Try IFSC Example", callback_data="try_ifsc_example")],
        [InlineKeyboardButton(f"{Style.HOME} Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        examples_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def phone_search_handler(update: Update, context: CallbackContext) -> None:
    """Handle phone search button."""
    search_text = f"""
{Style.PHONE} *PHONE NUMBER SEARCH*

Please enter the mobile number:

*Supported Formats:*
• `7044165702`
• `+917044165702`  
• `917044165702`

ℹ️ Enter the number with or without country code.
    """
    
    await update.callback_query.edit_message_text(
        search_text,
        parse_mode=ParseMode.MARKDOWN
    )
    context.user_data['expecting_phone'] = True
    context.user_data['expecting_vehicle'] = False
    context.user_data['expecting_ifsc'] = False

async def vehicle_search_handler(update: Update, context: CallbackContext) -> None:
    """Handle vehicle search button."""
    search_text = f"""
{Style.CAR} *VEHICLE SEARCH*

Please enter the vehicle registration number:

*Examples:*
• `UP32AB1234`
• `DL1CAB1234`
• `HR26DK7890`

ℹ️ Enter the number without spaces.
    """
    
    await update.callback_query.edit_message_text(
        search_text,
        parse_mode=ParseMode.MARKDOWN
    )
    context.user_data['expecting_vehicle'] = True
    context.user_data['expecting_phone'] = False
    context.user_data['expecting_ifsc'] = False

async def ifsc_search_handler(update: Update, context: CallbackContext) -> None:
    """Handle IFSC search button."""
    search_text = f"""
{Style.BANK} *IFSC CODE SEARCH*

Please enter the IFSC code:

*Examples:*
• `SBIN0003010` - State Bank of India
• `HDFC0000001` - HDFC Bank
• `ICIC0000001` - ICICI Bank

ℹ️ IFSC code is 11 characters (4 letters + 7 digits/letters)
    """
    
    await update.callback_query.edit_message_text(
        search_text,
        parse_mode=ParseMode.MARKDOWN
    )
    context.user_data['expecting_ifsc'] = True
    context.user_data['expecting_phone'] = False
    context.user_data['expecting_vehicle'] = False

async def try_phone_example(update: Update, context: CallbackContext) -> None:
    """Try phone number example."""
    await handle_phone_number(update, context, "7044165702")

async def try_vehicle_example(update: Update, context: CallbackContext) -> None:
    """Try vehicle number example."""
    await handle_vehicle_search(update, context, "UP32AB1234")

async def try_ifsc_example(update: Update, context: CallbackContext) -> None:
    """Try IFSC code example."""
    await handle_ifsc_search(update, context, "SBIN0003010")

# ============================
# PHONE NUMBER FUNCTIONALITY
# ============================

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
    loading_message_id = await show_loading(chat_id, context, "phone")
    
    # Clean the phone number
    clean_number = clean_phone_number(number_input)
    
    if len(clean_number) != 10:
        error_text = f"""
{Style.ERROR} *Invalid Phone Input*

Please provide a valid 10-digit Indian mobile number.

*Examples:*
• `7044165702`
• `+917044165702`  
• `917044165702`

{Style.WARNING} Ensure the number follows standard Indian mobile format.
        """
        
        keyboard = [
            [InlineKeyboardButton(f"{Style.PHONE} Try Again", callback_data="phone_search")],
            [InlineKeyboardButton(f"{Style.HOME} Main Menu", callback_data="main_menu")]
        ]
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
        response = requests.get(f"{PHONE_API_URL}{clean_number}", timeout=20)
        response.raise_for_status()
        
        # Parse response
        data = parse_api_response(response.text)
        
        # Delete loading message
        await context.bot.delete_message(chat_id=chat_id, message_id=loading_message_id)
        
        await process_and_send_phone_results(update, context, clean_number, data)
            
    except requests.exceptions.Timeout:
        error_text = f"""
{Style.CLOCK} *Request Timeout*

The data source is taking longer than expected to respond.

*Number:* `{clean_number}`
*Status:* Processing delayed

{Style.WARNING} Please try again in a few moments.
        """
        await send_error_message(update, context, error_text, clean_number, loading_message_id, "phone")
        
    except requests.exceptions.RequestException as e:
        error_text = f"""
{Style.ERROR} *Network Error*

Unable to connect to data sources at this time.

*Number:* `{clean_number}`
*Issue:* Connection failed

{Style.WARNING} Please check your internet connection and try again.
        """
        await send_error_message(update, context, error_text, clean_number, loading_message_id, "phone")
        
    except ValueError as e:
        error_text = f"""
{Style.ERROR} *Data Processing Error*

Received unexpected response format from data source.

*Number:* `{clean_number}`
*Technical Issue:* Data parsing failed

{Style.WARNING} Our team has been notified. Please try again shortly.
        """
        await send_error_message(update, context, error_text, clean_number, loading_message_id, "phone")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        error_text = f"""
{Style.ERROR} *System Error*

An unexpected error occurred during processing.

*Number:* `{clean_number}`
*Error Code:* SYSTEM_001

{Style.WARNING} Please try again in a few minutes.
        """
        await send_error_message(update, context, error_text, clean_number, loading_message_id, "phone")

async def send_error_message(update: Update, context: CallbackContext, error_text: str, number: str, loading_message_id: int = None, search_type="phone"):
    """Send error message with retry button."""
    if search_type == "phone":
        retry_button = InlineKeyboardButton(f"{Style.PHONE} Retry Search", callback_data=f"retry_phone_{number}")
        search_button = InlineKeyboardButton(f"{Style.PHONE} New Phone Search", callback_data="phone_search")
    elif search_type == "vehicle":
        retry_button = InlineKeyboardButton(f"{Style.CAR} Retry Search", callback_data=f"retry_vehicle_{number}")
        search_button = InlineKeyboardButton(f"{Style.CAR} New Vehicle Search", callback_data="vehicle_search")
    else:  # ifsc
        retry_button = InlineKeyboardButton(f"{Style.BANK} Retry Search", callback_data=f"retry_ifsc_{number}")
        search_button = InlineKeyboardButton(f"{Style.BANK} New IFSC Search", callback_data="ifsc_search")
    
    keyboard = [
        [retry_button],
        [search_button],
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

async def process_and_send_phone_results(update: Update, context: CallbackContext, number: str, data: dict) -> None:
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
{Style.SEARCH} *PHONE INTELLIGENCE REPORT*

{Style.PHONE} *Target Number:* `{number}`
{Style.WARNING} *Status:* Data Retrieved - No Valid Records

*Analysis Complete*
The number was processed successfully, but no actionable intelligence was found in available databases.

{Style.CALENDAR} *Report Generated:* {time.strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            keyboard = [
                [InlineKeyboardButton(f"{Style.PHONE} New Phone Search", callback_data="phone_search")],
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
{Style.SEARCH} *PHONE INTELLIGENCE REPORT*

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
            [InlineKeyboardButton(f"{Style.PHONE} New Phone Search", callback_data="phone_search")],
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
{Style.SEARCH} *PHONE INTELLIGENCE REPORT* {Style.BOLD}

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
        InlineKeyboardButton(f"{Style.PHONE} New Phone Search", callback_data="phone_search"),
        InlineKeyboardButton(f"{Style.CAR} Vehicle Search", callback_data="vehicle_search"),
        InlineKeyboardButton(f"{Style.BANK} IFSC Search", callback_data="ifsc_search"),
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
    
    data = query.data
    if data.startswith('retry_phone_'):
        number = data.replace('retry_phone_', '')
        await handle_phone_number(update, context, number)
    elif data.startswith('retry_vehicle_'):
        number = data.replace('retry_vehicle_', '')
        await handle_vehicle_search(update, context, number)
    elif data.startswith('retry_ifsc_'):
        number = data.replace('retry_ifsc_', '')
        await handle_ifsc_search(update, context, number)

# ============================
# VEHICLE FUNCTIONALITY
# ============================

def clean_vehicle_number(number: str) -> str:
    """Clean and validate vehicle number."""
    cleaned = number.upper().strip()
    # Remove spaces and special characters, keep alphanumeric
    cleaned = ''.join(c for c in cleaned if c.isalnum())
    return cleaned

def get_vehicle_info(vehicle_number):
    """Fetch vehicle information from both APIs"""
    results = {}
    
    # API 1 - RC Information
    try:
        logger.info(f"Calling Vehicle API1: {VEHICLE_API1_URL}{vehicle_number}")
        api1_response = requests.get(f"{VEHICLE_API1_URL}{vehicle_number}", timeout=15)
        if api1_response.status_code == 200:
            results['api1'] = api1_response.json()
        else:
            results['api1'] = {"error": f"API1 HTTP {api1_response.status_code}"}
    except Exception as e:
        results['api1'] = {"error": f"API1 Error: {str(e)}"}
    
    # API 2 - Detailed Information  
    try:
        logger.info(f"Calling Vehicle API2: {VEHICLE_API2_URL}{vehicle_number}")
        api2_response = requests.get(f"{VEHICLE_API2_URL}{vehicle_number}", timeout=15)
        if api2_response.status_code == 200:
            results['api2'] = api2_response.json()
        else:
            results['api2'] = {"error": f"API2 HTTP {api2_response.status_code}"}
    except Exception as e:
        results['api2'] = {"error": f"API2 Error: {str(e)}"}
    
    return results

def format_vehicle_results(vehicle_number, results):
    """Format the vehicle information results with ALL fields"""
    
    result_text = f"""
{Style.CAR} *VEHICLE INTELLIGENCE REPORT*

*Registration Number:* `{vehicle_number}`
*Report Time:* {time.strftime('%Y-%m-%d %H:%M:%S')}

────────────────────
    """
    
    # API 1 Results - Complete Fields
    api1_data = results.get('api1', {})
    if 'error' in api1_data:
        result_text += f"\n{Style.ERROR} *RC Information:* {api1_data['error']}\n"
    else:
        result_text += f"\n{Style.DOCUMENT} *RC INFORMATION*\n\n"
        data = api1_data
        
        # All API1 fields with proper formatting
        api1_fields = [
            (f"{Style.ID_CARD} RC Number", data.get('rc_number')),
            (f"{Style.USER} Owner Name", data.get('owner_name')),
            (f"{Style.FATHER} Father Name", data.get('father_name')),
            (f"🔢 Owner Serial No", data.get('owner_serial_no')),
            (f"{Style.FACTORY} Model Name", data.get('model_name')),
            (f"{Style.CAR} Maker Model", data.get('maker_model')),
            (f"📋 Vehicle Class", data.get('vehicle_class')),
            (f"{Style.FUEL} Fuel Type", data.get('fuel_type')),
            (f"{Style.GAS} Fuel Norms", data.get('fuel_norms')),
            (f"{Style.CALENDAR} Registration Date", data.get('registration_date')),
            (f"{Style.INSURANCE} Insurance Company", data.get('insurance_company')),
            (f"📄 Insurance No", data.get('insurance_no')),
            (f"{Style.SHIELD} Insurance Expiry", data.get('insurance_expiry')),
            (f"{Style.SHIELD} Insurance Upto", data.get('insurance_upto')),
            (f"{Style.CERTIFICATE} Fitness Upto", data.get('fitness_upto')),
            (f"{Style.MONEY} Tax Upto", data.get('tax_upto')),
            (f"🛂 PUC No", data.get('puc_no')),
            (f"🛂 PUC Upto", data.get('puc_upto')),
            (f"💰 Financier Name", data.get('financier_name')),
            (f"{Style.BUILDING} RTO", data.get('rto')),
            (f"{Style.LOCATION} Address", data.get('address')),
            (f"{Style.CITY} City", data.get('city')),
            (f"{Style.PHONE_V} Phone", data.get('phone'))
        ]
        
        for label, value in api1_fields:
            if value and str(value).strip() and str(value).lower() not in ['n/a', 'null', 'none', '']:
                result_text += f"• {label}: `{value}`\n"
    
    result_text += "\n────────────────────\n"
    
    # API 2 Results - Complete Fields
    api2_data = results.get('api2', {})
    if 'error' in api2_data:
        result_text += f"\n{Style.ERROR} *Detailed Info:* {api2_data['error']}\n"
    else:
        result_text += f"\n{Style.INFO} *DETAILED INFORMATION*\n\n"
        data = api2_data
        
        # All API2 fields with proper formatting
        api2_fields = [
            (f"🔢 Asset Number", data.get('asset_number')),
            (f"{Style.CAR} Asset Type", data.get('asset_type')),
            (f"{Style.CALENDAR} Registration Year", data.get('registration_year')),
            (f"{Style.CALENDAR} Registration Month", data.get('registration_month')),
            (f"{Style.CAR_DETAIL} Make Model", data.get('make_model')),
            (f"📋 Vehicle Type", data.get('vehicle_type')),
            (f"{Style.FACTORY} Make Name", data.get('make_name')),
            (f"{Style.FUEL} Fuel Type", data.get('fuel_type')),
            (f"{Style.ENGINE} Engine Number", data.get('engine_number')),
            (f"{Style.USER} Owner Name", data.get('owner_name')),
            (f"🆔 Chassis Number", data.get('chassis_number')),
            (f"🏢 Previous Insurer", data.get('previous_insurer')),
            (f"{Style.SHIELD} Previous Policy Expiry", data.get('previous_policy_expiry_date')),
            (f"{Style.COMMERCIAL} Is Commercial", data.get('is_commercial')),
            (f"📋 Vehicle Type V2", data.get('vehicle_type_v2')),
            (f"{Style.GEAR} Vehicle Type Processed", data.get('vehicle_type_processed')),
            (f"{Style.LOCATION} Permanent Address", data.get('permanent_address')),
            (f"📍 Present Address", data.get('present_address')),
            (f"{Style.CALENDAR} Registration Date", data.get('registration_date')),
            (f"{Style.BUILDING} Registration Address", data.get('registration_address')),
            (f"{Style.CAR} Model Name", data.get('model_name')),
            (f"{Style.FACTORY} Make Name 2", data.get('make_name2')),
            (f"{Style.CAR} Model Name 2", data.get('model_name2')),
            (f"🆔 Variant ID", data.get('variant_id')),
            (f"{Style.SHIELD} Previous Policy Expired", data.get('previous_policy_expired'))
        ]
        
        for label, value in api2_fields:
            if value is not None and str(value).strip() and str(value).lower() not in ['n/a', 'null', 'none', '']:
                # Handle boolean values
                if isinstance(value, bool):
                    value = "Yes" if value else "No"
                # Handle list values
                elif isinstance(value, list):
                    value = ', '.join(str(v) for v in value)
                result_text += f"• {label}: `{value}`\n"
    
    result_text += f"\n{Style.SHIELD} *Data Source:* Verified Vehicle Databases"
    result_text += f"\n{Style.INFO} *Note:* Some fields may be empty if not available in database"
    
    return result_text

async def handle_vehicle_search(update: Update, context: CallbackContext, vehicle_input: str = None) -> None:
    """Handle vehicle number input from user"""
    
    if vehicle_input is None:
        if update.message:
            vehicle_input = update.message.text
        else:
            return
    
    # Clean the vehicle number
    vehicle_number = clean_vehicle_number(vehicle_input)
    
    # Basic validation
    if len(vehicle_number) < 5:
        error_text = f"""
{Style.ERROR} *Invalid Vehicle Number!*

Please enter a valid registration number (minimum 5 characters).

*Examples:*
• `UP32AB1234`
• `DL1CAB1234`
• `HR26DK7890`
        """
        
        keyboard = [
            [InlineKeyboardButton(f"{Style.CAR} Try Again", callback_data="vehicle_search")],
            [InlineKeyboardButton(f"{Style.HOME} Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
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
        return
    
    chat_id = update.effective_chat.id
    
    # Send processing message
    loading_message_id = await show_loading(chat_id, context, "vehicle")
    
    try:
        # Get vehicle information
        logger.info(f"Fetching info for vehicle: {vehicle_number}")
        results = get_vehicle_info(vehicle_number)
        
        # Format and send results
        result_text = format_vehicle_results(vehicle_number, results)
        
        # Delete processing message
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=loading_message_id
        )
        
        # Create keyboard for navigation
        keyboard = [
            [InlineKeyboardButton(f"{Style.CAR} New Vehicle Search", callback_data="vehicle_search")],
            [InlineKeyboardButton(f"{Style.PHONE} Phone Search", callback_data="phone_search")],
            [InlineKeyboardButton(f"{Style.BANK} IFSC Search", callback_data="ifsc_search")],
            [InlineKeyboardButton(f"{Style.HOME} Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send result - Telegram has 4096 character limit, so we need to check
        if len(result_text) > 4096:
            # Split the message if too long
            parts = []
            while result_text:
                if len(result_text) > 4096:
                    part = result_text[:4096]
                    # Find the last newline to avoid cutting in the middle of a line
                    last_newline = part.rfind('\n')
                    if last_newline != -1:
                        part = result_text[:last_newline]
                        result_text = result_text[last_newline+1:]
                    else:
                        result_text = result_text[4096:]
                    parts.append(part)
                else:
                    parts.append(result_text)
                    break
            
            # Send first part with keyboard
            if update.message:
                await update.message.reply_text(
                    parts[0],
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.callback_query.edit_message_text(
                    parts[0],
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
            
            # Send remaining parts without keyboard
            for part in parts[1:]:
                if update.message:
                    await update.message.reply_text(
                        part,
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    # For callback queries, we can only edit the original message once
                    # So we send new messages for additional parts
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=part,
                        parse_mode=ParseMode.MARKDOWN
                    )
        else:
            # Send normally if within limit
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
        
        logger.info(f"Successfully sent results for vehicle: {vehicle_number}")
        
    except Exception as e:
        logger.error(f"Error processing vehicle {vehicle_number}: {str(e)}")
        
        # Update processing message with error
        error_text = f"""
{Style.ERROR} *Vehicle Search Failed*

Unable to retrieve information for `{vehicle_number}`.

*Possible reasons:*
• Vehicle number not found in databases
• Temporary service outage
• Invalid registration number

{Style.WARNING} Please try again with a different number.
        """
        
        keyboard = [
            [InlineKeyboardButton(f"{Style.CAR} Try Again", callback_data="vehicle_search")],
            [InlineKeyboardButton(f"{Style.HOME} Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=loading_message_id,
            text=error_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    # Clear the expecting state
    context.user_data['expecting_vehicle'] = False

# ============================
# IFSC CODE FUNCTIONALITY - COMPLETELY FIXED
# ============================

def clean_ifsc_code(ifsc_code: str) -> str:
    """Clean and validate IFSC code."""
    cleaned = ifsc_code.upper().strip()
    # Remove spaces and special characters, keep alphanumeric
    cleaned = ''.join(c for c in cleaned if c.isalnum())
    return cleaned

def get_ifsc_info(ifsc_code):
    """Fetch IFSC code information from API with COMPLETE error handling"""
    try:
        logger.info(f"🔍 Fetching IFSC info for: {ifsc_code}")
        logger.info(f"🌐 API URL: {IFSC_API_URL}{ifsc_code}")
        
        # Make request with proper headers and timeout
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{IFSC_API_URL}{ifsc_code}", 
            headers=headers,
            timeout=20,
            verify=True  # Enable SSL verification
        )
        
        logger.info(f"📡 Response Status: {response.status_code}")
        
        # Check if response is successful
        if response.status_code == 200:
            logger.info("✅ Got 200 response")
            
            # Try to parse JSON
            try:
                data = response.json()
                logger.info(f"📊 Parsed JSON data successfully")
                
                # Check if we have valid bank data
                if data and isinstance(data, dict):
                    if data.get('BANK') or data.get('BRANCH'):
                        logger.info("✅ Valid bank data found")
                        return {"success": True, "data": data}
                    else:
                        logger.warning("❌ No BANK or BRANCH in response")
                        return {"success": False, "error": "IFSC code exists but contains incomplete data"}
                else:
                    logger.warning("❌ Invalid response format")
                    return {"success": False, "error": "Invalid response format from API"}
                    
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON decode error: {e}")
                logger.error(f"📄 Response text: {response.text[:500]}")
                return {"success": False, "error": f"Invalid JSON response: {str(e)}"}
                
        elif response.status_code == 404:
            logger.warning("❌ IFSC code not found (404)")
            return {"success": False, "error": "IFSC code not found in database"}
            
        else:
            logger.error(f"❌ HTTP Error: {response.status_code}")
            return {"success": False, "error": f"API returned HTTP {response.status_code}"}
            
    except requests.exceptions.Timeout:
        logger.error("⏰ Request timeout")
        return {"success": False, "error": "Request timeout - API took too long to respond"}
        
    except requests.exceptions.ConnectionError:
        logger.error("🔌 Connection error")
        return {"success": False, "error": "Connection error - Unable to reach IFSC API"}
        
    except requests.exceptions.RequestException as e:
        logger.error(f"🌐 Request exception: {e}")
        return {"success": False, "error": f"Network error: {str(e)}"}
        
    except Exception as e:
        logger.error(f"💥 Unexpected error in IFSC lookup: {e}")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

def format_ifsc_results(ifsc_code, data):
    """Format the IFSC information results with enhanced error handling"""
    
    if not data.get('success', False):
        error_msg = data.get('error', 'Unknown error occurred')
        logger.error(f"❌ IFSC lookup failed: {error_msg}")
        
        return f"""
{Style.ERROR} *IFSC LOOKUP FAILED*

{Style.IFSC} *IFSC Code:* `{ifsc_code}`
{Style.ERROR} *Error:* {error_msg}

{Style.WARNING} *Troubleshooting Steps:*
• Verify the IFSC code spelling
• Check your internet connection
• Try again in a few minutes
• Contact support if issue persists

*Working IFSC Examples:*
• `SBIN0003010` - State Bank of India
• `HDFC0000001` - HDFC Bank
• `ICIC0000001` - ICICI Bank
        """
    
    bank_data = data['data']
    logger.info(f"✅ Formatting successful IFSC data for: {ifsc_code}")
    
    # Format boolean values for services
    def format_bool(value):
        return '✅ Yes' if value else '❌ No'
    
    # Format empty values
    def format_value(value):
        if value is None or value == '':
            return 'Not Available'
        return value
    
    result_text = f"""
{Style.BANK} *BANK IFSC DETAILS REPORT* {Style.BANK}

{Style.IFSC} *IFSC Code:* `{ifsc_code}`
{Style.CALENDAR} *Report Time:* {time.strftime('%Y-%m-%d %H:%M:%S')}

────────────────────

{Style.BANK} *BANK INFORMATION*
{Style.BANK} *Bank Name:* `{format_value(bank_data.get('BANK'))}`
{Style.ID_CARD} *Bank Code:* `{format_value(bank_data.get('BANKCODE'))}`

{Style.BRANCH} *BRANCH DETAILS*
{Style.BRANCH} *Branch Name:* `{format_value(bank_data.get('BRANCH'))}`
{Style.MICR} *MICR Code:* `{format_value(bank_data.get('MICR'))}`
{Style.CONTACT} *Contact:* `{format_value(bank_data.get('CONTACT'))}`

{Style.LOCATION} *LOCATION INFORMATION*
{Style.LOCATION} *Address:* `{format_value(bank_data.get('ADDRESS'))}`
{Style.DISTRICT} *District:* `{format_value(bank_data.get('DISTRICT'))}`
{Style.CITY} *City:* `{format_value(bank_data.get('CITY'))}`
{Style.STATE} *State:* `{format_value(bank_data.get('STATE'))}`
{Style.CENTRE} *Centre:* `{format_value(bank_data.get('CENTRE'))}`

{Style.NETWORK} *BANKING SERVICES*
{Style.UPI} *UPI:* {format_bool(bank_data.get('UPI', False))}
{Style.RTGS} *RTGS:* {format_bool(bank_data.get('RTGS', False))}
{Style.NEFT} *NEFT:* {format_bool(bank_data.get('NEFT', False))}
{Style.IMPS} *IMPS:* {format_bool(bank_data.get('IMPS', False))}
{Style.SWIFT} *SWIFT:* `{format_value(bank_data.get('SWIFT'))}`

{Style.SHIELD} *Data Source:* Razorpay IFSC API
{Style.INFO} *Note:* Information provided by official banking sources
    """
    
    logger.info("✅ IFSC result formatted successfully")
    return result_text

async def handle_ifsc_search(update: Update, context: CallbackContext, ifsc_input: str = None) -> None:
    """Handle IFSC code input from user with COMPLETE error handling"""
    
    if ifsc_input is None:
        if update.message:
            ifsc_input = update.message.text
        else:
            return
    
    # Clean the IFSC code
    ifsc_code = clean_ifsc_code(ifsc_input)
    logger.info(f"🔍 Starting IFSC search for: {ifsc_code}")
    
    # Enhanced validation - IFSC should be 11 characters alphanumeric
    if len(ifsc_code) != 11:
        error_text = f"""
{Style.ERROR} *Invalid IFSC Code Length!*

IFSC code must be exactly 11 characters long.

*Your Input:* `{ifsc_code}` ({len(ifsc_code)} characters)
*Required:* 11 characters (4 letters + 7 digits/letters)

*Valid Examples:*
• `SBIN0003010` - State Bank of India
• `HDFC0000001` - HDFC Bank
• `ICIC0000001` - ICICI Bank
        """
        
        keyboard = [
            [InlineKeyboardButton(f"{Style.BANK} Try Again", callback_data="ifsc_search")],
            [InlineKeyboardButton(f"{Style.HOME} Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
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
        return
    
    # Validate format: first 4 characters should be letters
    if not ifsc_code[:4].isalpha():
        error_text = f"""
{Style.ERROR} *Invalid IFSC Code Format!*

First 4 characters must be letters (bank code).

*Your Input:* `{ifsc_code}`
*Problem:* First 4 characters `{ifsc_code[:4]}` are not all letters

*Valid Format:* 4 letters + 7 digits/letters
*Example:* `SBIN0003010` (SBIN = State Bank of India)
        """
        
        keyboard = [
            [InlineKeyboardButton(f"{Style.BANK} Try Again", callback_data="ifsc_search")],
            [InlineKeyboardButton(f"{Style.HOME} Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
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
        return
    
    chat_id = update.effective_chat.id
    
    # Send processing message
    loading_message_id = await show_loading(chat_id, context, "ifsc")
    logger.info(f"⏳ Loading message sent: {loading_message_id}")
    
    try:
        # Get IFSC information with enhanced error handling
        logger.info(f"🌐 Calling IFSC API for: {ifsc_code}")
        result = get_ifsc_info(ifsc_code)
        logger.info(f"📊 API result: {result.get('success', False)}")
        
        # Format and send results
        result_text = format_ifsc_results(ifsc_code, result)
        logger.info("✅ Result formatted successfully")
        
        # Delete processing message
        try:
            await context.bot.delete_message(
                chat_id=chat_id,
                message_id=loading_message_id
            )
            logger.info("🗑️ Loading message deleted")
        except Exception as e:
            logger.warning(f"⚠️ Could not delete loading message: {e}")
        
        # Create keyboard for navigation
        keyboard = [
            [InlineKeyboardButton(f"{Style.BANK} New IFSC Search", callback_data="ifsc_search")],
            [InlineKeyboardButton(f"{Style.PHONE} Phone Search", callback_data="phone_search")],
            [InlineKeyboardButton(f"{Style.CAR} Vehicle Search", callback_data="vehicle_search")],
            [InlineKeyboardButton(f"{Style.HOME} Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send result
        logger.info("📤 Sending IFSC result to user")
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
        
        logger.info(f"✅ Successfully completed IFSC request for: {ifsc_code}")
        
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR in handle_ifsc_search: {e}")
        logger.exception("Full traceback:")
        
        # Update processing message with comprehensive error
        error_text = f"""
{Style.ERROR} *Critical System Error*

A critical error occurred while processing your IFSC code.

*IFSC Code:* `{ifsc_code}`
*Error Type:* {type(e).__name__}

{Style.WARNING} *Technical Details:*
• Error: {str(e)}
• Time: {time.strftime('%Y-%m-%d %H:%M:%S')}

*Please try:*
1. Checking the IFSC code format
2. Using a different IFSC code  
3. Trying again in a few minutes
4. Contacting support if issue persists

*Working IFSC Examples:*
• `SBIN0003010` - State Bank of India
• `HDFC0000001` - HDFC Bank
• `ICIC0000001` - ICICI Bank
        """
        
        keyboard = [
            [InlineKeyboardButton(f"{Style.BANK} Try Again", callback_data="ifsc_search")],
            [InlineKeyboardButton(f"{Style.HOME} Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=loading_message_id,
                text=error_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            logger.info("✅ Error message sent to user")
        except Exception as edit_error:
            logger.error(f"❌ Failed to edit error message: {edit_error}")
            # Try to send as new message
            try:
                if update.message:
                    await update.message.reply_text(
                        error_text,
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=error_text,
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.MARKDOWN
                    )
                logger.info("✅ Error message sent as new message")
            except Exception as send_error:
                logger.error(f"💥 COMPLETE FAILURE: {send_error}")
    
    # Clear the expecting state
    context.user_data['expecting_ifsc'] = False
    logger.info("🧹 IFSC search session cleared")

# ============================
# MAIN MESSAGE HANDLER
# ============================

async def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle all other messages."""
    text = update.message.text
    
    # Check if user is expecting specific input
    if context.user_data.get('expecting_phone', False):
        await handle_phone_number(update, context)
        return
    elif context.user_data.get('expecting_vehicle', False):
        await handle_vehicle_search(update, context)
        return
    elif context.user_data.get('expecting_ifsc', False):
        await handle_ifsc_search(update, context)
        return
    
    # Auto-detect input type
    cleaned_phone = clean_phone_number(text)
    cleaned_vehicle = clean_vehicle_number(text)
    cleaned_ifsc = clean_ifsc_code(text)
    
    # Check if it's a phone number (10 digits after cleaning)
    if len(cleaned_phone) == 10:
        await handle_phone_number(update, context)
        return
    
    # Check if it's a vehicle number (alphanumeric, 5-15 chars, contains letters)
    if 5 <= len(cleaned_vehicle) <= 15 and any(c.isalpha() for c in cleaned_vehicle):
        await handle_vehicle_search(update, context)
        return
    
    # Check if it's an IFSC code (11 characters, first 4 are letters)
    if len(cleaned_ifsc) == 11 and cleaned_ifsc[:4].isalpha() and cleaned_ifsc[4:].isalnum():
        await handle_ifsc_search(update, context)
        return
    
    # If we can't determine, show help
    help_text = f"""
{Style.INFO} *OSINT Pro Master Bot*

I can help you with phone, vehicle, and bank intelligence.

*For Phone Analysis:*
Send a 10-digit mobile number like:
• `7044165702`
• `+917044165702`

*For Vehicle Analysis:*
Send a vehicle registration like:
• `UP32AB1234`
• `DL1CAB1234`

*For IFSC Lookup:*
Send an IFSC code like:
• `SBIN0003010`
• `HDFC0000001`

Or use the buttons below to choose your search type.
    """
    
    keyboard = [
        [InlineKeyboardButton(f"{Style.PHONE} Phone Search", callback_data="phone_search"),
         InlineKeyboardButton(f"{Style.CAR} Vehicle Search", callback_data="vehicle_search")],
        [InlineKeyboardButton(f"{Style.BANK} IFSC Search", callback_data="ifsc_search")],
        [InlineKeyboardButton(f"{Style.HELP} Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        help_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

def main() -> None:
    """Start the bot and keep-alive server."""
    
    # Start keep-alive server in a separate thread
    keep_alive_thread = threading.Thread(target=run_keep_alive, daemon=True)
    keep_alive_thread.start()
    
    # Create Telegram Bot Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(help|main_menu|quick_examples|phone_search|vehicle_search|ifsc_search|new_search)$"))
    application.add_handler(CallbackQueryHandler(try_phone_example, pattern="^try_phone_example$"))
    application.add_handler(CallbackQueryHandler(try_vehicle_example, pattern="^try_vehicle_example$"))
    application.add_handler(CallbackQueryHandler(try_ifsc_example, pattern="^try_ifsc_example$"))
    application.add_handler(CallbackQueryHandler(retry_handler, pattern="^retry_"))
    application.add_handler(CallbackQueryHandler(handle_pagination, pattern="^page_"))
    
    # Start the Bot with enhanced logging
    print("🚀 OSINT PRO MASTER BOT - Starting Services...")
    print("=" * 50)
    print(f"{Style.SERVER} Keep-Alive Server: http://0.0.0.0:{KEEP_ALIVE_PORT}")
    print(f"{Style.ROCKET} Telegram Bot: @osint_pro_number_bot")
    print(f"{Style.PHONE} Phone Intelligence: ACTIVE")
    print(f"{Style.CAR} Vehicle Intelligence: ACTIVE")
    print(f"{Style.BANK} IFSC Lookup: ACTIVE")
    print(f"{Style.SHIELD} Status: ONLINE & MONITORING")
    print("=" * 50)
    print("Press Ctrl+C to stop all services")
    
    try:
        # Start polling with better error handling
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except Exception as e:
        logger.error(f"Bot error: {e}")
        print(f"{Style.ERROR} Bot service stopped due to error: {e}")
    finally:
        print("⏹️ All services stopped.")

if __name__ == '__main__':

    main()
