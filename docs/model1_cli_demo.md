# Model 1: CLI Demo System – Technical Documentation

**Version:** 1.0  
**Date:** February 20, 2026  
**Demo Type:** Terminal-Based Interactive Ticket Submission  
**Purpose:** Demonstrate Model 1 (Semantic Similarity & Duplicate Detection) in production-realistic flow

---

## Executive Summary

This CLI demo system simulates the complete end-to-end flow of an employee raising an internal IT helpdesk ticket and receiving AI-powered duplicate detection recommendations. It demonstrates **Model 1: Ticket Understanding** in a terminal environment before UI development.

**Key Principle:**  
*The CLI captures the exact same structured data that a future web/mobile UI form will collect, processes it identically, and produces the same Model 1 outputs.*

---

## Why a Terminal Demo Before UI?

### 1. **Validate AI Logic Before UI Investment**

Building a full web UI requires significant frontend development effort. This CLI demo allows stakeholders to:

- **Test Model 1 accuracy** with real user inputs
- **Evaluate duplicate detection quality** across various ticket types
- **Refine similarity thresholds** based on actual usage patterns
- **Identify edge cases** before committing to UI design

**Enterprise Benefit:** Reduces risk of expensive UI rework if AI logic needs adjustment.

---

### 2. **Demonstrate Production Data Flow**

The CLI mirrors the exact production architecture:

```
User Input (CLI Form)
    ↓
Structured Data Collection (context, subject, description)
    ↓
Ticket Text Builder (convert form fields → semantic text)
    ↓
Model 1: Embedding Generation (text → 384-dim vector)
    ↓
Model 1: Similarity Matching (compare with historical tickets)
    ↓
Model 1: Duplicate Detection (threshold check ≥ 80%)
    ↓
Recommendation Engine (link existing / create new)
    ↓
Display Results (CLI Output)
```

**Enterprise Benefit:** Stakeholders see the *real* AI, not a mockup or prototype.

---

### 3. **Enable Non-Technical Stakeholder Testing**

Product managers, business analysts, and executives can:

- Run the demo themselves (no coding required)
- Submit realistic tickets (VPN issues, hardware requests, software access)
- See AI recommendations instantly
- Provide feedback on accuracy and usefulness

**Enterprise Benefit:** Faster iteration cycles based on real stakeholder feedback.

---

### 4. **Prove Multi-Tenant Readiness**

The CLI demo uses the same multi-tenant data layer as production:

- Tickets are tenant-scoped (`acme_corp`, `initech`)
- Similarity search is tenant-isolated (no cross-tenant leakage)
- Embeddings are separately stored per tenant

**Enterprise Benefit:** Demonstrates SaaS readiness before full platform deployment.

---

## What Data Comes From the UI Form?

The CLI demo collects the **exact same fields** that a web/mobile form will capture:

### Form Field Mapping

| UI Form Field | CLI Prompt | Data Type | Example |
|---------------|------------|-----------|---------|
| **Issue Context** | "What is your issue related to?" | Dropdown (7 options) | "Hardware / Device" |
| **Context-Specific Detail** | "Which device is affected?" | Conditional dropdown | "Docking Station" |
| **Subject** | "Enter ticket subject" | Text input (10-200 chars) | "Monitor not detected via dock" |
| **Description** | "Enter detailed description" | Text area (min 20 chars) | "External display not showing up..." |

### Conditional Logic (Context-Driven)

The CLI implements **conditional field display** based on user selection:

| Selected Context | Additional Field | Options |
|------------------|------------------|---------|
| Software / Application | Application Name | GitHub, Jira, VS Code, Jenkins, Docker, etc. |
| Hardware / Device | Device Type | Laptop, Monitor, Docking Station, Keyboard, etc. |
| Network / VPN | Network Component | VPN, WiFi, DNS, SSL Certificate, etc. |
| Workplace / Facilities | Facility Item | Chair, Desk, Standing Desk, AC, etc. |
| Access / Permission | Access Type | Application Access, Database Access, Cloud Access, etc. |
| Environment / Setup | Environment | Local Dev, CI/CD Pipeline, Staging, Production, etc. |
| Others | Custom Input | Free text |

