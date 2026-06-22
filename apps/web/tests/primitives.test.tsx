import { render, screen, cleanup } from "@testing-library/react"
import { describe, it, expect, afterEach } from "vitest"
import { Card } from "@/components/ui/card"
import { Metric, LabelText } from "@/components/ui/typography"
import { ModalWrapper } from "@/components/ui/modal-wrapper"
import { Button } from "@/components/ui/button"

describe("Design System Primitives", () => {
  afterEach(() => {
    cleanup()
    document.body.style.transform = ""
  })

  it("Card applies --shadow-float and correct background token", () => {
    render(<Card data-testid="card">Card Content</Card>)
    const card = screen.getByTestId("card")
    expect(card.className).toContain("shadow-[var(--shadow-float)]")
    expect(card.className).toContain("bg-[var(--surface)]")
  })

  it("Button applies primary accent token classes by default", () => {
    render(<Button data-testid="button">Click Me</Button>)
    const button = screen.getByTestId("button")
    expect(button.className).toContain("bg-[var(--accent)]")
    expect(button.className).toContain("text-[var(--accent-on)]")
  })

  it("Metric renders with tabular-nums and correct typographic tokens", () => {
    render(<Metric data-testid="metric">1,234</Metric>)
    const metric = screen.getByTestId("metric")
    expect(metric.className).toContain("tabular-nums")
    expect(metric.className).toContain("text-[var(--ink)]")
    expect(metric.className).toContain("tracking-[-0.02em]")
  })

  it("LabelText renders with tabular-nums, uppercase, and ink-secondary", () => {
    render(<LabelText data-testid="label">Revenue</LabelText>)
    const label = screen.getByTestId("label")
    expect(label.className).toContain("tabular-nums")
    expect(label.className).toContain("uppercase")
    expect(label.className).toContain("text-[var(--ink-secondary)]")
  })

  it("ModalWrapper mount triggers backdrop-blur and canvas scale", () => {
    const { rerender } = render(
      <ModalWrapper isOpen={false} onClose={() => {}}>
        <div>Modal Content</div>
      </ModalWrapper>
    )

    // Should not scale initially
    expect(document.body.style.transform).toBe("")

    // Open modal
    rerender(
      <ModalWrapper isOpen={true} onClose={() => {}}>
        <div>Modal Content</div>
      </ModalWrapper>
    )

    // Should scale back the canvas
    expect(document.body.style.transform).toBe("scale(0.98)")
    
    // Check for backdrop blur on the overlay
    const backdrop = screen.getByTestId("modal-backdrop")
    expect(backdrop.className).toContain("backdrop-blur-[8px]")
  })
})
