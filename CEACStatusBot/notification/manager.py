import json
import os
import datetime

import pytz

from CEACStatusBot.captcha import CaptchaHandle, OnnxCaptchaHandle
from CEACStatusBot.request import query_status

from .handle import NotificationHandle

class NotificationManager:
    def __init__(
        self,
        location: str,
        number: str,
        passport_number: str,
        surname: str,
        captchaHandle: CaptchaHandle = OnnxCaptchaHandle("captcha.onnx"),
    ) -> None:
        self.__handleList = []
        self.__location = location
        self.__number = number
        self.__captchaHandle = captchaHandle
        self.__passport_number = passport_number
        self.__surname = surname
        self.__status_file = "status_record.json"

    def _get_local_time(self) -> datetime.datetime:
        try:
            TIMEZONE = os.environ["TIMEZONE"]
            localTimeZone = pytz.timezone(TIMEZONE)
            return datetime.datetime.now(localTimeZone)
        except (pytz.exceptions.UnknownTimeZoneError, KeyError):
            print("TIMEZONE Error, use default")
            return datetime.datetime.now()

    def addHandle(self, notificationHandle: NotificationHandle) -> None:
        self.__handleList.append(notificationHandle)

    def send(self) -> None:
        res = query_status(
            self.__location,
            self.__number,
            self.__passport_number,
            self.__surname,
            self.__captchaHandle,
        )
        if not res["success"]:
            raise RuntimeError("Query status failed, no notification sent.")
        current_status = res["status"]
        current_last_updated = res["case_last_updated"]
        print(f"Current status: {current_status} - Last updated: {current_last_updated}")
        # Load the previous statuses from the file
        statuses = self.__load_statuses()

        # Check if the current status is different from the last recorded status
        if not statuses or current_status != statuses[-1].get("status", None) or current_last_updated != statuses[-1].get("last_updated", None):
            self.__save_current_status(current_status, current_last_updated)
            self.__send_notifications(res)
        else:
            print("Status unchanged. No notification sent.")
            localTime = self._get_local_time()
            if localTime.hour in (8, 17):
                print(f"Sending daily digest email at hour {localTime.hour}")
                self.__send_email_only(res)

    def __load_statuses(self) -> list:
        if os.path.exists(self.__status_file):
            with open(self.__status_file, "r") as file:
                return json.load(file).get("statuses", [])
        return []

    def __save_current_status(self, status: str, last_updated: str) -> None:
        statuses = self.__load_statuses()
        statuses.append({
            "status": status,
            "last_updated": last_updated,
            "date": datetime.datetime.now().isoformat()
        })

        with open(self.__status_file, "w") as file:
            json.dump({"statuses": statuses}, file)

    def __send_notifications(self, res: dict) -> None:
        for notificationHandle in self.__handleList:
            notificationHandle.send(res)

    def __send_email_only(self, res: dict) -> None:
        from .email import EmailNotificationHandle
        sent = False
        for handle in self.__handleList:
            if isinstance(handle, EmailNotificationHandle):
                handle.send(res)
                sent = True
        if not sent:
            print("No EmailNotificationHandle registered. Check FROM/TO/PASSWORD in secrets.")
