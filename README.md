# Introduction

Similar to MediaWiki extensions that send a discord message whenever a change occurs (such as [this extension](https://github.com/jayktaylor/mw-discord)), this python script polls the recent changes made to a MediaWiki site and then automatically sends a message to a discord channel when new changes are detected. It has the advantage of not needing an additional extensio install, which is handy for wiki farms where admins don't have control over extensions.

By default, messages are only sent for users without the `autopatrolled` right. This serves as an "alert" so that admins can check for vandalism.

# Usage

The simplest way to use is to contact the author who can set things up.

If you'd like to run the bot yourself, then
1. Change `server_configs` in `discord_bot.py` to match your MediaWiki installation and your discord server channel.
2. Create a file named `token.txt` in the directory where `discord_bot.py` resides. Put your Discord bot token in that txt file.
3. You may need to install `discord.py` and `requests` via `pip` if you don't have these dependencies. 
4. Run `python discord_bot.py`. It will automatically poll for changes and send messages whenever unpatrolled changes are detected.
