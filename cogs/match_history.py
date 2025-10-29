import discord
from discord.ext import commands
from discord import app_commands
from services import db

class MatchHistory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="matches",
        description="View recent matches (all players or specific player)"
    )
    @app_commands.describe(
        player="Optional: View matches for a specific player (mention them)",
        limit="Optional: Number of matches to show (default: 5)"
    )
    async def matches(
        self, 
        interaction: discord.Interaction, 
        player: discord.Member = None,
        limit: int = 5
    ):
        await interaction.response.defer()

        try:
            if limit > 10:  # Cap at 10 for readability
                limit = 10

            if player:
                # Get matches for specific player
                matches = await db.get_player_match_history(player.id, limit)
                title = f"Match History for {player.display_name}"
            else:
                # Get recent matches across all players
                matches = await db.get_recent_matches(limit)
                title = "Recent Matches"

            if not matches:
                await interaction.followup.send("No matches found!")
                return

            # Format each match into an embed
            embeds = []
            for match in matches:
                # Sort players by team
                team1 = []
                team2 = []
                for p in match['players']:
                    if p['team'] == 1:
                        team1.append(p)
                    else:
                        team2.append(p)

                # Sort teams by score
                team1.sort(key=lambda p: p['score'], reverse=True)
                team2.sort(key=lambda p: p['score'], reverse=True)

                # Create embed
                embed = discord.Embed(
                    title=f"Match on {match['map_name']}",
                    description=f"**Score:** {match['team1_score']} - {match['team2_score']}",
                    timestamp=match['created_at'],
                    color=discord.Color.blue()
                )

                # Add team sections
                team1_text = []
                for p in team1:
                    mvp_star = "⭐" if p['mvp'] else ""
                    team1_text.append(
                        f"{mvp_star}`{p['agent']:<10}` {p['ign']:<20} {p['kills']}/{p['deaths']}/{p['assists']}"
                    )

                team2_text = []
                for p in team2:
                    mvp_star = "⭐" if p['mvp'] else ""
                    team2_text.append(
                        f"{mvp_star}`{p['agent']:<10}` {p['ign']:<20} {p['kills']}/{p['deaths']}/{p['assists']}"
                    )

                if team1_text:
                    embed.add_field(
                        name=f"🔵 Team 1 ({match['team1_score']})",
                        value="```\n" + "\n".join(team1_text) + "\n```",
                        inline=False
                    )
                if team2_text:
                    embed.add_field(
                        name=f"🔴 Team 2 ({match['team2_score']})",
                        value="```\n" + "\n".join(team2_text) + "\n```",
                        inline=False
                    )

                embeds.append(embed)

            # Send embeds (paginated if needed)
            if len(embeds) == 1:
                await interaction.followup.send(embed=embeds[0])
            else:
                # Add page numbers to embeds
                for i, embed in enumerate(embeds):
                    embed.set_footer(text=f"Match {i+1} of {len(embeds)}")
                
                # Send first embed with navigation buttons
                current_page = 0
                message = await interaction.followup.send(embed=embeds[current_page])

        except Exception as e:
            await interaction.followup.send(f"Error retrieving matches: {str(e)}")

async def setup(bot):
    await bot.add_cog(MatchHistory(bot))