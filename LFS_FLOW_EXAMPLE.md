# LFS System - Complete Flow Example

## Scenario: Zero Remorse, Vega, and Sentinel Looking for Scrims

### Initial State: All 3 Teams Post LFS

#### **Step 1: You (Zero Remorse Captain) post LFS**
```
LFS BO3
7PM IST, APAC
```
- ✅ Message instantly deleted from channel
- ✅ Request stored in database (status: `pending`)
- 📩 **You receive DM:** "No other requests yet"

---

#### **Step 2: 4Space (Vega Captain) posts LFS**
```
LFS BO3  
8PM IST, APAC
```
- ✅ Message instantly deleted from channel
- ✅ Request stored in database (status: `pending`)
- 📩 **4Space receives DM:** Shows Zero Remorse's request with buttons
- 📩 **You receive DM:** Shows Vega's new request with buttons

**Your DM now shows:**
```
🆕 New Scrim Request Available!

Team: Vega [VG]
Match Type: BO3
Time Slot: 8PM IST
Region: APAC

[✅ Accept Scrim] [🔔 Notify Me]
```

---

#### **Step 3: Ayas (Sentinel Captain) posts LFS**
```
LFS BO5
9PM IST, APAC
```
- ✅ Message instantly deleted from channel
- ✅ Request stored in database (status: `pending`)
- 📩 **Ayas receives DM:** Shows BOTH Zero Remorse + Vega requests
- 📩 **You receive DM:** Shows Sentinel's new request
- 📩 **4Space receives DM:** Shows Sentinel's new request

**Everyone now has access to all 3 requests**

---

### You Click Accept on Vega's Request

#### **Step 4: You click "✅ Accept Scrim" on Vega's request**

**System Actions:**
1. ✅ Checks if Vega's request is still `pending` → YES
2. ✅ Updates Zero Remorse request: `status = 'in_progress'`
3. ✅ Updates Vega request: `status = 'in_progress'`
4. ✅ Creates scrim match in database
5. 📩 Sends approval buttons to both you and 4Space

**You receive:**
```
🤝 SCRIM MATCH FOUND!

Opponent Team: Vega [VG]
Opponent Captain: 4Space

Their Request: BO3, 8PM IST
Your Request: BO3, 7PM IST

Please approve or decline this scrim match.

[✅ Approve] [❌ Decline]
```

**4Space receives the same with your team info**

**Ayas's View Updates:**
- Sentinel still has `status = 'pending'` (available)
- But Zero Remorse and Vega both show `status = 'in_progress'`

---

### Ayas Tries to Accept Zero Remorse or Vega

#### **Step 5: Ayas clicks "✅ Accept Scrim" on Zero Remorse's request**

**System Checks:**
1. ❌ Checks Zero Remorse request status → `in_progress` (not `pending`)
2. 🔍 Finds who Zero Remorse is scheduling with → Vega

**Ayas receives message:**
```
⚠️ Zero Remorse [ZR] is currently scheduling a scrim with Vega [VG].

Click the 🔔 Notify Me button to get notified if their match doesn't get scheduled!
```

**Accept button does NOT create a match**

---

#### **Step 6: Ayas clicks "🔔 Notify Me"**

**System Actions:**
1. ✅ Adds Ayas to waitlist for Zero Remorse's request
2. ✅ Ayas receives confirmation

**Ayas receives:**
```
🔔 You'll be notified if this scrim becomes available!
```

**If Ayas also clicks Notify on Vega's request:**
- ✅ Added to waitlist for Vega's request too
- Can be notified about either team

---

### Two Possible Outcomes

## Outcome A: Match Gets Scheduled ✅

#### **Step 7A: Both You and 4Space click "✅ Approve"**

**System Actions:**
1. ✅ Updates match status: `chat_active`
2. ✅ Updates both requests: `status = 'matched'`
3. ✅ Activates chat relay between you and 4Space
4. ❌ **Ayas does NOT get notified** (match was successful)

**Ayas's situation:**
- Sentinel request still `pending`
- Can continue accepting other requests
- Zero Remorse and Vega are permanently matched
- Waitlist entries removed (match successful)

---

## Outcome B: Match Does NOT Get Scheduled ❌

#### **Step 7B: You OR 4Space clicks "❌ Decline"**

**System Actions:**
1. ✅ Updates Zero Remorse request: `status = 'pending'` (available again!)
2. ✅ Updates Vega request: `status = 'pending'` (available again!)
3. ✅ Deletes the scrim match
4. ✅ **Notifies Ayas (and anyone else on waitlist)**

**Ayas receives:**
```
✅ Scrim Available Again!

Zero Remorse [ZR] vs Vega [VG] match was not scheduled.
Zero Remorse [ZR] is looking for scrims again!

Team: Zero Remorse [ZR]
Match Type: BO3
Time Slot: 7PM IST
Region: APAC

[✅ Accept Scrim] [🔔 Notify Me]
```

**AND if Ayas was on Vega's waitlist too:**
```
✅ Scrim Available Again!

Zero Remorse [ZR] vs Vega [VG] match was not scheduled.
Vega [VG] is looking for scrims again!

Team: Vega [VG]
Match Type: BO3
Time Slot: 8PM IST
Region: APAC

[✅ Accept Scrim] [🔔 Notify Me]
```

**Now Ayas can:**
- Click Accept on either Zero Remorse or Vega
- Both are back to `pending` status
- Full cycle starts again!

---

### You or 4Space receive:
```
❌ Scrim Match Declined

The scrim match with [Opponent] was declined.
Your scrim request is still active. You can continue looking for other teams!
```

- Your request goes back to `pending`
- You can accept Sentinel or any other pending request
- You stay in the LFS pool

---

## Summary of States

### Request Status Flow:
```
pending → in_progress → matched ✅
   ↑           ↓
   └─────── declined ❌
```

### What Captains See:

**Status: `pending`**
- ✅ Accept button enabled
- 🔔 Notify button enabled
- Shows normally

**Status: `in_progress`**
- ❌ Accept button disabled (shows warning)
- ✅ Notify button enabled
- Shows "⚠️ This team is currently scheduling"

**Status: `matched`**
- Request disappears (successful match)
- No longer shown to anyone

**Status: `pending` (after decline)**
- ✅ Both buttons enabled again
- Waitlisted captains get notified
- Fresh chance to accept

---

## Key Features

✅ **Team Membership Required** - Must be in a team to post LFS  
✅ **Instant Message Purge** - Channel stays clean  
✅ **See All Requests** - Complete visibility of all teams  
✅ **Smart Status Updates** - Real-time "in_progress" notifications  
✅ **Waitlist System** - Never miss when a team becomes available  
✅ **Second Chances** - Declined matches return to pending, not cancelled  

This creates a **fair, transparent, and flexible** scrim matching system! 🎮
