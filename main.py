import os
import asyncio
import html
from datetime import datetime
from email import policy
from email.parser import BytesParser

from aiosmtpd.controller import Controller
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

bot = Bot(token=os.getenv('TG_BOT_TOKEN'))
TG_CHANNEL_ID = os.getenv('TG_CHANNEL_ID')

def _log_email(sender, recipients, subject, body):
    print("=" * 50)
    print("📨 EMAIL RECEIVED")
    print(f"From: {sender}")
    print(f"To: {', '.join(recipients)}")
    print(f"Subject: {subject}")
    print(f"Body preview: {body[:200]}...")
    print("=" * 50)


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
    safe_body = html.escape(body[:1500])

    if len(body) > 1500:
        safe_body += " [...]"

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

            telegram_message = _format_for_telegram(
                sender=sender,
                recipients=envelope.rcpt_tos,
                subject=subject,
                body=body
            )

            _log_email(sender, envelope.rcpt_tos, subject, body)

            await bot.send_message(
                chat_id=TG_CHANNEL_ID,
                text=telegram_message,
                parse_mode='HTML'
            )

            return '250 OK'

        except Exception as e:
            print(f"[ERROR] {e}")
            return '500 Error'


async def main():
    controller = Controller(
        MailHandler(),
        hostname='127.0.0.1',
        port=1025
    )

    print("🚀 SMTP server started on localhost:1025")
    print("📧 Waiting for emails...")
    print("🛑 Press Ctrl+C to stop")

    controller.start()

    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        print("\n⏹ Stopping server...")
    finally:
        controller.stop()


if __name__ == "__main__":
    if not os.getenv('TG_BOT_TOKEN') or not os.getenv('TG_CHANNEL_ID'):
        print("❌ Set environment variables:")
        print("   TG_BOT_TOKEN - Telegram bot token")
        print("   TG_CHANNEL_ID - Telegram chat/channel ID")
        exit(1)

    asyncio.run(main())