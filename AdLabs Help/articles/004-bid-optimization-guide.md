# The Complete Guide to Amazon PPC Bid Optimization | AdLabs

Source: https://adlabs.app/guides/amazon-ppc-bid-optimization-guide/
Captured: 2026-07-26

---

Introduction
## Bidding Covers a Multitude of Sins
The one thing you can do right now that will immediately change the performance of your account is properly optimize your bids.
Not your keyword selection. Not campaign structure . Not match types. Bidding. Get your bids right and an account transforms overnight. Get it wrong and you'll burn budget on high-volume keywords while starving the ones that actually convert.
We manage millions in Amazon ad spend. When we take on a new account, we guarantee that performance will improve enough within 30 days to more than cover our fees — or we will refund the entire cost. That guarantee can exist for one reason: our bidding methodology. Every single time, it's the bids that turn around an account.
"Keyword bidding covers a multitude of sins. Your account could be fully auto campaigns — if the bids are right, the performance will be on target."
Here's a stat that surprised us: when we polled the Amazon PPC community, 88% said keyword selection was more important than bidding. We think that's backwards — and we think the reason is that most people aren't bidding correctly. They're using increase/decrease by X% rules, or blind automation that can't handle seasonality, data scarcity, or placement nuance.
This guide is the complete system. Every formula, every decision framework, every edge case — from the foundational Revenue Per Click model to advanced macro vs. micro strategies. No fluff. Just math, logic, and the frameworks that have driven results across hundreds of accounts.
💡 How to Use This Guide
Read it front to back for the full picture, or jump to a specific section when you need it. Each part builds on the previous ones, but the formulas and decision frameworks in each section stand on their own as reference material.
Part 1
## The Bidding Philosophy
### Why Bidding Beats Keyword Selection
Think of it this way: imagine you took over an account and could only change one thing — the keywords or the bids. Which one would make a bigger impact?
If you pick the best keywords in the world but the bids are wrong, you'll either get zero impressions (bids too low) or bankrupt the account (bids too high). But if you inherit mediocre keywords and set the bids correctly, the formulas will naturally increase spend on everything relevant and decrease spend on everything irrelevant. The account will self-optimize.
Keyword selection determines which queries you show up on. Bidding determines everything else — which placements you win, how much you spend per click, whether you hit your ACOS target, and ultimately whether your ads are profitable.
### The Problem with "Increase/Decrease by X%"
The most common bidding approach in the industry is rule-based: if ACOS is above target, decrease bids by 10%. If ACOS is below target, increase by 10%. Rinse, repeat.
This is fundamentally flawed for three reasons:
- It's slow. If a keyword has a 500% ACOS, decreasing by 10% per week means you'll burn through cash for months before reaching your target. The RPC formula gets you there in one move. 
- It's frequency-dependent. If you run your rules daily instead of weekly, a keyword that got no new data will still get its bid reduced 7 times. The data didn't change, but the bid was continually cut every day. RPC doesn't have this problem — you can run it hourly and the output is always the same if the data hasn't changed. 
- It's arbitrary. Why 10%? Why not 5% or 20%? The percentage is a guess. RPC calculates the exact bid needed to hit your target ACOS based on the keyword's actual performance data. 
⚠️ Common Mistake
Applying percentage-based bid rules to your current bid instead of your current CPC. The bid is a status — it's whatever it happens to be set to right now. The CPC is actual performance data from your selected time frame. Always calculate from CPC, never from bid.
### Use Math, Not Hunches
A core principle: every optimization should be mathematically derived. Hunches are fine when math runs out — but math should go first. The formulas in this guide eliminate guesswork for the vast majority of bid decisions. They account for conversion rates, average order values, placement settings, and data confidence. Hunches only begin where math ends.
Part 2
## The Revenue Per Click Formula
This is the foundational formula for everything. If you learn nothing else from this guide, learn this.
AdLabs campaign bid optimizer advanced settings allow for tailored optimizations, limits, and parameters. 
### The Core Concept
ACOS is spend divided by sales. At a keyword level, that's the same as CPC (Cost Per Click) divided by RPC (Revenue Per Click):
Keyword ACOS
Keyword ACOS = CPC ÷ RPC
Where RPC = Total Keyword Sales ÷ Total Keyword Clicks.
If your target ACOS is 30%, you need your CPC to be 30% of your RPC. Cross-multiply and you get the formula that drives everything:
The Core Formula
Target CPC = RPC × Target ACOS
Or equivalently:
Alternative Form
Target CPC = (Sales ÷ Clicks) × Target ACOS
### A Worked Example
Say a keyword has $100 in sales, 10 clicks, and a current CPC of $2. Your target ACOS is 30%.
- RPC = $100 ÷ 10 = $10 
- Target CPC = $10 × 0.30 = $3.00 
Your current CPC is $2, so you're actually underbidding. You can push that bid up to capture more traffic while staying within your ACOS target. If the CPC was $5 instead, you'd know immediately that it needs to start working its way down to $3.
🔑 Key Insight
The RPC formula doesn't increase or decrease by an arbitrary percentage. It calculates the exact target CPC needed to hit your target ACOS — based on how the keyword is actually performing. You can run it as many times as you want; as long as the underlying data hasn't changed, the output is the same.
### An Equivalent Mental Math Shortcut
Here's another way to think about it that's useful for quick mental math when you're scanning the ad console:
Mental Math Version
Target CPC = Current CPC × (Target ACOS ÷ Current ACOS)
If the current ACOS is 60% and your target is 30%, the ratio is 0.5 — cut the CPC in half. This gets you the same number as the RPC formula. We find the ratio version faster for mental math; the RPC version is more natural in spreadsheets.
### Critical Distinction: CPC vs. Bid
Your bid and your CPC are not the same thing. You might bid $10 but only pay $0.51 because you're the highest bidder by a mile. The ACOS data reflects CPCs, not bids. So always calculate from CPC data — never from the current bid.
If the bid was recently changed (by you, your client, or automation), the ACOS and CPC in your data still reflect the old bid period. Applying the formula to the current bid would be a mistake — you'd be operating on a status, not on data.
🚩 Red Flag
If someone reduced all bids to $0.05 yesterday, the 30-day ACOS still shows historical performance at the old CPCs. Reducing further because "ACOS is still high" would collapse the account. The bid is a status. The CPC is data. Calculate from data.
Part 3
## The 4 Criteria for Making Bid Changes
Every keyword in your account falls into one of four categories. Each category uses a different formula. The first two are for reducing spend . The last two are for increasing spend .
📉
1. High ACOS
High spend, high ACOS keywords. Use the RPC formula to calculate the exact bid that hits your target.
🚫
2. High Spend, No Sales
Lots of clicks, zero conversions. Use the CPA-based formula to anticipate the next conversion.
👀
3. Low Visibility
Low spend, low impressions. Step up bids 10–20% to test whether more traffic is available.
🎯
4. Low ACOS
Performing below target — room to push. Increase bids 5–25% to capture more sales at good efficiency.
Video Tutorial
Watch: A walkthrough of all four bid change criteria — when to reduce, when to increase, and which formula to use for each scenario.
### Criteria 1: High ACOS Keywords (Reduce Bids)
This is the most impactful formula. Apply it to every keyword with an ACOS above your target (we typically use a 10% grace range — so if your target is 30%, we start optimizing anything above ~33%).
The formula is simply the RPC model from Part 2:
High ACOS Bid Calculation
New Bid = (Keyword Sales ÷ Keyword Clicks) × Target ACOS
### Criteria 2: High Spend, Non-Converting (Covered in Part 4)
Keywords with significant spend but zero sales require a modified approach. Full breakdown in the next section.
### Criteria 3: Low Visibility (Increase Bids by X%)
Keywords with very few clicks or impressions. They're not generating enough data to calculate an RPC. The solution: increase bids by 10–20% to win better placements and attract more traffic.
This is the one scenario where we use the percentage-based step-up method — because there isn't enough conversion data to calculate a precise bid. We step up incrementally until the keyword generates enough data to be optimized with the RPC formula.
### Criteria 4: Low ACOS Keywords (Increase Bids Cautiously)
Keywords performing well below your target ACOS have room to grow. But we don't use the RPC formula here — many low ACOS keywords have very few clicks (1–2), which would produce absurdly high RPC values.
Instead, we increase bids by 5–25% per iteration , inching up to test whether more aggressive bidding can capture additional sales at the same efficiency. The bid increases approach — but never exceed — the maximum affordable CPC (the bid ceiling based on target ACOS). More on bid ceilings in Part 6.
💡 Pro Tip
We typically run either the decrease formulas (Criteria 1 & 2) or the increase formulas (Criteria 3 & 4), depending on account pacing. If ACOS is running hot and spend is high, focus on decreases. If ACOS is healthy and you want to grow, run the increases. This push-and-pull approach gives you more control than running all four simultaneously.
✦ ADLABS FEATURE
#### RPC-Based Bidding Built In — Every Bid Calculated from First Principles
AdLabs calculates your bid for every keyword using Revenue Per Click × target ACOS — no guesswork, no rules like "decrease by 10% if ACOS is high." The right bid, derived from your actual performance data, every time.
Try Free → 
Part 4
## Optimizing Non-Converting Keywords
This is probably the second most impactful formula in the entire system. Keywords with significant spend and zero sales are one of the biggest account-level ACOS killers — but most people handle them wrong.
### The Common (Wrong) Approaches
- Archive everything with $20+ spend and no sales. Where did $20 come from? It's arbitrary. A $200 product can afford $60 per acquisition. A $15 product can't afford $5. 
- Negate the keyword. You lose any future sales it might generate. If it's a relevant keyword, the problem isn't the keyword — it's the bid. 
- Decrease the bid by X%. Slow, imprecise, and frequency-dependent. 
### Step 1: Define "High Spend" Mathematically
Rather than picking an arbitrary spend threshold, calculate your target cost per acquisition (CPA) :
Target CPA
Target CPA = Average Order Value × Target ACOS
Example: if your AOV is $30 and your target ACOS is 33%, your target CPA is $10. That means anything with over $10 in spend and no sales has exceeded the threshold — even if it converted it would be over target ACOS.
This threshold is different for every product, every campaign. A $200 product at a 25% target might have a $50 CPA threshold. A $15 product at 30% has only $4.50. Using math instead of an arbitrary number means your system adapts automatically.
### Step 2: Calculate the Bid Using the Target CPA Formula
The key insight: we still use the RPC concept, but since there are no sales, we substitute the AOV as the anticipated revenue and project forward using the average clicks-to-conversion ratio:
Non-Converting Keyword Bid
Target CPC = Target ACOS × (AOV ÷ (Current Clicks + Avg Clicks to Conversion))
Where Avg Clicks to Conversion = Total Clicks ÷ Total Orders for the campaign (i.e., the inverse of conversion rate).
### Why This Works
The formula anticipates when the next conversion will happen and sets the bid so that when it does convert, you'll be right at your target ACOS. Here's what makes it elegant:
- With each additional non-converting click , the denominator grows, which naturally lowers the bid. The keyword's bids step themselves down automatically — no manual intervention required. 
- If the keyword eventually converts , the bid is already calibrated to hit the target ACOS. 
- If it never converts , the bid slowly approaches the minimum ($0.02) and you can eventually evaluate its relevance to pause or archive, or leave enabled to retest it as your conversion rate improves over time. 
- You can run this as frequently as you want — it's always recalculating from the data, never compounding percentage changes. 
Worked Example: Non-Converting Keyword
Setup: Campaign AOV is $30. Target ACOS is 30%. Average conversion rate is 10% (= 10 clicks to convert). The keyword currently has 15 clicks and zero sales.
- Target CPA = $30 × 0.30 = $9 
- Avg Clicks to Conversion = 10 
- Target CPC = 0.30 × ($30 ÷ (15 + 10)) = 0.30 × $1.20 = $0.36 
If the keyword gets 5 more clicks without converting (now at 20 clicks):
- Target CPC = 0.30 × ($30 ÷ (20 + 10)) = 0.30 × $1.00 = $0.30 
The bid naturally stepped down from $0.36 to $0.30 as more non-converting clicks accumulated. If it does convert on click 25, the total spend to that point will be close to the $9 target CPA.
🔑 Key Insight
Individually, no single low-data keyword is a big offender. But cumulatively, keywords with 1–5 clicks and no sales can constitute 10–20% of total account spend. This formula gives you a systematic way to manage all of them without blindly archiving potentially valuable terms.
Part 5
## When to Increase Bids
Knowing when and how to increase bids is equally important as knowing how to calculate bid reductions — and it's often harder to get right.
### Why Not Just Use RPC to Increase?
On low ACOS keywords with very few clicks, the RPC value is unreliable. A keyword with 1 click and 1 sale at a $0.20 CPC on a $20 product has an RPC of $20. Multiply by a 30% target ACOS and the formula says to set your bid at $6.00. That's dangerous — you'd be assuming a 100% conversion rate holds at a much higher CPC.
Additionally, jumping a bid from $0.10 to $0.50 in one move can throw you into a completely different competitive tier. On broad match or auto campaigns, that higher bid might attract a wider set of search terms with much lower conversion rates.
### The Step-Up Method
For low ACOS and low visibility keywords, increase bids by 5–25% per optimization cycle:
Account Condition 
Increase % 
Rationale 
On target, gentle growth 5–10% Conservative push for incremental volume 
Under pacing budget 10–20% More aggressive to close the gap 
Severely under pacing/launch 15–25% Need velocity now; monitor closely 
### The Grace Range
We use a 10% grace range around the target ACOS. If the target is 30%, anything between 27% and 33% is "on target" — don't touch it. Only optimize outside that range. This prevents unnecessary disruption on keywords that are performing within range.
### When to Increase Bids on High ACOS Keywords
This sounds counterintuitive, but there are some legitimate reasons to increase bids on a keyword that currently shows a high ACOS:
- The bid was previously set wrong. Maybe someone manually nuked the bids. The current bid is too low relative to what the data says the keyword can afford. The RPC formula corrects upward. 
- Performance has improved since the last optimization. Conversion rates went up, so the keyword can now support a higher CPC. The new calculated bid is above the current bid — but still below the historical CPC that caused the high ACOS. 
- Placement adjustments shifted. If you reduced a non-top-of-search placement modifier, the base bid may need to increase to maintain total effective CPC across placements. 
- Strategic ranking decision. You're willing to accept a higher ACOS on specific keywords for market positioning, share-of-voice, or organic ranking benefits. 
💡 Safety Check
For Sponsored Products: if you're increasing a bid on a high ACOS keyword, the new bid should still be below the historical CPC that caused the high ACOS. If it's above, something is wrong with the calculation. Exception: Sponsored Brands, where you may need to over-bid the base keyword to win top-of-search, then decrease non-top-of-search placements.
Part 6
## Bid Ceilings & Why RPC Is King
### The Bid Ceiling Concept
A bid ceiling is the maximum CPC you can afford to pay while staying at or below your target ACOS. It's derived directly from the RPC formula:
Bid Ceiling (Max Affordable CPC)
Max CPC = RPC × Target ACOS
This is the ceiling that low ACOS keyword bid increases should never exceed. When you're stepping bids up 5–25% on well-performing keywords, the RPC-derived ceiling is your hard stop.
### Smart Bid Ceilings for Low-Data Keywords
What about keywords with 1 click and no sales? Their individual RPC is meaningless. The solution: look at the ad group or campaign level to establish a benchmark.
If the ad group averages a $0.75 CPC at a 30% ACOS, that's roughly the ceiling for any individual keyword within it. A keyword with a $2 CPC and 1 click, no sales, is already over that benchmark — don't increase further. A keyword at $0.20 CPC with 1 click, no sales, has room to grow.
The data hierarchy for establishing ceilings:
- Keyword data (if sufficient clicks/sales) 
- Ad group data (if keyword data is insufficient) 
- Campaign data (if ad group is thin) 
- Account-wide data (last resort) 
### Why RPC Is King
Revenue Per Click isn't just a formula — it's a lens for every bidding decision in your account:
- For reducing high ACOS: RPC tells you exactly what the keyword can afford to pay per click. 
- For non-converting keywords: A projected RPC (using AOV) sets the anticipatory bid. 
- For increasing low ACOS: RPC sets the ceiling — never bid higher than what the keyword's revenue can support. 
- For managing investment levels: Lower the target ACOS to slow spend; raise it to accelerate. RPC adjusts all CPCs accordingly. 
- For starting bids: Use the destination ad group's RPC-derived target CPC as the initial bid. 
🔑 Key Insight
The "1X" bid ceiling means bids never exceed the max affordable CPC. Settings like "2X" or "3X" allow bids up to 2–3 times that ceiling — useful for ranking campaigns, but dangerous for profitability. Stick to 1X unless you have a specific strategic reason to go higher.
Part 7
## Placement Adjustments in Tandem
Here's a mistake we see constantly: people optimize keyword bids without touching placement settings, or vice versa. These must be managed simultaneously . Your effective CPC is:
Effective CPC
Effective CPC = Base Bid × Placement Multiplier
It's one bid with a combination of multipliers that produces one CPC. You can't optimize one without the other.
### The Goal: Balanced ACOS Across Placements
If your target ACOS is 30%, you should be hitting approximately 30% on top of search, 30% on rest of search, and 30% on product pages. The spend allocation should scale with where the conversion rates are — more spend on higher-converting placements.
If your top-of-search ACOS is 15% and product pages are 60%, that's not optimized. You're underspending where you convert best and overspending where you don't.
### How Placement Modifiers Work
#### Sponsored Products
Amazon only lets you increase bids for top of search and product pages — you can't decrease. The workaround: decrease all base keyword bids to target the worst-performing placement, then increase for better-performing placements.
Example: product pages convert 50% worse than top of search. You reduce all keyword bids by 50% (targeting the product pages CPC), then increase top of search by 100% to compensate. Net result: appropriate CPCs at every placement.
#### Sponsored Brands
Amazon has updated Sponsored Brands to support placement bid adjustments that more closely mirror Sponsored Products. You can now increase bids for Top of Search (rather than only decreasing for non-TOS placements), which eliminates the old inverted bidding approach.
Previously, SB only let you decrease bids for placements other than top of search. The strategy was to set your base bid high enough to compete for TOS, then use a negative modifier to bring it down everywhere else. That's no longer the only option.
Depending on the ad creative type (video, product collection, store spotlight, etc.), you may see placement modifiers for Top of Search, Rest of Search, and Product Pages — with the ability to increase up to 900%, similar to SP. The base bid serves as your floor, and placement modifiers scale it up for the placements you want to win.
You can also stack placement modifiers with audience-based bid adjustments. Amazon offers three audience segments for SB: New-to-Brand shoppers, Purchased Brand's Product, and Clicked or Added Brand's Product to Cart. This means you can bid aggressively for TOS against non-branded terms and layer on an NTB modifier to further boost bids for first-time customers.
Why "Lower Bids → Higher ACOS" Happens (And How to Fix It)
A common complaint: "I lowered my bids using RPC and my ACOS went up." Here's why.
ACOS is CPC ÷ RPC. The only way ACOS can increase when CPC decreases is if RPC dropped even faster — meaning conversion rates fell. This typically happens for one of two reasons:
- You lost top-of-search placements. Top of search usually has the best conversion rates. When you lowered bids without increasing the top-of-search multiplier, you lost those placements. Now all your spend is on product pages where ACOS is worse. 
- You lost your best search terms. On broad/phrase/auto campaigns, different search terms have different CPCs. The expensive ones might have been the best converters. When you lowered the bid, you kept only the cheap, low-converting traffic. 
The fix: Always adjust placement settings in tandem with bids. And harvest your best search terms into exact match campaigns so you can bid on them independently.
✦ ADLABS FEATURE
#### Placement-Level Data That Tells You Exactly Where to Adjust
AdLabs shows you CVR and RPC by placement — top of search, product pages, rest of search — per campaign and keyword. Know exactly how much to increase your TOS modifier and where to set your base bid, without the guesswork.
Try Free → 
Part 8
## How Often to Optimize
### The Short Answer: Once or Twice a Week
That's the standard cadence for most accounts. It gives enough time between optimizations to collect meaningful data and observe the impact of changes.
### Why Not Daily?
- Not enough data change. If you're using a 30-day lookback window, one additional day barely moves the averages. You'll make the same decisions you made yesterday. 
- Step-up methods compound dangerously. Increasing bids by 10% daily means you double the bid within a week. The data didn't warrant it. 
- Troubleshooting becomes impossible. If ACOS spikes after two weeks of daily changes across thousands of keywords, you can't trace which change caused the problem. 
### When to Optimize More Frequently
- New campaign launches: Check bids 2–4 times in the first week. You're trying to get visibility quickly and may need to adjust starting bids up if impressions are low. 
- Major events: Post-Prime Day, post-deal, significant market shifts. React faster, then return to normal cadence. 
### When to Optimize Less Frequently
- Account performing on target: If it ain't broke, don't fix it. Every 2 weeks or even monthly can be fine for well-dialed accounts with minimal market fluctuation happening. 
- Very low spend / thin data: You need longer windows (60–90 days) just to have enough data to act on. Monthly optimizations may be appropriate. 
- High AOV products with long consideration periods: If your average customer takes 7+ days between clicking and buying, yesterday's data is inherently incomplete. Give it time. 
💡 Pro Tip
You're not just paid to optimize — you're paid to know when not to optimize. There's an art to doing nothing. If sales are growing, ACOS is on target, and trends are positive, sitting on your hands might and just extending budgets might be the right call.
### The Two Things You Cannot Over-Optimize
The RPC-based formulas (Criteria 1: high ACOS, and Criteria 2: non-converting) can be run at any frequency without risk. They recalculate from data every time — running them twice in an hour produces the same output if the data hasn't changed.
The step-up methods (Criteria 3: low visibility, and Criteria 4: low ACOS) are frequency-sensitive. Each run compounds on the previous bid. These should typically only run once per optimization cycle (weekly).
Part 9
## Setting Starting Bids
Whether you're launching a new product , a new campaign, or harvesting keywords — you need a starting bid. There are five methods.
### Method 1: Amazon Suggested Bids (Use with Caution)
Amazon's suggested bid range is your 1st party reference point. It shows the range of low to high, and generally is accurate, but it shouldn't be followed blindly, like using suggested bids as base bids, for example.
### Method 2: Start Low, Inch Up
The most conservative approach. Start at $0.50–$1.00 (or below Amazon's suggested low), then increase 10–20% per cycle until you're getting impressions and clicks. This prevents overspending at launch. It's slower, but it guarantees good ACOS from day one.
### Method 3: Account Average CPC
If your account is healthy, your average CPC is a reasonable proxy for where new bids should land. Adjust up or down based on product price — a $15 product probably needs cheaper clicks than a $200 product.
### Method 4: Converting Search Term CPC
When harvesting keywords, you can use the search term's converting CPC as a starting point. But beware: sometimes converting CPCs are absurdly low (we've seen $0.02 conversions at midnight when all competitors ran out of budget). Starting at $0.02 means you'll need months of step-ups to reach competitive visibility.
Also: if you only harvest low ACOS search terms, you're leaving money on the table. High ACOS search terms often just need a lower bid — harvest them into exact match, apply the RPC formula, and let the math handle it.
### Method 5: Destination Ad Group Target CPC (Best)
The best approach: use the target CPC of the ad group where the keyword is going. This ad group already has performance data, placement settings, and a calculated average CPC. Set the new keyword bid to match that ad group's target, factoring in placement multipliers.
Part 10
## Macro vs. Micro Bid Changes
This is the framework that separates routine maintenance from reactive optimization. Most people only do one type. You need both.
### Macro Bid Changes (Routine Maintenance)
Attribute 
Macro Changes 
Scope Entire account or large campaign groups (80%+ of spend) 
Date Range 30–90 days for high data confidence 
Max Adjustments Tighter — ±10–15% on bids, ±20–33% on placements 
Frequency Every 1–2 weeks 
Risk Level Lower (small individual changes across many keywords) 
Purpose Keep the account tuned. Steady-state optimization. 
When you're optimizing 90%+ of account spend across thousands of keywords, you want conservative adjustment limits. Big swings create volatility — especially on broad/phrase/auto campaigns where bid changes affect which search terms you attract.
### Micro Bid Changes (Targeted Interventions)
Attribute 
Micro Changes 
Scope Specific campaigns, ad groups, or individual keywords (<10% of spend) 
Date Range 7–14 days for recent trends 
Max Adjustments Wider — ±25–50% on bids, unlimited on placements 
Frequency As needed — mid-week, reactive 
Risk Level Higher per keyword, but low total account impact 
Purpose Fix a specific problem. React to a trend. Push an opportunity. 
Micro changes are surgical. You spot a problem — one campaign's ACOS spiked, one keyword lost all its impressions, one product had a deal that changed conversion rates. You zoom in, use a shorter date range to capture the recent shift, and make more aggressive adjustments because the blast radius is small.
### Combining Both
The optimal rhythm:
- Weekly (macro): Run your full-account optimization with a 30-day lookback, conservative limits. This keeps everything tuned. 
- Mid-week (micro, as needed): Spot-check specific campaigns or keywords that are off. Use 7–14 day data. Apply more aggressive adjustments to small pockets of spend. 
💡 AdLabs Pro Tip
When you want to see what the algorithm truly recommends, temporarily remove all max increase/decrease limits and preview the output. Review it for any extreme outliers, adjust the settings if needed, then push through with appropriate guardrails back in place.
### Date Range Selection: The Hidden Art
Your date range isn't just "how many days of data" — it's a tradeoff between data confidence (longer = more reliable) and data relevance (shorter = reflects current conditions).
- Optimizing on January 1? Don't use the last 30 days — December's inflated conversion rates will produce overly aggressive bids for the lower-converting January period. 
- Just finished Prime Day? Don't include Prime Day data in your post-event optimization. Start your window after the event. 
- Start date rule: Your date range should begin after the most recent significant change — whether that's a deal, a bid optimization, a major stock-out, or seasonal shift. 
The most important mindset: you're not optimizing based on what happened — you're optimizing for what's about to happen. Choose a date range whose performance best predicts the near future.
✦ ADLABS FEATURE
#### TACOS Tracking + Bid History in One Dashboard
Track TACOS , organic %, and total sales alongside your bid changes — so you can see the direct impact of bid optimization on your organic rank and business performance. The full picture, not just the ad console view.
Try Free → 
Conclusion
## The Bid Optimization Mindset
### It's Math. Not Magic.
Every formula in this guide boils down to one simple idea: your cost per click should be a calculated percentage of your revenue per click. That's it. Everything else — the four criteria, the non-converting formula, the placement adjustments, the macro/micro framework — is just applying that idea to different scenarios.
### The Complete System at a Glance
Scenario 
Method 
Frequency-Safe? 
High ACOS keywords RPC × Target ACOS ✅ Run anytime 
High spend, no sales CPA-based RPC projection ✅ Run anytime 
Low ACOS keywords Step up 5–25% ⚠️ Once per cycle 
Low visibility keywords Step up 10–20% ⚠️ Once per cycle 
Placements Balance ACOS across all placements ✅ With keyword bids, 1-2X per month 
Full account (macro) 30+ days, conservative limits ✅ Weekly 
Specific issues (micro) 7–14 days, wider limits ✅ As needed 
### Prioritize by Volume Impact
A 100% ACOS on $50 of spend matters less than a 40% ACOS on $5,000 of spend. Always prioritize by dollar impact, not severity percentage. Fix what bleeds real money daily. Monitor what drips.
### Trust the Math, But Stay Human
We believe in being semi-automatic and data-driven, with humans in control. The formulas handle 80% of the work. The remaining 20% — date range selection, optimization frequency, when to hold, when to push — is the art. And that art comes from experience, judgment, and knowing your account.
Bid optimization on Amazon isn't a mystery. It's math. And now you have the complete system.
Use it wisely.
This guide is based on years of managing hundreds of Amazon advertising accounts, combined with deep expertise from That Amazon Ads Podcast and the AdLabs team's proprietary bidding frameworks.
