import os
import requests
import socks
import time
from datetime import datetime

PROXY_LIST = {"https":"socks5://127.0.0.1:9150"}
REGEX_PATTERN = "^/(notifu|list|rm|edit|settz)\s(\d{2}[.]\d{2}[.]\d{4}\s|\d{2}[.]\d{2}\s|)(\d{2}[:]\d{2}\s|\d{4}\s)(.+$)"

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
        self.notifu = {}
        
    def _get_incoming(self):
        params = {
            'timeout': 1,
        }

        if self.update_id:
            params['offset'] = self.update_id + 1

        r = requests.post("https://api.telegram.org/bot%s/getUpdates" % self.token, params=params, timeout=10, proxies=PROXY_LIST)
        if r.ok:
            response = r.json()
            # print(response)

            if response['result']:
                for item in response['result']:
                    self.update_id = item['update_id']
                    if 'message' in item:
                        self.incoming.append(item['message'])
                    elif 'edited_message' in item:
                        self.incoming.append(item['edited_message'])
                
    def start(self, timeout=2):
        while True:
            # TODO: add time checking and notification logic
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
            # TODO: обрабатывать ошибки
            print("Can't send message")
    
    def _notify(self, message):
        print("Writing info about notification")
        # TODO: сохранение настроек уведомления (написать для него отдельный класс)
        timestamp, message_text = parse_notifu(message['text'])
        chat_id = message['chat']['id']
        if chat_id not in self.notifu.keys():
            self.notifu[chat_id] = {}
        self.notifu[chat_id][timestamp] = message_text
        reply_text = "Уведомление создано"
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
        pass

def parse_notifu(text):
    import re
    match = re.search(REGEX_PATTERN, text)

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
    return (dt.timestamp(), text_str)


if __name__ == "__main__":
    bot = Bot(os.environ["NOTIFU_TOKEN"])
    bot.start()