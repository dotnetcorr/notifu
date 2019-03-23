import os
import requests
import socks
import time
from datetime import datetime, timedelta

from logger_factory import LoggerFactory

PROXY_LIST = {"https":"socks5://127.0.0.1:9150"}
REGEX_PATTERN = r"^/(notifu|list|rm|edit|settz)\s(\d{2}[.]\d{2}[.]\d{4}\s|\d{2}[.]\d{2}\s|)(\d{2}[:]\d{2}\s|\d{4}\s)(.+$)"
MAX_TIME = datetime(3000,12,31).timestamp() #   donkey or emir or me 
START_MESSAGE = u"""Noti-Fu создан для того, чтобы ты не забыл что-нибудь важное, юзернейм.\n
Чтобы создать напоминание, используй команду \n\"/notifu [дата] [время] [сообщение]\".\n
где дата - день.месяц или день.месяц.год,
    время в 24-часовом формате\n
Например: /notifu {0} Не забыть покормить котика."""

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
        # TODO: придумать другую структуру. В текущей сложно обращаться к отдельному напоминанию
        self.notifu = {}
        self._nearest_timestamps = {}
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
        for chat_id, timestamp in self._nearest_timestamps.items():
            if timestamp <= time.time():
                self._send_message(chat_id, self.notifu[chat_id].pop(timestamp))
                self._set_nearest_timestamp(chat_id)
            # TODO: remove current timestamp from notifu
            # NB! maybe saving current timestamp for snooze is better
            # TODO: add next nearest timestamp to chat_id

    def _set_nearest_timestamp(self, chat_id):
        min_ts = MAX_TIME
        for timestamp in self.notifu[chat_id].keys():
            if timestamp < min_ts:
                min_ts = timestamp
        self._nearest_timestamps[chat_id] = min_ts

    def _add_notification(self, chat_id, timestamp, text):
        self.notifu[chat_id][timestamp] = text
        if timestamp < self._nearest_timestamps.pop(chat_id, MAX_TIME):
            self._nearest_timestamps[chat_id] = timestamp

    def start(self, timeout=2):
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
        print("Writing info about notification")
        chat_id = message['chat']['id']
        dt, message_text = parse_notifu(message['text'])
        if dt is None:
            reply_text = u"Хорошая попытка... нет."
        elif is_datetime_valid(dt):
            if chat_id not in self.notifu.keys():
                self.notifu[chat_id] = {}
            self._add_notification(chat_id, dt.timestamp(), message_text)
            dt_str = dt.strftime("%d.%m.%Y %H:%M")
            reply_text = u"Напоминание на {0} успешно создано.".format(dt_str) 
        else:
            reply_text = u'Это надо было делать раньше, а раньше уже закончилось, юзернейм.'
        self._send_message(chat_id, reply_text)

    def _list(self, message):
        pass
    
    def _rm(self, message):
        pass
    
    def _edit(self, message):
        pass

    def _set_time_zone(self, message):
        pass

    def _start(self, message):
        chat_id = message['chat']['id']
        dt = datetime.today() + timedelta(seconds=120)
        dt_str = dt.strftime("%d.%m %H:%M")
        reply_text = START_MESSAGE.format(dt_str) 
        self._send_message(chat_id, reply_text)
        

def parse_notifu(text):
    import re
    match = re.search(REGEX_PATTERN, text)

    if match is None:
        print("Parsing failed")
        # Throw something
        return (None, None)
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
    return (dt, text_str)

def is_datetime_valid(dt):
    return dt > datetime.today()

if __name__ == "__main__":
    bot = Bot(os.environ["NOTIFU_TOKEN"])
    bot.start()