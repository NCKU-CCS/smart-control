import os
import datetime
import logging

from synology_api import filestation
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] - %(asctime)s\n%(message)s\n" + ("-" * 70),
    datefmt="%Y-%m-%dT%H:%M:%S",
)


URL = os.environ.get("URL", "localhost")
PORT = os.environ.get("PORT", "5000")
USER = os.environ.get("NAS_USER", "admin")
PASSWORD = os.environ.get("NAS_PASSWORD", "password")
IMAGE_PATH = os.environ.get("IMAGE_PATH", "/home/image")
NAS_PATH = os.environ.get("NAS_PATH", "/image")

def get_file_name(path):
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    file_path = os.path.join(path, yesterday.strftime("%Y-%m-%d"))
    return file_path

def compress_folder(folder):
    compress_file = folder + '.tar'
    cmd = f"tar cvf {compress_file} {folder}"
    returned_value = os.system(cmd)
    if returned_value == 0:
        return compress_file
    return False

def main():
    # Get folder name
    folder_path = get_file_name(IMAGE_PATH)
    # Compress folder
    compressed_file = compress_folder(folder_path)
    # Upload file
    uploader = filestation.FileStation(URL, PORT, USER, PASSWORD)
    response = uploader.upload_file(dest_path=NAS_PATH, file_path=compressed_file, overwrite='False')
    logging.info(f"[Upload Response] {response}")


if __name__ == "__main__":
    main()
