import requests
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time
import pandas as pd
import mysql.connector
from mysql.connector import Error
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import threading
import schedule
import logging
from dateutil import parser
import pytz
import re
from urllib.parse import urljoin, urlparse
import random

# Configure logging with proper encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('regulatory_updates_fetcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class NewsFetcher:
    def __init__(self, newsapi_keys, mysql_config=None, email_config=None):
        # Support multiple API keys (pass as list or single string)
        if isinstance(newsapi_keys, str):
            self.newsapi_keys = [newsapi_keys]
        else:
            self.newsapi_keys = newsapi_keys
        
        self.current_api_key_index = 0
        self.api_key_failures = {key: 0 for key in self.newsapi_keys}
        self.api_key_last_success = {key: datetime.now() for key in self.newsapi_keys}
        
        self.mysql_config = mysql_config
        
        # Email configuration - now uses passed config or raises error
        if email_config is None:
            raise ValueError("Email configuration must be provided when initializing NewsFetcher")
        self.email_config = email_config
        
        # Regular keywords (unlimited articles per run)
        self.keywords = [
            'Copyright', 'Patent', 'GST', 'Customs', 'Levy', 'FDI', 
            'SEBI', 'FEMA', 'IPR', 'Intellectual Property', 'Trademark', 
            'Tariff', 'Semiconductor', 'Press Note', 'Antitrust', 'DRHP', 
            'Anti-Dumping', 'Anti Dumping', 'Input Tax Credit', 'ITC', 'AI',
            "Regulations", "Regulatory", "Guidelines"
        ]
        
        # LIMITED KEYWORDS - Only 1 article per run (90 minutes cycle)
        self.limited_keywords = [
            'Tarrif'
        ]
        
        # Track limited keyword usage per run
        self.limited_keyword_usage = {}
        
        # Your custom sources (for web scraping) with enhanced selectors
        self.custom_sources = {
            'Economic Times Policy': {
                'url': "https://economictimes.indiatimes.com/news/economy/policy",
                'selectors': {
                    'article_container': ['div[data-nid]', 'div.story-box', 'div.eachStory'],
                    'title': ['h3', 'h2', 'h4', 'div.story-box h4', '.title'],
                    'link': ['a[href]'],
                    'date': ['time', 'span.publish-date', '.date', '[data-publish-date]']
                }
            },
            'MoneyControl': {
                'url': 'https://www.moneycontrol.com/news',
                'selectors': {
                    'article_container': ['li.clearfix', 'div.news_box', 'div.news-item'],
                    'title': ['h2', 'h3', 'a', '.news-title'],
                    'link': ['a[href]'],
                    'date': ['span.span_dt', 'time', '.date']
                }
            },
            'ZeeBiz Economy': {
                'url': "https://www.zeebiz.com/topics/economy",
                'selectors': {
                    'article_container': ['div.list-story', 'article', '.story-card'],
                    'title': ['h3', 'h2', '.story-title'],
                    'link': ['a[href]'],
                    'date': ['time', '.story-date', 'span.date']
                }
            },
            'Business Standard': {
                'url': "https://www.business-standard.com",
                'selectors': {
                    'article_container': ['div.listingstyle', 'div.cardlist', 'article', '.story-card'],
                    'title': ['h2', 'h3', '.headline', 'a.headline'],
                    'link': ['a[href]'],
                    'date': ['span.story-date', 'time', '.date']
                }
            },
            'Livemint': {
                'url': "https://www.livemint.com/",
                'selectors': {
                    'article_container': ['div.listView', 'div.story', 'article'],
                    'title': ['h3', 'h2', '.headline'],
                    'link': ['a[href]'],
                    'date': ['span.date', 'time', '.timestamp']
                }
            },
            'Indian Express': {
                'url': "https://indianexpress.com/section/business/#economy-and-policy",
                'selectors': {
                    'article_container': ['div.articles', 'article', '.snapper'],
                    'title': ['h3', 'h2', '.title'],
                    'link': ['a[href]'],
                    'date': ['span.date', 'time', '.posted-on']
                }
            },
            'NDTV Profit': {
                'url': "https://www.ndtvprofit.com/",
                'selectors': {
                    'article_container': ['div.story-card', 'article', '.news-item'],
                    'title': ['h3', 'h2', '.story-title'],
                    'link': ['a[href]'],
                    'date': ['time', '.story-date', '.timestamp']
                }
            },
            'CNBC TV18': {
                'url': "https://www.cnbctv18.com/economy/",
                'selectors': {
                    'article_container': ['div.jsx-', 'article', '.story-card'],
                    'title': ['h3', 'h2', '.story-title'],
                    'link': ['a[href]'],
                    'date': ['time', '.story-date']
                }
            },
            'The Hindu': {
                'url': "https://www.thehindubusinessline.com/",
                'selectors': {
                    'article_container': ['div.story-card', 'article', '.element'],
                    'title': ['h3', 'h2', '.story-title'],
                    'link': ['a[href]'],
                    'date': ['time', '.story-date', '.updated-time']
                }
            },
            'Financial Express': {
                'url': "https://www.financialexpress.com/",
                'selectors': {
                    'article_container': ['div.story-box', 'article', '.news-item'],
                    'title': ['h3', 'h2', '.story-title'],
                    'link': ['a[href]'],
                    'date': ['time', '.story-date']
                }
            }
        }
        
        # India timezone
        self.timezone = pytz.timezone('Asia/Kolkata')
        
        # Track last email sent times
        self.last_morning_email = None
        self.last_evening_email = None
        
        # Enhanced user agents for better scraping
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
        ]

    def get_current_api_key(self):
        """Get the current API key to use"""
        return self.newsapi_keys[self.current_api_key_index]

    def rotate_api_key(self):
        """Rotate to the next API key"""
        old_index = self.current_api_key_index
        self.current_api_key_index = (self.current_api_key_index + 1) % len(self.newsapi_keys)
        
        old_key_masked = self.newsapi_keys[old_index][:8] + "***"
        new_key_masked = self.newsapi_keys[self.current_api_key_index][:8] + "***"
        
        logging.warning(f"Rotating API key from {old_key_masked} to {new_key_masked}")
        return self.newsapi_keys[self.current_api_key_index]

    def handle_api_key_failure(self, api_key, error_code=None):
        """Handle API key failure and rotate if necessary"""
        self.api_key_failures[api_key] += 1
        
        # If rate limited (429) or too many failures, rotate immediately
        if error_code == 429 or self.api_key_failures[api_key] >= 3:
            if len(self.newsapi_keys) > 1:
                logging.warning(f"API key failed (code: {error_code}), rotating to next key")
                return self.rotate_api_key()
            else:
                logging.error("Only one API key available and it's rate limited. Waiting before retry...")
                time.sleep(60)  # Wait 1 minute before retry
        
        return api_key

    def mark_api_key_success(self, api_key):
        """Mark API key as successful"""
        self.api_key_failures[api_key] = 0
        self.api_key_last_success[api_key] = datetime.now()

    def reset_limited_keyword_usage(self):
        """Reset the limited keyword usage tracker for new run"""
        self.limited_keyword_usage = {}
        logging.info("Reset limited keyword usage tracker for new run")

    def can_use_limited_keyword(self, keyword):
        """Check if a limited keyword can still be used in this run"""
        if keyword not in self.limited_keywords:
            return True
        return self.limited_keyword_usage.get(keyword, 0) < 1

    def use_limited_keyword(self, keyword):
        """Mark a limited keyword as used in this run"""
        if keyword in self.limited_keywords:
            self.limited_keyword_usage[keyword] = self.limited_keyword_usage.get(keyword, 0) + 1
            logging.info(f"Limited keyword '{keyword}' used: {self.limited_keyword_usage[keyword]}/1")

    def normalize_heading(self, heading):
        """Normalize heading for duplicate detection"""
        if not heading:
            return ""
        
        # Convert to lowercase
        normalized = heading.lower()
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        # Remove common punctuation that doesn't change meaning
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Remove extra spaces again after punctuation removal
        normalized = ' '.join(normalized.split())
        
        return normalized.strip()

    def verify_table_exists(self):
        """Verify that the articles table exists"""
        connection = None
        try:
            connection = mysql.connector.connect(**self.mysql_config)
            cursor = connection.cursor()
            
            cursor.execute("SHOW TABLES LIKE 'articles'")
            result = cursor.fetchone()
            
            if result:
                logging.info("Articles table exists")
                return True
            else:
                logging.error("Articles table does not exist")
                return False
                
        except Error as e:
            logging.error(f"Error verifying table: {e}")
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def save_to_database(self, articles):
        """Save articles to MySQL database with detailed logging and duplicate heading detection"""
        if not articles:
            logging.info("No articles to save to database")
            return
        
        connection = None
        try:
            connection = mysql.connector.connect(**self.mysql_config)
            cursor = connection.cursor()
            
            insert_query = """
            INSERT INTO articles (article_heading, article_link, keyword, source, published_date, is_sent)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            inserted_count = 0
            skipped_duplicate_heading = 0
            error_count = 0
            
            for article in articles:
                try:
                    title = article.get('title', '')
                    url = article.get('url', '')
                    
                    if not title or not url:
                        logging.warning(f"Skipping article with missing title or URL: {article}")
                        error_count += 1
                        continue
                    
                    # Normalize the heading for comparison
                    normalized_title = self.normalize_heading(title)
                    
                    if not normalized_title:
                        logging.warning(f"Skipping article with empty normalized title: {title}")
                        error_count += 1
                        continue
                    
                    # Check if article with similar heading already exists
                    cursor.execute("""
                        SELECT article_heading, article_link 
                        FROM articles 
                        WHERE article_heading = %s
                    """, (title,))
                    
                    existing = cursor.fetchone()
                    
                    if existing:
                        skipped_duplicate_heading += 1
                        logging.debug(f"Duplicate heading found: '{title[:60]}...'")
                        logging.debug(f"  Existing: {existing[1][:80]}...")
                        logging.debug(f"  New:      {url[:80]}...")
                        continue
                    
                    # Insert the new article
                    cursor.execute(insert_query, (
                        title,
                        url,
                        article['keyword'],
                        article['source'],
                        article.get('published_date'),
                        False
                    ))
                    
                    inserted_count += 1
                    logging.info(f"✓ Inserted: {title[:60]}... from {article['source']}")
                        
                except Error as e:
                    error_count += 1
                    logging.error(f"✗ Error inserting article '{article.get('title', 'Unknown')[:50]}...': {e}")
                    logging.error(f"  URL: {article.get('url', 'Unknown')[:100]}")
                    continue
            
            connection.commit()
            
            # Comprehensive logging
            logging.info(f"=" * 70)
            logging.info(f"Database operation completed:")
            logging.info(f"  ✓ {inserted_count} new articles inserted")
            logging.info(f"  ⊘ {skipped_duplicate_heading} articles skipped (duplicate headings)")
            logging.info(f"  ✗ {error_count} errors encountered")
            logging.info(f"  = {len(articles)} total articles processed")
            logging.info(f"=" * 70)
            
        except Error as e:
            logging.error(f"Database connection error: {e}")
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def get_unsent_articles(self):
        """Get all articles with is_sent = FALSE"""
        connection = None
        try:
            connection = mysql.connector.connect(**self.mysql_config)
            cursor = connection.cursor(dictionary=True)
            
            query = """
            SELECT id, article_heading, article_link, keyword, source, published_date, is_sent, date_created, date_updated
            FROM articles 
            WHERE is_sent = FALSE
            ORDER BY published_date DESC, date_created DESC
            """
            
            cursor.execute(query)
            articles = cursor.fetchall()
            
            logging.info(f"Found {len(articles)} unsent articles")
            return articles
            
        except Error as e:
            logging.error(f"Error fetching unsent articles: {e}")
            return []
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def update_sent_status(self, article_ids, status=True):
        """Update is_sent status for given article IDs"""
        if not article_ids:
            return
        
        connection = None
        try:
            connection = mysql.connector.connect(**self.mysql_config)
            cursor = connection.cursor()
            
            placeholders = ','.join(['%s'] * len(article_ids))
            query = f"UPDATE articles SET is_sent = %s WHERE id IN ({placeholders})"
            
            cursor.execute(query, [status] + article_ids)
            connection.commit()
            
            logging.info(f"Updated is_sent status to {status} for {len(article_ids)} articles")
            
        except Error as e:
            logging.error(f"Error updating is_sent status: {e}")
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def create_html_table(self, articles):
        """Create HTML table for email"""
        if not articles:
            return "<p>No articles found.</p>"
        
        html = """
        <table style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif;">
            <thead>
                <tr style="background-color: #f2f2f2;">
                    <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">#</th>
                    <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Article Heading</th>
                    <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Source</th>
                    <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Keyword</th>
                    <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Published Date</th>
                    <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Link</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for i, article in enumerate(articles, 1):
            published_date = article.get('published_date')
            date_str = published_date.strftime('%Y-%m-%d %H:%M') if published_date else 'N/A'
            
            html += f"""
                <tr style="{'background-color: #f9f9f9;' if i % 2 == 0 else ''}">
                    <td style="border: 1px solid #ddd; padding: 8px;">{i}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{article['article_heading']}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{article['source']}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{article['keyword']}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{date_str}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">
                        <a href="{article['article_link']}" target="_blank" style="color: #0066cc;">Read Article</a>
                    </td>
                </tr>
            """
        
        html += "</tbody></table>"
        return html

    def send_email(self, articles, email_type="Regular"):
        """Send email with articles in tabular format with CC support"""
        if not articles:
            logging.info("No articles to send via email")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_config['sender_email']
            msg['To'] = self.email_config['recipient_email']
            
            cc_emails = []
            if 'cc_email' in self.email_config and self.email_config['cc_email']:
                cc_email = self.email_config['cc_email']
                if isinstance(cc_email, str):
                    cc_emails = [cc_email.strip()]
                elif isinstance(cc_email, list):
                    cc_emails = [email.strip() for email in cc_email if email.strip()]
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            msg['Subject'] = f"News Articles Report ({email_type}) - {len(articles)} Articles"
            
            html_table = self.create_html_table(articles)
            html_content = f"""
            <html>
                <head></head>
                <body>
                    <h2>News Articles Report ({email_type})</h2>
                    <p>Total articles: <strong>{len(articles)}</strong></p>
                    <p>Generated on: <strong>{datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S IST')}</strong></p>
                    <br>
                    {html_table}
                    <br>
                    <p style="font-size: 12px; color: #666;">
                        This is an automated email from the News Fetcher system.
                    </p>
                </body>
            </html>
            """
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['sender_email'], self.email_config['sender_password'])
            
            recipients = [self.email_config['recipient_email']] + cc_emails
            
            text = msg.as_string()
            server.sendmail(self.email_config['sender_email'], recipients, text)
            server.quit()
            
            logging.info(f"Email sent successfully to {self.email_config['recipient_email']}")
            if cc_emails:
                logging.info(f"CC sent to: {', '.join(cc_emails)}")
            return True
            
        except Exception as e:
            logging.error(f"Error sending email: {e}")
            return False

    def should_send_email(self, email_type):
        """Check if email should be sent based on time and last sent time"""
        now = datetime.now(self.timezone)
        current_date = now.date()
        
        if email_type == "morning":
            if not (10 <= now.hour < 12):
                return False
            if self.last_morning_email and self.last_morning_email.date() == current_date:
                return False
        elif email_type == "evening":
            if not (16 <= now.hour < 18):
                return False
            if self.last_evening_email and self.last_evening_email.date() == current_date:
                return False
        
        return True

    def send_scheduled_email(self, email_type):
        """Send scheduled email if conditions are met"""
        if not self.should_send_email(email_type):
            logging.info(f"Skipping {email_type} email - not the right time or already sent today")
            return
        
        unsent_articles = self.get_unsent_articles()
        
        if not unsent_articles:
            logging.info(f"No unsent articles for {email_type} email")
            return
        
        email_label = "Morning Report" if email_type == "morning" else "Evening Report"
        if self.send_email(unsent_articles, email_label):
            article_ids = [article['id'] for article in unsent_articles]
            self.update_sent_status(article_ids, True)
            logging.info(f"Marked {len(article_ids)} articles as sent after {email_type} email")
            
            if email_type == "morning":
                self.last_morning_email = datetime.now(self.timezone)
            else:
                self.last_evening_email = datetime.now(self.timezone)
        else:
            logging.error(f"Failed to send {email_type} email. Articles remain marked as unsent.")

    def parse_article_date(self, date_string, source_name):
        """Parse article date from various formats"""
        if not date_string:
            return None
        
        try:
            date_string = re.sub(r'[^\w\s:,-/]', '', str(date_string))
            parsed_date = parser.parse(date_string)
            
            if parsed_date.tzinfo is None:
                parsed_date = self.timezone.localize(parsed_date)
            
            return parsed_date.astimezone(pytz.UTC).replace(tzinfo=None)
            
        except Exception as e:
            logging.warning(f"Could not parse date '{date_string}' for {source_name}: {e}")
            return None

    def get_random_headers(self):
        """Get random headers for web scraping"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }

    def clean_title(self, title):
        """Clean article title"""
        if not title:
            return ""
        
        title = ' '.join(title.strip().split())
        
        unwanted_patterns = [
            r'\s*-\s*[^-]*$',
            r'^\s*\|\s*',
            r'\s*\|\s*$',
        ]
        
        for pattern in unwanted_patterns:
            title = re.sub(pattern, '', title)
        
        return title.strip()

    def extract_articles_with_selectors(self, soup, source_config, source_name, base_url):
        """Extract articles using multiple selector strategies"""
        articles = []
        selectors = source_config['selectors']
        
        # Try to find containers using provided selectors
        containers = []
        for container_selector in selectors['article_container']:
            found_containers = soup.select(container_selector)
            if found_containers:
                containers = found_containers
                logging.info(f"Found {len(containers)} containers using selector: {container_selector}")
                break
        
        # Fallback to generic selectors if no containers found
        if not containers:
            logging.warning(f"No containers found with provided selectors for {source_name}, trying fallback")
            containers = soup.find_all(['article', 'div'], class_=re.compile(r'(story|article|news|post)', re.I))
            if not containers:
                containers = soup.find_all('div', class_=re.compile(r'list|item|card', re.I))
            
            if containers:
                logging.info(f"Found {len(containers)} containers using fallback selectors")
        
        # Process each container
        for container in containers[:30]:  # Increased from 15 to 30
            try:
                title_elem = None
                link_elem = None
                date_elem = None
                
                # Try to find title
                for title_selector in selectors['title']:
                    title_elem = container.select_one(title_selector)
                    if title_elem and title_elem.get_text(strip=True):
                        break
                
                # If no title found with selectors, try finding any heading or link text
                if not title_elem or not title_elem.get_text(strip=True):
                    title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'a'])
                
                # Try to find link
                for link_selector in selectors['link']:
                    link_elem = container.select_one(link_selector)
                    if link_elem and link_elem.get('href'):
                        break
                
                # If no link found, search for any link in container
                if not link_elem or not link_elem.get('href'):
                    link_elem = container.find('a', href=True)
                
                # Try to find date
                for date_selector in selectors['date']:
                    date_elem = container.select_one(date_selector)
                    if date_elem:
                        break
                
                # Extract and validate data
                if title_elem and link_elem:
                    title = self.clean_title(title_elem.get_text())
                    href = link_elem.get('href', '')
                    
                    # Skip if title is too short or empty
                    if not title or len(title) < 10:
                        logging.debug(f"Skipping article with short title: {title}")
                        continue
                    
                    # Skip if no valid href
                    if not href or href == '#' or href.startswith('javascript:'):
                        logging.debug(f"Skipping article with invalid href: {href}")
                        continue
                    
                    # Normalize URL
                    if href.startswith('/'):
                        href = urljoin(base_url, href)
                    elif not href.startswith('http'):
                        href = urljoin(base_url, href)
                    
                    # Check if URL is valid
                    if not href.startswith('http'):
                        logging.debug(f"Skipping article with malformed URL: {href}")
                        continue
                    
                    # Check against all keywords
                    all_keywords = self.keywords + self.limited_keywords
                    matching_keyword = None
                    
                    for keyword in all_keywords:
                        pattern = r"\b" + re.escape(keyword) + r"\b"
                        if re.search(pattern, title, re.IGNORECASE):
                            if keyword in self.limited_keywords:
                                if not self.can_use_limited_keyword(keyword):
                                    logging.info(f"Skipping article for limited keyword '{keyword}' - already used")
                                    continue
                                else:
                                    self.use_limited_keyword(keyword)
                            
                            matching_keyword = keyword
                            break
                    
                    if matching_keyword:
                        published_date = None
                        if date_elem:
                            date_text = date_elem.get('datetime') or date_elem.get_text(strip=True)
                            published_date = self.parse_article_date(date_text, source_name)
                        
                        article_data = {
                            'title': title,
                            'url': href,
                            'keyword': matching_keyword,
                            'source': source_name,
                            'published_date': published_date
                        }
                        
                        articles.append(article_data)
                        logging.debug(f"Extracted: {title[:50]}... with keyword '{matching_keyword}'")
                
            except Exception as e:
                logging.warning(f"Error processing container in {source_name}: {e}")
                continue
        
        return articles

    def scrape_website_enhanced(self, source_name, source_config, max_articles=20):  # Increased from 10 to 20
        """Enhanced web scraping with multiple strategies and better debugging"""
        articles = []
        url = source_config['url']
        
        try:
            headers = self.get_random_headers()
            session = requests.Session()
            session.headers.update(headers)
            
            logging.info(f"Fetching {source_name} from {url}")
            response = session.get(url, timeout=15)
            response.raise_for_status()
            
            logging.info(f"Response status: {response.status_code}, Content length: {len(response.content)} bytes")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try primary extraction method
            articles = self.extract_articles_with_selectors(soup, source_config, source_name, url)
            logging.info(f"Primary extraction found {len(articles)} articles from {source_name}")
            
            # If primary method found nothing, try generic approach
            if not articles:
                logging.info(f"Trying generic approach for {source_name}")
                articles = self.generic_article_extraction(soup, source_name, url)
                logging.info(f"Generic extraction found {len(articles)} articles from {source_name}")
            
            # If still nothing, try RSS feed
            if not articles:
                logging.info(f"Trying RSS feed detection for {source_name}")
                articles = self.try_rss_feed(soup, source_name, url)
                logging.info(f"RSS feed found {len(articles)} articles from {source_name}")
            
            # Final diagnostic if no articles found
            if not articles:
                logging.warning(f"No articles found from {source_name} after all attempts")
                # Count potential containers for debugging
                potential_containers = soup.find_all(['article', 'div', 'li'])
                logging.info(f"Found {len(potential_containers)} potential containers in HTML")
                
                # Look for any links
                all_links = soup.find_all('a', href=True)
                logging.info(f"Found {len(all_links)} total links in page")
                
                # Check if any have keyword matches
                keyword_matches = 0
                for link in all_links[:50]:
                    title = self.clean_title(link.get_text())
                    if title and len(title) > 10:
                        for keyword in self.keywords + self.limited_keywords:
                            if re.search(r"\b" + re.escape(keyword) + r"\b", title, re.IGNORECASE):
                                keyword_matches += 1
                                logging.debug(f"Found keyword '{keyword}' in: {title[:60]}...")
                                break
                
                logging.info(f"Found {keyword_matches} links with keyword matches in first 50 links")
            else:
                logging.info(f"Successfully scraped {len(articles)} articles from {source_name}")
            
        except requests.RequestException as e:
            logging.error(f"Request error scraping {source_name}: {e}")
        except Exception as e:
            logging.error(f"Error parsing {source_name}: {e}")
            import traceback
            logging.debug(traceback.format_exc())
        
        return articles[:max_articles]

    def generic_article_extraction(self, soup, source_name, base_url):
        """Generic article extraction as fallback"""
        articles = []
        
        article_selectors = [
            'div[class*="story"]',
            'div[class*="article"]',
            'div[class*="news"]',
            'div[class*="post"]',
            'div[class*="item"]',
            'div[class*="card"]',
            'li[class*="story"]',
            'li[class*="article"]',
            'article',
            'a'  # Last resort - all links
        ]
        
        for selector in article_selectors:
            elements = soup.select(selector)
            if elements:
                logging.info(f"Found {len(elements)} elements with selector: {selector}")
                
                for element in elements[:30]:  # Increased from 10 to 30
                    try:
                        # Try to find title
                        title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5']) or element.find('a')
                        if not title_elem:
                            continue
                        
                        title = self.clean_title(title_elem.get_text())
                        if len(title) < 10:
                            continue
                        
                        # Try to find link
                        link_elem = element.find('a', href=True) or (title_elem if title_elem.name == 'a' else None)
                        if not link_elem or not link_elem.get('href'):
                            continue
                        
                        href = link_elem['href']
                        
                        # Skip invalid links
                        if not href or href == '#' or href.startswith('javascript:'):
                            continue
                        
                        # Normalize URL
                        if href.startswith('/'):
                            href = urljoin(base_url, href)
                        elif not href.startswith('http'):
                            href = urljoin(base_url, href)
                        
                        # Validate URL
                        if not href.startswith('http'):
                            continue
                        
                        # Check keywords
                        all_keywords = self.keywords + self.limited_keywords
                        matching_keyword = None
                        
                        for keyword in all_keywords:
                            pattern = r"\b" + re.escape(keyword) + r"\b"
                            if re.search(pattern, title, re.IGNORECASE):
                                if keyword in self.limited_keywords:
                                    if not self.can_use_limited_keyword(keyword):
                                        continue
                                    else:
                                        self.use_limited_keyword(keyword)
                                
                                matching_keyword = keyword
                                break
                        
                        if matching_keyword:
                            article_data = {
                                'title': title,
                                'url': href,
                                'keyword': matching_keyword,
                                'source': source_name,
                                'published_date': None
                            }
                            articles.append(article_data)
                            logging.debug(f"Generic extraction: {title[:50]}... with keyword '{matching_keyword}'")
                        
                    except Exception as e:
                        continue
                
                # If we found articles with this selector, don't try others
                if articles:
                    break
        
        return articles

    def try_rss_feed(self, soup, source_name, base_url):
        """Try to find and parse RSS feeds"""
        articles = []
        
        try:
            rss_links = soup.find_all('link', {'type': ['application/rss+xml', 'application/atom+xml']})
            
            for rss_link in rss_links:
                rss_url = rss_link.get('href')
                if rss_url:
                    if rss_url.startswith('/'):
                        rss_url = urljoin(base_url, rss_url)
                    
                    articles = self.parse_rss_feed(rss_url, source_name)
                    if articles:
                        break
        
        except Exception as e:
            logging.warning(f"RSS feed parsing failed for {source_name}: {e}")
        
        return articles

    def parse_rss_feed(self, rss_url, source_name):
        """Parse RSS feed for articles"""
        articles = []
        
        try:
            headers = self.get_random_headers()
            response = requests.get(rss_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')[:10]
            
            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')
                date_elem = item.find('pubDate')
                
                if title_elem and link_elem:
                    title = self.clean_title(title_elem.get_text())
                    url = link_elem.get_text().strip()
                    
                    all_keywords = self.keywords + self.limited_keywords
                    matching_keyword = None
                    
                    for keyword in all_keywords:
                        pattern = r"\b" + re.escape(keyword) + r"\b"
                        if re.search(pattern, title, re.IGNORECASE):
                            if keyword in self.limited_keywords:
                                if not self.can_use_limited_keyword(keyword):
                                    continue
                                else:
                                    self.use_limited_keyword(keyword)
                            
                            matching_keyword = keyword
                            break
                    
                    if matching_keyword:
                        published_date = None
                        if date_elem:
                            published_date = self.parse_article_date(date_elem.get_text(), source_name)
                        
                        articles.append({
                            'title': title,
                            'url': url,
                            'keyword': matching_keyword,
                            'source': f"{source_name} (RSS)",
                            'published_date': published_date
                        })
        
        except Exception as e:
            logging.warning(f"Error parsing RSS feed {rss_url}: {e}")
        
        return articles

    def fetch_newsapi_articles(self):
        """Fetch articles from NewsAPI with automatic API key rotation and rate limit handling"""
        articles = []
        all_keywords = self.keywords + self.limited_keywords
        
        for keyword in all_keywords:
            if keyword in self.limited_keywords and not self.can_use_limited_keyword(keyword):
                logging.info(f"Skipping NewsAPI search for limited keyword '{keyword}' - already used")
                continue
            
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': keyword,
                'domains': 'economictimes.indiatimes.com,livemint.com,moneycontrol.com',
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 20,
                'apiKey': self.get_current_api_key()
            }
            
            max_retries = len(self.newsapi_keys)
            retry_count = 0
            success = False
            
            while retry_count < max_retries and not success:
                try:
                    response = requests.get(url, params=params, timeout=10)
                    
                    if response.status_code == 429:
                        logging.warning(f"Rate limit hit for keyword '{keyword}' with API key {self.get_current_api_key()[:8]}***")
                        params['apiKey'] = self.handle_api_key_failure(self.get_current_api_key(), 429)
                        retry_count += 1
                        time.sleep(2)
                        continue
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    if data['status'] == 'ok':
                        self.mark_api_key_success(self.get_current_api_key())
                        keyword_articles_found = 0
                        
                        for article in data['articles']:
                            title = article.get('title', '')
                            
                            pattern = r"\b" + re.escape(keyword) + r"\b"
                            if re.search(pattern, title, re.IGNORECASE):
                                if keyword in self.limited_keywords and keyword_articles_found >= 1:
                                    break
                                
                                published_date = self.parse_article_date(
                                    article.get('publishedAt'), 
                                    'NewsAPI'
                                )
                                
                                articles.append({
                                    'title': title,
                                    'url': article.get('url', ''),
                                    'keyword': keyword,
                                    'source': f"NewsAPI - {article.get('source', {}).get('name', 'Unknown')}",
                                    'published_date': published_date
                                })
                                
                                keyword_articles_found += 1
                                
                                if keyword in self.limited_keywords:
                                    self.use_limited_keyword(keyword)
                                    break
                        
                        success = True
                    else:
                        logging.warning(f"NewsAPI returned status: {data.get('status')} for keyword '{keyword}'")
                        break
                    
                except requests.RequestException as e:
                    logging.error(f"Error fetching NewsAPI data for keyword '{keyword}': {e}")
                    if hasattr(e.response, 'status_code') and e.response.status_code == 429:
                        params['apiKey'] = self.handle_api_key_failure(self.get_current_api_key(), 429)
                        retry_count += 1
                        time.sleep(2)
                    else:
                        break
                except Exception as e:
                    logging.error(f"Unexpected error for keyword '{keyword}': {e}")
                    break
            
            if not success and retry_count >= max_retries:
                logging.error(f"Failed to fetch articles for keyword '{keyword}' after trying all API keys")
            
            time.sleep(1.5)
        
        return articles

    def fetch_custom_sources(self):
        """Fetch articles from custom sources using enhanced web scraping"""
        all_articles = []
        
        for source_name, source_config in self.custom_sources.items():
            logging.info(f"Scraping {source_name}...")
            articles = self.scrape_website_enhanced(source_name, source_config)
            all_articles.extend(articles)
            time.sleep(random.uniform(2, 5))
        
        return all_articles

    def fetch_all_news(self):
        """Fetch news from both NewsAPI and custom sources with enhanced duplicate tracking"""
        logging.info("Starting news fetch process...")
        self.reset_limited_keyword_usage()
        
        logging.info("Fetching news from NewsAPI...")
        newsapi_articles = self.fetch_newsapi_articles()
        
        logging.info("Fetching news from custom sources...")
        custom_articles = self.fetch_custom_sources()
        
        all_articles = newsapi_articles + custom_articles
        logging.info(f"Total articles scraped: {len(all_articles)} (NewsAPI: {len(newsapi_articles)}, Custom: {len(custom_articles)})")
        
        # Remove duplicates based on normalized headings within this scraping run
        seen_headings = {}
        unique_articles = []
        duplicate_count = 0
        
        for article in all_articles:
            title = article.get('title', '')
            url = article.get('url', '')
            
            if not title or not url:
                logging.warning(f"Skipping article with missing title or URL")
                continue
            
            # Normalize the heading
            normalized_title = self.normalize_heading(title)
            
            if not normalized_title:
                logging.warning(f"Skipping article with empty normalized title: {title}")
                continue
            
            if normalized_title not in seen_headings:
                seen_headings[normalized_title] = {
                    'title': title,
                    'url': url,
                    'source': article.get('source', 'Unknown')
                }
                unique_articles.append(article)
            else:
                duplicate_count += 1
                existing = seen_headings[normalized_title]
                logging.debug(f"Duplicate heading in current run:")
                logging.debug(f"  Original: '{existing['title'][:60]}...' from {existing['source']}")
                logging.debug(f"  Duplicate: '{title[:60]}...' from {article.get('source', 'Unknown')}")
        
        if duplicate_count > 0:
            logging.info(f"Removed {duplicate_count} duplicate headings from current scraping session")
        
        # Log keyword usage
        if self.limited_keyword_usage:
            logging.info("Limited keyword usage this run:")
            for keyword, count in self.limited_keyword_usage.items():
                logging.info(f"  {keyword}: {count}/1")
        
        # Save to database (will check for duplicate headings in database)
        if unique_articles:
            logging.info(f"Saving {len(unique_articles)} unique articles to database...")
            self.save_to_database(unique_articles)
        else:
            logging.warning("No unique articles found to save!")
        
        logging.info(f"Fetch completed. Processed {len(unique_articles)} unique articles")
        return unique_articles

    def get_database_stats(self):
        """Get database statistics"""
        connection = None
        try:
            connection = mysql.connector.connect(**self.mysql_config)
            cursor = connection.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM articles WHERE is_sent = TRUE")
            sent_articles = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM articles WHERE is_sent = FALSE")
            unsent_articles = cursor.fetchone()[0]
            
            cursor.execute("SELECT keyword, COUNT(*) FROM articles GROUP BY keyword")
            keyword_stats = cursor.fetchall()
            
            cursor.execute("SELECT source, COUNT(*) FROM articles GROUP BY source")
            source_stats = cursor.fetchall()
            
            return {
                'total_articles': total_articles,
                'sent_articles': sent_articles,
                'unsent_articles': unsent_articles,
                'keyword_stats': keyword_stats,
                'source_stats': source_stats
            }
            
        except Error as e:
            logging.error(f"Error getting database stats: {e}")
            return None
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def run_scheduler(self):
        """Run the scheduler for automated operations"""
        logging.info("Starting automated news fetcher scheduler...")
        logging.info(f"Using {len(self.newsapi_keys)} NewsAPI key(s)")
        
        schedule.every(90).minutes.do(self.fetch_all_news)
        schedule.every(30).minutes.do(lambda: self.send_scheduled_email("morning"))
        schedule.every(30).minutes.do(lambda: self.send_scheduled_email("evening"))
        
        self.fetch_all_news()
        
        logging.info("Scheduler started. Press Ctrl+C to stop.")
        logging.info("News fetching scheduled every 90 minutes")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logging.info("Scheduler stopped by user.")

    def manage_limited_keywords(self):
        """Interactive management of limited keywords"""
        print("\n=== Limited Keywords Management ===")
        print("Limited keywords are restricted to 1 article per 90-minute run cycle")
        print(f"Current limited keywords: {', '.join(self.limited_keywords) if self.limited_keywords else 'None'}")
        
        while True:
            print("\nOptions:")
            print("1. Add limited keyword")
            print("2. Remove limited keyword")
            print("3. View all keywords")
            print("4. Back to main menu")
            
            choice = input("Enter choice (1-4): ").strip()
            
            if choice == "1":
                keyword = input("Enter keyword to add to limited list: ").strip()
                if keyword and keyword not in self.limited_keywords:
                    self.limited_keywords.append(keyword)
                    print(f"Added '{keyword}' to limited keywords")
                elif keyword in self.limited_keywords:
                    print(f"'{keyword}' is already in limited keywords")
                else:
                    print("Invalid keyword")
            
            elif choice == "2":
                if not self.limited_keywords:
                    print("No limited keywords to remove")
                    continue
                
                print("Current limited keywords:")
                for i, kw in enumerate(self.limited_keywords, 1):
                    print(f"{i}. {kw}")
                
                try:
                    idx = int(input("Enter number to remove: ")) - 1
                    if 0 <= idx < len(self.limited_keywords):
                        removed = self.limited_keywords.pop(idx)
                        print(f"Removed '{removed}' from limited keywords")
                    else:
                        print("Invalid number")
                except ValueError:
                    print("Invalid input")
            
            elif choice == "3":
                print(f"\nRegular keywords ({len(self.keywords)}): {', '.join(self.keywords)}")
                print(f"Limited keywords ({len(self.limited_keywords)}): {', '.join(self.limited_keywords) if self.limited_keywords else 'None'}")
            
            elif choice == "4":
                break
            else:
                print("Invalid choice")

def main():
    """Main function to run the news fetcher"""
    
    # =================================================================
    # CONFIGURATION SECTION - Edit your settings here
    # =================================================================
    
    # MySQL Database Configuration
    MYSQL_CONFIG = {
        'host': 'host_name',
        'database': 'database_name',
        'user': 'your_username',
        'password': 'your_password'
    }
    
    # Email Configuration - EDIT HERE
    EMAIL_CONFIG = {
        'smtp_server': 'smtp.office365.com',
        'smtp_port': int('smtp_port'),
        'sender_email': 'sender@example.com',
        'sender_password': 'your_email_password',
        'recipient_email': 'recipient.email@example.com',
        'cc_email': 'email.cc@gmail.com'  # Single CC
        # For multiple CC: 'cc_email': ['email1@example.com', 'email2@example.com']
    }
    
    # NewsAPI Keys - Add multiple keys for automatic rotation
    API_KEYS = [
        "your_first_api_key",  # Primary key
        "your_second_api_key",  # Backup key
        # "your_third_api_key_here",
    ]
    
    # =================================================================
    # END OF CONFIGURATION SECTION
    # =================================================================
    
    fetcher = NewsFetcher(API_KEYS, MYSQL_CONFIG, EMAIL_CONFIG)
    
    if not fetcher.verify_table_exists():
        print("ERROR: Articles table does not exist in database!")
        print("Please create the table first using the provided SQL schema.")
        return
    
    print("=" * 60)
    print("Enhanced Automated News Fetcher with Heading-Based Duplicates")
    print("=" * 60)
    print(f"Active NewsAPI keys: {len(fetcher.newsapi_keys)}")
    print("Features:")
    print("- Automatic API key rotation on rate limits")
    print("- Heading-based duplicate detection (not URL)")
    print("- Limited keywords: 1 article per 90-minute cycle")
    print("- Enhanced web scraping with multiple strategies")
    print("- Robust error handling and retry logic")
    print("=" * 60)
    
    mode = input("""Choose mode:
