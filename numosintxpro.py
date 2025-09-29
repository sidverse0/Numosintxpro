import os
import logging
import re
import json
import requests
from flask import Flask, request

# Bot configuration
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8116705267:AAHuwa5tUK2sErOtTf64StZ4STOQUv2Abp4')
PORT = int(os.environ.get('PORT', 5000))

app = Flask(__name__)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# API endpoints
PHONE_API_URL = "https://decryptkarnrwalebkl.wasmer.app/?key=lodalelobaby&term="
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

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
            if '}{' in response_text:
                response_text = response_text.split('}{')[0] + '}'
            
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
        response = requests.get(f"{PHONE_API_URL}{phone_number}", timeout=15)
        
        if response.status_code != 200:
            return {"error": f"API returned status code: {response.status_code}"}
        
        data = safe_json_parse(response.text)
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

def send_telegram_message(chat_id, text, parse_mode='MarkdownV2', reply_markup=None):
    """Send message to Telegram using direct API call"""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode
    }
    
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return None

def send_welcome_message(chat_id):
    """Send welcome message with beautiful inline keyboard"""
    keyboard = {
        'inline_keyboard': [
            [{'text': '🔍 Phone Search', 'callback_data': 'search_phone'}],
            [{'text': 'ℹ️ Help Guide', 'callback_data': 'help'}],
            [{'text': '📊 About Bot', 'callback_data': 'about'}]
        ]
    }
    
    welcome_text = """
🎯 **Welcome to Phone Intelligence Bot** 🔍

I'm your advanced phone number analysis assistant! I can help you uncover detailed information about any phone number with precision and speed.

✨ **Premium Features:**
• 👨‍💼 Name & Family Details
• 🏡 Complete Address Information  
• 📞 Alternative Contact Numbers
• 🌍 Telecom Circle & Operator
• 🆔 Unique Identification Data
• 📧 Email Addresses (if available)

🚀 **Get started by clicking the search button below!**
    """
    
    return send_telegram_message(chat_id, welcome_text, 'Markdown', keyboard)

def send_help_message(chat_id):
    """Send help message with detailed instructions"""
    help_text = """
📖 **How to Use This Bot:** 🤖

1️⃣ **Click** *"Phone Search"* button
2️⃣ **Enter** 10-digit phone number in *any format*:
   📝 Examples:
   • `9525416052`
   • `91 9525 416052`  
   • `+919525416052`
   • `09525416052`
3️⃣ **Receive** detailed intelligence report

⚡ **Smart Features:**
• 🔄 Auto number normalization
• 👨‍💼 Comprehensive name details
• 🏡 Complete address mapping
• 📞 Alternative number tracking
• 🌍 Telecom circle information
• 🎯 All relevant results (no limits!)
    """
    
    keyboard = {
        'inline_keyboard': [
            [{'text': '🔍 Start Search', 'callback_data': 'search_phone'}],
            [{'text': '🏠 Main Menu', 'callback_data': 'home'}]
        ]
    }
    
    return send_telegram_message(chat_id, help_text, 'Markdown', keyboard)

def send_about_message(chat_id):
    """Send about message"""
    about_text = """
🤖 **About Phone Intelligence Bot**

**Version:** 2.0 • **Status:** 🟢 Active

🔧 **Technical Features:**
• Advanced API Integration
• Real-time Data Processing  
• Smart Duplicate Filtering
• Secure & Private Queries
• 24/7 Availability

📊 **Capabilities:**
• Multiple database access
• Comprehensive result analysis
• Beautiful formatted reports
• Instant response times

👨‍💻 **Developer:** Advanced AI Systems
🕒 **Uptime:** 99.9% Reliability
    """
    
    keyboard = {
        'inline_keyboard': [
            [{'text': '🔍 Start Searching', 'callback_data': 'search_phone'}],
            [{'text': '📖 User Guide', 'callback_data': 'help'}],
            [{'text': '🏠 Main Menu', 'callback_data': 'home'}]
        ]
    }
    
    return send_telegram_message(chat_id, about_text, 'Markdown', keyboard)

def send_search_prompt(chat_id):
    """Send search prompt message"""
    text = """
🔍 **Phone Number Search** 📱

Please enter the 10-digit phone number you want to investigate:

📝 **Format Examples:**
• `9525416052`
• `9142647694`  
• `9876543210`
• `91 9525 416052`
• `+919525416052`

💡 **Tip:** You can enter the number in any format - I'll automatically clean it up!
    """
    return send_telegram_message(chat_id, text, 'Markdown')

