# Custonomy Multi-Agent Architecture

## Core Principle

**"Process once, decide many times"**

Custonomy must NOT allow every agent to directly scan:
- Customer master
- Orders
- Campaign logs
- Browsing events
- Support tickets
- Delivery/return events

Instead, Custonomy uses a **shared feature layer**, a **shared signal layer**, a **trigger engine**, **supervisor agents** for routing, **child agents** only for shortlisted populations, and a final **Next Best Action** orchestration layer.

---

## Architecture Diagram (8 Layers)

```
Source Data (Customer Data, Orders, Campaign Logs, Feedback, Clickstream)
        ↓
Layer 1: Source Data Layer
        ↓
Layer 2: Shared Feature Computation Layer  ← Databricks sits here
        ↓
Layer 3: Signal Layer
        ↓
Layer 4: Trigger & Eligibility Engine
        ↓
Layer 5: Supervisor Agent Layer
        ↓
Layer 6: Child Agent Layer
        ↓
Layer 7: Next Best Action (NBA) Layer
        ↓
Layer 8: Human Approval & Execution
```

---

## Layer Descriptions

### Layer 1: Source Data Layer
Raw enterprise data enters the platform from:
- Customer Data
- Order transactions
- Browsing / app / web engagement
- Campaign execution logs
- Loyalty data
- Support / complaint / ticket systems
- Product / category / pricing systems
- Seasonal / event calendars

### Layer 2: Shared Feature Computation Layer
Computes reusable features **once**. All agents consume from here.

**Customer feature examples:** last purchase date, purchase frequency, average basket size, spend velocity, spend decline %, LTV, churn score, dormant bucket, win-back eligibility, category affinity, offer sensitivity, preferred channel, fatigue score, sentiment / experience risk, VIP flag, event responsiveness

**Business feature examples:** segment revenue trend, category revenue anomaly, channel performance trend, campaign overlap rate, discount dependency trend, seasonal demand index, event demand uplift

> This layer is the foundation for all agents.

### Layer 3: Signal Layer
The feature layer produces **decision-ready signals** (boolean flags). Signals are cheaper to consume than raw data.

Key signals: `spend_decline_flag`, `pre_churn_flag`, `dormant_60_120_flag`, `lost_120_plus_flag`, `high_value_watch_flag`, `cross_sell_ready_flag`, `offer_optimization_needed_flag`, `campaign_fatigue_flag`, `negative_experience_flag`, `segment_revenue_drop_flag`, `seasonal_intent_spike_flag`

### Layer 4: Trigger & Eligibility Engine
Determines who actually needs processing. Instead of scoring everyone every time, asks:
- Did something materially change?
- Did a threshold get crossed?
- Did a milestone occur?
- Did a business anomaly appear?

**Example triggers:**
- Customer inactive for 30 / 60 / 120 days
- Spend decline exceeds 20%
- Delivery failure occurred
- Support complaint logged
- Campaign proposed for launch
- Category revenue dropped beyond baseline
- Seasonal demand spike detected
- New order changes category affinity

> Only records that meet triggers move forward.

### Layer 5: Supervisor Agent Layer
Supervisors own business domains and route work to child agents. They do **not** deeply analyze all customers. They first perform lightweight routing logic, then invoke only relevant child agents.

### Layer 6: Child Agent Layer
Child agents execute only on:
- Shortlisted customers
- Shortlisted campaigns
- Shortlisted segments
- Shortlisted categories

They consume feature tables and signals, **not raw source data**.

### Layer 7: Next Best Action (NBA) Layer
The master decision layer. Does not rescan all data. Consumes already-prepared outputs from supervisors and child agents and decides:
- What to do
- When to do it
- Through which channel
- Whether to suppress all actions

### Layer 8: Human Approval & Execution
Every final recommendation goes to:
- User review
- Approval / modification / rejection
- Downstream activation

This stays aligned with the human-in-the-loop model.

---

## Supervisor and Child Agent Design

### A. Revenue Recovery Supervisor
**Purpose:** Recover revenue from declining, inactive, or lost customers.

