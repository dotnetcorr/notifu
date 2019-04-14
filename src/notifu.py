from datetime import datetime
import pickle
import time
import traceback

import pytz

from infrastructure.logger_factory import LoggerFactory
from infrastructure.exceptions import LateTimeException

MAX_TIME = datetime(3000,12,31).timestamp() #   donkey or emir or me
REGEX_PATTERN = r"^(\d{2}[.]\d{2}[.]\d{4}\s|\d{2}[.]\d{2}\s|)(\d{2}[:]\d{2}\s|\d{4}\s)(.+$)"

common_logger = LoggerFactory.create_logger("Notifu")

class Notifu:
    """
    Container for notifications
    """
    def __init__(self, chat_id, timezone=pytz.utc):
        self.chat_id = chat_id
        self.closest_ts = MAX_TIME
        self.__notifications = []
        self.__timezone = timezone
        self.__is_tz_default = True

    def _resort_array(self):
        self.__notifications.sort(key=lambda n: n.timestamp)
        self.closest_ts = self.__notifications[0].timestamp
        self.__store()

    def add_notification(self, notification):
        notification.set_timezone(self.__timezone)
        # TODO: check datetime validity (if notification is later than now)
        if notification.timestamp <= time.time():
            # TODO: Write specific exception
            raise LateTimeException("Too late")
        self.__notifications.append(notification)
        self._resort_array()
        return notification.datetime.strftime("%d.%m.%Y %H:%M UTC%z")

    def remove_notification(self, index):
        # remove by index in notifications array
        notification = self.__notifications.pop(index)
        self.__store()
        return notification

    def get_notifications(self, timestamp):
        # pop notifications behind timestamp, return them and update closest_ts
        # TODO: handle periods (change timestamp instead removing)
        notifications_list = []
        for notification in list(self.__notifications):
            if notification.datetime.timestamp() <= timestamp:
                notifications_list.append(notification)
                self.__notifications.remove(notification)
            else:
                break
        if len(notifications_list) > 0:
            self.__store()
        return notifications_list

    def get_all_notifications(self):
        return self.__notifications

    def get_timezone_str(self):
        return self.__timezone.zone

    def is_tz_default(self):
        return self.__is_tz_default

    def set_timezone(self, timezone):
        # TODO: return offset from UTC as +[-]XX
        self.__timezone = pytz.timezone(timezone)
        self.__is_tz_default = False
        self.__store()

    def __store(self):
        try:
            with open("storage/{0}.pkl".format(self.chat_id), 'wb') as f_out:
                pickle.dump(self, f_out)
        except Exception:
            common_logger.error(traceback.format_exc())
            raise
    
    @staticmethod
    def from_pickle(filename):
        with open("storage/"+filename, 'rb') as f_in:
            return pickle.load(f_in)


class Notification:
    def __init__(self, datetime, text, period=[]):
        self.datetime = datetime
        self.timestamp = datetime.timestamp()
        self.text = text
        self.period = period

    def set_timezone(self, tz):
        self.datetime = tz.localize(self.datetime)
        self.timestamp = self.datetime.timestamp()
    
    def __str__(self):
        return self.datetime.strftime("%d.%m.%Y %H:%M UTC%z") + ' ' + self.text

    @staticmethod
    def from_message(text):
        import re
        match = re.search(REGEX_PATTERN, text)

        if match is None:
            print("Parsing failed")
            # Throw something
            return None
        # TODO: handle cases with date/time overflow (e.g. 25:60)
        date_str = match.group(1).strip()
        # TODO: remove hardcode to pick current year
        if len(date_str) == 0:
            date_ = datetime.today()
        elif len(date_str) == 5:
            date_ = datetime.strptime(date_str+"2019", "%d.%m%Y")
        else:
            date_ = datetime.strptime(date_str, "%d.%m.%Y")

        time_ = datetime.strptime(match.group(2).strip(), "%H:%M")
        text_str = match.group(3).strip()
        dt = datetime.combine(date_.date(), time_.time())
        return Notification(datetime=dt, text=text_str)