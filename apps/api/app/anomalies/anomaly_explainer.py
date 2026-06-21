from __future__ import annotations
import httpx
from app.anomalies.schemas import Anomaly
from app.core.config import Settings
from app.analytics.result_formatter import compact_number

ALARMIST_BLOCKLIST = ["broken", "critical", "failure", "disaster", "collapse", "plummet", "crash", "fatal"]

async def explain_anomaly(anomaly: Anomaly, settings: Settings) -> Anomaly:
    """Uses Groq fallback model to generate an amber-never-red explanation of the anomaly."""
    
    api_key = settings.GROQ_API_KEY
    if not api_key:
        return anomaly
        
    actual = compact_number(anomaly.actual_value)
    if anomaly.expected_value is not None:
        expected = compact_number(anomaly.expected_value)
        diff = anomaly.actual_value - anomaly.expected_value
        pct = (diff / anomaly.expected_value) * 100 if anomaly.expected_value != 0 else 0
        pct_str = f"{abs(pct):.1f}%"
        direction = "down" if diff < 0 else "up"
    else:
        expected = "N/A"
        pct_str = "N/A"
        direction = "different"
        
    system_prompt = (
        "You are an analytics assistant that writes ONE clear, professional sentence explaining an anomaly. "
        "CONSTRAINTS: "
        "1. You MUST use the exact numbers provided below. Do not round or calculate anything. "
        "2. You MUST use neutral, professional 'amber' language. DO NOT use alarmist words like 'broken', "
        "'critical', 'failure', 'crash', or 'plummet'. Instead use phrases like 'worth checking', 'unusual', "
        "'lower than expected', or 'higher than expected'. "
        "3. Return ONLY the sentence with no quotes."
    )
    
    user_prompt = f"Date: {anomaly.date}\nMetric: {anomaly.metric_name}\n"
    if anomaly.dimension_name and anomaly.dimension_value:
        user_prompt += f"Concentrated in: {anomaly.dimension_name} = {anomaly.dimension_value}\n"
    user_prompt += f"Actual: {actual}\nExpected: {expected}\nChange: {direction} {pct_str}\n"
    
    try:
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
            text = response.json()["choices"][0]["message"]["content"].strip().strip('"')
            # Check blocklist
            text_lower = text.lower()
            if any(bad in text_lower for bad in ALARMIST_BLOCKLIST):
                # Fallback to safe string
                anomaly.explanation = f"Unusual {anomaly.metric_name} observed on {anomaly.date} ({direction} {pct_str}, worth checking)."
            else:
                anomaly.explanation = text
        else:
            anomaly.explanation = f"Unusual {anomaly.metric_name} observed on {anomaly.date} ({direction} {pct_str})."
    except Exception:
        anomaly.explanation = f"Unusual {anomaly.metric_name} observed on {anomaly.date} ({direction} {pct_str})."
        
    return anomaly
