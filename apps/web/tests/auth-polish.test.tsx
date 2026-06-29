import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AuthForm } from "@/components/auth/auth-form";
import { ResetForm } from "@/components/auth/reset-form";

const replace = vi.fn();
const signUp = vi.fn();
const params = new URLSearchParams();
let session: object | null = null;
afterEach(cleanup);

vi.mock("next/navigation", () => ({ useRouter: () => ({ replace, refresh: vi.fn() }), useSearchParams: () => params }));
vi.mock("@/lib/supabase/client", () => ({ createClient: () => ({ auth: { getSession: vi.fn().mockImplementation(async () => ({ data: { session } })), updateUser: vi.fn(), signOut: vi.fn(), signInWithPassword: vi.fn(), signUp } }) }));

describe("auth polish", () => {
  beforeEach(() => {
    params.delete("reason");
    params.delete("error");
    session = null;
    vi.clearAllMocks();
  });

  it("explains an expired session without a dead end", () => {
    params.set("reason", "session-expired");
    render(<AuthForm mode="login"/>);
    expect(screen.getByText(/session expired/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
  });

  it("requires matching password confirmation during signup", async () => {
    render(<AuthForm mode="signup"/>);
    expect(screen.getByLabelText("Confirm password")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Work email"), { target: { value: "owner@example.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "strong-pass-1" } });
    fireEvent.change(screen.getByLabelText("Confirm password"), { target: { value: "different-pass" } });
    fireEvent.click(screen.getByRole("button", { name: "Create account" }));
    expect(await screen.findByText("Passwords do not match")).toBeInTheDocument();
    expect(signUp).not.toHaveBeenCalled();
  });

  it("shows invalid reset-link recovery", async () => {
    render(<ResetForm/>);
    expect(await screen.findByText(/invalid or expired/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Request another link" })).toBeInTheDocument();
  });

  it("renders password fields for a valid recovery session", async () => {
    session = { access_token: "token" };
    render(<ResetForm/>);
    await waitFor(() => expect(screen.getByLabelText("New password")).toBeInTheDocument());
    expect(screen.getByLabelText("Confirm new password")).toBeInTheDocument();
  });
});
