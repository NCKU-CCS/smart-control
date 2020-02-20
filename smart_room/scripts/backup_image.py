import os
import datetime

from synology_api import filestation
from loguru import logger
from dotenv import load_dotenv


load_dotenv()


URL = os.environ.get("URL", "localhost")
PORT = os.environ.get("PORT", "5000")
USER = os.environ.get("NAS_USER", "admin")
PASSWORD = os.environ.get("NAS_PASSWORD", "password")
IMAGE_PATH = os.environ.get("IMAGE_PATH", "/home/image")
NAS_PATH = os.environ.get("NAS_PATH", "/image")

def get_file_name(path):
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    file_name = yesterday.strftime("%Y-%m-%d")
    file_path = os.path.join(path, file_name)
    return file_name, file_path

def compress_folder(folder, folder_name):
    compress_file = folder + '.tar'
    cmd = f"tar -C {IMAGE_PATH} -cvf {compress_file} {folder_name}"
    returned_value = os.system(cmd)
    if returned_value == 0:
        return compress_file
    return False

def main():
    # Get folder name
    folder_name, folder_path = get_file_name(IMAGE_PATH)
    # Compress folder
    compressed_file = compress_folder(folder_path, folder_name)
    # Upload file
    uploader = filestation.FileStation(URL, PORT, USER, PASSWORD)
    response = uploader.upload_file(dest_path=NAS_PATH, file_path=compressed_file, overwrite='False')
    logger.info(f"[Upload Response] {response}")


if __name__ == "__main__":
    main()
