import { AlertTriangle, BarChart2 } from "lucide-react";
import { Card } from "../ui/card";

interface ChartEmptyStateProps {
  type: "empty_data" | "unsupported_type";
  chartType?: string;
}

export function ChartEmptyState({ type, chartType }: ChartEmptyStateProps) {
  if (type === "unsupported_type") {
    // Log to known-issues
    console.warn(`[known-issues] ChartRenderer encountered an unsupported chart type: ${chartType}`);
    return (
      <Card className="w-full h-full min-h-[300px] flex flex-col items-center justify-center p-6 text-center border-dashed border-2 border-[var(--hairline)] bg-[var(--surface-subtle)]/30">
        <AlertTriangle className="text-[var(--warning)] mb-3" size={32} />
        <h3 className="font-medium text-[var(--ink)] mb-1">Unsupported Chart Type</h3>
        <p className="text-sm text-[var(--ink-secondary)]">
          The requested chart type <span className="font-mono bg-[var(--surface)] px-1 rounded">"{chartType}"</span> is not yet supported by this dashboard.
        </p>
      </Card>
    );
  }

  // empty_data
  return (
    <Card className="w-full h-full min-h-[300px] flex flex-col items-center justify-center p-6 text-center border-dashed border-2 border-[var(--hairline)] bg-[var(--surface-subtle)]/30">
      <BarChart2 className="text-[var(--ink-secondary)]/50 mb-3" size={32} />
      <h3 className="font-medium text-[var(--ink)] mb-1">No Data Available</h3>
      <p className="text-sm text-[var(--ink-secondary)]">
        The query returned an empty result set.
      </p>
    </Card>
  );
}
