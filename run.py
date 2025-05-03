import os
import argparse
import uvicorn
import webbrowser
from threading import Timer

def open_browser(port):
    """
    Open the browser after a short delay
    """
    webbrowser.open(f"http://localhost:{port}")

def run_app(host="0.0.0.0", port=6006, reload=True, open_browser_flag=True):
    """
    Run the FastAPI application
    """
    print(f"Starting the application on http://{host}:{port}")
    
    if open_browser_flag:
        # Open browser after a short delay
        Timer(2, open_browser, args=[port]).start()
    
    # Run the application
    uvicorn.run("app:app", host=host, port=port, reload=reload)

def main():
    parser = argparse.ArgumentParser(description="Run the FastAPI application")
    parser.add_argument("--host", default="0.0.0.0", help="Host to run the application on")
    parser.add_argument("--port", type=int, default=6006, help="Port to run the application on")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    
    args = parser.parse_args()
    
    # Check if setup.py has been run
    required_dirs = ["static", "uploads", "results", "temp", "services", "routers"]
    missing_dirs = [d for d in required_dirs if not os.path.exists(d)]
    
    if missing_dirs:
        print(f"The following required directories are missing: {', '.join(missing_dirs)}")
        print("Please run setup.py first to set up the project structure.")
        response = input("Do you want to run setup.py now? (y/n): ")
        if response.lower() == 'y':
            import setup
            setup.setup_project()
        else:
            print("Aborted.")
            return
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("Warning: .env file not found. API keys may not be configured.")
        print("You can create a .env file manually or run setup.py to create a template.")
    
    # Run the application
    run_app(
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
        open_browser_flag=not args.no_browser
    )

if __name__ == "__main__":
    main()