def process_phone_search(chat_id, phone_number):
    """Process phone number search with enhanced UX"""
    # Send processing message with cool emojis
    processing_text = f"""
🕵️‍♂️ **Launching Investigation** 🔍

**Target Number:** `{escape_markdown(phone_number)}`

⏳ Scanning multiple databases...
🔄 Processing information...
📊 Analyzing results...

Please wait while I gather comprehensive intelligence...
    """
    send_telegram_message(chat_id, processing_text, 'MarkdownV2')
    
    # Normalize phone number
    normalized_number, message = normalize_phone_number(phone_number)
    
    if normalized_number is None:
        error_text = f"""
❌ **Invalid Input** 🚫

{message}

📋 **Please enter a valid 10-digit phone number:**

💡 **Examples:**
• `9525416052`
• `9142647694`
• `9876543210`
        """
        send_telegram_message(chat_id, error_text, 'Markdown')
        return
    
    # Show normalization info if needed
    if phone_number != normalized_number:
        normalization_msg = f"""
🔄 **Number Normalized** ✅

**Original:** `{phone_number}`
**Cleaned:** `{normalized_number}`

Proceeding with cleaned number...
        """
        send_telegram_message(chat_id, normalization_msg, 'Markdown')
    
    # Get phone information
    data = get_phone_info(normalized_number)
    
    # Check if API returned error
    if 'error' in data:
        error_text = f"""
⚠️ **API Connection Error** 🔌

**Details:** {escape_markdown(data['error'])}

🔄 Please try again in a few moments.
📞 If problem persists, try a different number.
        """
        keyboard = {
            'inline_keyboard': [
                [{'text': '🔄 Try Again', 'callback_data': 'search_phone'}],
                [{'text': '🏠 Main Menu', 'callback_data': 'home'}]
            ]
        }
        send_telegram_message(chat_id, error_text, 'MarkdownV2', keyboard)
        return
    
    # Check if no data found
    if not data.get('data'):
        error_text = f"""
🔍 **No Intelligence Found** 🕵️‍♂️

**Number:** `{escape_markdown(normalized_number)}`

📊 **Possible Reasons:**
• 📵 Number not in our databases
• 🔄 Try a different number format  
• 🆕 Number might be new/unregistered
• 🔒 Number information is protected
        """
        keyboard = {
            'inline_keyboard': [
                [{'text': '🔄 Try Different Number', 'callback_data': 'search_phone'}],
                [{'text': '🏠 Main Menu', 'callback_data': 'home'}]
            ]
        }
        send_telegram_message(chat_id, error_text, 'MarkdownV2', keyboard)
        return
    
    # Format and send results
    result_message = format_phone_results(normalized_number, data)
    
    keyboard = {
        'inline_keyboard': [
            [{'text': '🔍 New Search', 'callback_data': 'search_phone'}],
            [{'text': '🏠 Main Menu', 'callback_data': 'home'}],
            [{'text': '📊 More Info', 'callback_data': 'about'}]
        ]
    }
    
    # Split and send message parts
    message_parts = split_long_message(result_message)
    for i, part in enumerate(message_parts):
        if i == len(message_parts) - 1:
            # Last part gets the buttons
            send_telegram_message(chat_id, part, 'MarkdownV2', keyboard)
        else:
            send_telegram_message(chat_id, part, 'MarkdownV2')

@app.route('/')
def index():
    return "🎯 Phone Intelligence Bot is running! 🔍"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Telegram webhook"""
    try:
        data = request.get_json()
        
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '').strip()
            
            if text == '/start':
                send_welcome_message(chat_id)
            elif text == '/help':
                send_help_message(chat_id)
            elif text.startswith('/'):
                # Ignore other commands
                pass
            else:
                # Assume any other text is a phone number search
                process_phone_search(chat_id, text)
        
        elif 'callback_query' in data:
            callback_query = data['callback_query']
            chat_id = callback_query['message']['chat']['id']
            callback_data = callback_query['data']
            
            if callback_data == 'search_phone':
                send_search_prompt(chat_id)
            elif callback_data == 'help':
                send_help_message(chat_id)
            elif callback_data == 'about':
                send_about_message(chat_id)
            elif callback_data == 'home':
                send_welcome_message(chat_id)
            
            # Answer callback query to remove loading state
            requests.post(f"{TELEGRAM_API_URL}/answerCallbackQuery", 
                         json={'callback_query_id': callback_query['id']})
        
        return 'OK'
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'OK'

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Set Telegram webhook (run this once)"""
    # You need to replace this with your actual Render URL
    webhook_url = "https://your-app-name.onrender.com/webhook"
    response = requests.post(f"{TELEGRAM_API_URL}/setWebhook", 
                           json={'url': webhook_url})
    return response.json()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)