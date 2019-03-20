import os
import requests
import socks
import time

PROXY_LIST = {"https":"socks5://127.0.0.1:9150"}

class Bot:

    def __init__(self, token):
        self.token = token
        self.incoming = []
        self.routes = {
            "/notifu": self._notify,
            "/list": self._list
        }
        
    def _get_incoming(self):
        params = {
            'timeout': 1,
        }
        r = requests.post("https://api.telegram.org/bot%s/getUpdates" % self.token, params=params, timeout=10, proxies=PROXY_LIST)
        if r.ok:
            response = r.json()
            print(response)

            if response['result']:
                for item in response['result']:
                    self.update_id = item['update_id']
                    if 'message' in item:
                        self.incoming.append(item['message'])
                    elif 'edited_message' in item:
                        self.incoming.append(item['edited_message'])
                
    def start(self, timeout=2):
        while True:
            self._get_incoming()

            # TODO: выяснить, как удалить полученное сообщение из апдейтов
            if self.incoming:
                for message in self.incoming:
                    # TODO: parse command from message text
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
        reply_text = "Уведомление создано"
        self._send_message(message['chat']['id'], reply_text)

    def _list(self, message):
        pass


if __name__ == "__main__":
    bot = Bot(os.environ["NOTIFU_TOKEN"])
    bot.start()