**Routing logic:**
- Active but declining → Churn Prevention Agent
- Inactive 60–120 days → Dormant Customer Activation Agent
- Inactive 120+ days → Win-Back Strategy Agent

**Child agents:** Churn Prevention Agent, Dormant Customer Activation Agent, Win-Back Strategy Agent

**Compute rule:** Only one child agent should run per customer in most cases.

---

### B. Customer Value Growth Supervisor
**Purpose:** Grow value from existing customers.

**Routing logic:**
- Mid-tier with upside → Loyalty Growth Agent
- Ready for adjacent category / premium move → Cross-Sell & Upsell Intelligence Agent
- Investment allocation decision needed → Customer Lifetime Value Optimization Agent

**Child agents:** Loyalty Growth Agent, Cross-Sell & Upsell Intelligence Agent, Customer Lifetime Value Optimization Agent

**Compute rule:** CLV and growth opportunity signals should be reused by all three, not recalculated separately.

---

### C. Campaign Intelligence Supervisor
**Purpose:** Validate and optimize campaign plans before launch.

**Routing logic:**
1. First predict performance
2. If viable, optimize incentives
3. Before approval, run risk / fatigue guardrails

**Child agents:** Campaign Outcome Prediction Agent, Offer Optimization Agent, Campaign Risk & Fatigue Agent

**Compute rule:** Campaigns should be evaluated at campaign/audience level first, not customer-by-customer unless necessary.

---

### D. Customer Experience Guardian Supervisor
**Purpose:** Protect customers from experience-driven attrition.

**Routing logic:**
- Negative experience detected → Customer Sentiment & Experience Agent
- Same customer is high-value / VIP → High-Value Customer Protection Agent escalation

**Child agents:** Customer Sentiment & Experience Agent, High-Value Customer Protection Agent

**Compute rule:** This should be highly event-driven, not periodic full scans.

---

### E. Revenue Intelligence Supervisor
**Purpose:** Detect emerging revenue loss and understand where it is happening.

**Routing logic:**
- Decline detected in category / segment / cohort → Revenue Loss Detection Agent
- If pattern unclear or new behavior emerges → Segment Discovery Agent

**Child agents:** Revenue Loss Detection Agent, Segment Discovery Agent

**Compute rule:** Primarily segment-level and cohort-level processing, not full customer-level rescoring.

---

### F. Seasonal Demand Intelligence Supervisor
**Purpose:** Improve event and seasonal planning.

**Routing logic:**
- Seasonal/event window approaching → Seasonal & Event Intelligence Agent
- If new behavior cluster appears → Segment Discovery Agent support

**Child agents:** Seasonal & Event Intelligence Agent, Segment Discovery Agent

**Compute rule:** Mostly weekly or periodic, with event-specific intensification.

---

### G. Master Orchestrator — Next Best Action Agent
**Purpose:** Choose the single best action or no action.

**Input sources:**
- Revenue Recovery Supervisor output
- Customer Value Growth Supervisor output
- Campaign Intelligence Supervisor output
- Experience Guardian Supervisor output
- Revenue Intelligence Supervisor output
- Seasonal Intelligence Supervisor output

**Compute rule:** Should consume prepared recommendations and suppression rules only.

---

## Processing Strategy by Compute Cost

### Tier 1: Cheap Rules — Use on large populations
Purpose: Reduce the candidate pool.

Examples: days since last purchase, spend drop threshold, campaign count in last 14 days, top 10% LTV flag, complaint count, event responsiveness flag

### Tier 2: Medium-cost Scoring — Use only on eligible populations
Purpose: Rank and prioritize.

Examples: churn score, reactivation probability, win-back feasibility, offer sensitivity, CLV opportunity score, fatigue risk score

### Tier 3: Expensive Decisioning / Reasoning — Use only on top candidates
Purpose: Produce actionable recommendations.

Examples: tailored intervention recommendation, departure reason diagnosis, campaign scenario simulation, final next-best-action resolution

---

## Invocation Policy (General Rules)

