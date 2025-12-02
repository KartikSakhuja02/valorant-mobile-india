import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import re
import os
import json
import io
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from services import db


# Timezone mappings
TIMEZONE_MAP = {
    'IST': 'Asia/Kolkata',
    'CET': 'Europe/Paris',
    'CEST': 'Europe/Paris',  # Central European Summer Time
    'EST': 'America/New_York',
    'EDT': 'America/New_York',  # Eastern Daylight Time
    'CST': 'America/Chicago',
    'CDT': 'America/Chicago',  # Central Daylight Time
    'MST': 'America/Denver',
    'MDT': 'America/Denver',  # Mountain Daylight Time
    'PST': 'America/Los_Angeles',
    'PDT': 'America/Los_Angeles',  # Pacific Daylight Time
    'GMT': 'Europe/London',
    'BST': 'Europe/London',  # British Summer Time
    'JST': 'Asia/Tokyo',
    'KST': 'Asia/Seoul',
    'AEST': 'Australia/Sydney',
    'AEDT': 'Australia/Sydney',  # Australian Eastern Daylight Time
    'NZST': 'Pacific/Auckland',
    'NZDT': 'Pacific/Auckland',  # New Zealand Daylight Time
    'SGT': 'Asia/Singapore',
    'HKT': 'Asia/Hong_Kong',
    'PHT': 'Asia/Manila',
    'WIB': 'Asia/Jakarta',
    'PKT': 'Asia/Karachi',
    'GST': 'Asia/Dubai',  # Gulf Standard Time
    'MSK': 'Europe/Moscow',
    'EET': 'Europe/Athens',
    'EEST': 'Europe/Athens',  # Eastern European Summer Time
    'BRT': 'America/Sao_Paulo',
    'ART': 'America/Argentina/Buenos_Aires',
    'VET': 'America/Caracas',
}


def parse_time_with_timezone(time_str: str):
    """
    Parse time string like '7PM IST' or '9:30PM CET' and return hour, minute, timezone
    Returns: (hour_24, minute, timezone_abbr) or None if invalid
    """
    # Match patterns like: 7PM IST, 9:30PM CET, 10:45 PM EST, etc.
    pattern = r'(\d{1,2})(?::(\d{2}))?\s*(AM|PM)\s+([A-Z]{3,4})'
    match = re.search(pattern, time_str.upper())
    
    if not match:
        return None
    
    hour = int(match.group(1))
    minute = int(match.group(2)) if match.group(2) else 0
    period = match.group(3)
    timezone = match.group(4)
    
    # Validate timezone
    if timezone not in TIMEZONE_MAP:
        return None
    
    # Convert to 24-hour format
    if period == 'PM' and hour != 12:
        hour += 12
    elif period == 'AM' and hour == 12:
        hour = 0
    
    # Validate hour and minute
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None
    
    return (hour, minute, timezone)


def convert_time_to_timezone(hour: int, minute: int, from_tz: str, to_tz: str) -> tuple:
    """
    Convert time from one timezone to another
    Returns: (hour_24, minute, formatted_string)
    """
    try:
        # Create a datetime object for today with the given time
        today = datetime.now()
        source_tz = ZoneInfo(TIMEZONE_MAP[from_tz])
        target_tz = ZoneInfo(TIMEZONE_MAP[to_tz])
        
        # Create time in source timezone
        dt_source = datetime(today.year, today.month, today.day, hour, minute, tzinfo=source_tz)
        
        # Convert to target timezone
        dt_target = dt_source.astimezone(target_tz)
        
        # Format the time
        hour_12 = dt_target.hour % 12
        if hour_12 == 0:
            hour_12 = 12
        period = 'AM' if dt_target.hour < 12 else 'PM'
        
        if dt_target.minute == 0:
            formatted = f"{hour_12}{period} {to_tz}"
        else:
            formatted = f"{hour_12}:{dt_target.minute:02d}{period} {to_tz}"
        
        return (dt_target.hour, dt_target.minute, formatted)
    except:
        return (hour, minute, f"{hour}:{minute:02d}")


class ScrimRequestView(View):
    """View for accepting scrim requests or getting notified"""
    def __init__(self, request_id: int, requester_captain_id: int, acceptor_captain_id: int, cog):
        super().__init__(timeout=86400)  # 24 hours timeout
        self.request_id = request_id
        self.requester_captain_id = requester_captain_id
        self.acceptor_captain_id = acceptor_captain_id
        self.cog = cog
    
    @discord.ui.button(label="✅ Accept Scrim", style=discord.ButtonStyle.success)
    async def accept_button(self, interaction: discord.Interaction, button: Button):
        """Accept this scrim request"""
        if interaction.user.id != self.acceptor_captain_id:
            await interaction.response.send_message("This button is not for you!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Check if this request is still available
            request = await db.get_scrim_request_by_id(self.request_id)
            if not request:
                await interaction.followup.send(
                    "❌ This scrim request no longer exists!",
                    ephemeral=True
                )
                # Disable buttons
                for item in self.children:
                    item.disabled = True
                await interaction.edit_original_response(view=self)
                return
            
            # Check if request is in_progress (another captain is scheduling with them)
            if request['status'] == 'in_progress':
                # Get the teams involved
                request_team = await db.get_team_by_id(request['team_id'])
                request_team_name = f"{request_team['name']} [{request_team['tag']}]" if request_team else "Unknown"
                
                # Find who they're scheduling with
                matches = await db.get_captain_pending_matches(request['captain_discord_id'])
                other_team_name = "another team"
                if matches:
                    match = matches[0]
                    other_captain_id = match['captain_2_discord_id'] if match['captain_1_discord_id'] == request['captain_discord_id'] else match['captain_1_discord_id']
                    other_team = await db.get_team_by_captain(other_captain_id)
                    if not other_team:
                        other_team = await db.get_player_team(other_captain_id)
                    other_team_name = f"{other_team['name']} [{other_team['tag']}]" if other_team else "another team"
                
                await interaction.followup.send(
                    f"⚠️ **{request_team_name}** is currently scheduling a scrim with **{other_team_name}**.\n\n"
                    f"Click the 🔔 **Notify Me** button to get notified if their match doesn't get scheduled!",
                    ephemeral=True
                )
                return
            
            # Check if request status is not pending
            if request['status'] != 'pending':
                await interaction.followup.send(
                    f"❌ This scrim request is no longer available! (Status: {request['status']})",
                    ephemeral=True
                )
                # Disable buttons
                for item in self.children:
                    item.disabled = True
                await interaction.edit_original_response(view=self)
                return
            
            # Check if acceptor already has a pending match
            pending_matches = await db.get_captain_pending_matches(self.acceptor_captain_id)
            if pending_matches:
                await interaction.followup.send(
                    "⚠️ You already have a pending scrim match! Please approve/decline it first.",
                    ephemeral=True
                )
                return
            
            # Check if acceptor has a pending request
            acceptor_request = await db.get_captain_pending_request(self.acceptor_captain_id)
            if not acceptor_request:
                await interaction.followup.send(
                    "❌ You don't have an active scrim request! Post one in the LFS channel first.",
                    ephemeral=True
                )
                return
            
            # Create a scrim match between these two
            await self.cog.create_scrim_match_from_requests(
                request, 
                acceptor_request, 
                interaction.user
            )
            
            # Disable buttons
            for item in self.children:
                item.disabled = True
            await interaction.edit_original_response(
                content=interaction.message.content + "\n\n✅ **You accepted this scrim request!**",
                view=self
            )
            
            await interaction.followup.send(
                "✅ Scrim request accepted! Both captains will be notified.",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error accepting scrim: {str(e)}",
                ephemeral=True
            )
    
    @discord.ui.button(label="🔔 Notify Me", style=discord.ButtonStyle.secondary)
    async def notify_button(self, interaction: discord.Interaction, button: Button):
        """Get notified when this scrim becomes available"""
        if interaction.user.id != self.acceptor_captain_id:
            await interaction.response.send_message("This button is not for you!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Add to waitlist (we'll implement this in the database)
            await db.add_to_scrim_waitlist(self.request_id, self.acceptor_captain_id)
            
            await interaction.followup.send(
                "🔔 You'll be notified if this scrim becomes available!",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error: {str(e)}",
                ephemeral=True
            )


class ScrimApprovalView(View):
    """View for scrim approval buttons"""
    def __init__(self, match_id: int, captain_num: int, opponent_name: str):
        super().__init__(timeout=3600)  # 1 hour timeout
        self.match_id = match_id
        self.captain_num = captain_num
        self.opponent_name = opponent_name
    
    @discord.ui.button(label="✅ Approve", style=discord.ButtonStyle.success)
    async def approve_button(self, interaction: discord.Interaction, button: Button):
        """Approve the scrim match"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Update approval status
            await db.update_scrim_match_approval(self.match_id, self.captain_num, True)
            
            # Get match details
            match = await db.get_scrim_match_by_id(self.match_id)
            
            if not match:
                await interaction.followup.send("❌ Match not found!", ephemeral=True)
                return
            
            # Check if both captains approved
            if match['captain_1_approved'] and match['captain_2_approved']:
                # Both approved - start chat relay and ask for format selection
                await db.update_scrim_match_status(self.match_id, 'chat_active')
                await db.update_scrim_request_status(match['request_id_1'], 'matched')
                await db.update_scrim_request_status(match['request_id_2'], 'matched')
                
                # Clear waitlists for both requests (match successful, don't notify)
                await db.clear_scrim_waitlist(match['request_id_1'])
                await db.clear_scrim_waitlist(match['request_id_2'])
                
                # Notify both captains
                bot = interaction.client
                captain_1 = await bot.fetch_user(match['captain_1_discord_id'])
                captain_2 = await bot.fetch_user(match['captain_2_discord_id'])
                
                # Get the original formats from their requests
                request_1 = await db.get_scrim_request_by_id(match['request_id_1'])
                request_2 = await db.get_scrim_request_by_id(match['request_id_2'])
                
                format_1 = request_1['match_type'].upper() if request_1 else 'Unknown'
                format_2 = request_2['match_type'].upper() if request_2 else 'Unknown'
                
                match_info = (
                    f"✅ **SCRIM MATCH CONFIRMED!**\n\n"
                    f"Both captains have approved!\n\n"
                    f"🔄 **Chat relay is now active!**\n"
                    f"Any message you send to me will be forwarded to the other captain.\n\n"
                    f"**Next Step: Choose Format**\n"
                    f"Please select which format you want to play.\n"
                    f"You can discuss via DM (messages are being relayed)."
                )
                
                try:
                    await captain_1.send(match_info)
                except:
                    pass
                
                try:
                    await captain_2.send(match_info)
                except:
                    pass
                
                # Send format selection buttons to both captains
                cog = interaction.client.get_cog('Scrim')
                if cog:
                    await cog.send_format_selection(match, captain_1, captain_2, format_1, format_2)
                
                # Disable buttons
                for item in self.children:
                    item.disabled = True
                
                await interaction.edit_original_response(
                    content=f"✅ **Match Confirmed!**\n\nBoth captains approved. Choose your format now!\nChat relay is active - you can discuss the format via DM.",
                    view=self
                )
                
            else:
                # Only this captain approved, waiting for other
                await interaction.followup.send(
                    f"✅ You approved the scrim with **{self.opponent_name}**!\n"
                    f"Waiting for the other captain to approve...",
                    ephemeral=True
                )
                
                # Disable buttons for this user
                for item in self.children:
                    item.disabled = True
                await interaction.edit_original_response(view=self)
                
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error processing approval: {str(e)}",
                ephemeral=True
            )
    
    @discord.ui.button(label="❌ Decline", style=discord.ButtonStyle.danger)
    async def decline_button(self, interaction: discord.Interaction, button: Button):
        """Decline the scrim match"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Update match status to declined (request cancelled)
            await db.update_scrim_match_status(self.match_id, 'declined')
            
            # Get match details
            match = await db.get_scrim_match_by_id(self.match_id)
            
            if match:
                # Get the scrim cog to access helper methods
                scrim_cog = interaction.client.get_cog('Scrim')
                
                # Mark BOTH requests back to 'pending' (available again)
                await db.update_scrim_request_status(match['request_id_1'], 'pending')
                await db.update_scrim_request_status(match['request_id_2'], 'pending')
                
                # Get both requests to notify waitlist
                request_1 = await db.get_scrim_request_by_id(match['request_id_1'])
                request_2 = await db.get_scrim_request_by_id(match['request_id_2'])
                
                # Notify the other captain
                bot = interaction.client
                other_captain_id = (match['captain_2_discord_id'] 
                                   if self.captain_num == 1 
                                   else match['captain_1_discord_id'])
                
                try:
                    other_captain = await bot.fetch_user(other_captain_id)
                    await other_captain.send(
                        f"❌ **Scrim Match Declined**\n\n"
                        f"The scrim match with **{self.opponent_name}** was declined.\n"
                        f"Your scrim request is still active. You can continue looking for other teams!"
                    )
                except:
                    pass
                
                # Notify waitlisted captains that these requests are available again
                if scrim_cog and request_1 and request_2:
                    await scrim_cog.notify_waitlist_available(request_1, request_2)
            
            # Disable buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.edit_original_response(
                content=f"❌ You declined the scrim with **{self.opponent_name}**.",
                view=self
            )
            
            await interaction.followup.send(
                "✅ Scrim declined. Your request is still active, you can accept other scrims!",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error processing decline: {str(e)}",
                ephemeral=True
            )


class FormatSelectionView(View):
    """View for selecting scrim format (BO1/BO3/BO5)"""
    def __init__(self, match_id: int, captain_discord_id: int, captain_num: int, format_1: str, format_2: str, cog, other_captain_id: int):
        super().__init__(timeout=None)  # Persistent view
        self.match_id = match_id
        self.captain_discord_id = captain_discord_id
        self.captain_num = captain_num
        self.format_1 = format_1
        self.format_2 = format_2
        self.cog = cog
        self.other_captain_id = other_captain_id
    
    @discord.ui.button(label="Captain 1's Format", style=discord.ButtonStyle.primary, custom_id="format_cap1")
    async def format_1_button(self, interaction: discord.Interaction, button: Button):
        """Select captain 1's format"""
        if interaction.user.id != self.captain_discord_id:
            await interaction.response.send_message("This button is not for you!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        await self.cog.handle_format_selection(self.match_id, self.captain_num, self.format_1, interaction.user)
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)
        
        await interaction.followup.send(
            f"✅ You selected **{self.format_1}** format!",
            ephemeral=True
        )
    
    @discord.ui.button(label="Captain 2's Format", style=discord.ButtonStyle.primary, custom_id="format_cap2")
    async def format_2_button(self, interaction: discord.Interaction, button: Button):
        """Select captain 2's format"""
        if interaction.user.id != self.captain_discord_id:
            await interaction.response.send_message("This button is not for you!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        await self.cog.handle_format_selection(self.match_id, self.captain_num, self.format_2, interaction.user)
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)
        
        await interaction.followup.send(
            f"✅ You selected **{self.format_2}** format!",
            ephemeral=True
        )
    
    @discord.ui.button(label="Other Format", style=discord.ButtonStyle.secondary, custom_id="format_other")
    async def other_format_button(self, interaction: discord.Interaction, button: Button):
        """Select other format"""
        if interaction.user.id != self.captain_discord_id:
            await interaction.response.send_message("This button is not for you!", ephemeral=True)
            return
        
        # Show modal to enter custom format
        modal = FormatInputModal(self.match_id, self.captain_num, self.cog)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="❌ Cancel Scrim", style=discord.ButtonStyle.danger, custom_id="format_cancel")
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        """Cancel the scrim"""
        if interaction.user.id != self.captain_discord_id:
            await interaction.response.send_message("This button is not for you!", ephemeral=True)
            return
        
        # Show modal to ask for reason using stored other_captain_id
        modal = ScrimCancelReasonModal(self.match_id, self.captain_discord_id, 
                                       self.other_captain_id, self.cog)
        await interaction.response.send_modal(modal)


