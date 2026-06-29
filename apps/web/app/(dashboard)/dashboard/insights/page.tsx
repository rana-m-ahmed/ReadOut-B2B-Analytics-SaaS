import { PageHeader } from "@/components/dashboard/page-header";
import { InsightsWorkspace } from "@/components/insights/insights-workspace";
export default function Insights(){return <div className="mx-auto max-w-[1400px]"><PageHeader eyebrow="Automated discoveries" title="Insights worth a closer look." description="Readout scans for patterns with enough signal to inform a decision."/><InsightsWorkspace/></div>}
