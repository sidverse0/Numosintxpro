import os
import logging
import re
import json
import requests
from flask import Flask, request

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

def get_relevant_results(data, searched_number):
    """Get relevant results that match the searched mobile number"""
    if not data or 'data' not in data:
        return []
    
    seen = set()
    relevant_results = []
    
    for item in data['data']:
        mobile = item.get('mobile', '')
        alt = item.get('alt', '')
        
        if mobile == searched_number or alt == searched_number:
            name = clean_text(item.get('name', ''))
            unique_key = f"{mobile}_{name}"
            
            if unique_key not in seen:
                seen.add(unique_key)
                relevant_results.append(item)
                
                if len(relevant_results) >= 2:
                    break
    
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
    """Format single phone result with emojis"""
    message = f"📊 *RESULT {result_number}:*\n\n"
    
    message += f"📞 *Mobile:* `{escape_markdown(result.get('mobile', 'N/A'))}`\n"
    message += f"👤 *Name:* {escape_markdown(clean_text(result.get('name', 'N/A')))}\n"
    message += f"👨‍👦 *Father:* {escape_markdown(clean_text(result.get('fname', 'N/A')))}\n"
    
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
        message += "*Possible reasons:*\n• Number not in database\n• Try different number\n• Number might be new/unregistered\n"
        return message
    
    relevant_results = get_relevant_results(data, searched_number)
    
    if not relevant_results:
        message += "❌ *No relevant results found*\n\n"
        message += "No records found matching the searched number\n"
        return message
    
    total_results = len(data.get('data', []))
    relevant_count = len(relevant_results)
    message += f"📈 *Found {total_results} total results, showing {relevant_count} relevant*\n\n"
    
    for i, result in enumerate(relevant_results, 1):
        message += format_phone_result(result, i)
        if i < len(relevant_results):
            message += "\n" + "─" * 30 + "\n\n"
    
    message += "\n" + "═" * 40 + "\n"
    message += "🔄 *Search again? Use /start command*"
    
    return message

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
    """Send welcome message with inline keyboard"""
    keyboard = {
        'inline_keyboard': [
            [{'text': '📱 Phone Search', 'callback_data': 'search_phone'}],
            [{'text': 'ℹ️ Help', 'callback_data': 'help'}]
        ]
    }
    
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
    
    return send_telegram_message(chat_id, welcome_text, 'Markdown', keyboard)

def send_help_message(chat_id):
    """Send help message"""
    help_text = """
*🤖 How to Use This Bot:*

1\. 📱 Click *"Phone Search"* button
2\. 🔢 Enter 10\-digit phone number in *any format*:
   \- 9525416052
   \- 91 9525 416052
   \- \+919525416052
   \- 09525416052
3\. 📊 Get detailed information with relevant results

*⚡ Smart Features:*
• 🔄 Auto number normalization
• 👤 Name & Family Details
• 🏠 Complete Address
• 📞 Alternative Numbers
• 🎯 Only relevant results
    """
    
    keyboard = {
        'inline_keyboard': [
            [{'text': '📱 Start Search', 'callback_data': 'search_phone'}]
        ]
    }
    
    return send_telegram_message(chat_id, help_text, 'MarkdownV2', keyboard)

def send_search_prompt(chat_id):
    """Send search prompt message"""
    text = "📱 *Phone Number Search*\n\nPlease enter the 10-digit phone number:\n\n*Examples:* \n• `9525416052`\n• `9142647694`\n• `9876543210`"
    return send_telegram_message(chat_id, text, 'Markdown')

def process_phone_search(chat_id, phone_number):
    """Process phone number search"""
    # Send processing message
    processing_text = f"🔍 *Searching for {escape_markdown(phone_number)}...*\n\n⏳ Please wait while we fetch the information..."
    send_telegram_message(chat_id, processing_text, 'Markdown')
    
    # Normalize phone number
    normalized_number, message = normalize_phone_number(phone_number)
    
    if normalized_number is None:
        error_text = f"{message}\n\n*Please enter a valid 10-digit phone number:*\n\n*Examples:* \n• `9525416052`\n• `9142647694`\n• `9876543210`"
        send_telegram_message(chat_id, error_text, 'Markdown')
        return
    
    # Show normalization info if needed
    if phone_number != normalized_number:
        send_telegram_message(chat_id, f"🔄 *Number Normalized:*\n`{phone_number}` → `{normalized_number}`", 'Markdown')
    
    # Get phone information
    data = get_phone_info(normalized_number)
    
    # Check if API returned error
    if 'error' in data:
        error_text = f"❌ *API Error\\!*\n\n{escape_markdown(data['error'])}\n\nPlease try again later\\."
        keyboard = {
            'inline_keyboard': [
                [{'text': '🔄 Try Again', 'callback_data': 'search_phone'}],
                [{'text': '🏠 Home', 'callback_data': 'home'}]
            ]
        }
        send_telegram_message(chat_id, error_text, 'MarkdownV2', keyboard)
        return
    
    # Check if no data found
    if not data.get('data'):
        error_text = f"❌ *No Data Found\\!*\n\nNo information found for `{escape_markdown(normalized_number)}`\n\n*Possible reasons:*\n• Number not in database\n• Try different number\n• Number might be new"
        keyboard = {
            'inline_keyboard': [
                [{'text': '🔄 Try Again', 'callback_data': 'search_phone'}],
                [{'text': '🏠 Home', 'callback_data': 'home'}]
            ]
        }
        send_telegram_message(chat_id, error_text, 'MarkdownV2', keyboard)
        return
    
    # Format and send results
    result_message = format_phone_results(normalized_number, data)
    
    keyboard = {
        'inline_keyboard': [
            [{'text': '🔄 Search Again', 'callback_data': 'search_phone'}],
            [{'text': '🏠 Home', 'callback_data': 'home'}]
        ]
    }
    
    send_telegram_message(chat_id, result_message, 'MarkdownV2', keyboard)

@app.route('/')
def index():
    return "📱 Phone Info Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Telegram webhook"""
    try:
        data = request.get_json()
        
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')
            
            if text == '/start':
                send_welcome_message(chat_id)
            elif text == '/help':
                send_help_message(chat_id)
            else:
                # Check if user is in search mode (you can implement state management here)
                process_phone_search(chat_id, text)
        
        elif 'callback_query' in data:
            callback_query = data['callback_query']
            chat_id = callback_query['message']['chat']['id']
            data = callback_query['data']
            
            if data == 'search_phone':
                send_search_prompt(chat_id)
            elif data == 'help':
                send_help_message(chat_id)
            elif data == 'home':
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
    webhook_url = "https://your-render-app-url.onrender.com/webhook"
    response = requests.post(f"{TELEGRAM_API_URL}/setWebhook", 
                           json={'url': webhook_url})
    return response.json()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)