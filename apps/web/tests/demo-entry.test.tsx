import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DemoEntry } from "@/components/auth/demo-entry";
import { api } from "@/lib/api/client";

const replace = vi.fn();
const refresh = vi.fn();
const setActiveDataset = vi.fn();
const getSession = vi.fn();
const signInAnonymously = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, refresh }),
}));

vi.mock("@/stores/app-store", () => ({
  useAppStore: {
    getState: () => ({ setActiveDataset }),
  },
}));

vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: { getSession, signInAnonymously },
  }),
}));

vi.mock("@/lib/api/client", () => ({
  api: {
    getDatasets: vi.fn(),
  },
}));

describe("DemoEntry", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("activates the demo dataset before routing into the dashboard", async () => {
    getSession.mockResolvedValue({ data: { session: { access_token: "token" } } });
    vi.mocked(api.getDatasets).mockResolvedValue([
      {
        id: "11111111-1111-4111-8111-111111111111",
        name: "Demo Sales Orders",
        description: "Shared public demo sales dataset",
        source_type: "demo_seed",
        storage_bucket: "readout-datasets",
        storage_path: "users/demo/datasets/demo/raw.csv",
        file_size_bytes: 2048,
        row_count: 1000,
        created_at: "2026-06-27T00:00:00Z",
        updated_at: "2026-06-27T00:00:00Z",
      },
    ]);

    render(<DemoEntry />);

    await waitFor(() =>
      expect(setActiveDataset).toHaveBeenCalledWith("11111111-1111-4111-8111-111111111111"),
    );
    expect(replace).toHaveBeenCalledWith("/dashboard/overview");
    expect(refresh).toHaveBeenCalled();
  });

  it("shows an error and does not route when the demo dataset is unavailable", async () => {
    getSession.mockResolvedValue({ data: { session: { access_token: "token" } } });
    vi.mocked(api.getDatasets).mockResolvedValue([]);

    render(<DemoEntry />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The demo session could not start. Check the public Supabase configuration and try again.",
    );
    expect(replace).not.toHaveBeenCalled();
    expect(setActiveDataset).not.toHaveBeenCalled();
  });
});
