import os
import datetime
import hashlib
import shutil

from loguru import logger
from dotenv import load_dotenv

import synology_filestation as filestation

load_dotenv()


NAS_URL = os.environ.get("NAS_URL", "localhost")
NAS_PORT = os.environ.get("NAS_PORT", "5000")
NAS_USER = os.environ.get("NAS_USER", "admin")
NAS_PASSWORD = os.environ.get("NAS_PASSWORD", "password")
IMAGE_PATH = os.environ.get("IMAGE_PATH", "/home/image")
NAS_PATH = os.environ.get("NAS_PATH", "/image")


def get_file_name(path):
    previous_interval = datetime.datetime.today() - datetime.timedelta(hours=1)
    file_name = previous_interval.strftime("%Y-%m-%d_%p")
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
    return returned_value


def check_md5(uploader, compressed_file, nas_file):
    local_md5 = cal_local_md5(compressed_file)
    nas_md5 = cal_nas_md5(uploader, nas_file)
    logger.info(f"[check_md5] Calculated\nlocal md5:{local_md5}\nnas md5:{nas_md5}")
    if local_md5 == nas_md5:
        return True
    return False


def cal_local_md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as readfile:
        for chunk in iter(lambda: readfile.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def cal_nas_md5(uploader, fname):
    return uploader.get_file_md5(fname)


def remove_old_file(folder_path, compressed_file):
    logger.info(
        f"[Delete Old File]\nfolder:{folder_path}\ncompressed file:{compressed_file}"
    )
    shutil.rmtree(folder_path, ignore_errors=True)
    os.remove(compressed_file)


def main():
    # Get folder name
    folder_name, folder_path = get_file_name(IMAGE_PATH)
    # Compress folder
    compressed_file = compress_folder(folder_path, folder_name)
    # Login NAS
    uploader = filestation.FileStation(NAS_URL, NAS_PORT, NAS_USER, NAS_PASSWORD)
    # Upload file
    response = uploader.upload_file(dest_path=NAS_PATH, file_path=compressed_file)
    logger.info(f"[Upload Response] {response}")
    # Use md5 hash to check local file is same as upload file
    nas_file = f"{NAS_PATH}/{folder_name}.tar"
    md5_check = check_md5(uploader, compressed_file, nas_file)
    # Delete local image file (folder and .tar file) if NAS stored them
    if md5_check:
        logger.success(f"[md5 check] pass")
        remove_old_file(folder_path, compressed_file)
    else:
        logger.error(f"[md5 check] faild")
    # Logout NAS
    uploader.logout()


if __name__ == "__main__":
    main()