1. No child agent should scan raw enterprise tables directly.
2. All child agents must consume precomputed features/signals.
3. A child agent should run only if trigger conditions are satisfied.
4. Where child agents are mutually exclusive, only one should run.
5. Expensive reasoning should happen only after eligibility filtering.
6. The NBA agent should combine outputs, not restart analysis.

---

## Processing Cadence

| Cadence | Use For | Examples |
|---------|---------|---------|
| Real-time / near real-time | Urgent or event-based actions | Delivery failures, complaints/tickets, cart abandonment, VIP customer deviation, active campaign suppression decisions |
| Daily | Operational customer intelligence | Spend decline, churn screening, dormant screening, cross-sell readiness, fatigue updates, category affinity refresh |
| Weekly | Deeper optimization | CLV optimization refresh, segment discovery, offer sensitivity recalibration, seasonal/event demand shifts |
| Monthly | Strategic recalibration | Model retraining, threshold updates, policy tuning, long-term segment evolution |

---

## Event-Driven Optimization Model

Recommended event types (each updates features incrementally, not full platform rescans):

| Event | Trigger |
|-------|---------|
| `OrderPlaced` | Update purchase frequency, AOV, category affinity |
| `SupportComplaintLogged` | Update sentiment risk score |
| `ProductViewed` | Update browsing affinity |
| `CartAbandoned` | Trigger abandonment recovery |
| `CampaignPlanned` | Campaign Intelligence Supervisor |
| `CampaignSent` | Update fatigue score |
| `LoyaltyTierChanged` | Update VIP flag, LTV |
| `InactivityMilestoneReached` | Trigger dormant/win-back flow |
| `SegmentRevenueDropDetected` | Revenue Intelligence Supervisor |
| `SeasonalSignalDetected` | Seasonal Demand Intelligence Supervisor |

---

## Architecture Summary Table

| Layer | Purpose | Compute Style | Output |
|-------|---------|--------------|--------|
| Source Data | Capture raw enterprise data | Ingestion only | Raw records |
| Feature Layer | Compute reusable metrics once | Batch + incremental | Feature tables |
| Signal Layer | Convert features into business signals | Lightweight | Eligibility flags |
| Trigger Engine | Identify records needing action | Rule-based | Candidate sets |
| Supervisor Layer | Route to right decision domain | Lightweight orchestration | Routed workloads |
| Child Agent Layer | Perform focused analysis | Scoped compute | Recommendations |
| NBA Layer | Resolve conflicts and choose action | Decision orchestration | Final action |
| Human Approval | Review and approve | Manual | Approved execution |

---

## Final Recommended Operating Model

Custonomy should run as a **signal-driven, supervisor-orchestrated, feature-store-backed decision platform**.

That means:
- **Data scanned once**
- **Signals reused everywhere**
- **Supervisors control invocation**
- **Child agents run only when justified**
- **NBA chooses the final action**
- **Human approves execution**

This keeps Custonomy: scalable, explainable, fast, cost-efficient, and enterprise-ready.

---

## Example Execution Flows

### Example 1: Revenue Recovery
1. Daily feature update computes spend decline and inactivity windows.
2. Trigger engine finds customers with: 20%+ spend decline, 60+ days inactivity, or 120+ days inactivity.
3. Revenue Recovery Supervisor routes: decline → Churn Prevention, 60–120 → Dormant Activation, 120+ → Win-Back.
4. Each child agent produces recommendation only for assigned customers.
5. NBA decides whether to trigger recovery, cross-sell, or no action.

### Example 2: Campaign Planning
1. Marketer drafts campaign.
2. Campaign Intelligence Supervisor starts processing.
3. Outcome Prediction Agent estimates likely performance.
4. Offer Optimization Agent recommends best incentive structure.
5. Risk & Fatigue Agent validates overlap, fatigue, and discount dependency.
6. Final optimized campaign goes to NBA or approval workflow.

### Example 3: Experience Recovery
1. Delivery delay event lands in platform.
2. Customer experience features update immediately.
3. Trigger engine checks severity + customer value.
4. Experience Supervisor routes: standard customer → Sentiment & Experience Agent; VIP customer → High-Value Protection escalation.
5. Recovery recommendation goes to approval.
