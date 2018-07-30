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

import datetime


class Song:
    """
    Represents a song that can be played by a :class:`player.Player` instance.
    """
    def __init__(self, stream_url, title, requester=None, length=0, text_channel=None, image=None, song_url=""):
        """
        :param stream_url: URL of the stream to download the song from
        :type stream_url: str
        :param title: The title of the song
        :type title: str
        :param requester: The user who requested the song
        :type requester: discord.User
        :param length: The length of the song in seconds
        :type length: int
        :param text_channel: The text channel the song was added from
        :type text_channel: discord.Channel
        :param image: Link to the artwork or thumbnail of the song
        :type image: str
        :param song_url: A URL to the song
        :type song_url: str
        """
        self.stream_url = stream_url
        self.title = title
        self.requester = requester
        self.length = length
        self.text_channel = text_channel
        self.image = image
        self.song_url = song_url
        self._last_resume = datetime.datetime.fromtimestamp(0)
        self._seconds_played = 0  # used for when the song is paused

    def play(self):
        """
        Used for tracking elapsed time. Call this when the song starts playing or is resumed.
        """
        self._last_resume = datetime.datetime.now()

    def pause(self):
        """
        Used for tracking elapsed time. Call this when the song is paused.
        """
        now = datetime.datetime.now()
        delta = (now - self._last_resume).seconds
        self._seconds_played += delta

    def elapsed(self):
        """
        Gets the elapsed play time.

        :return: Elapsed play time in seconds
        :rtype: int
        """
        now = datetime.datetime.now()
        return (now - self._last_resume).seconds + self._seconds_played

