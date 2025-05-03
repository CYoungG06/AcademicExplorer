import os
import time
import uuid
import requests
import zipfile
import tempfile
import shutil

# 配置信息
with open("api.txt", "r", encoding="utf-8") as f:
    API_KEY = f.read().strip()

API_URL = "https://mineru.net/api/v4"
BEARER_TOKEN = f"Bearer {API_KEY}"
PDF_FOLDER = "test_papers_1"
OUTPUT_FOLDER = "mdss"

# API端点
BATCH_URL = f"{API_URL}/file-urls/batch"
RESULTS_URL = f"{API_URL}/extract-results/batch"

headers = {
    "Content-Type": "application/json",
    "Authorization": BEARER_TOKEN
}

def process_pdfs():
    # 1. 收集所有PDF文件
    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print("未找到PDF文件")
        return

    # 2. 准备请求数据
    files_data = []
    for pdf_file in pdf_files:
        files_data.append({
            "name": pdf_file,
            "is_ocr": True,
            "data_id": str(uuid.uuid4())
        })

    # 3. 发送初始请求获取上传URL
    payload = {
        "enable_formula": True,
        "language": "ch",
        "layout_model": "doclayout_yolo",
        "enable_table": True,
        "files": files_data
    }

    try:
        response = requests.post(BATCH_URL, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"初始化请求失败: {response.status_code}")
            return

        result = response.json()
        print(result)
        # if result.get("code") != 200:
        #     print(f"API错误: {result.get('msg')}")
        #     return

        batch_id = result["data"]["batch_id"]
        upload_urls = result["data"]["file_urls"]

        # 4. 上传所有PDF文件
        for idx, file_info in enumerate(files_data):
            pdf_path = os.path.join(PDF_FOLDER, file_info["name"])
            with open(pdf_path, "rb") as f:
                upload_res = requests.put(upload_urls[idx], data=f)
                if upload_res.status_code != 200:
                    print(f"上传失败: {file_info['name']}")
                    return
                print(f"上传成功: {file_info['name']}")

        print("所有文件上传成功，等待处理...")

        # 5. 轮询处理结果
        while True:
            time.sleep(3)
            res = requests.get(f"{RESULTS_URL}/{batch_id}", headers=headers)
            res_data = res.json()
            
            # if res_data.get("code") != 200:
            #     print(f"查询失败: {res_data.get('msg')}")
            #     continue

            batch_status = res_data["data"]
            all_done = True
            results = []

            for item in batch_status["extract_result"]:
                if item["state"] == "done":
                    results.append(item)
                elif item["state"] == "failed":
                    print(f"处理失败: {item['file_name']} - {item['err_msg']}")
                    return
                else:
                    all_done = False

            if all_done:
                print("所有文件处理完成")
                break

        # 6. 下载和处理结果
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        
        for item in results:
            if not item.get("full_zip_url"):
                continue

            # 下载ZIP文件
            zip_url = item["full_zip_url"]
            file_name = item["file_name"]
            print(f"正在处理: {file_name}")

            # 创建临时目录
            with tempfile.TemporaryDirectory() as tmp_dir:
                zip_path = os.path.join(tmp_dir, "temp.zip")
                
                # 下载文件
                zip_res = requests.get(zip_url)
                if zip_res.status_code != 200:
                    print(f"下载失败: {file_name}")
                    continue
                
                with open(zip_path, "wb") as f:
                    f.write(zip_res.content)

                # 解压文件
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(tmp_dir)

                # 寻找解压目录
                extracted_dir = None
                for root, dirs, files in os.walk(tmp_dir):
                    if "full.md" in files and "images" in dirs:
                        extracted_dir = root
                        break

                if not extracted_dir:
                    print(f"文件结构异常: {file_name}")
                    continue

                # 准备输出目录
                base_name = os.path.splitext(file_name)[0]
                output_dir = os.path.join(OUTPUT_FOLDER, base_name)
                os.makedirs(output_dir, exist_ok=True)

                # 处理Markdown文件
                md_source = os.path.join(extracted_dir, "full.md")
                md_target = os.path.join(output_dir, f"{base_name}.md")
                shutil.copy(md_source, md_target)

                # 处理图片目录
                images_source = os.path.join(extracted_dir, "images")
                images_target = os.path.join(output_dir, "images")
                if os.path.exists(images_target):
                    shutil.rmtree(images_target)
                shutil.copytree(images_source, images_target)

                print(f"处理完成: {file_name}")

    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    process_pdfs()