import os
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Initialize Flask app
app = Flask(__name__)

# Retrieve environment variables
TOKEN = os.environ.get("TELEGRAM_TOKEN")
# Render provides the PORT dynamically, default to 5000 for local testing
PORT = int(os.environ.get("PORT", 5000)) 
WEBHOOK_URL = os.environ.get("WEBHOOK_URL") # Example: https://your-app.onrender.com

# Initialize Telegram Application
tg_app = Application.builder().token(TOKEN).build()

# --- BOT LOGIC ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message and a main menu for the Store Guide."""
    keyboard = [
        [InlineKeyboardButton("🏬 View Categories", callback_data="categories")],
        [InlineKeyboardButton("📍 Store Location & Hours", callback_data="info")],
        [InlineKeyboardButton("📞 Contact Support", callback_data="support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if message exists (from text command) or if it's a callback query
    if update.message:
        await update.message.reply_text(
            "Welcome to the Store Guide Bot! 🛍️\nHow can I assist you today?", 
            reply_markup=reply_markup
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            "Welcome to the Store Guide Bot! 🛍️\nHow can I assist you today?", 
            reply_markup=reply_markup
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles button clicks from the user."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "categories":
        keyboard = [
            [InlineKeyboardButton("👕 Clothing", callback_data="cat_clothing")],
            [InlineKeyboardButton("📱 Electronics", callback_data="cat_electronics")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ]
        await query.edit_message_text("Select a store category:", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif query.data == "info":
        text = "📍 **Main Location:** 123 Market St, Cityville\n\n⏰ **Hours:**\nMon - Fri: 9 AM - 9 PM\nSat - Sun: 10 AM - 6 PM"
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif query.data == "support":
        text = "📞 Need help? Reach out to our team at support@example.com or call +1-555-0199."
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        
    elif query.data == "main_menu":
        await start(update, context)
        
    elif query.data.startswith("cat_"):
        category = query.data.split("_")[1].capitalize()
        text = f"You selected **{category}**. Here are the featured items today...\n(Integrate your regional platform link or catalog here!)"
        keyboard = [[InlineKeyboardButton("🔙 Back to Categories", callback_data="categories")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# Register Telegram Handlers
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CallbackQueryHandler(button_handler))

# --- FLASK ROUTES FOR WEBHOOK ---

@app.route("/", methods=["GET"])
def index():
    return "Store Guide Bot is running!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    """Receives updates from Telegram and processes them."""
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), tg_app.bot)
        # Process the update asynchronously
        asyncio.run(tg_app.process_update(update))
        return "OK", 200

# --- INITIALIZATION ---

def setup_webhook():
    """Registers the webhook URL with Telegram on startup."""
    if WEBHOOK_URL:
        asyncio.run(tg_app.initialize())
        asyncio.run(tg_app.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook"))
        print(f"Webhook set successfully to {WEBHOOK_URL}/webhook")
    else:
        print("Warning: WEBHOOK_URL not found. Running locally without registering webhook.")

# Trigger webhook registration when running in production
if os.environ.get("TELEGRAM_TOKEN"):
    setup_webhook()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
