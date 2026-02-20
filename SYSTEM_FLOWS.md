# 🔄 Complete System Flows - Explainable AI Smart Helpdesk

This document provides **comprehensive flow diagrams** for all scenarios in the system, including category classification, duplicate detection, auto-reply, priority assignment, and routing.

---

## 📊 Table of Contents

1. [High-Level System Overview](#high-level-system-overview)
2. [Flow 1: New Ticket (No Duplicates)](#flow-1-new-ticket-no-duplicates)
3. [Flow 2: High Similarity - Auto-Reply Enabled (≥60%)](#flow-2-high-similarity-auto-reply-enabled-60)
4. [Flow 3: Duplicate Detection (≥80%)](#flow-3-duplicate-detection-80)
5. [Flow 4: Security Escalation](#flow-4-security-escalation)
6. [Flow 5: First-Ever Ticket (Empty Database)](#flow-5-first-ever-ticket-empty-database)
7. [Flow 6: Model Failure - Fallback Mode](#flow-6-model-failure-fallback-mode)
8. [Flow 7: Ambiguous Category Classification](#flow-7-ambiguous-category-classification)
9. [Flow 8: Complete End-to-End Pipeline](#flow-8-complete-end-to-end-pipeline)

---

## 🌐 High-Level System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER SUBMITS TICKET                      │
│  Subject + Description + Context (Hardware/Software/Network...)  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 STEP 1: MODEL 2 - CATEGORY CLASSIFICATION        │
│  • Zero-shot semantic similarity                                │
│  • Compares ticket to 11 category descriptions                  │
│  • Outputs: Category + Confidence Score                         │
│  • User category selection IGNORED                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│           STEP 2: MODEL 1 - DUPLICATE DETECTION                  │
│  • Category-weighted similarity matching                        │
│  • Same category = 1.0x weight, Different = 0.6x                │
│  • Outputs: Similar tickets + Weighted scores                   │
│  • Decision: Is Duplicate? (≥80%), Auto-Reply? (≥60%)          │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
                     ┌────────┴────────┐
                     │                 │
                     ▼                 ▼
        ┌────────────────┐    ┌──────────────────┐
        │ Similarity ≥60%│    │ Similarity <60%  │
        │ AUTO-REPLY ON  │    │ AUTO-REPLY OFF   │
        └────────┬───────┘    └────────┬─────────┘
                 │                     │
                 └──────────┬──────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│             STEP 3: MODEL 3 - PRIORITY PREDICTION                │
│  • Keyword analysis (production, critical, blocked, etc.)       │
│  • Category risk assessment                                     │
│  • Priority inheritance (if duplicate)                          │
│  • Outputs: Priority (Low/Medium/High/Critical) + Confidence    │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  STEP 4: ROUTING DECISION                        │
│  • Rule-based team assignment (based on category)               │
│  • Security escalation (if keywords detected)                   │
│  • SLA calculation (based on priority)                          │
│  • Outputs: Assigned Team + Expected Response Time              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       RESULTS DISPLAY                            │
│  • Browser: Formatted analysis results                          │
│  • Terminal: Complete step-by-step reasoning                    │
│  • Auto-Reply: Suggested solution (if similarity ≥60%)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📌 Flow 1: New Ticket (No Duplicates)

**Scenario:** User submits a ticket about a new problem not seen before

```
USER INPUT
├─ Subject: "Excel macros not working after Windows update"
├─ Description: "All Excel macros stopped working after last week's update..."
└─ Context: Software / Application

                    ↓

┌───────────────────────────────────────────────────────────┐
│ MODEL 2: CATEGORY CLASSIFICATION                          │
├───────────────────────────────────────────────────────────┤
│ Input: Subject + Description                              │
│ Process:                                                   │
│   1. Encode ticket text → 384-dim vector                  │
│   2. Compare to 11 category descriptions                  │
│   3. Calculate cosine similarity                          │
│ Output:                                                    │
│   ✓ Predicted Category: Software (0.89 confidence)        │
│   ✓ Alternative: Hardware (0.12 confidence)               │
│   ✓ Method: Zero-shot semantic similarity                 │
└───────────────────────────────────────────────────────────┘

                    ↓

┌───────────────────────────────────────────────────────────┐
│ MODEL 1: DUPLICATE DETECTION                              │
├───────────────────────────────────────────────────────────┤
│ Input: Ticket embedding + Predicted Category (Software)   │
│ Process:                                                   │
│   1. Compare to 30 historical tickets                     │
│   2. Apply category weighting:                            │
│      • Software tickets: 1.0x weight                      │
│      • Other categories: 0.6x weight                      │
│   3. Sort by weighted similarity                          │
│ Output:                                                    │
│   ✓ Highest Similarity: 45% (Ticket #ACME-012)            │
│   ✓ Is Duplicate? NO (below 80% threshold)                │
│   ✓ Auto-Reply? NO (below 60% threshold)                  │
│   ✓ Status: NEW TICKET - Manual review required           │
└───────────────────────────────────────────────────────────┘

                    ↓

┌───────────────────────────────────────────────────────────┐
│ MODEL 3: PRIORITY PREDICTION                              │
├───────────────────────────────────────────────────────────┤
│ Input: Subject + Description + Category                   │
│ Process:                                                   │
│   1. Scan for impact keywords:                            │
│      • Critical: "production down", "security breach"     │
│      • High: "blocked", "cannot work", "urgent"           │
│      • Medium: "slow", "intermittent", "sometimes"        │
│      • Low: "question", "how to", "enhancement"           │
│   2. Apply category risk:                                 │
│      • Security/DevOps → Risk: High                       │
│      • Software/Network → Risk: Medium                    │
│      • Hardware/Facilities → Risk: Low                    │
│   3. Combine keyword + category                           │
│ Output:                                                    │
│   ✓ Keywords Found: "not working", "stopped" → Medium     │
│   ✓ Category Risk: Software → Medium                      │
│   ✓ Final Priority: MEDIUM (65% confidence)               │
└───────────────────────────────────────────────────────────┘

                    ↓

┌───────────────────────────────────────────────────────────┐
│ ROUTING DECISION                                           │
├───────────────────────────────────────────────────────────┤
│ Category: Software                                         │
│ Assigned Team: Application Support Team                   │
│ Expected Response: 4 hours (Medium priority)              │
│ Auto-Reply: ❌ Not available (similarity too low)          │
└───────────────────────────────────────────────────────────┘

OUTCOME:
✓ Ticket created as NEW
✓ Routed to Application Support Team
✓ Priority: MEDIUM
✓ SLA: 4 hours
✓ Manual review required (no auto-reply)
```

---

## 🤖 Flow 2: High Similarity - Auto-Reply Enabled (≥60%)

**Scenario:** User submits a ticket very similar to a previously resolved issue

```
USER INPUT
├─ Subject: "VPN disconnects every 30 minutes"
├─ Description: "Corporate VPN keeps disconnecting every half hour..."
└─ Context: Network / VPN

                    ↓

┌───────────────────────────────────────────────────────────┐
│ MODEL 2: CATEGORY CLASSIFICATION                          │
├───────────────────────────────────────────────────────────┤
│ Output:                                                    │
│   ✓ Predicted Category: Network (0.92 confidence)         │
│   ✓ User said: Network / VPN ✓ (Matches AI prediction)    │
└───────────────────────────────────────────────────────────┘

                    ↓

┌───────────────────────────────────────────────────────────┐
│ MODEL 1: DUPLICATE DETECTION                              │
├───────────────────────────────────────────────────────────┤
│ Process:                                                   │
│   1. Compare to historical tickets                        │
│   2. Found: Ticket #ACME-004 (VPN disconnects issue)      │
│   3. Raw Similarity: 88%                                  │
│   4. Category Match: YES (both Network)                   │
│   5. Weighted Score: 88% × 1.0 = 88%                      │
│ Output:                                                    │
│   ✓ Highest Similarity: 88%                               │
│   ✓ Is Duplicate? YES (≥80% threshold) ✓                  │
│   ✓ Auto-Reply? YES (≥60% threshold) ✓✓                   │
└───────────────────────────────────────────────────────────┘

                    ↓

┌───────────────────────────────────────────────────────────┐
│ 🤖 AUTO-REPLY GENERATOR                                    │
├───────────────────────────────────────────────────────────┤
│ Similarity: 88% (HIGH CONFIDENCE)                          │
│ Source Ticket: #ACME-004                                   │
│                                                            │
│ Generated Auto-Reply:                                      │
│ ┌────────────────────────────────────────────────────────┐│
│ │ 🎯 Suggested Solution:                                 ││
│ │ Based on similar ticket 'VPN disconnects every 30     ││
│ │ minutes' (Category: Network, Priority: High), this     ││
│ │ issue typically requires Network Operations Team       ││
│ │ attention. The AI recommends routing this to the       ││
│ │ same team that handled the similar case.               ││
│ │                                                        ││
│ │ 📋 Recommended Next Steps:                             ││
│ │ ✓ Review similar ticket #ACME-004 for resolution      ││
│ │ ✓ Expected priority: High                             ││
│ │ ✓ Typical handling team: Network Operations Team      ││
│ └────────────────────────────────────────────────────────┘│
└───────────────────────────────────────────────────────────┘

                    ↓

┌───────────────────────────────────────────────────────────┐
│ MODEL 3: PRIORITY PREDICTION                              │
├───────────────────────────────────────────────────────────┤
│ Process:                                                   │
│   • Detected as DUPLICATE                                 │
│   • Inherit priority from original ticket #ACME-004       │
│ Output:                                                    │
│   ✓ Priority: HIGH (inherited from duplicate)             │
│   ✓ Confidence: 100% (priority inheritance)               │
└───────────────────────────────────────────────────────────┘

                    ↓

┌───────────────────────────────────────────────────────────┐
│ ROUTING DECISION                                           │
├───────────────────────────────────────────────────────────┤
│ Category: Network                                          │
│ Assigned Team: Network Operations Team                    │
│ Expected Response: 1 hour (High priority)                 │
│ Auto-Reply: ✅ ENABLED                                     │
└───────────────────────────────────────────────────────────┘

OUTCOME:
✓ Ticket flagged as DUPLICATE
✓ Auto-Reply message generated (88% similarity)
✓ User sees suggested solution immediately
✓ Routed to Network Operations Team
✓ Priority: HIGH (inherited)
✓ SLA: 1 hour
✓ Support team can review similar ticket #ACME-004 for faster resolution
```

---

## 🔁 Flow 3: Duplicate Detection (≥80%)

**Scenario:** User submits exact duplicate of existing ticket

```
USER INPUT
├─ Subject: "Cannot access GitHub Enterprise"
├─ Description: "Need access to GitHub repos..."
└─ Context: Software / Access

                    ↓

┌───────────────────────────────────────────────────────────┐
│ MODEL 2: CATEGORY CLASSIFICATION                          │
│ Output: Software Access (0.85 confidence)                 │
└───────────────────────────────────────────────────────────┘

                    ↓

┌───────────────────────────────────────────────────────────┐
│ MODEL 1: DUPLICATE DETECTION                              │
├───────────────────────────────────────────────────────────┤
│ Found: Ticket #ACME-001 "Need GitHub Enterprise access"   │
│ Raw Similarity: 95%                                       │
│ Category Match: YES                                        │
│ Weighted Score: 95% × 1.0 = 95%                           │
│                                                            │
│ Decision Tree:                                             │
│   IF weighted_similarity ≥ 80% THEN                       │
│     is_duplicate = TRUE                                    │
│     IF weighted_similarity ≥ 60% THEN                     │
│       auto_reply_enabled = TRUE                           │
│                                                            │
│ Output:                                                    │
│   ✓ Is Duplicate? YES (95% ≥ 80%) ✓                       │
│   ✓ Auto-Reply? YES (95% ≥ 60%) ✓                         │
│   ✓ Confidence: HIGH                                       │
└───────────────────────────────────────────────────────────┘

                    ↓

┌───────────────────────────────────────────────────────────┐
│ 🤖 AUTO-REPLY (HIGH CONFIDENCE)                            │
│ Similarity: 95% - Nearly identical to Ticket #ACME-001    │
│ Suggested: Link user to original ticket resolution        │
└───────────────────────────────────────────────────────────┘

                    ↓

┌───────────────────────────────────────────────────────────┐
│ MODEL 3: PRIORITY PREDICTION                              │
│ Action: Inherit priority from #ACME-001                   │
│ Output: Priority: HIGH (inherited, 100% confidence)       │
└───────────────────────────────────────────────────────────┘

                    ↓

┌───────────────────────────────────────────────────────────┐
│ ROUTING DECISION                                           │
│ Team: Identity & Access Management Team                   │
│ SLA: 1 hour (High priority)                               │
│ Special Handling: Duplicate - May auto-close or merge     │
└───────────────────────────────────────────────────────────┘

OUTCOME:
✓ Duplicate detected (95% similarity)
✓ User notified of existing ticket
✓ Auto-reply with solution
✓ Priority inherited
✓ May be auto-merged or closed as duplicate
```

---

## 🔐 Flow 4: Security Escalation

**Scenario:** User reports potential security incident

```
USER INPUT
├─ Subject: "Suspicious email asking for password"
├─ Description: "Received email claiming to be from IT asking to 
│   click link and enter credentials. Link is http://compamy-login.tk.
│   I did not click. Is this phishing?"
└─ Context: Software / Email

                    ↓

┌───────────────────────────────────────────────────────────┐
│ MODEL 2: CATEGORY CLASSIFICATION                          │
├───────────────────────────────────────────────────────────┤
│ Process:                                                   │
│   1. Standard category classification                     │
│   2. 🚨 SECURITY KEYWORD DETECTION TRIGGER 🚨              │
│                                                            │
│ Security Keywords Detected:                                │
│   ✓ "phishing" → Security threat                          │
│   ✓ "suspicious" → Security indicator                     │
│   ✓ "credentials" → Sensitive data                        │
│   ✓ "click link" → Phishing pattern                       │
│                                                            │
│ 🔒 SECURITY OVERRIDE ACTIVATED                             │
│                                                            │
│ Output:                                                    │
│   ✓ Original Category: Software (0.78 confidence)         │
│   ✓ OVERRIDDEN TO: Security (1.00 confidence)             │
│   ✓ Reason: Security keywords detected                    │
└───────────────────────────────────────────────────────────┘

                    ↓

┌───────────────────────────────────────────────────────────┐
│ MODEL 1: DUPLICATE DETECTION                              │
│ (Bypassed for security tickets - every incident unique)   │
│ Output: Auto-Reply DISABLED for security tickets          │
└───────────────────────────────────────────────────────────┘

                    ↓

┌───────────────────────────────────────────────────────────┐
│ MODEL 3: PRIORITY PREDICTION                              │
├───────────────────────────────────────────────────────────┤
│ 🚨 SECURITY ESCALATION PROTOCOL                            │
│                                                            │
│ Process:                                                   │
│   IF category == "Security" THEN                          │
│     priority = CRITICAL                                    │
│     confidence = 1.00                                      │
│     bypass_normal_priority_logic()                        │
│                                                            │
│ Output:                                                    │
│   ✓ Priority: CRITICAL (auto-escalated)                   │
│   ✓ Confidence: 100%                                       │
│   ✓ Reason: Security incident requires immediate action   │
└───────────────────────────────────────────────────────────┘

                    ↓

┌───────────────────────────────────────────────────────────┐
│ 🚨 ROUTING DECISION (SECURITY ESCALATION)                  │
├───────────────────────────────────────────────────────────┤
│ Category: Security (OVERRIDE)                              │
│ Assigned Team: Security Operations Center (SOC)           │
│ Expected Response: 15 minutes (CRITICAL priority)         │
│ Auto-Reply: ❌ DISABLED (Security tickets need review)     │
│                                                            │
│ Special Handling:                                          │
│   • Immediate notification to SOC                         │
│   • Email alert to security team                          │
│   • No auto-close or auto-reply                           │
│   • Incident tracking enabled                             │
└───────────────────────────────────────────────────────────┘

OUTCOME:
✓ Security keywords triggered override
✓ Category changed from Software → Security
✓ Priority auto-escalated to CRITICAL
✓ Routed to SOC with 15-minute SLA
✓ Auto-reply disabled (manual review required)
✓ Immediate notification sent
✓ Every security report treated as unique incident
```

---

## 🆕 Flow 5: First-Ever Ticket (Empty Database)

**Scenario:** Brand new company, zero historical tickets

```
USER INPUT
├─ Subject: "Laptop overheating during video calls"
├─ Description: "My work laptop gets very hot..."
└─ Context: Hardware / Device

                    ↓

┌───────────────────────────────────────────────────────────┐
│ MODEL 2: CATEGORY CLASSIFICATION                          │
├───────────────────────────────────────────────────────────┤
│ Process:                                                   │
│   • ZERO-SHOT LEARNING (no training data needed)          │
│   • Compare ticket to pre-defined category descriptions   │
│   • Uses semantic similarity only                         │
│ Output:                                                    │
│   ✓ Predicted Category: Hardware (0.91 confidence)        │
│   ✓ Works perfectly with 0 historical tickets ✓           │
└───────────────────────────────────────────────────────────┘

                    ↓

┌───────────────────────────────────────────────────────────┐
│ MODEL 1: DUPLICATE DETECTION                              │
├───────────────────────────────────────────────────────────┤
│ Process:                                                   │
│   1. Check historical ticket count                        │
│   2. IF tickets.length == 0 THEN                          │
│        ACTIVATE ZERO-SHOT MODE                            │
│                                                            │
│ ⚠️  ZERO-SHOT MODE ACTIVATED                               │
│                                                            │
│ Output:                                                    │
│   ✓ Historical Tickets: 0                                 │
│   ✓ Duplicate Detection: SKIPPED (no data)                │
│   ✓ Auto-Reply: DISABLED (no similar tickets)             │
│   ✓ Status: NEW TICKET (first in database)                │
│   ✓ Message: "This is normal for the first ticket"        │
└───────────────────────────────────────────────────────────┘

                    ↓

┌───────────────────────────────────────────────────────────┐
│ MODEL 3: PRIORITY PREDICTION                              │
├───────────────────────────────────────────────────────────┤
│ Process:                                                   │
│   • NO priority inheritance (no duplicates)               │
│   • Use RULE-BASED priority assignment                    │
│   • Scan for keywords: "hot", "overheating"               │
│   • Category Hardware → Medium risk                       │
│ Output:                                                    │
│   ✓ Keywords: "overheating", "hot" → Medium               │
│   ✓ Category Risk: Hardware → Medium                      │
│   ✓ Final Priority: MEDIUM (65% confidence)               │
└───────────────────────────────────────────────────────────┘

                    ↓

┌───────────────────────────────────────────────────────────┐
│ ROUTING DECISION                                           │
│ Team: Desktop Support Team                                │
│ SLA: 4 hours (Medium priority)                            │
│ Special Note: First ticket in system - baseline created   │
└───────────────────────────────────────────────────────────┘

OUTCOME:
✓ System works perfectly with 0 historical tickets
✓ Zero-shot classification successful
✓ Duplicate detection gracefully skipped
✓ Rule-based priority assignment used
✓ Ticket becomes baseline for future similarity matching
✓ No crash, no error - production ready from day 1
```

---

## 🛟 Flow 6: Model Failure - Fallback Mode

**Scenario:** AI models fail to load (network issue, corrupted files, etc.)

```
SYSTEM STARTUP
│
├─ Attempting to load Model 2...
│   └─ ❌ ERROR: Failed to load sentence-transformers model
│
├─ Attempting to load Model 1...
│   └─ ❌ ERROR: Embeddings file not found
│
├─ Attempting to load Model 3...
│   └─ ✓ Loaded successfully
│
└─ RESULT: AI system partially unavailable

                    ↓

┌───────────────────────────────────────────────────────────┐
│ FALLBACK MODE ACTIVATION                                   │
├───────────────────────────────────────────────────────────┤
│ Triggered by: try-catch block in app.py initialization    │
│                                                            │
│ Code:                                                      │
│   ai_enabled = False                                       │
│   try:                                                     │
│       classifier = TicketCategoryClassifier()              │
│       similarity_matcher = ...                            │
│       priority_engine = ...                               │
│       ai_enabled = True                                    │
│   except Exception as e:                                   │
│       print("[ERROR] AI models failed to load")           │
│       print("[FALLBACK] Using rule-based routing")        │
│       ai_enabled = False  # Graceful degradation          │
│                                                            │
│ Status: ai_enabled = False                                 │
└───────────────────────────────────────────────────────────┘

                    ↓

USER SUBMITS TICKET
│
├─ POST /submit-ticket
│
└─ Check: if not ai_enabled:

                    ↓

┌───────────────────────────────────────────────────────────┐
│ FALLBACK ROUTING                                           │
├───────────────────────────────────────────────────────────┤
│ AI Models: UNAVAILABLE                                     │
│ Fallback Method: User-selected context                    │
│                                                            │
│ Process:                                                   │
│   1. Use user-selected context (Software/Hardware/Network)│
│   2. Apply rule-based category mapping                    │
│   3. Assign default priority: Medium                      │
│   4. Route based on context                               │
│                                                            │
│ Example:                                                   │
│   User Context: "Software / Application"                  │
│   → Category: Software                                     │
│   → Team: Application Support Team                        │
│   → Priority: Medium (default)                            │
│   → SLA: 4 hours                                          │
│                                                            │
│ User Message:                                              │
│   "AI system is currently unavailable. Your ticket has    │
│   been submitted using rule-based routing. A support      │
│   team member will review it shortly."                    │
└───────────────────────────────────────────────────────────┘

OUTCOME:
✓ System continues operating (no crash)
✓ Tickets still accepted and routed
✓ Rule-based fallback used
✓ User notified of degraded service
✓ Support team still receives tickets
✓ Business continuity maintained
✓ Admin alerted to fix AI models
```

---

## 🤔 Flow 7: Ambiguous Category Classification

**Scenario:** Ticket could belong to multiple categories

```
USER INPUT
├─ Subject: "Application slow when connected to VPN"
├─ Description: "CRM application becomes very slow when I connect 
│   through VPN. Without VPN, works fine. Could be software or network?"
└─ Context: Software / Application

                    ↓

┌───────────────────────────────────────────────────────────┐
│ MODEL 2: CATEGORY CLASSIFICATION                          │
├───────────────────────────────────────────────────────────┤
│ Process:                                                   │
│   1. Encode ticket                                        │
│   2. Compare to all 11 categories                         │
│   3. Detect ambiguity (multiple high scores)              │
│                                                            │
│ Category Scores:                                           │
│   ✓ Software: 0.62 (62%) ← TOP MATCH                      │
│   ✓ Network: 0.58 (58%)  ← CLOSE SECOND                   │
│   ✓ Cloud: 0.31 (31%)                                     │
│   ✓ DevOps: 0.28 (28%)                                    │
│   ✓ Database: 0.15 (15%)                                  │
│                                                            │
│ Ambiguity Detection:                                       │
│   Δ = Top score - 2nd score = 0.62 - 0.58 = 0.04 (4%)     │
│   IF Δ < 0.10 THEN classification is AMBIGUOUS            │
│                                                            │
│ Output:                                                    │
│   ✓ Predicted Category: Software (low confidence)         │
│   ✓ Ambiguity Flag: TRUE                                  │
│   ✓ Alternative: Network (58% - very close)               │
│   ✓ Recommendation: Manual review or dual-team routing    │
└───────────────────────────────────────────────────────────┘

                    ↓

┌───────────────────────────────────────────────────────────┐
│ MODEL 1: DUPLICATE DETECTION                              │
│ (Proceeds normally with Software category)                │
│ Output: No high-similarity matches found                  │
└───────────────────────────────────────────────────────────┘

                    ↓

┌───────────────────────────────────────────────────────────┐
│ MODEL 3: PRIORITY PREDICTION                              │
│ Keywords: "slow", "without VPN works fine"                │
│ Output: Priority: MEDIUM                                  │
└───────────────────────────────────────────────────────────┘

                    ↓

┌───────────────────────────────────────────────────────────┐
│ ROUTING DECISION (AMBIGUOUS CASE HANDLING)                 │
├───────────────────────────────────────────────────────────┤
│ Primary Category: Software                                 │
│ Alternative: Network (58% confidence)                      │
│                                                            │
│ Smart Handling Options:                                    │
│   Option 1: Route to primary (Application Support)        │
│   Option 2: CC both teams (App Support + Network Ops)     │
│   Option 3: Escalate to senior tech for triage            │
│                                                            │
│ Selected: Option 1 (with note to check Network)           │
│                                                            │
│ Assigned Team: Application Support Team                   │
│ CC/Note: "Consider Network team collaboration - VPN issue"│
│ SLA: 4 hours (Medium priority)                            │
└───────────────────────────────────────────────────────────┘

OUTCOME:
✓ Ambiguity detected and flagged
✓ Primary category selected (Software)
✓ Alternative category noted (Network)
✓ Support team alerted to potential cross-team issue
✓ Complete transparency in classification
✓ User sees both category scores in results
```

---

## 🔄 Flow 8: Complete End-to-End Pipeline

**Master flow diagram showing all components**

```
┌─────────────────────────────────────────────────────────────────┐
│                    TICKET SUBMISSION FLOW                        │
│                     (Complete Pipeline)                          │
└─────────────────────────────────────────────────────────────────┘

[1] USER INPUT
    │
    ├─ Subject: String (min 10 chars)
    ├─ Description: String (min 20 chars)
    ├─ Context: Dropdown (Software/Hardware/Network/...)
    └─ Subtype: Optional (Application name, Device type, etc.)
    │
    ↓
    
[2] INPUT VALIDATION (HTML5 + Backend)
    │
    ├─ Subject length ≥ 10? ✓
    ├─ Description length ≥ 20? ✓
    ├─ Context selected? ✓
    │
    ↓ PASS
    
[3] SEMANTIC TEXT BUILDER
    │
    ├─ Combine: Context + Subtype + Subject + Description
    ├─ Example: "[Context: Software] [Application: Outlook]
    │            Outlook crashes when opening PDF attachments.
    │            Error message: 'Outlook has stopped working'..."
    │
    ↓
    
[4] MODEL 2: CATEGORY CLASSIFICATION (Zero-Shot)
    │
    ├─ Input: Semantic text
    ├─ Process: Encode → Compare to 11 categories → Similarity
    ├─ Security Check: Scan for security keywords
    │   └─ IF detected → Override category to "Security"
    │
    ├─ Output:
    │   ├─ Predicted Category (e.g., "Software")
    │   ├─ Confidence Score (e.g., 0.89)
    │   ├─ All Category Scores (for explainability)
    │   └─ Security Override Flag (if applicable)
    │
    ↓
    
[5] MODEL 1: DUPLICATE DETECTION (Category-Weighted)
    │
    ├─ Input: Ticket embedding + Predicted category
    │
    ├─ Edge Case Checks:
    │   ├─ Historical tickets == 0? → Zero-shot mode
    │   └─ If zero-shot → Skip duplicate detection
    │
    ├─ Process:
    │   ├─ Encode new ticket → 384-dim vector
    │   ├─ Compare to all historical tickets
    │   ├─ Apply category weighting:
    │   │   ├─ Same category: 1.0x
    │   │   └─ Different category: 0.6x
    │   ├─ Sort by weighted similarity
    │   └─ Check thresholds:
    │       ├─ ≥80% → Mark as DUPLICATE
    │       └─ ≥60% → Enable AUTO-REPLY
    │
    ├─ Output:
    │   ├─ Similar Tickets (top 5)
    │   ├─ Highest Weighted Similarity
    │   ├─ Is Duplicate? (boolean)
    │   ├─ Auto-Reply Enabled? (boolean)
    │   └─ Zero-Shot Mode? (boolean)
    │
    ↓
    
[6] AUTO-REPLY GENERATOR (If similarity ≥60%)
    │
    ├─ Triggered: similarity_score ≥ 0.60
    │
    ├─ Process:
    │   ├─ Extract source ticket details
    │   ├─ Generate suggested solution
    │   ├─ List recommended next steps
    │   └─ Add disclaimer for manual verification
    │
    ├─ Output:
    │   ├─ Auto-Reply Message
    │   ├─ Confidence (HIGH if ≥80%, MEDIUM if 60-79%)
    │   ├─ Source Ticket ID
    │   └─ Suggested Next Steps
    │
    ↓
    
[7] MODEL 3: PRIORITY PREDICTION
    │
    ├─ Input: Subject + Description + Category
    │
    ├─ Decision Tree:
    │   ├─ Is Duplicate?
    │   │   └─ YES → Inherit priority from original ticket
    │   │
    │   └─ NO → Calculate new priority:
    │       ├─ Scan for impact keywords:
    │       │   ├─ Critical: "production down", "security breach"
    │       │   ├─ High: "blocked", "cannot work", "urgent"
    │       │   ├─ Medium: "slow", "sometimes", "intermittent"
    │       │   └─ Low: "question", "how to", "enhancement"
    │       │
    │       ├─ Apply category risk:
    │       │   ├─ Security/DevOps → Elevate priority
    │       │   ├─ Software/Network → Keep as-is
    │       │   └─ Hardware → May lower if keywords weak
    │       │
    │       └─ Combine: Keyword priority + Category risk
    │
    ├─ Security Override:
    │   └─ IF category == "Security" → Force CRITICAL
    │
    ├─ Output:
    │   ├─ Suggested Priority (Low/Medium/High/Critical)
    │   ├─ Confidence Score
    │   ├─ Reasoning (list of factors)
    │   └─ Keyword Matches (for explainability)
    │
    ↓
    
[8] ROUTING DECISION (Rule-Based)
    │
    ├─ Input: Predicted Category
    │
    ├─ Category → Team Mapping:
    │   ├─ Software → Application Support Team
    │   ├─ Hardware → Desktop Support Team
    │   ├─ Network → Network Operations Team
    │   ├─ Security → Security Operations Center (SOC)
    │   ├─ DevOps → DevOps & Infrastructure Team
    │   ├─ Database → Database Administration Team
    │   ├─ Cloud → Cloud Platform Team
    │   ├─ Access → Identity & Access Management Team
    │   └─ Other → General IT Support Team
    │
    ├─ SLA Calculation (Based on Priority):
    │   ├─ Critical → 15 minutes
    │   ├─ High → 1 hour
    │   ├─ Medium → 4 hours
    │   └─ Low → 8 hours
    │
    ├─ Output:
    │   ├─ Assigned Team
    │   ├─ Expected Response Time
    │   └─ Special Handling Notes
    │
    ↓
    
[9] RESULTS DISPLAY
    │
    ├─ Terminal Output (Complete Reasoning):
    │   ├─ [STEP 0] Input Normalization
    │   ├─ [STEP 1] Model 2 - Category Classification
    │   │   └─ Shows all category scores + explanation
    │   ├─ [STEP 2] Model 1 - Duplicate Detection
    │   │   └─ Shows top 5 similar tickets + weighting
    │   ├─ [AUTO-REPLY] (if enabled)
    │   │   └─ Shows suggested solution + next steps
    │   ├─ [STEP 3] Model 3 - Priority Prediction
    │   │   └─ Shows keywords found + category risk
    │   ├─ [STEP 4] Routing Decision
    │   │   └─ Shows assigned team + SLA
    │   └─ [FINAL SUMMARY]
    │       └─ Recap of all decisions
    │
    └─ Browser Output (Formatted Results):
        ├─ Ticket Summary (timestamp, subject, description)
        ├─ Model 2 Results (category, confidence, scores)
        ├─ Model 1 Results (duplicate status, similar tickets)
        ├─ Auto-Reply Section (if enabled) ← NEW!
        │   ├─ Suggested solution
        │   ├─ Next steps
        │   └─ Source ticket reference
        ├─ Model 3 Results (priority, confidence, reasoning)
        ├─ Routing (assigned team, SLA, team description)
        └─ Explainability Note (audit trail reference)

┌─────────────────────────────────────────────────────────────────┐
│                         OUTCOME SUMMARY                          │
├─────────────────────────────────────────────────────────────────┤
│ ✓ Ticket analyzed by 3 AI models sequentially                   │
│ ✓ Complete explainability (every decision logged)               │
│ ✓ Auto-reply generated (if similarity ≥60%)                     │
│ ✓ Duplicate detected (if similarity ≥80%)                       │
│ ✓ Security escalation (if keywords detected)                    │
│ ✓ Zero-shot capability (works with 0 historical tickets)        │
│ ✓ Fallback mode (graceful degradation if models fail)           │
│ ✓ Rule-based routing (deterministic team assignment)            │
│ ✓ SLA calculated (based on priority)                            │
│ ✓ Full transparency (terminal + browser results)                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Summary: System Capabilities

| Feature | Status | Threshold | Action |
|---------|--------|-----------|--------|
| **Zero-Shot Learning** | ✅ | N/A | Works from day 1, no training |
| **Category Classification** | ✅ | N/A | 11 categories, semantic similarity |
| **Duplicate Detection** | ✅ | ≥80% | Flag as duplicate |
| **Auto-Reply** | ✅ | ≥60% | Generate suggested solution |
| **Manual Review** | ✅ | <60% | No auto-reply, team handles |
| **Security Escalation** | ✅ | Keyword-based | Auto-route to SOC |
| **Priority Assignment** | ✅ | Keyword + Category | Low/Medium/High/Critical |
| **Fallback Mode** | ✅ | On AI failure | Rule-based routing |
| **Empty Database** | ✅ | 0 tickets | Zero-shot mode |
| **Explainability** | ✅ | Always | Every decision logged |

---

## 🎯 Key Decision Thresholds

```
Similarity Score Ranges:

  0% ────────────────── 60% ────────── 80% ─────── 100%
  │                     │              │            │
  │                     │              │            │
  NEW TICKET            AUTO-REPLY     DUPLICATE    EXACT MATCH
  Manual review         Enabled        Detected     Inherited priority
  No auto-reply         Medium conf    High conf    100% conf
```

**Decision Logic:**
- **< 60%**: New ticket, manual review required, no auto-reply
- **60-79%**: Auto-reply enabled (MEDIUM confidence), not duplicate
- **80-100%**: Duplicate detected + Auto-reply (HIGH confidence)

---

## 🔍 Transparency Guarantee

Every flow includes:
1. ✅ Terminal logging (step-by-step reasoning)
2. ✅ Browser display (formatted results)
3. ✅ Confidence scores (for every decision)
4. ✅ Alternative categories (for ambiguous cases)
5. ✅ Explainability notes (why each decision was made)
6. ✅ Source attribution (which model, which ticket)
7. ✅ Audit trail (complete decision path)

**No black boxes. No hidden logic. Complete transparency.**

---

**Document Version:** 2.0  
**Last Updated:** February 20, 2026  
**Status:** Production Ready ✅
