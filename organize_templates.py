"""
📁 Template Organizer
Moves downloaded agent templates from Downloads folder to data/agent_templates/

Usage:
    python organize_templates.py
"""

import shutil
from pathlib import Path
import os

def organize_templates():
    # Common download locations
    downloads_paths = [
        Path.home() / "Downloads",
        Path.home() / "Desktop",
        Path(".")  # Current directory
    ]
    
    templates_dir = Path("data/agent_templates")
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # All agent names
    agents = [
        'astra', 'breach', 'brimstone', 'chamber', 'clove',
        'cypher', 'deadlock', 'fade', 'gekko', 'harbor',
        'iso', 'jett', 'kayo', 'killjoy', 'neon',
        'omen', 'phoenix', 'raze', 'reyna', 'sage',
        'skye', 'sova', 'viper', 'vyse', 'yoru'
    ]
    
    moved_count = 0
    
    print("\n" + "="*70)
    print("📁 TEMPLATE ORGANIZER")
    print("="*70)
    
    # Search for agent templates
    for downloads in downloads_paths:
        if not downloads.exists():
            continue
        
        print(f"\n🔍 Searching in: {downloads}")
        
        for agent in agents:
            template_file = downloads / f"{agent}.png"
            
            if template_file.exists():
                destination = templates_dir / f"{agent}.png"
                
                # Copy file
                shutil.copy2(template_file, destination)
                print(f"   ✅ Copied {agent}.png")
                moved_count += 1
                
                # Optionally delete from Downloads
                try:
                    template_file.unlink()
                    print(f"      🗑️  Removed from Downloads")
                except:
                    pass
    
    print("\n" + "="*70)
    print(f"📊 SUMMARY")
    print("="*70)
    print(f"✅ Moved {moved_count} templates")
    
    # Check what we have
    existing = list(templates_dir.glob("*.png"))
    print(f"📁 Total templates in data/agent_templates/: {len(existing)}")
    
    if existing:
        print("\n✅ Templates found:")
        for template in sorted(existing):
            print(f"   - {template.name}")
    
    # Check missing
    existing_names = {f.stem.lower() for f in existing}
    missing = [a for a in agents if a not in existing_names]
    
    if missing:
        print(f"\n❌ Still missing ({len(missing)}):")
        for agent in missing:
            print(f"   - {agent}")
    else:
        print("\n🎉 ALL 25 AGENTS COMPLETE!")
        print("   Ready to use template matching!")

if __name__ == "__main__":
    try:
        organize_templates()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
