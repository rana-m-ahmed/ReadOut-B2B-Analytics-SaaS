import { Asterisk } from "lucide-react";

export function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: React.ReactNode }) {
  return (
    <header className="dashboard-page-header">
      <div>
        <p className="dashboard-eyebrow"><Asterisk size={12}/>{eyebrow}</p>
        <h1>{title}</h1>
        <p className="dashboard-page-description">{description}</p>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </header>
  );
}
