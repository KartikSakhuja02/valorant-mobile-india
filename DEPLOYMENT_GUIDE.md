# Deployment Guide - VCT Veto System + Thread Fixes

## Summary of Changes

### 1. VCT-Style Map Veto System ✅
**Commit:** `3f70ef9` - "Implement VCT-style map veto system with ban/pick phases and coin toss"

**Changes:**
- Complete rewrite of map veto system in `cogs/scrim.py`
- Replaced simple ban counting with professional VCT-style ban/pick sequences
- Added coin toss for decider map side selection (replaces knife rounds)
- Supports BO1, BO3, and BO5 formats correctly

**New Features:**
- ✅ Ban Phase: Teams ban maps in turn
- ✅ Pick Phase: Teams pick maps AND choose starting side (Attack/Defense)
- ✅ Decider Map: Last map uses coin toss for side selection
- ✅ Beautiful embed summary showing all maps with sides
- ✅ Color-coded buttons (red=ban, green=pick)
- ✅ Team A/B designation based on coin toss

### 2. Fixed Read-Only Threads ✅
**Commit:** `c148456` - "Fix read-only threads - make registration threads public and writable"

**Changes:**
- `cogs/registration.py`: Changed private threads to public (users can now message)
- `cogs/registration_helpdesk.py`: Made help threads public and invitable
- `cogs/team_registration_ui.py`: Made team registration threads public

**Problem Solved:**
- Users can now send messages in registration threads
- Threads are no longer read-only
- Staff and users can communicate properly

---

## Deployment Commands (Run on Raspberry Pi)

```bash
# Navigate to bot directory
cd ~/valorant-mobile-india

# Pull latest changes
git pull origin main

# Restart the bot
sudo systemctl restart valorant-bot

# Check bot status
sudo systemctl status valorant-bot

# View logs (optional)
sudo journalctl -u valorant-bot -f
```

---

## Testing Checklist

### VCT Veto System Testing
- [ ] Test BO1 scrim match
  - [ ] Verify 6 bans happen
  - [ ] Verify decider map is selected
  - [ ] Verify coin toss works for decider
  - [ ] Verify final summary shows correctly

- [ ] Test BO3 scrim match
  - [ ] Verify 2 bans, 2 picks, 2 bans sequence
  - [ ] Verify side selection works for picked maps
  - [ ] Verify decider coin toss works
  - [ ] Verify final summary shows 3 maps with sides

- [ ] Test BO5 scrim match
  - [ ] Verify 2 bans, 4 picks sequence
  - [ ] Verify side selection for all 4 picked maps
  - [ ] Verify decider coin toss
  - [ ] Verify final summary shows 5 maps

### Thread Testing
- [ ] Test player screenshot registration
  - [ ] Verify thread is created
  - [ ] Verify user can send messages
  - [ ] Verify staff can reply
  - [ ] Verify registration completes

- [ ] Test player manual registration
  - [ ] Verify thread is created
  - [ ] Verify user can send messages
  - [ ] Verify conversation works
  - [ ] Verify registration completes

- [ ] Test registration helpdesk
  - [ ] Verify Help button creates thread
  - [ ] Verify user can communicate with staff
  - [ ] Verify thread is not read-only

- [ ] Test team registration
  - [ ] Verify thread is created
  - [ ] Verify captain can send messages
  - [ ] Verify team registration completes

---

## Files Changed

### Modified Files
1. `cogs/scrim.py` (361 insertions, 19 deletions)
   - Rewrote entire map veto system
   - Added 8 new functions for veto flow
   - Added 2 new View classes (MapVetoView, SideSelectionView)

2. `cogs/registration.py` (6 insertions, 4 deletions)
   - Fixed thread creation to be public

3. `cogs/registration_helpdesk.py` (14 insertions, 1 deletion)
   - Made threads public and invitable
   - Added unarchiving logic

4. `cogs/team_registration_ui.py` (12 insertions, 2 deletions)
   - Made threads public with unarchiving

### New Files
1. `VCT_VETO_SYSTEM.md`
   - Complete documentation of new veto system
   - Examples and usage guide

2. `fix_threads.py`
   - Utility script (can be deleted after deployment)

---

## Key Features

### VCT Veto System
- **Format-Aware**: Automatically uses correct veto sequence based on BO1/BO3/BO5
- **Professional Flow**: Matches real VCT tournament veto process
- **Side Selection**: Teams choose Attack/Defense for picked maps
- **Coin Toss**: Random side selection for decider map (fair)
- **Beautiful UI**: Color-coded buttons and detailed embed summaries

### Thread Fixes
- **Public Threads**: Users can now send messages freely
- **Auto-Unarchive**: Threads won't auto-archive during use
- **Invitable**: Staff can be added properly
- **No Read-Only**: All participants can communicate

---

## Rollback (If Needed)

If something goes wrong, rollback to previous commit:

```bash
cd ~/valorant-mobile-india
git reset --hard 42f835e  # Last known good commit
sudo systemctl restart valorant-bot
```

---

## Support

If you encounter any issues:

1. Check bot logs: `sudo journalctl -u valorant-bot -n 100`
2. Verify database connection: `psql -U valm_user -d valm -c "SELECT COUNT(*) FROM players;"`
3. Check Python errors in logs
4. Test with a single scrim match first

---

## Notes

- **VCT Veto System** replaces old ban counting system completely
- **Coin toss** is purely random (50/50) for fairness
- **All veto messages** are sent via DM (private)
- **Final summary** is posted in LFS channel + sent to both captains
- **Thread fixes** apply to all registration methods
- **No breaking changes** - all existing data remains intact

---

## What's Next?

After successful deployment:
1. Monitor first few scrim matches closely
2. Gather feedback from users
3. Verify veto flow works smoothly
4. Check thread communication is working
5. Celebrate the upgrade! 🎉
