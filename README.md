### Getting a Telegram Bot Token

## Step 1: Create a bot via @BotFather

1. Open Telegram and find @BotFather
2. Send the command /newbot
3. Enter the bot name (e.g., "Beauty Salon")
4. Enter the bot username (e.g., beauty_salon_bot)
5. Copy the token (format: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)

## Step 2: Configure Web App

1. Send the command /mybots to @BotFather
2. Select your bot
3. Click "Bot Settings" → "Menu Button" → "Configure menu button"
4. Send the URL of your Web App (https://yourdomain.com/webapp/)

## Step 3: Get your Telegram ID

1. Find @userinfobot
2. Send /start
3. Copy your ID (number)

### Configuring Google Sheets API

## Step 1: Create a project in Google Cloud Console

1. Go to https://console.cloud.google.com/
2. Create a new project (e.g., "Telegram Booking Bot")
3. Select the created project

## Step 2: Enable APIs

1. In the side menu, select "APIs & Services" → "Enable APIs and Services"
2. Find and enable:
   - Google Sheets API
   - Google Drive API

## Step 3: Create a Service Account

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Enter a name (e.g., "booking-bot")
4. Click "Create and Continue"
5. Select the role "Editor"
6. Click "Done"

## Step 4: Create a JSON Key

1. Click on the created service account
2. Go to the "Keys" tab
3. Click "Add Key" → "Create new key"
4. Select JSON format
5. Download the file and rename it to credentials.json

## Step 5: Configure Google Sheet

1. Create a new Google Sheet
2. Name it "Client Bookings"
3. Open the credentials.json file
4. Find the "client_email" field (format: xxx@xxx.iam.gserviceaccount.com)
5. In the Google Sheet, click "Share"
6. Add the service account email with "Editor" permissions