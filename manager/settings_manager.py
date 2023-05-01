import json
from colorama import Fore, Style
from embeds import now
import requests

def load_settings_req() -> dict:
    try:
        response = requests.get("")
        if response.status_code == 200:
            settings = response.json()
            if not(isinstance(settings["webhook"], str) and isinstance(settings["retry"], int) and isinstance(settings["timeout"], int)):
                input(f"{Fore.RED}[{now()}] Value(s) in settings.json entered incorrectly!\n[{now()}] Return to Exit...\n{Style.RESET_ALL}")
            if settings["timeout"] == 0:
                input(f"{Fore.RED}[{now()}] Timeout must be greater than 0!\n[{now()}] Return to Exit...\n{Style.RESET_ALL}")
                quit()
            return settings
        else:
            input(f"{Fore.RED}[{now()}] settings.json not found - error {response.status_code}\n[{now()}] Return to Exit...{Style.RESET_ALL}")
    except (json.decoder.JSONDecodeError, KeyError):
        input(f"{Fore.RED}[{now()}] Error reading settings.json - check values\n[{now()}] Return to Exit...\n{Style.RESET_ALL}")
        quit()
    except requests.exceptions.RequestException:
        input(f"{Fore.RED}[{now()}] Error Sending Re - Return to Exit...")
        quit()
