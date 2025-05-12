"""
Module for sending job alerts to Telegram.

This module contains functions to format and send job listings to a Telegram channel.
"""

import pandas as pd
import requests
from datetime import datetime
from typing import Dict, List, Optional, Union

from config import (
    TELEGRAM_BOT_TOKEN, 
    TELEGRAM_CHAT_ID, 
    SENT_JOBS_FILE, 
    MAX_MESSAGE_LENGTH
)
from logger import setup_logger

# Set up logger
logger = setup_logger(__name__)


class TelegramNotifier:
    """Class to handle Telegram notifications for job postings."""
    
    @staticmethod
    def send_to_telegram(message: str, buttons: Optional[List[Dict[str, str]]] = None) -> Dict:
        """
        Send a message to Telegram using the Telegram Bot API with optional inline buttons.

        Args:
            message: The message text to send
            buttons: A list of dictionaries representing buttons (text and callback data)

        Returns:
            Response from the Telegram API as a dictionary
        """
        try:
            if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
                logger.error("Telegram credentials not set! Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in environment.")
                return {"ok": False, "error": "Credentials not set"}

            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False,
            }

            # Add inline buttons if provided
            if buttons:
                inline_keyboard = [[{"text": btn["text"], "callback_data": btn["callback_data"]}] for btn in buttons]
                payload["reply_markup"] = {"inline_keyboard": inline_keyboard}

            response = requests.post(url, json=payload)
            result = response.json()

            if not result.get("ok"):
                logger.error(f"Failed to send Telegram message: {result.get('description')}")

            return result
        except Exception as e:
            logger.error(f"Error sending message to Telegram: {e}")
            return {"ok": False, "error": str(e)}

    @staticmethod
    def format_job_message(job: pd.Series) -> str:
        """
        Format a job listing as a Telegram message with Markdown formatting.

        Args:
            job: A pandas Series containing job information

        Returns:
            Formatted job message for Telegram
        """
        # Create a Markdown formatted message
        message_parts = []
        
        # Add job title
        message_parts.append(f"*{job['title']}*")
        
        # Add company name
        if 'company' in job and pd.notna(job['company']):
            message_parts.append(f"📢 *{job['company']}*")
        
        # Add location
        if 'location' in job and pd.notna(job['location']):
            message_parts.append(f"📍 {job['location']}")
        
        # Add job details
        details = []
        if 'job_type' in job and pd.notna(job['job_type']):
            details.append(job['job_type'])
        if 'date_posted' in job and pd.notna(job['date_posted']):
            details.append(f"Posted: {job['date_posted']}")
        if details:
            message_parts.append(" | ".join(details))
        
        # Add search term that matched
        if 'search_term' in job and pd.notna(job['search_term']):
            message_parts.append(f"🔍 Search term: `{job['search_term']}`")
        
        # Add source
        if 'source' in job and pd.notna(job['source']):
            message_parts.append(f"Source: {job['source']}")
        
        # Add job URL
        if 'job_url' in job and pd.notna(job['job_url']):
            message_parts.append(f"\n🔗 [View Job Posting]({job['job_url']})")
        
        # Join all parts with newlines
        message = "\n".join(message_parts)
        
        # Truncate message if it's too long for Telegram
        if len(message) > MAX_MESSAGE_LENGTH:
            message = message[:MAX_MESSAGE_LENGTH - 100] + "...\n\n[Message truncated]"
        
        return message

    @staticmethod
    def add_job_buttons(job_id: str) -> List[Dict[str, str]]:
        """Create interactive buttons for a job listing."""
        return [
            {"text": "💾 Save Job", "callback_data": f"save_{job_id}"},
            {"text": "👍 Interested", "callback_data": f"interested_{job_id}"},
            {"text": "✅ Applied", "callback_data": f"applied_{job_id}"}
        ]


