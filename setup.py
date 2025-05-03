import os
import shutil
import argparse

def setup_project():
    """
    Set up the project structure and copy necessary files.
    """
    print("Setting up the project structure...")
    
    # Create directories using create_dirs.py
    try:
        from create_dirs import create_directories
        create_directories()
    except ImportError:
        # Fallback if create_dirs.py is not available
        directories = [
            "static",
            "uploads",
            "results",
            "temp",
            "services",
            "routers"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"Created directory: {directory}")
    
    # Copy index.html and JavaScript files to static directory
    if os.path.exists("index.html"):
        os.makedirs("static", exist_ok=True)
        shutil.copy("index.html", "static/index.html")
        print("Copied index.html to static directory")
    
    # Create static/js directory if it doesn't exist
    os.makedirs("static/js", exist_ok=True)
    
    # Copy JavaScript files if they exist
    if os.path.exists("static/js/api.js") and os.path.exists("static/js/main.js"):
        print("JavaScript files already exist in static/js directory")
    
    # Create empty .env file if it doesn't exist
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("""# API Keys
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.deepseek.com/v1
GOOGLE_KEY=
MINERU_API_KEY=

# Model Settings (these will be read from constants.py)
CRAWLER_MODEL=deepseek-chat
SELECTOR_MODEL=deepseek-chat
REVIEW_MODEL=deepseek-chat
""")
        print("Created empty .env file")
    
    # Create api.txt file for MinerU if it doesn't exist
    if not os.path.exists("api.txt"):
        with open("api.txt", "w") as f:
            f.write("")
        print("Created empty api.txt file for MinerU")
    
    print("\nProject setup complete!")
    print("\nNext steps:")
    print("1. Add your API keys to the .env file")
    print("2. Install dependencies with: pip install -r requirements.txt")
    print("3. Run the application with: uvicorn app:app --host 0.0.0.0 --port 8000 --reload")

def main():
    parser = argparse.ArgumentParser(description="Set up the project structure")
    parser.add_argument("--force", action="store_true", help="Force setup even if directories already exist")
    
    args = parser.parse_args()
    
    if args.force:
        setup_project()
    else:
        # Check if any of the directories already exist
        directories = ["static", "uploads", "results", "temp", "services", "routers"]
        existing_dirs = [d for d in directories if os.path.exists(d)]
        
        if existing_dirs:
            print(f"The following directories already exist: {', '.join(existing_dirs)}")
            response = input("Do you want to continue with setup? (y/n): ")
            if response.lower() == 'y':
                setup_project()
            else:
                print("Setup aborted.")
        else:
            setup_project()

if __name__ == "__main__":
    main()
