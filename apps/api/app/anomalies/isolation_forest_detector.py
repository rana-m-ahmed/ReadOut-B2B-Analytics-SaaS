from __future__ import annotations
from typing import Any
from uuid import UUID

from sklearn.ensemble import IsolationForest
import numpy as np

from app.analytics.duckdb_engine import execute_dataset_query
from app.analytics.result_formatter import format_results
from app.db.models import DatasetColumn
from app.anomalies.schemas import Anomaly
from app.core.config import Settings

def _find_column(columns: list[DatasetColumn], possible_names: list[str]) -> DatasetColumn | None:
    for c in columns:
        for p in possible_names:
            if p in c.name.lower():
                return c
    return None

def detect_isolation_forest_anomalies(
    workspace_id: UUID,
    dataset_id: UUID,
    columns: list[DatasetColumn],
    settings: Settings
) -> list[Anomaly]:
    """Runs a multivariate isolation forest detector."""
    
    anomalies: list[Anomaly] = []
    
    date_col = _find_column(columns, ["date", "time", "timestamp"])
    if not date_col:
        return []
        
    revenue_col = _find_column(columns, ["revenue", "price", "amount"])
    order_col = _find_column(columns, ["order_id", "transaction_id"])
    discount_col = _find_column(columns, ["discount", "margin"])
    
    if not revenue_col:
        return []
        
    order_agg = f"count(distinct {order_col.name})" if order_col else f"count(*)"
    discount_agg = f"avg({discount_col.name})" if discount_col else "0"
    
    sql = f"""
        SELECT 
            date_trunc('day', {date_col.name}) as d,
            sum({revenue_col.name}) as revenue,
            {order_agg} as orders,
            {discount_agg} as discount
        FROM dataset
        WHERE {date_col.name} IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """
    
    try:
        res = execute_dataset_query(workspace_id, dataset_id, sql, settings=settings)
        if len(res.rows) < 10:
            return [] # Need sufficient history
            
        dates = [row["d"] for row in res.rows]
        features = []
        for row in res.rows:
            features.append([
                float(row["revenue"] or 0),
                float(row["orders"] or 0),
                float(row["discount"] or 0)
            ])
            
        X = np.array(features)
        
        # Isolation Forest
        clf = IsolationForest(contamination="auto", random_state=42)
        preds = clf.fit_predict(X)
        scores = clf.decision_function(X) # lower is more anomalous
        
        # Collect anomaly candidates first
        candidates = []
        for i, pred in enumerate(preds):
            if pred == -1 and scores[i] < -0.1: # Significant anomaly
                candidates.append((i, scores[i]))
                
        # Limit to top 5 most anomalous points (lowest scores)
        candidates.sort(key=lambda x: x[1])
        top_candidates = candidates[:5]
        
        for i, score in top_candidates:
            anomalies.append(Anomaly(
                detector_type="isolation_forest",
                date=str(dates[i]),
                metric_name="multivariate",
                dimension_name=None,
                dimension_value=None,
                actual_value=float(X[i][0]), # revenue
                expected_value=None,
                severity=float(score),
                chart_payload=None
            ))
            
    except Exception as e:
        pass
        
    return anomalies
