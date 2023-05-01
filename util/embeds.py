from datetime import datetime
from discord import Webhook, RequestsWebhookAdapter
from colorama import Fore, Style, init
import logging
import discord
import requests

RED = discord.Colour.red()
GREEN = discord.Colour.green()
ORANGE = discord.Colour.gold()

init()

def now():
    return datetime.now().time()

class CheckoutEmbed:
    def __init__(self, hook, mode, method, profile_name, proxy_list, pid, t_id):
        self.hook = hook
        self.mode = mode
        self.method = method
        self.profile_name = profile_name
        self.proxy_list = proxy_list
        self.pid = pid
        self.t_id = t_id

    def base_embed(self, title, colour, scraper):

        json_data = scraper.get(f"https://api.currys.co.uk/store/api/products/{self.pid}").json()
        embed = discord.Embed(title=title, colour=colour)
        embed.add_field(name="Store", value="Currys " + self.mode.capitalize(), inline=True)
        embed.add_field(name="Product ID", value=f"[{self.pid}](https://www.currys.co.uk/GBUK/product-{self.pid}-pdt.html)", inline=True)
        embed.add_field(name="Task ID",value=self.t_id)
        embed.add_field(name="Payment Method", value=self.method, inline=True)
        embed.add_field(name="Profile", value=f"||{self.profile_name}||")
        embed.add_field(name="Proxy List", value=f"||{self.proxy_list}||")
        embed.set_thumbnail(url=json_data["payload"][0]["images"][0]["url"])
        embed.set_footer(text=f"JBOT | {now()}")

        return embed
    
    def successful_checkout_embed(self, link, atc_speed, checkout_speed, scraper, user_id):
        try:
            embed = self.base_embed(
                ":moneybag: Complete Manual Payment :moneybag:",
                 GREEN,
                 scraper)

            embed.add_field(name="ATC Speed", value=atc_speed)
            embed.add_field(name="Checkout Speed", value=checkout_speed)
            embed.add_field(name="Checkout Link", value=f"[CLICK ME!]({link})", inline=True)
            hookurl = self.hook.split("/")
            build_webhook = Webhook.partial(hookurl[5], hookurl[6], adapter=RequestsWebhookAdapter())
            build_webhook.send(embed=embed, content=f"<@{user_id}> Checkout Ready!")
        except (discord.errors.NotFound, TypeError, requests.exceptions.ConnectionError):
            logging.warning(Fore.RED + f"[{now()}] Failed To Send Webhook!" + Style.RESET_ALL)
        except discord.errors.HTTPException:
            logging.warning(Fore.RED + f"[{now()}] Error 429 - Webhook Rate Limit!" + Style.RESET_ALL)


    def failed_checkout_embed(self, reason, scraper, user_id):
        try:
            embed = self.base_embed(":x: Failed Checkout :x:", RED, scraper)
            embed.add_field(name="Reason", value=reason)
            hookurl = self.hook.split("/")
            build_webhook = Webhook.partial(hookurl[5], hookurl[6], adapter=RequestsWebhookAdapter())
            build_webhook.send(embed=embed, content=f"<@{user_id}> Failed Checkout!")
        except(discord.errors.NotFound, TypeError, requests.exceptions.ConnectionError):
            logging.warning(Fore.RED + f"[{now()}] Failed To Send Webhook!" + Style.RESET_ALL)
        except discord.errors.HTTPException:
            logging.warning(Fore.RED + f"[{now()}] Error 429 - Webhook Rate Limit!" + Style.RESET_ALL)

class BaseMonitorEmbed:
    def __init__(self, pid, hook):
        self.pid = pid
        self.hook = hook

class APIMonitorEmbed(BaseMonitorEmbed):
    def __init__(self, pid, hook, scraper):
        super().__init__(pid, hook)
        self.scraper = scraper

    def send_embed(self, loaded, purchasable):  
        response = self.scraper.get(f"https://api.currys.co.uk/store/api/products/{self.pid}")
        product_data = response.json()["payload"][0]
        embed = discord.Embed(title=product_data["label"], description="*Product may not be live*", url=product_data["link"],  colour=GREEN, timestamp=datetime.utcnow())
        embed.add_field(name="Loaded Stock", value=loaded, inline=True)
        embed.add_field(name="Purchasable Stock", value=purchasable, inline=True)
        embed.set_thumbnail(url=product_data["images"][0]["url"])
        embed.set_footer(text="By Jheels | Currys API V0.0.5")
        hook = self.hook.split("/")
        webhook = Webhook.partial(hook[5], hook[6], adapter=RequestsWebhookAdapter())
        webhook.send(embed=embed, username="Currys API")

class FrontendMonitorEmbed(BaseMonitorEmbed):
    def __init__(self, pid, hook):
        super().__init__(pid, hook)

    def send_embed(self, title, img_url, price):
        embed = discord.Embed(title=title, url="https://api.currys.co.uk/store/api/products/"+self.pid, colour=GREEN, timestamp=datetime.utcnow())
        embed.add_field(name="Instock", value=True, inline=True)
        embed.add_field(name="Price", value=price, inline=True)
        embed.add_field(name="PID", value=self.pid, inline=False)
        embed.set_footer(text="By Jheels | Currys Frontend V0.0.5")
        embed.set_thumbnail(url=img_url)
        hook = self.hook.split("/")
        webhook = Webhook.partial(hook[5], hook[6], adapter=RequestsWebhookAdapter())
        webhook.send(embed=embed, username="Currys Frontend")

class HelperEmbed:
    def __init__(self, ctx, url):
        self.ctx = ctx
        self.url = url

    def base_embed(self, colour, title: str):
        embed = discord.Embed(title=title, url=self.url, color=colour, timestamp=datetime.utcnow())
        embed.set_footer(text=f"By Jheels | Requested by {self.ctx.author.display_name}")
        embed.set_author(name="Currys Helper")
        return embed
    
    def invalid_embed(self, pid: int, reason: str):
        embed = self.base_embed(RED, "Failure!")
        embed.add_field(name="Cannot Add:", value=pid, inline=True)
        embed.add_field(name="Reason:", value=reason, inline=True)
        return embed
        