# Customer Features & Signals

These are per-customer metrics computed in the shared feature layer. They power all supervisor and child agent decisions. Each feature has a formula, variables, and anomaly threshold.

---

## a. Spend Decline Flag

**Definition:** Tracks if a customer's spending has declined significantly over a given period.

**Logic:** Compares current spend to historical spending patterns over a defined period (e.g., 30 or 60 days). Flags customers who are spending less for potential recovery actions.

**Formula:**
```
Spend Decline % = ((Previous Spend – Current Spend) / Previous Spend) × 100
```

**Variables:**
- **Previous Spend (PS):** Total spend in the past 30 days (e.g., ₹15,000)
- **Current Spend (CS):** Total spend in the current 30 days (e.g., ₹10,000)

**Threshold:** Flag if Spend Decline % exceeds **20%** over 30 days.

---

## b. Days Since Last Purchase

**Definition:** Calculates the number of days since the customer last made a purchase.

**Logic:** Measures customer inactivity. If value exceeds thresholds (30, 60, 90 days), signals the customer as inactive or dormant.

**Formula:**
```
Days Since Last Purchase = Current Date − Last Purchase Date
```

**Variables:**
- **Current Date (CD):** Today's date
- **Last Purchase Date (LPD):** Date of the last purchase

**Threshold:** Flag if Days Since Last Purchase > **30**.

---

## c. Purchase Frequency

**Definition:** Measures how frequently a customer makes a purchase within a given period.

**Logic:** A decrease in frequency indicates the customer is losing interest. Tracks and flags customers with declining purchase frequency.

**Formula:**
```
Purchase Frequency = Total Purchases ÷ Time Window (e.g., 30 days)
```

**Variables:**
- **Total Purchases (TP):** Total number of purchases in the time window
- **Time Window (TW):** Defined time period (e.g., 30 days)

**Threshold:** Flag if Purchase Frequency < **1** purchase per week.

---

## d. Average Order Value (AOV)

**Definition:** The average amount of money spent by a customer per order.

**Logic:** Tracks average value of a customer's orders. A significant drop signals a decrease in customer engagement or shift to lower-value items.

**Formula:**
```
AOV = Total Spend ÷ Total Orders
```

**Variables:**
- **Total Spend (TS):** Total amount spent (e.g., ₹5,000)
- **Total Orders (TO):** Total number of orders (e.g., 10)

**Threshold:** Flag if Current AOV < Previous AOV × **0.8** (20% drop).

---

## e. Spend Velocity

**Definition:** Measures how quickly a customer is spending over a defined period.

**Logic:** Compares how quickly a customer is spending money compared to their previous pattern. A decrease signals disengagement.

**Formula:**
```
Spend Velocity = Total Spend ÷ Time Between Purchases (days)
```

**Variables:**
- **Total Spend (TS):** Total amount spent in a defined period (e.g., ₹2,000)
- **Time Between Purchases (TBP):** Average time interval between two purchases (e.g., 10 days)

**Threshold:** Flag if Spend Velocity < Previous Spend Velocity × **0.7** (30% slower than usual).

---

## f. Lifetime Value (LTV)

**Definition:** The total expected revenue a customer will generate over their entire relationship with the business.

**Logic:** Predictive metric used for targeting high-value customers for loyalty programs or retention strategies.

**Formula:**
```
LTV = Average Purchase Value (APV) × Purchase Frequency (PF) × Customer Lifespan (CL)
```

**Variables:**
- **Average Purchase Value (APV):** Average value of an order (e.g., ₹1,500)
- **Purchase Frequency (PF):** Number of purchases per year (e.g., 4)
- **Customer Lifespan (CL):** Expected number of years a customer will stay active (e.g., 5 years)

---

## g. Churn Score

**Definition:** A score estimating the likelihood of a customer churning based on recent behaviour.

**Logic:** Calculated using machine learning models considering recency, frequency, and monetary factors (RFM). High churn scores flag customers as at risk.

**Formula:**
```
Churn Score = w1 × Recency Score + w2 × Frequency Score + w3 × Monetary Score
```

**Variables:**
- **Recency Score (RS):** Score based on days since last purchase
- **Frequency Score (FS):** Score based on how often a customer buys
- **Monetary Score (MS):** Score based on total spend

**Weights (example):**
- w1 = 0.5 (high weight for recency)
- w2 = 0.3 (medium weight for frequency)
- w3 = 0.2 (lower weight for monetary)

**Threshold:** Flag as **High Churn Risk** if Churn Score > **70**.

---

## h. Dormant Bucket

**Definition:** Classifies customers based on how long they've been inactive.

**Logic:** Groups customers into dormant buckets by days since last purchase to apply different reactivation strategies.

**Formula:**
```
Dormant Status = Current Date − Last Purchase Date
```

**Thresholds:**
- **Bucket 1:** 30–60 days → Low priority
- **Bucket 2:** 60–90 days → Medium priority
- **Bucket 3:** 90+ days → High priority

---

## i. Win-back Eligibility

**Definition:** Identifies customers who are eligible for win-back campaigns.

**Logic:** A customer is eligible for win-back if they have been inactive for a long period (120+ days) but still have significant Lifetime Value (LTV).

**Formula:**
```
Win-back Eligibility = (Days Since Last Purchase > 120) AND (LTV > 2000)
```

**Variables:**
- **LTV:** Lifetime value of the customer
- **Days Since Last Purchase:** Number of days since the last purchase

---

## j. Category Affinity

**Definition:** Measures how strongly a customer is interested in specific product categories.

**Logic:** Tracks which product categories the customer engages with and spends the most on. Helps identify cross-sell opportunities.