**Why This Matters:**  
In production, the UI form will show/hide fields dynamically (e.g., "Application Name" dropdown only appears when "Software / Application" is selected). The CLI replicates this exact behavior.

---

## What Model 1 Does (and Does NOT Do)

### ✅ What Model 1 DOES

#### 1. **Semantic Understanding**

Model 1 converts natural language ticket text into a 384-dimensional embedding vector using the `all-MiniLM-L6-v2` sentence transformer model.

**Example:**

```
Input Text:
  [Context: Hardware / Device]
  [Device: Docking Station]
  Monitor not detected via docking station.
  External display not showing up when connected through dock.

Output:
  384-dimensional vector: [0.021, -0.045, 0.133, ..., -0.089]
```

#### 2. **Similarity Matching**

Model 1 computes **cosine similarity** between the new ticket embedding and all historical ticket embeddings.

**Example Output:**

```
Top 3 Similar Tickets:
1. ACME-013 – External monitor connection issue (87.3% similarity)
2. INIT-008 – Docking station USB not working (64.2% similarity)
3. ACME-004 – HDMI port failure (52.7% similarity)
```

#### 3. **Duplicate Detection**

Model 1 applies a **threshold-based rule**: If similarity ≥ 80%, flag as potential duplicate.

**Example:**

```
✓ Similarity: 87.3% ≥ 80% → DUPLICATE LIKELY
✗ Similarity: 64.2% < 80% → NEW ISSUE
```

---

### ❌ What Model 1 Does NOT Do

#### 1. **Priority Assignment**

Model 1 does **NOT** determine ticket priority (Low, Medium, High, Critical).

- **Why:** Priority depends on business impact, SLA rules, and urgency indicators.
- **Handled By:** Model 3 (Priority Classification) – not yet implemented.

**Example:**  
If a ticket says "Production database is down", Model 1 will NOT automatically mark it as "Critical". It only finds similar tickets. Model 3 will classify priority based on keywords like "production", "down", "database".

---

#### 2. **Routing/Assignment**

Model 1 does **NOT** route tickets to specific teams or agents.

- **Why:** Routing involves team capacity, skill matching, and workload balancing.
- **Handled By:** Model 4 (Intelligent Routing) – not yet implemented.

**Example:**  
Model 1 will find that a "GitHub access request" is similar to past GitHub tickets, but it won't assign it to the "DevOps Team". Model 4 will handle routing based on team expertise and availability.

---

#### 3. **Category Classification**

Model 1 does **NOT** auto-classify tickets into categories (Software, Hardware, Network, etc.).

- **Why:** The category is provided by the user via the form (UI context selection).
- **Handled By:** User input in this demo; Model 2 (Auto-Classification) could refine it in future.

**Example:**  
User selects "Hardware / Device" → CLI uses this as the category. Model 1 doesn't change it.

---

#### 4. **Ticket Creation/Updates**

Model 1 does **NOT** create tickets in a database or update existing tickets.

- **Why:** Model 1 is a **read-only AI inference engine**. It analyzes and recommends.
- **Handled By:** Application layer (API + database) – outside Model 1 scope.

**Example:**  
Model 1 outputs: "Link to ticket ACME-013". The application layer must then create a database link or comment. Model 1 only provides the recommendation.

---

## CLI Demo: Input/Output Examples

### Example 1: Duplicate Detected (Hardware Issue)

**Input (User responds to CLI prompts):**

```
Issue Context: Hardware / Device
Device Type: Docking Station
Subject: Docking station not detecting external monitor
Description: When I connect my Dell monitor to the docking station, 
             it's not being detected. Monitor works fine when 
             connected directly to laptop via HDMI.
```

