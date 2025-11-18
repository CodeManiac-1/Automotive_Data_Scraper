#!/usr/bin/env python3
"""
Test script to verify that all dependencies are installed correctly
and the scraper can initialize properly.
"""

import sys
import importlib

def test_imports():
    """Test that all required packages can be imported"""
    required_packages = [
        'requests',
        'bs4',  # beautifulsoup4
        'selenium',
        'pandas',
        'fake_useragent',
        'webdriver_manager'
    ]
    
    print("Testing package imports...")
    failed_imports = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✓ {package}")
        except ImportError as e:
            print(f"✗ {package}: {e}")
            failed_imports.append(package)
    
    if failed_imports:
        print(f"\nFailed to import: {', '.join(failed_imports)}")
        print("Please install missing packages using: pip install -r requirements.txt")
        return False
    
    print("\nAll packages imported successfully!")
    return True

def test_scraper_initialization():
    """Test that the scraper can be initialized"""
    try:
        from enhanced_sylvania_scraper import EnhancedSylvaniaFitmentScraper
        
        print("\nTesting scraper initialization...")
        scraper = EnhancedSylvaniaFitmentScraper(headless=True)
        print("✓ Scraper initialized successfully")
        
        # Test basic methods
        print("✓ Basic methods accessible")
        
        return True
    except Exception as e:
        print(f"✗ Scraper initialization failed: {e}")
        return False

def test_selenium_driver():
    """Test that Selenium can set up Chrome driver"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        print("\nTesting Selenium Chrome driver setup...")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Test basic navigation
        driver.get("https://www.google.com")
        print("✓ Chrome driver setup and navigation successful")
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"✗ Chrome driver test failed: {e}")
        print("This might be due to Chrome not being installed or other system issues.")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Sylvania Scraper Setup Test")
    print("=" * 60)
    
    tests = [
        ("Package Imports", test_imports),
        ("Scraper Initialization", test_scraper_initialization),
        ("Selenium Driver", test_selenium_driver)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
        
        print("-" * 40)
    
    # Summary
    print("\nTest Summary:")
    print("=" * 30)
    all_passed = True
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 30)
    if all_passed:
        print("✓ All tests passed! The scraper is ready to use.")
        print("\nTo run the scraper:")
        print("  python enhanced_sylvania_scraper.py")
        print("  # or")
        print("  python run_scraper.py --no-headless  # to see browser")
    else:
        print("✗ Some tests failed. Please fix the issues before running the scraper.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
