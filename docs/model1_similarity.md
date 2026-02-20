# Model 1: Category-Weighted Similarity Matching

## Table of Contents
- [Overview](#overview)
- [Purpose](#purpose)
- [Architecture](#architecture)
- [Input/Output Contract](#inputoutput-contract)
- [Enhancement: Category Weighting](#enhancement-category-weighting)
- [Design Decisions](#design-decisions)
- [Why No Training](#why-no-training)
- [Enterprise Justification](#enterprise-justification)
- [CLI Usage Examples](#cli-usage-examples)
- [Limitations](#limitations)
- [Testing](#testing)

---

## Overview

Model 1 is the **Ticket Understanding layer** that detects duplicate tickets and finds similar historical tickets using semantic similarity. The **enhanced version** includes category-aware weighting to improve duplicate detection accuracy.

**Model Version:** 1.1 (Category-Weighted)  
**Base Model:** all-MiniLM-L6-v2 (384-dimensional embeddings)  
**Method:** Cosine similarity with category weighting  
**Duplicate Threshold:** 0.80 (80% similarity)

---

## Purpose

### Primary Responsibilities
1. **Duplicate Detection:** Identify if a new ticket is a repeat of an existing issue
2. **Similar Ticket Retrieval:** Find top-N most similar historical tickets
3. **Category-Aware Ranking:** Prioritize matches within the predicted category

### What Model 1 Does
- ✅ Semantic text comparison using embeddings
- ✅ Duplicate detection with configurable threshold
- ✅ Category-weighted similarity scoring
- ✅ Find similar past tickets for context

### What Model 1 Does NOT Do
- ❌ Category classification (that's Model 2)
- ❌ Priority assignment (that's Model 3)
- ❌ Routing decisions (deterministic rules handle that)
- ❌ Text generation or ticket resolution

---

## Architecture

### Standard Flow
```
New Ticket (Subject + Description)
         ↓
   Encode to Embedding (384-dim vector)
         ↓
   Compute Cosine Similarity with ALL Historical Tickets
         ↓
   Rank by Similarity Score
         ↓
   Return Top-N Matches + Duplicate Flag
```

### Enhanced Flow (Category-Weighted)
```
New Ticket + Predicted Category (from Model 2)
         ↓
   Encode to Embedding
         ↓
   Compute Raw Cosine Similarity with ALL Historical Tickets
         ↓
   Apply Category Weighting:
     - Same Category: weight = 1.0
     - Different Category: weight = 0.6
         ↓
   Weighted Score = Raw Similarity × Weight
         ↓
   Rank by Weighted Score
         ↓
   Return Top-N Matches + Duplicate Flag
```

---

## Input/Output Contract

### Input
```python
{
    "subject": str,              # Required - ticket subject
    "description": str,          # Required - ticket description  
    "predicted_category": str,   # Required for weighted version
    "top_n": int                 # Optional - number of results (default: 3)
}
```

### Output (Weighted Version)
```python
{
    "is_duplicate": bool,                # True if highest score >= 0.80
    "highest_weighted_score": float,     # Top similarity score (0-1)
    "highest_raw_similarity": float,     # Top score before weighting
    "similar_tickets": [
        {
            "ticket_id": str,
            "category": str,
            "subject": str,
            "description": str,
            "status": str,
            "priority": str,
            "raw_similarity": float,      # Before weighting
            "weighted_score": float,      # After weighting
            "weight_applied": float,      # 1.0 or 0.6
            "category_match": bool,       # Same category as new ticket?
            "is_duplicate": bool          # >= 0.80 threshold
        }
    ],
    "weighting_applied": true,
    "predicted_category": str,
    "explainability": {
        "same_category_weight": 1.0,
        "different_category_weight": 0.6,
        "duplicate_threshold": 0.80,
        "category_matches": int          # How many in same category
    }
}
```

---

## Enhancement: Category Weighting

### Problem Solved
Without category weighting, a hardware issue might match a software issue with high textual similarity, even though they're fundamentally different problem types.

### Solution
Apply a weighting factor based on category match:
- **Same Category:** `score = cosine_similarity × 1.0` (full score)
- **Different Category:** `score = cosine_similarity × 0.6` (40% penalty)

### Benefits
1. **Better Duplicate Detection:** Duplicates in the same category rank higher
2. **No Hard Filtering:** Still allows cross-category matches (just ranked lower)
3. **Explainable:** Clear why certain tickets rank higher
4. **Deterministic:** Same input always produces same output

### Example Impact
```
Scenario: New "VPN Connection Issue" ticket
          Predicted Category: Network

Without Weighting:
  #1: T015 (Network, VPN) - Raw: 0.87
  #2: T023 (Software, App) - Raw: 0.85  ← High textual similarity but wrong category
  #3: T009 (Network, DNS) - Raw: 0.79

With Category Weighting:
  #1: T015 (Network, VPN) - Raw: 0.87 × 1.0 = 0.87 ✓ Same category
  #2: T009 (Network, DNS) - Raw: 0.79 × 1.0 = 0.79 ✓ Same category  
  #3: T023 (Software, App) - Raw: 0.85 × 0.6 = 0.51 ✗ Cross-category penalty
```

---

## Design Decisions

### 1. Using Pre-Trained Embeddings Only
**Decision:** Use `all-MiniLM-L6-v2` with no fine-tuning

**Rationale:**
- General-purpose model works well for diverse ticket types
- No training data required (zero-shot)
- Consistent with Model 2 (same embedding space)
- Fast inference (~100ms per ticket)

**Trade-offs:**
- Domain-specific jargon might not be optimally represented
- Cannot adapt to tenant-specific terminology
- But: Simplicity and consistency outweigh these minor issues

### 2. Cosine Similarity Metric
**Decision:** Use cosine similarity instead of Euclidean distance

**Rationale:**
- Measures angle between vectors (semantic meaning)
- Normalized 0-1 scale (interpretable)
- Industry standard for text similarity

### 3. Duplicate Threshold at 0.80
**Decision:** 80% similarity required for duplicate detection

**Rationale:**
- Tested on sample dataset - balances false positives/negatives
- Lower threshold (0.70) → too many false duplicates
- Higher threshold (0.90) → misses valid duplicates
- Configurable if needed per tenant

### 4. Category Weighting Factors
**Decision:** Same category = 1.0, Different = 0.6

**Rationale:**
- 40% penalty is significant but not eliminates cross-category matches
- Tested empirically - better duplicate detection
- Still shows relevant cross-category tickets for unusual cases
- Explainable to stakeholders

---

## Why No Training

### Enterprise Requirement: No Training Pipeline

**Reasons:**
1. **Cold Start Problem:** New tenants have no historical data
2. **Data Drift:** Ticket patterns change over time, requiring retraining
3. **Multi-Tenant Complexity:** Cannot mix tenant data for training
4. **Compliance:** Training on customer data raises privacy concerns
5. **Operational Overhead:** Training infrastructure, monitoring, versioning

### Zero-Shot Approach Instead

**Advantages:**
- Works immediately for new tenants
- No data privacy concerns (no training on customer data)
- Deterministic behavior (same input → same output)
- No model versioning issues
- Easy to audit and explain

**How We Achieve This:**
- Use pre-trained `all-MiniLM-L6-v2` (trained on general text)
- Embeddings capture semantic meaning out-of-the-box
- Category weighting adds domain awareness without training
- Rule-based thresholds (tunable, not learned)

---

## Enterprise Justification

### Why This Approach for Enterprise SaaS

#### 1. Multi-Tenant Safety
- ✅ No cross-contamination between tenants
- ✅ Same model behavior for all customers (fairness)
- ✅ No tenant-specific training data required

#### 2. Compliance & Privacy
- ✅ No training on customer data (GDPR/CCPA safe)
- ✅ Embeddings are not reversible to original text
- ✅ Audit trail: can explain every decision

#### 3. Operational Simplicity
- ✅ No training infrastructure needed
- ✅ No model versioning complexity
- ✅ Consistent behavior across deployments

#### 4. Explainability Requirements
- ✅ "Why is this a duplicate?" → Similarity score + category match
- ✅ Stakeholders can understand cosine similarity concept
- ✅ No black-box ML decisions

#### 5. Performance & Scale
- ✅ Sub-second inference time
- ✅ Pre-computed embeddings for historical tickets
- ✅ Scales horizontally (stateless)

---

## CLI Usage Examples

### Example 1: VPN Duplicate Detection
```bash
$ python src/model1_weighted_similarity.py
```

**Input:**
```
Subject: VPN connection timeout
Description: Cannot connect to VPN. Connection times out.
Predicted Category: Network
```

**Output:**
```
TOP 3 SIMILAR TICKETS (Category-Weighted)

#1 - Weighted Score: 0.8523 (85.23%) ⚠️ POSSIBLE DUPLICATE
  Raw Similarity: 0.8523 × Weight 1.0 = 0.8523
  Category: Network (✓ Same Category)
  Ticket ID: T001
  Subject: VPN authentication failure
  Status: Resolved, Priority: High

#2 - Weighted Score: 0.7845 (78.45%)
  Raw Similarity: 0.7845 × Weight 1.0 = 0.7845
  Category: Network (✓ Same Category)
  Ticket ID: T005
  Subject: Remote access VPN slow
  
#3 - Weighted Score: 0.5234 (52.34%)
  Raw Similarity: 0.8723 × Weight 0.6 = 0.5234
  Category: Software (✗ Different Category)
  Ticket ID: T012
  Subject: Application connection timeout
```

### Example 2: Cross-Category Penalty
```bash
# Same ticket with WRONG category prediction

Predicted Category: Software (incorrect)

#1 - Weighted Score: 0.5114 (51.14%)
  Raw Similarity: 0.8523 × Weight 0.6 = 0.5114
  Category: Network (✗ Different Category)
  Ticket ID: T001
  
→ Duplicate NOT detected due to category penalty
```

---

## Limitations

### 1. Embedding Model Constraints
- **Limitation:** Model trained on general text, not domain-specific
- **Impact:** Technical jargon or acronyms might not be optimally represented
- **Mitigation:** Still works well for most enterprise IT terminology

### 2. No Context Memory
- **Limitation:** Each ticket analyzed independently
- **Impact:** Cannot detect patterns like "multiple related tickets"
- **Mitigation:** This is by design for stateless, deterministic behavior

### 3. Category Dependency
- **Limitation:** Weighted version requires accurate category prediction
- **Impact:** Wrong category from Model 2 = incorrect weighting
- **Mitigation:** Model 2 has high accuracy; fallback to non-weighted still works

### 4. Fixed Threshold
- **Limitation:** 0.80 threshold may not suit all ticket types
- **Impact:** Some edge cases might be missed or over-flagged
- **Mitigation:** Threshold is configurable per tenant if needed

### 5. No Temporal Awareness
- **Limitation:** Does not consider how old similar tickets are
- **Impact:** Might match very old, outdated issues
- **Mitigation:** Could filter by date in future enhancement

---

## Testing

### Test Coverage
See: `tests/test_model1_weighted_similarity.py`

**Test Cases:**
1. ✅ Same category weighting boost
2. ✅ Cross-category weighting penalty
3. ✅ Duplicate detection accuracy
4. ✅ Determinism (same input → same output)
5. ✅ Weighting mathematics correctness

### Running Tests
```bash
python tests/test_model1_weighted_similarity.py
```

### Expected Results
```
Total Tests: 5
Passed: 5 ✓
Failed: 0 ❌
Success Rate: 100.0%
```

---

## Summary

Model 1 provides **enterprise-grade duplicate detection** using:
- ✅ Pre-trained embeddings (no training required)
- ✅ Category-aware weighting (intelligent ranking)
- ✅ Deterministic behavior (auditable)
- ✅ Fast inference (sub-second)
- ✅ Multi-tenant safe

**Key Innovation:** Category weighting improves accuracy without requiring any model training or tenant-specific customization.

---

**Version:** 1.1.0  
**Last Updated:** 2026-02-20  
**Maintainer:** AI Engineering Team