**Model 1 Processing:**

```
Semantic Text Built:
  [Context: Hardware / Device]
  [Device: Docking Station]
  Docking station not detecting external monitor.
  When I connect my Dell monitor to the docking station, 
  it's not being detected. Monitor works fine when 
  connected directly to laptop via HDMI.

Embedding Generated: 384-dim vector
Similarity Computed: Cosine similarity with 30 historical tickets
```

**CLI Output:**

```
==================================================================================
                         AI ANALYSIS RESULT – MODEL 1
==================================================================================

📝 Your Ticket:
   Context: Hardware / Device
   Device Type: Docking Station
   Subject: Docking station not detecting external monitor

🔍 Top Similar Historical Tickets:

  1. ACME-013 – Monitor not detected via docking station
     Similarity: 87.3% ⚠️  Possible Duplicate
     Status: Open
     Priority: Medium

  2. INIT-005 – External display connection issue
     Similarity: 62.4%
     Status: Resolved
     Priority: Low

  3. ACME-007 – HDMI port not working on dock
     Similarity: 54.1%
     Status: Open
     Priority: Medium

--------------------------------------------------------------------------------
Duplicate Detection Status:

  ⚠️  DUPLICATE LIKELY (Similarity: 87.3% ≥ 80%)

--------------------------------------------------------------------------------
💡 AI Recommendation:

  • This ticket appears to be a duplicate of ACME-013
  • Recommended Action: Link to existing ticket ACME-013
  • Status: Open
  • Next Step: Notify user about ongoing investigation

==================================================================================
                              END OF ANALYSIS
==================================================================================

✓ Ticket analysis complete.
  In production, this would create/link the ticket automatically.
```

---

### Example 2: New Issue (Software Problem)

**Input:**

```
Issue Context: Software / Application
Application: VS Code
Subject: VS Code not detecting Python interpreter after update
Description: After updating to Python 3.11, VS Code is not showing 
             it in the interpreter list. Tried reloading window and 
             reinstalling Python extension but still not showing up.
```

**Model 1 Processing:**

```
Semantic Text Built:
  [Context: Software / Application]
  [Application: VS Code]
  VS Code not detecting Python interpreter after update.
  After updating to Python 3.11, VS Code is not showing 
  it in the interpreter list. Tried reloading window and 
  reinstalling Python extension but still not showing up.

Embedding Generated: 384-dim vector
Similarity Computed: Against 30 historical tickets
```

**CLI Output:**

```
==================================================================================
                         AI ANALYSIS RESULT – MODEL 1
==================================================================================

📝 Your Ticket:
   Context: Software / Application
   Application: VS Code
   Subject: VS Code not detecting Python interpreter after update

🔍 Top Similar Historical Tickets:

  1. INIT-006 – VS Code extensions not syncing
     Similarity: 58.2%
     Status: Open
     Priority: Low

  2. ACME-007 – IntelliJ IDEA license activation failed
     Similarity: 47.9%
     Status: Open
     Priority: High

  3. INIT-015 – npm registry connection timeout
     Similarity: 43.1%
     Status: Open
     Priority: High

--------------------------------------------------------------------------------
Duplicate Detection Status:

  ✓ NEW ISSUE (Highest Similarity: 58.2% < 80%)

--------------------------------------------------------------------------------
💡 AI Recommendation:

  • This appears to be a new issue
  • Recommended Action: Create new ticket
  • Suggested Routing: Development Tools Team
  • Reference Similar Ticket: INIT-006 for context

==================================================================================
                              END OF ANALYSIS
==================================================================================

✓ Ticket analysis complete.
  In production, this would create/link the ticket automatically.
```

---

### Example 3: Critical VPN Issue

**Input:**

