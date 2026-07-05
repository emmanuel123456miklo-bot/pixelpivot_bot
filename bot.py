import os
import io
import re
import requests
import urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from PIL import Image
from datetime import datetime
import logging

# ====== CONFIGURATION ======
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
PORT = int(os.environ.get("PORT", 8080))

# ====== LOGGING ======
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ====== KEYBOARDS ======
main_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔗 Shorten URL", callback_data="shorten")],
    [InlineKeyboardButton("🎨 Generate Image", callback_data="generate")],
    [InlineKeyboardButton("🖼️ Convert Image", callback_data="convert")],
    [InlineKeyboardButton("📝 Check Plagiarism", callback_data="plagiarism")],
    [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
])

# ====== COMMAND HANDLERS ======

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with main menu"""
    welcome_text = (
        "👋 *Welcome to PixelPivot Bot!*\n\n"
        "I'm your all-in-one tool for:\n"
        "• 🔗 URL shortening\n"
        "• 🎨 AI image generation\n"
        "• 🖼️ Image conversion\n"
        "• 📝 Plagiarism checking\n\n"
        "Use the buttons below to get started!"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_keyboard, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help information"""
    help_text = (
        "📖 *How to use PixelPivot Bot*\n\n"
        "*URL Shortening*\n"
        "Send me any URL and I'll shorten it!\n\n"
        "*AI Image Generation*\n"
        "Send /generate followed by your prompt\n"
        "Example: `/generate a cat in space wearing a hat`\n\n"
        "*Image Conversion*\n"
        "Send me an image and tell me the format\n"
        "Example: `convert to png`\n\n"
        "*Plagiarism Check*\n"
        "Send me text and I'll check for plagiarism\n"
        "Example: `/check This is some text to check`\n\n"
        "Use the buttons below or type commands!"
    )
    await update.message.reply_text(help_text, reply_markup=main_keyboard, parse_mode="Markdown")

