# Business Features

These are segment-level and category-level metrics computed in the shared feature layer. They power business intelligence supervisors and campaign intelligence agents.

---

## 1. Segment Revenue Trend

**Definition:** Measures the change in revenue over time for a specific customer segment (e.g., high-value segment or a particular geographic region).

**Logic:** Compares the current revenue of a segment with its past performance over a predefined time window. A significant decline could signal churn, dissatisfaction, or external factors (seasonal shifts, competitor action).

**Formula:**
```
Segment Revenue Trend = (Current Segment Revenue − Previous Segment Revenue) ÷ Previous Segment Revenue × 100
```

**Variables:**
- **Current Segment Revenue (CSR):** Revenue from the segment in the current period (e.g., ₹20,000)
- **Previous Segment Revenue (PSR):** Revenue from the same segment in the previous period (e.g., ₹25,000)

**Threshold:** Flag if Segment Revenue Trend < **-10%** (10% drop).

---

## 2. Category Revenue Anomaly

**Definition:** Detects significant revenue shifts within specific product categories (e.g., electronics, fashion) compared to baseline or historical data.

**Logic:** Tracks the revenue of a specific category over time. If revenue deviates significantly from the expected trend, it signals a potential issue like declining demand, inventory issues, or competitive pressure.

**Formula:**
```
Category Revenue Anomaly = ((Current Category Revenue − Historical Category Revenue) ÷ Historical Category Revenue) × 100
```

**Variables:**
- **Current Category Revenue (CCR):** Revenue from a specific category (e.g., ₹50,000 in electronics)
- **Historical Category Revenue (HCR):** Average revenue for the category over a defined period (e.g., ₹60,000)

**Threshold:** Flag if Category Revenue Anomaly < **-20%** (20% decline).

---

## 3. Channel Performance Trend

**Definition:** Tracks the performance changes of different marketing channels (e.g., email, SMS, app notifications) over time.

**Logic:** Tracked by metrics such as conversion rate (CVR), click-through rate (CTR), or revenue generated. A decline may signal ineffective messaging, channel saturation, or poor customer engagement.

**Formula:**
```
Channel Performance Trend = (Current Channel Performance − Previous Channel Performance) ÷ Previous Channel Performance × 100
```

**Variables:**
- **Current Channel Performance (CCP):** Performance metric for the current period (e.g., CTR = 3%)
- **Previous Channel Performance (PCP):** Performance metric for the previous period (e.g., CTR = 5%)

**Threshold:** Flag if Channel Performance Trend < **-10%** (10% drop).

---

## 4. Campaign Overlap Rate

**Definition:** Measures the overlap of customers targeted by multiple marketing campaigns in a given time frame, which could lead to message fatigue or customer dissatisfaction.

**Logic:** Compares the audience targeted by current and past campaigns. High overlap means the same customers are being targeted by multiple campaigns, causing over-communication or campaign fatigue.

**Formula:**
```
Campaign Overlap Rate = (Number of Customers Targeted by Both Campaigns ÷ Total Customers Targeted by Current Campaign) × 100
```

**Variables:**
- **Customers Targeted by Both Campaigns (CTB):** Customers who received both campaigns (e.g., 3,000)
- **Total Customers Targeted by Current Campaign (CTC):** Total customers targeted in the current campaign (e.g., 10,000)

**Threshold:** Flag if Campaign Overlap Rate exceeds **30%**.

---

## 5. Discount Dependency Trend

**Definition:** Tracks how dependent a customer or segment is on discounts to make purchases, which can lead to margin erosion over time.

**Logic:** Measures the frequency with which customers or segments respond to discount offers. If customers become too reliant on discounts, it erodes the perceived value of products and leads to reduced margins.

**Formula:**
```
Discount Dependency Trend = (Number of Discount-Driven Purchases ÷ Total Purchases) × 100
```

**Variables:**
- **Number of Discount-Driven Purchases (DDP):** Purchases made using a discount (e.g., 50 purchases)
- **Total Purchases (TP):** Total number of purchases (e.g., 200 purchases)

**Threshold:** Flag if Discount Dependency Trend > **40%**.

---

## 6. Seasonal Demand Index

**Definition:** Measures the strength of demand for products or categories based on seasonality (e.g., holiday shopping, winter fashion).

**Logic:** Calculates how demand for certain products or categories changes according to seasonality trends. Helps businesses understand when to scale up marketing efforts or adjust product offerings based on historical data and seasonal forecasts.

**Formula:**
```
Seasonal Demand Index = (Current Season Demand ÷ Average Historical Demand for the Season) × 100
```

**Variables:**
- **Current Season Demand (CSD):** Current sales or engagement for the season (e.g., ₹100,000 in December)
- **Average Historical Demand (AHD):** Average sales in the same season for previous years (e.g., ₹90,000 in December)

**Threshold:** Flag if Seasonal Demand Index > **115%** (15% increase — demand spike).

---

## 7. Event Demand Uplift

**Definition:** Tracks the increase in demand for specific products or categories during events (e.g., sales, product launches, festivals).

**Logic:** Measures how customer demand for products changes before, during, and after a major event (e.g., Diwali, Black Friday). A significant uplift indicates marketing efforts and timing were effective.

**Formula:**
```
Event Demand Uplift = (Demand During Event ÷ Demand Before Event) × 100
```

**Variables:**
- **Demand During Event (DDE):** Sales or engagement during the event (e.g., ₹50,000 during Diwali sale)
- **Demand Before Event (DBE):** Sales or engagement before the event (e.g., ₹30,000 before Diwali)

**Threshold:** Flag if Event Demand Uplift > **130%** (30% increase).

---

## Segment / Category Feature Store Schema

| Column | Description |
|--------|-------------|
| `segment_id` / `category_id` | Identifier |
| `revenue_baseline` | Historical average revenue |
| `revenue_current` | Current period revenue |
| `anomaly_score` | Revenue anomaly score |
| `seasonal_index` | Seasonal demand index value |
| `demand_spike_flag` | Boolean — spike detected |
| `engagement_shift_score` | Engagement change score |
| `campaign_saturation_score` | Campaign overlap / fatigue score |

## Campaign Feature Store Schema

One row per campaign / audience version.

| Column | Description |
|--------|-------------|
| `campaign_id` | Unique campaign identifier |
| `target_audience_size` | Number of customers targeted |
| `audience_overlap_7d` | Overlap with recent campaigns |
| `fatigue_risk_score` | Audience fatigue risk |
| `predicted_open_rate` | Predicted email open rate |
| `predicted_click_rate` | Predicted CTR |
| `predicted_conversion_rate` | Predicted conversion |
| `predicted_revenue` | Expected revenue from campaign |
| `discount_dependency_risk` | Risk of margin erosion |
| `recommended_offer_type` | Offer type recommendation |
| `recommended_offer_value` | Offer value recommendation |
