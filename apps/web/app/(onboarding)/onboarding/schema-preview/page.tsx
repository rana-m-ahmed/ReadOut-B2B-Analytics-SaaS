import { OnboardingShell } from "@/components/onboarding/onboarding-shell";
import { SchemaProfile } from "@/components/onboarding/schema-profile";

export default async function SchemaPreview({
  searchParams,
}: {
  searchParams: Promise<{ dataset?: string }>;
}) {
  const { dataset } = await searchParams;

  return (
    <OnboardingShell
      step={2}
      title="Teach Readout what matters"
      description="Review our suggestions, choose the metrics that run your business, and preview the dashboard before activation."
    >
      <SchemaProfile datasetId={dataset} />
    </OnboardingShell>
  );
}
