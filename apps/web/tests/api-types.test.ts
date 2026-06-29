import { describe, expect, it } from "vitest";
import { Anomaly, Ask, Insight } from "@/lib/api/types";

const id = "17fb30c1-5211-4c81-bdb7-502219f200d1";

describe("API response contracts", () => {
  it("accepts non-persistent overview answers", () => {
    const result = Ask.safeParse({
      answer_id: id,
      session_id: null,
      summary: "The result is $1.2M.",
      chart: null,
      query_plan: null,
      confidence: "high",
      suggested_followups: [],
      clarification_required: null,
      debug_sql: null,
    });
    expect(result.success).toBe(true);
  });

  it("accepts graceful Ask degradation", () => {
    const result = Ask.safeParse({
      answer_id: null,
      session_id: null,
      summary: "The analysis engine is temporarily unavailable.",
      chart: null,
      query_plan: null,
      confidence: null,
      suggested_followups: [],
      clarification_required: null,
      debug_sql: null,
    });
    expect(result.success).toBe(true);
  });

  it("accepts nullable insight and anomaly fields returned by the API", () => {
    expect(
      Insight.safeParse({
        id,
        dataset_id: null,
        title: "Revenue insight",
        body: "Revenue changed.",
        insight_type: "trend",
        severity: "info",
        score: null,
        metadata: {},
        created_at: "2026-06-28T00:00:00Z",
      }).success,
    ).toBe(true);
    expect(
      Anomaly.safeParse({
        id,
        dataset_id: null,
        detector_type: "zscore",
        metric_name: null,
        severity: "warning",
        explanation: null,
        anomaly_payload: {},
        created_at: "2026-06-28T00:00:00Z",
      }).success,
    ).toBe(true);
  });
});
