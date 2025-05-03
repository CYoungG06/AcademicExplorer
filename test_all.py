import os
import sys
import unittest
import requests
import time
import subprocess
import signal
import argparse
from urllib.parse import urljoin

# Default settings
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8000
DEFAULT_TIMEOUT = 30  # seconds

class TestAPIServer:
    """
    Test runner for the API server
    """
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self.server_process = None
    
    def start_server(self):
        """
        Start the API server
        """
        print("Starting API server...")
        
        # Start the server as a subprocess
        self.server_process = subprocess.Popen(
            ["uvicorn", "app:app", "--host", self.host, "--port", str(self.port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create a new process group
        )
        
        # Wait for the server to start
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            try:
                response = requests.get(urljoin(self.base_url, "/api/health"))
                if response.status_code == 200:
                    print(f"Server started successfully at {self.base_url}")
                    return True
            except requests.exceptions.ConnectionError:
                time.sleep(1)
        
        print("Failed to start server within timeout")
        self.stop_server()
        return False
    
    def stop_server(self):
        """
        Stop the API server
        """
        if self.server_process:
            print("Stopping API server...")
            
            # Kill the process group
            try:
                os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(self.server_process.pid), signal.SIGKILL)
            except Exception as e:
                print(f"Error stopping server: {e}")
            
            self.server_process = None
    
    def run_tests(self, test_type="basic"):
        """
        Run the tests
        """
        if test_type == "basic":
            return self.run_basic_tests()
        elif test_type == "api":
            return self.run_api_tests()
        elif test_type == "all":
            basic_result = self.run_basic_tests()
            api_result = self.run_api_tests()
            return basic_result and api_result
        else:
            print(f"Unknown test type: {test_type}")
            return False
    
    def run_basic_tests(self):
        """
        Run basic tests
        """
        print("\n=== Running Basic Tests ===")
        
        # Test health endpoint
        try:
            response = requests.get(urljoin(self.base_url, "/api/health"))
            if response.status_code == 200:
                print("✅ Health check passed")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
        
        # Test system info endpoint
        try:
            response = requests.get(urljoin(self.base_url, "/api/utils/system"))
            if response.status_code == 200:
                print("✅ System info check passed")
            else:
                print(f"❌ System info check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ System info check failed: {e}")
            return False
        
        # Test config info endpoint
        try:
            response = requests.get(urljoin(self.base_url, "/api/utils/config"))
            if response.status_code == 200:
                print("✅ Config info check passed")
            else:
                print(f"❌ Config info check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Config info check failed: {e}")
            return False
        
        print("All basic tests passed!")
        return True
    
    def run_api_tests(self):
        """
        Run API tests using test_api.py
        """
        print("\n=== Running API Tests ===")
        
        # Run test_api.py
        try:
            result = subprocess.run(
                [sys.executable, "test_api.py", "--url", self.base_url, "--health"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ API tests passed")
                return True
            else:
                print(f"❌ API tests failed: {result.returncode}")
                print(result.stdout)
                print(result.stderr)
                return False
        except Exception as e:
            print(f"❌ API tests failed: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Run tests for the API server")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host to run the server on")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to run the server on")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Timeout for server startup")
    parser.add_argument("--test-type", choices=["basic", "api", "all"], default="basic", help="Type of tests to run")
    parser.add_argument("--no-server", action="store_true", help="Don't start the server (assume it's already running)")
    
    args = parser.parse_args()
    
    # Create test runner
    test_runner = TestAPIServer(args.host, args.port, args.timeout)
    
    # Start server if needed
    server_started = True
    if not args.no_server:
        server_started = test_runner.start_server()
    
    # Run tests if server started successfully
    success = False
    if server_started:
        try:
            success = test_runner.run_tests(args.test_type)
        finally:
            # Stop server if we started it
            if not args.no_server:
                test_runner.stop_server()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
