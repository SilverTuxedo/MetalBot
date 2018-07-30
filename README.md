# MetalBot

## Introduction

MetalBot is a music bot for Discord servers. This bot uses Python 3.5
and [discord.py](https://github.com/Rapptz/discord.py).  It is intended
to be self-hosted and used by relatively small servers. MetalBot is
meant to be simple and easy to understand. it is a basic and convenient
bot which does what it needs to and nothing else. This bot can play
music from YouTube video and playlist URLs.

## Commands

By default, all commands are prefixed by `!`. However, this can by
changed in the bot's options.

* `!join` / `!summon` - Makes the bot join your voice channel.
* `!play <YouTube URL/query>` - Adds the given YouTube URL to the queue.
If something other than a YouTube URL is given,
 the bot searchers YouTube for the query and enqueues the first search
 result.
* `!np` - Shows you the details of the song that is now playing. 
* `!queue` - Shows you the play queue.
* `!volume [value]` - Shows you the current volume of the bot. If a
value is entered, the volume is changed. Both absolute and relative
values (+[value]) can be entered.
* `!<value>` - Shorthand for `!volume [value]`.
* `!skip` - Votes to skip the current playing song. The conditions for a
vote to pass can be changed in the options.
* `!clear` - Votes to clear the bot's queue. Like `!skip`, the
conditions for a vote to pass can be changed in the options.
* `!shuffle` - Shuffles the play queue's order.

Owner only commands:

* `!shutdown` - Disconnects the bot from voice channels and logs out.
* `!forceskip` - Immediately skips the currently playing song.
* `!forceclear` - Immediately clears the queue.



## Setup

#### Step 1: Setting the options
Open `config/options.ini` with your preferred text editor. Enter the
bot's Token. You should also enter the bot owner's ID or role if you
want access to less democratic commands.

#### Step 2: Running the bot
This bot uses Python 3.5. To run the bot, execute `run.py`.

#### Step 3: Enqueuing music
You can summon the bot to your voice channel using `!summon` and start
playing music using `!play`. If you entered an owner ID in the options,
the bot will try to join the owner's voice channel when it starts
running.