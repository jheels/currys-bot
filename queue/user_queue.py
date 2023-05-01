from embeds import now
import requests
import json
import decorators
import io

class Queue:
    def __init__(self, operator):
        self.sftp = operator
        try:
            self.queue = requests.get(f"https://{self.sftp.HOST}/{self.sftp.USER}/queue/queue.json").json()
        except (requests.exceptions.RequestException, json.decoder.JSONDecodeError):
            print("Error Retrieving Queue - Creating new queue")
            self.queue = []

    def is_empty(self):
        return self.queue == []

    def increase_delay(self):
        return self.sftp.increase_delay()

    def is_user_in_queue(self, user_id: str) -> int:
        for pos, val in enumerate(self.queue):
            if user_id == val["userId"]:
                return pos
        return -1

    @decorators.async_exception_handler
    async def add_user(self, user_id: str, task_buffer: io.StringIO, profile_buffer: io.BytesIO):
        self.queue.append({"userId": user_id})
        await self.sftp.write_to_queue_ftp(self.queue)
        if not requests.get(f"https://{self.sftp.HOST}/{self.sftp.USER}/queue/{user_id}"):
            await self.sftp.create_user_dir(user_id)
            task_buffer = io.BytesIO(task_buffer.getvalue().encode("utf-8"))
            await self.sftp.upload_queue_file(task_buffer, user_id, "tasks.csv")
            await self.sftp.upload_queue_file(profile_buffer, user_id, "profiles.json")

    @decorators.async_exception_handler
    async def remove_user(self, user_id: str, pos: int):
        if len(self.queue) > 0:
            self.queue.pop(pos)
            await self.sftp.write_to_queue_ftp(self.queue)
            if requests.get(f"https://{self.sftp.HOST}/{self.sftp.USER}/queue/{user_id}"):
                await self.sftp.remove_user_dir(user_id)
            else:
                print(f"[{now()}] ERROR CREATING DIR: {user_id} DOES NOT EXIST")
        else:
            print(f"[{now()}] ERROR POPPING FROM QUEUE: QUEUE EMPTY")
