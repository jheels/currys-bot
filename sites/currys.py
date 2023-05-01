from datetime import datetime
from colorama import Fore, init, Style
from embeds import now
import proxy_manager
import logging
import time
import googlemaps
import os
import embeds
import threading
import random   
import cloudscraper
import helheim
import decorators

init()
logging.basicConfig(format='%(message)s')
helheim.auth('')

status = {
    "successful": 0,
    "failed": 0,
    "carted": 0
}
os.system("title JBOT")

def injection(session, response):
    if helheim.isChallenge(session, response):
        return helheim.solve(session, response)
    return response

def update_title_bar(value: str):
    global status

    if "preload" not in value:
        if "success" in value:
            status["successful"] += 1
        elif "failed" in value:
            status["failed"] += 1
        elif "carted" in value:
            status["carted"] += 1
        else:
            for i in status:
                status[i] = 0

    os.system(f'title JBOT - Success: {status["successful"]} / Failed: {status["failed"]} / Carted: {status["carted"]}')

def scraper():
    scraper = cloudscraper.CloudScraper(
        requestPostHook = injection,
        captcha = {
            "provider": "vanaheim",
        },
        browser = {
            "browser": "chrome",
            "platform": "windows",
            "mobile": False
        }
    )
    helheim.wokou(scraper)
    return scraper