```
Issue Context: Network / VPN
Network Component: VPN
Subject: VPN gateway not responding since this morning
Description: Corporate VPN gateway not responding since this morning. 
             Multiple engineers cannot connect remotely. Getting 
             connection timeout error to vpn.acme.com. Very urgent 
             as 60% of team is remote.
```

**CLI Output (Excerpt):**

```
🔍 Top Similar Historical Tickets:

  1. INIT-003 – VPN gateway not responding
     Similarity: 92.7% ⚠️  Possible Duplicate
     Status: Open
     Priority: Critical

  2. ACME-004 – VPN disconnects every 30 minutes
     Similarity: 71.3%
     Status: Open
     Priority: High

Duplicate Detection Status:

  ⚠️  DUPLICATE LIKELY (Similarity: 92.7% ≥ 80%)

💡 AI Recommendation:

  • This ticket appears to be a duplicate of INIT-003
  • Recommended Action: Link to existing ticket INIT-003
  • Status: Open
  • Next Step: Notify user about ongoing investigation
```

**Enterprise Insight:**  
This prevents creating duplicate "VPN down" tickets during an outage, reducing support team overhead.

---

## How This Maps to Enterprise Requirements

### PowerGrid PS / ITSM Standards

| ITSM Requirement | CLI Demo Implementation | Production Mapping |
|------------------|-------------------------|-------------------|
| **Ticket Deduplication** | Model 1 detects duplicates ≥ 80% similarity | Same logic in production API |
| **Knowledge Base Linking** | Top-3 similar tickets shown as context | UI shows these as "Related Articles" |
| **Intelligent Routing Hints** | Category-based team suggestion | Model 4 will use this + workload balancing |
| **Audit Trail** | CLI logs all inputs/outputs to terminal | Production logs to database with timestamps |
| **User Feedback Loop** | User sees AI recommendation immediately | UI shows recommendation + allows override |

---

### Multi-Tenant SaaS Readiness

The CLI demo uses **tenant-scoped data**:

```python
# Tickets are tenant-prefixed
ACME-001, ACME-002, ... (acme_corp tenant)
INIT-001, INIT-002, ... (initech tenant)

# Embeddings stored separately
data/tenants/acme_corp/embeddings.pkl
data/tenants/initech/embeddings.pkl

# Similarity search is tenant-isolated
# User from acme_corp ONLY sees acme_corp tickets
```

**Enterprise Benefit:**  
Proves data isolation before launching multi-tenant SaaS platform.

---

## Running the CLI Demo

### Prerequisites

1. **Generate Embeddings** (one-time setup):

```bash
python src/model1_embeddings.py
```

This creates `data/ticket_embeddings.pkl` with vector representations of all 30 historical tickets.

---

### Run the Demo

```bash
python src/cli_ticket_input.py
```

**Expected Flow:**

1. Welcome banner displays
2. User selects issue context (e.g., "Hardware / Device")
3. User selects device type (e.g., "Docking Station")
4. User enters subject (e.g., "Monitor not detected")
5. User enters description (detailed explanation)
6. System validates inputs
7. System builds semantic text
8. Model 1 analyzes (embedding + similarity)
9. Results displayed with duplicate detection + recommendation

**Time:** ~2 minutes per ticket submission

---

## Technical Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLI DEMO ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────┐
│  cli_ticket_input.py │  ← Main entry point (user interaction)
└──────────┬──────────┘
           │
           ├─ Collect structured inputs (context, subject, description)
           │
           ├─ Validate inputs (min lengths, required fields)
           │
           ↓
┌─────────────────────────┐
│ ticket_text_builder.py   │  ← Converts form fields → semantic text
└──────────┬──────────────┘
           │
           ├─ build_semantic_text()
           ├─ normalize_category()
           ├─ validate_ticket_input()
           │
           ↓
┌─────────────────────────┐
│   model1_similarity.py   │  ← Model 1 inference (UNCHANGED)
└──────────┬──────────────┘
           │
           ├─ encode_new_ticket() → 384-dim embedding
           ├─ find_similar_tickets() → top-N matches
           ├─ check_duplicate() → boolean (≥ 80%)
           │
           ↓
