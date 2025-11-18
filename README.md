# Sylvania Automotive Fitment Data Scraper

This project scrapes fitment data from the Sylvania Automotive website (https://www.sylvania-automotive.com/) for vehicle years 2018-2025.

## Features

- **Dynamic Form Handling**: Properly handles the cascading dropdown menus (Year → Make → Model → Bulb Position)
- **Rate Limiting**: Implements delays and retries to avoid being blocked
- **Progress Tracking**: Saves progress and can resume from interruption
- **Proxy Support**: Optional proxy rotation to avoid IP blocking
- **Error Handling**: Robust error handling with retry mechanisms
- **CSV Output**: Exports data to CSV format

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. The script will automatically download and manage ChromeDriver using webdriver-manager.

## Usage

### Basic Usage

Run the basic scraper:
```bash
python sylvania_scraper.py
```

### Enhanced Version (Recommended)

Run the enhanced scraper with progress tracking:
```bash
python enhanced_sylvania_scraper.py
```

### Configuration Options

You can modify the Enhanced scraper with these options:

```python
scraper = EnhancedSylvaniaFitmentScraper(
    use_proxy=False,  # Set to True to use proxy rotation
    proxy_list=[],    # Add your proxy servers here
    headless=True     # Set to False to see browser window
)
```

## Output

The scraper generates a CSV file `sylvania_fitment_data.csv` with the following columns:

- `year`: Vehicle year (2018-2025)
- `make`: Vehicle manufacturer
- `model`: Vehicle model
- `bulb_position`: Bulb position/type
- `year_value`: Form value for year
- `make_value`: Form value for make
- `model_value`: Form value for model
- `position_value`: Form value for position

## Features Explained

### Rate Limiting
- Random delays between 3-7 seconds between requests
- Additional delays between models to be respectful to the server
- Configurable retry attempts for failed operations

### Progress Tracking
- Saves progress to `scraping_progress.json`
- Can resume from the last processed vehicle if interrupted
- Automatically cleans up progress file on successful completion

### Error Handling
- Handles timeouts when waiting for dynamic content to load
- Retries failed operations up to 3 times
- Graceful handling of missing elements or failed page loads

### Anti-Detection Measures
- Random user agents
- Disabled automation indicators
- Optional proxy support
- Realistic delays between actions

## Troubleshooting

### Common Issues

1. **ChromeDriver Issues**: The script uses webdriver-manager to automatically download ChromeDriver, but you may need to update Chrome browser.

2. **Timeout Errors**: If you're getting timeout errors, try increasing the delays:
   ```python
   scraper.min_delay = 5
   scraper.max_delay = 10
   ```

3. **IP Blocking**: If you get blocked, wait a while and consider using proxies:
   ```python
   proxy_list = ["http://proxy1:port", "http://proxy2:port"]
   scraper = EnhancedSylvaniaFitmentScraper(use_proxy=True, proxy_list=proxy_list)
   ```

4. **Memory Issues**: For large datasets, the scraper saves progress periodically to avoid data loss.

### Resume Interrupted Scraping

If the scraper is interrupted, simply run it again. It will automatically resume from where it left off using the progress file.

## Notes

- The scraper is designed to be respectful to the target website with appropriate delays
- Only scrapes data for years 2018-2025 as requested
- Handles the dynamic nature of the form where options change based on previous selections
- The website may have anti-bot measures, so the scraper includes various techniques to avoid detection

## Legal Notice

This scraper is for educational purposes. Make sure you comply with the website's terms of service and robots.txt file. Use responsibly and don't overload the server with requests.
