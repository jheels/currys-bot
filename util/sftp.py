from embeds import now
import pysftp
import json
import io
import decorators

class SFTPOperator:
    def __init__(self) -> None:
        self.HOST = ""
        self.USER = ""
        self.PASS = ""
        self.CNOPTS = pysftp.CnOpts()
        self.CNOPTS.hostkeys = None     
        self.base, self.attempts = 1.4, 0 # delay
    
    def increase_delay(self) -> float:
        if self.attempts == 5:
            self.attempts = 0
        delay = self.base ** self.attempts
        self.attempts += 1

        return delay

    async def json_to_bytes_buffer(self, json_data):
        data = json.dumps(json_data, ensure_ascii=False, indent=4)
        bio = io.BytesIO()
        bio.write(data.encode())
        bio.seek(0)

        return bio

    @decorators.async_exception_handler
    async def write_to_queue_ftp(self, queue: list):
        with pysftp.Connection(host=self.HOST, username=self.USER, password=self.PASS, cnopts=self.CNOPTS) as sftp:
            print(f"[{now()}] Connection established {self.HOST}: ATTEMPTING TO UPDATE QUEUE")
            sftp.chdir("jheels/queue")
            bio = await self.json_to_bytes_buffer(queue)
            sftp.putfo(bio, "queue.json")


    @decorators.async_exception_handler
    async def create_user_dir(self, user_id: str):
        with pysftp.Connection(host=self.HOST, username=self.USER, password=self.PASS, cnopts=self.CNOPTS) as sftp:
            print(f"[{now()}] Connection established {self.HOST}: ATTEMPTING TO CREATE USER DIR - {user_id}")
            sftp.chdir("jheels/queue")
            sftp.mkdir(user_id)

    @decorators.async_exception_handler
    async def remove_user_dir(self, user_id: str):
        with pysftp.Connection(host=self.HOST, username=self.USER, password=self.PASS, cnopts=self.CNOPTS) as sftp:
            print(f"[{now()}] Connection established {self.HOST}: ATTEMPTING TO REMOVE USER DIR - {user_id}")
            sftp.execute(f"rm -rf jheels/queue/{user_id}")
    

    @decorators.async_exception_handler
    async def upload_queue_file(self, buffer, user_id: str, filename: str):
        with pysftp.Connection(host=self.HOST, username=self.USER, password=self.PASS, cnopts=self.CNOPTS) as sftp:
            print(f"[{now()}] Connection established {self.HOST}: ATTEMPTING FILE UPLOAD - {filename}")
            sftp.chdir(f"jheels/queue/{user_id}")
            sftp.putfo(buffer, filename)
        

    @decorators.async_exception_handler
    async def upload_file(self, buffer, path: str, filename: str):
        with pysftp.Connection(host=self.HOST, username=self.USER, password=self.PASS, cnopts=self.CNOPTS) as sftp:
            print(f"[{now()}] Connection established {self.HOST}: ATTEMPTING FILE UPLOAD - {filename} - DIR: {path}")
            sftp.chdir(path)
            sftp.putfo(buffer, filename)