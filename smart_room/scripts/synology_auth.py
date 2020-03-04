import requests

from loguru import logger


class Authentication:
    def __init__(self, ip_address, port, username, password):
        self._ip_address = ip_address
        self._port = port
        self._username = username
        self._password = password
        self._sid = None
        self._base_url = "http://%s:%s/webapi/" % (self._ip_address, self._port)
        self.full_api_list = {}
        self.app_api_list = {}

    def login(self, application):
        login_api = "auth.cgi?api=SYNO.API.Auth"
        param = {
            "version": "2",
            "method": "login",
            "account": self._username,
            "passwd": self._password,
            "session": application,
            "format": "cookie",
        }

        response = requests.get(self._base_url + login_api, param).json()

        if response["success"] is True:
            self._sid = response["data"]["sid"]
            logger.success(f"[Login] Success\nResponse: {response}")
            return True

        logger.error(f"[Login] Faild\nResponse: {response}")
        return False

    def logout(self, application):
        logout_api = "auth.cgi?api=SYNO.API.Auth"
        param = {"version": "2", "method": "logout", "session": application}

        response = requests.get(self._base_url + logout_api, param)

        if response.json()["success"] is True:
            self._sid = None
            logger.success(f"[Logout] Success\nResponse: {response.text}")
            return True

        logger.error(f"[Logiout] Faild\nResponse: {response.text}")
        return False

    def get_api_list(self, app=None):
        query_path = "query.cgi?api=SYNO.API.Info"
        list_query = {"version": "1", "method": "query", "query": "all"}

        response = requests.get(self._base_url + query_path, list_query).json()

        if app:
            for key in response["data"]:
                if app.lower() in key.lower():
                    self.app_api_list[key] = response["data"][key]
        else:
            self.full_api_list = response["data"]

    def request_data(self, api_name, api_path, req_param, method=None):
        # Convert all booleen in string in lowercase because Synology API is waiting for "true" or "false"
        for key, value in req_param.items():
            if isinstance(value, bool):
                req_param[key] = str(value).lower()

        req_param["_sid"] = self._sid

        if method == "get" or method is None:
            url = ("%s%s" % (self._base_url, api_path)) + "?api=" + api_name
            response = requests.get(url, req_param)
            return response.json()

        if method == "post":
            url = ("%s%s" % (self._base_url, api_path)) + "?api=" + api_name
            response = requests.post(url, req_param)
            return response.json()

        return False

    @property
    def sid(self):
        return self._sid

    @property
    def base_url(self):
        return self._base_url
