#!/bin/bash

# IBM Bob Legacy Code Modernization Platform - Quick Start Script
# This script automates the setup and launch process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
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

check_command() {
    if command -v "$1" &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_error "$1 is not installed"
        return 1
    fi
}

# Main script
main() {
    print_header "IBM Bob Quick Start"
    echo ""
    
    # Step 1: Check prerequisites
    print_header "Step 1: Checking Prerequisites"
    
    MISSING_DEPS=0
    
    # Check Python
    if check_command python3; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_info "Python version: $PYTHON_VERSION"
        
        # Check if version is 3.11+
        MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 11 ]); then
            print_error "Python 3.11 or higher is required"
            MISSING_DEPS=1
        fi
    else
        print_error "Python 3 is required"
        MISSING_DEPS=1
    fi
    
    # Check pip
    check_command pip3 || MISSING_DEPS=1
    
    # Check git
    check_command git || print_warning "Git not found (optional)"
    
    if [ $MISSING_DEPS -eq 1 ]; then
        print_error "Missing required dependencies. Please install them first."
        echo ""
        print_info "Installation instructions:"
        print_info "  macOS: brew install python@3.11"
        print_info "  Ubuntu: sudo apt install python3.11 python3-pip"
        print_info "  RHEL: sudo dnf install python3.11 python3-pip"
        exit 1
    fi
    
    echo ""
    
    # Step 2: Setup virtual environment
    print_header "Step 2: Setting Up Virtual Environment"
    
    cd "$PROJECT_DIR"
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists"
        read -p "Remove and recreate? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv
            print_info "Removed existing virtual environment"
        fi
    fi
    
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    print_info "Activating virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment activated"
    
    echo ""
    
    # Step 3: Install dependencies
    print_header "Step 3: Installing Dependencies"
    
    print_info "Upgrading pip..."
    pip install --upgrade pip --quiet
    
    print_info "Installing requirements..."
    pip install -r requirements.txt --quiet
    print_success "Dependencies installed"
    
    echo ""
    
    # Step 4: Configure environment
    print_header "Step 4: Configuring Environment"
    
    if [ ! -f ".env" ]; then
        print_info "Creating .env file from template..."
        cp .env.example .env
        print_success ".env file created"
        
        print_warning "Please configure your IBM watsonx.ai credentials in .env"
        print_info "Required variables:"
        print_info "  - WATSONX_API_KEY"
        print_info "  - WATSONX_PROJECT_ID"
        echo ""
        
        read -p "Do you want to configure now? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            read -p "Enter your watsonx.ai API key: " API_KEY
            read -p "Enter your watsonx.ai Project ID: " PROJECT_ID
            
            # Update .env file
            sed -i.bak "s/your_api_key_here/$API_KEY/" .env
            sed -i.bak "s/your_project_id_here/$PROJECT_ID/" .env
            rm .env.bak
            
            print_success "Credentials configured"
        else
            print_warning "Remember to configure .env before running the application"
        fi
    else
        print_success ".env file already exists"
    fi
    
    echo ""
    
    # Step 5: Create output directories
    print_header "Step 5: Creating Output Directories"
    
    mkdir -p output logs
    print_success "Output directories created"
    
    echo ""
    
    # Step 6: Run tests
    print_header "Step 6: Running Tests (Optional)"
    
    read -p "Run tests to verify installation? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        print_info "Running tests..."
        if python -m pytest tests/ -v --tb=short 2>/dev/null; then
            print_success "All tests passed"
        else
            print_warning "Some tests failed (this may be expected if watsonx.ai is not configured)"
        fi
    fi
    
    echo ""
    
    # Step 7: Launch application
    print_header "Step 7: Launch Application"
    
    echo "Choose how to start IBM Bob:"
    echo "  1) Streamlit Web UI (recommended for beginners)"
    echo "  2) REST API Server (for programmatic access)"
    echo "  3) Both UI and API"
    echo "  4) Run demo"
    echo "  5) Exit (manual start)"
    echo ""
    
    read -p "Enter choice (1-5): " -n 1 -r CHOICE
    echo ""
    echo ""
    
    case $CHOICE in
        1)
            print_info "Starting Streamlit UI..."
            print_success "UI will be available at: http://localhost:8501"
            echo ""
            streamlit run ui/app.py
            ;;
        2)
            print_info "Starting REST API..."
            print_success "API will be available at: http://localhost:8000"
            print_success "API docs at: http://localhost:8000/docs"
            echo ""
            python scripts/run_api_server.py
            ;;
        3)
            print_info "Starting both UI and API..."
            print_success "UI: http://localhost:8501"
            print_success "API: http://localhost:8000"
            echo ""
            python scripts/run_api_server.py &
            API_PID=$!
            streamlit run ui/app.py
            kill $API_PID 2>/dev/null
            ;;
        4)
            print_info "Running demo..."
            python scripts/demo.py
            ;;
        5)
            print_info "Setup complete!"
            echo ""
            print_info "To start manually:"
            print_info "  1. Activate virtual environment: source venv/bin/activate"
            print_info "  2. Start UI: streamlit run ui/app.py"
            print_info "  3. Or start API: python scripts/run_api_server.py"
            print_info "  4. Or run demo: python scripts/demo.py"
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
    
    echo ""
    print_header "Setup Complete!"
    print_success "IBM Bob is ready to use"
    echo ""
    print_info "Documentation:"
    print_info "  - User Guide: USER_GUIDE.md"
    print_info "  - API Docs: API_DOCUMENTATION.md"
    print_info "  - Demo Guide: DEMO.md"
    echo ""
}

# Run main function
main "$@"

