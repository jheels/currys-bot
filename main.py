from discord.ext import commands
from datetime import datetime
from embeds import now
from itertools import cycle, islice
import discord
import asyncio
import io
import csv
import manager.profile_manager as profile_manager
import cloudscraper
import helheim
import discord.ext
import requests
import json
import io
import random
import operate_queue
import threading
import sftp
import user_queue

helheim.auth('')

RED = discord.Color.red()
GREEN = discord.Color.green()
BLUE = discord.Color.blue()


client = commands.Bot(command_prefix = "!")
timeout = 60

sftp_operator = sftp.SFTPOperator()
q = user_queue.Queue(sftp_operator)

def injection(session, response):
    if helheim.isChallenge(session, response):
        return helheim.solve(session, response)
    return response

scraper = cloudscraper.CloudScraper(
                browser={
                    'browser': 'chrome',
                    'mobile': False, 
                    'platform': 'windows'
                },
                requestPostHook=injection,
                captcha={"provider":"vanaheim"}
            )
helheim.wokou(scraper)


def get_product_data(session, product: int):
    while True:
        try:
            print(f"Getting Data for: {product}")
            response = session.get(f"https://api.currys.co.uk/store/api/products/{product}")
            product_data = response.json()["payload"][0]["label"]
            return product_data
        except json.decoder.JSONDecodeError:
            print(f"Error parsing JSON: {product} - Retrying...")
        except (requests.exceptions.RequestException, helheim.exceptions.HelheimSolveError):
            print(f"Error sending Request: {product} - Retrying...")


def load_all_pids(session):
    response = session.get("https://bmacs.tech/jheels/pids.txt").text
    pids = response.split("\n")
    products = {}

    for pid in pids:
        products[pid] = get_product_data(session, pid)
    
    return products

def gen_tasks_csv(selection, name: str):

    header = ['MODE', 'PID', 'PROFILE', 'PAYMENT', 'PROXIES']
    data = [["NORMAL",pid,name, random.choice(["card", "paypal"]),"proxies"] for pid in selection]

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(data)
    buffer.seek(0)

    return buffer


@client.event
async def on_ready():
    print(f"[{now()}] Bot is Running...")
    await client.change_presence(status=discord.Status.online, activity=discord.Game(name="!info"))


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command doesn't exist")
        return
    elif isinstance(error, commands.errors.PrivateMessageOnly):
        await ctx.send("DM only command")
        return
    elif isinstance(error, commands.errors.MissingPermissions):
        await ctx.send("You do not have permission!")
        return
    raise error


async def gentasks(ctx, profile_name: str):

    def check_author(msg):
        return msg.author == ctx.author and ctx.channel == msg.channel

    def check(msg):
        if msg.attachments == []:
            content = msg.content.replace("\n", " ").split(" ")
            return all(i.isdigit() and len(i) == 8 for i in content) and len(content) <= 10
        return False

    embed = discord.Embed(title="Enter PIDs below", color=BLUE, timestamp=datetime.utcnow())
    embed.add_field(name="Max quantity:", value="10")
    embed.add_field(name="Note:", value="Run !view to view PIDs again", inline=True)
    embed.set_footer(text=f"By Jheels | Requested by {ctx.author.display_name}")
    await ctx.send(embed=embed)


    select_pids = await client.wait_for("message", timeout=timeout, check=check_author)
    while not check(select_pids):
        if len(select_pids.content) > 0:
            if select_pids.content[0] == "!":
                await ctx.send("Stopping Command")
                return None
        await ctx.send("Invalid input - try again")
        select_pids = await client.wait_for("message", timeout=timeout, check=check_author)
    else:
        content = select_pids.content.replace("\n", " ").split(" ")
        content = list(islice(cycle(content), 20))
        buffer = gen_tasks_csv(content, profile_name)
        await ctx.send("Here are the generated tasks (preview)", file=discord.File(buffer, "tasks.csv"))
        return buffer


def gen_embed(step, profile: dict):
    embed = discord.Embed(title=step, color=BLUE, timestamp=datetime.utcnow())
    embed.set_footer(text="Profile Creation")
    for key, value in profile.items():
        embed.add_field(name=key, value=value, inline=True)
    return embed


