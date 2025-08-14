#!/usr/bin/env python3
"""
Scholarship Discovery Scheduler
Automated scheduler for running scholarship discovery at regular intervals
"""
import os
import sys
import time
import logging
import schedule
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Ensure the script's own directory is in sys.path to find run_agent
# run_agent.py will handle adding its 'src' directory to the path for its own imports
sys.path.insert(0, str(Path(__file__).parent))

from run_agent import setup_environment, run_discovery, create_default_search_criteria

# Call setup_environment() early, as it loads .env files needed by other modules
# and potentially by run_agent upon its import if it had top-level code relying on env vars.
setup_environment()

def setup_logging():
    """Setup logging for the scheduler."""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"scheduler_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def create_search_variations():
    """Create different search criteria for variety."""
    current_year = datetime.now().year
    variations = [
        f"new merit-based scholarships for college students {current_year}",
        f"need-based financial aid and grants {current_year}",
        f"STEM scholarships and fellowships for students {current_year}",
        f"diversity and minority scholarships {current_year}",
        f"graduate school scholarships and funding {current_year}",
        f"undergraduate scholarships and awards {current_year}",
        f"local and regional scholarship opportunities {current_year}",
    ]
    
    # Rotate based on day of week
    day_index = datetime.now().weekday()
    return variations[day_index % len(variations)]


async def scheduled_discovery_job():
    """Main job function for scheduled discovery."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting scheduled scholarship discovery")
        
        # Create varied search criteria
        search_criteria = create_search_variations()
        logger.info(f"Using search criteria: {search_criteria}")
        
        # Create output file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"logs/scholarship_discovery_{timestamp}.json"
        
        # Run discovery
        result = await run_discovery(
            search_criteria=search_criteria,
            output_file=output_file,
            save_to_sheets=True
        )
        
        # Log results
        if result.get("success", False):
            logger.info(f"Discovery successful - Found: {result.get('scholarships_discovered', 0)}, Saved: {result.get('scholarships_saved', 0)}")
        else:
            logger.error(f"Discovery failed: {result.get('error', 'Unknown error')}")
        
    except Exception as e:
        logger.error(f"Scheduled job failed: {e}")


def run_job_sync():
    """Synchronous wrapper for the async job."""
    asyncio.run(scheduled_discovery_job())


def main():
    """Main scheduler function."""
    # Setup
    logger = setup_logging()
    
    # Validate environment
    if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_gemini_api_key_here":
        logger.error("GEMINI_API_KEY not properly configured")
        sys.exit(1)
    
    logger.info("Starting scholarship discovery scheduler")
    
    # Schedule jobs
    # Daily at 2:00 AM
    schedule.every().day.at("02:00").do(run_job_sync)
    
    # Optional: Additional runs for testing (uncomment if needed)
    # schedule.every().monday.at("10:00").do(run_job_sync)
    # schedule.every().wednesday.at("14:00").do(run_job_sync)
    # schedule.every().friday.at("16:00").do(run_job_sync)
    
    logger.info("Scheduler configured:")
    for job in schedule.get_jobs():
        logger.info(f"  - {job}")
    
    logger.info("Scheduler started. Press Ctrl+C to stop.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        sys.exit(1)


def run_now():
    """Run discovery immediately (for testing)."""
    logger = setup_logging()
    
    logger.info("Running immediate scholarship discovery")
    
    try:
        asyncio.run(scheduled_discovery_job())
    except Exception as e:
        logger.error(f"Immediate run failed: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scholarship discovery scheduler")
    parser.add_argument(
        "--now", 
        action="store_true", 
        help="Run discovery immediately instead of scheduling"
    )
    
    args = parser.parse_args()
    
    if args.now:
        run_now()
    else:
        main()
