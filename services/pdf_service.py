import os
import time
import uuid
import requests
import zipfile
import tempfile
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PDFProcessor:
    def __init__(self, api_key=None, api_url="https://mineru.net/api/v4"):
        """
        Initialize the PDF processor with API key and URL
        
        Args:
            api_key: MinerU API key (if None, will try to read from api.txt or environment)
            api_url: MinerU API URL
        """
        self.api_key = api_key
        
        # Try to get API key from environment if not provided
        if not self.api_key:
            self.api_key = os.getenv("MINERU_API_KEY")
            
        if not self.api_key:
            raise ValueError("MinerU API key not found. Please provide it or set MINERU_API_KEY environment variable.")
            
        self.api_url = api_url
        self.bearer_token = f"Bearer {self.api_key}"
        self.batch_url = f"{self.api_url}/file-urls/batch"
        self.results_url = f"{self.api_url}/extract-results/batch"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": self.bearer_token
        }
        
    def process_pdfs(self, pdf_folder, output_folder):
        """
        Process PDF files in the specified folder and save results to output folder
        
        Args:
            pdf_folder: Path to folder containing PDF files
            output_folder: Path to folder where results will be saved
            
        Returns:
            List of paths to processed Markdown files
        """
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # 1. Collect all PDF files
        pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')]
        if not pdf_files:
            print("No PDF files found")
            return []

        # 2. Prepare request data
        files_data = []
        for pdf_file in pdf_files:
            files_data.append({
                "name": pdf_file,
                "is_ocr": True,
                "data_id": str(uuid.uuid4())
            })

        # 3. Send initial request to get upload URLs
        payload = {
            "enable_formula": True,
            "language": "ch",
            "layout_model": "doclayout_yolo",
            "enable_table": True,
            "files": files_data
        }

        try:
            response = requests.post(self.batch_url, headers=self.headers, json=payload)
            if response.status_code != 200:
                print(f"Initialization request failed: {response.status_code}")
                return []

            result = response.json()
            batch_id = result["data"]["batch_id"]
            upload_urls = result["data"]["file_urls"]

            # 4. Upload all PDF files
            for idx, file_info in enumerate(files_data):
                pdf_path = os.path.join(pdf_folder, file_info["name"])
                with open(pdf_path, "rb") as f:
                    upload_res = requests.put(upload_urls[idx], data=f)
                    if upload_res.status_code != 200:
                        print(f"Upload failed: {file_info['name']}")
                        continue
                    print(f"Upload successful: {file_info['name']}")

            print("All files uploaded successfully, waiting for processing...")

            # 5. Poll for processing results
            processed_files = []
            while True:
                time.sleep(3)
                res = requests.get(f"{self.results_url}/{batch_id}", headers=self.headers)
                res_data = res.json()
                
                batch_status = res_data["data"]
                all_done = True
                results = []

                for item in batch_status["extract_result"]:
                    if item["state"] == "done":
                        results.append(item)
                    elif item["state"] == "failed":
                        print(f"Processing failed: {item['file_name']} - {item.get('err_msg', 'Unknown error')}")
                    else:
                        all_done = False

                if all_done:
                    print("All files processed")
                    break

            # 6. Download and process results
            for item in results:
                if not item.get("full_zip_url"):
                    continue

                # Download ZIP file
                zip_url = item["full_zip_url"]
                file_name = item["file_name"]
                print(f"Processing: {file_name}")

                # Create temporary directory
                with tempfile.TemporaryDirectory() as tmp_dir:
                    zip_path = os.path.join(tmp_dir, "temp.zip")
                    
                    # Download file
                    zip_res = requests.get(zip_url)
                    if zip_res.status_code != 200:
                        print(f"Download failed: {file_name}")
                        continue
                    
                    with open(zip_path, "wb") as f:
                        f.write(zip_res.content)

                    # Extract files
                    with zipfile.ZipFile(zip_path, "r") as zip_ref:
                        zip_ref.extractall(tmp_dir)

                    # Find extracted directory
                    extracted_dir = None
                    for root, dirs, files in os.walk(tmp_dir):
                        if "full.md" in files and "images" in dirs:
                            extracted_dir = root
                            break

                    if not extracted_dir:
                        print(f"Abnormal file structure: {file_name}")
                        continue

                    # Prepare output directory
                    base_name = os.path.splitext(file_name)[0]
                    output_dir = os.path.join(output_folder, base_name)
                    os.makedirs(output_dir, exist_ok=True)

                    # Process Markdown file
                    md_source = os.path.join(extracted_dir, "full.md")
                    md_target = os.path.join(output_dir, f"{base_name}.md")
                    shutil.copy(md_source, md_target)

                    # Process images directory
                    images_source = os.path.join(extracted_dir, "images")
                    images_target = os.path.join(output_dir, "images")
                    if os.path.exists(images_target):
                        shutil.rmtree(images_target)
                    shutil.copytree(images_source, images_target)

                    processed_files.append(md_target)
                    print(f"Processing completed: {file_name}")

            return processed_files

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return []

# Function to maintain compatibility with original MinerU.py
def process_pdfs_with_env():
    """
    Process PDFs using environment variables for folders
    This maintains compatibility with the original MinerU.py
    """
    pdf_folder = os.getenv("PDF_FOLDER", "test_papers_1")
    output_folder = os.getenv("OUTPUT_FOLDER", "mdss")
    api_key = os.getenv("MINERU_API_KEY")
    
    processor = PDFProcessor(api_key=api_key)
    return processor.process_pdfs(pdf_folder, output_folder)

# For backward compatibility
def process_pdfs():
    return process_pdfs_with_env()

if __name__ == "__main__":
    process_pdfs()
