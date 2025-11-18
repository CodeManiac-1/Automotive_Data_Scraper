#!/usr/bin/env python3
"""
Simple runner script for the Sylvania fitment data scraper.
This script provides an easy way to run the scraper with different configurations.
"""

import sys
import argparse
from enhanced_sylvania_scraper import EnhancedSylvaniaFitmentScraper

def main():
    parser = argparse.ArgumentParser(description='Sylvania Fitment Data Scraper')
    parser.add_argument('--headless', action='store_true', default=True,
                        help='Run browser in headless mode (default: True)')
    parser.add_argument('--no-headless', action='store_false', dest='headless',
                        help='Run browser with GUI visible')
    parser.add_argument('--use-proxy', action='store_true', default=False,
                        help='Enable proxy rotation (requires proxy list)')
    parser.add_argument('--proxy-file', type=str,
                        help='File containing proxy list (one per line)')
    parser.add_argument('--output', type=str, default='sylvania_fitment_data.csv',
                        help='Output CSV filename (default: sylvania_fitment_data.csv)')
    parser.add_argument('--min-delay', type=float, default=3.0,
                        help='Minimum delay between requests in seconds (default: 3.0)')
    parser.add_argument('--max-delay', type=float, default=7.0,
                        help='Maximum delay between requests in seconds (default: 7.0)')
    
    args = parser.parse_args()
    
    # Load proxy list if specified
    proxy_list = []
    if args.proxy_file:
        try:
            with open(args.proxy_file, 'r') as f:
                proxy_list = [line.strip() for line in f if line.strip()]
            print(f"Loaded {len(proxy_list)} proxies from {args.proxy_file}")
        except FileNotFoundError:
            print(f"Error: Proxy file {args.proxy_file} not found")
            sys.exit(1)
    
    # Create and configure scraper
    scraper = EnhancedSylvaniaFitmentScraper(
        use_proxy=args.use_proxy,
        proxy_list=proxy_list,
        headless=args.headless
    )
    
    # Configure delays
    scraper.min_delay = args.min_delay
    scraper.max_delay = args.max_delay
    scraper.output_file = args.output
    
    print("Starting Sylvania fitment data scraper...")
    print(f"Headless mode: {args.headless}")
    print(f"Using proxies: {args.use_proxy}")
    print(f"Delays: {args.min_delay}-{args.max_delay} seconds")
    print(f"Output file: {args.output}")
    print("-" * 50)
    
    try:
        scraper.run()
        print("\nScraping completed successfully!")
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        print(f"\nError during scraping: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
