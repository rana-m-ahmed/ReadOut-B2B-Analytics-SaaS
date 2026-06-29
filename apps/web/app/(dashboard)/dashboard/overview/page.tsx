import { PageHeader } from "@/components/dashboard/page-header";
import { OverviewWorkspace } from "@/components/dashboard/overview-workspace";
import { Badge } from "@/components/ui/states";

export default function Overview() {
  return <div className="mx-auto max-w-[1400px]"><PageHeader eyebrow="Workspace pulse" title="Good morning. Here’s the signal." description="A resilient overview of your active dataset and the decisions worth carrying forward." action={<Badge tone="success">Data connected</Badge>}/><OverviewWorkspace/></div>;
}
