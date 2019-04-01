from datetime import datetime

# MAX_TIME = datetime(3000,12,31).timestamp() #   donkey or emir or me

class Notifu:
    """
    Container for notifications
    """
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.notifications = []
        self.closest_ts = None

    def _resort_array(self):
        self.notifications.sort(key=lambda n: n.timestamp)
        self.closest_ts = self.notifications[0].timestamp

    def add_notification(self, timestamp, text, period=[]):
        # add new
        self.notifications.append(Notification(start_ts=timestamp,
                                               text=text,
                                               period=period))
        self._resort_array()

    def remove_notification(self, index):
        # remove by index in notifications array
        del self.notifications[index]
        # maybe there's no need to resort
        self._resort_array()

    def get_notifications(self, timestamp):
        # pop notifications behind timestamp, return them and update closest_ts
        # TODO: handle periods (change timestamp instead removing)
        notifications_list = []
        for notification in list(self.notifications):
            if notification.timestamp <= timestamp:
                notifications_list.append(notification)
                self.notifications.remove(notification)
            else:
                break
        return notifications_list
    
class Notification:
    def __init__(self, start_ts, text, period=[]):
        self.timestamp = start_ts
        self.text = text
        self.period = period