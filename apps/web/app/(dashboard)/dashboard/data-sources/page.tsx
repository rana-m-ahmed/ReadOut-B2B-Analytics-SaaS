import { PageHeader } from "@/components/dashboard/page-header";
import { DataSourcesWorkspace } from "@/components/data/data-sources-workspace";
export default function DataSources(){return <div className="mx-auto max-w-[1400px]"><PageHeader eyebrow="Data workspace" title="Sources you can trust." description="Connect, review, switch, and safely manage the datasets available to Readout."/><DataSourcesWorkspace/></div>}
