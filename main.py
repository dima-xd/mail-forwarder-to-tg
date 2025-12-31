import logging
import os
import html
import re
import sys
from datetime import datetime
from email import policy
from email.parser import BytesParser

from aiosmtpd.controller import Controller
from telegram import Bot, Update
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, ContextTypes
from cachetools import TTLCache

load_dotenv()

TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
DOMAIN = os.getenv('DOMAIN')
SMTP_HOST = os.getenv('SMTP_HOST', '0.0.0.0')
SMTP_PORT = int(os.getenv('SMTP_PORT', '25'))
EMAIL_TTL = int(os.getenv('EMAIL_TTL', '1800'))
MAX_EMAILS = int(os.getenv('MAX_EMAILS', '10000'))

bot = Bot(token=TG_BOT_TOKEN)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

emails = TTLCache(maxsize=MAX_EMAILS, ttl=EMAIL_TTL)

def _extract_text(msg):
    if not msg.is_multipart():
        payload = msg.get_payload(decode=True)
        return payload.decode('utf-8', errors='ignore') if payload else ""

    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            payload = part.get_payload(decode=True)
            if payload:
                return payload.decode('utf-8', errors='ignore')

    return "No text content"


def _format_for_telegram(sender, recipients, subject, body):
    safe_sender = html.escape(sender)
    safe_recipients = html.escape(', '.join(recipients))
    safe_subject = html.escape(subject)
    safe_body = html.escape(body)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""<b>📧 New Email</b>
<code>{timestamp}</code>

<b>From:</b> <code>{safe_sender}</code>
<b>To:</b> <code>{safe_recipients}</code>
<b>Subject:</b> {safe_subject}

<pre>{safe_body}</pre>"""


class MailHandler:
    async def handle_DATA(self, server, session, envelope):
        try:
            msg = BytesParser(policy=policy.default).parsebytes(envelope.content)
            subject = msg.get('subject', 'No Subject')
            sender = envelope.mail_from

            body = _extract_text(msg)

            # Get registered nicknames for recipients
            registered_recipients = []
            for rcpt in envelope.rcpt_tos:
                nickname = rcpt.split('@')[0]
                if nickname in emails:
                    registered_recipients.append(rcpt)

            if not registered_recipients:
                logging.info(f"No registered recipients for email to {envelope.rcpt_tos}. Discarding email.")
                return '250 OK'

            for rcpt in registered_recipients:
                logging.info(f"Email received for {rcpt} from {sender} with subject '{subject}'")

                telegram_message = _format_for_telegram(
                    sender=sender,
                    recipients=envelope.rcpt_tos,
                    subject=subject,
                    body=body
                )

                user = emails[rcpt.split('@')[0]]

                await bot.send_message(
                    chat_id=user,
                    text=telegram_message,
                    parse_mode='HTML'
                )

            return '250 OK'

        except Exception as e:
            logging.error(f"[ERROR] {e}")
            return '500 Error'

def is_valid_email_name(name: str) -> bool:
    EMAIL_NAME_RE = re.compile(
        r'^[a-z0-9](?:[a-z0-9]|[_-](?=[a-z0-9])){1,28}[a-z0-9]$'
    )
    return bool(EMAIL_NAME_RE.fullmatch(name))

async def create(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id

    if len(update.message.text.split(' ')) != 2:
        await update.message.reply_html(
            f"{user.mention_html()}, usage: /create 'nickname'\nExample: /create john",
        )
        return

    if not is_valid_email_name(update.message.text.split(' ')[1]):
        await update.message.reply_html(
            f"{user.mention_html()}, invalid nickname. It must be 3-30 characters long, contain only lowercase letters, digits, underscores or hyphens, and cannot start or end with a special character.",
        )
        return

    nickname = update.message.text.split(' ')[1]

    # Check if user_id already has an email
    if user_id in emails.values():
        await update.message.reply_html(
            f"{user.mention_html()}, you already have an email address. Only one email per user is allowed.\nYou can create a new one after 30 minutes.",
        )
        return

    # Check if nickname is already taken
    if emails.get(nickname):
        await update.message.reply_html(
            f"{user.mention_html()}, nickname <b>{nickname}</b> is already taken. Choose another one.",
        )
        return

    emails[nickname] = user.id

    await update.message.reply_html(
        f"{user.mention_html()}, created <b>{nickname}@{os.getenv('DOMAIN')}</b> email address.\nAll emails sent to this address will be forwarded to this Telegram chat.",
    )

def main():
    controller = Controller(
        MailHandler(),
        hostname=SMTP_HOST,
        port=SMTP_PORT
    )

    logging.info("🚀 SMTP server started on localhost:%d", SMTP_PORT)
    logging.info("📧 Waiting for emails...")
    logging.info("🛑 Press Ctrl+C to stop")

    controller.start()

    application = Application.builder().token(TG_BOT_TOKEN).build()

    application.add_handler(CommandHandler("create", create))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    if not TG_BOT_TOKEN or not DOMAIN:
        logging.error("❌ Set environment variables:")
        logging.error("   TG_BOT_TOKEN - Telegram bot token")
        logging.error("   DOMAIN - Your email domain (e.g., example.com)")
        exit(1)

    main()
