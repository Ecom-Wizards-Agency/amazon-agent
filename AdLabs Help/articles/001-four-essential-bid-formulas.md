# Amazon PPC Bid Optimization: 4 Essential Formulas | AdLabs

Source: https://adlabs.app/amazon-ppc-bid-optimization-the-4-essential-formulas-for-optimizing-bids-hitting-your-target-acos/
Captured: 2026-07-26

---

Amazon PPC Tactics & Strategies 
# Amazon PPC Bid Optimization: The 4 Essential Formulas for Optimizing Bids & Hitting Your Target ACOS
June 6, 2023 Andrew Bailiff No comments yet 
Table of Contents 
How to Optimize Your Bids & Hit Your Target ACOS in Amazon PPC 
The 4 Essential Criteria for Bid Optimization 
1️⃣ High ACOS Keywords 
2️⃣ High Spend, Non-Converting Keywords 
3️⃣ Low ACOS Keywords 
4️⃣ Low Visibility Keywords 
A Word on Placement Adjustments 
## How to Optimize Your Bids & Hit Your Target ACOS in Amazon PPC 
One of the biggest challenges that many Amazon sellers face every day is knowing how and when to optimize bids on their Amazon PPC campaigns. 
Contrary to popular belief, where 88% of advertisers prioritize keyword selection over bidding, mastering bid optimization is the key to creating successful and profitable Amazon PPC campaigns. 
To effectively optimize your bids, you need to have a cohesive system in place to deliver consistent results and hit your ACOS targets.  
That’s what this article is about. 
You’ll learn the 4 categories of bid optimizations that you should be analyzing every week, and how to use simple formulas to dial in your bids. 
Let’s get into it. 
## The 4 Essential Criteria for Bid Optimization 
When using other PPC bidding tools, we always felt in the dark about what was happening to our bids (and why).
Most tools use black box algorithms which make it impossible to know what’s going on or how to adjust the settings to get the results you want.
And the “ two week learning curve ” narrative isn’t satisfactory when performance is suffering.
When we started AdLabs, it was pivotal that we practice “white box” principles that let you know exactly what to expect from the bid optimizer so you can better wield it to drive the best performance possible for your accounts.
We optimize bids when keywords fall under any of the 4 criteria:
- High ACOS
- High Spend, Non-Converting
- Low ACOS
- Low Visibility
Let’s break down each category to learn how to calculate your bids in each criteria.
#### 1️⃣ High ACOS Keywords 
Definition: If a keyword’s ACOS is exceeding your Target ACOS. 
For this category of keywords, we recommend calculating what the keyword bid should be in order to hit the Target ACOS.
In order to do this, we suggest using the “ Revenue Per Click ” (RPC)  method.
This method allows you to figure out what you should be paying on a click-by-click basis, based on the revenue you generate on a click-by-click basis, in order to hit your target ACOS.
Formula: Keyword Bid = Revenue Per Click (RPC) * Target ACOS 
Example: 
- Let’s say you have a Target ACOS of 30%
- You would calculate the new bid based on the keyword’s RPC * Target ACOS 
- If the RPC (Sales / Clicks) was equal to $5, your keyword bid to hit a 30% ACOS would be $1.50 ($5 * 0.3 = $1.50) Most of the time, this optimization results in  reducing  the keyword’s bid.
However, you may sometimes see that a bid  increases  from it’s current value even though it is a “High ACOS” keyword.
This is nothing to be concerned about, as the “current bid” isn’t an actual data point but rather a status (e.g., you could have reduced the bid to $0.02 just a few minutes earlier, but that current bid has nothing to do with the keyword’s performance for the selected date range).
The “new bid” for a High ACOS keyword will  always  be lower than the keyword’s CPC for the selected date range as we optimize to hit the target ACOS.
#### 2️⃣ High Spend, Non-Converting Keywords 
Definition: We consider keywords as “High Spend” when the spend on the keyword exceeds the Target CPA based on the AOV of your product and Target ACOS. 
You would calculate what your Target Cost Per Acquisition (Target CPA) should be based on your Target ACOS and Average Order Value (AOV):
Target CPA = Target ACOS * AOV 
If spend on a keyword exceeds your Target CPA without earning a sale, you know the bid is too high given the current performance.
You would then calculate the bid based on Anticipated Revenue Per Click (similarly to High ACOS keywords) , by referencing the Ad Group’s average conversion rate and AOV.
Example: 
- Target ACOS = 30%
- AOV = $20
- Target CPA = 30% * $20 (i.e., $6)
- “High Spend” threshold = $6.00
- If a keyword’s spend exceeds $6.00 and has no sales, the keyword is considered “High Spend” and the bid should be calculated based on the keyword’s Anticipated RPC * Target ACOS  
Formula: AOV / Current Keyword Clicks * Target ACOS 
Let’s imagine a scenario where a keyword has 10 non-converting clicks and illustrate using the same metrics from the example above.
Example Formula: $20 / 10 (Anticipated RPC) = $2 *0.30 (Target ACOS) 
- Keyword Bid = $0.60 
#### 3️⃣ Low ACOS Keywords 
After years of testing, we have found that bid increases are best executed in small increments rather than large jumps.
So if a keyword has at least one sale and the ACOS is below your Target ACOS, you would simply increase the bid by +5-10% .
How much you increase the bid, whether it be +5%, +10% or even +20% is largely determined by how quickly you want to test the keyword at higher spend velocity and how far below your target ACOS the keyword’s performance is. 
If your target ACOS is 30% and a keyword is performing at 10%,  you could probably be more aggressive on the bid increase. 
Side note: We always recommend having a buffer of a keyword’s ACOS being ~20% below your target ACOS to justify a bid increase.  
For example , if your target ACOS is 30%, you would want to only increase bids on targets that have an ACOS of 24% or lower.
If a keyword is performing at 29% ACOS, and your target is 30%, you might just want to leave that keyword where it is.
Example: 
- Target ACOS = 30%
- “Low ACOS” threshold = 20% lower than 30% (i.e., 24%)
- If a keyword’s ACOS is below 24%, we will increase the bid by +10%
#### 4️⃣ Low Visibility Keywords 
We classify “low visibility keywords” as those which have fewer clicks than is necessary to earn a sale.
This is called the average Clicks-to-Conversion  (aCTC) which is calculated as Clicks divided by Orders.
Example: 
- Average Clicks-to-Conversion = 10 clicks
- “Low Visibility” threshold = 10% fewer than 10 clicks (i.e., 9 clicks)
- If a keyword has fewer than 9 clicks, we will increase the bid by 5%
It is possible for a keyword to fall under  both  the Low Visibility and Low ACOS conditions (e.g., a keyword with 1 click and 1 sale).
In these scenarios, the “Low ACOS” condition trumps and the keyword should be optimized accordingly.
## A Word on Placement Adjustments 
Please keep in mind that when changing bids, you also need to consider any adjustments to placement modifiers. 
In AdLabs, we assign a unique “Campaign Placement Modifier” to every single campaign, which functions as an additional variable in our keyword bidding calculations.
This means the bid optimization output may differ slightly from what you might calculate if you were to use the exact same formulas mentioned above.
As much as we aim to be transparent with our bidding solution, the exact math behind our “Campaign Placement Modifier” variable is something we believe gives us (and our users) a  strong advantage  over competing brands and softwares.
We therefore treat this specific element as a trade secret to maintain the competitive edge for all AdLabs users.
To learn more about the calculations for the placements themselves, sign up for AdLabs and we’re happy to share.
Searching for Better Amazon PPC Results? 
Discover how the auto-manual "hybrid" approach to Amazon PPC instantly improves performance
Start free trial 
Comparing Amazon PPC tools? Check out our side-by-side tool comparisons to find the right fit for your business.
- amazon ppc bid optimization 
- Amazon Ads Strategy 
- Amazon Advertising 
- amazon advertising strategy 
- Amazon Campaign Management 
- amazon fba 
- Amazon Keyword Bidding 
- Amazon PPC 
- amazon ppc bidding 
- Amazon PPC Bidding Tips 
- amazon ppc optimization 
- amazon ppc software 
- amazon ppc strategy 
- amazon seller 
- Amazon Sponsored Products 
- best amazon ppc software 
Andrew Bailiff 
Co-Founder & CMO at AdLabs
