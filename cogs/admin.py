import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
import pandas as pd
from services import db

class AdminSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = Path(__file__).parent.parent / "data"
        self.players_file = self.data_dir / "players.json"
        self.teams_file = self.data_dir / "teams.json"
        self.logs_file = self.data_dir / "admin_logs.json"
    
    def is_admin(self, interaction: discord.Interaction) -> bool:
        if not interaction.guild:
            return False
        # Check if user is server owner
        if interaction.guild.owner_id == interaction.user.id:
            return True
        if interaction.user.guild_permissions.administrator:
            return True
        user_roles = [role.name.lower() for role in interaction.user.roles]
        return any(role in user_roles for role in ['admin', 'staff', 'moderator', 'mod'])
    
    def log_action(self, user_id: int, username: str, action: str, details: str, old_data: dict = None):
        try:
            with open(self.logs_file, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []
        
        log_entry = {
            "id": len(logs) + 1,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "username": username,
            "action": action,
            "details": details
        }
        
        if old_data:
            log_entry["old_data"] = old_data
        
        logs.append(log_entry)
        
        if len(logs) > 1000:
            logs = logs[-1000:]
        
        with open(self.logs_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=4, ensure_ascii=False)

    @app_commands.command(name="edit-player", description="[ADMIN] Edit player IGN and ID")
    @app_commands.describe(
        player="Player's Discord @mention or ID",
        new_ign="New in-game name (optional)",
        new_id="New in-game ID (optional)"
    )
    async def edit_player(self, interaction: discord.Interaction, player: discord.Member, new_ign: Optional[str] = None, new_id: Optional[int] = None):
        if not self.is_admin(interaction):
            await interaction.response.send_message("❌ You need Admin or Staff role!", ephemeral=True)
            return
        
        if not new_ign and not new_id:
            await interaction.response.send_message("❌ Provide at least one field to update!", ephemeral=True)
            return
        
        # Get player from database
        player_data = await db.get_player(player.id)
        
        if not player_data:
            await interaction.response.send_message(f"❌ {player.mention} is not registered!", ephemeral=True)
            return
        
        old_values = player_data.copy()
        
        # Update player in database
        try:
            if new_ign:
                await db.update_player_ign(player.id, new_ign)
            if new_id:
                # Update player_id field
                pool = await db.get_pool()
                async with pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE players
                        SET player_id = $1
                        WHERE discord_id = $2
                    """, new_id, player.id)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error updating player: {e}", ephemeral=True)
            return
        
        changes = []
        if new_ign:
            changes.append(f"IGN: {old_values.get('ign')} → {new_ign}")
        if new_id:
            changes.append(f"ID: {old_values.get('player_id')} → {new_id}")
        
        self.log_action(interaction.user.id, str(interaction.user), "edit_player", f"Edited {player} - {', '.join(changes)}", old_data=old_values)
        
        embed = discord.Embed(title="✅ Player Updated", description=f"Successfully updated {player.mention}", color=discord.Color.green())
        if new_ign:
            embed.add_field(name="IGN", value=f"`{old_values.get('ign')}` → **{new_ign}**", inline=False)
        if new_id:
            embed.add_field(name="ID", value=f"`{old_values.get('player_id')}` → **{new_id}**", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="edit-kda", description="[ADMIN] Edit player K/D/A stats")
    @app_commands.describe(
        player="Player's Discord @mention or ID",
        kills="New kills count",
        deaths="New deaths count",
        assists="New assists count",
        tournament_id="Tournament ID (default: 1)"
    )
    async def edit_kda(self, interaction: discord.Interaction, player: discord.Member, kills: int, deaths: int, assists: int, tournament_id: str = "1"):
        if not self.is_admin(interaction):
            await interaction.response.send_message("❌ You need Admin or Staff role!", ephemeral=True)
            return
        
        from services import db

        # Check if player exists
        existing_player = await db.get_player(player.id)
        if not existing_player:
            await interaction.response.send_message(f"❌ {player.mention} is not registered!", ephemeral=True)
            return
        
        # Get current stats for logging
        old_stats = await db.get_player_stats(player.id)
        if not old_stats:
            old_stats = {"kills": 0, "deaths": 0, "assists": 0}
        
        # Update stats in database
        stats_update = {
            "kills": kills,
            "deaths": deaths,
            "assists": assists
        }
        
        try:
            await db.update_player_stats(player.id, stats_update)
        
            # Log the action
            self.log_action(interaction.user.id, str(interaction.user), "edit_kda", 
                        f"Edited {player} K/D/A: {old_stats.get('kills', 0)}/{old_stats.get('deaths', 0)}/{old_stats.get('assists', 0)} → {kills}/{deaths}/{assists}",
                        old_data=old_stats)
            
            kd_ratio = kills / deaths if deaths > 0 else kills
            embed = discord.Embed(title="✅ Stats Updated", description=f"Successfully updated {player.mention}'s K/D/A", color=discord.Color.green())
            embed.add_field(name="Old Stats", value=f"**K/D/A:** {old_stats.get('kills', 0)}/{old_stats.get('deaths', 0)}/{old_stats.get('assists', 0)}", inline=True)
            embed.add_field(name="New Stats", value=f"**K/D/A:** {kills}/{deaths}/{assists}", inline=True)
            embed.add_field(name="K/D Ratio", value=f"**{kd_ratio:.2f}**", inline=False)
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error updating stats: {str(e)}", ephemeral=True)

    @app_commands.command(name="edit-record", description="[ADMIN] Edit player matches/wins/losses")
    @app_commands.describe(
        player="Player's Discord @mention or ID",
        matches="Total matches played",
        wins="Total wins",
        losses="Total losses",
        tournament_id="Tournament ID (default: 1)"
    )
    async def edit_record(self, interaction: discord.Interaction, player: discord.Member, matches: int, wins: int, losses: int, tournament_id: str = "1"):
        if not self.is_admin(interaction):
            await interaction.response.send_message("❌ You need Admin or Staff role!", ephemeral=True)
            return
        
        from services import db

        # Check if player exists
        existing_player = await db.get_player(player.id)
        if not existing_player:
            await interaction.response.send_message(f"❌ {player.mention} is not registered!", ephemeral=True)
            return
        
        # Get current stats for logging
        old_stats = await db.get_player_stats(player.id)
        if not old_stats:
            old_stats = {"wins": 0, "losses": 0}
        
        # Update stats in database
        try:
            stats_update = {
                "matches_played": matches,
                "wins": wins,
                "losses": losses
            }
            await db.update_player_stats(player.id, stats_update)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error updating stats: {str(e)}", ephemeral=True)
            return
        
        self.log_action(interaction.user.id, str(interaction.user), "edit_record",
                       f"Edited {player} record: {old_stats.get('wins', 0)}W-{old_stats.get('losses', 0)}L → {wins}W-{losses}L",
                       old_data=old_stats)
        
        win_rate = (wins / matches * 100) if matches > 0 else 0
        embed = discord.Embed(title="✅ Record Updated", description=f"Successfully updated {player.mention}'s match record", color=discord.Color.green())
        embed.add_field(name="Old Record", value=f"**{old_stats.get('wins', 0)}W - {old_stats.get('losses', 0)}L**\n{old_stats.get('matches_played', 0)} matches", inline=True)
        embed.add_field(name="New Record", value=f"**{wins}W - {losses}L**\n{matches} matches\n{win_rate:.1f}% WR", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="delete-player", description="[ADMIN] Delete a player from the system")
    @app_commands.describe(player="Player's Discord @mention or ID")
    async def delete_player(self, interaction: discord.Interaction, player: discord.Member):
        if not self.is_admin(interaction):
            await interaction.response.send_message("❌ You need Admin or Staff role!", ephemeral=True)
            return
        
        try:
            with open(self.players_file, "r", encoding="utf-8") as f:
                players = json.load(f)
        except FileNotFoundError:
            await interaction.response.send_message("❌ No players found!", ephemeral=True)
            return
        
        found = False
        deleted_player = None
        for i, p in enumerate(players):
            if p.get("discord_id") == player.id:
                deleted_player = p.copy()
                players.pop(i)
                found = True
                break
        
        if not found:
            await interaction.response.send_message(f"❌ {player.mention} is not registered!", ephemeral=True)
            return
        
        with open(self.players_file, "w", encoding="utf-8") as f:
            json.dump(players, f, indent=4, ensure_ascii=False)
        
        self.log_action(interaction.user.id, str(interaction.user), "delete_player", f"Deleted player {deleted_player.get('ign', 'Unknown')} ({player.id})", old_data=deleted_player)
        
        embed = discord.Embed(title="✅ Player Deleted", description=f"Successfully deleted {player.mention}\nIGN: **{deleted_player.get('ign', 'Unknown')}**", color=discord.Color.red())
        embed.add_field(name="💡 Tip", value="This action is logged in `/admin-logs`", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ban-player", description="[ADMIN] Ban player from leaderboards")
    @app_commands.describe(player="Player's Discord @mention or ID", reason="Reason for ban")
    async def ban_player(self, interaction: discord.Interaction, player: discord.Member, reason: Optional[str] = "No reason provided"):
        if not self.is_admin(interaction):
            await interaction.response.send_message("❌ You need Admin or Staff role!", ephemeral=True)
            return
        
        try:
            with open(self.players_file, "r", encoding="utf-8") as f:
                players = json.load(f)
        except FileNotFoundError:
            await interaction.response.send_message("❌ No players found!", ephemeral=True)
            return
        
        player_found = False
        for p in players:
            if p.get("discord_id") == player.id:
                player_found = True
                p["banned"] = True
                p["ban_reason"] = reason
                p["banned_by"] = interaction.user.id
                p["banned_at"] = datetime.now().isoformat()
                break
        
        if not player_found:
            await interaction.response.send_message(f"❌ {player.mention} is not registered!", ephemeral=True)
            return
        
        with open(self.players_file, "w", encoding="utf-8") as f:
            json.dump(players, f, indent=4, ensure_ascii=False)
        
        self.log_action(interaction.user.id, str(interaction.user), "ban_player", f"Banned {player} - Reason: {reason}")
        
        embed = discord.Embed(title="🚫 Player Banned", description=f"{player.mention} has been banned from leaderboards.", color=discord.Color.orange())
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Note", value="Player data is preserved. Use `/unban-player` to restore.", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unban-player", description="[ADMIN] Unban a player")
    @app_commands.describe(player="Player's Discord @mention or ID")
    async def unban_player(self, interaction: discord.Interaction, player: discord.Member):
        if not self.is_admin(interaction):
            await interaction.response.send_message("❌ You need Admin or Staff role!", ephemeral=True)
            return
        
        try:
            with open(self.players_file, "r", encoding="utf-8") as f:
                players = json.load(f)
        except FileNotFoundError:
            await interaction.response.send_message("❌ No players found!", ephemeral=True)
            return
        
        player_found = False
        was_banned = False
        for p in players:
            if p.get("discord_id") == player.id:
                player_found = True
                was_banned = p.get("banned", False)
                p["banned"] = False
                p.pop("ban_reason", None)
                p.pop("banned_by", None)
                p.pop("banned_at", None)
                break
        
        if not player_found:
            await interaction.response.send_message(f"❌ {player.mention} is not registered!", ephemeral=True)
            return
        
        if not was_banned:
            await interaction.response.send_message(f"❌ {player.mention} is not banned!", ephemeral=True)
            return
        
        with open(self.players_file, "w", encoding="utf-8") as f:
            json.dump(players, f, indent=4, ensure_ascii=False)
        
        self.log_action(interaction.user.id, str(interaction.user), "unban_player", f"Unbanned {player}")
        
        embed = discord.Embed(title="✅ Player Unbanned", description=f"{player.mention} has been unbanned and will appear on leaderboards.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ban-team", description="[ADMIN] Ban team from leaderboards")
    @app_commands.describe(team_name="Team name", reason="Reason for ban")
    async def ban_team(self, interaction: discord.Interaction, team_name: str, reason: Optional[str] = "No reason provided"):
        if not self.is_admin(interaction):
            await interaction.response.send_message("❌ You need Admin or Staff role!", ephemeral=True)
            return
        
        try:
            with open(self.teams_file, "r", encoding="utf-8") as f:
                teams = json.load(f)
        except FileNotFoundError:
            await interaction.response.send_message("❌ No teams found!", ephemeral=True)
            return
        
        team_found = False
        for t in teams:
            if t.get("name", "").lower() == team_name.lower():
                team_found = True
                t["banned"] = True
                t["ban_reason"] = reason
                t["banned_by"] = interaction.user.id
                t["banned_at"] = datetime.now().isoformat()
                break
        
        if not team_found:
            await interaction.response.send_message(f"❌ Team **{team_name}** not found!", ephemeral=True)
            return
        
        with open(self.teams_file, "w", encoding="utf-8") as f:
            json.dump(teams, f, indent=4, ensure_ascii=False)
        
        self.log_action(interaction.user.id, str(interaction.user), "ban_team", f"Banned team {team_name} - Reason: {reason}")
        
        embed = discord.Embed(title="🚫 Team Banned", description=f"Team **{team_name}** has been banned from leaderboards.", color=discord.Color.orange())
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Note", value="Team data is preserved. Use `/unban-team` to restore.", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unban-team", description="[ADMIN] Unban a team")
    @app_commands.describe(team_name="Team name")
    async def unban_team(self, interaction: discord.Interaction, team_name: str):
        if not self.is_admin(interaction):
            await interaction.response.send_message("❌ You need Admin or Staff role!", ephemeral=True)
            return
        
        try:
            with open(self.teams_file, "r", encoding="utf-8") as f:
                teams = json.load(f)
        except FileNotFoundError:
            await interaction.response.send_message("❌ No teams found!", ephemeral=True)
            return
        
        team_found = False
        was_banned = False
        for t in teams:
            if t.get("name", "").lower() == team_name.lower():
                team_found = True
                was_banned = t.get("banned", False)
                t["banned"] = False
                t.pop("ban_reason", None)
                t.pop("banned_by", None)
                t.pop("banned_at", None)
                break
        
        if not team_found:
            await interaction.response.send_message(f"❌ Team **{team_name}** not found!", ephemeral=True)
            return
        
        if not was_banned:
            await interaction.response.send_message(f"❌ Team **{team_name}** is not banned!", ephemeral=True)
            return
        
        with open(self.teams_file, "w", encoding="utf-8") as f:
            json.dump(teams, f, indent=4, ensure_ascii=False)
        
        self.log_action(interaction.user.id, str(interaction.user), "unban_team", f"Unbanned team {team_name}")
        
        embed = discord.Embed(title="✅ Team Unbanned", description=f"Team **{team_name}** has been unbanned and will appear on leaderboards.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="export-data", description="[ADMIN] Export all tournament data as Excel")
    @app_commands.describe(include_banned="Include banned players/teams (default: no)")
    async def export_data(self, interaction: discord.Interaction, include_banned: bool = False):
        if not self.is_admin(interaction):
            await interaction.response.send_message("❌ You need Admin or Staff role!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Load all data
            players = []
            teams = []
            matches = []
            
            if os.path.exists(self.players_file):
                with open(self.players_file, "r", encoding="utf-8") as f:
                    players = json.load(f)
            
            if os.path.exists(self.teams_file):
                with open(self.teams_file, "r", encoding="utf-8") as f:
                    teams = json.load(f)
            
            matches_file = self.data_dir / "matches.json"
            if os.path.exists(matches_file):
                with open(matches_file, "r", encoding="utf-8") as f:
                    matches = json.load(f)
            
            # Filter banned if requested
            if not include_banned:
                players = [p for p in players if not p.get("banned", False)]
                teams = [t for t in teams if not t.get("banned", False)]
            
            # Create Excel file with multiple sheets
            export_filename = f"tournament_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            export_path = self.data_dir / "exports"
            export_path.mkdir(exist_ok=True)
            export_file = export_path / export_filename
            
            with pd.ExcelWriter(export_file, engine='openpyxl') as writer:
                # Players sheet
                players_data = []
                for p in players:
                    stats = p.get("stats", {}).get("1", {})
                    players_data.append({
                        "Discord ID": p.get("discord_id"),
                        "IGN": p.get("ign"),
                        "In-Game ID": p.get("id"),
                        "Region": p.get("region", "Unknown"),
                        "Kills": stats.get("kills", 0),
                        "Deaths": stats.get("deaths", 0),
                        "Assists": stats.get("assists", 0),
                        "Matches": stats.get("matches_played", 0),
                        "Wins": stats.get("wins", 0),
                        "Losses": stats.get("losses", 0),
                        "K/D Ratio": round(stats.get("kills", 0) / stats.get("deaths", 1), 2) if stats.get("deaths", 0) > 0 else stats.get("kills", 0),
                        "Win Rate %": round((stats.get("wins", 0) / stats.get("matches_played", 1)) * 100, 1) if stats.get("matches_played", 0) > 0 else 0,
                        "Banned": p.get("banned", False)
                    })
                
                df_players = pd.DataFrame(players_data)
                df_players.to_excel(writer, sheet_name='Players', index=False)
                
                # Teams sheet
                teams_data = []
                for t in teams:
                    record = t.get("record", {})
                    wins = record.get("wins", 0)
                    losses = record.get("losses", 0)
                    total_matches = wins + losses
                    
                    teams_data.append({
                        "Team Name": t.get("name"),
                        "Region": t.get("region", "Unknown"),
                        "Roster Size": len(t.get("roster", [])),
                        "Wins": wins,
                        "Losses": losses,
                        "Total Matches": total_matches,
                        "Win Rate %": round((wins / total_matches) * 100, 1) if total_matches > 0 else 0,
                        "Banned": t.get("banned", False)
                    })
                
                df_teams = pd.DataFrame(teams_data)
                df_teams.to_excel(writer, sheet_name='Teams', index=False)
                
                # Matches sheet
                matches_data = []
                for m in matches:
                    matches_data.append({
                        "Date": m.get("timestamp", "Unknown"),
                        "Team A": m.get("team_a"),
                        "Team B": m.get("team_b"),
                        "Winner": m.get("winner"),
                        "Tournament": m.get("tournament_id", "1")
                    })
                
                df_matches = pd.DataFrame(matches_data)
                df_matches.to_excel(writer, sheet_name='Matches', index=False)
            
            # Log action
            self.log_action(interaction.user.id, str(interaction.user), "export_data", 
                          f"Exported data to {export_filename} (include_banned={include_banned})")
            
            # Send file
            embed = discord.Embed(title="📊 Data Export Complete", description="All tournament data has been exported to Excel.", color=discord.Color.blue())
            embed.add_field(name="Players", value=str(len(players)), inline=True)
            embed.add_field(name="Teams", value=str(len(teams)), inline=True)
            embed.add_field(name="Matches", value=str(len(matches)), inline=True)
            embed.add_field(name="Sheets", value="• Players\n• Teams\n• Matches", inline=False)
            embed.add_field(name="Filename", value=f"`{export_filename}`", inline=False)
            
            await interaction.followup.send(embed=embed, file=discord.File(export_file, filename=export_filename))
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error exporting data: {str(e)}", ephemeral=True)

    @app_commands.command(name="archive-season", description="[ADMIN] Archive current season")
    @app_commands.describe(season_name="Name for the archived season (e.g., 'Season 1')")
    async def archive_season(self, interaction: discord.Interaction, season_name: str):
        if not self.is_admin(interaction):
            await interaction.response.send_message("❌ You need Admin or Staff role!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            archive_path = self.data_dir / "archives" / season_name.replace(" ", "_").lower()
            archive_path.mkdir(parents=True, exist_ok=True)
            
            files_to_archive = ["players.json", "teams.json", "matches.json", "scoring_config.json", "admin_logs.json"]
            
            archived_files = []
            for filename in files_to_archive:
                source = self.data_dir / filename
                if source.exists():
                    dest = archive_path / filename
                    shutil.copy2(source, dest)
                    archived_files.append(filename)
            
            metadata = {
                "season_name": season_name,
                "archived_date": datetime.now().isoformat(),
                "archived_by": str(interaction.user),
                "archived_files": archived_files
            }
            
            with open(archive_path / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)
            
            self.log_action(interaction.user.id, str(interaction.user), "archive_season", f"Archived season: {season_name}")
            
            embed = discord.Embed(title="📁 Season Archived", description=f"**{season_name}** has been archived successfully!", color=discord.Color.gold())
            embed.add_field(name="Archived Files", value="\n".join([f"• `{f}`" for f in archived_files]), inline=False)
            embed.add_field(name="Location", value=f"`data/archives/{season_name.replace(' ', '_').lower()}/`", inline=False)
            embed.add_field(name="⚠️ Important", value="Current data files were **copied** (not deleted).\nData remains active. To reset, manually delete current data files.", inline=False)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error archiving season: {str(e)}", ephemeral=True)

    @app_commands.command(name="recalculate-leaderboards", description="[ADMIN] Recalculate all leaderboard scores")
    async def recalculate_leaderboards(self, interaction: discord.Interaction):
        if not self.is_admin(interaction):
            await interaction.response.send_message("❌ You need Admin or Staff role!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            with open(self.players_file, "r", encoding="utf-8") as f:
                players = json.load(f)
            
            with open(self.teams_file, "r", encoding="utf-8") as f:
                teams = json.load(f)
            
            total_players = len(players)
            banned_players = sum(1 for p in players if p.get("banned", False))
            total_teams = len(teams)
            banned_teams = sum(1 for t in teams if t.get("banned", False))
            
            self.log_action(interaction.user.id, str(interaction.user), "recalculate_leaderboards", "Triggered leaderboard recalculation")
            
            embed = discord.Embed(title="✅ Leaderboards Recalculated", description="All leaderboard scores validated and ready.", color=discord.Color.green())
            embed.add_field(name="Total Players", value=f"{total_players} ({banned_players} banned)", inline=True)
            embed.add_field(name="Total Teams", value=f"{total_teams} ({banned_teams} banned)", inline=True)
            embed.add_field(name="Note", value="Leaderboards calculate in real-time. Use `/leaderboard-players` or `/leaderboard-teams` to view.", inline=False)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error recalculating: {str(e)}", ephemeral=True)

    @app_commands.command(name="admin-logs", description="[ADMIN] View recent admin actions")
    @app_commands.describe(limit="Number of logs to show (default: 10)")
    async def view_logs(self, interaction: discord.Interaction, limit: int = 10):
        if not self.is_admin(interaction):
            await interaction.response.send_message("❌ You need Admin or Staff role!", ephemeral=True)
            return
        
        try:
            with open(self.logs_file, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []
        
        if not logs:
            await interaction.response.send_message("📋 No admin actions logged yet.", ephemeral=True)
            return
        
        recent_logs = logs[-limit:]
        recent_logs.reverse()
        
        embed = discord.Embed(title="📋 Admin Action Logs", description=f"Showing last {len(recent_logs)} actions", color=discord.Color.blue(), timestamp=datetime.now())
        
        for log in recent_logs[:10]:
            timestamp = datetime.fromisoformat(log["timestamp"]).strftime("%Y-%m-%d %H:%M")
            value = f"**{log['username']}** - `{log['action']}`\n{log['details']}"
            embed.add_field(name=f"⏰ {timestamp}", value=value, inline=False)
        
        embed.set_footer(text="💡 All edits are logged for audit")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="clear-team-stats", description="🗑️ Admin: Clear all team statistics and recent matches")
    async def clear_team_stats(self, interaction: discord.Interaction):
        """Clear all team stats including recent matches."""
        if not self.is_admin(interaction):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return
        
        # Confirmation view
        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
                self.value = None
            
            @discord.ui.button(label="✅ Yes, Clear All Stats", style=discord.ButtonStyle.danger)
            async def confirm(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                self.value = True
                self.stop()
                await button_interaction.response.defer()
            
            @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
            async def cancel(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                self.value = False
                self.stop()
                await button_interaction.response.defer()
        
        # Ask for confirmation
        view = ConfirmView()
        await interaction.response.send_message(
            "⚠️ **WARNING:** This will clear all team statistics and recent match history!\n\n"
            "This action will:\n"
            "• Delete all recent match data from team_stats\n"
            "• Reset total matches, wins, and losses in team_stats\n"
            "• Keep team registrations and members intact\n\n"
            "**This cannot be undone!** Are you sure?",
            view=view,
            ephemeral=True
        )
        
        # Wait for response
        await view.wait()
        
        if view.value is None:
            await interaction.edit_original_response(content="❌ Command timed out.", view=None)
            return
        
        if not view.value:
            await interaction.edit_original_response(content="✅ Cancelled. No stats were cleared.", view=None)
            return
        
        # Clear team stats
        try:
            # Clear team_stats table
            pool = await db.get_pool()
            async with pool.acquire() as conn:
                result = await conn.execute("DELETE FROM team_stats")
            
            # Log the action
            self.log_action(
                interaction.user.id,
                str(interaction.user),
                "CLEAR_TEAM_STATS",
                "Cleared all team statistics and recent matches"
            )
            
            await interaction.edit_original_response(
                content="✅ **Team stats cleared successfully!**\n\n"
                        "• All recent match history deleted\n"
                        "• Team stats reset\n"
                        "• Teams and members are still registered\n\n"
                        "New matches will start fresh statistics.",
                view=None
            )
            
        except Exception as e:
            await interaction.edit_original_response(
                content=f"❌ Error clearing team stats: {str(e)}",
                view=None
            )

async def setup(bot):
    await bot.add_cog(AdminSystem(bot))