async def profile_creation(ctx):

    def check_author(msg):
        return ctx.author == msg.author and ctx.channel == msg.channel

    profile = {
        "profileName": "\u200b",
        "firstName": "\u200b",
        "lastName": "\u200b",
        "email": "\u200b",
        "phone": "\u200b",
        "line1": "\u200b",
        "line2": "\u200b",
        "city": "\u200b",
        "postCode": "\u200b"
        }

    embed = gen_embed("Initiating Creation", profile)
    embed_msg = await ctx.send(embed=embed)
    key_list = list(profile.keys())
    for i in key_list:
        embed = gen_embed(f"Enter: {i}  ({key_list.index(i)+1}/{len(key_list)})", profile)
        await embed_msg.edit(embed=embed)
        user_msg = await client.wait_for("message", timeout=timeout, check=check_author)
        content = user_msg.content
        while "empty" in content.lower() or user_msg.attachments != []:
            await ctx.send("Invalid Input - Try again")
            user_msg = await client.wait_for("message", timeout=timeout, check=check_author)
            content = user_msg.content
        if content[0] == "!":
            return None
        else:
            profile[i] = content
    embed = gen_embed("Profile Creation Completed", profile)
    await embed_msg.edit(embed=embed)

    return profile


async def get_user_msg(ctx, options: list):

    def check_author(msg):
        return ctx.author == msg.author and ctx.channel == msg.channel

    user_msg = await client.wait_for("message", timeout=timeout, check=check_author)
    while user_msg.attachments != [] or user_msg.content.upper() not in options:
        if len(user_msg.content) > 0:
            if user_msg.content[0] == "!":
                return None
        await ctx.send("Invalid input - try again")
        user_msg = await client.wait_for("message", timeout=timeout)

    return user_msg.content


@client.command()
@commands.dm_only()
async def view(ctx):
    
    choice_embed = discord.Embed(title="What GPU PIDs would you like to view", color=BLUE, timestamp=datetime.utcnow())
    gpu = {
        "1": "3060",
        "2": "3060 Ti",
        "3": "3070",
        "4": "3070 Ti",
        "5": "3080",
        "6": "3080 Ti"
    }

    for key, value in gpu.items():
        choice_embed.add_field(name=key, value=f"RTX {value}", inline=True)
    await ctx.send(embed=choice_embed)

    try:
        choice = await get_user_msg(ctx, [str(i) for i in range(1,7)])
        if choice is not None:
            await ctx.send(f"You have selected {gpu[choice]}")
            choice_split = gpu[choice].split(" ")
            pids_embed = discord.Embed(title="PIDs", color=BLUE, timestamp=datetime.utcnow())

            for pid, name in all_pids.items():
                if set(choice_split) <= set(name.split(" ")):
                    if "Ti" in name.split(" "):
                        if "Ti" in choice_split:
                            pids_embed.add_field(name=name, value=f"[{pid}](https://www.currys.co.uk/GBUK/product-{pid}-pdt.html)", inline=False)
                    else:
                        pids_embed.add_field(name=name, value=f"[{pid}](https://www.currys.co.uk/GBUK/product-{pid}-pdt.html)", inline=False)

            await ctx.send(embed=pids_embed)
    except asyncio.exceptions.TimeoutError:
        embed = discord.Embed(title="Timeout - run command again", color=RED, timestamp=datetime.utcnow())
        await ctx.send(embed=embed)


@client.command()
@commands.dm_only()
async def enter(ctx):
    user_id = str(ctx.message.author.id)
    pos = q.is_user_in_queue(user_id)

    if pos == -1:
        try:
            profile = await profile_creation(ctx)

            if profile is not None:
                await ctx.send("Validating Information...")
                errors = profilemanager.check_errors(profile)
                if len(errors) != 0:
                    embed = discord.Embed(title="List of Errors", color=RED, timestamp=datetime.utcnow())
                    for error in errors:
                        embed.add_field(name=error, value=True, inline=True)
                    embed.set_footer(text="Run Command Again")
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(title="Beginning Task Creation", color=GREEN, timestamp=datetime.utcnow())
                    await ctx.send(embed=embed)
                    task_buffer = await gentasks(ctx, profile["profileName"])
                    profile_buffer = await sftp_operator.json_to_bytes_buffer(profile)

                    if task_buffer is not None:
                        await ctx.send("Adding to Queue...")
                        await q.add_user(user_id, task_buffer, profile_buffer)
                        embed = discord.Embed(title="Successfully Added to Queue!", color=GREEN, timestamp=datetime.utcnow())
                        embed.add_field(name="Your position:", value=len(q.queue))
                        await ctx.send(embed=embed)
        except asyncio.exceptions.TimeoutError:
            embed = discord.Embed(title="Timeout - run command again", color=RED, timestamp=datetime.utcnow())
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="You are already in queue!", color=RED, timestamp=datetime.utcnow())
        embed.add_field(name="Position", value=pos+1)
        await ctx.send(embed=embed)


