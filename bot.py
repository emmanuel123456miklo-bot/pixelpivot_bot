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
    
    # Start the bot - USE POLLING ONLY (simpler for Railway)
    logger.info("Bot is starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
