import csv
import os
import time
from datetime import datetime
from prettytable import PrettyTable
from colorama import Fore, Style, init
import discord
import logos
import monitors
import currys
import settings_manager
import task_manager
import embeds
import helheim
import cloudscraper

helheim.auth('')

def injection(session, response):
    if helheim.isChallenge(session, response):
        return helheim.solve(session, response)
    return response

init()

RED = Fore.RED
GREEN = Fore.LIGHTGREEN_EX
YELLOW = Fore.YELLOW
CYAN = Fore.CYAN

class Utilities:
    def __init__(self, version):
        self.version = version

    def cls(self):
        os.system("cls")

    def now(self):
        return datetime.now().time()
    
    def mass_edit(self):
        pid = input(f"[JBOT - {self.version}] [{self.now()}] Enter PID: ")

        while not (len(pid) == 8 and pid.isdigit()):
            self.invalid_input()
            pid = input(f"[JBOT - {self.version}] [{self.now()}] Enter PID: ")
            
        tasks = taskmanager.read_tasks()
        for i in tasks.values():
            i["mode"] = "NORMAL"
            i["pid"] = str(pid)

        print(f"{GREEN}[JBOT - {self.version}] [{self.now()}] Successfully Edited PID!" + Style.RESET_ALL)
        return tasks

    def invalid_input(self):
        print(f"{RED}[JBOT - {self.version}] [{self.now()}] INVALID INPUT" + Style.RESET_ALL)
        time.sleep(1)


class Menu:
    def __init__(self, user, version, key_type):
        self.user = user.upper()
        self.version = version
        self.key_type = key_type
        self.utilities = Utilities(version)

    def main_menu_choice(self):
        print(CYAN + logos.name)
        print(f"{YELLOW}WELCOME BACK: {CYAN}{self.user:<15}\n")
        print(f"{YELLOW}KEY TYPE: {CYAN}{self.key_type:<10}\n")
        print(f"{YELLOW}VERSION: {CYAN}{self.version:<10}\n")
        options = ["Start Tasks", "SHOCK DROP MODE", "View Tasks", "Tools", "Exit"]
        for count, value in enumerate(options, start=1):
            print(f"{YELLOW}[JBOT - {self.version}] [{self.utilities.now()}]{Fore.WHITE} {count}. {value}")
        menu_choice = input(f"\n[JBOT - {self.version}] [{self.utilities.now()}] Select an option: ")

        return menu_choice

class ToolsMenu(Menu):
    def __init__(self, user, version, key_type):
        super().__init__(user, version, key_type)
        self.settings = settingsmanager.load_settings_req()
    
    def tools_menu_choice(self):
        print(CYAN + logos.tools)
        options = ["Launch Frontend Monitor", "Launch API Monitor", "Test Webhook", "Return to Menu"]
        for count, value in enumerate(options, start=1):
            print(f"{YELLOW}[JBOT - {self.version}] [{self.utilities.now()}]{Fore.WHITE} {count}. {value}")
        self.tool_choice = input(f"\n[JBOT - {self.version}] [{self.utilities.now()}] Select an option: ")

        return self.tool_choice
    
    def test_webhook(self):
        try:
            hook = self.settings["webhook"]
            embed = embeds.CheckoutEmbed(hook, "TEST", "TEST", "TEST", "TEST", "10154628", "0")
            print(f"{GREEN}[JBOT - {self.version}] [{self.utilities.now()}] SENDING WEBHOOK..." + Style.RESET_ALL)
            embed.successful_checkout_embed("https://www.currys.co.uk", "0", "0")
        except (discord.errors.NotFound, TypeError, monitors.requests.ConnectionError, IndexError):
            print(f"{RED}[JBOT - {self.version}] [{self.utilities.now()}] FAILED TO SEND!")
    
    def monitor(self):
        if self.tool_choice == "1":
            print(f"\n[JBOT - {self.version}] [{self.utilities.now()}]{GREEN} Grabbing PIDs From TASKS.CSV" + Style.RESET_ALL)
            monitor = monitors.FrontendMonitor()
        elif self.tool_choice == "2":
            print(f"\n{GREEN}[JBOT - {self.version}] [{self.utilities.now()}]{GREEN} Grabbing PIDs From TASKS.CSV" + Style.RESET_ALL)
            monitor = monitors.APIMonitor()
        else:
            return
        scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome', # we want a chrome user-agent
                    'mobile': False, # pretend to be a desktop by disabling mobile user-agents
                    'platform': 'windows', # pretend to be 'windows' or 'darwin' by only giving this type of OS for user-agents
                },
                requestPostHook=injection,
                captcha={"provider":"vanaheim"}
            )
        helheim.wokou(scraper)
        while not monitor.error:
            monitor.monitor_all_pids(scraper)

class ViewTasks:
    def __init__(self):
        with open("tasks.csv", "r") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            self.rows = [row for row in csv_reader]

    def show_table(self):
        table = PrettyTable(self.rows[0])
        for row in self.rows[1:]:
            if len("".join(row)) == 0:
                table.add_row(["EMPTY" for i in range(len(row))])
            else:
                table.add_row(row)
        print(table)


class Bot:
    def __init__(self, user, version, key_type):
        self.user = user
        self.version = version
        self.key_type = key_type
        os.system(f"title JBOT - Version: {self.version}")
        self.utilities = Utilities(self.version)

    def tools(self):
        tools_menu = ToolsMenu(self.user, self.version, self.key_type)
        choice = tools_menu.tools_menu_choice()

        while choice not in [str(i) for i in range(1,5)]:
            self.utilities.invalid_input()
            self.utilities.cls()
            choice = tools_menu.tools_menu_choice()
        if int(choice) in range(1,3):
            tools_menu.monitor()
        elif choice == "3":
            tools_menu.test_webhook()
        else:
            self.utilities.cls()
            self.instance()
        input(f"[JBOT - {self.version}] [{self.utilities.now()}] Press Enter to Return")
        self.utilities.cls()
        self.tools()

    def instance(self):
        menu = Menu(self.user, self.version, self.key_type)
        choice = menu.main_menu_choice()

        while choice not in [str(i) for i in range(1,6)]:
            self.utilities.invalid_input()
            self.utilities.cls()
            choice = menu.main_menu_choice()

        if choice == "1":
            self.utilities.cls()
            if not os.path.exists(os.getcwd()+"\proxies"):
                input(f"[{self.utilities.now()}] Cannot Find Proxies Folder... Return to Menu ")
                self.utilities.cls()
                self.instance()
            currysv2.run(taskmanager.read_tasks())
            self.utilities.cls()
            self.instance()
        elif choice == "2":
            tasks = self.utilities.mass_edit()
            self.utilities.cls()
            currysv2.run(tasks)
            self.utilities.cls()
            self.instance()
        elif choice == "3":
            self.utilities.cls()
            print(Fore.CYAN + logos.tasks + Style.RESET_ALL)
            task_viewer = ViewTasks()
            try:
                task_viewer.show_table()
            except FileNotFoundError:
                print(f"{RED}[JBOT - {self.version}] [{self.utilities.now()}] tasks.csv Not Found!")
            input(f"\n{Fore.WHITE}[JBOT - {self.version}] [{self.utilities.now()}] Press Enter to return...\n")
            self.utilities.cls()
            self.instance()
        elif choice == "4":
            self.utilities.cls()
            self.tools()
        else:
            quit()
Bot("JHEELS", "TEST", "XXXX-XXXX-XXXX").instance()

