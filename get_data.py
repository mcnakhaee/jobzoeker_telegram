"""
Job data collection and processing script.

This script scrapes job postings from multiple job sites based on search terms,
processes the results, and saves the filtered data to CSV files.
"""

import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import langid
import pandas as pd
from jobspy import scrape_jobs
from tqdm import tqdm
import os 
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
# Import Telegram notification function
try:
    from send_to_telegram import send_jobs_to_telegram
    TELEGRAM_ENABLED = True
except ImportError:
    TELEGRAM_ENABLED = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Configuration
SEARCH_TERMS = [
    #'r', 'ggplot', 'data analyst', 'analytics engineer',
    #'data scientist', 'pyspark', 'data visualization', 'data journalist',
    'ai engineer'#, 'Big Data', 'data pipeline', 'R Shiny', 
    #'R Developer',
      'weaviate', 'rag','data visualization','generative ai','azure ai search'
      'genai','ggplot','llm','python'
]

JOB_SITES = ["indeed", "glassdoor", "linkedin"]
LOCATION = "Netherlands"
RESULTS_PER_SEARCH = 40
MAX_AGE_DAYS = 7
EXCLUDED_TERMS = ['PhD', 'Manager', 'Intern']
OUTPUT_DIR = Path(".")
RETRY_ATTEMPTS = 3
REQUEST_DELAY = 5  # seconds between requests
SEND_TELEGRAM_NOTIFICATIONS = True  # Enable/disable Telegram notifications


def detect_language(text: str) -> str:
    """
    Detect the language of a given text.

    Args:
        text: The text to analyze

    Returns:
        The detected language code (e.g., 'en', 'nl')
    """
    try:
        if not isinstance(text, str) or not text.strip():
            return 'unknown'
        lang, _ = langid.classify(text)
        return lang
    except Exception as e:
        logger.warning(f"Language detection failed: {e}")
        return 'unknown'


def load_existing_data(file_path: Path) -> pd.DataFrame:
    """
    Load existing job data from CSV file if it exists.

    Args:
        file_path: Path to the CSV file

    Returns:
        DataFrame containing existing job data or an empty DataFrame
    """
    try:
        if file_path.exists():
            return pd.read_csv(file_path)
        else:
            logger.info(f"File {file_path} not found. Starting with empty dataset.")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return pd.DataFrame()


def scrape_job_data(
    search_term: str, 
    site: str, 
    location: str = LOCATION,
    results_wanted: int = RESULTS_PER_SEARCH,
    hours_old: int = MAX_AGE_DAYS * 24
) -> pd.DataFrame:
    """
    Scrape job listings from a specific site for a search term.

    Args:
        search_term: Term to search for
        site: Job site to scrape ("indeed", "glassdoor", or "linkedin")
        location: Location to search in
        results_wanted: Maximum number of results to fetch
        hours_old: Maximum age of job postings in hours

    Returns:
        DataFrame containing scraped job data
    """
    for attempt in range(RETRY_ATTEMPTS):
        try:
            logger.info(f"Scraping {site} for '{search_term}' in {location}")
            
            fetch_description = site == "linkedin"  # Only needed for LinkedIn
            
            jobs = scrape_jobs(
                site_name=site,
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                hours_old=hours_old,
                linkedin_fetch_description=fetch_description,
                country_indeed=location if site in ["indeed", "glassdoor"] else None
            )
            
            if jobs.empty:
                logger.warning(f"No results found for '{search_term}' on {site}")
                return pd.DataFrame()
                
            jobs['search_term'] = search_term
            jobs['source'] = site
            return jobs
            
        except Exception as e:
            logger.error(f"Error scraping {site} for '{search_term}': {e}")
            if attempt < RETRY_ATTEMPTS - 1:
                wait_time = REQUEST_DELAY * (attempt + 1)
                logger.info(f"Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{RETRY_ATTEMPTS})")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to scrape {site} for '{search_term}' after {RETRY_ATTEMPTS} attempts")
                return pd.DataFrame()
    
    return pd.DataFrame()


def filter_jobs(df: pd.DataFrame, min_date: datetime) -> pd.DataFrame:
    """
    Filter job listings based on language, title keywords, and date.

    Args:
        df: DataFrame containing job data
        min_date: Minimum date to include

    Returns:
        Filtered DataFrame
    """
    if df.empty:
        return df

    # Detect language in job descriptions
    logger.info("Detecting languages in job descriptions")
    df['lang'] = df['description'].apply(detect_language)
    
    # Filter by language (English only)
    filtered = df[df['lang'] == 'en'].copy()
    
    # Filter out unwanted job types
    for term in EXCLUDED_TERMS:
        filtered = filtered[~filtered['title'].str.contains(term, case=False, na=False)]
    
    # Convert date column to datetime
    filtered['date_posted'] = pd.to_datetime(filtered['date_posted'], errors='coerce')
    
    # Remove entries with invalid dates
    filtered = filtered.dropna(subset=['date_posted'])
    
    # Keep only recent jobs
    filtered = filtered[filtered['date_posted'] >= min_date]
    
    # Remove duplicates
    filtered = filtered.drop_duplicates(subset=['title', 'company'])
    
    logger.info(f"Filtered from {len(df)} to {len(filtered)} jobs")
    return filtered


