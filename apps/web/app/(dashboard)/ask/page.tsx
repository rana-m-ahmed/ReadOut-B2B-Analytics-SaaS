import { AskThread } from "../../../components/ask/AskThread";
import { AskBar } from "../../../components/ask/AskBar";

export default function AskPage() { 
  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="flex-1 overflow-hidden relative">
        <AskThread />
      </div>
      <div className="shrink-0 pt-4 pb-2 border-t border-[var(--hairline)]">
        <AskBar />
      </div>
    </div>
  ); 
}
