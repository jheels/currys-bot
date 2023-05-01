from embeds import now
import requests
import csv
import settings_manager
import currys
import time
import json
import asyncio

def get_first_pos() -> int:
    while True:
        try:
            queue = requests.get("").json()
            if queue != []:
                first_pos = queue[0]["userId"]
                return first_pos
        except requests.exceptions.RequestException:
            print(f"[{now()}] Error Getting First User - Retrying...")
        return 0

def get_user_tasks(first_pos: int) -> list:
    header = ["mode", "pid", "profile", "paymentMethod", "proxyList"]
    while True:
        try:
            csv_file = requests.get(f"tasks.csv")
            decoded_content = csv_file.content.decode('utf-8')
            reader = csv.DictReader(decoded_content.splitlines(), fieldnames=header)
            next(reader)
            task_list = [i for i in reader if len("".join(i.values())) != 0]

            return task_list
        except Exception as e:
            print(f"[{now()}] Error Grabbing User Tasks - Retrying...")
            raise e


def get_user_profile(first_pos: int) -> dict:
    while True:
        try:
            profile_json = requests.get(f"profiles.json").json()
            profile_json = {profile_json["profileName"]: profile_json}
            
            return profile_json
        except json.decoder.JSONDecodeError:
            print(f"[{now()}] Error Grabbing User Profile - Retrying...")
        except requests.exceptions.RequestException:
            print(f"[{now()}] Error Sending Request - Retrying...")


async def run_first_user(queue):
    settings = settingsmanager.load_settings_req()
    print(f"[{now()}] Checking Queue for first user")
    while True:
        first = get_first_pos()
        if first != 0:
            profile, task = get_user_profile(first), get_user_tasks(first)
            currys.run_server(profile, settings, task, first)
            await queue.remove_user(first, 0)
        else:
            print(f"[{now()}] Queue empty - Retrying in 60s")
            time.sleep(60)


async def callback(q):
    await run_first_user(q)

def between_callback(q):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    asyncio.run(callback(q))
    loop.close()


"""
check if the queue is empty by sending request
if q is empty then wait X period then check again
if q is not empty retrieve first user from the q
retrieve their data from the q
Inform user that it is their turn now
run it until all tasks are finished or if X period passes
once that is satisfied remove the user from the q and get the next user again
keep running always on
"""