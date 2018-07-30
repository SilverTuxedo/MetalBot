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

from bot.metalbot import MetalBot
import bot.utils
import configparser

print("starting...")

config_params = {
    "Login": ["Token"],
    "Permissions": ["OwnerID", "OwnerRole"],
    "Preferences": ["CommandPrefix", "DefaultVolume", "MaxPlaylistLength", "MaxSongLength", "MentionPlaying"],
    "Votes": ["SelfInstaSkip", "PassSkipVoteAfter", "MinimalSkipCount", "MinimalSkipPercent", "MinimalClearCount",
              "MinimalClearPercent"]
}

config = configparser.ConfigParser()
config.read("config/options.ini")
missing = bot.utils.get_missing_from_config(config, config_params)

if len(missing) > 0:
    for m in missing:
        print("Missing %s: %s" % m)
    print("Config is missing options! Please check the config.")
elif len(config.get("Login", "Token")) == 0:
    print("Token is missing! Please update the config.")
else:
    client = MetalBot(config)
    client.run(config.get("Login", "Token"))
