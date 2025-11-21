# Installation Guide

Complete step-by-step installation guide for the Automated News Fetcher.

## Table of Contents

- [System Requirements](#system-requirements)
- [Windows Installation](#windows-installation)
- [Linux Installation](#linux-installation)
- [macOS Installation](#macos-installation)
- [Docker Installation](#docker-installation)
- [Configuration](#configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements
- **OS**: Windows 10+, Ubuntu 18.04+, macOS 10.14+
- **Python**: 3.7 or higher
- **MySQL**: 5.7 or higher
- **RAM**: 2GB minimum, 4GB recommended
- **Disk Space**: 500MB for application + database
- **Internet**: Stable connection for API calls and web scraping

### Recommended Requirements
- **Python**: 3.9 or higher
- **MySQL**: 8.0 or higher
- **RAM**: 4GB or more
- **Disk Space**: 2GB+ for long-term storage

## Windows Installation

### Step 1: Install Python

1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run installer
3. **Important**: Check "Add Python to PATH"
4. Click "Install Now"
5. Verify installation:
   ```cmd
   python --version
   pip --version
   ```

### Step 2: Install MySQL

1. Download [MySQL Installer](https://dev.mysql.com/downloads/installer/)
2. Choose "MySQL Server" in setup
3. Select "Development Computer" configuration
4. Set root password (remember this!)
5. Complete installation
6. Verify installation:
   ```cmd
   mysql --version
   ```

### Step 3: Clone Repository

```cmd
# Install Git if not already installed
# Download from: https://git-scm.com/download/win

git clone https://github.com/yourusername/news-fetcher.git
cd news-fetcher
```

### Step 4: Create Virtual Environment

```cmd
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your command prompt.

### Step 5: Install Dependencies

```cmd
pip install -r requirements.txt
```

### Step 6: Setup Database

```cmd
# Login to MySQL
mysql -u root -p

# Create database (or use SQL file)
source database_schema.sql

# Or manually:
CREATE DATABASE your_database_name CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE your_database_name;
# (paste table creation SQL)
```

### Step 7: Configure Application

```cmd
# Copy example configuration
copy .env.example .env

# Edit .env with your credentials
notepad .env
```

### Step 8: Run Application

```cmd
python news_fetcher.py
```

## Linux Installation

### Step 1: Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### Step 2: Install Python

```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip python3-venv -y

# CentOS/RHEL
sudo yum install python3 python3-pip -y

# Verify
python3 --version
pip3 --version
```

### Step 3: Install MySQL

#### Ubuntu/Debian:
```bash
sudo apt install mysql-server -y
sudo mysql_secure_installation
```

#### CentOS/RHEL:
```bash
sudo yum install mysql-server -y
sudo systemctl start mysqld
sudo systemctl enable mysqld
sudo mysql_secure_installation
```

### Step 4: Clone Repository

```bash
# Install Git if needed
sudo apt install git -y  # Ubuntu/Debian
# or
sudo yum install git -y  # CentOS/RHEL

# Clone repository
git clone https://github.com/yourusername/news-fetcher.git
cd news-fetcher
```

### Step 5: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 6: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 7: Setup Database

```bash
# Login to MySQL
sudo mysql -u root -p

# Import schema
mysql -u root -p < database_schema.sql
```

### Step 8: Configure Application

```bash
cp .env.example .env
nano .env  # or use your preferred editor
```

### Step 9: Run Application

```bash
python news_fetcher.py
```

### Optional: Setup as System Service

Create service file:
```bash
sudo nano /etc/systemd/system/news-fetcher.service
```

Add content:
```ini
[Unit]
Description=Automated News Fetcher
After=network.target mysql.service

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/news-fetcher
Environment="PATH=/path/to/news-fetcher/venv/bin"
ExecStart=/path/to/news-fetcher/venv/bin/python news_fetcher.py

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable news-fetcher
sudo systemctl start news-fetcher
sudo systemctl status news-fetcher
```

## macOS Installation

### Step 1: Install Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install Python

```bash
brew install python@3.9
python3 --version
```

### Step 3: Install MySQL

```bash
brew install mysql
brew services start mysql
mysql_secure_installation
```

### Step 4: Clone Repository

```bash
git clone https://github.com/yourusername/news-fetcher.git
cd news-fetcher
```

### Step 5: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 6: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 7: Setup Database

```bash
mysql -u root -p < database_schema.sql
```

### Step 8: Configure Application

```bash
cp .env.example .env
nano .env
```

### Step 9: Run Application

```bash
python news_fetcher.py
```

## Docker Installation

### Prerequisites
- Docker installed and running
- Docker Compose installed

### Step 1: Create Docker Files

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run application
CMD ["python", "news_fetcher.py"]
```

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./database_schema.sql:/docker-entrypoint-initdb.d/schema.sql

  news-fetcher:
    build: .
    depends_on:
      - mysql
    environment:
      MYSQL_HOST: mysql
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: root
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    volumes:
      - ./logs:/app/logs

volumes:
  mysql_data:
```

### Step 2: Configure and Run

```bash
# Clone repository
git clone https://github.com/yourusername/news-fetcher.git
cd news-fetcher

# Setup environment
cp .env.example .env
nano .env

# Build and run
docker-compose up -d

# View logs
docker-compose logs -f news-fetcher

# Stop
docker-compose down
```

## Configuration

### Database Configuration

Edit `.env` file:
```ini
MYSQL_HOST=localhost
MYSQL_DATABASE=your_database_name
MYSQL_USER=root
MYSQL_PASSWORD=your_secure_password
```

### Email Configuration

For **Office 365**:
```ini
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SENDER_EMAIL=your_email@domain.com
SENDER_PASSWORD=your_password
```

For **Gmail**:
```ini
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password  # Use App Password, not account password
```

**Gmail Setup:**
1. Enable 2-Factor Authentication
2. Generate App Password: Google Account → Security → App passwords
3. Use App Password in configuration

For **Custom SMTP**:
```ini
SMTP_SERVER=mail.your-domain.com
SMTP_PORT=587
SENDER_EMAIL=noreply@your-domain.com
SENDER_PASSWORD=your_password
```

### NewsAPI Configuration

1. Get API keys from [newsapi.org](https://newsapi.org/)
2. Add to `.env`:
```ini
NEWSAPI_KEY_1=your_first_key
NEWSAPI_KEY_2=your_second_key
NEWSAPI_KEY_3=your_third_key
```

**Free Tier Limits:**
- 100 requests per day
- Use multiple keys for higher limits

## Verification

### Test Database Connection

```python
python -c "
import mysql.connector
config = {
    'host': 'localhost',
    'database': 'your_database_name',
    'user': 'root',
    'password': 'your_password'
}
conn = mysql.connector.connect(**config)
print('Database connection successful!')
conn.close()
"
```

### Test Email Sending

```python
python -c "
import smtplib
from email.mime.text import MIMEText

msg = MIMEText('Test email')
msg['Subject'] = 'Test'
msg['From'] = 'your_email@domain.com'
msg['To'] = 'recipient@domain.com'

server = smtplib.SMTP('smtp.office365.com', 587)
server.starttls()
server.login('your_email@domain.com', 'your_password')
server.send_message(msg)
server.quit()
print('Email sent successfully!')
"
```

### Test NewsAPI

```python
python -c "
import requests
api_key = 'your_api_key'
response = requests.get(f'https://newsapi.org/v2/everything?q=test&apiKey={api_key}')
print(f'Status: {response.status_code}')
print(f'Response: {response.json()['status']}')
"
```

### Run Test Fetch

```bash
python news_fetcher.py
# Choose option 2: Fetch news once
```

## Troubleshooting

### Python Installation Issues

**Windows - Python not found:**
```cmd
# Add Python to PATH manually
setx PATH "%PATH%;C:\Users\YourUsername\AppData\Local\Programs\Python\Python39"
```

**Linux - pip not found:**
```bash
sudo apt install python3-pip
# or
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
```

### MySQL Installation Issues

**Can't connect to MySQL server:**
```bash
# Check if MySQL is running
sudo systemctl status mysql  # Linux
# or
net start mysql  # Windows

# Start MySQL if stopped
sudo systemctl start mysql  # Linux
# or
net start mysql  # Windows
```

**Access denied for user:**
```bash
# Reset root password
sudo mysql
ALTER USER 'root'@'localhost' IDENTIFIED BY 'new_password';
FLUSH PRIVILEGES;
```

### Dependency Installation Issues

**SSL Certificate Error:**
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

**Compilation Error (mysqlclient):**
```bash
# Ubuntu/Debian
sudo apt install python3-dev default-libmysqlclient-dev build-essential

# macOS
brew install mysql-client
export PATH="/usr/local/opt/mysql-client/bin:$PATH"

# Then retry
pip install -r requirements.txt
```

### Application Runtime Issues

**ModuleNotFoundError:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Reinstall requirements
pip install -r requirements.txt
```

**Database connection timeout:**
- Check firewall settings
- Verify MySQL is listening on correct port
- Check network connectivity

### Email Sending Issues

**Authentication failed:**
- Verify email/password are correct
- Use App Password for Gmail/Office 365
- Check account security settings
- Enable "Less secure app access" if applicable

**Connection refused:**
- Verify SMTP server and port
- Check firewall rules
- Try different SMTP port (465 for SSL)

## Next Steps

After successful installation:

1. **Test the application**: Run mode 2 (Fetch news once)
2. **Verify database**: Check that articles are saved
3. **Test email**: Send a test email with mode 3
4. **Start scheduler**: Run mode 1 for automated operation
5. **Monitor logs**: Check `regulatory_updates_fetcher.log`

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review application logs
3. Search [existing issues](https://github.com/Acash-bits/news-fetcher/issues)
4. Create a new issue with:
   - OS and Python version
   - Error messages
   - Steps to reproduce
   - Relevant log excerpts

---

**Installation complete!** Return to [README.md](README.md) for usage instructions.