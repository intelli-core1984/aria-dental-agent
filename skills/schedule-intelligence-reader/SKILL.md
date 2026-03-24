---
# ══════════════════════════════════════════════════════
#  CORTEX SKILL DEFINITION — MACHINE + HUMAN READABLE
# ══════════════════════════════════════════════════════
name: Schedule Intelligence Reader
skill_id: skill-001
version: 1.0.0
status: active
author: CORTEX
signed: true
rollback_to: null
created: 2026-03-23
updated: 2026-03-23

# Trigger conditions — what causes this skill to fire
triggers:
  - "schedule review"
  - "weekly brief"
  - "CEO dashboard"
  - "chair coverage"
  - "schedule health"
  - "KPI review"
  - "practice report"

# What data sources this skill reads
inputs:
  primary:
    - type: excel
      description: CEO dashboard or practice management export (.xlsx, .csv)
    - type: report
      description: Practice management software report (Dentrix, Eaglesoft, OpenDental)
  secondary:
    - type: screenshot
      description: Dashboard screenshots — used for validation only, never as primary source

# What this skill produces
outputs:
  - Weekly CEO Brief (structured report)
  - Data Confidence Assessment
  - Schedule Health Status (2-day + 2-week)
  - Core Observations (schedule risk only)
  - Accountability Prompts by role

# What this skill is explicitly NOT allowed to do
non_goals:
  - Send emails
  - Modify schedules
  - Interact with Dentrix or any practice software directly
  - Perform follow-ups
  - Execute tasks of any kind

# Permissions — read-only data access only
permissions:
  read: [excel_files, csv_files, screenshots, pdf_reports]
  write: []
  network: false
  app_control: false

# Roles referenced in accountability outputs
roles:
  - Front Desk
  - Treatment Coordinator
  - Hygienist
  - Dentist
  - Office Manager

# Apps this skill understands report formats from
compatible_software:
  - Dentrix
  - Eaglesoft
  - OpenDental
  - Curve Dental
  - Carestream Dental

# How CORTEX manages this skill
management:
  update_authority: CORTEX_ONLY
  auto_rollback_on_failure: true
  test_before_push: true
  agent_can_edit: false
---

# Skill 001 — Schedule Intelligence Reader

## Mission

Interpret the CEO dashboard or practice report, validate data quality, and determine schedule health with priority on **2-day and 2-week chair coverage**.

> **Core Rule:** If chairs are not filled, all other metrics are secondary.
> This skill answers one question: **"Are our chairs full — and if not, why?"**

---

## Step 1 — Ingest the Data

Read all available inputs in this order:

1. **Excel dashboard** — parse every tab. Extract all metric values, goals, and periods.
2. **Practice management report** — cross-reference with dashboard values.
3. **Screenshots** — use only to spot-check or resolve conflicts. Never as sole source.

Normalize every extracted metric into this internal data model:

```
metric_name        : string
category           : Tier1 | Tier2 | Tier3
period_type        : daily | weekly | monthly
goal               : number | null
actual             : number | null
variance           : actual - goal
variance_percent   : (variance / goal) * 100
target_direction   : higher_is_better | lower_is_better
status             : green | yellow | red
trend              : up | down | flat | unknown
urgency_score      : 1–10
confidence_score   : 0.0–1.0
owner              : role name (see roles list)
flags              : [] | [list of issues]
```

---

## Step 2 — Validate Every Metric (Do Not Skip)

**The agent must NOT trust bad data.**

### Check for these problems on every metric:

| Problem | Example | Action |
|---|---|---|
| Missing value | Hygiene reappointment % = blank | Flag. Request source. |
| Impossible range | Patient acceptance = 147% | Flag as error. Do not use. |
| Stale report | Date = 3 weeks ago | Flag. Ask for current data. |
| Contradictory KPIs | High reappointment % AND high unscheduled active patients | Flag conflict. Surface both. |
| Static/duplicate values | Same number 4 weeks in a row | Flag as suspicious. |
| Totals don't match breakdowns | Sum of hygiene visits ≠ total visits | Flag inconsistency. |

### Confidence Scoring:
- **1.0** — value present, validated, cross-referenced
- **0.7–0.9** — value present, single source, plausible
- **0.4–0.6** — value present but questionable (anomaly detected)
- **0.0–0.3** — value missing, impossible, or contradicted

### Critical Rule:
> If a Tier 1 metric has confidence < 0.5, **pause conclusions** on schedule health. Surface the data issue first.

---

## Step 3 — Anomaly Detection

Trigger an anomaly flag when:

- A metric moves >25% week-over-week without an obvious cause
- Two metrics contradict each other logically:
  - High new patients + flat or declining scheduled treatment
  - Strong reappointment % + high unscheduled active patients
  - Low missed calls + low new patients
  - High collections + high AR days
- A value is technically valid but operationally unlikely for a dental practice

**Do not silently pass anomalies.** Every anomaly gets surfaced in the report.

---

## Step 4 — Evaluate Schedule Health

This is the highest-priority output of this skill.

### Primary Questions (answer in this order):

1. **Are chairs filled in the next 2 days?**
   - Pull: Open chair time (2-day), Scheduled treatment (2-day)
   - Assign status:
     - ✅ **Protected** — <10% open chair time, treatment scheduled to goal
     - ⚠️ **Vulnerable** — 10–25% open chair time OR scheduled treatment 80–99% of goal
     - 🔴 **Underbooked** — >25% open chair time OR scheduled treatment <80% of goal