# ====== URL SHORTENER ======
async def shorten_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shorten a URL using is.gd or v.gd"""
    url = update.message.text.strip()
    
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("❌ Please send a valid URL starting with http:// or https://")
        return
    
    try:
        # Using is.gd API (free, no registration needed)
        response = requests.get(
            "https://is.gd/create.php",
            params={"format": "simple", "url": url},
            timeout=10
        )
        
        if response.status_code == 200 and not response.text.startswith("Error"):
            short_url = response.text.strip()
            await update.message.reply_text(
                f"✅ *URL Shortened!*\n\n"
                f"🔗 Original: {url}\n"
                f"✂️ Short: {short_url}\n\n"
                f"_Powered by is.gd_",
                parse_mode="Markdown"
            )
        else:
            # Try v.gd as fallback
            response = requests.get(
                "https://v.gd/create.php",
                params={"format": "simple", "url": url},
                timeout=10
            )
            if response.status_code == 200 and not response.text.startswith("Error"):
                short_url = response.text.strip()
                await update.message.reply_text(
                    f"✅ *URL Shortened!*\n\n"
                    f"🔗 Original: {url}\n"
                    f"✂️ Short: {short_url}",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("❌ Failed to shorten URL. Please try again.")
    except Exception as e:
        logger.error(f"Error shortening URL: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again later.")

# ====== AI IMAGE GENERATOR ======
async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate AI image from prompt using Pollinations.ai"""
    # Check if user provided a prompt
    if not context.args:
        await update.message.reply_text(
            "🎨 *Please provide a prompt*\n\n"
            "Example: `/generate a beautiful sunset over mountains`",
            parse_mode="Markdown"
        )
        return
    
    prompt = " ".join(context.args)
    
    # Send "typing" status
    await update.message.chat.send_action(action="typing")
    
    # Send initial message
    status_msg = await update.message.reply_text(f"🎨 *Generating image...*\n\nPrompt: _{prompt}_", parse_mode="Markdown")
    
    try:
        # Using Pollinations.ai (100% free, no API key needed)
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=768&seed={datetime.now().timestamp()}"
        
        # Download the image
        response = requests.get(image_url, timeout=30)
        
        if response.status_code == 200:
            # Send the image
            await update.message.reply_photo(
                photo=io.BytesIO(response.content),
                caption=f"🎨 *AI Generated Image*\n\nPrompt: _{prompt}_\n\n_Powered by Pollinations.ai_",
                parse_mode="Markdown"
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Failed to generate image. Please try again.")
            
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        await status_msg.edit_text("❌ An error occurred. Please try again later.")

# ====== IMAGE CONVERTER ======
async def convert_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Convert image to specified format"""
    # Get the format from the caption or command
    format_map = {
        'png': 'PNG',
        'jpg': 'JPEG',
        'jpeg': 'JPEG',
        'webp': 'WEBP',
        'bmp': 'BMP',
        'gif': 'GIF',
        'tiff': 'TIFF',
        'ico': 'ICO'
    }
    
    # Check if it's a reply to an image
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text(
            "🖼️ *Please reply to an image*\n\n"
            "1. Send an image to the bot\n"
            "2. Reply to that image with the format\n"
            "Example: `convert to png`\n\n"
            "*Supported formats:* png, jpg, webp, bmp, gif, tiff, ico",
            parse_mode="Markdown"
        )
        return
    
    # Extract format from message
    text = update.message.text.lower()
    target_format = None
    
    for fmt in format_map.keys():
        if fmt in text:
            target_format = format_map[fmt]
            break
    
    if not target_format:
        await update.message.reply_text(
            "❌ Please specify a valid format.\n\n"
            "Supported formats: png, jpg, webp, bmp, gif, tiff, ico"
        )
        return
    
    try:
        # Get the image file
        photo = update.message.reply_to_message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()
        
        # Convert the image
        img = Image.open(io.BytesIO(image_bytes))
        
        # Handle RGBA to RGB for JPEG
        if target_format == 'JPEG' and img.mode == 'RGBA':
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])
            img = rgb_img
        
        # Save to buffer
        output_buffer = io.BytesIO()
        img.save(output_buffer, format=target_format)
        output_buffer.seek(0)
        
        # Send the converted image
        filename = f"converted.{target_format.lower()}"
        await update.message.reply_document(
            document=output_buffer,
            filename=filename,
            caption=f"✅ *Converted to {target_format.upper()}*",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error converting image: {e}")
        await update.message.reply_text("❌ Failed to convert image. Please try again.")

# ====== PLAGIARISM CHECKER ======
async def check_plagiarism(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check text for plagiarism (simplified version)"""
    # Get text from command or reply
    text = None
    
    if context.args:
        text = " ".join(context.args)
    elif update.message.reply_to_message and update.message.reply_to_message.text:
        text = update.message.reply_to_message.text
    else:
        await update.message.reply_text(
            "📝 *Please provide text to check*\n\n"
            "Example: `/check This is some text to check`\n"
            "Or reply to a message with `/check`",
            parse_mode="Markdown"
        )
        return
    
    if len(text) < 10:
        await update.message.reply_text("❌ Text is too short. Please provide at least 10 characters.")
        return
    
    await update.message.chat.send_action(action="typing")
    
    try:
        word_count = len(text.split())
        char_count = len(text)
        
        await update.message.reply_text(
            f"📝 *Plagiarism Check Results*\n\n"
            f"📊 Text Analysis:\n"
            f"• Words: {word_count}\n"
            f"• Characters: {char_count}\n"
            f"• Sentences: {len(text.split('.'))}\n\n"
            f"⚠️ *Note:* This is a demo version.\n"
            f"For accurate plagiarism detection, please use a dedicated service like:\n"
            f"• Grammarly.com\n"
            f"• Quetext.com\n"
            f"• DupliChecker.com\n\n"
            f"_Powered by PixelPivot Bot_",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error checking plagiarism: {e}")
        await update.message.reply_text(
            "⚠️ *Service temporarily unavailable*\n\n"
            "Please try:\n"
            "1. Using a dedicated plagiarism checker like DupliChecker.com\n"
            "2. Or try again later\n\n"
            "_This is a demo feature_",
            parse_mode="Markdown"
        )

# ====== CALLBACK QUERY HANDLER ======
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "shorten":
        await query.edit_message_text(
            "🔗 *URL Shortener*\n\n"
            "Send me any URL and I'll shorten it!\n\n"
            "Example: `https://example.com/long/url/to/shorten`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
        )
    elif query.data == "generate":
        await query.edit_message_text(
            "🎨 *AI Image Generator*\n\n"
            "Send /generate followed by your prompt\n\n"
            "Example: `/generate a beautiful sunset over mountains`\n\n"
            "I'll create an AI-generated image for you!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
        )
    elif query.data == "convert":
        await query.edit_message_text(
            "🖼️ *Image Converter*\n\n"
            "1. Send me an image\n"
            "2. Reply to it with: `convert to png`\n\n"
            "*Supported formats:*\n"
            "png, jpg, webp, bmp, gif, tiff, ico",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
        )
    elif query.data == "plagiarism":
        await query.edit_message_text(
            "📝 *Plagiarism Checker*\n\n"
            "Send /check followed by the text\n\n"
            "Example: `/check This is some text to check for plagiarism`\n\n"
            "Or reply to a message with `/check`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
        )
    elif query.data == "help":
        await query.edit_message_text(
            "📖 *How to use PixelPivot Bot*\n\n"
            "*URL Shortening*\n"
            "Send any URL to shorten it\n\n"
            "*AI Image Generation*\n"
            "`/generate [your prompt]`\n\n"
            "*Image Conversion*\n"
            "Reply to an image with `convert to [format]`\n\n"
            "*Plagiarism Check*\n"
            "`/check [text]` or reply with `/check`\n\n"
            "Use the buttons below to go back!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
        )
    elif query.data == "back":
        await query.edit_message_text(
            "👋 *PixelPivot Bot*\n\n"
            "Choose a service below:",
            parse_mode="Markdown",
            reply_markup=main_keyboard
        )

# ====== MESSAGE HANDLER ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages"""
    text = update.message.text
    
    if not text:
        return
    
    # Check if it's a URL for shortening
    if re.match(r'^https?://[^\s]+', text):
        await shorten_url(update, context)
        return
    
    # Check if it's an image conversion command
    if "convert to" in text.lower() and update.message.reply_to_message:
        await convert_image(update, context)
        return
    
    # Default response
    await update.message.reply_text(
        "🤔 I didn't understand that. Use the buttons below or type /help for assistance.",
        reply_markup=main_keyboard
    )

# ====== ERROR HANDLER ======
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")

# ====== MAIN FUNCTION ======
def main():
    """Start the bot"""
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Register command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("generate", generate_image))
    app.add_handler(CommandHandler("check", check_plagiarism))
    
    # Register callback handler
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    # Register message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))
    
    # Register error handler
    app.add_error_handler(error_handler)
    
    # Start the bot using polling
    logger.info("Bot is starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
