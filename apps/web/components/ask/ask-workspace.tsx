"use client";

import { useCallback, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, Pin, RefreshCw, Send, SlidersHorizontal, Sparkles } from "lucide-react";
import { api } from "@/lib/api/client";
import { queryKeys } from "@/lib/api/queryKeys";
import { getDefaultDashboard } from "@/lib/dashboard";
import { useAppStore } from "@/stores/app-store";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Drawer } from "@/components/ui/drawer";
import { ChartRenderer } from "@/components/charts/chart-renderer";
import type { AskT } from "@/lib/api/types";

type Turn = { q: string; a?: AskT; error?: string };

export function AskWorkspace() {
  const dataset = useAppStore((state) => state.activeDataset);
  const collapsed = useAppStore((state) => state.sidebarCollapsed);
  const session = useAppStore((state) => state.askSession);
  const setSession = useAppStore((state) => state.setAskSession);
  const [question, setQuestion] = useState("");
  const [pending, setPending] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [plan, setPlan] = useState<AskT | null>(null);
  const [pinning, setPinning] = useState(false);
  const [notice, setNotice] = useState("");
  const config = useQuery({
    queryKey: queryKeys.datasets.analysisConfig(dataset ?? "missing"),
    queryFn: () => api.getAnalysisConfig(dataset!),
    enabled: Boolean(dataset),
  });

  const starterQuestion = (() => {
    const active = config.data;
    const primaryMetric = active?.metrics.find((metric) => metric.is_primary) ?? active?.metrics[0];
    const firstDimension = active?.dimensions[0];
    if (!primaryMetric) return "What should I pay attention to in this dataset?";
    if (firstDimension && active?.capabilities.can_render_trends) {
      return `Show ${primaryMetric.label} by ${firstDimension.label} for the last 30 days.`;
    }
    if (firstDimension) {
      return `Break down ${primaryMetric.label} by ${firstDimension.label}.`;
    }
    return `What is ${primaryMetric.label}?`;
  })();

  const submit = useCallback(async (raw: string) => {
    const q = raw.trim();
    if (!dataset || !q || pending) return;
    setPending(true);
    setNotice("");
    setTurns((value) => [...value, { q }]);
    try {
      const answer = await api.ask({ dataset_id: dataset, question: q, session_id: session });
      setSession(answer.session_id);
      setTurns((value) => [...value.slice(0, -1), { q, a: answer }]);
      setQuestion("");
    } catch {
      setTurns((value) => [...value.slice(0, -1), { q, error: "Readout could not answer right now. Please retry shortly." }]);
    } finally {
      setPending(false);
    }
  }, [dataset, pending, session, setSession]);

  async function pin(answer: AskT) {
    if (pinning || !answer.answer_id) return;
    setPinning(true);
    setNotice("");
    try {
      const dashboard_id = await getDefaultDashboard();
      await api.createWidget({ dashboard_id, source_type: "ask_message", source_id: answer.answer_id, title: answer.chart?.title });
      setNotice("Pinned to your overview.");
    } catch {
      setNotice("This answer could not be pinned. Nothing was changed.");
    } finally {
      setPinning(false);
    }
  }

  return (
    <div className="ask-room mx-auto max-w-5xl pb-36">
      <div className="grid gap-6">
        {turns.length === 0 && (
          <Card className="signal-card ask-empty relative overflow-hidden p-8 text-center md:p-14">
            <div className="ask-orbit" aria-hidden="true"><span/><span/><span/></div>
            <span className="relative mx-auto flex size-12 items-center justify-center rounded-full bg-[var(--marketing-violet)] text-white shadow-[0_14px_35px_rgba(96,70,232,.35)]"><Sparkles size={19}/></span>
            <p className="dashboard-section-label relative mt-6">Natural language analysis</p>
            <h2 className="relative mt-3 text-3xl font-semibold tracking-[-.045em] md:text-4xl">What do you want to understand?</h2>
            <p className="relative mx-auto mt-3 max-w-lg text-sm leading-6 text-white/70">Ask a direct business question. Readout resolves it against your schema and returns the evidence with the answer.</p>
            <button className="relative mt-7 inline-flex items-center gap-2 rounded-full border border-white/[.1] bg-white/[.04] px-5 py-3 text-sm font-semibold transition hover:-translate-y-0.5 hover:border-[rgba(168,255,120,.25)] hover:bg-white/[.07]" onClick={() => submit(starterQuestion)}>Try a starter question <ArrowUpRight size={15}/></button>
          </Card>
        )}

        {turns.map((turn, index) => (
          <article key={`${turn.q}-${index}`} className="grid gap-3">
            <p className="max-w-[82%] justify-self-end rounded-2xl rounded-br-md bg-[var(--marketing-violet)] px-4 py-3 text-sm text-white shadow-[0_12px_30px_rgba(96,70,232,.2)]">{turn.q}</p>
            <Card className="signal-card min-w-0 rounded-tl-md p-6 md:p-7">
              {turn.error ? (
                <div role="alert"><p className="font-semibold text-[var(--danger)]">{turn.error}</p><Button className="mt-4" variant="secondary" size="sm" onClick={() => submit(turn.q)}><RefreshCw size={15}/>Retry</Button></div>
              ) : turn.a ? (
                <>
                  <p className="mb-6 max-w-3xl text-lg leading-8 text-white/82">{turn.a.clarification_required?.message ?? turn.a.summary ?? "Readout completed the request but did not return a written summary."}</p>
                  {turn.a.chart && <ChartRenderer payload={turn.a.chart}/>}
                  <div className="mt-5 flex flex-wrap gap-2">
                    <Button size="sm" variant="secondary" onClick={() => pin(turn.a!)} disabled={!turn.a.chart || !turn.a.answer_id || !turn.a.mapping_version || pinning}><Pin size={15}/>{!turn.a.mapping_version ? "Map dataset to pin" : pinning ? "Pinning…" : "Pin chart"}</Button>
                    {turn.a.query_plan && <Button size="sm" variant="ghost" onClick={() => setPlan(turn.a!)}><SlidersHorizontal size={15}/>View query plan</Button>}
                  </div>
                  {turn.a.suggested_followups.length > 0 && <div className="mt-4 flex flex-wrap gap-2">{turn.a.suggested_followups.map((followup) => <button onClick={() => submit(followup)} key={followup} className="rounded-full border border-white/[.09] px-3 py-2 text-xs font-semibold text-white/55 transition hover:border-[rgba(168,255,120,.22)] hover:text-white">{followup}</button>)}</div>}
                </>
              ) : (
                <div className="flex items-center gap-3 text-sm font-semibold text-[var(--marketing-mint)]"><span className="ask-thinking"><i/><i/><i/></span>Reading schema · Building query plan · Rendering chart</div>
              )}
            </Card>
          </article>
        ))}
        {notice && <p role="status" className="text-sm font-semibold text-[var(--marketing-mint)]">{notice}</p>}
      </div>

      <form onSubmit={(event) => { event.preventDefault(); submit(question); }} className={`ask-composer fixed bottom-20 left-4 right-4 z-20 mx-auto flex max-w-5xl gap-2 p-2 md:bottom-6 ${collapsed ? "md:left-[104px]" : "md:left-[256px]"}`}>
        <label className="sr-only" htmlFor="ask">Ask about your data</label>
        <textarea id="ask" rows={1} value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); submit(question); } }} className="min-h-12 flex-1 resize-none bg-transparent px-3 py-3 text-sm outline-none placeholder:text-white/60" placeholder={dataset ? "Ask a question about this dataset…" : "Choose a dataset to begin"} disabled={!dataset || pending}/>
        <Button size="icon" aria-label="Send question" disabled={!dataset || pending || !question.trim()}><Send size={18}/></Button>
      </form>

      <Drawer open={Boolean(plan)} onOpenChange={(open) => !open && setPlan(null)} title="Query plan">
        <p className="mb-2 text-xs font-bold uppercase tracking-wider text-[var(--ink-secondary)]">Validated analytics intent</p>
        <pre className="overflow-auto rounded-xl bg-[var(--marketing-ink)] p-4 text-xs text-white">{JSON.stringify(plan?.query_plan, null, 2)}</pre>
        <p className="mb-2 mt-6 text-xs font-bold uppercase tracking-wider text-[var(--ink-secondary)]">Executed SQL</p>
        <pre className="overflow-auto rounded-xl bg-[var(--marketing-ink)] p-4 text-xs text-white">{plan?.debug_sql ?? "SQL was not returned for this answer."}</pre>
      </Drawer>
    </div>
  );
}