class Task:
    def __init__(self, task: dict, profile: dict, settings: dict, user_id: str):
        self.task = task
        self.profile = profile
        self.settings = settings
        self.delay = float(self.settings["retry"])
        self.timeout = float(self.settings["timeout"])
        self.payment_method = self.task["paymentMethod"]
        self.pid = self.task["pid"]
        self.proxy_list = self.task["proxyList"]
        self.proxy_manager = proxymanager.ProxyManager(self.proxy_list)
        self.proxy_manager.read_proxies()
        self.mode = self.task["mode"].upper()
        self.user_id = user_id
        self.count = 0
        os.system(f'title JBOT - Success: {status["successful"]} / Failed: {status["failed"]} / Carted: {status["carted"]}')


    def rotate_proxy(self, session):
        proxy = self.proxy_manager.assign_proxy()
        session.proxies["http"] = proxy
        session.proxies["https"] = proxy
    
    def get_lat_lng(self):
        while True:
            try:
                gmaps = googlemaps.Client("").geocode(self.profile["postCode"])
                
                return gmaps[0]["geometry"]["location"]
            except (googlemaps.exceptions.HTTPError, googlemaps.exceptions.TransportError):
                logging.warning(f"[{now()}] [CURRYS - SYSTEM] [{self.pid:<3}] Geocode Error - Bad Request Retrying...{Style.RESET_ALL}")

    
    def get_session_token(self, session, t_id: int):
        session_token = session.post("https://api.currys.co.uk/store/api/token", timeout=self.timeout)
        
        while session_token.status_code != 200:
            logging.warning(f"{Fore.RED}[{now()}] [CURRYS {self.mode:<7} - {t_id:<3}] [{self.user_id}] [{self.pid:<3}] Error Getting Token - Rate Limit...{Style.RESET_ALL}")
            self.rotate_proxy(session)
            time.sleep(self.delay)
            session_token = session.post("https://api.currys.co.uk/store/api/token", timeout=self.timeout)
            
        else:
            return session_token.json()["bid"]

    
    def add_to_cart(self, session, t_id: int, token: str, pid: str):
        logging.warning(f"{Fore.YELLOW}[{now()}] [CURRYS {self.mode:<7} - {t_id:<3}] [{self.user_id}] [{pid:<3}] Adding to Cart...{Style.RESET_ALL}")
        atc_post = session.post(f"https://api.currys.co.uk/store/api/checkout/baskets/{token}/products", data={"productId": str(pid)}, timeout=self.timeout)
        
        while atc_post.status_code != 200 or atc_post.json()["payload"]["totalQuantity"] == 0:
            logging.warning(f"{Fore.RED}[{now()}] [CURRYS {self.mode:<7} - {t_id:<3}] [{self.user_id}] [{pid:<3}] Error Adding to Cart{Style.RESET_ALL}")
            self.rotate_proxy(session)
            time.sleep(self.delay)
            atc_post = session.post(f"https://api.currys.co.uk/store/api/checkout/baskets/{token}/products", data={"productId": str(pid)}, timeout=self.timeout)
            
        else:
            logging.warning(f"{Fore.LIGHTGREEN_EX}[{now()}] [CURRYS {self.mode:<7} - {t_id:<3}] [{self.user_id}] [{pid:<3}] Successfully Added to Cart{Style.RESET_ALL}")
            update_title_bar("carted")

    
    def submit_delivery_location(self, session, t_id: int, token: str, lat_lng: dict):
        postcode_payload = {
            "location": self.profile["postCode"],
            "latitude": lat_lng["lat"],
            "longitude": lat_lng["lng"]
        }
        logging.warning(f"{Fore.CYAN}[{now()}] [CURRYS {self.mode:<7} - {t_id:<3}] [{self.user_id}] [{self.pid:<3}] Submitting Postcode...{Style.RESET_ALL}")
        put_postcode = session.put(f"https://api.currys.co.uk/store/api/baskets/{token}/deliveryLocation", json=postcode_payload, timeout=self.timeout)
        
        while put_postcode.status_code != 200:
            logging.warning(f"{Fore.RED}[{now()}] Error Submitting Postcode...{Style.RESET_ALL}")
            self.rotate_proxy(session)
            time.sleep(self.delay)
            put_postcode = session.put(f"https://api.currys.co.uk/store/api/baskets/{token}/deliveryLocation", json=postcode_payload, timeout=self.timeout)
            
        else:
            return put_postcode.json()["payload"]["consignments"][0]["availableDeliverySlots"][0]

    
    def submit_delivery_rates(self, session, t_id: int, token: str, postcode_json: dict):
        delivery_rates_payload = {
            "provider": postcode_json["provider"],
            "priceAmountWithVat": postcode_json["price"]["amountWithVat"],
            "priceVatRate": postcode_json["price"]["vatRate"],
            "priceCurrency": postcode_json["price"]["currency"],
            "date": postcode_json["date"],
            "timeSlot": postcode_json["timeSlot"]
        }
        delivery_rates = {
            "small_box_home_delivery_standard_delivery": "small-box-home-delivery",
            "big_box_home_delivery": "big-box-home-delivery"
        }

        put_delivery_rates = session.put(f"https://api.currys.co.uk/store/api/baskets/{token}/consignments/" + delivery_rates[delivery_rates_payload["provider"]] + "/deliverySlot", json=delivery_rates_payload, timeout=self.timeout)
        
        while put_delivery_rates.status_code != 200:
            logging.warning(f"{Fore.RED}[{now()}] [CURRYS {self.mode:<7} - {t_id:<3}] [{self.user_id}] [{self.pid:<3}] Error Submitting Delivery Slot...{Style.RESET_ALL}")
            self.rotate_proxy(session)
            time.sleep(self.delay)
            put_delivery_rates = session.put(f"https://api.currys.co.uk/store/api/baskets/{token}/consignments/" + delivery_rates[delivery_rates_payload["provider"]] + "/deliverySlot", json=delivery_rates_payload, timeout=self.timeout)
            
    
    def get_customer_id(self, session, t_id: int):
        logging.warning(f"{Fore.YELLOW}[{now()}] [CURRYS {self.mode:<7} - {t_id:<3}] [{self.user_id}] [{self.pid:<3}] Submitting Email...{Style.RESET_ALL}")
        submit_email = session.post("https://api.currys.co.uk/store/api/token", json={"customerEmail": self.profile["email"]}, timeout=self.timeout)
        
        while submit_email.status_code != 200:
            if submit_email.status_code == 401:
                logging.warning(f"{Fore.RED}[{now()}] [CURRYS {self.mode:<7} - {t_id:<3}] [{self.user_id}] [{self.pid:<3}] Account Does Not Exist - Stopping Task...{Style.RESET_ALL}")
                update_title_bar("failed")
                return None
            self.rotate_proxy(session)
            logging.warning(f"{Fore.RED}[{now()}] [CURRYS {self.mode:<7} - {t_id:<3}] [{self.user_id}] [{self.pid:<3}] Error Submitting Email...{Style.RESET_ALL}")
            time.sleep(self.delay)
            submit_email = session.post("https://api.currys.co.uk/store/api/token", json={"customerEmail": self.profile["email"]}, timeout=self.timeout)
            
        else:
            return submit_email.json()["cid"]

    
    
    def submit_address(self, session, t_id: int, c_id: str, stage: int):
        self.profile["type"] = "guest"
        self.profile["title"] = random.choice(["mr", "mrs", "ms", "miss"])
        self.profile["company"] = None
        self.profile["line3"] = None
        logging.warning(f"{Fore.CYAN}[{now()}] [CURRYS {self.mode:<7} - {t_id:<3}] [{self.user_id}] [{self.pid:<3}] Submitting Address [{stage}]...{Style.RESET_ALL}")
        submit_address_post = session.post(f"https://api.currys.co.uk/store/api/customers/{c_id}/addresses", json=self.profile, timeout=self.timeout)
        
        while submit_address_post.status_code != 200:
            logging.warning(f"{Fore.RED}[{now()}] [CURRYS {self.mode:<7} - {t_id:<3}] [{self.user_id}] [{self.pid:<3}] Error Submitting Address [{stage}]...{Style.RESET_ALL}")
            self.rotate_proxy(session)
            time.sleep(self.delay)
            submit_address_post = session.post(f"https://api.currys.co.uk/store/api/customers/{c_id}/addresses", json=self.profile, timeout=self.timeout)
            
        return submit_address_post.json()["payload"]["addressId"]

    
    def submit_address_id(self, session, t_id: int, id_one: str, id_two: str):
        post_id = session.post("https://api.currys.co.uk/store/api/token", json={
            "customerEmail": self.profile["email"],
            "customerGuestBillingAddressId": id_one,
            "customerGuestDeliveryAddressId": id_two
        }, timeout=self.timeout)
        
        while post_id.status_code != 200:
            logging.warning(f"{Fore.RED}[{now()}] [CURRYS {self.mode:<7} - {t_id:<3}] [{self.pid:<3}] Error Adding Customer - Retrying{Style.RESET_ALL}")
            self.rotate_proxy(session)
            post_id = session.post("https://api.currys.co.uk/store/api/token", json={
            "customerEmail": self.profile["email"],
            "customerGuestBillingAddressId": id_one,
            "customerGuestDeliveryAddressId": id_two
        }, timeout=self.timeout)


    def create_order(self, session, t_id: int, token: str):
        logging.warning(f"{Fore.YELLOW}[{now()}] [CURRYS {self.mode:<7} - {t_id:<3}] [{self.user_id}] [{self.pid:<3}] Submitting Order...{Style.RESET_ALL}")
        create_order_post = session.post(f"https://api.currys.co.uk/store/api/baskets/{token}/orders", timeout=self.timeout)
        
        while create_order_post.status_code != 200:
            self.rotate_proxy(session)
            logging.warning(f"{Fore.RED}[{now()}] [CURRYS {self.mode:<7} - {t_id:<3}] [{self.user_id}] [{self.pid:<3}] Error Creating Order - Retrying...{Style.RESET_ALL}")
            time.sleep(self.delay)
            create_order_post = session.post(f"https://api.currys.co.uk/store/api/baskets/{token}/orders", timeout=self.timeout)
            
    
    def submit_order(self, session, t_id: int, token: str):
        submit_order_post = session.post(f"https://api.currys.co.uk/store/api/baskets/{token}/payments", json={"paymentMethodType": self.payment_method}, timeout=self.timeout)
        
        while submit_order_post.status_code != 200:
            logging.warning(f"{Fore.RED}[{now()}] [CURRYS {self.mode:<7} - {t_id:<3}] [{self.user_id}] [{self.pid:<3}] Error Completing Order - Retrying...{Style.RESET_ALL}")
            self.rotate_proxy(session)
            time.sleep(self.delay)
            submit_order_post = session.post(f"https://api.currys.co.uk/store/api/baskets/{token}/payments", json={"paymentMethodType": self.payment_method}, timeout=self.timeout)
            
        payment_url = submit_order_post.json()["payload"]["paymentRequests"][0]["paymentMethodRequestData"]["payment_url"]

        while payment_url is None:
            logging.warning(f"{Fore.RED}[{now()}] [CURRYS {self.mode:<7} - {t_id:<3}] [{self.user_id}] [{self.pid:<3}] Error Completing Order - Unknown Reason - Retrying...{Style.RESET_ALL}")
            self.rotate_proxy(session)
            time.sleep(self.delay)
            submit_order_post = session.post(f"https://api.currys.co.uk/store/api/baskets/{token}/payments", json={"paymentMethodType": self.payment_method}, timeout=self.timeout)
            payment_url = submit_order_post.json()["payload"]["paymentRequests"][0]["paymentMethodRequestData"]["payment_url"]
            
        else:
            logging.warning(f"{Fore.LIGHTGREEN_EX}[{now()}] [CURRYS {self.mode:<7} - {t_id:<3}] [{self.user_id}] [{self.pid:<3}] Submitted Order!{Style.RESET_ALL}")
            update_title_bar("success")
        
        return payment_url

    
    def gen_cloudflare_cookies(self, session, t_id: int):
        logging.warning(f"{Fore.MAGENTA}[{now()}] [CURRYS SYSTEM - {t_id:<3}] [{self.user_id}] [{self.pid:<3}] Solving Cloudflare V2...{Style.RESET_ALL}")
        session.get("https://api.currys.co.uk")
        
    @decorators.request_exception_handler
    def checkout(self, t_id: int):
        embed = embeds.CheckoutEmbed(self.settings["webhook"], self.mode, self.payment_method.capitalize(), self.profile["profileName"] , self.proxy_list, self.pid, t_id)
        lat_lng = self.get_lat_lng()
        logging.warning(f"[{now()}] [CURRYS {self.mode:<7}- {t_id:<3}] [{self.user_id}] [{self.pid:<3}] Initiating Task...")
        with scraper() as session:
            self.rotate_proxy(session)
            self.gen_cloudflare_cookies(session, t_id)
            start_checkout = datetime.now()
            token = self.get_session_token(session, t_id)
            atc_start = datetime.now()
            self.add_to_cart(session, t_id, token, self.pid)
            atc_end = datetime.now()
            postcode_json = self.submit_delivery_location(session, t_id, token, lat_lng)
            self.submit_delivery_rates(session, t_id, token, postcode_json)
            customer_id = self.get_customer_id(session, t_id)
            if customer_id is not None:
                billing_id = self.submit_address(session, t_id, customer_id, 1)
                delivery_id = self.submit_address(session, t_id, customer_id, 2)
                self.submit_address_id(session, t_id, billing_id, delivery_id)
                self.create_order(session, t_id, token)
                payment_url = self.submit_order(session, t_id, token)
                end_checkout = datetime.now()
                embed.successful_checkout_embed(payment_url, atc_end-atc_start, end_checkout-start_checkout, session, self.user_id)
            else:
                embed.failed_checkout_embed("Account Does not Exist", session, self.user_id)


# this is user for client side operation need to make one for server side running

def run_server(profiles: dict, settings: dict, tasks: list, user_id: int):
    update_title_bar("clear")
    error = False

    logging.warning(f"[{now()}] Getting Tasks from tasks.csv")
    for t_id in range(len(tasks)):
        if tasks[t_id]["profile"] in profiles:
            tasks[t_id]["profile"] = profiles[tasks[t_id]["profile"]]
        else:
            logging.warning(Fore.RED + f"[{now()}] Found Error in Task {t_id} - Profile Not Found...")
            error = True

    if len(tasks) != 0 and not error:
        logging.warning(f"[{now()}] Found {len(tasks)} Tasks - Starting Tasks!\n")
    else:
        logging.warning(f"{Style.RESET_ALL}[{now()}] No Valid Tasks Found...\n")

    task_list = [Task(task, task["profile"], settings, user_id) for task in tasks]
    threads = [threading.Thread(target=i.checkout, args=[task_list.index(i)]) for i in task_list]

    for th in threads:
        th.start()

    for th in threads:
        th.join()
    
    logging.warning(f"{Fore.CYAN}[{now()}] All Tasks Executed - Removing User...{Style.RESET_ALL}")

    os.system("title JBOT")