from colorama import Fore, init, Style
from ssl import SSLEOFError
from socket import gaierror
from embeds import now
import time
import requests
import asyncio
import pysftp
import logging
from helheim.exceptions import (
    HelheimRuntimeError,
    HelheimSolveError
)

init()

def async_exception_handler(func):
    async def wrapper(self, *args, **kwargs):
        while True:
            try:
                delay = round(self.increase_delay(), 2)
                return await func(self, *args, **kwargs)
            except requests.exceptions.Timeout:
                print(f"Timeout Error - Retrying in {delay}...")
                asyncio.sleep(delay)
            except requests.exceptions.ConnectionError:
                print(f"Connection Error - Retrying in {delay}...")
                asyncio.sleep(delay)
            except requests.exceptions.RequestException:
                print(f"General Request Error - Retrying in {delay}...")
                asyncio.sleep(delay)
            except pysftp.exceptions.ConnectionException:
                print(f"SFTP Connection Error - Retrying in {delay}...")
                asyncio.sleep(delay)
            except IOError:
                print("File/Path does not exist")
                break
    return wrapper

def request_exception_handler(func):
    def inner_function(self, *args, **kwargs):
        while True:
            try:
                if self.count != 3:
                    self.count += 1
                    val = func(self, *args, **kwargs)
                    return val
                logging.warning(f"{Fore.RED}[{now()}] [CURRYS {self.mode:<7}]  [{self.user_id}] [{self.pid:<3}] Max Task Retry Attempts - Stopping...{Style.RESET_ALL}")
                return 
            except requests.exceptions.Timeout:
                logging.warning(f"{Fore.RED}[{now()}] [CURRYS {self.mode:<7}]  [{self.user_id}] [{self.pid:<3}] Request Timeout - Restarting...{Style.RESET_ALL}")
                time.sleep(self.delay)
            except (requests.exceptions.SSLError, SSLEOFError):
                logging.warning(f"{Fore.RED}[{now()}] [CURRYS {self.mode:<7}] [{self.user_id}] [{self.pid:<3}] SSL EOF Error - Restarting...{Style.RESET_ALL}")
                time.sleep(self.delay)
            except (requests.exceptions.ProxyError, requests.exceptions.ConnectionError, gaierror):
                logging.warning(f"{Fore.MAGENTA}[{now()}] [CURRYS {self.mode:<7}] [{self.user_id}] [{self.pid:<3}] Connection Error - Restarting...{Style.RESET_ALL}")
                time.sleep(self.delay)
            except requests.exceptions.RequestException:
                logging.warning(f"{Fore.MAGENTA}[{now()}] [CURRYS {self.mode:<7}] [{self.user_id}] [{self.pid:<3}] Request Error - Restarting...{Style.RESET_ALL}")
                time.sleep(self.delay)
            except IndexError:
                logging.warning(f"{Fore.RED}[{now()}] [CURRYS {self.mode:<7}] [{self.user_id}] [{self.pid:<3}] Invalid Postcode - Stopping..." + Style.RESET_ALL)
                time.sleep(self.delay)
                return
            except (HelheimRuntimeError, HelheimSolveError):
                logging.warning(f"{Fore.MAGENTA}[{now()}] [CURRYS {self.mode:<7}] [{self.user_id}] [{self.pid:<3}] Cloudflare Error - Stopping...{Style.RESET_ALL}")
                return
    return inner_function