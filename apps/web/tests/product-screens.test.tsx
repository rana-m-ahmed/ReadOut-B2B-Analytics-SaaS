import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import Settings from "@/app/(dashboard)/dashboard/settings/page";
import { AnomaliesWorkspace } from "@/components/anomalies/anomalies-workspace";
import { DataSourcesWorkspace } from "@/components/data/data-sources-workspace";
import { InsightsWorkspace } from "@/components/insights/insights-workspace";
import { api } from "@/lib/api/client";

const push = vi.fn();
const replace = vi.fn();
const refresh = vi.fn();
const setActive = vi.fn();
const signOut = vi.fn();
const updateUser = vi.fn();

let active = "11111111-1111-4111-8111-111111111111";
let anonymous = true;

afterEach(cleanup);

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, replace, refresh }),
}));

vi.mock("@/stores/app-store", () => ({
  useAppStore: (selector: (state: unknown) => unknown) =>
    selector({
      activeDataset: active,
      setActiveDataset: setActive,
      colorFor: () => "var(--accent)",
    }),
}));

vi.mock("@/lib/dashboard", () => ({
  getDefaultDashboard: vi.fn().mockResolvedValue(
    "22222222-2222-4222-8222-222222222222",
  ),
}));

vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      getUser: vi.fn().mockImplementation(async () => ({
        data: {
          user: {
            email: anonymous ? undefined : "owner@example.com",
            is_anonymous: anonymous,
          },
        },
      })),
      signOut,
      updateUser,
    },
  }),
}));

vi.mock("@/lib/api/client", () => ({
  api: {
    getDatasets: vi.fn(),
    getProfile: vi.fn(),
    getAnalysisConfig: vi.fn(),
    deleteDataset: vi.fn(),
    getInsights: vi.fn(),
    generateInsights: vi.fn(),
    createWidget: vi.fn(),
    getAnomalies: vi.fn(),
    scanAnomalies: vi.fn(),
    deleteAnomaly: vi.fn(),
  },
}));

const dataset = {
  id: active,
  name: "Sales review",
  description: null,
  source_type: "csv",
  storage_bucket: "data",
  storage_path: "file.csv",
  file_size_bytes: 2048,
  row_count: 1200,
  created_at: "2026-01-01",
  updated_at: "2026-06-27",
};

const profile = {
  dataset_id: active,
  row_count: 1200,
  quality_score: 92,
  warnings: [],
  columns: [
    {
      name: "revenue_safe",
      display_name: "Revenue Total",
      data_type: "number" as const,
      semantic_role: "metric" as const,
      missing_percent: 0,
    },
  ],
};

const insight = {
  id: "33333333-3333-4333-8333-333333333333",
  dataset_id: active,
  title: "Regional mix shifted",
  body: "West contributed more of this period's revenue.",
  insight_type: "mix",
  severity: "high confidence",
  score: 8.2,
  metadata: {},
  created_at: "2026-06-27",
};

const anomaly = {
  id: "44444444-4444-4444-8444-444444444444",
  dataset_id: active,
  detector_type: "zscore",
  metric_name: "Revenue",
  severity: "notable",
  explanation: "Revenue moved below its recent baseline.",
  anomaly_payload: {},
  created_at: "2026-06-27",
};

function renderWithQuery(ui: ReactNode) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("complete product screens", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    active = dataset.id;
    anonymous = true;
    vi.mocked(api.getDatasets).mockResolvedValue([dataset]);
    vi.mocked(api.getProfile).mockResolvedValue(profile);
    vi.mocked(api.getAnalysisConfig).mockResolvedValue({
      dataset_id: active,
      mapping_status: "active",
      active_version: 1,
      primary_time_column_id: null,
      metrics: [],
      dimensions: [],
      suggestions: null,
      columns: [],
      capabilities: {
        can_render_kpis: true,
        can_render_trends: false,
        can_group: false,
        can_scan_anomalies: false,
      },
    });
    vi.mocked(api.deleteDataset).mockResolvedValue(undefined);
    vi.mocked(api.getInsights).mockResolvedValue([]);
    vi.mocked(api.generateInsights).mockResolvedValue([insight]);
    vi.mocked(api.getAnomalies).mockResolvedValue([]);
    vi.mocked(api.scanAnomalies).mockResolvedValue([anomaly]);
    vi.mocked(api.deleteAnomaly).mockResolvedValue(undefined);
  });

  it("renders, switches, expands without leaking internal names, and confirms deletion", async () => {
    render(<DataSourcesWorkspace />);
    expect(await screen.findByText("Sales review")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Use dataset"));
    expect(setActive).toHaveBeenCalledWith(dataset.id);
    fireEvent.click(screen.getByText("Schema"));
    expect(await screen.findByText("Revenue Total")).toBeInTheDocument();
    expect(screen.queryByText("revenue_safe")).not.toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("Delete Sales review"));
    expect(
      screen.getByRole("dialog", { name: "Delete dataset?" }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByText("Confirm"));
    await waitFor(() => expect(api.deleteDataset).toHaveBeenCalledWith(dataset.id));
  });

  it("shows insight empty state and generates a real feed", async () => {
    renderWithQuery(<InsightsWorkspace />);
    expect(await screen.findByText("No significant insights yet")).toBeInTheDocument();
    fireEvent.click(screen.getAllByText("Discover insights")[0]);
    expect(await screen.findByText("Regional mix shifted")).toBeInTheDocument();
    expect(api.generateInsights).toHaveBeenCalledWith(dataset.id);
  });

  it("shows calm anomaly state, scans, reviews, and dismisses", async () => {
    renderWithQuery(<AnomaliesWorkspace />);
    expect(await screen.findByText("No notable deviations found")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Scan anomalies"));
    expect(await screen.findByText("Revenue")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Review"));
    expect(screen.getByRole("dialog", { name: "Signal detail" })).toBeInTheDocument();
    fireEvent.click(screen.getByText("Acknowledge and dismiss"));
    await waitFor(() => expect(api.deleteAnomaly).toHaveBeenCalledWith(anomaly.id));
  });

  it("renders anonymous upgrade and signs out", async () => {
    render(<Settings />);
    expect(await screen.findByText("Anonymous demo")).toBeInTheDocument();
    expect(screen.getByText("Secure this workspace")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Sign out"));
    await waitFor(() => expect(signOut).toHaveBeenCalled());
    expect(replace).toHaveBeenCalledWith("/login");
  });

  it("distinguishes a verified account", async () => {
    anonymous = false;
    render(<Settings />);
    expect(await screen.findByText("Verified account")).toBeInTheDocument();
    expect(screen.queryByText("Secure this workspace")).not.toBeInTheDocument();
  });
});
