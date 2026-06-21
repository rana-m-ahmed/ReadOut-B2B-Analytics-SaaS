from __future__ import annotations
import json
import httpx
from app.insights.schemas import InsightCandidate
from app.core.config import Settings
from app.analytics.result_formatter import compact_number

async def write_insights(candidates: list[InsightCandidate], settings: Settings, limit: int = 3) -> list[InsightCandidate]:
    """Uses Groq fallback model to generate single-sentence summaries by injecting exact numbers."""
    
    top_candidates = candidates[:limit]
    if not top_candidates:
        return []
    
    for c in top_candidates:
        # Format the exact strings the LLM MUST use
        exact_primary = compact_number(c.primary_value) if isinstance(c.primary_value, (int, float)) else str(c.primary_value)
        exact_pct = f"{c.percent_change * 100:.1f}%" if c.percent_change is not None else None
        exact_comparison = str(c.comparison_value) if c.comparison_value is not None else None
        
        system_prompt = (
            "You are a strict text-substitution writer. You will write exactly ONE sentence.\n"
            "You MUST use the EXACT strings provided below. Do not round, estimate, or change the numbers.\n"
            "Return ONLY the sentence, with no quotes or preamble."
        )
        
        user_prompt = f"Insight Type: {c.insight_type}\nMetric: {c.metric_name}\n"
        user_prompt += f"EXACT Primary Value String: {exact_primary}\n"
        if exact_pct:
            user_prompt += f"EXACT Percent Change String: {exact_pct}\n"
        if exact_comparison:
            user_prompt += f"EXACT Secondary Value String: {exact_comparison}\n"
            
        try:
            api_key = settings.GROQ_API_KEY
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.GROQ_FALLBACK_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.0,
                        "max_tokens": 100
                    },
                    timeout=10.0
                )
            if response.status_code < 400:
                c.text = response.json()["choices"][0]["message"]["content"].strip().strip('"')
            else:
                c.text = f"{c.metric_name} is {exact_primary}."
        except Exception:
            # Fallback to a hardcoded string if LLM fails
            c.text = f"{c.metric_name} is {exact_primary}."
            
    return top_candidates