1. Run automated scheduler (every 90 minutes)
2. Fetch news once
3. Send scheduled email
4. View database statistics
5. Manual operations
6. Manage limited keywords
7. Test scraping for specific source
8. View API key status
Enter choice (1-8): """).strip()
    
    if mode == "1":
        fetcher.run_scheduler()
        
    elif mode == "2":
        articles = fetcher.fetch_all_news()
        logging.info(f"Fetched {len(articles)} articles")
        
    elif mode == "3":
        email_type = input("Enter email type (morning/evening): ").strip().lower()
        if email_type in ["morning", "evening"]:
            fetcher.send_scheduled_email(email_type)
        else:
            print("Invalid email type")
            
    elif mode == "4":
        stats = fetcher.get_database_stats()
        if stats:
            print(f"\n=== Database Statistics ===")
            print(f"Total articles: {stats['total_articles']}")
            print(f"Sent articles: {stats['sent_articles']}")
            print(f"Unsent articles: {stats['unsent_articles']}")
            
            print(f"\nArticles by Keyword:")
            for keyword, count in stats['keyword_stats']:
                print(f"  {keyword}: {count}")
                
            print(f"\nArticles by Source:")
            for source, count in stats['source_stats']:
                print(f"  {source}: {count}")
        else:
            print("Unable to fetch database statistics")
            
    elif mode == "5":
        print("\nManual Operations:")
        print("1. View unsent articles")
        print("2. Send all unsent articles")
        print("3. Test limited keyword mechanism")
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == "1":
            unsent_articles = fetcher.get_unsent_articles()
            if unsent_articles:
                print(f"\n=== {len(unsent_articles)} Unsent Articles ===")
                for i, article in enumerate(unsent_articles[:20]):
                    print(f"{i+1}. ID: {article['id']}")
                    print(f"   Title: {article['article_heading']}")
                    print(f"   Source: {article['source']}")
                    print(f"   Keyword: {article['keyword']}")
                    print("-" * 80)
            else:
                print("No unsent articles found")
                
        elif choice == "2":
            unsent_articles = fetcher.get_unsent_articles()
            if unsent_articles:
                if fetcher.send_email(unsent_articles, "Manual Send"):
                    article_ids = [article['id'] for article in unsent_articles]
                    fetcher.update_sent_status(article_ids, True)
                    print(f"Sent email and marked {len(article_ids)} articles as sent")
                else:
                    print("Failed to send email")
            else:
                print("No unsent articles to send")
        
        elif choice == "3":
            print("\nTesting Limited Keyword Mechanism:")
            print("Current limited keywords:", fetcher.limited_keywords)
            print("Current usage:", fetcher.limited_keyword_usage)
            
            test_keyword = input("Enter a keyword to test: ").strip()
            if test_keyword:
                print(f"Can use '{test_keyword}': {fetcher.can_use_limited_keyword(test_keyword)}")
                if fetcher.can_use_limited_keyword(test_keyword):
                    fetcher.use_limited_keyword(test_keyword)
                    print(f"After usage - Can use '{test_keyword}': {fetcher.can_use_limited_keyword(test_keyword)}")
        else:
            print("Invalid choice")
    
    elif mode == "6":
        fetcher.manage_limited_keywords()
    
    elif mode == "7":
        print("\nAvailable sources:")
        for i, source_name in enumerate(fetcher.custom_sources.keys(), 1):
            print(f"{i}. {source_name}")
        
        try:
            choice = int(input("Enter source number to test: ")) - 1
            source_names = list(fetcher.custom_sources.keys())
            if 0 <= choice < len(source_names):
                source_name = source_names[choice]
                source_config = fetcher.custom_sources[source_name]
                
                print(f"\nTesting scraping for: {source_name}")
                print(f"URL: {source_config['url']}")
                
                articles = fetcher.scrape_website_enhanced(source_name, source_config)
                
                print(f"\nFound {len(articles)} articles:")
                for i, article in enumerate(articles, 1):
                    print(f"{i}. {article['title']}")
                    print(f"   Keyword: {article['keyword']}")
                    print("-" * 50)
            else:
                print("Invalid source number")
        except ValueError:
            print("Invalid input")
    
    elif mode == "8":
        print("\n=== API Key Status ===")
        print(f"Total API keys: {len(fetcher.newsapi_keys)}")
        print(f"Current active key index: {fetcher.current_api_key_index}")
        for i, key in enumerate(fetcher.newsapi_keys):
            masked_key = key[:8] + "***"
            failures = fetcher.api_key_failures.get(key, 0)
            last_success = fetcher.api_key_last_success.get(key)
            status = "🟢 Active" if i == fetcher.current_api_key_index else "⚪ Standby"
            print(f"\nKey {i+1}: {masked_key}")
            print(f"  Status: {status}")
            print(f"  Failures: {failures}")
            print(f"  Last success: {last_success.strftime('%Y-%m-%d %H:%M:%S') if last_success else 'Never'}")
    
    else:
        print("Invalid choice. Please run the program again and choose 1-8.")

if __name__ == "__main__":
    main()
