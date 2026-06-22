import { DatasetList } from "../../../components/data/DatasetList";

export default function DataSourcesPage() {
  return (
    <div className="py-8 px-4 w-full h-full overflow-y-auto">
      <div className="max-w-5xl mx-auto mb-8">
        <h1 className="text-3xl font-bold text-[var(--ink)] mb-2">Data Sources</h1>
        <p className="text-[var(--ink-secondary)]">Manage your uploaded datasets and their inferred schemas.</p>
      </div>
      
      <DatasetList />
    </div>
  );
}