**Formula:**
```
Category Affinity = Spend in Category ÷ Total Spend
```

**Variables:**
- **Spend in Category (S):** Total spend in a particular category (e.g., ₹5,000 on electronics)
- **Total Spend (TS):** Total spend across all categories (e.g., ₹10,000)

---

## k. Offer Sensitivity

**Definition:** Measures how sensitive a customer is to promotional offers.

**Logic:** Identifies customers who respond positively to offers (discounts, free shipping, etc.).

**Formula:**
```
Offer Sensitivity = Purchases with Offers ÷ Total Purchases
```

**Variables:**
- **Purchases with Offers (PO):** Number of purchases made with offers (e.g., 6 out of 10)
- **Total Purchases (TP):** Total number of purchases (e.g., 10)

**Threshold:** Flag as **High Sensitivity** if Offer Sensitivity > **60%**.

---

## l. Fatigue Score

**Definition:** Tracks how many campaigns a customer has been exposed to within a given period to identify campaign fatigue.

**Logic:** Customers exposed to many offers in a short time are flagged for fatigue to prevent over-saturation.

**Formula:**
```
Fatigue Score = Number of Campaigns (in time period)
```

**Variables:**
- **Number of Campaigns (NC):** Number of campaigns the customer has been exposed to
- **Time Period (TP):** Time period during which campaigns were received (e.g., 30 days)

**Threshold:** Flag as **High Fatigue** if Fatigue Score > **5**.

---

## m. Sentiment Risk Score

**Definition:** Evaluates how negatively a customer feels based on interactions with support, products, or services.

**Logic:** A high sentiment risk score indicates a customer is likely to churn due to dissatisfaction and triggers recovery strategies.

**Formula:**
```
Sentiment Risk Score = w1 × Negative Feedback Count + w2 × Support Ticket Escalation Count
```

**Variables:**
- **Negative Feedback Count (NFC):** Number of negative feedback entries
- **Support Ticket Escalation Count (STEC):** Number of escalated support tickets

**Threshold:** Flag for recovery action if Sentiment Risk Score > **80**.

---

## n. VIP Flag

**Definition:** Flags customers who generate a significant portion of the business's revenue.

**Logic:** Based on the Lifetime Value (LTV) of the customer. Helps prioritize high-revenue customers for exclusive treatment.

**Formula:**
```
VIP Flag = (LTV ≥ Top 5% LTV Threshold)
```

**Variables:**
- **LTV:** Lifetime value of the customer
- **Top 5% LTV Threshold:** The LTV value representing the top 5% of customers

---

## o. Event Responsiveness

**Definition:** Flags customers who engage with event-based campaigns (e.g., seasonal, holiday promotions).

**Logic:** Tracks how customers respond to seasonal or event-based offers, enabling more effective targeting during future events.

**Formula:**
```
Event Responsiveness = Purchases During Event ÷ Total Purchases
```

**Variables:**
- **Purchases During Event (PDE):** Purchases made during a seasonal or event-related campaign
- **Total Purchases (TP):** Total number of purchases made by the customer

**Threshold:** Flag for future event campaigns if Event Responsiveness > **50%**.

---

## Signal Layer (Derived from Features)

The feature layer produces these decision-ready boolean signals:

| Signal | Meaning |
|--------|---------|
| `spend_decline_flag` | Customer spend dropped significantly |
| `pre_churn_flag` | Customer showing early churn signals |
| `dormant_60_120_flag` | Inactive 60–120 days |
| `lost_120_plus_flag` | Inactive 120+ days |
| `high_value_watch_flag` | High LTV customer needs monitoring |
| `cross_sell_ready_flag` | Category affinity suggests cross-sell opportunity |
| `offer_optimization_needed_flag` | Offer sensitivity warrants offer tuning |
| `campaign_fatigue_flag` | Too many campaigns recently |
| `negative_experience_flag` | Sentiment risk score is high |
| `segment_revenue_drop_flag` | Segment revenue is declining |
| `seasonal_intent_spike_flag` | Seasonal demand spike detected |

> Signals are cheaper to consume than raw data.

---

## Customer Feature Store Schema

One row per customer, updated incrementally.

| Column | Type | Description |
|--------|------|-------------|
| `customer_id` | ID | Unique customer identifier |
| `last_purchase_date` | Date | Date of last purchase |
| `days_since_last_purchase` | Int | Days elapsed since last purchase |
| `purchase_frequency_30d` | Float | Purchase frequency in last 30 days |
| `purchase_frequency_90d` | Float | Purchase frequency in last 90 days |
| `avg_order_value` | Float | Average order value |
| `spend_velocity_30d` | Float | Spend velocity over 30 days |
| `spend_decline_pct` | Float | Spend decline percentage |
| `ltv_current` | Float | Current LTV |
| `ltv_projected` | Float | Projected LTV |
| `churn_score` | Float | Churn risk score (0–100) |
| `dormant_bucket` | Int | Dormancy bucket (1/2/3) |
| `winback_eligibility_score` | Float | Win-back eligibility score |
| `category_affinity_vector` | Vector | Category spend distribution |
| `offer_sensitivity_score` | Float | Offer sensitivity (0–1) |
| `fatigue_score` | Int | Number of recent campaigns |
| `preferred_channel` | String | Email / SMS / App |
| `sentiment_risk_score` | Float | Sentiment risk (0–100) |
| `vip_flag` | Bool | True if top 5% LTV |
| `event_affinity_score` | Float | Event responsiveness score |
| `cooldown_until` | Date | Suppress campaigns until this date |
