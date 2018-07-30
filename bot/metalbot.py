# -----------------------
# MetalBot: A self hosted music bot for Discord servers.
# Copyright (C) 2018 SilverTuxedo
#
# This file is part of MetalBot.
#
# MetalBot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# MetalBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with MetalBot.  If not, see <https://www.gnu.org/licenses/>.
# -----------------------

import discord
from threading import Thread
import traceback
from bot import opus_loader
from bot.player import Player
from bot.song import Song
from bot.permissions import Permissions
from bot import songfetcher
from bot import utils


class MetalBot(discord.Client):
    """
    Represents a music bot's client connection that connects to Discord. This bot is capable of playing songs and
    playlists from YouTube by streaming them to a :class:`discord.VoiceClient`.
    """
    def __init__(self, config):
        """
        :param config: The bot's config
        :type config: configparser.ConfigParser
        """
        self.config = config

        self.player = Player(update_listener=self.song_changed_handler,
                             volume=self.config.getfloat("Preferences", "DefaultVolume"))
        # sets including members who voted on some command
        self.voters = {
            "skip": set(),
            "clear": set()
        }
        self.permissions = Permissions(
            owner_id=self.config.get("Permissions", "OwnerID"),
            owner_role=self.config.get("Permissions", "OwnerRole")
        )
        self.idle_playing_str = self.config["Preferences"]["CommandPrefix"] + "play"  # shown when nothing is playing

        super().__init__()

    async def on_ready(self):
        """
        Initial set up of the bot once it is connected to Discord.
        """
        utils.safe_print('Logged in as')
        utils.safe_print(self.user.name)
        utils.safe_print(self.user.id)
        utils.safe_print('------')
        await self.set_listening_to(self.idle_playing_str)
        await self.auto_summon(self.config["Permissions"]["OwnerID"])

    async def join_voice_channel(self, channel):
        """
        Makes the bot join a given voice Channel, and makes sure that OPUS is loaded before doing so. If the bot is already in a voice channel it is moved to the one given.

        :param channel: The Channel the bot should join
        :type channel: discord.Channel
        :return: A voice client that is fully connected to the voice server.
        :rtype: discord.VoiceClient
        """
        # make sure OPUS is loaded
        if not discord.opus.is_loaded():
            utils.safe_print("loading opus...")
            opus_loader.load_opus_lib()

        utils.safe_print("Joining voice channel %s" % channel)
        voice = self.voice_client_in(channel.server)
        if voice is None:
            voice = await super().join_voice_channel(channel)
        else:
            voice = await voice.move_to(channel)

        self.player.voice_client = voice
        self.player.ensure_playing()
        return voice

    async def set_listening_to(self, title):
        """
        Sets the bot's presence to "listening to " + title. Removes presence if title is None.

        :param title: the text for the bot's presence
        :type title: str
        """
        if title is None or len(title) == 0:
            await self.change_presence(game=None)
        else:
            await self.change_presence(game=discord.Game(
                name=title,
                type=2
            ))

    async def auto_summon(self, user_id):
        """
        Makes the bot join the voice channel of the user with the id given

        :param user_id: Id of a Discord user
        :type user_id: str
        :return: Whether or not the operation was successful
        :rtype: bool
        """
        for server in self.servers:
            for channel in server.channels:
                for member in channel.voice_members:
                    if member.id == user_id:
                        await self.join_voice_channel(channel)
                        return True

        return False

    def skip_song(self):
        """
        Immediately skips the current song
        """
        self.voters["skip"].clear()
        self.player.play_next()

    def song_changed_handler(self, song):
        """
        Fires when the player's song changed.

        :param song: The song that is currently playing
        :type song: Song
        """
        self.voters["skip"].clear()
        if song is None:
            self.loop.create_task(self.set_listening_to(self.idle_playing_str))
            self.voters["clear"].clear()
        else:
            playing_str = "**%s** is now playing!" % song.title
            if self.config.getboolean("Preferences", "MentionPlaying"):
                playing_str = song.requester.mention + ", " + playing_str

            self.loop.create_task(
                self.send_message(song.text_channel, playing_str)
            )
            self.loop.create_task(self.set_listening_to(song.title))

    def get_listener_count(self, server):
        """
        Returns the number of users listening to the bot in a specific server. This does not count deafened users.

        :param server: The server to count listeners in
        :type server: discord.Server
        :return: The number of listeners
        :rtype: int
        """
        voice = self.voice_client_in(server)
        if voice is None:
            return 0

        listener_count = 0
        for member in voice.channel.voice_members:
            if member == self.user or member.voice.self_deaf or member.voice.deaf:
                continue
            listener_count += 1

        return listener_count

    async def skip_song_democratic(self, voter, server, text_channel=None):
        """
        Skips a song if enough users decided to skip it according to the bot's config.

        :param voter: A user who wants to skip
        :type voter: discord.Member
        :param server: The server of the voter
        :type server: discord.Server
        :param text_channel: The text channel to report the skip's status to
        :type text_channel: discord.Channel
        """

        if self.config.getboolean("Votes", "SelfInstaSkip") and voter == self.player.current_song.requester:
            await self.send_message(text_channel, "Skipping...")
            self.skip_song()
            return True

        seconds_to_skip = self.config.getint("Votes", "PassSkipVoteAfter")
        if seconds_to_skip > 0:
            left_to_skip = self.player.calc_elapsed_delta(seconds_to_skip)
            if left_to_skip <= 0:
                if text_channel is not None:
                    await self.send_message(text_channel, "Vote passed because enough time had passed. Skipping...")
                self.skip_song()
                return True

        listener_count = self.get_listener_count(server)

        self.voters["skip"].add(voter)
        current_count = len(self.voters["skip"])

        extra_skips_needed = utils.calc_min_votes_skip(
            current_count,
            listener_count,
            self.config.getfloat("Votes", "MinimalSkipPercent"),
            self.config.getint("Votes", "MinimalSkipCount")
        )

        if extra_skips_needed <= 0:  # vote passed
            if text_channel is not None:
                await self.send_message(text_channel, "Vote passed. Skipping...")
            self.skip_song()
            return True
        elif text_channel is not None:
            await self.send_message(text_channel, "%s, vote registered. %s more votes needed to skip." %
                                    (voter.mention, extra_skips_needed))
        return False

    async def clear_democratic(self, voter, server, text_channel=None):
        """
        Clears the queue if enough users decided to clear it according to the bot's config.

        :param voter: A user who wants to skip
        :type voter: discord.Member
        :param server: The server of the voter
        :type server: discord.Server
        :param text_channel: The text channel to report the skip's status to
        :type text_channel: discord.Channel
        """
        listener_count = self.get_listener_count(server)
        self.voters["clear"].add(voter)
        current_count = len(self.voters["clear"])

        extra_skips_needed = utils.calc_min_votes_skip(
            current_count,
            listener_count,
            self.config.getfloat("Votes", "MinimalClearPercent"),
            self.config.getint("Votes", "MinimalClearCount")
        )

        if extra_skips_needed <= 0:  # vote passed
            cleared = self.player.clear_queue()
            if text_channel is not None:
                await self.send_message(text_channel, "Vote passed. Cleared %s songs." % cleared)
        elif text_channel is not None:
            await self.send_message(text_channel, "%s, vote registered. %s more votes needed to clear." %
                                    (voter.mention, extra_skips_needed))

    def add_youtube_to_queue(self, url, original_msg):
        """
        Adds a video from YouTube to the play queue.

        :param url: URL of the video
        :type url: str
        :param original_msg: The message that caused this function to be called
        :type original_msg: discord.Message
        """

        newsong = None
        try:
            newsong = songfetcher.get_youtube_song(url)
        except ValueError as e:
            utils.safe_print(("got ValueError with input '%s' Error: %s" % (url, e)))
            self.loop.create_task(
                self.send_error(original_msg.channel, "Value Error:\n```%s```\nInput: `%s`" % (e, url))
            )
            traceback.print_stack()
            return False
        except OSError as e:
            utils.safe_print(("got OSError with input '%s' Error: %s" % (url, e)))
            self.loop.create_task(
                self.send_error(original_msg.channel, "OS Error:\n```%s```\nInput: `%s`" % (e, url))
            )
            traceback.print_stack()
            return False

        newsong.requester = original_msg.author
        newsong.text_channel = original_msg.channel

        max_length = self.config.getint("Preferences", "MaxSongLength")
        if newsong.length > max_length > 0:
            self.loop.create_task(
                self.send_error(original_msg.channel, "Song too long! (%s, limit is %s)" % (
                    utils.seconds_to_timestamp(newsong.length),
                    utils.seconds_to_timestamp(max_length),
                ))
            )
            return False

        estimated_time = self.player.calc_queue_time()
        self.player.add_to_queue(newsong)

        if estimated_time > 0:
            self.loop.create_task(
                self.send_message(original_msg.channel, "Enqueued **%s**, ETA: %s" %
                                  (newsong.title, utils.seconds_to_timestamp(estimated_time)))
            )
        return True

    def add_ytsearch_to_queue(self, term, original_msg):
        """
        Searches YouTube for the term given and adds the first video found to the player queue

        :param term: The search term
        :type term: str
        :param original_msg: The message that caused this function to be called
        :type original_msg: discord.Message
        :return: Whether or not the operation was successful
        :rtype: bool
        """

        urls = utils.search_youtube(term)
        if len(urls) > 0:
            self.add_youtube_to_queue(urls[0], original_msg)
            return True
        else:
            self.loop.create_task(
                self.send_error(original_msg.channel, "No results for search term: `%s`" % term)
            )
            return False

    def add_ytplaylist_to_queue(self, playlist_url, original_msg):
        """
        Adds videos from a YouTube playlist to the play queue. The playlist can be limited via the bot's config.

        :param playlist_url: URL of the playlist
        :type playlist_url: str
        :param original_msg: The message that caused this function to be called
        :type original_msg: discord.Message
        """

        playlist_dict = songfetcher.get_ytplaylist_pafys(playlist_url)
        song_count = len(playlist_dict)

        if song_count > self.config.getint("Preferences", "MaxPlaylistLength") > 0:
            self.loop.create_task(
                self.send_message(
                    original_msg.channel, "Playlist is longer than the limit. Processing %s/%s songs..." %
                                          (self.config.getint("Preferences", "MaxPlaylistLength"), song_count)
                )
            )
        else:
            self.loop.create_task(
                self.send_message(original_msg.channel, "Processing %s songs..." % song_count)
            )
        self.loop.create_task(
            self.send_typing(original_msg.channel)
        )
        songs = []
        for element in playlist_dict:
            video = element['pafy']
            utils.safe_print(("processing " + str(video.title)))
            song = songfetcher.get_pafy_song(video)
            if song is not None:
                if 0 < song.length < self.config.getint("Preferences", "MaxSongLength"):
                    songs.append(song)

            if len(songs) >= self.config.getint("Preferences", "MaxPlaylistLength") > 0:
                break

        total_time = 0

        for song in songs:
            song.requester = original_msg.author
            song.text_channel = original_msg.channel
            self.player.add_to_queue(song)
            total_time += song.length

        self.loop.create_task(
            self.send_message(original_msg.channel,
                              "Successfully added %s songs to the queue for a total play time of %s." %
                              (len(songs), utils.seconds_to_timestamp(total_time)))
        )

        return True

    def get_queue_embed(self):
        """
        Builds and returns a rich-embed with the current queue

        :return: A :class:`discord.Embed` with the current queue
        :rtype: discord.Embed
        """

        if self.player is None or self.player.queue.empty():
            return discord.Embed(
                title="No songs in the queue!",
                description="Queue something with %splay" % self.config["Preferences"]["CommandPrefix"]
            )
        else:
            queue_str = ""
            index = 1
            for song in list(self.player.queue.queue):
                queue_str += "%s. **%s** by %s\n" % (index, song.title, song.requester.mention)
                if index >= 15:
                    queue_str += "And %s more..." % (self.player.queue.qsize() - index)
                    break
                index += 1
            em = discord.Embed(
                title="Queue",
                description=queue_str
            )
            em.set_footer(text=("Next song in %s" % utils.seconds_to_timestamp(self.player.calc_current_left())))
            return em

    def get_now_playing_embed(self):
        """
        Builds and returns a rich-embed with the currently playing song

        :return: A :class:`discord.Embed` with the currently playing song
        :rtype: discord.Embed
        """

        current_song = self.player.current_song
        em = discord.Embed(
            title="Nothing currently playing!",
            description="Queue something with %splay" % self.config["Preferences"]["CommandPrefix"]
        )
        if current_song is not None:
            em = discord.Embed(
                title=current_song.title,
                description="by %s \n%s\n[%s/%s]\n%s" %
                            (current_song.requester.mention,
                             utils.progress_bar(current_song.elapsed() / current_song.length),
                             utils.seconds_to_timestamp(current_song.elapsed()),
                             utils.seconds_to_timestamp(current_song.length),
                             current_song.song_url
                             )
            )
            if current_song.image is not None and len(current_song.image) > 0:
                em.set_thumbnail(url=current_song.image)

        return em

    async def change_volume(self, new_volume, original_msg):
        """
        Changes the player's _volume.

        :param new_volume: The new _volume for the player. Values should be in range 0-100.
        :type new_volume: str
        :param original_msg: The message that caused this function to be called
        :type original_msg: discord.Message
        """
        try:
            volume = float(new_volume) / 100.0
            if new_volume.startswith('+') or volume < 0:  # relative _volume
                volume += self.player.volume
            if 0.0 < volume <= 1.0:
                old_volume = self.player.volume * 100
                self.player.volume = volume
                await self.send_message(original_msg.channel, "Changed _volume from %.1f to %.1f" %
                                        (old_volume, volume * 100))
            else:
                await self.send_error(original_msg.channel, "Volume %.1f out of range: 1-100" % (volume * 100))
        except ValueError:
            await self.send_error(original_msg.channel, "`%s` is not a number" % new_volume)

    async def send_error(self, channel, details):
        """
        Sends an error rich-embed to the channel given

        :param channel: The channel to send the message to
        :type channel: discord.Channel
        :param details: The details of the error
        :type details: str
        """
        em = discord.Embed(
            title="Error",
            description=details,
            color=0xe74c3c
        )
        await self.send_message(channel, embed=em)

    async def send_info(self, channel, title, details):
        """
        Sends an info rich-embed to the channel given

        :param channel: The channel to send the message to
        :type channel: discord.Channel
        :param title: The info's title
        :type title: str
        :param details: Some details about the info
        :type details: str
        """
        em = discord.Embed(
            title=title,
            description=details,
            color=0x3498db
        )
        await self.send_message(channel, embed=em)

    async def on_message(self, msg):
        """
        Processing of all messages and commands received.

        :param msg: A message from a text channel
        :type msg: discord.Message
        """

        # do not process messages in private channels
        if msg.channel.is_private:
            return
        # do not process messages that are not commands
        if not msg.content.startswith(self.config["Preferences"]["CommandPrefix"]):
            return
        # ignore the bot's own messages
        if msg.author == self.user:
            return

        command = msg.content[len(self.config["Preferences"]["CommandPrefix"]):]  # remove prefix
        lower_command = command.lower()  # remove prefix

        if lower_command == "shutdown":
            if not self.permissions.is_owner(msg.author):
                await self.send_error(msg.channel, "You lack permission to use this command.")
                return

            await self.send_message(msg.channel, "Shutting down...")
            utils.safe_print("Shutting down...")

            for voice in list(self.voice_clients):
                await voice.disconnect()
            await self.change_presence(game=None)
            await self.logout()

        elif lower_command == "summon" or lower_command == "join":
            channel = msg.author.voice_channel
            if channel is None:
                await self.send_error(msg.channel, "You're not in a voice channel!")
            else:
                await self.join_voice_channel(channel)

        elif lower_command.startswith("volume"):
            arg = command[len("volume") + 1:]
            if len(arg) == 0:  # no argument given
                await self.send_message(msg.channel, "Current volume is %.1f" %
                                        (self.player.volume * 100))
                return

            await self.change_volume(arg, msg)

        elif lower_command[0].isdigit() \
                or ((lower_command[0] == '-' or lower_command[0] == '+') and lower_command[1].isdigit()):
            await self.change_volume(lower_command, msg)

        elif lower_command == "skip":
            bot_voice = self.voice_client_in(msg.server)
            if bot_voice is None or not self.player.is_playing():
                await self.send_error(msg.channel, "Nothing is currently playing!")
                return

            if msg.author.voice_channel is None or msg.author.voice_channel != bot_voice.channel:
                await self.send_error(msg.channel, "Join **%s** to use this command" % bot_voice.channel.name)
                return

            await self.skip_song_democratic(msg.author, msg.server, msg.channel)

        elif command == "clear":
            bot_voice = self.voice_client_in(msg.server)
            if bot_voice is None:
                await self.send_error(msg.channel, "Nothing is currently playing!")
                return

            if msg.author.voice_channel is None or msg.author.voice_channel != bot_voice.channel:
                await self.send_error(msg.channel, "Join **%s** to use this command" % bot_voice.channel.name)
                return

            await self.clear_democratic(msg.author, msg.server, msg.channel)

        elif lower_command == "forceskip":
            if not self.permissions.is_owner(msg.author):
                await self.send_error(msg.channel, "You lack permission to use this command.")
                return
            self.skip_song()

        elif lower_command == "forceclear":
            if not self.permissions.is_owner(msg.author):
                await self.send_error(msg.channel, "You lack permission to use this command.")
                return
            await self.send_message(msg.channel, "Cleared %s songs." % self.player.clear_queue())

        elif lower_command == "queue":
            await self.send_message(msg.channel, embed=self.get_queue_embed())

        elif lower_command == "np" or lower_command == "song":
            await self.send_message(msg.channel, embed=self.get_now_playing_embed())

        elif lower_command == "shuffle":
            await self.send_typing(msg.channel)
            self.player.shuffle_queue()
            await self.send_message(msg.channel, ":clubs: :diamonds: Queue shuffled! :spades: :hearts:")

        elif lower_command.startswith("play"):

            if not self.is_voice_connected(msg.server):
                await self.send_error(msg.channel, "You must summon me first!")
                return

            if msg.author.voice_channel is None:
                await self.send_error(msg.channel, "Please join a voice channel to use this command.")
                return

            arg = command[len("play") + 1:]
            if len(arg) == 0:  # no argument given
                await self.send_error(msg.channel, "Usage: %splay <YouTube-URL>" %
                                      self.config["Preferences"]["CommandPrefix"])
                return

            await self.send_typing(msg.channel)

            download_thread_target = None

            if "youtube.com/watch" in arg or "youtu.be/" in arg:
                download_thread_target = self.add_youtube_to_queue
            elif "youtube.com/playlist" in arg:
                download_thread_target = self.add_ytplaylist_to_queue

            if download_thread_target is None:  # nothing could process this text, search YouTube
                dt = Thread(target=self.add_ytsearch_to_queue, args=(arg, msg))
                dt.start()
            else:
                dt = Thread(target=download_thread_target, args=(arg, msg))
                dt.start()
