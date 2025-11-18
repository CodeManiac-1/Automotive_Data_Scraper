import requests
import time
import csv
import json
import random
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SylvaniaFitmentScraper:
    def __init__(self):
        self.base_url = "https://www.sylvania-automotive.com/"
        self.ua = UserAgent()
        self.session = requests.Session()
        self.driver = None
        self.fitment_data = []
        
        # Rate limiting settings
        self.min_delay = 2  # Minimum delay between requests
        self.max_delay = 5  # Maximum delay between requests
        
        # Target years
        self.target_years = list(range(2018, 2026))  # 2018 to 2025
        
    def setup_selenium_driver(self):
        """Set up Selenium WebDriver with proper options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'--user-agent={self.ua.random}')
        
        # Additional options to avoid detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def wait_for_options_to_load(self, select_element, min_options=2, timeout=10):
        """Wait for select element to be populated with options"""
        wait = WebDriverWait(self.driver, timeout)
        try:
            wait.until(lambda driver: len(select_element.find_elements(By.TAG_NAME, "option")) >= min_options)
            return True
        except:
            logger.warning(f"Options didn't load within {timeout} seconds")
            return False
            
    def random_delay(self):
        """Add random delay to avoid detection"""
        delay = random.uniform(self.min_delay, self.max_delay)
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
        """Select an option by its value"""
        try:
            select_obj = Select(select_element)
            select_obj.select_by_value(value)
            return True
        except Exception as e:
            logger.error(f"Error selecting option {value}: {e}")
            return False
            
    def scrape_fitment_data(self):
        """Main method to scrape fitment data"""
        try:
            logger.info("Setting up Selenium driver...")
            self.setup_selenium_driver()
            
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
            
            for year_option in target_year_options:
                year_text = year_option['text']
                year_value = year_option['value']
                
                logger.info(f"Processing year: {year_text}")
                
                # Select year
                if not self.select_option_by_value(year_select, year_value):
                    continue
                    
                self.random_delay()
                
                # Wait for make options to load
                make_select = self.driver.find_element(By.NAME, "bulbFinderMake")
                if not self.wait_for_options_to_load(make_select):
                    logger.warning(f"Make options didn't load for year {year_text}")
                    continue
                    
                make_options = self.get_select_options(make_select)
                logger.info(f"Found {len(make_options)} makes for year {year_text}")
                
                for make_option in make_options:
                    make_text = make_option['text']
                    make_value = make_option['value']
                    
                    logger.info(f"  Processing make: {make_text}")
                    
                    # Select make
                    if not self.select_option_by_value(make_select, make_value):
                        continue
                        
                    self.random_delay()
                    
                    # Wait for model options to load
                    model_select = self.driver.find_element(By.NAME, "bulbFinderModel")
                    if not self.wait_for_options_to_load(model_select):
                        logger.warning(f"Model options didn't load for {year_text} {make_text}")
                        continue
                        
                    model_options = self.get_select_options(model_select)
                    logger.info(f"    Found {len(model_options)} models for {year_text} {make_text}")
                    
                    for model_option in model_options:
                        model_text = model_option['text']
                        model_value = model_option['value']
                        
                        logger.info(f"    Processing model: {model_text}")
                        
                        # Select model
                        if not self.select_option_by_value(model_select, model_value):
                            continue
                            
                        self.random_delay()
                        
                        # Wait for bulb position options to load
                        position_select = self.driver.find_element(By.NAME, "bulbFinderPositions")
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
                        
                        # Add extra delay between models to avoid being too aggressive
                        time.sleep(1)
                    
                    # Reset model and position selects for next make
                    self.driver.refresh()
                    wait.until(EC.presence_of_element_located((By.NAME, "bulbFinderYear")))
                    
                    # Re-select year and make
                    year_select = self.driver.find_element(By.NAME, "bulbFinderYear")
                    self.select_option_by_value(year_select, year_value)
                    self.random_delay()
                    
                    make_select = self.driver.find_element(By.NAME, "bulbFinderMake")
                    self.wait_for_options_to_load(make_select)
                    
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                
    def save_to_csv(self, filename="sylvania_fitment_data.csv"):
        """Save the scraped data to CSV file"""
        if not self.fitment_data:
            logger.warning("No data to save")
            return
            
        try:
            df = pd.DataFrame(self.fitment_data)
            df.to_csv(filename, index=False)
            logger.info(f"Saved {len(self.fitment_data)} records to {filename}")
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
            
    def run(self):
        """Run the complete scraping process"""
        logger.info("Starting Sylvania fitment data scraping...")
        start_time = time.time()
        
        self.scrape_fitment_data()
        self.save_to_csv()
        
        end_time = time.time()
        logger.info(f"Scraping completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Total records collected: {len(self.fitment_data)}")

if __name__ == "__main__":
    scraper = SylvaniaFitmentScraper()
    scraper.run()
