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

import queue
import bot.utils as utils
from random import shuffle


class Player:
    """
    Represents a music player that can be used by :class:`MetalBot`. It uses :class:`song.Song` objects as input.
    """
    def __init__(self, voice_client=None, volume=0.15, update_listener=None):
        """
        :param voice_client: The voice client the player should play in
        :type voice_client: discord.VoiceClient
        :param volume: The volume of the player, range: 0.0-1.0.
        :type volume: float
        :param update_listener: A method that should be called when the player changes its state
        :type update_listener: function
        """
        self.queue = queue.Queue()
        self.voice_client = voice_client
        self.update_listener = update_listener
        self._current_song = None
        self._volume = volume
        self._stream_player = None

    def is_playing(self):
        """
        Gets the play state of the player.

        :return: Whether or not the player is playing something
        :rtype: bool
        """
        return self._current_song is not None

    def can_play(self):
        """
        Returns whether or not the player is capable of playing music.

        :rtype: bool
        """
        return self.voice_client is not None

    def ensure_playing(self):
        """
        Makes sure the player is playing something if it can.
        """
        if not self.is_playing() and not self.queue.empty() and self.can_play():
            self.play_next()

    @property
    def current_song(self):
        """
        The currently playing song in the Player. This is read-only.
        """
        return self._current_song

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, volume):
        self._volume = volume
        if self._stream_player is not None:
            self._stream_player.volume = self._volume

    def add_to_queue(self, song):
        """
        Adds an song to the play queue and starts playing.

        :param song: The song to add
        :type song: song.Song
        """
        self.queue.put(song)
        utils.safe_print("Added to queue: %s" % song.title)
        if not self.is_playing() and self.can_play():
            self.play_next()

    def clear_queue(self):
        """
        Clears the play queue from all of its elements

        :return: The number of items removed
        :rtype: int
        """
        removed_count = 0
        while not self.queue.empty():
            self.queue.get()
            removed_count += 1
        return removed_count

    def shuffle_queue(self):
        """
        Shuffles the play queue's order.
        """
        if self.queue.empty():
            return
        song_list = list(self.queue.queue)
        shuffle(song_list)
        self.clear_queue()
        for song in song_list:
            self.queue.put(song)

    def calc_queue_time(self):
        """
        Calculates the total number of seconds of playback in the queue, including what is left of the song that is
        currently playing.

        :return: Seconds left in play queue
        :rtype: int
        """
        time = 0
        for song in list(self.queue.queue):
            time += song.length
        time += self.calc_current_left()

        return time

    def calc_current_left(self):
        """
        Calculates the number of seconds left for the song that is currently playing.

        :return: Seconds left in the current song
        :rtype: int
        """
        if self._current_song is None:
            return 0
        return self._current_song.length - self._current_song.elapsed()

    def calc_elapsed_delta(self, seconds):
        """
        Calculates the number of seconds between the seconds given and seconds elapsed of the current song

        :param seconds: Some number of seconds
        :type seconds: int
        :return: The difference between seconds and the current song's elapsed seconds
        :rtype: int
        """
        if self._current_song is None:
            return seconds
        return seconds - self._current_song.elapsed()

    def fire_update_listener(self):
        """
        Calls the update listener (usually a function of the bot)
        """
        if self.update_listener is not None:
            self.update_listener(self._current_song)

    def play_next(self):
        """
        Plays the next song in the queue.
        """
        if self._stream_player is not None:
            self._stream_player.after = None
            self._stream_player.stop()
            if self._current_song is not None:
                utils.safe_print("Song finished: %s" % self._current_song.title)

        self._current_song = None

        if not self.queue.empty():
            song = self.queue.get()
            self._stream_player = self.voice_client.create_ffmpeg_player(
                filename=song.stream_url,
                after=self.play_next
            )
            self._stream_player.volume = self._volume
            self._stream_player.start()
            self._current_song = song
            self._current_song.play()
            utils.safe_print("Playing: %s" % self._current_song.title)

        self.fire_update_listener()

