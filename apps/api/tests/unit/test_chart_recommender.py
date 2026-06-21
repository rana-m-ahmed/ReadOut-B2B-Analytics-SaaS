from __future__ import annotations

from app.analytics.chart_recommender import recommend_chart_type
from app.analytics.duckdb_engine import QueryColumn, QueryResult

def _col(name: str, type_: str) -> QueryColumn:
    return QueryColumn(name=name, duckdb_type=type_)

def test_recommend_chart_type():
    # date+one metric -> line
    res = QueryResult(rows=[], columns=[_col("d", "DATE"), _col("m", "DOUBLE")])
    assert recommend_chart_type(res) == "line"

    # date+multiple metrics -> multi-line
    res = QueryResult(rows=[], columns=[_col("d", "DATE"), _col("m1", "DOUBLE"), _col("m2", "INTEGER")])
    assert recommend_chart_type(res) == "multi_line"

    # category+metric -> bar
    res = QueryResult(rows=[], columns=[_col("c", "VARCHAR"), _col("m", "DOUBLE")])
    assert recommend_chart_type(res) == "bar"

    # category-share-of-total -> donut
    res = QueryResult(rows=[], columns=[_col("c", "VARCHAR"), _col("m", "DOUBLE"), _col("proportion", "DOUBLE")])
    assert recommend_chart_type(res) == "donut"

    # two numeric columns -> scatter
    res = QueryResult(rows=[], columns=[_col("n1", "DOUBLE"), _col("n2", "DOUBLE")])
    assert recommend_chart_type(res) == "scatter"

    # single metric -> metric card
    res = QueryResult(rows=[], columns=[_col("m", "DOUBLE")])
    assert recommend_chart_type(res) == "metric_card"

    # date+category+metric -> stacked bar
    res = QueryResult(rows=[], columns=[_col("d", "DATE"), _col("c", "VARCHAR"), _col("m", "DOUBLE")])
    assert recommend_chart_type(res) in ("stacked_bar", "multi_line")

    # anomaly-over-time -> line with highlighted point
    res = QueryResult(rows=[], columns=[_col("anomaly_value", "DOUBLE"), _col("baseline_value", "DOUBLE")])
    assert recommend_chart_type(res) == "line_with_highlighted_point"
