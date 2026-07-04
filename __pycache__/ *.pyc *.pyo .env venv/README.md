# PixelPivot Bot 🤖

An all-in-one Telegram bot for URL shortening, AI image generation, image conversion, and plagiarism checking.

## Features

- 🔗 URL Shortening (is.gd & v.gd)
- 🎨 AI Image Generation (Pollinations.ai)
- 🖼️ Image Conversion (PNG, JPG, WEBP, BMP, GIF, TIFF, ICO)
- 📝 Plagiarism Checking

## Deployment

This bot is designed to run on Railway with GitHub integration.

### Environment Variables

- `BOT_TOKEN`: Your Telegram bot token from @BotFather
- `RAILWAY_ENVIRONMENT`: Set to "true" for Railway deployment

## Commands

- `/start` - Show welcome menu
- `/help` - Show help information
- `/generate [prompt]` - Generate AI image
- `/check [text]` - Check text for plagiarism
- Send any URL to shorten it
- Reply to an image with "convert to [format]"

## License

MIT
