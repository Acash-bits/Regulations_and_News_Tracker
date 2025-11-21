"""
Configuration Template for News Fetcher Application

This file provides a template for configuration settings.
Copy this file to 'config.py' and update with your actual credentials.

IMPORTANT: Never commit config.py to version control!
Add config.py to .gitignore
"""

# ===================================================================
# MySQL Database Configuration
# ===================================================================
MYSQL_CONFIG = {
    'host': 'localhost',           # Database host (use 'mysql' for Docker)
    'database': 'your_db_name',     # Database name
    'user': 'root',                # MySQL username
    'password': 'your_password'    # MySQL password - CHANGE THIS!
}

# ===================================================================
# Email Configuration (SMTP)
# ===================================================================
EMAIL_CONFIG = {
    # Office 365 SMTP Settings
    'smtp_server': 'smtp.office365.com',
    'smtp_port': 587,
    
    # Gmail SMTP Settings (alternative)
    # 'smtp_server': 'smtp.gmail.com',
    # 'smtp_port': 587,
    
    # Email Credentials
    'sender_email': 'your_email@domain.com',     # CHANGE THIS!
    'sender_password': 'your_password',          # CHANGE THIS! Use App Password for Gmail
    
    # Recipients
    'recipient_email': 'recipient@domain.com',   # Primary recipient - CHANGE THIS!
    
    # CC Recipients (optional)
    'cc_email': 'cc@domain.com'                  # Single CC - CHANGE THIS!
    # For multiple CC recipients, use list:
    # 'cc_email': ['cc1@domain.com', 'cc2@domain.com', 'cc3@domain.com']
}

# ===================================================================
# NewsAPI Keys Configuration
# ===================================================================
# Add multiple API keys for automatic rotation
# Free tier: 100 requests/day per key
# Get keys from: https://newsapi.org/
# ===================================================================
API_KEYS = [
    "your_primary_newsapi_key",      # CHANGE THIS!
    "your_backup_newsapi_key_1",     # CHANGE THIS!
    "your_backup_newsapi_key_2",     # CHANGE THIS! (optional)
    # Add more keys as needed for higher throughput
]

# ===================================================================
# Application Settings
# ===================================================================
APP_SETTINGS = {
    # Fetch interval in minutes (default: 90 minutes)
    'fetch_interval_minutes': 90,
    
    # Morning email schedule (hours in 24h format)
    'morning_email_start': 10,      # 10 AM
    'morning_email_end': 12,        # 12 PM
    
    # Evening email schedule (hours in 24h format)
    'evening_email_start': 16,      # 4 PM
    'evening_email_end': 18,        # 6 PM
    
    # Timezone (India Standard Time)
    'timezone': 'Asia/Kolkata',
    
    # Maximum articles per source per fetch
    'max_articles_per_source': 10,
    
    # Enable/disable logging
    'logging_enabled': True,
    'log_file': 'regulatory_updates_fetcher.log',
    'log_level': 'INFO',  # Options: DEBUG, INFO, WARNING, ERROR
}

# ===================================================================
# Keyword Configuration
# ===================================================================

# Regular keywords (unlimited articles per cycle)
REGULAR_KEYWORDS = [
    'Copyright',
    'Patent',
    'GST',
    'Customs',
    'Levy',
    'FDI',
    'SEBI',
    'FEMA',
    'IPR',
    'Intellectual Property',
    'Trademark',
    'Tariff',
    'Semiconductor',
    'Press Note',
    'Antitrust',
    'DRHP',
    'Anti-Dumping',
    'Anti Dumping',
    'Input Tax Credit',
    'ITC',
    'AI',
    'Regulations',
    'Regulatory',
    'Guidelines'
]

# Limited keywords (1 article per 90-minute cycle)
# Use this for high-frequency keywords to avoid spam
LIMITED_KEYWORDS = [
    'Tarrif',
    # Add more keywords as needed
]

# ===================================================================
# Custom News Sources Configuration
# ===================================================================
# Add or modify news sources to scrape
# Format:
# 'Source Name': {
#     'url': 'website_url',
#     'selectors': {
#         'article_container': ['css_selector1', 'css_selector2'],
#         'title': ['title_selector1', 'title_selector2'],
#         'link': ['link_selector'],
#         'date': ['date_selector1', 'date_selector2']
#     }
# }
# ===================================================================
CUSTOM_SOURCES = {
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

# ===================================================================
# Advanced Configuration (Optional)
# ===================================================================

# User agents for web scraping (rotated randomly)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
]

# NewsAPI domains to search (for NewsAPI fetching)
NEWSAPI_DOMAINS = 'economictimes.indiatimes.com,livemint.com,moneycontrol.com'

# Request timeouts (seconds)
REQUEST_TIMEOUT = 15
API_REQUEST_TIMEOUT = 10

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Database connection pool settings
DB_POOL_SIZE = 5
DB_POOL_NAME = 'news_fetcher_pool'

# ===================================================================
# Usage Example
# ===================================================================
"""
from config_template import (
    MYSQL_CONFIG, 
    EMAIL_CONFIG, 
    API_KEYS, 
    APP_SETTINGS,
    REGULAR_KEYWORDS,
    LIMITED_KEYWORDS,
    CUSTOM_SOURCES
)

# Initialize NewsFetcher with configuration
fetcher = NewsFetcher(
    newsapi_keys=API_KEYS,
    mysql_config=MYSQL_CONFIG,
    email_config=EMAIL_CONFIG
)

# Override keywords if needed
fetcher.keywords = REGULAR_KEYWORDS
fetcher.limited_keywords = LIMITED_KEYWORDS

# Start scheduler
fetcher.run_scheduler()
"""