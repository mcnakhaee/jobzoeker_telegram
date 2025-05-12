"""
Configuration settings for the JobZoeker application.

This module centralizes all configuration settings for the job scraping
and notification system.
"""

import os
from pathlib import Path
from typing import List

# Project paths
OUTPUT_DIR = Path(".")
SENT_JOBS_FILE = OUTPUT_DIR / "sent_jobs.csv"

# Telegram settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SEND_TELEGRAM_NOTIFICATIONS = True
MAX_MESSAGE_LENGTH = 4096  # Telegram message character limit

# Job search settings
SEARCH_TERMS = [
    'ai engineer',
    'weaviate', 
    'rag',
    'data visualization',
    'generative ai',
    'azure ai search',
    'genai',
    'ggplot',
    'llm',
    'python'
]

JOB_SITES = ["indeed", "glassdoor", "linkedin"]
LOCATION = "Netherlands"
RESULTS_PER_SEARCH = 40
MAX_AGE_DAYS = 7
EXCLUDED_TERMS = ['PhD', 'Manager', 'Intern']

# Scraping settings
RETRY_ATTEMPTS = 3
REQUEST_DELAY = 5  # seconds between requests