@client.command()
@commands.dm_only()
async def edit(ctx):
    user_id = str(ctx.message.author.id)
    pos = q.is_user_in_queue(user_id)
    if pos == -1:
        await ctx.send("You are not in the queue!")
    else:
        embed = discord.Embed(title="What CSV would you like to edit:", color=BLUE, timestamp=datetime.utcnow())
        embed.add_field(name="1.", value="Profile")
        embed.add_field(name="2.", value="Tasks")
        await ctx.send(embed=embed)
        try:
            user_msg = await get_user_msg(ctx, ["1", "2"])
            if user_msg == "1":
                new_profile = await profile_creation(ctx)
                buffer = await sftp_operator.json_to_bytes_buffer(new_profile)
                prev_profile_name = requests.get(f"https://bmacs.tech/jheels/queue/{user_id}/profiles.json").json()["profileName"]
                await ctx.send("Editing Profile...")
                await sftp_operator.upload_queue_file(buffer, user_id, "profiles.json")
                if prev_profile_name != new_profile["profileName"]:
                    reader = convert_task_to_list(user_id)
                    for row in reader[1:]:
                        row[2] = new_profile["profileName"]
                    buffer = io.StringIO()
                    writer = csv.writer(buffer)
                    writer.writerows(reader)
                    buffer.seek(0)
                    buffer = io.BytesIO(buffer.getvalue().encode("utf-8"))
                    await sftp_operator.upload_queue_file(buffer, user_id, "tasks.csv")
                await ctx.send("Profiles edited successfully")
            elif user_msg == "2":
                reader = convert_task_to_list(user_id) 
                profile_name = list(reader)[1][2]
                buffer = await gentasks(ctx, profile_name)
                buffer = io.BytesIO(buffer.getvalue().encode("utf-8"))
                await sftp_operator.upload_queue_file(buffer, user_id, "tasks.csv")
                await ctx.send("Tasks edited successfully")
            return
        except asyncio.exceptions.TimeoutError:
            embed = discord.Embed(title="Timeout - run command again", color=RED, timestamp=datetime.utcnow())
            await ctx.send(embed=embed)
    
def convert_task_to_list(user_id: str):
    response = requests.get(f"https://bmacs.tech/jheels/queue/{user_id}/tasks.csv")
    profile_csv = response.content.decode("utf-8")
    reader = list(csv.reader(profile_csv.splitlines(), delimiter=','))

    return reader


@client.command()
@commands.dm_only()
async def leave(ctx):

    user_id = str(ctx.message.author.id)
    pos = q.is_user_in_queue(user_id)
    if pos == -1:
        await ctx.send("You are not in the queue!")
    else:
        embed = discord.Embed(title="Confirm to leave the queue - [Y, N]", color=BLUE, timestamp=datetime.utcnow())
        await ctx.send(embed=embed)
        user_msg = await get_user_msg(ctx, ["Y", "N"])
        if user_msg.upper() == "Y":
            await ctx.send(f"Removing {ctx.author} from the queue...")
            await q.remove_user(user_id, pos)
            await ctx.send("You have been removed from the queue!")
        elif user_msg is None:
            return


@client.command()
@commands.dm_only()
async def position(ctx):
    user_id = str(ctx.message.author.id)
    pos = q.is_user_in_queue(user_id)
    if pos == -1:
        await ctx.send("You are not in the queue!")
    else:
        await ctx.send(f"Your position is: {pos+1} out of {len(q.queue)}")