┌─────────────────────────┐
│  cli_ticket_input.py     │  ← Display results in terminal
└─────────────────────────┘
    • Top 3 similar tickets
    • Duplicate status
    • AI recommendation
```

---

### Data Flow

```
User Input (CLI)
    ↓
Structured Data
    {
      "context": "Hardware / Device",
      "context_details": {"device_type": "Docking Station"},
      "subject": "Monitor not detected",
      "description": "External display not showing up..."
    }
    ↓
Semantic Text Builder
    ↓
Semantic Text
    [Context: Hardware / Device]
    [Device: Docking Station]
    Monitor not detected.
    External display not showing up...
    ↓
Model 1: Encoding
    ↓
384-dimensional embedding vector
    [0.021, -0.045, 0.133, ..., -0.089]
    ↓
Model 1: Similarity Matching
    ↓
Cosine similarity with 30 historical tickets
    ↓
Top 3 Results + Duplicate Flag
    {
      "similar_tickets": [
        {"ticket_id": "ACME-013", "similarity": 0.873},
        {"ticket_id": "INIT-005", "similarity": 0.624},
        {"ticket_id": "ACME-007", "similarity": 0.541}
      ],
      "is_duplicate": True,
      "top_similarity": 0.873
    }
    ↓
Display Results (Terminal)
```

---

## Validation & Quality Assurance

### Input Validation Rules

| Field | Validation Rule | Error Message |
|-------|----------------|---------------|
| Subject | Not empty | "Subject cannot be empty" |
| Subject | ≥ 10 characters | "Subject must be at least 10 characters" |
| Subject | ≤ 200 characters | "Subject must be less than 200 characters" |
| Description | Not empty | "Description cannot be empty" |
| Description | ≥ 20 characters | "Description must be at least 20 characters" |

---

### Model 1 Quality Checks

Before displaying results, the CLI verifies:

1. ✅ **Embeddings file exists** (`data/ticket_embeddings.pkl`)
2. ✅ **Model loads successfully** (all-MiniLM-L6-v2)
3. ✅ **Similarity scores are valid** (0.0 to 1.0 range)
4. ✅ **No hallucinated results** (all returned tickets exist in `tickets.csv`)

---

## Future Enhancements (Post-CLI Demo)

Once the CLI demo is validated, the following enhancements can be built:

### 1. **Web UI Form**

Replace CLI prompts with:
- Dropdown menus (styled with enterprise design system)
- Auto-complete for application names
- Rich text editor for description
- Real-time duplicate detection (as user types)

### 2. **Model 2: Auto-Classification**

If user selects "Others" for context, Model 2 will:
- Analyze subject + description
- Auto-suggest correct category
- Reduce manual categorization

### 3. **Model 3: Priority Prediction**

Add AI-based priority assignment:
- Extract urgency signals ("urgent", "production down", "blocking")
- Predict priority (Low/Medium/High/Critical)
- Override available for user

### 4. **Model 4: Intelligent Routing**

Route tickets based on:
- Similar ticket resolution history (which team solved it?)
- Team workload and availability
- Agent skill matching

---

## Conclusion

The CLI demo system provides a **production-realistic demonstration** of Model 1's capabilities without requiring a full UI. It allows enterprise stakeholders to:

- ✅ Test AI accuracy with real inputs
- ✅ Validate duplicate detection quality
- ✅ See exact data flow from form → Model 1 → recommendation
- ✅ Provide feedback before UI development

**Next Steps:**

1. Run embeddings generation: `python src/model1_embeddings.py`
2. Test CLI demo: `python src/cli_ticket_input.py`
3. Validate with stakeholders across various ticket types
4. Iterate on threshold tuning (80% default, adjustable per tenant)
5. Proceed to UI development once AI logic is validated

---

**End of Documentation**
