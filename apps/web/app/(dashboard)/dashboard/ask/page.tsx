import { PageHeader } from "@/components/dashboard/page-header";
import { AskWorkspace } from "@/components/ask/ask-workspace";
export default function Ask(){return <div className="mx-auto max-w-[1400px]"><PageHeader eyebrow="Ask Readout" title="A conversation with your data." description="Every answer is grounded in the active dataset and carries its reasoning forward."/><AskWorkspace/></div>}