def collect_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Collect job data from multiple sources and filter the results.

    Returns:
        Tuple containing (filtered jobs DataFrame, all jobs DataFrame)
    """
    # Load existing data
    jobs_file = OUTPUT_DIR / "jobs.csv"
    merged_df = load_existing_data(jobs_file)
    
    # Calculate date thresholds
    today = datetime.today()
    first_day_last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    
    # Create progress bar
    total_searches = len(SEARCH_TERMS) * len(JOB_SITES)
    pbar = tqdm(total=total_searches, desc="Scraping jobs")
    
    # Scrape jobs for each search term and site
    all_scraped_jobs = []
    
    for search_term in SEARCH_TERMS:
        for site in JOB_SITES:
            jobs = scrape_job_data(search_term, site)
            if not jobs.empty:
                all_scraped_jobs.append(jobs)
            time.sleep(REQUEST_DELAY)
            pbar.update(1)
    
    pbar.close()
    
    # Combine all scraped jobs
    if all_scraped_jobs:
        scraped_df = pd.concat(all_scraped_jobs, ignore_index=True)
        
        # Merge with existing data
        if not merged_df.empty:
            combined_df = pd.concat([merged_df, scraped_df], ignore_index=True)
        else:
            combined_df = scraped_df
    else:
        logger.warning("No new jobs were scraped")
        combined_df = merged_df
    
    # Process and filter the data
    if not combined_df.empty:
        # Remove exact duplicates
        all_jobs = combined_df.drop_duplicates(subset=['title', 'company', 'description'])
        
        # Filter jobs
        filtered_jobs = filter_jobs(all_jobs, min_date=first_day_last_month)
        
        return filtered_jobs, all_jobs
    else:
        logger.warning("No jobs data available")
        return pd.DataFrame(), pd.DataFrame()


def save_data(filtered_jobs: pd.DataFrame, all_jobs: pd.DataFrame) -> None:
    """
    Save job data to CSV files.

    Args:
        filtered_jobs: DataFrame of filtered job listings
        all_jobs: DataFrame of all job listings
    """
    jobs_file = OUTPUT_DIR / "jobs.csv"
    all_jobs_file = OUTPUT_DIR / "all_jobs.csv"
    
    try:
        if not filtered_jobs.empty:
            filtered_jobs.to_csv(jobs_file, index=False)
            logger.info(f"Saved {len(filtered_jobs)} filtered jobs to {jobs_file}")
        
        if not all_jobs.empty:
            all_jobs.to_csv(all_jobs_file, index=False)
            logger.info(f"Saved {len(all_jobs)} total jobs to {all_jobs_file}")
            
    except Exception as e:
        logger.error(f"Error saving data: {e}")


def send_telegram_notifications(filtered_jobs: pd.DataFrame) -> None:
    """
    Send notifications for new jobs to Telegram.

    Args:
        filtered_jobs: DataFrame of filtered job listings to notify about
    """
    if not TELEGRAM_ENABLED:
        logger.warning("Telegram notifications are enabled but the send_to_telegram module couldn't be imported")
        return
        
    if filtered_jobs.empty:
        logger.info("No jobs to send notifications for")
        return
        
    try:
        logger.info("Sending job notifications to Telegram")
        sent_count = send_jobs_to_telegram(filtered_jobs)
        logger.info(f"Sent {sent_count} job notifications to Telegram")
    except Exception as e:
        logger.error(f"Error sending Telegram notifications: {e}")


def send_telegram_test_message() -> bool:
    """
    Send a test message to Telegram to verify the connection.
    
    Returns:
        True if message was sent successfully, False otherwise
    """
    if not TELEGRAM_ENABLED:
        logger.warning("Telegram notifications are disabled or couldn't be imported")
        return False
    
    try:
        logger.info("Sending test message to Telegram")
        from send_to_telegram import send_to_telegram
        
        test_message = (
            "*Job Scraper System Test*\n\n"
            "✅ This is a test message from the job scraper system.\n"
            f"🕒 System time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"🔍 Search terms: {len(SEARCH_TERMS)} terms configured\n"
            f"🌐 Sites: {', '.join(JOB_SITES)}\n"
            "📊 The job notification system is working correctly."
        )
        
        response = send_to_telegram(test_message)
        success = response.get("ok", False)
        
        if success:
            logger.info("Test message sent successfully")
        else:
            logger.error(f"Failed to send test message: {response.get('description', 'Unknown error')}")
        
        return success
    except Exception as e:
        logger.error(f"Error sending test message to Telegram: {e}")
        return False


def main() -> None:
    """Entry point of the script."""
    logger.info("Starting job data collection")
    
    try:
        # Send a test message to verify Telegram setup
        if SEND_TELEGRAM_NOTIFICATIONS and TELEGRAM_ENABLED:
            send_telegram_test_message()
        
        start_time = time.time()
        filtered_jobs, all_jobs = collect_data()
        save_data(filtered_jobs, all_jobs)
        
        # Send actual job notifications if enabled
        if SEND_TELEGRAM_NOTIFICATIONS and TELEGRAM_ENABLED:
            send_telegram_notifications(filtered_jobs)
        
        execution_time = time.time() - start_time
        logger.info(f"Job data collection completed in {execution_time:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True)


if __name__ == "__main__":
    main()