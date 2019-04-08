import os
import requests
import socks
import time
from datetime import datetime, timedelta

from logger_factory import LoggerFactory
from notifu import Notifu, Notification
import strings

PROXY_LIST = {"https":"socks5://127.0.0.1:9150"}
REGEX_PATTERN = r"^/(notifu|list|rm|edit|settz)\s(\d{2}[.]\d{2}[.]\d{4}\s|\d{2}[.]\d{2}\s|)(\d{2}[:]\d{2}\s|\d{4}\s)(.+$)"


class Bot:

    def __init__(self, token):
        self.token = token
        self.incoming = []
        self.update_id = None
        self.routes = {
            "/start": self._start,
            "/notifu": self._notify,
            "/list": self._list,
            "/rm": self._rm,
            "/edit": self._edit,
            "/settz": self._set_time_zone
        }
        self.notifu = {}    # { chat_id : notifu_obj }
        self.__logger = LoggerFactory.create_logger(name=self.__class__.__name__)
        
    def _get_incoming(self):
        params = {
            'timeout': 3,
        }

        if self.update_id:
            params['offset'] = self.update_id + 1

        self.__logger.info("Trying get incoming messages")
        r = requests.post("https://api.telegram.org/bot%s/getUpdates" % self.token, params=params, timeout=10, proxies=PROXY_LIST)
        if r.ok:
            response = r.json()

            if response['result']:
                for item in response['result']:
                    self.update_id = item['update_id']
                    if 'message' in item:
                        self.incoming.append(item['message'])
                    elif 'edited_message' in item:
                        self.incoming.append(item['edited_message'])
    
    def _handle_notifications(self):
        for chat_id, notifu_item in self.notifu.items():
            if notifu_item.closest_ts <= time.time():
                notifications = notifu_item.get_notifications(time.time())
                for notification in notifications:
                    self._send_message(chat_id, notification.text)
            # NB! maybe saving current timestamp for snooze is better

    def start(self, timeout=1):
        while True:
            # TODO: handle timezones correct
            self._handle_notifications()
            self._get_incoming()

            if self.incoming:
                for message in self.incoming:
                    command = message['text'].split()[0]
                    if command in self.routes.keys():
                        self.routes[command](message)
                self.incoming = []
            else:
                time.sleep(timeout)

    def _send_message(self, chat_id, message):
        payload = {
            "chat_id": chat_id,
            "text": message
        }
        result = requests.post("https://api.telegram.org/bot%s/sendMessage" % self.token, params=payload, timeout=10, proxies=PROXY_LIST)
        if not result.ok:
            # TODO: handle errors
            print("Can't send message")
    
    def _notify(self, message):
        # TODO: take care of this spaghetti code
        print("Writing info about notification")
        chat_id = message['chat']['id']
        try:
            notification = Notification.from_message(message['text'])
            notifu = self.notifu.setdefault(chat_id, Notifu(chat_id=chat_id))
            # self.notifu[chat_id].add_notification(notification)
            notifu.add_notification(notification)
            dt_str = notification.datetime.strftime("%d.%m.%Y %H:%M")
            reply_text = strings.SUCCESS_ADDED_NOTIFICATION.format(dt_str)
        except Exception:
            # TODO: catch different types of exception (no_dt_ex and dt_not_valid_ex)
            reply_text = strings.ERR_TRICKY
        finally:
            self._send_message(chat_id, reply_text)

    def _list(self, message):
        pass
    
    def _rm(self, message):
        pass
    
    def _edit(self, message):
        pass

    def _set_time_zone(self, message):
        chat_id = message['chat']['id']
        tz_str = message['text'].split(' ')[-1]
        # TODO: handle possible errors from timezone parsing
        self.notifu.setdefault(chat_id, Notifu(chat_id=chat_id))
        try:
            self.notifu[chat_id].set_timezone(tz_str)
            reply_text = strings.SUCCESS_SET_TZ.format(tz_str)
        # TODO: catch right exception
        except Exception: 
            reply_text = strings.ERR_SET_TZ
        finally:
            self._send_message(chat_id, reply_text)

    def _start(self, message):
        chat_id = message['chat']['id']
        dt = datetime.today() + timedelta(seconds=120)
        dt_str = dt.strftime("%d.%m %H:%M")
        reply_text = strings.START_MESSAGE.format(dt_str) 
        self._send_message(chat_id, reply_text)
        if chat_id not in self.notifu.keys():
            self.notifu[chat_id] = Notifu(chat_id=chat_id)
            self._notify_default_tz(chat_id)
    
    def _notify_default_tz(self, chat_id):
        self._send_message(chat_id, strings.TZ_SUGGEST)


if __name__ == "__main__":
    bot = Bot(os.environ["NOTIFU_TOKEN"])
    bot.start()