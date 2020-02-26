import os
import datetime

from loguru import logger
from dotenv import load_dotenv

import synology_filestation as filestation

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
    compress_file = folder + ".tar"
    cmd = f"tar -C {IMAGE_PATH} -cf {compress_file} {folder_name}"
    logger.info("compressing files")
    returned_value = os.system(cmd)
    logger.info("compressing done")
    if returned_value == 0:
        return compress_file
    return False


def main():
    # Get folder name
    folder_name, folder_path = get_file_name(IMAGE_PATH)
    # Compress folder
    compressed_file = compress_folder(folder_path, folder_name)
    # Login NAS
    uploader = filestation.FileStation(URL, PORT, USER, PASSWORD)
    # Upload file
    response = uploader.upload_file(
        dest_path=NAS_PATH, file_path=compressed_file, overwrite="False"
    )
    logger.info(f"[Upload Response] {response}")
    # Use md5 hash to check local file is same as upload file
    # Delete local image file (folder and .tar file) if NAS stored them
    # Logout NAS
    uploader.logout()


if __name__ == "__main__":
    main()
