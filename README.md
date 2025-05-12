# JobZoeker Telegram

A tool for automatically scraping job listings from popular job boards and sending them to a Telegram channel.

## Overview

JobZoeker Telegram automatically scrapes job postings from multiple job sites based on your search terms, filters them according to your preferences, and sends the results directly to your Telegram account.

## Features

- 🌐 Multi-site scraping (LinkedIn, Indeed, Glassdoor)
- 🔍 Customizable search terms and locations
- 🔤 Language filtering (focuses on English job listings)
- 🚫 Keyword exclusion to remove unwanted job types
- 📱 Telegram notifications with interactive buttons
- ⏱️ Automated scheduling via GitHub Actions
- 📊 Saves all job data to CSV files for further analysis

## Setup Guide

### Prerequisites

- GitHub account (for hosting the automated workflow)
- Telegram account
- Telegram bot token (obtained from BotFather)
- Basic familiarity with GitHub

### Step 1: Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Start a chat and send `/newbot` command
3. Follow the instructions to create your bot
4. **Important:** Save the API token BotFather provides (looks like `1234567890:ABCDefGhIJKlmNoPQRsTUVwxyZ`)

### Step 2: Get Your Chat ID

You need to determine where the job notifications should be sent:

#### For personal notifications:
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It will reply with your personal chat ID

#### For a channel:
1. Create a channel in Telegram
2. Add your bot as an administrator to the channel
3. Get the channel ID (typically in format `-100xxxxxxxxxx`)
   - You can use [@username_to_id_bot](https://t.me/username_to_id_bot) to find this ID

### Step 3: Fork This Repository

1. Click the "Fork" button at the top right of this repository
2. This creates your own copy of the project in your GitHub account

### Step 4: Set Up Repository Secrets

1. In your forked repository, go to Settings → Secrets and variables → Actions
2. Add two new repository secrets:
   - `TELEGRAM_BOT_TOKEN`: Your bot token from Step 1
   - `TELEGRAM_CHAT_ID`: Your chat ID from Step 2

### Step 5: Customize Your Job Search

Edit the `get_data.py` file in your fork to customize your job search parameters:

```python
# Change these values to match your preferences
SEARCH_TERMS = [
    'ai engineer',
    'python developer',
    'data scientist',
    # Add your own search terms here
]

JOB_SITES = ["indeed", "glassdoor", "linkedin"]
LOCATION = "Netherlands"  # Change to your desired location
RESULTS_PER_SEARCH = 40
MAX_AGE_DAYS = 7
EXCLUDED_TERMS = ['PhD', 'Manager', 'Intern']  # Terms to exclude from results

```

###  Step 6: Enable GitHub Actions
Go to the "Actions" tab in your forked repository
Click the green button to enable workflows
The workflow is configured to run at 11 AM and 5 PM daily (you can modify this schedule in main.yml)
### Step 7: Trigger Your First Run
From the Actions tab, select the "Build Docker image and deploy to Heroku" workflow
Click "Run workflow" and select "Run workflow" from the dropdown
Wait for the workflow to complete (this may take a few minutes)
You should receive a test message in your Telegram chat
Running Locally (Optional)
If you want to test or run the job scraper on your own computer:

Clone your forked repository:

Install the required dependencies:

Create a .env file with your Telegram credentials:

Run the script:

Troubleshooting
No messages received: Ensure your bot has permission to send messages to the chat or channel
GitHub Actions failure: Check the workflow logs in the Actions tab for error details
Bot not responding: Make sure you didn't block the bot in Telegram
Error messages: Check if your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are correctly set
Files and Structure
get_data.py: Main script for collecting and filtering jobs
send_to_telegram.py: Handles formatting and sending job alerts to Telegram
main.yml: GitHub Actions workflow for automated running
requirements_collect_data.txt: Python dependencies
Contributing
Pull requests are welcome! Feel free to improve the code or add new features.

License
This project is available for personal use. Please respect the terms of service of the job sites being scraped. ```