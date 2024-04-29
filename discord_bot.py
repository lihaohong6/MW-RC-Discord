from dataclasses import dataclass
from requests.exceptions import SSLError, ConnectTimeout
import traceback
from discord.ext import tasks
from fetch_recent_changes import RecentChangesFetcher

import discord
import logging


channel_id = 1233942761485635646

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fetcher = RecentChangesFetcher(name="blue-archive", 
                                            api_root="https://bluearchive.wiki/w/api.php", 
                                            article_root="https://bluearchive.wiki/wiki/")
        self.rc_id = self.fetcher.load_last_change()

    async def setup_hook(self) -> None:
        # start the task to run in the background
        self.poll_recent_changes.start()

    async def on_ready(self):
        self.fetcher.setup()
        self.logger = logging.getLogger("discord")
        self.logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        

    @tasks.loop(seconds=60)  # task runs every 60 seconds
    async def poll_recent_changes(self):
        try:
            new_rc_id, message = self.fetcher.get_recent_changes(self.rc_id)
        except (SSLError, ConnectTimeout) as e:
            logging.error(f"Network error: {str(e)}. Perhaps the server is down?")
            return
        except Exception as e:
            logging.error(traceback.format_exc())
            return
        if message.strip() != "":
            channel = self.get_channel(channel_id)  # channel ID goes here
            await channel.send(message)
        if new_rc_id != self.rc_id:
            self.fetcher.save_last_change(new_rc_id)
            self.rc_id = new_rc_id

    @poll_recent_changes.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in


client = MyClient(intents=discord.Intents.default())
client.run(open("token.txt", "r").read())
