-- ===================================================================
-- DATABASE SCHEMA FOR NEWS FETCHER APPLICATION
-- ===================================================================
-- Description: Complete database setup for storing news articles
--              with duplicate prevention and email tracking
-- Version: 2.0
-- Last Updated: 2024
-- ===================================================================

-- Create database with UTF-8 support for international characters
CREATE DATABASE IF NOT EXISTS your_database_name 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE your_database_name;
-- ===================================================================
-- MAIN ARTICLES TABLE
-- ===================================================================
-- Stores all fetched news articles with metadata and tracking info
-- ===================================================================

DROP TABLE IF EXISTS articles;

CREATE TABLE articles (
    -- Primary Key
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique identifier for each article',
    
    -- Article Information
    article_heading VARCHAR(500) NOT NULL COMMENT 'Title/headline of the article',
    article_link VARCHAR(1000) NOT NULL UNIQUE COMMENT 'URL of the article (unique constraint prevents duplicates)',
    keyword VARCHAR(100) NOT NULL COMMENT 'Keyword that matched this article',
    source VARCHAR(200) NOT NULL COMMENT 'Source name (e.g., NewsAPI - Economic Times, MoneyControl)',
    
    -- Date Information
    published_date DATETIME COMMENT 'Publication date/time from source (UTC)',
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'When this record was created',
    date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last update timestamp',
    
    -- Email Tracking
    is_sent BOOLEAN DEFAULT FALSE COMMENT 'Whether this article has been sent via email',
    
    -- Indexes for Performance
    INDEX idx_keyword (keyword) COMMENT 'Fast lookup by keyword',
    INDEX idx_source (source) COMMENT 'Fast lookup by source',
    INDEX idx_is_sent (is_sent) COMMENT 'Fast lookup of unsent articles',
    INDEX idx_published_date (published_date) COMMENT 'Fast sorting by publication date',
    INDEX idx_date_created (date_created) COMMENT 'Fast sorting by creation date',
    
    -- Composite Index for Common Queries
    INDEX idx_sent_published (is_sent, published_date DESC) COMMENT 'Optimized for fetching unsent articles ordered by date'
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Main table storing all news articles';

-- ===================================================================
-- SAMPLE DATA (Optional - for testing)
-- ===================================================================

-- INSERT INTO articles (article_heading, article_link, keyword, source, published_date, is_sent)
-- VALUES 
-- ('GST Council announces new reforms', 'https://example.com/gst-reforms-2024', 'GST', 'NewsAPI - Economic Times', NOW(), FALSE),
-- ('SEBI introduces new IPO guidelines', 'https://example.com/sebi-ipo-guidelines', 'SEBI', 'LiveMint', NOW(), FALSE),
-- ('Copyright Act amendments proposed', 'https://example.com/copyright-amendments', 'Copyright', 'MoneyControl', NOW(), FALSE);

-- ===================================================================
-- USEFUL QUERIES
-- ===================================================================

-- Get all unsent articles (used by email scheduler)
-- SELECT * FROM articles WHERE is_sent = FALSE ORDER BY published_date DESC, date_created DESC;

-- Get article count by keyword
-- SELECT keyword, COUNT(*) as count FROM articles GROUP BY keyword ORDER BY count DESC;

-- Get article count by source
-- SELECT source, COUNT(*) as count FROM articles GROUP BY source ORDER BY count DESC;

-- Get articles from last 24 hours
-- SELECT * FROM articles WHERE date_created >= DATE_SUB(NOW(), INTERVAL 24 HOUR);

-- Mark specific articles as sent
-- UPDATE articles SET is_sent = TRUE WHERE id IN (1, 2, 3);

-- Delete articles older than 90 days (cleanup)
-- DELETE FROM articles WHERE date_created < DATE_SUB(NOW(), INTERVAL 90 DAY);

-- ===================================================================
-- BACKUP RECOMMENDATION
-- ===================================================================
-- Regular backups recommended:
-- mysqldump -u root -p your_database_name > backup_$(date +%Y%m%d).sql
-- ===================================================================