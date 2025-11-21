#!/bin/bash

# ===================================================================
# Automated Setup Script for News Fetcher
# ===================================================================
# This script automates the installation and configuration process
# Compatible with: Ubuntu/Debian, CentOS/RHEL, macOS
# ===================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}====================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}====================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists apt-get; then
            OS="ubuntu"
            PKG_MANAGER="apt-get"
        elif command_exists yum; then
            OS="centos"
            PKG_MANAGER="yum"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PKG_MANAGER="brew"
    else
        OS="unknown"
    fi
}

# Main installation process
main() {
    print_header "Automated News Fetcher - Setup Script"
    
    # Detect operating system
    detect_os
    print_info "Detected OS: $OS"
    
    # Check Python installation
    print_header "Checking Python Installation"
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version)
        print_success "Python installed: $PYTHON_VERSION"
    else
        print_error "Python 3 not found!"
        print_info "Installing Python 3..."
        
        case $OS in
            ubuntu)
                sudo apt-get update
                sudo apt-get install -y python3 python3-pip python3-venv
                ;;
            centos)
                sudo yum install -y python3 python3-pip
                ;;
            macos)
                if ! command_exists brew; then
                    print_info "Installing Homebrew..."
                    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
                fi
                brew install python@3.9
                ;;
        esac
        print_success "Python 3 installed"
    fi
    
    # Check MySQL installation
    print_header "Checking MySQL Installation"
    if command_exists mysql; then
        MYSQL_VERSION=$(mysql --version)
        print_success "MySQL installed: $MYSQL_VERSION"
    else
        print_warning "MySQL not found!"
        read -p "Do you want to install MySQL? (y/n): " install_mysql
        
        if [[ $install_mysql == "y" ]]; then
            case $OS in
                ubuntu)
                    sudo apt-get update
                    sudo apt-get install -y mysql-server
                    sudo systemctl start mysql
                    sudo systemctl enable mysql
                    ;;
                centos)
                    sudo yum install -y mysql-server
                    sudo systemctl start mysqld
                    sudo systemctl enable mysqld
                    ;;
                macos)
                    brew install mysql
                    brew services start mysql
                    ;;
            esac
            print_success "MySQL installed"
            print_info "Running MySQL secure installation..."
            sudo mysql_secure_installation
        fi
    fi
    
    # Create virtual environment
    print_header "Setting Up Virtual Environment"
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_success "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    print_info "Activating virtual environment..."
    source venv/bin/activate
    
    # Install dependencies
    print_header "Installing Python Dependencies"
    if [ -f "requirements.txt" ]; then
        print_info "Installing packages from requirements.txt..."
        pip install --upgrade pip
        pip install -r requirements.txt
        print_success "Dependencies installed"
    else
        print_error "requirements.txt not found!"
        exit 1
    fi
    
    # Setup environment file
    print_header "Setting Up Configuration"
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Created .env file from template"
            print_warning "Please edit .env file with your credentials!"
        else
            print_error ".env.example not found!"
        fi
    else
        print_success ".env file already exists"
    fi
    
    # Setup database
    print_header "Setting Up Database"
    read -p "Do you want to set up the database now? (y/n): " setup_db
    
    if [[ $setup_db == "y" ]]; then
        read -p "Enter MySQL root password: " -s mysql_password
        echo
        
        if [ -f "database_schema.sql" ]; then
            print_info "Creating database and tables..."
            mysql -u root -p"$mysql_password" < database_schema.sql 2>/dev/null
            if [ $? -eq 0 ]; then
                print_success "Database setup complete"
            else
                print_error "Database setup failed. Please check your credentials and try manually."
            fi
        else
            print_error "database_schema.sql not found!"
        fi
    fi
    
    # Verification
    print_header "Verification"
    
    print_info "Testing database connection..."
    python3 -c "
import mysql.connector
try:
    conn = mysql.connector.connect(
        host='localhost',
        database='lks_company',
        user='root',
        password='$mysql_password'
    )
    conn.close()
    print('✓ Database connection successful!')
except Exception as e:
    print(f'✗ Database connection failed: {e}')
" 2>/dev/null || print_warning "Could not verify database connection"
    
    # Final instructions
    print_header "Setup Complete!"
    echo
    print_success "Installation completed successfully!"
    echo
    print_info "Next steps:"
    echo "  1. Edit .env file with your credentials:"
    echo "     nano .env"
    echo
    echo "  2. Activate virtual environment:"
    echo "     source venv/bin/activate"
    echo
    echo "  3. Run the application:"
    echo "     python news_fetcher.py"
    echo
    print_info "For detailed documentation, see README.md"
    echo
}

# Run main function
main