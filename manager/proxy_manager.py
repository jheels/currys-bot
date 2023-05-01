from embeds import now
import random
import requests

class ProxyManager:
    def __init__(self, proxy_list: str):
        self.proxy_list = proxy_list
        self.proxies = []

    def format_proxy(self, proxy: str):
        try:
            proxy = proxy.strip("\n").split(":")
            proxy = f"http://{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}"
            return proxy
        except IndexError:
            print(f"[{now()}] Error formatting proxy! Switching to Local IP...")


    def read_proxies(self):
        try:
            response = requests.get(f"")
            if response.status_code == 200:
                response = response.text.split("\n")
                self.proxies = [self.format_proxy(proxy) for proxy in response]
        except requests.exceptions.RequestException:
            print(f"[{now()}] Error grabbing {self.proxy_list}.txt! Switching to Local IP...")

        if not len(self.proxies):
            print(f"[{now()}] {self.proxy_list}.txt Empty! Switching to Local IP...")

    
    def assign_proxy(self) -> str:
        if len(self.proxies):
            return random.choice(self.proxies)
