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


class Permissions:
    def __init__(self, owner_id="", owner_role=""):
        """
        :param owner_id: The owner's unique Discord ID
        :type owner_id: str
        :param owner_role: The name of the role that should be treated as the owner
        :type owner_role: str
        """
        self.owner_id = owner_id
        self.owner_role = owner_role

    def is_owner(self, member):
        """
        Returns whether or not a server member should be considered the owner of the bot.

        :param member: A Discord server Member
        :type member: discord.Member
        :return: Should the user be considered an owner
        :rtype: bool
        """
        if len(self.owner_id) > 0 and member.id == self.owner_id:
            return True
        if len(self.owner_role) > 0 and self.owner_role in [role.name for role in member.roles]:
            return True
        return False
