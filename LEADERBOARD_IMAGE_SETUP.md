# Leaderboard Image Integration Guide

## Files Created:

### 1. `services/leaderboard_image_generator.py`
- Generates leaderboard images with team data on template backgrounds
- Uses Lato-Bold.ttf font
- Supports all 5 regions: global, apac, emea, americas, india
- Function: `generate_leaderboard_image(region, limit=10)`

### 2. `test_leaderboard_alignment.py`
- Test script to verify text alignment on images
- Generates test images with sample data and red alignment guides
- Edit TEST_CONFIG in the script to adjust positioning
- Run: `python test_leaderboard_alignment.py`
- Output: `test_alignment/test_apac_leaderboard.jpg`

## How to Use:

### Step 1: Test Alignment
```bash
python test_leaderboard_alignment.py
```
- Check the output in `test_alignment` folder
- Adjust values in TEST_CONFIG if needed
- Re-run until text is properly aligned

### Step 2: Update Image Generator
Once alignment looks good, copy the values from `test_leaderboard_alignment.py` TEST_CONFIG 
to `services/leaderboard_image_generator.py` LEADERBOARD_CONFIG for the specific region.

### Step 3: Integrate into /lb Command

Add this import at the top of `cogs/leaderboards.py`:
```python
from services.leaderboard_image_generator import generate_leaderboard_image
```

Replace the `/lb` command implementation (around line 747) with:
```python
async def leaderboard_regional(self, interaction: discord.Interaction, region: str = "global"):
    """Display regional team leaderboard with generated image"""
    await interaction.response.defer()
    
    try:
        # Get team leaderboard data
        lb_data = await db.get_team_leaderboard(region, limit=10)
        
        if not lb_data:
            await interaction.followup.send(
                f"📊 No teams found in the **{region.upper()}** leaderboard yet.\\n"
                "Teams will appear here after playing matches!"
            )
            return
        
        # Generate leaderboard image
        image_path = await generate_leaderboard_image(region, limit=10)
        
        # Send image
        file = discord.File(image_path, filename=f'{region}_leaderboard.jpg')
        
        embed = discord.Embed(
            title=f"🏆 {region.upper()} Team Leaderboard",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        # Add top team info
        top_team = lb_data[0]
        embed.add_field(
            name="👑 Top Team",
            value=f"**[{top_team['team_tag']}] {top_team['team_name']}**\\n"
                  f"Points: `{top_team['points']:.1f}` | W/L: `{top_team['wins']}-{top_team['losses']}`",
            inline=False
        )
        
        embed.set_image(url=f"attachment://{region}_leaderboard.jpg")
        embed.set_footer(text="💡 Use /lb <region> to view other regional leaderboards")
        
        await interaction.followup.send(embed=embed, file=file)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
```

## Configuration:

### Current Settings (test_leaderboard_alignment.py):
```python
TEST_CONFIG = {
    'region': 'apac',
    'template': APAC_Leaderboard.jpg,
    'title_pos': (640, 100),
    'title_size': 60,
    'header_y': 250,
    'header_size': 28,
    'rank_x': 120,
    'team_name_x': 240,
    'matches_x': 680,
    'wins_x': 800,
    'losses_x': 920,
    'points_x': 1100,
    'row_start_y': 320,
    'row_height': 65,
    'row_size': 32,
}
```

### To Adjust:
1. Modify values in `test_leaderboard_alignment.py`
2. Run script to see changes
3. Copy working values to `services/leaderboard_image_generator.py`
4. Repeat for each region template

## Notes:
- Image size: 4000x3200 pixels
- Font: Lato-Bold.ttf
- Text color: White (255, 255, 255)
- Header color: Light gray (220, 220, 220)
- Max teams per image: 10
- Red alignment guides help with positioning
