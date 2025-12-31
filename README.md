# Mail Forwarder to Telegram

A lightweight SMTP server that forwards incoming emails directly to Telegram. Perfect for receiving notifications, alerts, or any emails in your Telegram chat.

## Prerequisites

- Python 3.13+ (or Docker)
- Telegram Bot Token (get it from [@BotFather](https://t.me/botfather))
- A domain with DNS access
- A server with a public IP address

## DNS Configuration

To receive emails, configure your domain's DNS records as follows:

### Required DNS Records

1. **A Record** - Point your domain to your server IP:
   ```
   Type: A
   Name: @ (or your subdomain)
   Value: YOUR_SERVER_IP
   TTL: 3600
   ```

2. **MX Record** - Set mail exchange record:
   ```
   Type: MX
   Name: @ (or your subdomain)
   Value: YOUR_DOMAIN (e.g., mail.example.com)
   Priority: 10
   TTL: 3600
   ```

3. **TXT Record** - Add SPF record to prevent spam:
   ```
   Type: TXT
   Name: @ (or your subdomain)
   Value: v=spf1 ip4:YOUR_SERVER_IP -all
   TTL: 3600
   ```

**Example Configuration:**
```
A    @              YOUR_SERVER_IP
MX   @              mail.example.com    10
TXT  @              "v=spf1 ip4:YOUR_SERVER_IP -all"
```

## Installation

### Option 1: Local Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/dima-xd/mail-forwarder-to-tg.git
   cd mail-forwarder-to-tg
   ```

2. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` with your values:**
   ```env
   TG_BOT_TOKEN=your_bot_token_here
   DOMAIN=example.com
   SMTP_HOST=0.0.0.0
   SMTP_PORT=25
   EMAIL_TTL=1800
   MAX_EMAILS=10000
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the server:**
   ```bash
   python main.py
   ```

### Option 2: Docker

1. **Clone and configure:**
   ```bash
   git clone https://github.com/dima-xd/mail-forwarder-to-tg.git
   cd mail-forwarder-to-tg
   cp .env.example .env
   # Edit .env file
   ```

2. **Build and run:**
   ```bash
   docker build -t mail-forwarder .
   docker run -d -p 25:25 --env-file .env --name mail-forwarder mail-forwarder
   ```

## Usage

1. **Start a chat with your Telegram bot**

2. **Create an email address:**
   ```
   /create john
   ```
   The bot will respond with your new email address: `john@example.com`

3. **Receive emails:**
   - All emails sent to `john@example.com` will be forwarded to your Telegram chat
   - The email nickname expires after 30 minutes (configurable via `EMAIL_TTL`)
   - You can only have one email address at a time

4. **Email format in Telegram:**
   ```
   📧 New Email
   2025-12-25 14:30:00

   From: sender@domain.com
   To: example@example.com
   Subject: Test Email

   Email body content...
   ```