class JobNotificationTracker:
    """Class to track which jobs have already been sent to Telegram."""
    
    @staticmethod
    def load_sent_jobs() -> pd.DataFrame:
        """
        Load the list of already sent jobs from CSV file.

        Returns:
            DataFrame containing ids of jobs that have already been sent
        """
        try:
            if SENT_JOBS_FILE.exists():
                return pd.read_csv(SENT_JOBS_FILE)
            else:
                logger.info(f"No sent jobs record found. Creating new tracking file.")
                return pd.DataFrame(columns=['job_id'])
        except Exception as e:
            logger.error(f"Error loading sent jobs file: {e}")
            return pd.DataFrame(columns=['job_id'])

    @staticmethod
    def save_sent_jobs(df: pd.DataFrame) -> None:
        """
        Save the list of sent jobs to CSV file.

        Args:
            df: DataFrame containing job ids that have been sent
        """
        try:
            df.to_csv(SENT_JOBS_FILE, index=False)
            logger.info(f"Updated sent jobs tracking file with {len(df)} entries")
        except Exception as e:
            logger.error(f"Error saving sent jobs file: {e}")


def send_jobs_to_telegram(jobs_df: pd.DataFrame) -> int:
    """
    Send job listings to Telegram that haven't been sent before.

    Args:
        jobs_df: DataFrame containing job listings

    Returns:
        Number of new jobs sent
    """
    if jobs_df.empty:
        logger.info("No jobs to send")
        return 0

    # Create a unique job identifier
    jobs_df['job_id'] = jobs_df.apply(
        lambda row: f"{row.get('title', '')}_{row.get('company', '')}_{row.get('location', '')}", 
        axis=1
    )
    
    # Load previously sent jobs
    tracker = JobNotificationTracker()
    sent_jobs = tracker.load_sent_jobs()
    sent_job_ids = set(sent_jobs['job_id'].values) if not sent_jobs.empty else set()
    
    # Identify new jobs that haven't been sent yet
    new_jobs = jobs_df[~jobs_df['job_id'].isin(sent_job_ids)]
    
    if new_jobs.empty:
        logger.info("No new jobs to send")
        return 0
    
    logger.info(f"Sending {len(new_jobs)} new job listings to Telegram")
    
    # Send each new job to Telegram with buttons
    notifier = TelegramNotifier()
    sent_count = 0
    
    for _, job in new_jobs.iterrows():
        message = notifier.format_job_message(job)
        buttons = notifier.add_job_buttons(job['job_id'])
        response = notifier.send_to_telegram(message, buttons)
        
        if response.get("ok", False):
            sent_count += 1
            # Record this job as sent
            sent_jobs = pd.concat([
                sent_jobs, 
                pd.DataFrame([{'job_id': job['job_id']}])
            ], ignore_index=True)
    
    # Save updated sent jobs list
    tracker.save_sent_jobs(sent_jobs)
    
    logger.info(f"Successfully sent {sent_count} new job listings to Telegram")
    return sent_count


def send_test_message() -> bool:
    """
    Send a test message to Telegram to verify the connection.
    
    Returns:
        True if message was sent successfully, False otherwise
    """
    try:
        logger.info("Sending test message to Telegram")
        notifier = TelegramNotifier()
        
        test_message = (
            "*Job Scraper System Test*\n\n"
            "✅ This is a test message from the job scraper system.\n"
            f"🕒 System time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"🔍 Search terms: {len(SEARCH_TERMS)} terms configured\n"
            f"🌐 Sites: {', '.join(JOB_SITES)}\n"
            "📊 The job notification system is working correctly."
        )
        
        response = notifier.send_to_telegram(test_message)
        success = response.get("ok", False)
        
        if success:
            logger.info("Test message sent successfully")
        else:
            logger.error(f"Failed to send test message: {response.get('description', 'Unknown error')}")
        
        return success
    except Exception as e:
        logger.error(f"Error sending test message to Telegram: {e}")
        return False


if __name__ == "__main__":
    """Send new job listings from the CSV file to Telegram."""
    try:
        logger.info("Starting Telegram job notification process")
        
        jobs_file = SENT_JOBS_FILE.parent / "jobs.csv"
        if not jobs_file.exists():
            logger.error(f"Jobs file not found at {jobs_file}")
            exit(1)
            
        jobs_df = pd.read_csv(jobs_file)
        sent_count = send_jobs_to_telegram(jobs_df)
        
        logger.info(f"Job notification process completed. Sent {sent_count} new jobs.")
        
    except Exception as e:
        logger.error(f"Error in Telegram notification process: {e}")
        exit(1)