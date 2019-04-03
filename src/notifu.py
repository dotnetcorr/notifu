from datetime import datetime, timezone
import pytz

MAX_TIME = datetime(3000,12,31).timestamp() #   donkey or emir or me
REGEX_PATTERN = r"^/(notifu|list|rm|edit|settz)\s(\d{2}[.]\d{2}[.]\d{4}\s|\d{2}[.]\d{2}\s|)(\d{2}[:]\d{2}\s|\d{4}\s)(.+$)"

class Notifu:
    """
    Container for notifications
    """
    def __init__(self, chat_id, timezone=timezone.utc):
        self.__chat_id = chat_id
        self.__notifications = []
        self.__closest_ts = MAX_TIME
        self.__timezone = timezone

    def _resort_array(self):
        self.__notifications.sort(key=lambda n: n.timestamp)
        self.__closest_ts = self.__notifications[0].timestamp

    def add_notification(self, notification):
        notification.set_timestamp(self.__timezone)
        # TODO: check datetime validity (if notification is later than now)
        if not is_datetime_valid:
            # TODO: Write specific exception
            raise Exception()
        self.__notifications.append(notification)
        self._resort_array

    def remove_notification(self, index):
        # remove by index in notifications array
        del self.__notifications[index]
        # maybe there's no need to resort
        self._resort_array()

    def get_notifications(self, timestamp):
        # pop notifications behind timestamp, return them and update closest_ts
        # TODO: handle periods (change timestamp instead removing)
        notifications_list = []
        for notification in list(self.__notifications):
            if notification.timestamp <= timestamp:
                notifications_list.append(notification)
                self.__notifications.remove(notification)
            else:
                break
        return notifications_list

    def set_timezone(self, timezone):
        # TODO: return offset from UTC as +[-]XX
        self.__timezone = pytz.timezone(timezone)
    

class Notification:
    def __init__(self, datetime, text, timestamp=None, period=[]):
        self.datetime = datetime
        self.timestamp = timestamp
        self.text = text
        self.period = period

    def set_timestamp(self, tz):
        self.timestamp = self.datetime.replace(tzinfo=tz).timestamp()
    
    @staticmethod
    def from_message(text):
        import re
        match = re.search(REGEX_PATTERN, text)

        if match is None:
            print("Parsing failed")
            # Throw something
            return None
        # TODO: handle cases with date/time overflow (e.g. 25:60)
        date_str = match.group(2).strip()   
        # TODO: remove hardcode to pick current year
        if len(date_str) == 0:
            date_ = datetime.today()
        elif len(date_str) == 5:
            date_ = datetime.strptime(date_str+"2019", "%d.%m%Y")
        else:
            date_ = datetime.strptime(date_str, "%d.%m.%Y")

        time_ = datetime.strptime(match.group(3).strip(), "%H:%M")
        text_str = match.group(4).strip()
        dt = datetime.combine(date_.date(), time_.time())
        return Notification(datetime=dt, text=text_str)


def is_datetime_valid(dt):
    return dt > datetime.today()