2. **Is the 2-week schedule strong?**
   - Pull: Open chair time (2-week), Unscheduled treatment, Unscheduled active patients
   - Assign status:
     - ✅ **Strong** — schedule filling normally, treatment pipeline healthy
     - ⚠️ **Watch** — gaps forming, unscheduled treatment rising
     - 🔴 **Weak** — significant open time, pipeline thin, follow-up behind

3. **Is scheduled treatment volume sufficient to maintain production?**
   - Compare scheduled treatment to production goal
   - If behind: flag which Tier 2 metrics explain why (acceptance %, new patients, recall %)

---

## Step 5 — KPI Priority Hierarchy

Process and report metrics in this order. Tier 2 and 3 are only reported if they explain Tier 1 findings.

### Tier 1 — Schedule Protection (Always Reported)
| Metric | Owner | Target Direction |
|---|---|---|
| Scheduled treatment | Treatment Coordinator | Higher |
| Open chair time | Front Desk + Office Manager | Lower |
| 2-day schedule coverage | Front Desk | Higher |
| 2-week schedule coverage | Office Manager | Higher |
| Unscheduled treatment | Treatment Coordinator | Lower |
| Unscheduled active patients | Front Desk | Lower |
| Hygiene reappointment % | Hygienist | Higher |
| Patients not rescheduled | Front Desk | Lower |
| Follow-up calls completed | Front Desk | Higher |

### Tier 2 — Patient Flow & Conversion (Report if explains Tier 1)
| Metric | Owner | Target Direction |
|---|---|---|
| Patient acceptance % | Treatment Coordinator | Higher |
| New patients | Front Desk + Marketing | Higher |
| Missed call % | Front Desk | Lower |
| Reviews received | Office Manager | Higher |
| Perio % | Hygienist | Higher |
| Hygiene production/visit | Hygienist | Higher |

### Tier 3 — Financial Metrics (Report last, only if relevant)
| Metric | Owner | Target Direction |
|---|---|---|
| Collections | Office Manager | Higher |
| AR days | Office Manager | Lower |
| AR ratio | Office Manager | Lower |
| AR > 30 days | Office Manager | Lower |

---

## Step 6 — Threshold System

Each KPI evaluates against 3 layers in this order:

1. **Practice Target** — clinic-defined goal (from dashboard). Use this first.
2. **Dynamic Threshold** — adjust for seasonality, staffing changes, capacity shifts. If the practice had a provider out this week, adjust expectations accordingly.
3. **Default Benchmark** — industry baseline. Use only when practice target is missing.

If no target exists for a metric, flag it and use the industry benchmark but note the assumption.

---

## Step 7 — Build the Weekly CEO Brief

Output a single structured report. No filler. No padding. Every word earns its place.

---

### OUTPUT FORMAT

```
═══════════════════════════════════════════
WEEKLY CEO BRIEF — SCHEDULE INTELLIGENCE
[Practice Name] · [Period]
Generated: [date]
═══════════════════════════════════════════

━━━ 1. DATA CONFIDENCE ━━━━━━━━━━━━━━━━━━
Overall: [Complete / Incomplete / Questionable]

Missing metrics:
  - [metric name] — [what was expected, what to do]

Anomalies detected:
  - [metric]: [description of conflict or anomaly]

Items requiring clarification:
  - [specific question to ask the practice]

━━━ 2. SCHEDULE STATUS ━━━━━━━━━━━━━━━━━━

2 DAYS AHEAD:  [✅ Protected | ⚠️ Vulnerable | 🔴 Underbooked]
  Open chairs:        [X%] (goal: <10%)
  Scheduled tx:       [$X] (goal: $X)
  Note: [one sentence if action needed]

2 WEEKS AHEAD: [✅ Strong | ⚠️ Watch | 🔴 Weak]
  Open time forming:  [yes/no + detail]
  Unscheduled tx:     [$X]
  Unscheduled pts:    [X]
  Note: [one sentence if action needed]

━━━ 3. CORE OBSERVATIONS ━━━━━━━━━━━━━━━━
[Only signals that directly affect chair utilization.
 Max 5 observations. Most critical first.]

  1. [Observation — plain language, no jargon]
  2. [Observation]
  3. [Observation]

━━━ 4. ACCOUNTABILITY ━━━━━━━━━━━━━━━━━━
[Only include roles with a specific action this week]

  FRONT DESK
    → [Specific action item]

  TREATMENT COORDINATOR
    → [Specific action item]

  HYGIENIST
    → [Specific action item]

  OFFICE MANAGER
    → [Specific action item]

  DENTIST
    → [Specific action item — only if relevant]

═══════════════════════════════════════════
```

---

## Guardrails — What This Skill Must Never Do

- ❌ Never send, forward, or transmit this report anywhere
- ❌ Never modify any schedule, record, or file
- ❌ Never make a conclusion when critical data confidence is below 0.5
- ❌ Never silently assume a missing value — always flag it
- ❌ Never report Tier 2 or Tier 3 metrics without connecting them to a Tier 1 finding
- ❌ Never produce a report longer than necessary — cut everything that doesn't affect chair decisions

---

## Success Criteria

This skill is performing correctly when it:

- [ ] Accurately reads all KPI values from the provided inputs
- [ ] Correctly identifies schedule risk (2-day and 2-week)
- [ ] Flags bad, missing, or contradictory data reliably
- [ ] Prioritizes schedule over all other metrics in every output
- [ ] Produces a clear, actionable brief without filler
- [ ] Assigns the right owner to every accountability item
- [ ] Aligns with human judgment ≥ 80–90% of the time across reviews

---

## Update Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0.0 | 2026-03-23 | CORTEX | Initial release |

---
*This file is managed by CORTEX. Office agents are read-only. Do not edit locally.*
*To request changes: submit to CORTEX → validation → signed push.*
