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

from bot import song
from bot import utils
import pafy


def get_pafy_song(pafy_obj):
    """
    Builds and returns a Song from a Pafy object.

    :param pafy_obj: The pafy object to create the song from
    :type pafy_obj: pafy.Pafy
    :return: The song with details from the pafy object
    :rtype: song.Song
    """
    audio_stream = pafy_obj.getbestaudio()
    return song.Song(
        stream_url=audio_stream.url,
        title=pafy_obj.title,
        length=pafy_obj.length,
        image=pafy_obj.bigthumb if pafy_obj.bigthumb else pafy_obj.thumb,
        song_url="https://www.youtube.com/watch?v=" + pafy_obj.videoid
    )


def get_youtube_song(url):
    """
    Builds and returns a Song from a YouTube URL.

    :param url: URL of the video
    :type url: str
    :return: The song
    :rtype: song.Song
    """
    video = pafy.new(url)
    audio_stream = video.getbestaudio()

    return song.Song(
        stream_url=audio_stream.url,
        title=video.title,
        length=video.length,
        image=video.bigthumb if video.bigthumb else video.thumb,
        song_url="https://www.youtube.com/watch?v=" + video.videoid
    )


def get_ytsearch_song(term):
    """
    Searches YouTube for the term given and returns a Song based on the first YouTube result.

    :param term: The search term
    :type term: str
    :return: The song, None if no song was found.
    :rtype: song.Song
    """

    urls = utils.search_youtube(term)
    if len(urls) > 0:
        return get_youtube_song(urls[0])
    else:
        return None


def get_ytplaylist_pafys(playlist_url):
    """
    Returns a dict with :class:`pafy.Pafy` objects that each represent an item in the playlist.

    :param playlist_url: URL of the playlist
    :type playlist_url: str
    :return: A dict of :class:`pafy.Pafy` objects.
    :rtype: dict
    """
    playlist = pafy.get_playlist(playlist_url)
    return playlist["items"]


def get_ytplaylist_songs(playlist_url, limits=None):
    """
    Returns a list of :class:`song.Song` objects from the given playlist. This takes into account limits like the max
    number of songs to process and the max song length

    :param playlist_url: URL of the playlist
    :type playlist_url: str
    :param limits: A dictionary. Supported limits: MaxSongCount: int / MaxSongLength: int
    :type limits: dict
    :return: A tuple: (list of :class:`song.Song` objects, number of songs removed by filters).
    :rtype: tuple
    """

    playlist = pafy.get_playlist(playlist_url)
    playlist_dict = playlist["items"]
    song_count = len(playlist_dict)

    if limits is None:
        limits = dict()

    if limits.get("MaxSongCount") is not None:
        if song_count > limits["MaxSongCount"]:
            song_count = limits["MaxSongCount"]

    songs = []
    for element in playlist_dict:
        video = element['pafy']
        utils.safe_print(("processing " + str(video.title)))
        try:
            newsong = get_pafy_song(video)
            if newsong is not None:
                if not (limits.get("MaxSongLength") is not None and newsong.length > limits.get("MaxSongLength")):
                    songs.append(newsong)
        except ValueError as e:
            utils.safe_print("Value error! " + str(e))
        except OSError as e:
            utils.safe_print("OS error! " + str(e))

        if len(songs) >= song_count:
            break

    removed_count = len(playlist_dict) - len(songs)

    return songs, removed_count