class FormatInputModal(discord.ui.Modal, title="Enter Format"):
    """Modal for entering custom format"""
    
    format_input = discord.ui.TextInput(
        label="Format (BO1, BO3, or BO5)",
        style=discord.TextStyle.short,
        placeholder="Enter BO1, BO3, or BO5",
        required=True,
        max_length=10
    )
    
    def __init__(self, match_id: int, captain_num: int, cog):
        super().__init__()
        self.match_id = match_id
        self.captain_num = captain_num
        self.cog = cog
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Validate format
        format_text = self.format_input.value.strip().upper()
        if not re.match(r'^BO[135]$', format_text):
            await interaction.followup.send(
                "❌ Invalid format! Please enter BO1, BO3, or BO5.",
                ephemeral=True
            )
            return
        
        await self.cog.handle_format_selection(self.match_id, self.captain_num, format_text, interaction.user)
        
        await interaction.followup.send(
            f"✅ You selected **{format_text}** format!",
            ephemeral=True
        )


class MapBanConfirmView(View):
    """View for confirming map banning start"""
    def __init__(self, match_id: int, requester_name: str, cog):
        super().__init__(timeout=300)  # 5 minute timeout
        self.match_id = match_id
        self.requester_name = requester_name
        self.cog = cog
    
    @discord.ui.button(label="✅ Yes, Start Map Banning", style=discord.ButtonStyle.success)
    async def confirm_button(self, interaction: discord.Interaction, button: Button):
        """Confirm starting map banning"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            match = await db.get_scrim_match_by_id(self.match_id)
            if match:
                await self.cog.start_map_banning(match, interaction.user)
                
            # Disable buttons
            for item in self.children:
                item.disabled = True
            await interaction.edit_original_response(view=self)
            
            await interaction.followup.send("✅ Map banning phase started!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
    
    @discord.ui.button(label="❌ No, Continue Chat", style=discord.ButtonStyle.danger)
    async def decline_button(self, interaction: discord.Interaction, button: Button):
        """Decline map banning"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            match = await db.get_scrim_match_by_id(self.match_id)
            if match:
                # Notify the requester that it was declined
                requester_id = match['captain_1_discord_id'] if interaction.user.id == match['captain_2_discord_id'] else match['captain_2_discord_id']
                requester = await interaction.client.fetch_user(requester_id)
                await requester.send(f"❌ **{interaction.user.display_name}** declined to start map banning. Chat relay continues.")
            
            # Disable buttons
            for item in self.children:
                item.disabled = True
            await interaction.edit_original_response(view=self)
            
            await interaction.followup.send("✅ Continuing chat relay.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)


class CancelScrimConfirmView(View):
    """View for confirming scrim cancellation"""
    def __init__(self, match_id: int, requester_name: str, cog):
        super().__init__(timeout=300)  # 5 minute timeout
        self.match_id = match_id
        self.requester_name = requester_name
        self.cog = cog
    
    @discord.ui.button(label="✅ Yes, Cancel Scrim", style=discord.ButtonStyle.success)
    async def confirm_button(self, interaction: discord.Interaction, button: Button):
        """Confirm scrim cancellation"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            match = await db.get_scrim_match_by_id(self.match_id)
            if match:
                await self.cog.cancel_scrim_match(match, interaction.user)
                
            # Disable buttons
            for item in self.children:
                item.disabled = True
            await interaction.edit_original_response(view=self)
            
            await interaction.followup.send("✅ Scrim cancelled. You've been added back to the queue.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
    
    @discord.ui.button(label="❌ No, Continue Scrim", style=discord.ButtonStyle.danger)
    async def decline_button(self, interaction: discord.Interaction, button: Button):
        """Decline cancellation"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            match = await db.get_scrim_match_by_id(self.match_id)
            if match:
                # Notify the requester that it was declined
                requester_id = match['captain_1_discord_id'] if interaction.user.id == match['captain_2_discord_id'] else match['captain_2_discord_id']
                requester = await interaction.client.fetch_user(requester_id)
                await requester.send(f"❌ **{interaction.user.display_name}** declined to cancel the scrim. Chat relay continues.")
            
            # Disable buttons
            for item in self.children:
                item.disabled = True
            await interaction.edit_original_response(view=self)
            
            await interaction.followup.send("✅ Continuing scrim.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)


class CoinTossView(View):
    """View for coin toss selection"""
    def __init__(self, match: dict, caller: discord.User, other: discord.User, cog):
        super().__init__(timeout=300)
        self.match = match
        self.caller = caller
        self.other = other
        self.cog = cog
    
    @discord.ui.button(label="🔴 Heads", style=discord.ButtonStyle.primary)
    async def heads_button(self, interaction: discord.Interaction, button: Button):
        await self.do_toss(interaction, "Heads")
    
    @discord.ui.button(label="⚫ Tails", style=discord.ButtonStyle.secondary)
    async def tails_button(self, interaction: discord.Interaction, button: Button):
        await self.do_toss(interaction, "Tails")
    
    async def do_toss(self, interaction: discord.Interaction, call: str):
        """Perform the coin toss"""
        await interaction.response.defer(ephemeral=True)
        
        import random
        result = random.choice(["Heads", "Tails"])
        won = (call == result)
        
        winner = self.caller if won else self.other
        loser = self.other if won else self.caller
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)
        
        # Notify both captains
        await self.caller.send(
            f"🪙 **COIN TOSS RESULT**\n\n"
            f"You called: **{call}**\n"
            f"Result: **{result}**\n\n"
            f"{'🎉 You WON the toss!' if won else '❌ You LOST the toss.'}\n\n"
            f"**Winner:** {winner.display_name} - Bans first\n"
            f"**Loser:** {loser.display_name} - Picks sides"
        )
        
        await self.other.send(
            f"🪙 **COIN TOSS RESULT**\n\n"
            f"{self.caller.display_name} called: **{call}**\n"
            f"Result: **{result}**\n\n"
            f"{'🎉 You WON the toss!' if not won else '❌ You LOST the toss.'}\n\n"
            f"**Winner:** {winner.display_name} - Bans first\n"
            f"**Loser:** {loser.display_name} - Picks sides"
        )
        
        # Start map banning with the winner
        await self.cog.start_banning_maps(self.match, winner, loser)


class MapVetoView(View):
    """View for map veto (ban or pick)"""
    def __init__(self, match: dict, acting_captain: discord.User, maps: list, action: str, cog):
        super().__init__(timeout=300)
        self.match = match
        self.acting_captain = acting_captain
        self.maps = maps
        self.action = action  # 'ban' or 'pick'
        self.cog = cog
        
        # Add buttons for each map
        for map_name in maps:
            if action == 'ban':
                button = Button(label=f"🚫 Ban {map_name}", style=discord.ButtonStyle.danger)
            else:  # pick
                button = Button(label=f"✅ Pick {map_name}", style=discord.ButtonStyle.success)
            
            button.callback = self.create_veto_callback(map_name)
            self.add_item(button)
    
    def create_veto_callback(self, map_name: str):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.acting_captain.id:
                await interaction.response.send_message("This button is not for you!", ephemeral=True)
                return
            
            await interaction.response.defer(ephemeral=True)
            await self.cog.handle_veto_action(self.match, self.acting_captain, map_name, self.action)
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            await interaction.edit_original_response(view=self)
        return callback


class SideSelectionView(View):
    """View for selecting Attack or Defense side"""
    def __init__(self, match: dict, captain: discord.User, map_name: str, cog, is_decider: bool = False):
        super().__init__(timeout=300)
        self.match = match
        self.captain = captain
        self.map_name = map_name
        self.cog = cog
        self.is_decider = is_decider
    
    @discord.ui.button(label="⚔️ Attack", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def attack_button(self, interaction: discord.Interaction, button: Button):
        await self.select_side(interaction, "Attack")
    
    @discord.ui.button(label="🛡️ Defense", style=discord.ButtonStyle.primary, emoji="🛡️")
    async def defense_button(self, interaction: discord.Interaction, button: Button):
        await self.select_side(interaction, "Defense")
    
    async def select_side(self, interaction: discord.Interaction, side: str):
        if interaction.user.id != self.captain.id:
            await interaction.response.send_message("This button is not for you!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)
        
        if self.is_decider:
            await self.cog.handle_decider_side_selection(self.match, self.captain, self.map_name, side)
        else:
            await self.cog.handle_side_selection(self.match, self.captain, self.map_name, side)


class MapBanView(View):
    """LEGACY View for old banning system - kept for compatibility"""
    def __init__(self, match: dict, banner: discord.User, maps: list, ban_count: int, cog):
        super().__init__(timeout=300)
        self.match = match
        self.banner = banner
        self.maps = maps
        self.ban_count = ban_count
        self.cog = cog
        
        # Add buttons for each map
        for map_name in maps:
            button = Button(label=f"🚫 Ban {map_name}", style=discord.ButtonStyle.danger)
            button.callback = self.create_ban_callback(map_name)
            self.add_item(button)
    
    def create_ban_callback(self, map_name: str):
        async def callback(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            await self.cog.handle_map_ban(self.match, self.banner, map_name, self.maps, self.ban_count)
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            await interaction.edit_original_response(view=self)
        return callback


class SidePickView(View):
    """View for picking sides (Attack/Defense)"""
    def __init__(self, match: dict, picker: discord.User, map_name: str, map_index: int, total_maps: int, cog):
        super().__init__(timeout=300)
        self.match = match
        self.picker = picker
        self.map_name = map_name
        self.map_index = map_index
        self.total_maps = total_maps
        self.cog = cog
    
    @discord.ui.button(label="⚔️ Attack", style=discord.ButtonStyle.danger)
    async def attack_button(self, interaction: discord.Interaction, button: Button):
        await self.pick_side(interaction, "Attack")
    
    @discord.ui.button(label="🛡️ Defense", style=discord.ButtonStyle.primary)
    async def defense_button(self, interaction: discord.Interaction, button: Button):
        await self.pick_side(interaction, "Defense")
    
    async def pick_side(self, interaction: discord.Interaction, side: str):
        await interaction.response.defer(ephemeral=True)
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)
        
        await self.cog.handle_side_pick(self.match, self.picker, self.map_name, side, self.map_index, self.total_maps)


class ScrimCompleteCheckView(View):
    """View for checking if scrim is complete"""
    def __init__(self, match_id: int, captain_discord_id: int, other_captain_id: int, cog):
        super().__init__(timeout=None)  # Persistent view
        self.match_id = match_id
        self.captain_discord_id = captain_discord_id
        self.other_captain_id = other_captain_id
        self.cog = cog
        self.custom_id_prefix = f"scrim_complete_{match_id}_{captain_discord_id}"
    
    @discord.ui.button(label="✅ Yes, We're Done", style=discord.ButtonStyle.success, custom_id="scrim_done")
    async def done_button(self, interaction: discord.Interaction, button: Button):
        """Mark scrim as complete and request screenshots"""
        if interaction.user.id != self.captain_discord_id:
            await interaction.response.send_message("This button is not for you!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # Check if other captain also clicked done
        if not hasattr(self.cog, 'scrim_completion_votes'):
            self.cog.scrim_completion_votes = {}
        
        match_key = f"match_{self.match_id}"
        if match_key not in self.cog.scrim_completion_votes:
            self.cog.scrim_completion_votes[match_key] = set()
        
        self.cog.scrim_completion_votes[match_key].add(self.captain_discord_id)
        
        # Check if both captains voted yes
        if len(self.cog.scrim_completion_votes[match_key]) >= 2:
            # Both captains ready, request screenshots
            await self.cog.request_scrim_screenshots(self.match_id)
            
            # Disable buttons
            for item in self.children:
                item.disabled = True
            await interaction.edit_original_response(view=self)
            
            await interaction.followup.send(
                "✅ Both captains confirmed! Please upload your match result screenshot now.",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "✅ Waiting for the other captain to confirm...",
                ephemeral=True
            )
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger, custom_id="scrim_cancel")
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        """Cancel the scrim"""
        if interaction.user.id != self.captain_discord_id:
            await interaction.response.send_message("This button is not for you!", ephemeral=True)
            return
        
        # Show modal to ask for reason
        modal = ScrimCancelReasonModal(self.match_id, self.captain_discord_id, self.other_captain_id, self.cog)
        await interaction.response.send_modal(modal)


class ScrimCancelReasonModal(discord.ui.Modal, title="Cancel Scrim"):
    """Modal for entering cancellation reason"""
    
    reason = discord.ui.TextInput(
        label="Reason for cancellation",
        style=discord.TextStyle.paragraph,
        placeholder="Please provide a reason for cancelling this scrim...",
        required=True,
        max_length=500
    )
    
    def __init__(self, match_id: int, captain_discord_id: int, other_captain_id: int, cog):
        super().__init__()
        self.match_id = match_id
        self.captain_discord_id = captain_discord_id
        self.other_captain_id = other_captain_id
        self.cog = cog
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Store this captain's reason
        if not hasattr(self.cog, 'scrim_cancel_reasons'):
            self.cog.scrim_cancel_reasons = {}
        
        match_key = f"match_{self.match_id}"
        if match_key not in self.cog.scrim_cancel_reasons:
            self.cog.scrim_cancel_reasons[match_key] = {}
        
        self.cog.scrim_cancel_reasons[match_key][self.captain_discord_id] = self.reason.value
        
        # Check if other captain also cancelled
        if len(self.cog.scrim_cancel_reasons[match_key]) >= 2:
            # Both captains cancelled, process cancellation
            await self.cog.process_scrim_cancellation(self.match_id, self.cog.scrim_cancel_reasons[match_key])
            
            # Send confirmation to this captain
            await interaction.followup.send(
                "✅ Both captains have agreed to cancel. The scrim has been cancelled and logged.",
                ephemeral=True
            )
            
            # Send confirmation to other captain too
            try:
                other_captain = await self.cog.bot.fetch_user(self.other_captain_id)
                await other_captain.send(
                    "✅ **Scrim Cancelled**\n\n"
                    "Both captains have agreed to cancel the scrim. The cancellation has been logged."
                )
            except:
                pass
        else:
            # Send cancel button with reason to other captain
            try:
                other_captain = await self.cog.bot.fetch_user(self.other_captain_id)
                
                # Create embed showing the reason
                embed = discord.Embed(
                    title="⚠️ Cancellation Request",
                    description="The other captain wants to cancel the scrim.",
                    color=0xFFA500
                )
                embed.add_field(
                    name="Their Reason",
                    value=self.reason.value,
                    inline=False
                )
                embed.add_field(
                    name="Action Required",
                    value="Click the ❌ Cancel button below and provide your reason to complete the cancellation.",
                    inline=False
                )
                
                # Create a new cancel modal view
                view = discord.ui.View(timeout=600)
                cancel_button = discord.ui.Button(
                    label="❌ Cancel Scrim",
                    style=discord.ButtonStyle.danger
                )
                
                async def cancel_callback(button_interaction: discord.Interaction):
                    if button_interaction.user.id != self.other_captain_id:
                        await button_interaction.response.send_message(
                            "This button is not for you!",
                            ephemeral=True
                        )
                        return
                    
                    # Show modal for other captain's reason
                    modal = ScrimCancelReasonModal(
                        self.match_id,
                        self.other_captain_id,
                        self.captain_discord_id,
                        self.cog
                    )
                    await button_interaction.response.send_modal(modal)
                
                cancel_button.callback = cancel_callback
                view.add_item(cancel_button)
                
                await other_captain.send(embed=embed, view=view)
            except Exception as e:
                print(f"Error sending cancel request to other captain: {e}")
            
            await interaction.followup.send(
                "✅ Your cancellation reason has been submitted. Waiting for the other captain to respond...",
                ephemeral=True
            )


class ScoreConfirmationView(View):
    """View for confirming detected scores"""
    def __init__(self, match_id: int, captain_discord_id: int, team_1_score: int, team_2_score: int, cog):
        super().__init__(timeout=300)
        self.match_id = match_id
        self.captain_discord_id = captain_discord_id
        self.team_1_score = team_1_score
        self.team_2_score = team_2_score
        self.cog = cog
    
    @discord.ui.button(label="✅ Correct", style=discord.ButtonStyle.success)
    async def correct_button(self, interaction: discord.Interaction, button: Button):
        """Confirm the scores are correct"""
        if interaction.user.id != self.captain_discord_id:
            await interaction.response.send_message("This button is not for you!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # Store this captain's confirmation
        if not hasattr(self.cog, 'score_confirmations'):
            self.cog.score_confirmations = {}
        
        match_key = f"match_{self.match_id}"
        if match_key not in self.cog.score_confirmations:
            self.cog.score_confirmations[match_key] = set()
        
        self.cog.score_confirmations[match_key].add(self.captain_discord_id)
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)
        
        # Check if both captains confirmed
        if len(self.cog.score_confirmations[match_key]) >= 2:
            # Both confirmed, save to database
            await self.cog.save_scrim_results(self.match_id, self.team_1_score, self.team_2_score)
            
            await interaction.followup.send(
                "✅ Scores confirmed and recorded! Thank you for playing.",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "✅ Score confirmed. Waiting for the other captain...",
                ephemeral=True
            )
    
    @discord.ui.button(label="❌ Incorrect", style=discord.ButtonStyle.danger)
    async def incorrect_button(self, interaction: discord.Interaction, button: Button):
        """Reject the scores"""
        if interaction.user.id != self.captain_discord_id:
            await interaction.response.send_message("This button is not for you!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # Disable buttons
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)
        
        await interaction.followup.send(
            "❌ Scores marked as incorrect. Please contact an admin to manually record the results.",
            ephemeral=True
        )
        
        # Notify both captains and log
        await self.cog.handle_score_dispute(self.match_id, interaction.user)


class Scrim(commands.Cog):
    """Scrim management system for Looking for Scrim (LFS)"""
    
    def __init__(self, bot):
        self.bot = bot
        self.lfs_channel_name = "looking-for-scrim"  # Channel name to monitor
        self.lfs_channel_id = int(os.getenv('LFS_CHANNEL_ID', 0)) if os.getenv('LFS_CHANNEL_ID') else None
        self._instructions_sent = False  # Flag to send message only once
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Send instructions message when bot starts"""
        # Only send once
        if self._instructions_sent:
            return
        
        if not self.lfs_channel_id:
            print("⚠️  LFS_CHANNEL_ID not set in .env file. Skipping LFS instructions message.")
            print("💡 Tip: Add LFS_CHANNEL_ID to your .env file to enable auto-instructions.")
            return
        
        try:
            channel = self.bot.get_channel(self.lfs_channel_id)
            if not channel:
                print(f"❌ LFS channel not found with ID: {self.lfs_channel_id}")
                print(f"💡 Tip: Make sure the channel exists and the bot has access to it.")
                return
            
            # Purge all messages in the channel first
            print(f"🧹 Purging all messages in {channel.name}...")
            deleted = await channel.purge(limit=100)  # Purge up to 100 messages
            print(f"🗑️ Deleted {len(deleted)} messages from {channel.name}")
            
            # Create a comprehensive Discord embed UI
            embed = discord.Embed(
                title="🎮 Looking for Scrim",
                description="Post your scrim requests below and get automatically matched with teams!",
                color=0xFF4654  # Valorant red
            )
            
            # Message Format
            embed.add_field(
                name="📝 Message Format",
                value="```\nLFS [BO1/BO3/BO5]\n[TIME], [REGION]\n```",
                inline=False
            )
            
            # Examples
            embed.add_field(
                name="💡 Examples",
                value=(
                    "```\nLFS BO3\n7PM IST, APAC\n```\n"
                    "```\nLFS BO5\n9PM CET, EMEA\n```"
                ),
                inline=False
            )
            
            # Valid Options
            embed.add_field(
                name="✅ Valid Match Types",
                value="`BO1` • `BO3` • `BO5`",
                inline=True
            )
            
            embed.add_field(
                name="🌍 Valid Regions",
                value="`APAC` • `EMEA` • `AMERICAS` • `INDIA`",
                inline=True
            )
            
            # How It Works
            embed.add_field(
                name="🔄 How It Works",
                value=(
                    "1. Post your request in the format above\n"
                    "2. Your message will be deleted and stored\n"
                    "3. Matched with teams in your region\n"
                    "4. Both captains see each other's preferences\n"
                    "5. Click ✅ Approve or ❌ Decline in DM\n"
                    "6. If both approve, scrim is confirmed! 🎉\n\n"
                    "**Note:** You may be matched with different BO/time - decide in DM!"
                ),
                inline=False
            )
            
            # Commands
            embed.add_field(
                name="⚙️ Commands",
                value="`/cancel-scrim` - Cancel your pending request",
                inline=False
            )
            
            # Footer
            embed.set_footer(text="⚠️ Important: DMs must be enabled to receive match notifications!")
            
            # Send only the embed (no text)
            await channel.send(embed=embed)
            
            self._instructions_sent = True  # Mark as sent
            print(f"✅ LFS instructions sent to channel: {channel.name}")
            
        except Exception as e:
            print(f"❌ Error sending LFS instructions: {e}")
            import traceback
            traceback.print_exc()
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen for LFS messages in the looking-for-scrim channel AND relay DMs between captains"""
        
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Check if it's a DM
        if isinstance(message.channel, discord.DMChannel):
            await self.handle_captain_dm(message)
            return
        
        # Check if it's in the LFS channel (by ID or name)
        is_lfs_channel = False
        if self.lfs_channel_id and message.channel.id == self.lfs_channel_id:
            is_lfs_channel = True
        elif message.channel.name == self.lfs_channel_name:
            is_lfs_channel = True
        
        if not is_lfs_channel:
            return
        
        # Parse the message format
        # Expected format:
        # LFS BO1/BO3/BO5
        # TIME, REGION (e.g., 7PM IST, APAC)
        
        content = message.content.strip()
        lines = content.split('\n')
        
        if len(lines) < 2:
            # Send error message
            error_msg = await message.channel.send(
                f"❌ {message.author.mention} Invalid format! Please use:\n"
                "```\nLFS BO1/BO3/BO5\n"
                "TIME, REGION (e.g., 7PM IST, APAC)\n```"
            )
            # Delete both messages after 10 seconds
            await message.delete()
            await error_msg.delete(delay=10)
            return
        
        # Parse first line: LFS BO1/BO3/BO5
        first_line = lines[0].strip().upper()
        match_type_match = re.search(r'LFS\s+(BO[135])', first_line)
        
        if not match_type_match:
            error_msg = await message.channel.send(
                f"❌ {message.author.mention} Invalid format! First line should be: `LFS BO1`, `LFS BO3`, or `LFS BO5`"
            )
            await message.delete()
            await error_msg.delete(delay=10)
            return
        
        match_type = match_type_match.group(1).lower()
        
        # Parse second line: TIME, REGION
        second_line = lines[1].strip()
        parts = [p.strip() for p in second_line.split(',')]
        
        if len(parts) < 2:
            error_msg = await message.channel.send(
                f"❌ {message.author.mention} Invalid format! Second line should be: `TIME, REGION`\n"
                "Example: `7PM IST, APAC`"
            )
            await message.delete()
            await error_msg.delete(delay=10)
            return
        
        time_part = parts[0].strip()
        region_input = parts[1].strip().upper()
        
        # Validate region
        valid_regions = ['APAC', 'EMEA', 'AMERICAS', 'INDIA']
        if region_input not in valid_regions:
            error_msg = await message.channel.send(
                f"❌ {message.author.mention} Invalid region! Must be one of: {', '.join(valid_regions)}"
            )
            await message.delete()
            await error_msg.delete(delay=10)
            return
        
        region = region_input.lower()
        
        # Parse the time with timezone
        parsed_time = parse_time_with_timezone(time_part)
        if not parsed_time:
            supported_tz = ', '.join(sorted(TIMEZONE_MAP.keys()))
            error_msg = await message.channel.send(
                f"❌ {message.author.mention} Invalid time format! Please use format like:\n"
                f"`7PM IST, APAC` or `9:30PM CET, EMEA`\n\n"
                f"**Supported timezones:** {supported_tz}"
            )
            await message.delete()
            await error_msg.delete(delay=20)
            return
        
        hour, minute, timezone = parsed_time
        
        # Convert to datetime object with timezone
        # Use today's date + the parsed time in the specified timezone
        tz = ZoneInfo(TIMEZONE_MAP[timezone])
        now = datetime.now(tz)
        time_slot = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If the time has already passed today, set it for tomorrow
        if time_slot < now:
            time_slot = time_slot + timedelta(days=1)
        
        # Delete the user's message immediately (valid format)
        await message.delete()
        
        # Get captain's team (MUST be registered to a team)
        try:
            captain_id = message.author.id
            
            # Check if user is part of ANY team (captain or member)
            team = await db.get_team_by_captain(captain_id)
            if not team:
                # Check if they're a member of a team
                team = await db.get_player_team(captain_id)
            
            if not team:
                error_msg = await message.channel.send(
                    f"❌ {message.author.mention} You must be registered to a team before you can look for scrims!"
                )
                await error_msg.delete(delay=15)
                return
            
            team_id = team['id']
            team_name = f"{team['name']} [{team['tag']}]"
            
            # Check if THIS TEAM already has a pending request (by any member)
            existing_request = await db.get_team_pending_request(team_id)
            if existing_request:
                # Get the member who posted it
                poster = await self.bot.fetch_user(existing_request['captain_discord_id'])
                poster_name = poster.name if poster else "Unknown"
                
                error_msg = await message.channel.send(
                    f"⚠️ {message.author.mention} Your team already has a pending LFS request posted by **{poster_name}**!\n"
                    "Only one request per team is allowed at a time."
                )
                await error_msg.delete(delay=15)
                return
            
            # Check if captain already has a pending match (being scheduled)
            pending_matches = await db.get_captain_pending_matches(captain_id)
            if pending_matches:
                error_msg = await message.channel.send(
                    f"⚠️ {message.author.mention} You already have a pending scrim match! "
                    "Please approve/decline it before creating a new request."
                )
                await error_msg.delete(delay=15)
                return
            
            # Create scrim request (expires in 24 hours)
            expires_at = datetime.utcnow() + timedelta(hours=24)
            request = await db.create_scrim_request(
                captain_discord_id=captain_id,
                team_id=team_id,
                region=region,
                match_type=match_type,
                time_slot=time_slot,
                timezone=timezone,
                expires_at=expires_at
            )
            
            # Send confirmation message (will be deleted after 15 seconds)
            # Format time_slot for display
            time_display = time_slot.strftime("%I:%M %p %Z") if isinstance(time_slot, datetime) else str(time_slot)
            confirm_msg = await message.channel.send(
                f"✅ **Scrim Request Posted!**\n\n"
                f"**Team:** {team_name}\n"
                f"**Posted by:** {message.author.mention}\n"
                f"**Match Type:** {match_type.upper()}\n"
                f"**Region:** {region.upper()}\n"
                f"**Time:** {time_display}\n\n"
                f"Check your DMs to see all available scrim requests! 🔍"
            )
            await confirm_msg.delete(delay=15)
            
            # Send all pending requests to this captain
            await self.send_all_scrim_requests(request, message.author)
            
            # Notify all OTHER pending captains about this NEW request
            await self.notify_other_captains(request, message.author)
            
        except Exception as e:
            error_msg = await message.channel.send(
                f"❌ {message.author.mention} Error creating scrim request: {str(e)}"
            )
            await error_msg.delete(delay=15)
    
    async def send_all_scrim_requests(self, new_request: dict, captain: discord.Member):
        """Send all available scrim requests to the captain who just posted"""
        try:
            # Get all pending requests (excluding this captain)
            pending_requests = await db.get_pending_scrim_requests(
                exclude_captain_id=new_request['captain_discord_id']
            )
            
            if not pending_requests:
                # No other requests yet
                try:
                    await captain.send(
                        "📋 **No other scrim requests available yet.**\n\n"
                        "You'll be notified when someone else posts a scrim request!"
                    )
                except:
                    pass
                return
            
            # Send header message
            try:
                await captain.send(
                    f"📋 **Available Scrim Requests:**\n"
                    f"Found {len(pending_requests)} team(s) looking for scrims!\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━"
                )
            except:
                return
            
            # Get requester's timezone for conversion
            requester_tz = new_request.get('timezone', 'IST')
            
            for req in pending_requests:
                # Check if in avoid list
                in_avoid_list = await db.check_avoid_list(
                    new_request['captain_discord_id'],
                    req['captain_discord_id']
                )
                
                # Check if this request is already in a match that's being scheduled
                req_status = await db.get_scrim_request_status(req['id'])
                
                # Get team info
                team = await db.get_team_by_captain(req['captain_discord_id'])
                if not team:
                    team = await db.get_player_team(req['captain_discord_id'])
                team_name = f"{team['name']} [{team['tag']}]" if team else "Unknown Team"
                
                # Handle time_slot (now a datetime object)
                req_time = req['time_slot']
                req_tz = req.get('timezone', 'IST')
                
                # Format the time for display
                if isinstance(req_time, datetime):
                    their_time_display = req_time.strftime("%I:%M %p %Z")
                    
                    # Convert to requester's timezone if different
                    if requester_tz and req_tz != requester_tz:
                        requester_tz_obj = ZoneInfo(TIMEZONE_MAP.get(requester_tz, 'UTC'))
                        converted_time = req_time.astimezone(requester_tz_obj)
                        your_time_display = converted_time.strftime("%I:%M %p %Z")
                        time_display = f"**Your Time:** {your_time_display}\n**Their Time:** {their_time_display}"
                        scrim_time = converted_time
                    else:
                        time_display = f"**Time:** {their_time_display}"
                        scrim_time = req_time
                    
                    # Calculate time until scrim
                    now = datetime.now(scrim_time.tzinfo)
                    time_until = scrim_time - now
                    
                    # If negative, it's tomorrow
                    if time_until.total_seconds() < 0:
                        time_until = time_until + timedelta(days=1)
                    
                    hours_until = int(time_until.total_seconds() // 3600)
                    minutes_until = int((time_until.total_seconds() % 3600) // 60)
                    
                    # Add countdown
                    if hours_until > 0:
                        time_display += f"\n⏰ In {hours_until}h {minutes_until}m"
                    else:
                        time_display += f"\n⏰ In {minutes_until} minutes"
                else:
                    # Fallback for string time_slot (backward compatibility)
                    time_display = f"**Time:** {req_time}"
                
                # Build status text
                status_text = ""
                if req_status == 'in_progress':
                    status_text = "\n⚠️ **This team is currently scheduling with another team.**"
                elif in_avoid_list:
                    status_text = "\n🚫 **This team is in your avoid list.**"
                
                # Create embed for this request
                embed = discord.Embed(
                    title=f"🎮 Scrim Request",
                    color=discord.Color.blue() if req_status == 'pending' else discord.Color.orange(),
                    timestamp=scrim_time  # Set timestamp to the scrim time for Discord's relative display
                )
                embed.add_field(name="Team", value=team_name, inline=False)
                embed.add_field(name="Match Type", value=req['match_type'].upper(), inline=True)
                embed.add_field(name="Region", value=req.get('region', 'N/A').upper(), inline=True)
                embed.add_field(name="🕐 Schedule", value=time_display, inline=False)
                
                if status_text:
                    embed.description = status_text
                
                # Add view with buttons (disabled if in avoid list or in progress)
                view = ScrimRequestView(
                    req['id'],
                    req['captain_discord_id'],
                    new_request['captain_discord_id'],
                    self
                )
                
                if in_avoid_list or req_status == 'in_progress':
                    for item in view.children:
                        if isinstance(item, Button) and item.label == "✅ Accept Scrim":
                            item.disabled = True
                
                try:
                    await captain.send(embed=embed, view=view)
                except:
                    pass
            
        except Exception as e:
            print(f"Error in send_all_scrim_requests: {e}")
            import traceback
            traceback.print_exc()
    
    async def notify_other_captains(self, new_request: dict, new_captain: discord.Member):
        """Notify all OTHER pending captains about this NEW scrim request"""
        try:
            # Get all pending requests (excluding this captain)
            pending_requests = await db.get_pending_scrim_requests(
                exclude_captain_id=new_request['captain_discord_id']
            )
            
            if not pending_requests:
                return
            
            # Get team info for new request
            team = await db.get_team_by_captain(new_request['captain_discord_id'])
            if not team:
                team = await db.get_player_team(new_request['captain_discord_id'])
            team_name = f"{team['name']} [{team['tag']}]" if team else "Unknown Team"
            
            new_req_tz = new_request.get('timezone', 'IST')
            
            # Notify each other captain
            for req in pending_requests:
                try:
                    other_captain = await self.bot.fetch_user(req['captain_discord_id'])
                    
                    # Check if in avoid list
                    in_avoid_list = await db.check_avoid_list(
                        req['captain_discord_id'],
                        new_request['captain_discord_id']
                    )
                    
                    if in_avoid_list:
                        continue  # Don't notify if in avoid list
                    
                    # Convert new request's time to this captain's timezone
                    other_tz = req.get('timezone', 'IST')
                    new_time = new_request['time_slot']
                    new_req_tz = new_request.get('timezone', 'IST')
                    
                    if isinstance(new_time, datetime):
                        their_time_display = new_time.strftime("%I:%M %p %Z")
                        
                        # Convert to other captain's timezone if different
                        if new_req_tz != other_tz:
                            other_tz_obj = ZoneInfo(TIMEZONE_MAP.get(other_tz, 'UTC'))
                            converted_time = new_time.astimezone(other_tz_obj)
                            your_time_display = converted_time.strftime("%I:%M %p %Z")
                            time_display = f"**Your Time:** {your_time_display}\n**Their Time:** {their_time_display}"
                            scrim_time = converted_time
                        else:
                            time_display = f"**Time:** {their_time_display}"
                            scrim_time = new_time
                        
                        # Calculate time until scrim
                        now = datetime.now(scrim_time.tzinfo)
                        time_until = scrim_time - now
                        
                        if time_until.total_seconds() < 0:
                            time_until = time_until + timedelta(days=1)
                        
                        hours_until = int(time_until.total_seconds() // 3600)
                        minutes_until = int((time_until.total_seconds() % 3600) // 60)
                        
                        # Add countdown
                        if hours_until > 0:
                            time_display += f"\n⏰ In {hours_until}h {minutes_until}m"
                        else:
                            time_display += f"\n⏰ In {minutes_until} minutes"
                    else:
                        # Fallback for string
                        time_display = f"**Time:** {new_time}"
                        scrim_time = datetime.now()  # Default for timestamp
                    
                    # Create embed for the new request
                    embed = discord.Embed(
                        title=f"🆕 New Scrim Request Available!",
                        color=discord.Color.green(),
                        timestamp=scrim_time  # Set to scrim time for Discord's relative display
                    )
                    embed.add_field(name="Team", value=team_name, inline=False)
                    embed.add_field(name="Match Type", value=new_request['match_type'].upper(), inline=True)
                    embed.add_field(name="Region", value=new_request.get('region', 'N/A').upper(), inline=True)
                    embed.add_field(name="🕐 Schedule", value=time_display, inline=False)
                    
                    # Create view with buttons
                    view = ScrimRequestView(
                        new_request['id'],
                        new_request['captain_discord_id'],
                        req['captain_discord_id'],
                        self
                    )
                    
                    await other_captain.send(embed=embed, view=view)
                    
                except:
                    pass
        
        except Exception as e:
            print(f"Error in notify_other_captains: {e}")
            import traceback
            traceback.print_exc()
    
    async def create_scrim_match_from_requests(self, request_1: dict, request_2: dict, acceptor: discord.User):
        """Create a scrim match from two requests when one captain accepts another's request"""
        try:
            # Update both requests to 'in_progress' status
            await db.update_scrim_request_status(request_1['id'], 'in_progress')
            await db.update_scrim_request_status(request_2['id'], 'in_progress')
            
            # Create the match
            match = await db.create_scrim_match(
                request_id_1=request_1['id'],
                request_id_2=request_2['id'],
                captain_1_id=request_1['captain_discord_id'],
                captain_2_id=request_2['captain_discord_id'],
                team_1_id=request_1['team_id'],
                team_2_id=request_2['team_id'],
                region=request_1['region'],
                match_type=request_1['match_type'],
                time_slot=request_1['time_slot']
            )
            
            # Get team info
            team_1 = await db.get_team_by_id(request_1['team_id'])
            team_2 = await db.get_team_by_id(request_2['team_id'])
            team_1_name = f"{team_1['name']} [{team_1['tag']}]" if team_1 else "Unknown"
            team_2_name = f"{team_2['name']} [{team_2['tag']}]" if team_2 else "Unknown"
            
            # Get captains
            captain_1 = await self.bot.fetch_user(request_1['captain_discord_id'])
            captain_2 = await self.bot.fetch_user(request_2['captain_discord_id'])
            
            # Create approval views
            view_1 = ScrimApprovalView(match['id'], 1, team_2_name)
            view_2 = ScrimApprovalView(match['id'], 2, team_1_name)
            
            # Build match info messages
            # Captain 1 gets notified that the acceptor (captain 2) accepted their request
            msg_1 = (
                f"🤝 **SCRIM MATCH FOUND!**\n\n"
                f"**Opponent Team:** {team_2_name}\n"
                f"**Opponent Captain:** {captain_2.display_name}\n\n"
                f"**Their Request:** {request_2['match_type'].upper()}, {request_2['time_slot']}\n"
                f"**Your Request:** {request_1['match_type'].upper()}, {request_1['time_slot']}\n\n"
                f"**{acceptor.display_name}** accepted your scrim request!\n"
                f"Please approve or decline this scrim match."
            )
            
            # Captain 2 (the acceptor) sees their own acceptance
            msg_2 = (
                f"🤝 **SCRIM MATCH FOUND!**\n\n"
                f"**Opponent Team:** {team_1_name}\n"
                f"**Opponent Captain:** {captain_1.display_name}\n\n"
                f"**Their Request:** {request_1['match_type'].upper()}, {request_1['time_slot']}\n"
                f"**Your Request:** {request_2['match_type'].upper()}, {request_2['time_slot']}\n\n"
                f"You accepted their scrim request!\n"
                f"Please approve or decline this scrim match."
            )
            
            # Send DMs
            try:
                await captain_1.send(msg_1, view=view_1)
            except:
                pass
            
            try:
                await captain_2.send(msg_2, view=view_2)
            except:
                pass
            
            # Notify waitlisted captains
            await self.notify_waitlist(request_1['id'], team_1_name, team_2_name)
            await self.notify_waitlist(request_2['id'], team_2_name, team_1_name)
            
        except Exception as e:
            print(f"Error in create_scrim_match_from_requests: {e}")
            import traceback
            traceback.print_exc()
    
    async def send_format_selection(self, match: dict, captain_1: discord.User, captain_2: discord.User, format_1: str, format_2: str):
        """Send format selection buttons to both captains"""
        try:
            # Store captain IDs for cancel button access
            if not hasattr(self, 'match_data'):
                self.match_data = {}
            if match['id'] not in self.match_data:
                self.match_data[match['id']] = {}
            self.match_data[match['id']]['captain_1_id'] = captain_1.id
            self.match_data[match['id']]['captain_2_id'] = captain_2.id
            
            # Create embed explaining the format selection
            embed = discord.Embed(
                title="🎮 Choose Scrim Format",
                description=(
                    "Please select which format you want to play.\n"
                    "You can discuss with the other captain via DM (chat relay is active).\n\n"
                    "**Both captains must select the same format to proceed.**"
                ),
                color=0x3498DB
            )
            
            embed.add_field(
                name=f"Captain 1's Format ({captain_1.display_name})",
                value=f"**{format_1}**",
                inline=True
            )
            
            embed.add_field(
                name=f"Captain 2's Format ({captain_2.display_name})",
                value=f"**{format_2}**",
                inline=True
            )
            
            embed.add_field(
                name="Other Format",
                value="Choose a different format (BO1/BO3/BO5)",
                inline=True
            )
            
            # Update button labels with the actual formats and pass other captain ID
            view_1 = FormatSelectionView(match['id'], captain_1.id, 1, format_1, format_2, self, captain_2.id)
            view_1.children[0].label = f"{format_1} (Captain 1)"
            view_1.children[1].label = f"{format_2} (Captain 2)"
            
            view_2 = FormatSelectionView(match['id'], captain_2.id, 2, format_1, format_2, self, captain_1.id)
            view_2.children[0].label = f"{format_1} (Captain 1)"
            view_2.children[1].label = f"{format_2} (Captain 2)"
            
            # Send to both captains
            try:
                await captain_1.send(embed=embed, view=view_1)
            except Exception as e:
                print(f"Error sending format selection to captain 1: {e}")
            
            try:
                await captain_2.send(embed=embed, view=view_2)
            except Exception as e:
                print(f"Error sending format selection to captain 2: {e}")
            
        except Exception as e:
            print(f"Error in send_format_selection: {e}")
            import traceback
            traceback.print_exc()
    
    async def handle_format_selection(self, match_id: int, captain_num: int, selected_format: str, user: discord.User):
        """Handle format selection from a captain"""
        try:
            # Store format selection
            if not hasattr(self, 'format_selections'):
                self.format_selections = {}
            
            match_key = f"match_{match_id}"
            if match_key not in self.format_selections:
                self.format_selections[match_key] = {}
            
            self.format_selections[match_key][captain_num] = selected_format
            
            # Check if both captains have selected
            if len(self.format_selections[match_key]) >= 2:
                format_cap1 = self.format_selections[match_key].get(1)
                format_cap2 = self.format_selections[match_key].get(2)
                
                # Get match and captains
                match = await db.get_scrim_match_by_id(match_id)
                if not match:
                    return
                
                captain_1 = await self.bot.fetch_user(match['captain_1_discord_id'])
                captain_2 = await self.bot.fetch_user(match['captain_2_discord_id'])
                
                # Check if both selected the same format
                if format_cap1 == format_cap2:
                    # Both agreed on format, update match and proceed
                    await db.update_scrim_match_format(match_id, format_cap1.lower())
                    
                    # Store the agreed format in match_data for map banning
                    if match_id not in self.match_data:
                        self.match_data[match_id] = {}
                    self.match_data[match_id]['agreed_format'] = format_cap1.lower()
                    
                    # Notify both captains
                    success_msg = (
                        f"✅ **Format Agreed!**\n\n"
                        f"Both captains selected **{format_cap1}**.\n\n"
                        f"**Commands:**\n"
                        f"• `!ban-map` - Request to start map banning\n"
                        f"• `!cancel-scrim` - Request to cancel scrim\n\n"
                        f"Chat relay is still active. Use `!ban-map` when ready!"
                    )
                    
                    try:
                        await captain_1.send(success_msg)
                    except:
                        pass
                    
                    try:
                        await captain_2.send(success_msg)
                    except:
                        pass
                    
                    # Clean up format selection tracking
                    del self.format_selections[match_key]
                else:
                    # Different formats selected, ask to discuss
                    conflict_msg = (
                        f"⚠️ **Format Mismatch**\n\n"
                        f"Captain 1 selected: **{format_cap1}**\n"
                        f"Captain 2 selected: **{format_cap2}**\n\n"
                        f"Please discuss and select again. The selection buttons are still available above."
                    )
                    
                    try:
                        await captain_1.send(conflict_msg)
                    except:
                        pass
                    
                    try:
                        await captain_2.send(conflict_msg)
                    except:
                        pass
                    
                    # Reset selections so they can choose again
                    self.format_selections[match_key] = {}
            else:
                # Only one captain selected, notify and wait
                match = await db.get_scrim_match_by_id(match_id)
                if not match:
                    return
                
                other_captain_id = match['captain_2_discord_id'] if captain_num == 1 else match['captain_1_discord_id']
                other_captain = await self.bot.fetch_user(other_captain_id)
                
                try:
                    await other_captain.send(
                        f"⏳ **{user.display_name}** has selected **{selected_format}** format.\n"
                        f"Please select your format preference."
                    )
                except:
                    pass
        
        except Exception as e:
            print(f"Error in handle_format_selection: {e}")
            import traceback
            traceback.print_exc()
    
    async def notify_waitlist(self, request_id: int, team_1_name: str, team_2_name: str):
        """Notify captains on waitlist that a scrim is in progress"""
        try:
            waitlist = await db.get_scrim_waitlist(request_id)
            
            for captain_id in waitlist:
                try:
                    captain = await self.bot.fetch_user(captain_id)
                    await captain.send(
                        f"📊 **Scrim Status Update**\n\n"
                        f"**{team_1_name}** vs **{team_2_name}** is now in scheduling progress.\n"
                        f"You'll be notified if this scrim doesn't get scheduled!"
                    )
                except:
                    pass
        except Exception as e:
            print(f"Error in notify_waitlist: {e}")
    
    async def notify_waitlist_available(self, request_1: dict, request_2: dict):
        """Notify waitlisted captains that scrims are available again (match was declined)"""
        try:
            # Get team info for both requests
            team_1 = await db.get_team_by_id(request_1['team_id'])
            team_2 = await db.get_team_by_id(request_2['team_id'])
            team_1_name = f"{team_1['name']} [{team_1['tag']}]" if team_1 else "Unknown"
            team_2_name = f"{team_2['name']} [{team_2['tag']}]" if team_2 else "Unknown"
            
            # Notify waitlist for request 1
            waitlist_1 = await db.get_scrim_waitlist(request_1['id'])
            for captain_id in waitlist_1:
                try:
                    captain = await self.bot.fetch_user(captain_id)
                    
                    # Check if captain still has a pending request
                    captain_request = await db.get_captain_pending_request(captain_id)
                    if not captain_request:
                        continue  # Skip if they don't have an active request
                    
                    # Create embed for the now-available request
                    embed = discord.Embed(
                        title=f"✅ Scrim Available Again!",
                        description=f"**{team_1_name}** vs **{team_2_name}** match was not scheduled.\n**{team_1_name}** is looking for scrims again!",
                        color=discord.Color.green(),
                        timestamp=request_1['created_at']
                    )
                    embed.add_field(name="Team", value=team_1_name, inline=False)
                    embed.add_field(name="Match Type", value=request_1['match_type'].upper(), inline=True)
                    embed.add_field(name="Time Slot", value=request_1['time_slot'], inline=True)
                    embed.add_field(name="Region", value=request_1['region'].upper(), inline=True)
                    
                    # Create view with buttons
                    view = ScrimRequestView(
                        request_1['id'],
                        request_1['captain_discord_id'],
                        captain_id,
                        self
                    )
                    
                    await captain.send(embed=embed, view=view)
                    
                except Exception as e:
                    print(f"Error notifying captain {captain_id}: {e}")
            
            # Notify waitlist for request 2
            waitlist_2 = await db.get_scrim_waitlist(request_2['id'])
            for captain_id in waitlist_2:
                try:
                    captain = await self.bot.fetch_user(captain_id)
                    
                    # Check if captain still has a pending request
                    captain_request = await db.get_captain_pending_request(captain_id)
                    if not captain_request:
                        continue  # Skip if they don't have an active request
                    
                    # Create embed for the now-available request
                    embed = discord.Embed(
                        title=f"✅ Scrim Available Again!",
                        description=f"**{team_1_name}** vs **{team_2_name}** match was not scheduled.\n**{team_2_name}** is looking for scrims again!",
                        color=discord.Color.green(),
                        timestamp=request_2['created_at']
                    )
                    embed.add_field(name="Team", value=team_2_name, inline=False)
                    embed.add_field(name="Match Type", value=request_2['match_type'].upper(), inline=True)
                    embed.add_field(name="Time Slot", value=request_2['time_slot'], inline=True)
                    embed.add_field(name="Region", value=request_2['region'].upper(), inline=True)
                    
                    # Create view with buttons
                    view = ScrimRequestView(
                        request_2['id'],
                        request_2['captain_discord_id'],
                        captain_id,
                        self
                    )
                    
                    await captain.send(embed=embed, view=view)
                    
                except Exception as e:
                    print(f"Error notifying captain {captain_id}: {e}")
                    
        except Exception as e:
            print(f"Error in notify_waitlist_available: {e}")
            import traceback
            traceback.print_exc()
    
    async def find_and_match_scrim(self, new_request: dict, captain: discord.Member):
        """DEPRECATED: Kept for compatibility. New flow uses send_all_scrim_requests"""
        # This method is no longer used but kept to prevent errors
        pass
    
    async def handle_captain_dm(self, message: discord.Message):
        """Handle DM messages from captains for chat relay"""
        try:
            captain_id = message.author.id
            
            # Check if we're waiting for a screenshot from this captain
            if hasattr(self, 'awaiting_screenshots'):
                for match_id, data in self.awaiting_screenshots.items():
                    if captain_id in [data['captain_1'], data['captain_2']] and captain_id not in data['received']:
                        # Check if message has attachments
                        if message.attachments:
                            screenshot = message.attachments[0]
                            if screenshot.content_type and screenshot.content_type.startswith('image/'):
                                # Store screenshot
                                match_key = f"match_{match_id}"
                                if not hasattr(self, 'scrim_screenshots'):
                                    self.scrim_screenshots = {}
                                if match_key not in self.scrim_screenshots:
                                    self.scrim_screenshots[match_key] = {}
                                
                                self.scrim_screenshots[match_key][captain_id] = screenshot
                                data['received'].add(captain_id)
                                
                                await message.add_reaction("✅")
                                await message.channel.send("✅ Screenshot received! Waiting for the other captain...")
                                
                                # Check if both screenshots received
                                if len(data['received']) == 2:
                                    # Both received, validate and extract scores
                                    await self.process_screenshots(match_id)
                                
                                return
            
            # Check if captain has an active chat match
            pending_matches = await db.get_captain_pending_matches(captain_id)
            print(f"📨 DM from {message.author.display_name} (ID: {captain_id})")
            print(f"Found {len(pending_matches)} matches for this captain")
            
            # Find a match with chat_active status
            active_match = None
            for match in pending_matches:
                print(f"  Match ID {match['id']}: status = {match.get('status')}")
                if match.get('status') == 'chat_active':
                    active_match = match
                    break
            
            if not active_match:
                # No active chat, ignore the DM
                print(f"⚠️ No active chat found for captain {captain_id}")
                return
            
            print(f"✅ Active match found: ID {active_match['id']}")
            
            # Check for commands
            content_lower = message.content.strip().lower()
            
            # !ban-map command - Request to start map banning
            if content_lower == '!ban-map':
                print(f"🗺️ Map banning requested by captain {captain_id}")
                await self.request_map_banning(active_match, message.author)
                return
            
            # !cancel-scrim command - Request to cancel scrim
            if content_lower == '!cancel-scrim':
                print(f"❌ Scrim cancellation requested by captain {captain_id}")
                await self.request_scrim_cancellation(active_match, message.author)
                return
            
            # Relay the message to the other captain
            other_captain_id = (active_match['captain_2_discord_id'] 
                               if captain_id == active_match['captain_1_discord_id'] 
                               else active_match['captain_1_discord_id'])
            
            print(f"📤 Relaying message to captain {other_captain_id}")
            
            try:
                other_captain = await self.bot.fetch_user(other_captain_id)
                await other_captain.send(f"**{message.author.display_name}:** {message.content}")
                
                # Confirm to sender
                await message.add_reaction("✅")
                print(f"✅ Message relayed successfully")
            except discord.Forbidden:
                await message.channel.send("❌ Couldn't send message to the other captain. They may have DMs disabled.")
                print(f"❌ Forbidden: Can't DM captain {other_captain_id}")
            except Exception as e:
                await message.channel.send(f"❌ Error relaying message: {str(e)}")
                print(f"❌ Error relaying: {e}")
                
        except Exception as e:
            print(f"Error in handle_captain_dm: {e}")
            import traceback
            traceback.print_exc()
    
    async def request_map_banning(self, match: dict, requester: discord.User):
        """Request to start map banning (requires confirmation from other captain)"""
        try:
            # Get the other captain
            other_captain_id = (match['captain_2_discord_id'] 
                               if requester.id == match['captain_1_discord_id'] 
                               else match['captain_1_discord_id'])
            
            other_captain = await self.bot.fetch_user(other_captain_id)
            
            # Send confirmation request
            view = MapBanConfirmView(match['id'], requester.display_name, self)
            await other_captain.send(
                f"🗺️ **Map Banning Request**\n\n"
                f"**{requester.display_name}** wants to start map banning.\n"
                f"Do you want to proceed?",
                view=view
            )
            
            # Notify requester
            await requester.send(
                f"✅ Map banning request sent to **{other_captain.display_name}**.\n"
                f"Waiting for their response..."
            )
            
        except Exception as e:
            print(f"Error in request_map_banning: {e}")
            await requester.send(f"❌ Error requesting map banning: {str(e)}")
    
    async def request_scrim_cancellation(self, match: dict, requester: discord.User):
        """Request to cancel scrim (requires confirmation from other captain)"""
        try:
            # Get the other captain
            other_captain_id = (match['captain_2_discord_id'] 
                               if requester.id == match['captain_1_discord_id'] 
                               else match['captain_1_discord_id'])
            
            other_captain = await self.bot.fetch_user(other_captain_id)
            
            # Send confirmation request
            view = CancelScrimConfirmView(match['id'], requester.display_name, self)
            await other_captain.send(
                f"❌ **Scrim Cancellation Request**\n\n"
                f"**{requester.display_name}** wants to cancel this scrim.\n"
                f"Do you agree?",
                view=view
            )
            
            # Notify requester
            await requester.send(
                f"✅ Cancellation request sent to **{other_captain.display_name}**.\n"
                f"Waiting for their response..."
            )
            
        except Exception as e:
            print(f"Error in request_scrim_cancellation: {e}")
            await requester.send(f"❌ Error requesting cancellation: {str(e)}")
    
    async def cancel_scrim_match(self, match: dict, confirmer: discord.User):
        """Cancel the scrim match and add both captains to avoid list"""
        try:
            captain_1_id = match['captain_1_discord_id']
            captain_2_id = match['captain_2_discord_id']
            
            # Update match status to declined
            await db.update_scrim_match_status(match['id'], 'declined')
            
            # Put both requests back to pending status
            await db.update_scrim_request_status(match['request_id_1'], 'pending')
            await db.update_scrim_request_status(match['request_id_2'], 'pending')
            
            # Add to avoid list for 6 hours
            await db.add_to_avoid_list(captain_1_id, captain_2_id, hours=6)
            
            # Notify both captains
            captain_1 = await self.bot.fetch_user(captain_1_id)
            captain_2 = await self.bot.fetch_user(captain_2_id)
            
            cancel_msg = (
                f"❌ **SCRIM CANCELLED**\n\n"
                f"Both captains agreed to cancel the scrim.\n\n"
                f"✅ **Your request is back in the queue!**\n"
                f"You'll automatically be matched with other teams when they post LFS requests.\n\n"
                f"⏰ You won't be matched with **each other** for the next 6 hours.\n\n"
                f"Waiting for new opponents..."
            )
            
            try:
                await captain_1.send(cancel_msg)
            except:
                pass
            
            try:
                await captain_2.send(cancel_msg)
            except:
                pass
                
        except Exception as e:
            print(f"Error in cancel_scrim_match: {e}")
    
    async def start_map_banning(self, match: dict, initiator: discord.User):
        """Start the map banning phase with coin toss"""
        try:
            import random
            
            # Update match status to map_banning
            await db.update_scrim_match_status(match['id'], 'map_banning')
            
            # Get captains
            captain_1_id = match['captain_1_discord_id']
            captain_2_id = match['captain_2_discord_id']
            
            captain_1 = await self.bot.fetch_user(captain_1_id)
            captain_2 = await self.bot.fetch_user(captain_2_id)
            
            # Coin toss - randomly select who calls
            coin_caller = random.choice([captain_1, captain_2])
            other_captain = captain_2 if coin_caller == captain_1 else captain_1
            
            # Send coin toss request
            toss_view = CoinTossView(match, coin_caller, other_captain, self)
            await coin_caller.send(
                f"🪙 **COIN TOSS**\n\n"
                f"You've been selected to call the toss!\n"
                f"Choose Heads or Tails:",
                view=toss_view
            )
            
            await other_captain.send(
                f"🪙 **COIN TOSS**\n\n"
                f"**{coin_caller.display_name}** is calling the toss...\n"
                f"Waiting for result..."
            )
                
        except Exception as e:
            print(f"Error in start_map_banning: {e}")
            import traceback
            traceback.print_exc()
    
    async def start_banning_maps(self, match: dict, winner: discord.User, loser: discord.User):
        """Start the VCT-style map veto process"""
        # Store veto state in match_data
        if not hasattr(self, 'match_data'):
            self.match_data = {}
        
        # Determine format
        match_type = match['match_type']
        if match['id'] in self.match_data and 'agreed_format' in self.match_data[match['id']]:
            match_type = self.match_data[match['id']]['agreed_format']
        
        self.match_data[match['id']] = {
            'toss_winner': winner.id,
            'toss_loser': loser.id,
            'format': match_type,
            'banned_maps': [],
            'picked_maps': [],  # [(map_name, picker_team, side_chosen)]
            'decider_map': None,
            'veto_step': 0,
            'sides': {}
        }
        
        # All available maps (7 maps)
        all_maps = ["Ascent", "Bind", "Breeze", "Fracture", "Haven", "Icebox", "Split"]
        self.match_data[match['id']]['available_maps'] = all_maps.copy()
        
        # Get team names for display
        team_1 = await db.get_team_by_captain(match['captain_1_discord_id'])
        team_2 = await db.get_team_by_captain(match['captain_2_discord_id'])
        team_a_name = f"{team_1['name']}" if team_1 else f"Team {winner.display_name}"
        team_b_name = f"{team_2['name']}" if team_2 else f"Team {loser.display_name}"
        
        self.match_data[match['id']]['team_a_id'] = winner.id
        self.match_data[match['id']]['team_b_id'] = loser.id
        self.match_data[match['id']]['team_a_name'] = team_a_name
        self.match_data[match['id']]['team_b_name'] = team_b_name
        
        # Get captains
        captain_1 = await self.bot.fetch_user(match['captain_1_discord_id'])
        captain_2 = await self.bot.fetch_user(match['captain_2_discord_id'])
        
        # Define veto sequence based on format
        if match_type == 'bo1':
            # BO1: A ban, B ban, A ban, B ban, A ban, B ban, remaining = decider, coin toss for side
            veto_sequence = [
                ('ban', 'A'), ('ban', 'B'), ('ban', 'A'), ('ban', 'B'),
                ('ban', 'A'), ('ban', 'B'), ('decider', None)
            ]
        elif match_type == 'bo3':
            # BO3: A ban, B ban, A pick (+ side), B pick (+ side), B ban, A ban, remaining = decider, coin toss
            veto_sequence = [
                ('ban', 'A'), ('ban', 'B'),
                ('pick', 'A'), ('pick', 'B'),
                ('ban', 'B'), ('ban', 'A'),
                ('decider', None)
            ]
        else:  # bo5
            # BO5: A ban, B ban, A pick (+ side), B pick (+ side), A pick (+ side), B pick (+ side), remaining = decider, coin toss
            veto_sequence = [
                ('ban', 'A'), ('ban', 'B'),
                ('pick', 'A'), ('pick', 'B'),
                ('pick', 'A'), ('pick', 'B'),
                ('decider', None)
            ]
        
        self.match_data[match['id']]['veto_sequence'] = veto_sequence
        
        # Start veto process
        await self.process_next_veto_step(match, captain_1, captain_2)
    
    async def process_next_veto_step(self, match: dict, captain_1: discord.User, captain_2: discord.User):
        """Process the next step in the veto sequence"""
        match_data = self.match_data[match['id']]
        veto_sequence = match_data['veto_sequence']
        step_index = match_data['veto_step']
        
        if step_index >= len(veto_sequence):
            # Veto complete
            await self.finalize_veto(match, captain_1, captain_2)
            return
        
        action, team = veto_sequence[step_index]
        
        if action == 'decider':
            # Remaining map is the decider
            remaining = match_data['available_maps'][0]
            match_data['decider_map'] = remaining
            match_data['picked_maps'].append((remaining, 'Decider', 'Coin Toss'))
            match_data['veto_step'] += 1
            
            # Do coin toss for decider map
            await self.do_coin_toss_for_decider(match, captain_1, captain_2, remaining)
        else:
            # Determine which captain acts
            team_a_id = match_data['team_a_id']
            acting_captain = captain_1 if (team == 'A' and captain_1.id == team_a_id) or (team == 'B' and captain_1.id != team_a_id) else captain_2
            other_captain = captain_2 if acting_captain == captain_1 else captain_1
            
            if action == 'ban':
                await self.send_veto_ui(match, acting_captain, other_captain, action, team)
            elif action == 'pick':
                await self.send_veto_ui(match, acting_captain, other_captain, action, team)
    
    async def send_veto_ui(self, match: dict, acting_captain: discord.User, other_captain: discord.User, action: str, team: str):
        """Send veto UI (ban or pick)"""
        match_data = self.match_data[match['id']]
        available_maps = match_data['available_maps']
        step_index = match_data['veto_step']
        
        team_name = match_data['team_a_name'] if team == 'A' else match_data['team_b_name']
        
        if action == 'ban':
            view = MapVetoView(match, acting_captain, available_maps, action, self)
            await acting_captain.send(
                f"🚫 **MAP BAN** - Step {step_index + 1}\n\n"
                f"**Your Team ({team_name})** must ban a map.\n"
                f"Available maps: {', '.join(available_maps)}\n\n"
                f"Select a map to ban:",
                view=view
            )
            await other_captain.send(
                f"⏳ **{team_name}** ({acting_captain.display_name}) is banning a map..."
            )
        else:  # pick
            view = MapVetoView(match, acting_captain, available_maps, action, self)
            await acting_captain.send(
                f"✅ **MAP PICK** - Step {step_index + 1}\n\n"
                f"**Your Team ({team_name})** must pick a map.\n"
                f"Available maps: {', '.join(available_maps)}\n\n"
                f"Select a map to pick:",
                view=view
            )
            await other_captain.send(
                f"⏳ **{team_name}** ({acting_captain.display_name}) is picking a map..."
            )
    
    async def handle_veto_action(self, match: dict, captain: discord.User, map_name: str, action: str):
        """Handle a ban or pick action"""
        match_data = self.match_data[match['id']]
        available_maps = match_data['available_maps']
        
        # Remove map from available
        available_maps.remove(map_name)
        
        # Get captains
        captain_1 = await self.bot.fetch_user(match['captain_1_discord_id'])
        captain_2 = await self.bot.fetch_user(match['captain_2_discord_id'])
        
        if action == 'ban':
            match_data['banned_maps'].append(map_name)
            
            # Notify both
            await captain_1.send(f"🚫 **{captain.display_name}** banned **{map_name}**")
            await captain_2.send(f"🚫 **{captain.display_name}** banned **{map_name}**")
            
            # Move to next step
            match_data['veto_step'] += 1
            await self.process_next_veto_step(match, captain_1, captain_2)
        
        elif action == 'pick':
            # Need side selection for picked maps
            team_name = match_data['team_a_name'] if captain.id == match_data['team_a_id'] else match_data['team_b_name']
            
            # Send side selection UI
            view = SideSelectionView(match, captain, map_name, self)
            await captain.send(
                f"✅ You picked **{map_name}**!\n\n"
                f"🛡️⚔️ **Choose your starting side:**",
                view=view
            )
            
            other = captain_2 if captain == captain_1 else captain_1
            await other.send(f"✅ **{captain.display_name}** picked **{map_name}** (choosing side...)")
    
    async def handle_side_selection(self, match: dict, captain: discord.User, map_name: str, side: str):
        """Handle side selection for a picked map"""
        match_data = self.match_data[match['id']]
        team_name = match_data['team_a_name'] if captain.id == match_data['team_a_id'] else match_data['team_b_name']
        
        # Store pick with side
        match_data['picked_maps'].append((map_name, team_name, side))
        match_data['sides'][map_name] = {'picker': captain.id, 'side': side}
        
        # Get captains
        captain_1 = await self.bot.fetch_user(match['captain_1_discord_id'])
        captain_2 = await self.bot.fetch_user(match['captain_2_discord_id'])
        
        # Notify both
        await captain_1.send(f"✅ **{map_name}**: {team_name} starts on **{side}**")
        await captain_2.send(f"✅ **{map_name}**: {team_name} starts on **{side}**")
        
        # Move to next step
        match_data['veto_step'] += 1
        await self.process_next_veto_step(match, captain_1, captain_2)
    
    async def do_coin_toss_for_decider(self, match: dict, captain_1: discord.User, captain_2: discord.User, map_name: str):
        """Perform coin toss for decider map side selection"""
        import random
        
        match_data = self.match_data[match['id']]
        
        # Random coin toss
        toss_winner = random.choice([captain_1, captain_2])
        toss_loser = captain_2 if toss_winner == captain_1 else captain_1
        
        # Send side selection to toss winner
        view = SideSelectionView(match, toss_winner, map_name, self, is_decider=True)
        await toss_winner.send(
            f"🪙 **COIN TOSS for {map_name}** 🪙\n\n"
            f"✅ You **WON** the toss!\n\n"
            f"🛡️⚔️ **Choose your starting side:**",
            view=view
        )
        await toss_loser.send(
            f"🪙 **COIN TOSS for {map_name}** 🪙\n\n"
            f"❌ You **LOST** the toss.\n\n"
            f"⏳ **{toss_winner.display_name}** is choosing the starting side..."
        )
    
    async def handle_decider_side_selection(self, match: dict, captain: discord.User, map_name: str, side: str):
        """Handle side selection for decider map after coin toss"""
        match_data = self.match_data[match['id']]
        team_name = match_data['team_a_name'] if captain.id == match_data['team_a_id'] else match_data['team_b_name']
        
        # Update decider map side
        for i, (m, t, s) in enumerate(match_data['picked_maps']):
            if m == map_name and t == 'Decider':
                match_data['picked_maps'][i] = (m, team_name, side)
                break
        
        match_data['sides'][map_name] = {'picker': captain.id, 'side': side}
        
        # Get captains
        captain_1 = await self.bot.fetch_user(match['captain_1_discord_id'])
        captain_2 = await self.bot.fetch_user(match['captain_2_discord_id'])
        
        # Notify both
        await captain_1.send(f"✅ **{map_name}** (Decider): {team_name} starts on **{side}**")
        await captain_2.send(f"✅ **{map_name}** (Decider): {team_name} starts on **{side}**")
        
        # Veto complete
        await self.finalize_veto(match, captain_1, captain_2)
    
    async def finalize_veto(self, match: dict, captain_1: discord.User, captain_2: discord.User):
        """Show final veto summary"""
        match_data = self.match_data[match['id']]
        
        # Create beautiful summary embed
        embed = discord.Embed(
            title="🎮 MAP VETO COMPLETE",
            description=f"**{match_data['format'].upper()}** • **{match['region'].upper()}**",
            color=0x00FF00
        )
        
        # Teams
        embed.add_field(
            name="👥 Teams",
            value=f"**Team A:** {match_data['team_a_name']}\n**Team B:** {match_data['team_b_name']}",
            inline=False
        )
        
        # Banned Maps
        if match_data['banned_maps']:
            embed.add_field(
                name="🚫 Banned Maps",
                value=", ".join(match_data['banned_maps']),
                inline=False
            )
        
        # Map Pool with Sides
        maps_text = ""
        for i, (map_name, team, side) in enumerate(match_data['picked_maps'], 1):
            other_side = 'Defense' if side == 'Attack' else 'Attack'
            other_team = match_data['team_b_name'] if team == match_data['team_a_name'] else match_data['team_a_name']
            
            if team == 'Decider':
                maps_text += f"**Map {i}: {map_name}** (Decider - Coin Toss)\n"
                maps_text += f"  🛡️ {side}\n\n"
            else:
                maps_text += f"**Map {i}: {map_name}** (Picked by {team})\n"
                maps_text += f"  • {team}: {side}\n"
                maps_text += f"  • {other_team}: {other_side}\n\n"
        
        embed.add_field(
            name="🗺️ Map Pool",
            value=maps_text,
            inline=False
        )
        
        embed.set_footer(text=f"Match ID: {match['id']} • Good luck!")
        
        # Send to both captains
        await captain_1.send(embed=embed)
        await captain_2.send(embed=embed)
        
        # Also send to LFS channel
        lfs_channel_id = os.getenv('LFS_CHANNEL_ID')
        if lfs_channel_id:
            lfs_channel = self.bot.get_channel(int(lfs_channel_id))
            if lfs_channel:
                await lfs_channel.send(
                    f"🎮 **Scrim Match Ready!**\n"
                    f"**{match_data['team_a_name']}** vs **{match_data['team_b_name']}**",
                    embed=embed
                )
    
    async def send_ban_ui(self, match: dict, current_banner: discord.User, other_captain: discord.User, available_maps: list, ban_count: int, total_bans: int):
        """Send map ban UI to current banner"""
        view = MapBanView(match, current_banner, available_maps, ban_count, self)
        
        await current_banner.send(
            f"🗺️ **MAP BANNING** (Ban {ban_count + 1}/{total_bans})\n\n"
            f"Available maps: {', '.join(available_maps)}\n\n"
            f"Select a map to ban:",
            view=view
        )
        
        await other_captain.send(
            f"⏳ **Waiting for {current_banner.display_name}** to ban a map...\n"
            f"Ban {ban_count + 1}/{total_bans}"
        )
    
    async def handle_map_ban(self, match: dict, banner: discord.User, banned_map: str, available_maps: list, ban_count: int):
        """Handle a map ban"""
        match_data = self.match_data[match['id']]
        match_data['banned_maps'].append(banned_map)
        
        # Remove banned map
        new_available = [m for m in available_maps if m != banned_map]
        
        # Get captains
        captain_1 = await self.bot.fetch_user(match['captain_1_discord_id'])
        captain_2 = await self.bot.fetch_user(match['captain_2_discord_id'])
        
        # Notify both
        await captain_1.send(f"🚫 **{banner.display_name}** banned **{banned_map}**")
        await captain_2.send(f"🚫 **{banner.display_name}** banned **{banned_map}**")
        
        # Determine total bans needed
        match_type = match['match_type']
        total_bans = 7 if match_type == 'bo1' else (5 if match_type == 'bo3' else 3)
        
        # Check if banning is complete
        if ban_count + 1 >= total_bans:
            # Banning complete, move to side selection
            match_data['final_maps'] = new_available
            await self.start_side_selection(match, captain_1, captain_2)
        else:
            # Continue banning (alternate between captains)
            toss_winner_id = match_data['toss_winner']
            next_banner = captain_2 if banner.id == captain_1.id else captain_1
            other = captain_1 if next_banner == captain_2 else captain_2
            
            await self.send_ban_ui(match, next_banner, other, new_available, ban_count + 1, total_bans)
    
    async def start_side_selection(self, match: dict, captain_1: discord.User, captain_2: discord.User):
        """Start side selection phase"""
        match_data = self.match_data[match['id']]
        final_maps = match_data['final_maps']
        
        # Toss loser picks sides
        loser_id = match_data['toss_loser']
        side_picker = captain_1 if captain_1.id == loser_id else captain_2
        other = captain_2 if side_picker == captain_1 else captain_1
        
        await side_picker.send(
            f"🛡️⚔️ **SIDE SELECTION**\n\n"
            f"You lost the toss, so you pick sides for all maps!\n"
            f"Maps: {', '.join(final_maps)}\n\n"
            f"Starting with **{final_maps[0]}**..."
        )
        
        await other.send(
            f"⏳ **{side_picker.display_name}** is picking sides for all maps..."
        )
        
        # Send first map side selection
        view = SidePickView(match, side_picker, final_maps[0], 0, len(final_maps), self)
        await side_picker.send(
            f"**Map 1: {final_maps[0]}**\n"
            f"Choose your starting side:",
            view=view
        )
    
    async def handle_side_pick(self, match: dict, picker: discord.User, map_name: str, side: str, map_index: int, total_maps: int):
        """Handle a side pick"""
        match_data = self.match_data[match['id']]
        match_data['sides'][map_name] = side
        
        # Get captains
        captain_1 = await self.bot.fetch_user(match['captain_1_discord_id'])
        captain_2 = await self.bot.fetch_user(match['captain_2_discord_id'])
        other = captain_2 if picker == captain_1 else captain_1
        
        # Notify both
        await picker.send(f"✅ **{map_name}**: You chose **{side}**")
        await other.send(f"✅ **{map_name}**: {picker.display_name} chose **{side}**")
        
        # Check if more maps need sides
        if map_index + 1 < total_maps:
            # Next map
            final_maps = match_data['final_maps']
            next_map = final_maps[map_index + 1]
            
            view = SidePickView(match, picker, next_map, map_index + 1, total_maps, self)
            await picker.send(
                f"**Map {map_index + 2}: {next_map}**\n"
                f"Choose your starting side:",
                view=view
            )
        else:
            # All sides picked, show final summary
            await self.show_final_summary(match, captain_1, captain_2)
    
    async def show_final_summary(self, match: dict, captain_1: discord.User, captain_2: discord.User):
        """Show beautiful final scrim summary"""
        match_data = self.match_data[match['id']]
        final_maps = match_data['final_maps']
        sides = match_data['sides']
        
        # Get team info
        team_1 = await db.get_team_by_captain(captain_1.id)
        team_2 = await db.get_team_by_captain(captain_2.id)
        
        team_1_name = f"{team_1['name']} [{team_1['tag']}]" if team_1 else captain_1.display_name
        team_2_name = f"{team_2['name']} [{team_2['tag']}]" if team_2 else captain_2.display_name
        
        # Determine who is on which side for each map
        loser_id = match_data['toss_loser']
        team_picked_sides = captain_1 if captain_1.id == loser_id else captain_2
        
        # Create beautiful embed
        embed = discord.Embed(
            title="🎮 SCRIM MATCH DETAILS",
            description=f"**{match['match_type'].upper()}** • **{match['region'].upper()}**",
            color=0xFF4654
        )
        
        # Teams
        embed.add_field(
            name="👥 Teams",
            value=f"**Team 1:** {team_1_name}\n**Team 2:** {team_2_name}",
            inline=False
        )
        
        # Maps and Sides
        maps_text = ""
        for i, map_name in enumerate(final_maps, 1):
            side = sides[map_name]
            if team_picked_sides == captain_1:
                maps_text += f"**Map {i}: {map_name}**\n"
                maps_text += f"  • {team_1_name}: {side}\n"
                maps_text += f"  • {team_2_name}: {'Defense' if side == 'Attack' else 'Attack'}\n\n"
            else:
                maps_text += f"**Map {i}: {map_name}**\n"
                maps_text += f"  • {team_1_name}: {'Defense' if side == 'Attack' else 'Attack'}\n"
                maps_text += f"  • {team_2_name}: {side}\n\n"
        
        embed.add_field(name="🗺️ Maps & Sides", value=maps_text, inline=False)
        
        # Additional info
        time_display = match['time_slot'].strftime("%I:%M %p %Z") if isinstance(match['time_slot'], datetime) else str(match['time_slot'])
        embed.add_field(name="⏰ Time", value=time_display, inline=True)
        embed.add_field(name="🌍 Region", value=match['region'].upper(), inline=True)
        
        embed.set_footer(text="Good luck and have fun! 🎉")
        
        # Send to both captains
        await captain_1.send(embed=embed)
        await captain_2.send(embed=embed)
        
        # Update match status to in_progress (they're playing now)
        await db.update_scrim_match_status(match['id'], 'in_progress')
        
        print(f"✅ Scrim match {match['id']} setup completed, now in progress")
        
        # Log scheduled scrim to bot logs
        logs_channel_id = os.getenv('LOGS_CHANNEL_ID')
        if logs_channel_id:
            try:
                logs_channel = self.bot.get_channel(int(logs_channel_id))
                if logs_channel:
                    log_embed = discord.Embed(
                        title="🎮 Scrim Scheduled",
                        description=f"**Match ID:** {match['id']}\n**Type:** {match['match_type'].upper()}\n**Region:** {match['region'].upper()}",
                        color=0x3498DB,
                        timestamp=datetime.now()
                    )
                    
                    log_embed.add_field(
                        name="Teams",
                        value=f"**{team_1_name}** vs **{team_2_name}",
                        inline=False
                    )
                    
                    log_embed.add_field(
                        name="Captains",
                        value=f"{captain_1.mention} vs {captain_2.mention}",
                        inline=False
                    )
                    
                    log_embed.add_field(name="Maps & Sides", value=maps_text, inline=False)
                    log_embed.add_field(name="⏰ Time", value=time_display, inline=True)
                    log_embed.add_field(name="🌍 Region", value=match['region'].upper(), inline=True)
                    
                    await logs_channel.send(embed=log_embed)
            except Exception as e:
                print(f"Error logging scheduled scrim: {e}")
        
        # Send completion check buttons after match details
        await self.send_completion_check(match, captain_1, captain_2)
    
    async def send_completion_check(self, match: dict, captain_1: discord.User, captain_2: discord.User):
        """Send completion check to both captains after match setup"""
        # Wait a bit before asking (they need to play first!)
        embed = discord.Embed(
            title="✅ Match Ready",
            description=(
                "Your scrim details have been finalized! Once you've finished playing:\n\n"
                "• Click **✅ Yes, We're Done** if the match is complete\n"
                "• Click **❌ Cancel** if you need to cancel the scrim\n\n"
                "**Both captains must respond to proceed.**"
            ),
            color=0x00FF00
        )
        
        # Send to captain 1
        view1 = ScrimCompleteCheckView(match['id'], captain_1.id, captain_2.id, self)
        await captain_1.send(embed=embed, view=view1)
        
        # Send to captain 2
        view2 = ScrimCompleteCheckView(match['id'], captain_2.id, captain_1.id, self)
        await captain_2.send(embed=embed, view=view2)
    
    async def request_scrim_screenshots(self, match_id: int):
        """Request screenshots from both captains"""
        match = await db.get_scrim_match_by_id(match_id)
        if not match:
            return
        
        captain_1 = await self.bot.fetch_user(match['captain_1_discord_id'])
        captain_2 = await self.bot.fetch_user(match['captain_2_discord_id'])
        
        # Initialize screenshot storage
        if not hasattr(self, 'scrim_screenshots'):
            self.scrim_screenshots = {}
        
        match_key = f"match_{match_id}"
        self.scrim_screenshots[match_key] = {}
        
        # Request from both captains
        embed = discord.Embed(
            title="📸 Upload Match Screenshot",
            description=(
                "Please upload a screenshot of the final match results.\n\n"
                "**Requirements:**\n"
                "• Must show final scoreboard\n"
                "• Must show all 10 player names clearly\n"
                "• Must be from the end-game screen\n\n"
                "Simply attach and send the image in this DM."
            ),
            color=0x3498DB
        )
        
        await captain_1.send(embed=embed)
        await captain_2.send(embed=embed)
        
        # Store that we're waiting for screenshots
        if not hasattr(self, 'awaiting_screenshots'):
            self.awaiting_screenshots = {}
        self.awaiting_screenshots[match_id] = {
            'captain_1': captain_1.id,
            'captain_2': captain_2.id,
            'received': set()
        }
    
    async def process_scrim_cancellation(self, match_id: int, reasons: dict):
        """Process scrim cancellation with reasons from both captains"""
        match = await db.get_scrim_match_by_id(match_id)
        if not match:
            return
        
        # Get team info
        captain_1 = await self.bot.fetch_user(match['captain_1_discord_id'])
        captain_2 = await self.bot.fetch_user(match['captain_2_discord_id'])
        
        team_1 = await db.get_team_by_captain(captain_1.id)
        team_2 = await db.get_team_by_captain(captain_2.id)
        
        team_1_name = f"{team_1['name']} [{team_1['tag']}]" if team_1 else captain_1.display_name
        team_2_name = f"{team_2['name']} [{team_2['tag']}]" if team_2 else captain_2.display_name
        
        # Update match status
        await db.update_scrim_match_status(match_id, 'cancelled')
        
        # Add both teams to avoid list for 6 hours
        try:
            await db.add_to_avoid_list(
                match['captain_1_discord_id'],
                match['captain_2_discord_id'],
                hours=6
            )
            await db.add_to_avoid_list(
                match['captain_2_discord_id'],
                match['captain_1_discord_id'],
                hours=6
            )
        except Exception as e:
            print(f"Error adding to avoid list: {e}")
        
        # Send cancellation confirmation to both captains
        cancel_embed = discord.Embed(
            title="❌ Scrim Cancelled",
            description=(
                "Both captains have agreed to cancel the scrim.\n\n"
                f"**Match ID:** {match_id}\n"
                f"**{team_1_name}** vs **{team_2_name}**"
            ),
            color=0xFF0000
        )
        
        cancel_embed.add_field(
            name="Your Reason",
            value=reasons.get(captain_1.id, 'No reason provided'),
            inline=False
        )
        
        cancel_embed.add_field(
            name="Other Captain's Reason",
            value=reasons.get(captain_2.id, 'No reason provided'),
            inline=False
        )
        
        # Send to captain 1
        try:
            await captain_1.send(embed=cancel_embed)
        except:
            pass
        
        # Send to captain 2 (swap the reasons)
        cancel_embed_2 = discord.Embed(
            title="❌ Scrim Cancelled",
            description=(
                "Both captains have agreed to cancel the scrim.\n\n"
                f"**Match ID:** {match_id}\n"
                f"**{team_1_name}** vs **{team_2_name}**"
            ),
            color=0xFF0000
        )
        
        cancel_embed_2.add_field(
            name="Your Reason",
            value=reasons.get(captain_2.id, 'No reason provided'),
            inline=False
        )
        
        cancel_embed_2.add_field(
            name="Other Captain's Reason",
            value=reasons.get(captain_1.id, 'No reason provided'),
            inline=False
        )
        
        try:
            await captain_2.send(embed=cancel_embed_2)
        except:
            pass
        
        # Log to bot logs channel
        logs_channel_id = os.getenv('LOGS_CHANNEL_ID')
        if logs_channel_id:
            try:
                logs_channel = self.bot.get_channel(int(logs_channel_id))
                if logs_channel:
                    embed = discord.Embed(
                        title="❌ Scrim Cancelled",
                        description=f"**Match ID:** {match_id}\n**Type:** {match['match_type'].upper()}\n**Region:** {match['region'].upper()}",
                        color=0xFF0000,
                        timestamp=datetime.now()
                    )
                    
                    embed.add_field(
                        name=f"Team 1: {team_1_name}",
                        value=f"**Captain:** {captain_1.mention}\n**Reason:** {reasons.get(captain_1.id, 'No reason provided')}",
                        inline=False
                    )
                    
                    embed.add_field(
                        name=f"Team 2: {team_2_name}",
                        value=f"**Captain:** {captain_2.mention}\n**Reason:** {reasons.get(captain_2.id, 'No reason provided')}",
                        inline=False
                    )
                    
                    await logs_channel.send(embed=embed)
            except:
                pass
        
        # Clean up match data
        if match_id in self.match_data:
            del self.match_data[match_id]
        
        # Clear vote tracking
        match_key = f"match_{match_id}"
        if hasattr(self, 'scrim_completion_votes') and match_key in self.scrim_completion_votes:
            del self.scrim_completion_votes[match_key]
        if hasattr(self, 'scrim_cancel_reasons') and match_key in self.scrim_cancel_reasons:
            del self.scrim_cancel_reasons[match_key]
        
        print(f"❌ Scrim match {match_id} cancelled by both captains")
    
    async def validate_scrim_screenshots(self, match_id: int, screenshot_1, screenshot_2):
        """Validate screenshots and extract scores"""
        # This would use OCR service similar to registration
        # For now, we'll implement a basic version
        
        # TODO: Implement actual screenshot processing with OCR
        # 1. Download both screenshots
        # 2. Use OCR to extract player names
        # 3. Compare against team rosters
        # 4. Extract scores
        # 5. Return validation result
        
        # Placeholder return
        return {
            'valid': True,
            'team_1_score': 13,
            'team_2_score': 11,
            'map': 'Haven'
        }
    
    async def process_screenshots(self, match_id: int):
        """Process both screenshots after they're received"""
        try:
            match = await db.get_scrim_match_by_id(match_id)
            if not match:
                return
            
            captain_1 = await self.bot.fetch_user(match['captain_1_discord_id'])
            captain_2 = await self.bot.fetch_user(match['captain_2_discord_id'])
            
            match_key = f"match_{match_id}"
            screenshots = self.scrim_screenshots.get(match_key, {})
            
            if len(screenshots) < 2:
                return
            
            # Get both screenshots
            screenshot_1 = screenshots[captain_1.id]
            screenshot_2 = screenshots[captain_2.id]
            
            # Notify both captains we're processing
            await captain_1.send("⏳ Processing screenshots...")
            await captain_2.send("⏳ Processing screenshots...")
            
            # Validate and extract scores
            result = await self.validate_scrim_screenshots(match_id, screenshot_1, screenshot_2)
            
            if not result['valid']:
                # Screenshots don't match or couldn't be validated
                await captain_1.send("❌ Screenshots couldn't be validated. Please contact an admin.")
                await captain_2.send("❌ Screenshots couldn't be validated. Please contact an admin.")
                return
            
            # Scores extracted, ask for confirmation
            team_1 = await db.get_team_by_captain(captain_1.id)
            team_2 = await db.get_team_by_captain(captain_2.id)
            
            team_1_name = f"{team_1['name']} [{team_1['tag']}]" if team_1 else captain_1.display_name
            team_2_name = f"{team_2['name']} [{team_2['tag']}]" if team_2 else captain_2.display_name
            
            score_embed = discord.Embed(
                title="📊 Detected Scores",
                description="Please confirm if these scores are correct:",
                color=0x3498DB
            )
            
            score_embed.add_field(
                name="Final Score",
                value=f"**{team_1_name}:** {result['team_1_score']}\n**{team_2_name}:** {result['team_2_score']}",
                inline=False
            )
            
            if 'map' in result:
                score_embed.add_field(name="Map", value=result['map'], inline=False)
            
            # Send confirmation buttons to both captains
            view1 = ScoreConfirmationView(match_id, captain_1.id, result['team_1_score'], result['team_2_score'], self)
            await captain_1.send(embed=score_embed, view=view1)
            
            view2 = ScoreConfirmationView(match_id, captain_2.id, result['team_1_score'], result['team_2_score'], self)
            await captain_2.send(embed=score_embed, view=view2)
            
            # Clean up screenshot tracking
            if match_id in self.awaiting_screenshots:
                del self.awaiting_screenshots[match_id]
            
        except Exception as e:
            print(f"Error processing screenshots for match {match_id}: {e}")
            import traceback
            traceback.print_exc()
    
    async def save_scrim_results(self, match_id: int, team_1_score: int, team_2_score: int):
        """Save scrim results to database"""
        match = await db.get_scrim_match_by_id(match_id)
        if not match:
            return
        
        # Update match status to completed with scores
        await db.update_scrim_match_status(match_id, 'completed')
        
        # TODO: Add function to store scores in database
        # This would require a new table or columns in scrim_matches
        
        # Get captains
        captain_1 = await self.bot.fetch_user(match['captain_1_discord_id'])
        captain_2 = await self.bot.fetch_user(match['captain_2_discord_id'])
        
        # Get screenshots if available
        match_key = f"match_{match_id}"
        screenshots = self.scrim_screenshots.get(match_key, {}) if hasattr(self, 'scrim_screenshots') else {}
        
        # Log to bot logs
        logs_channel_id = os.getenv('LOGS_CHANNEL_ID')
        if logs_channel_id:
            try:
                logs_channel = self.bot.get_channel(int(logs_channel_id))
                if logs_channel:
                    team_1 = await db.get_team_by_captain(captain_1.id)
                    team_2 = await db.get_team_by_captain(captain_2.id)
                    
                    team_1_name = f"{team_1['name']} [{team_1['tag']}]" if team_1 else captain_1.display_name
                    team_2_name = f"{team_2['name']} [{team_2['tag']}]" if team_2 else captain_2.display_name
                    
                    embed = discord.Embed(
                        title="✅ Scrim Completed",
                        description=f"**Match ID:** {match_id}\n**Type:** {match['match_type'].upper()}\n**Region:** {match['region'].upper()}",
                        color=0x00FF00,
                        timestamp=datetime.now()
                    )
                    
                    embed.add_field(
                        name="Final Score",
                        value=f"**{team_1_name}:** {team_1_score}\n**{team_2_name}:** {team_2_score}",
                        inline=False
                    )
                    
                    winner = team_1_name if team_1_score > team_2_score else team_2_name
                    embed.add_field(name="Winner", value=f"🏆 {winner}", inline=False)
                    
                    embed.add_field(
                        name="Captains",
                        value=f"{captain_1.mention} vs {captain_2.mention}",
                        inline=False
                    )
                    
                    # Send embed first
                    msg = await logs_channel.send(embed=embed)
                    
                    # Send screenshots if available
                    if screenshots:
                        screenshot_files = []
                        try:
                            for captain_id, attachment in screenshots.items():
                                if attachment:
                                    # Download and re-upload screenshot
                                    file_bytes = await attachment.read()
                                    screenshot_files.append(
                                        discord.File(
                                            io.BytesIO(file_bytes),
                                            filename=f"screenshot_{captain_id}.png"
                                        )
                                    )
                            
                            if screenshot_files:
                                await logs_channel.send(
                                    f"📸 **Screenshots for Match ID {match_id}:**",
                                    files=screenshot_files
                                )
                        except Exception as e:
                            print(f"Error uploading screenshots: {e}")
            except Exception as e:
                print(f"Error logging scrim completion: {e}")
        
        # Clean up tracking
        match_key = f"match_{match_id}"
        if hasattr(self, 'score_confirmations') and match_key in self.score_confirmations:
            del self.score_confirmations[match_key]
        
        print(f"✅ Scrim match {match_id} results saved: {team_1_score}-{team_2_score}")
    
    async def handle_score_dispute(self, match_id: int, disputer: discord.User):
        """Handle when a captain disputes the detected scores"""
        logs_channel_id = os.getenv('LOGS_CHANNEL_ID')
        if logs_channel_id:
            try:
                logs_channel = self.bot.get_channel(int(logs_channel_id))
                if logs_channel:
                    embed = discord.Embed(
                        title="⚠️ Score Dispute",
                        description=f"**Match ID:** {match_id}\n{disputer.mention} disputed the detected scores.",
                        color=0xFFA500,
                        timestamp=datetime.now()
                    )
                    embed.add_field(
                        name="Action Required",
                        value="An admin needs to manually review and record the match results.",
                        inline=False
                    )
                    await logs_channel.send(embed=embed)
            except:
                pass
        
        print(f"⚠️ Score dispute for match {match_id} by {disputer.display_name}")
    
    @app_commands.command(name="cancel-scrim", description="Cancel your pending scrim request or match")
    async def cancel_scrim(self, interaction: discord.Interaction):
        """Cancel a pending scrim request or match"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            captain_id = interaction.user.id
            cancelled_count = 0
            
            # First, check for pending scrim REQUESTS (LFS posts in queue)
            pending_requests = await db.get_pending_scrim_requests()
            my_requests = [r for r in pending_requests if r['captain_discord_id'] == captain_id]
            
            if my_requests:
                # Cancel all the user's pending requests
                for request in my_requests:
                    await db.cancel_scrim_request(request['id'])
                    cancelled_count += 1
                
                await interaction.followup.send(
                    f"✅ Cancelled {cancelled_count} pending scrim request(s) from the queue.",
                    ephemeral=True
                )
                return
            
            # If no requests, check for pending MATCHES (waiting for approval)
            pending_matches = await db.get_captain_pending_matches(captain_id)
            
            if not pending_matches:
                await interaction.followup.send(
                    "❌ You don't have any pending scrim requests or matches to cancel.",
                    ephemeral=True
                )
                return
            
            # Cancel all pending matches
            for match in pending_matches:
                await db.update_scrim_match_status(match['id'], 'declined')
                cancelled_count += 1
            
            await interaction.followup.send(
                f"✅ Cancelled {cancelled_count} pending scrim match(es).",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ Error cancelling scrim: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="lfs-setup", description="Get the LFS channel ID for .env file (Admin only)")
    async def lfs_setup(self, interaction: discord.Interaction):
        """Helper command to get the LFS channel ID"""
        # Check if user is admin
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ This command is only available to administrators.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # Find the LFS channel
        lfs_channel = discord.utils.get(interaction.guild.text_channels, name=self.lfs_channel_name)
        
        if not lfs_channel:
            await interaction.followup.send(
                f"❌ Channel `{self.lfs_channel_name}` not found!\n\n"
                f"Please create a text channel named: `{self.lfs_channel_name}`",
                ephemeral=True
            )
            return
        
        # Send the channel ID
        message = (
            f"✅ **LFS Channel Found!**\n\n"
            f"**Channel:** {lfs_channel.mention}\n"
            f"**Channel ID:** `{lfs_channel.id}`\n\n"
            f"**Setup Instructions:**\n"
            f"1. Open your `.env` file\n"
            f"2. Add this line:\n"
            f"```\n"
            f"LFS_CHANNEL_ID={lfs_channel.id}\n"
            f"```\n"
            f"3. Restart the bot\n\n"
            f"The bot will automatically send instructions to {lfs_channel.mention} on startup!"
        )
        
        await interaction.followup.send(message, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Scrim(bot))