@client.command()
@commands.has_permissions(administrator=True)
async def clear(ctx):
    if not q.is_empty():
        embed = discord.Embed(title="Confirm to clear the queue: [Y, N]", color=BLUE, timestamp=datetime.utcnow())
        await ctx.send(embed=embed)
        user_msg = await get_user_msg(ctx, ["Y", "N"])
        if user_msg.upper() == "Y":
            for user in q.queue:
                await sftp_operator.remove_user_dir(user["userId"])
            q.queue = []
            await sftp_operator.write_to_queue_ftp(q.queue)
            await ctx.send("Queue has been cleared!")
        elif user_msg is None:
            return
    else:
        await ctx.send("Queue already empty...")


@client.command()
@commands.dm_only()
async def example(ctx):
    embed = discord.Embed(title="Example of Correct Inputs", color=BLUE, timestamp=datetime.utcnow())
    dict_of_examples = {
        "profileName": "Only Letters/Numbers (no spaces)",
        "firstName": "Only Letters",
        "lastName": "Only Letters",
        "email": "Valid email registered on Currys",
        "phone": "UK phone number starting with 0",
        "line1": "Only Letters/Numbers with Spaces",
        "line2": "Only Letters/Numbers with Spaces",
        "city": "Only Letters and Spaces",
        "postCode": "Valid UK postcode"
    }
    for k, v in dict_of_examples.items():
        embed.add_field(name=k, value=v)

    await ctx.send(embed=embed)


@client.command()
@commands.dm_only()
async def profile(ctx):    
    user_id = str(ctx.message.author.id)
    pos = q.is_user_in_queue(user_id)

    if pos == -1:
        await ctx.send("You're not in the queue!")
    else:
        try:
            profile_json = requests.get(f"https://bmacs.tech/jheels/queue/{user_id}/profiles.json").json()
            embed = discord.Embed(title="Stored Profile", color=BLUE, timestamp=datetime.utcnow())

            for key, value in profile_json.items():
                embed.add_field(name=key, value=f"||{value}||")
        except (json.decoder.JSONDecodeError, requests.exceptions.RequestException):
            await ctx.send("Unable to grab your profile")

        await ctx.send(embed=embed)


@client.command()
@commands.dm_only()
async def info(ctx):
    embed = discord.Embed(title="List of Commands", color=BLUE, timestamp=datetime.utcnow())
    dict_of_commands = {
        "!info": "Call this command",
        "!enter": "Enter the queue",
        "!leave": "Leave the queue",
        "!edit": "Edit your stored task/profile",
        "!example": "Show valid inputs for !enter",
        "!view": "View GPUS sold by Currys UK",
        "!profile": "View your stored profile"
    }

    for k, v in dict_of_commands.items():
        embed.add_field(name=k, value=v, inline=False)
    await ctx.send(embed=embed)     


@client.command()
@commands.has_permissions(administrator=True)
async def proxies(ctx):

    def check_author(msg):
        return ctx.author == msg.author and ctx.channel == msg.channel
        
    try:
        embed = discord.Embed(title="Upload Proxy File", color=BLUE, timestamp=datetime.utcnow())
        embed.add_field(name="Format", value=".txt file")
        await ctx.send(embed=embed)
        user_msg = await client.wait_for("message", timeout=timeout, check=check_author)
        while user_msg.attachments == []:
            if len(user_msg.content) > 0:
                if user_msg.content[0] == "!":
                    return None
            await ctx.send("Invalid file - Upload .txt file")
            user_msg = await client.wait_for("message", timeout=timeout, check=check_author)
        else:
            first_attach = user_msg.attachments[0]
            if first_attach.content_type.split(";")[0] == "text/plain":
                try:
                    print(f"[{now()}] Attempting to update: proxies.txt")
                    response = requests.get(first_attach.url).content
                    buffer = io.BytesIO(response)
                    await sftp_operator.upload_file(buffer, "jheels/", "proxies.txt")   
                except requests.exceptions.RequestException:
                    await ctx.send("Error uploading file - run command again")
    except asyncio.exceptions.TimeoutError:
        embed = discord.Embed(title="Timeout - run command again", color=RED, timestamp=datetime.utcnow())
        await ctx.send(embed=embed)

def run(token: str):
    threads = []
    threads.append(threading.Thread(target=operate_queue.between_callback, args=[q]))
    threads.append(threading.Thread(target=client.run, args=[token]))

    for th in threads:
        th.start()

    for th in threads:
        th.join()

if __name__ == "__main__":
    run("")
