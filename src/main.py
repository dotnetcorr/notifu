import os
import time
from datetime import datetime, timedelta
import traceback

import requests
import socks

from infrastructure.logger_factory import LoggerFactory
from infrastructure.exceptions import LateTimeException
from infrastructure import strings
from notifu import Notifu, Notification


if bool(int(os.environ.get("NOTIFU_USE_PROXY", "0"))):
    PROXY_LIST = {"https":"socks5://127.0.0.1:9150"}
else:
    PROXY_LIST = None


class Bot:

    def __init__(self, token):
        self.token = token
        self.incoming = []
        self.update_id = None
        self.routes = {
            "/start": self._start,
            "/help": self._help,
            "/notifu": self._add_notification,
            "/list": self._list,
            "/rm": self._rm,
            "/edit": self._edit,
            "/settz": self._set_time_zone
        }
        self.notifu = {}    # { chat_id : notifu_obj }
        self.__logger = LoggerFactory.create_logger(name=self.__class__.__name__)
        for f in os.listdir("storage"):
            obj = Notifu.from_pickle(f)
            if obj:
                self.notifu[obj.chat_id] = obj
        print("Restored {0} notifu".format(len(self.notifu.keys())))
        
    def _get_incoming(self):
        params = {
            'timeout': 3,
        }

        if self.update_id:
            params['offset'] = self.update_id + 1

        try:
            # self.__logger.info("Trying get incoming messages")
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
        except:
            self.__logger.error(traceback.format_exc())
    
    def _handle_notifications(self):
        for chat_id, notifu_item in self.notifu.items():
            if notifu_item.closest_ts <= time.time():
                notifications = notifu_item.get_notifications(time.time())
                for notification in notifications:
                    self._send_message(chat_id, notification.text)

    def start(self, timeout=1):
        while True:
            # TODO: handle timezones correct
            self._handle_notifications()
            self._get_incoming()

            if self.incoming:
                for message in self.incoming:
                    chat_id = message['chat']['id']
                    if chat_id not in self.notifu.keys():
                        self.notifu[chat_id] = Notifu(chat_id=chat_id)
                    command = message['text'].split()[0]
                    message_text = ' '.join(message['text'].split()[1:])
                    if command in self.routes.keys():
                        self.routes[command](self.notifu[chat_id], message_text)
                self.incoming = []
            else:
                time.sleep(timeout)

    def _send_message(self, chat_id, message):
        payload = {
            "chat_id": chat_id,
            "text": message
        }
        try:
            result = requests.post("https://api.telegram.org/bot%s/sendMessage" % self.token, params=payload, timeout=10, proxies=PROXY_LIST)
            if not result.ok:
                # TODO: handle errors
                self.__logger.error(result.text)
        except:
            self.__logger.error(traceback.format_exc())
    
    def _add_notification(self, notifu, message):
        # TODO: take care of this spaghetti code
        self.__logger.info("Writing info about notification")
        try:
            notification = Notification.from_message(message)
            dt_str = notifu.add_notification(notification)
            reply_text = strings.SUCCESS_ADDED_NOTIFICATION.format(dt_str)
        except LateTimeException:
            self.__logger.error(traceback.format_exc())
            reply_text = strings.ERR_OVERTIME
        except Exception:
            # TODO: catch different types of exception (no_dt_ex and dt_not_valid_ex)
            self.__logger.error(traceback.format_exc())
            reply_text = strings.ERR_TRICKY
        finally:
            self._send_message(notifu.chat_id, reply_text)

    def _list(self, notifu, message):
        notifications = notifu.get_all_notifications()
        if len(notifications) > 0:
            reply_text = '\n'.join(["{0}. {1}".format(n+1, str(o)) for n, o in enumerate(notifications)])
        else:
            reply_text = strings.WARN_NO_NOTIFICATIONS
        self._send_message(notifu.chat_id, reply_text)

    
    def _rm(self, notifu, message):
        # TODO: remove item with n-1 index (because for user it starts from 1)
        idx = int(message)
        removed = notifu.remove_notification(idx-1)
        if removed:
            reply_text = strings.NOTIFICATION_REMOVED.format(removed)
        else:
            reply_text = strings.DEFAULT_ERROR
        self._send_message(notifu.chat_id, reply_text)
        
    
    def _edit(self, notifu, message):
        pass

    def _set_time_zone(self, notifu, message):
        tz_str = message
        # TODO: handle possible errors from timezone parsing
        try:
            notifu.set_timezone(tz_str)
            reply_text = strings.SUCCESS_SET_TZ.format(notifu.get_timezone_str())
        # TODO: catch right exception
        except Exception: 
            reply_text = strings.ERR_SET_TZ
        finally:
            self._send_message(notifu.chat_id, reply_text)

    def _start(self, notifu, message):
        dt = datetime.today() + timedelta(seconds=120)
        dt_str = dt.strftime("%d.%m %H:%M")
        reply_text = strings.START_MESSAGE.format(dt_str) 
        self._send_message(notifu.chat_id, reply_text)
        if notifu.is_tz_default():
            # TODO: find more clever way to warn user about default timezone
            self._warn_default_tz(notifu.chat_id)
    
    def _help(self, notifu, message):
        reply_text = strings.HELP_MESSAGE.format(notifu.get_timezone_str())
        self._send_message(notifu.chat_id, reply_text)

    def _warn_default_tz(self, chat_id):
        self._send_message(chat_id, strings.DEFAULT_TZ_WARN)


if __name__ == "__main__":
    bot = Bot(os.environ["NOTIFU_TOKEN"])
    bot.start()