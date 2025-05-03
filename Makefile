# Makefile for 智能文献处理系统

.PHONY: setup install run test clean

# Default target
all: setup install run

# Setup the project
setup:
	@echo "Setting up the project..."
	python setup.py

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

# Run the application
run:
	@echo "Running the application..."
	python run.py

# Run the application in development mode
dev:
	@echo "Running the application in development mode..."
	uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Run tests
test:
	@echo "Running tests..."
	python test_all.py

# Run API tests
test-api:
	@echo "Running API tests..."
	python test_api.py

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	rm -rf __pycache__
	rm -rf temp/*
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

# Show help
help:
	@echo "智能文献处理系统 - Makefile targets:"
	@echo "  setup      - Set up the project structure"
	@echo "  install    - Install dependencies"
	@echo "  run        - Run the application"
	@echo "  dev        - Run the application in development mode"
	@echo "  test       - Run tests"
	@echo "  test-api   - Run API tests"
	@echo "  clean      - Clean temporary files"
	@echo "  all        - Setup, install, and run (default)"
	@echo "  help       - Show this help message"
