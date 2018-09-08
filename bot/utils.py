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

import requests
import math
import sys
from lxml import html


def seconds_to_timestamp(secs):
    """
    Formats seconds to MM:SS or HH:MM:SS

    :param secs: Number of seconds
    :type secs: int
    :return: Time in MM:SS or HH:MM:SS
    :rtype: str
    """
    timestamp = ""
    hours = secs // 60 // 60
    mins = secs // 60 % 60
    secs %= 60
    if hours > 0:
        if hours < 10:
            timestamp += "0"
        timestamp += str(hours) + ":"
    if mins < 10:
        timestamp += "0"
    timestamp += str(mins) + ":"
    if secs < 10:
        timestamp += "0"
    timestamp += str(secs)
    return timestamp


def calc_min_votes_skip(current_count, listener_count, min_percent, min_users):
    """
    Returns the minimal number of people who need to vote to make the vote pass, taking into account the number of
    people who already voted.

    :param current_count: The number of people who already voted to skip
    :type current_count: int
    :param listener_count: The number of people who are listening to the bot
    :type listener_count: int
    :param min_percent: The minimum percent of people needed for the  vote to pass
    :type min_percent: float
    :param min_users: The minimum number of people needed for the  vote to pass
    :type min_users: int
    :return: The minimal number of extra skips needed
    :rtype: int
    """
    min_by_percent = math.ceil(listener_count * min_percent) - current_count
    min_by_users = min_users - current_count
    return min(min_by_percent, min_by_users)


def search_youtube(term):
    """
    Search YouTube.com for the term given and return a list with the resulting URLs

    :param term: A search term
    :type term: str
    :return: list with YouTube video URLs
    :rtype: list
    """
    resp = requests.get("https://www.youtube.com/results", params={
        "search_query": term
    })

    tree = html.fromstring(resp.content)
    elements = tree.xpath("//a[contains(@class, 'yt-uix-tile-link')]")
    results = []
    for e in elements:
        if  e.get('href').startswith("/watch"):
            results.append('https://www.youtube.com' + e.get('href'))
    return results


def progress_bar(percent, length=20, position='⬤', track='▬'):
    """
    Returns a progress bar made of characters.

    :param percent: The percent of progress made. Range: 0.0-1.0.
    :type percent: float
    :param length: The length of the bar
    :type length: int
    :param position: The character that represents the current scrubbing location
    :type position: str
    :param track: The character that represents the scrubbing track
    :type track: str
    :return: The progress bar
    :rtype: str
    """
    if percent > 1:
        percent = 1
    elif percent < 0:
        percent = 0

    bar = list(track * length)
    location = round(percent * (length - 1))
    bar[location] = position
    return "".join(bar)


def get_missing_from_config(config, params):
    missing = []
    for section in params:
        for option in params[section]:
            if not config.has_option(section, option):
                missing.append((section, option))
    return missing


def is_member_deafened(member):
    """
    Returns if a member is deafened, either by themselves or the server.

    :param member: The member to check for
    :type member: discord.Member
    :return: Whether or not the member is deafened.
    :rtype: bool
    """
    return member.voice.self_deaf or member.voice.deaf


def safe_print(text, end="\n", flush=True):
    """
    Safely prints text to the terminal

    :param text: Text to print
    :type text: str
    :param end: Additional string added after text
    :type end: str
    :param flush: Whether or not to flush the system buffer
    :type flush: bool
    """
    sys.stdout.buffer.write((text + end).encode('utf-8', 'replace'))
    if flush:
        sys.stdout.flush()

