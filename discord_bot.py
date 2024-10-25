from dataclasses import dataclass
import requests
from requests.exceptions import Timeout
import traceback
from discord.ext import tasks
from fetch_recent_changes import RecentChangesFetcher

import discord
import logging

@dataclass
class ServerConfig:
    name: str
    api_root: str
    article_root: str
    channel_id: int
    rc_id: int = -1
    fetcher: RecentChangesFetcher = None
    
    
server_configs = [
    ServerConfig("blue-archive", 
                 "https://bluearchive.wiki/w/api.php", 
                 "https://bluearchive.wiki/wiki/", 
                 1233942761485635646),
    ServerConfig("strinova",
                 "https://strinova.org/w/api.php",
                 "https://strinova.org/wiki/",
                 1294157798422220873)
]

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger("discord.rc")
        self.logger.setLevel(logging.INFO)
        for config in server_configs:
            config.fetcher = RecentChangesFetcher(config.name, config.api_root, config.article_root, self.logger)
            config.rc_id = config.fetcher.load_last_change()

    async def setup_hook(self) -> None:
        # start the task to run in the background
        self.poll_recent_changes.start()

    async def on_ready(self):
        self.logger.info(f'Logged in as {self.user} (ID: {self.user.id})')

    @tasks.loop(seconds=60)  # task runs every 60 seconds
    async def poll_recent_changes(self):
        for config in server_configs:
            try:
                new_rc_id, message = config.fetcher.get_recent_changes(config.rc_id)
            except (ConnectionError, Timeout) as e:
                logging.error(f"Network error: {str(e)}. Perhaps the server for {config.name} is down?")
                continue
            except requests.JSONDecodeError as e:
                logging.error(f"Cannot decode JSON: {str(e)}")
            except Exception as e:
                logging.error(f"{str(e)} on {config.name}")
                logging.error(traceback.format_exc())
                continue
            if message.strip() != "":
                channel = self.get_channel(config.channel_id)  # channel ID goes here
                await channel.send(message)
            if new_rc_id != config.rc_id:
                config.fetcher.save_last_change(new_rc_id)
                config.rc_id = new_rc_id

    @poll_recent_changes.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in


client = MyClient(intents=discord.Intents.default())
client.run(open("token.txt", "r").read())
