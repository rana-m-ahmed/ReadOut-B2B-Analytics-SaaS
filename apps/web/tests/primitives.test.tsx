import { useState } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Metric } from "@/components/ui/typography";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Drawer } from "@/components/ui/drawer";

function DrawerHarness() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button onClick={() => setOpen(true)}>Open details</button>
      <Drawer open={open} onOpenChange={setOpen} title="Accessible details">
        <button>Drawer action</button>
      </Drawer>
    </>
  );
}

describe("reskinned primitives", () => {
  it("renders tabular metrics", () => {
    render(<Metric>12,450</Metric>);
    expect(screen.getByText("12,450")).toHaveClass("tabular");
  });

  it("uses Readout tokens", () => {
    const { container } = render(
      <>
        <Button>Go</Button>
        <Card>Data</Card>
      </>,
    );
    expect(container.innerHTML).toContain("var(--accent)");
    expect(container.innerHTML).toContain("var(--radius-card)");
  });

  it("labels drawers, focuses their close control, and restores trigger focus", async () => {
    render(<DrawerHarness />);
    const trigger = screen.getByRole("button", { name: "Open details" });
    trigger.focus();
    fireEvent.click(trigger);

    expect(screen.getByRole("dialog", { name: "Accessible details" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole("button", { name: "Close" })).toHaveFocus());

    fireEvent.keyDown(document, { key: "Escape" });
    await waitFor(() => expect(trigger).toHaveFocus());
  });
});
