from datetime import datetime
import json
import os
from http.client import HTTPException
from typing import Dict, Any
from http import HTTPStatus
from http.client import responses
from telegram import Update
from telegram.ext import Application, CommandHandler

# Get the token from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

# Initialize bot application
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

async def start_command(update: Update, context):
    """Handle /start command"""
    await update.message.reply_text('Hello! DualAI bot is working.')

# Add command handlers
application.add_handler(CommandHandler("start", start_command))

async def handle_update(update_dict):
    """Process incoming Telegram update"""
    update = Update.de_json(update_dict, application.bot)
    await application.process_update(update)

async def handler(request):
    """Handle incoming requests."""
    try:
        if request.method == 'GET':
            body = {
                "status": "ok",
                "message": "DualAI bot endpoint is working",
                "timestamp": datetime.now().isoformat(),
                "bot_info": {
                    "token_configured": bool(TELEGRAM_BOT_TOKEN),
                    "endpoint_url": request.headers.get('x-forwarded-proto', 'http') + '://' + request.headers.get('x-forwarded-host', 'localhost')
                }
            }
            return Response(
                status=200,
                body=json.dumps(body),
                headers={
                    "Content-Type": "application/json"
                }
            )
        elif request.method == 'POST':
            # Validate that request is from Telegram
            if not TELEGRAM_BOT_TOKEN:
                return Response(
                    status=401,
                    body=json.dumps({"error": "Telegram token not configured"}),
                    headers={"Content-Type": "application/json"}
                )

            # Parse incoming update from Telegram
            try:
                update_dict = json.loads(request.body)
            except json.JSONDecodeError:
                return Response(
                    status=400,
                    body=json.dumps({"error": "Invalid JSON"}),
                    headers={"Content-Type": "application/json"}
                )
            
            # Process the update
            await handle_update(update_dict)
            
            body = {
                "status": "ok",
                "message": "Update processed successfully"
            }
            return Response(
                status=200,
                body=json.dumps(body),
                headers={
                    "Content-Type": "application/json"
                }
            )
        else:
            body = {
                "error": "Method not allowed"
            }
            return Response(
                status=405,
                body=json.dumps(body),
                headers={
                    "Content-Type": "application/json"
                }
            )
    except Exception as e:
        body = {
            "error": str(e)
        }
        return Response(
            status=500,
            body=json.dumps(body),
            headers={
                "Content-Type": "application/json"
            }
        )

class Response:
    def __init__(self, status: int, body: str, headers: Dict[str, str] = None):
        self.status = status
        self.statusText = responses[status]
        self.body = body
        self.headers = headers or {} 