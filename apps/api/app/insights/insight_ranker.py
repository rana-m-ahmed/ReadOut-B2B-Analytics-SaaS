from __future__ import annotations
from app.insights.schemas import InsightCandidate

# Weight configurations for insight ranking, centralized for easy tuning.
WEIGHT_BUSINESS_IMPACT = 3       # Applied if the primary metric is revenue and magnitude is high.
WEIGHT_HIGH_CHANGE = 2           # Applied if the percentage change (growth/decline) is > 15%.
WEIGHT_TOP_CATEGORY = 2          # Applied if the insight is about a top category/region contribution.
WEIGHT_RECENTLY_SEEN = -1        # Applied if the user has seen similar insights recently (history penalty).
WEIGHT_TOO_OBVIOUS = -1          # Applied if the insight is a basic truism or extremely low variance.

def rank_insights(candidates: list[InsightCandidate], history_types: set[str] | None = None) -> list[InsightCandidate]:
    """Scores and sorts candidates based on business impact, significance, novelty, and readability."""
    seen = history_types or set()
    
    for c in candidates:
        score = 0
        
        # 1. Business Impact
        if "revenue" in c.metric_name.lower() or "price" in c.metric_name.lower():
            if isinstance(c.primary_value, (int, float)) and c.primary_value > 10000:
                score += WEIGHT_BUSINESS_IMPACT
                
        # 2. High Change / Statistical Significance
        if c.percent_change is not None:
            if abs(c.percent_change) > 0.15:
                score += WEIGHT_HIGH_CHANGE
            elif abs(c.percent_change) < 0.01:
                score += WEIGHT_TOO_OBVIOUS
                
        # 3. Top Category / Region
        if c.insight_type in ("top_category", "region_contribution"):
            score += WEIGHT_TOP_CATEGORY
            
        # 4. Novelty
        if c.insight_type in seen:
            score += WEIGHT_RECENTLY_SEEN
            
        c.score = score
        
    # Sort descending by score
    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates
