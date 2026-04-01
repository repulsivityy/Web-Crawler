import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import re
import argparse
import sys
import os

from urllib.parse import urljoin

def clean_html(html_content, base_url):
    """
    Cleans HTML content by removing tags that are typically not relevant
    for main content extraction, and converts relative URLs to absolute ones.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Convert relative URLs to absolute
    for a in soup.find_all('a', href=True):
        a['href'] = urljoin(base_url, a['href'])
    for img in soup.find_all('img', src=True):
        img['src'] = urljoin(base_url, img['src'])

    # List of tags to remove
    tags_to_remove = [
        'script', 'style', 'nav', 'footer', 'header', 'form', 'aside',
        'iframe', 'svg', 'noscript', 'canvas', 'video', 'audio', 'button'
    ]

    for tag in soup(tags_to_remove):
        tag.decompose()

    return str(soup)

def scrape_to_markdown(url, output_file=None, verify=True):
    """
    Scrapes a website, cleans the HTML, and converts it to Markdown.
    """
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        print(f"Scraping {url}...")
        response = requests.get(url, headers=headers, timeout=20, verify=verify)
        response.raise_for_status()
        
        # Clean HTML before conversion
        print("Cleaning HTML content...")
        cleaned_html = clean_html(response.text, url)
        
        # Convert to Markdown
        print("Converting to Markdown...")
        # heading_style="ATX" uses # for headers instead of underlining
        markdown_content = md(cleaned_html, heading_style="ATX", bullets="-")
        
        # Post-processing: clean up excessive newlines
        markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content).strip()

        # Generate filename if not provided
        if not output_file:
            # Extract domain and clean it for a filename
            match = re.search(r'https?://(?:www\.)?([^/]+)', url)
            if match:
                domain = match.group(1).replace('.', '_')
                output_file = f"{domain}_content.md"
            else:
                output_file = "scraped_content.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Successfully saved content to '{output_file}'.")
        return output_file

    except requests.exceptions.SSLError as e:
        if verify:
            print(f"SSL Certificate Verification Failed. Retrying with 'verify=False'...", file=sys.stderr)
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            return scrape_to_markdown(url, output_file, verify=False)
        else:
            print(f"Error fetching URL (SSL): {e}", file=sys.stderr)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description="Scrape a website and convert its content to Markdown for AI agents.")
    parser.add_argument("url", help="The full URL of the website to scrape.")
    parser.add_argument("-o", "--output", help="Optional output filename (default: domain_name.md).")
    parser.add_argument("-k", "--insecure", action="store_false", dest="verify", default=True, help="Allow insecure connections (skip SSL verification).")
    
    args = parser.parse_args()
    
    scrape_to_markdown(args.url, args.output, verify=args.verify)

if __name__ == "__main__":
    main()
