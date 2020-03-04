import os
import time

import requests
from loguru import logger

import synology_auth as syn


class FileStation:
    def __init__(self, ip_address, port, username, password):

        self.session = syn.Authentication(ip_address, port, username, password)

        self._md5_calc_taskid = ""
        self._md5_calc_taskid_list = []
        self.request_data = self.session.request_data

        self.session.login("FileStation")
        self.session.get_api_list("FileStation")

        self.file_station_list = self.session.app_api_list
        self._sid = self.session.sid
        self.base_url = self.session.base_url

    def logout(self):
        self.session.logout("FileStation")

    def start_md5_calc(self, file_path=None):
        api_name = "SYNO.FileStation.MD5"
        info = self.file_station_list[api_name]
        api_path = info["path"]
        req_param = {"version": info["maxVersion"], "method": "start"}

        if file_path is None:
            logger.error(f"[start_md5_calc] file_path is needed!")
            return False

        req_param["file_path"] = file_path

        response = self.request_data(api_name, api_path, req_param)

        if response["success"] is False:
            logger.error(f"[start_md5_calc] Server Error\nResponse: {response}")
            return False

        self._md5_calc_taskid = response["data"]["taskid"]
        self._md5_calc_taskid_list.append(self._md5_calc_taskid)

        logger.info(
            f"[start_md5_calc] Success!\ntaskid: {self._md5_calc_taskid}\nResponse: {response}"
        )

        return self._md5_calc_taskid

    def get_md5_status(self, taskid=None):
        api_name = "SYNO.FileStation.MD5"
        info = self.file_station_list[api_name]
        api_path = info["path"]
        req_param = {"version": info["maxVersion"], "method": "status"}

        if taskid:
            req_param["taskid"] = f'"{taskid}"'
        elif self._md5_calc_taskid:
            req_param["taskid"] = f'"{self._md5_calc_taskid}"'
        else:
            logger.error(
                f"[get_md5_status] No taskid found!\nHint: Need to run start_md5_calc first."
            )
            return False

        response = self.request_data(api_name, api_path, req_param)

        if response["success"] is False:
            logger.error(f"[get_md5_status] Server Error\nResponse: {response}")
            return False

        if not response["data"]["finished"]:
            logger.info(
                f"[get_md5_status] Hash is not complete.\nWait 20s and check again."
            )
            time.sleep(20)
            md5_hash = self.get_md5_status(taskid=taskid)
        else:
            md5_hash = response["data"]["md5"]

        logger.info(
            f"[get_md5_status] Success!\ntaskid: {self._md5_calc_taskid}\nResponse: {response}"
        )

        return md5_hash

    def get_file_md5(self, file_path=None):
        # Start calculate md5 hash
        taskid = self.start_md5_calc(file_path)
        # Get md5 hash
        md5_hash = self.get_md5_status(taskid)

        if md5_hash:
            logger.success(
                f"[get_file_md5] Success!\nfile: {file_path}\nmd5: {md5_hash}"
            )
            return md5_hash

        logger.error(f"[get_file_md5] Faild!\nfile: {file_path}")

        return False

    def upload_file(self, dest_path, file_path):
        api_name = "SYNO.FileStation.Upload"
        info = self.file_station_list[api_name]
        api_path = info["path"]
        filename = os.path.basename(file_path)

        url = f"{self.base_url}{api_path}?api={api_name}&version={info['minVersion']}&method=upload&_sid={self._sid}"

        args = {"path": dest_path, "create_parents": "true", "overwrite": "true"}

        response = requests.get(
            url,
            data=args,
            files={
                "file": (filename, open(file_path, "rb"), "application/octet-stream")
            },
        )

        if response.status_code == 200 and response.json()["success"]:
            logger.success(
                f"[upload_file] Success!\nfile: {file_path}\nupload dir: {dest_path}"
            )
            return True
        logger.error(
            f"[upload_file] Faild\nfile: {file_path}\nResponse: {response.text}"
        )
        return False
