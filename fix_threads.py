"""Fix thread creation in all registration files"""
import re

files_to_fix = [
    'cogs/registration.py',
    'cogs/registration_helpdesk.py',
    'cogs/team_registration_ui.py',
    'cogs/team_registration_helpdesk.py',
    'cogs/admin_team_register.py'
]

pattern = r'auto_archive_duration=1440,`n\s+type=discord\.ChannelType\.public_thread,`n\s+invitable=True'
replacement = 'auto_archive_duration=1440'

for filepath in files_to_fix:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '`n' in content:
            original_count = content.count('`n')
            content = re.sub(pattern, replacement, content)
            new_count = content.count('`n')
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Fixed {filepath} - Removed {original_count - new_count} occurrences")
        else:
            print(f"⏭️  Skipped {filepath} - No `n found")
    except Exception as e:
        print(f"❌ Error fixing {filepath}: {e}")

print("\n✅ Thread fix complete!")
