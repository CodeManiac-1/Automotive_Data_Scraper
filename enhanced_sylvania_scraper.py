import requests
import time
import csv
import json
import random
import os
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
# import pandas as pd  # Comment out to avoid dependency issues
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedSylvaniaFitmentScraper:
    def __init__(self, use_proxy=False, proxy_list=None, headless=True):
        self.base_url = "https://www.sylvania-automotive.com/"
        self.ua = UserAgent()
        self.driver = None
        self.fitment_data = []
        self.use_proxy = use_proxy
        self.proxy_list = proxy_list or []
        self.headless = headless
        
        # Rate limiting settings
        self.min_delay = 3  # Increased minimum delay
        self.max_delay = 7  # Increased maximum delay
        self.retry_attempts = 3
        
        # Target years
        self.target_years = list(range(2018, 2026))  # 2018 to 2025
        
        # Progress tracking
        self.progress_file = "scraping_progress.json"
        self.output_file = "sylvania_fitment_data.csv"
        
    def load_progress(self):
        """Load previous scraping progress if exists"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
                    self.fitment_data = progress.get('fitment_data', [])
                    logger.info(f"Loaded {len(self.fitment_data)} records from previous session")
                    return progress.get('last_processed', {})
            except Exception as e:
                logger.error(f"Error loading progress: {e}")
        return {}
        
    def save_progress(self, last_processed=None):
        """Save current progress"""
        try:
            progress = {
                'fitment_data': self.fitment_data,
                'last_processed': last_processed or {},
                'timestamp': time.time()
            }
            with open(self.progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
                
            # Also save CSV as backup
            self.save_to_csv()
        except Exception as e:
            logger.error(f"Error saving progress: {e}")
        
    def setup_selenium_driver(self):
        """Set up Selenium WebDriver with proper options and optional proxy"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
            
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'--user-agent={self.ua.random}')
        
        # Additional options to avoid detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')  # Speed up loading
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add proxy if specified
        if self.use_proxy and self.proxy_list:
            proxy = random.choice(self.proxy_list)
            chrome_options.add_argument(f'--proxy-server={proxy}')
            logger.info(f"Using proxy: {proxy}")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set page load timeout
            self.driver.set_page_load_timeout(30)
            
            return True
        except Exception as e:
            logger.error(f"Error setting up driver: {e}")
            return False
            
    def wait_for_options_to_load(self, select_element, min_options=2, timeout=15):
        """Wait for select element to be populated with options"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(lambda driver: len(select_element.find_elements(By.TAG_NAME, "option")) >= min_options)
            return True
        except TimeoutException:
            logger.warning(f"Options didn't load within {timeout} seconds")
            return False
            
    def random_delay(self, extra_delay=0):
        """Add random delay to avoid detection"""
        delay = random.uniform(self.min_delay, self.max_delay) + extra_delay
        time.sleep(delay)
        
    def get_select_options(self, select_element):
        """Extract all options from a select element"""
        options = []
        try:
            select_obj = Select(select_element)
            for option in select_obj.options:
                value = option.get_attribute('value')
                text = option.text.strip()
                if value and value != "" and text != "Please Select":
                    options.append({'value': value, 'text': text})
        except Exception as e:
            logger.error(f"Error getting select options: {e}")
        return options
        
    def select_option_by_value(self, select_element, value):
        """Select an option by its value with retry logic"""
        for attempt in range(self.retry_attempts):
            try:
                select_obj = Select(select_element)
                select_obj.select_by_value(value)
                return True
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed to select option {value}: {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(2)
        return False
        
    def refresh_page_and_navigate_to_form(self):
        """Refresh page and navigate back to the form"""
        try:
            self.driver.refresh()
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.NAME, "bulbFinderYear")))
            return True
        except Exception as e:
            logger.error(f"Error refreshing page: {e}")
            return False
            
    def scrape_fitment_data(self):
        """Main method to scrape fitment data with resume capability"""
        last_processed = self.load_progress()
        
        try:
            logger.info("Setting up Selenium driver...")
            if not self.setup_selenium_driver():
                logger.error("Failed to setup driver")
                return
            
            logger.info("Loading Sylvania automotive page...")
            self.driver.get(self.base_url)
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.NAME, "bulbFinderYear")))
            
            logger.info("Page loaded successfully")
            
            # Get year select element
            year_select = self.driver.find_element(By.NAME, "bulbFinderYear")
            year_options = self.get_select_options(year_select)
            
            # Filter for target years only
            target_year_options = [opt for opt in year_options if opt['text'].isdigit() and int(opt['text']) in self.target_years]
            
            logger.info(f"Found {len(target_year_options)} target years to scrape")
            
            # Resume from last processed if available
            start_year_idx = 0
            if last_processed.get('year'):
                for i, year_opt in enumerate(target_year_options):
                    if year_opt['text'] == last_processed['year']:
                        start_year_idx = i
                        break
                        
            for year_idx, year_option in enumerate(target_year_options[start_year_idx:], start_year_idx):
                year_text = year_option['text']
                year_value = year_option['value']
                
                logger.info(f"Processing year: {year_text} ({year_idx + 1}/{len(target_year_options)})")
                
                # Select year
                if not self.select_option_by_value(year_select, year_value):
                    logger.error(f"Failed to select year {year_text}")
                    continue
                    
                self.random_delay()
                
                # Wait for make options to load
                try:
                    make_select = self.driver.find_element(By.NAME, "bulbFinderMake")
                except NoSuchElementException:
                    logger.error("Make select element not found")
                    continue
                    
                if not self.wait_for_options_to_load(make_select):
                    logger.warning(f"Make options didn't load for year {year_text}")
                    continue
                    
                make_options = self.get_select_options(make_select)
                logger.info(f"Found {len(make_options)} makes for year {year_text}")
                
                # Resume from last processed make if same year
                start_make_idx = 0
                if last_processed.get('year') == year_text and last_processed.get('make'):
                    for i, make_opt in enumerate(make_options):
                        if make_opt['text'] == last_processed['make']:
                            start_make_idx = i
                            break
                
                for make_idx, make_option in enumerate(make_options[start_make_idx:], start_make_idx):
                    make_text = make_option['text']
                    make_value = make_option['value']
                    
                    logger.info(f"  Processing make: {make_text} ({make_idx + 1}/{len(make_options)})")
                    
                    # Select make
                    if not self.select_option_by_value(make_select, make_value):
                        logger.error(f"Failed to select make {make_text}")
                        continue
                        
                    self.random_delay()
                    
                    # Wait for model options to load
                    try:
                        model_select = self.driver.find_element(By.NAME, "bulbFinderModel")
                    except NoSuchElementException:
                        logger.error("Model select element not found")
                        continue
                        
                    if not self.wait_for_options_to_load(model_select):
                        logger.warning(f"Model options didn't load for {year_text} {make_text}")
                        continue
                        
                    model_options = self.get_select_options(model_select)
                    logger.info(f"    Found {len(model_options)} models for {year_text} {make_text}")
                    
                    for model_idx, model_option in enumerate(model_options):
                        model_text = model_option['text']
                        model_value = model_option['value']
                        
                        logger.info(f"    Processing model: {model_text} ({model_idx + 1}/{len(model_options)})")
                        
                        # Select model
                        if not self.select_option_by_value(model_select, model_value):
                            logger.error(f"Failed to select model {model_text}")
                            continue
                            
                        self.random_delay()
                        
                        # Wait for bulb position options to load
                        try:
                            position_select = self.driver.find_element(By.NAME, "bulbFinderPositions")
                        except NoSuchElementException:
                            logger.error("Position select element not found")
                            continue
                            
                        if not self.wait_for_options_to_load(position_select):
                            logger.warning(f"Position options didn't load for {year_text} {make_text} {model_text}")
                            continue
                            
                        position_options = self.get_select_options(position_select)
                        logger.info(f"      Found {len(position_options)} positions for {year_text} {make_text} {model_text}")
                        
                        for position_option in position_options:
                            position_text = position_option['text']
                            position_value = position_option['value']
                            
                            # Store the fitment data
                            fitment_record = {
                                'year': year_text,
                                'make': make_text,
                                'model': model_text,
                                'bulb_position': position_text,
                                'year_value': year_value,
                                'make_value': make_value,
                                'model_value': model_value,
                                'position_value': position_value
                            }
                            
                            self.fitment_data.append(fitment_record)
                            logger.info(f"      Added: {year_text} {make_text} {model_text} - {position_text}")
                        
                        # Save progress after each model
                        current_progress = {
                            'year': year_text,
                            'make': make_text,
                            'model': model_text
                        }
                        self.save_progress(current_progress)
                        
                        # Add extra delay between models
                        self.random_delay(1)
                    
                    # Refresh page and re-navigate for next make
                    if make_idx < len(make_options) - 1:  # Don't refresh on last make
                        if not self.refresh_page_and_navigate_to_form():
                            logger.error("Failed to refresh page")
                            break
                            
                        # Re-select year
                        year_select = self.driver.find_element(By.NAME, "bulbFinderYear")
                        if not self.select_option_by_value(year_select, year_value):
                            break
                        self.random_delay()
                        
                        make_select = self.driver.find_element(By.NAME, "bulbFinderMake")
                        if not self.wait_for_options_to_load(make_select):
                            break
                
                logger.info(f"Completed year {year_text}")
                
        except KeyboardInterrupt:
            logger.info("Scraping interrupted by user")
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                
    def save_to_csv(self, filename=None):
        """Save the scraped data to CSV file"""
        if not self.fitment_data:
            logger.warning("No data to save")
            return
            
        filename = filename or self.output_file
        try:
            # Remove duplicates manually
            unique_data = []
            seen = set()
            for record in self.fitment_data:
                record_tuple = tuple(sorted(record.items()))
                if record_tuple not in seen:
                    seen.add(record_tuple)
                    unique_data.append(record)
            
            # Write to CSV manually
            if unique_data:
                fieldnames = unique_data[0].keys()
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(unique_data)
                logger.info(f"Saved {len(unique_data)} unique records to {filename}")
            else:
                logger.warning("No unique data to save")
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
            
    def cleanup_progress(self):
        """Clean up progress file after successful completion"""
        try:
            if os.path.exists(self.progress_file):
                os.remove(self.progress_file)
                logger.info("Cleaned up progress file")
        except Exception as e:
            logger.error(f"Error cleaning up progress file: {e}")
            
    def run(self):
        """Run the complete scraping process"""
        logger.info("Starting Enhanced Sylvania fitment data scraping...")
        start_time = time.time()
        
        try:
            self.scrape_fitment_data()
            self.save_to_csv()
            self.cleanup_progress()
        except Exception as e:
            logger.error(f"Error in main run: {e}")
        
        end_time = time.time()
        logger.info(f"Scraping completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Total records collected: {len(self.fitment_data)}")

if __name__ == "__main__":
    # Example proxy list (you can add your own proxies here)
    proxy_list = [
        # "http://proxy1:port",
        # "http://proxy2:port",
    ]
    
    scraper = EnhancedSylvaniaFitmentScraper(
        use_proxy=False,  # Set to True if you want to use proxies
        proxy_list=proxy_list,
        headless=True  # Set to False if you want to see the browser
    )
    scraper.run()
