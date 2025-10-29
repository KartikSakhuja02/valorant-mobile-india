# Team Staff Management System

## Overview
Comprehensive team staff management system allowing captains to add/remove managers (2 slots) and coach (1 slot) to their teams.

## Database Changes

### Migration Script
**File:** `migrations/add_team_staff.py`
- Adds 3 new columns to `teams` table:
  - `manager_1_id` (BIGINT, references players)
  - `manager_2_id` (BIGINT, references players)
  - `coach_id` (BIGINT, references players)
- Creates indexes for faster lookups
- All columns are nullable and cascade to SET NULL on player deletion

### Run Migration
```bash
python migrations/add_team_staff.py
```

## Database Functions

### New Functions in `services/db.py`

1. **`add_team_manager(team_id, manager_id, slot)`**
   - Adds a manager to slot 1 or 2
   - Returns True if successful, False if slot is taken
   - Validates slot number (must be 1 or 2)

2. **`remove_team_manager(team_id, slot=None, manager_id=None)`**
   - Removes a manager by slot number OR by manager_id
   - Flexible removal by either identifier

3. **`add_team_coach(team_id, coach_id)`**
   - Adds a coach to the team
   - Returns True if successful, False if slot is taken
   - Only one coach allowed per team

4. **`remove_team_coach(team_id)`**
   - Removes the coach from the team

5. **`get_team_staff(team_id)`**
   - Returns all staff information including:
     - manager_1_id, manager_1_ign
     - manager_2_id, manager_2_ign
     - coach_id, coach_ign
   - Uses LEFT JOINs to get player IGNs

## Slash Commands

### New Cog: `cogs/team_staff.py`

#### `/add-manager <user>`
- **Permission:** Captain only
- **Description:** Add a manager to your team
- **Validation:**
  - User must be registered as player
  - User cannot be the captain
  - User cannot already be a manager
  - User cannot be the coach (no dual roles)
  - Both slots must not be full
- **Behavior:** Automatically assigns to first available slot (1 or 2)

#### `/remove-manager <user>`
- **Permission:** Captain only
- **Description:** Remove a manager from your team
- **Validation:**
  - User must be a current manager
- **Behavior:** Removes manager from whichever slot they occupy

#### `/add-coach <user>`
- **Permission:** Captain only
- **Description:** Add a coach to your team
- **Validation:**
  - User must be registered as player
  - User cannot be the captain
  - User cannot already be a manager (no dual roles)
  - Coach slot must be empty
- **Behavior:** Assigns user to the single coach slot

#### `/remove-coach`
- **Permission:** Captain only
- **Description:** Remove the coach from your team
- **Validation:**
  - Team must have a coach
- **Behavior:** Clears the coach slot

#### `/view-staff`
- **Permission:** Any team member
- **Description:** View your team's staff (managers and coach)
- **Display:**
  - Team name and tag
  - Captain
  - Manager 1 (with IGN or "Empty slot")
  - Manager 2 (with IGN or "Empty slot")
  - Coach (with IGN or "Empty slot")
  - Team logo as thumbnail

## Profile Integration

### Updated: `cogs/profiles.py`
- `/team-profile` command now displays staff section
- Shows managers and coach (if assigned)
- Staff section appears before roster
- Format:
  ```
  📋 Staff
  👔 Manager 1: @User
  👔 Manager 2: @User
  🎓 Coach: @User
  ```

## Role Restrictions

### Staff Roles Are Mutually Exclusive:
- ❌ Captain cannot be manager or coach
- ❌ Manager cannot be coach
- ❌ Coach cannot be manager
- ✅ Staff members CAN be players on the roster

### Slot Limits:
- **Managers:** Maximum 2
- **Coach:** Maximum 1
- **Captain:** Always 1 (existing system)

## Features

### Automatic Slot Assignment
- When adding a manager, system automatically finds first available slot
- No need to specify slot number manually
- Slots filled in order: Slot 1 → Slot 2

### Flexible Removal
- Remove by user mention (automatically finds which slot)
- Graceful handling of empty slots

### Staff Visibility
- All team members can view staff with `/view-staff`
- Staff shown in team profiles (`/team-profile`)
- Staff information included in team data queries

### Data Integrity
- Foreign key constraints ensure staff are registered players
- ON DELETE SET NULL prevents orphaned references
- Indexes for efficient staff lookups

## Testing Checklist

### Manager Management
- [ ] Add manager to empty team (should go to slot 1)
- [ ] Add second manager (should go to slot 2)
- [ ] Try to add third manager (should fail)
- [ ] Remove manager 1, add new manager (should fill slot 1)
- [ ] Remove manager by mention
- [ ] Try to add captain as manager (should fail)
- [ ] Try to add coach as manager (should fail)

### Coach Management
- [ ] Add coach to team
- [ ] Try to add second coach (should fail)
- [ ] Remove coach
- [ ] Try to add captain as coach (should fail)
- [ ] Try to add manager as coach (should fail)

### Profile Display
- [ ] View staff with empty slots
- [ ] View staff with all slots filled
- [ ] View team profile with staff
- [ ] Verify team logo appears in staff view

### Edge Cases
- [ ] Non-captain tries to add staff (should fail)
- [ ] Add unregistered user as staff (should fail)
- [ ] Remove non-existent manager (should fail)
- [ ] Remove coach when none exists (should fail)

## Usage Examples

### Add Staff
```
Captain: /add-manager @John
Bot: ✅ @John has been added as Manager 1 for Team Alpha!

Captain: /add-manager @Sarah
Bot: ✅ @Sarah has been added as Manager 2 for Team Alpha!

Captain: /add-coach @Mike
Bot: ✅ @Mike has been added as Coach for Team Alpha!
```

### View Staff
```
Player: /view-staff

Bot: [Embed]
📋 Team Alpha [TA] - Staff

👑 Captain
@CaptainName

👔 Managers
Manager 1: @John (JohnIGN)
Manager 2: @Sarah (SarahIGN)

🎓 Coach
@Mike (MikeIGN)
```

### Remove Staff
```
Captain: /remove-manager @John
Bot: ✅ @John has been removed as manager from Team Alpha.

Captain: /remove-coach
Bot: ✅ @Mike has been removed as coach from Team Alpha.
```

## Future Enhancements
- [ ] Manager permissions (e.g., invite players, manage scrims)
- [ ] Coach-specific commands (strategy notes, VOD reviews)
- [ ] Staff activity logs
- [ ] Multiple teams per person (as staff)
- [ ] Staff history tracking
- [ ] Role-based Discord role assignment

## Integration Points

### Commands That Display Staff:
1. `/team-profile [name]` - Shows staff section
2. `/view-staff` - Dedicated staff view
3. Team embeds in various contexts (can be extended)

### Database Queries:
- `get_team_by_id()` - Returns team with staff IDs
- `get_team_staff()` - Returns detailed staff info with IGNs
- Staff columns available in all team queries

## Notes
- Staff roles are organizational only (no special permissions yet)
- Staff members can still be regular players on roster
- Staff changes are instant (no approval needed)
- Only captain can manage staff
- Staff data is preserved in database even if player unregisters
