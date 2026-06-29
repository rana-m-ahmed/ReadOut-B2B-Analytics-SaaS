"use client";
import { useMemo } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Info } from "lucide-react";
import type { ChartT } from "@/lib/api/types";
const clean = (v: unknown) => (v == null ? "—" : String(v));
const numeric = (v: unknown) => typeof v === "number" && Number.isFinite(v);
const COLORS = ["var(--accent)", "var(--success)", "var(--warning)", "var(--marketing-cyan)", "var(--marketing-coral)"];
const colorFor = (category: string) => {
  let hash = 0;
  for (const char of category) hash = (hash * 31 + char.charCodeAt(0)) | 0;
  return COLORS[Math.abs(hash) % COLORS.length];
};
function DataTable({ payload }: { payload: ChartT }) {
  const keys = useMemo(
    () =>
      Array.from(new Set(payload.data.flatMap(Object.keys))).filter(
        (k) => !k.startsWith("formatted_"),
      ),
    [payload.data],
  );
  return (
    <div className="max-h-72 overflow-auto">
      <table className="w-full min-w-[420px] text-left text-sm">
        <thead className="sticky top-0 bg-[var(--surface-subtle)]">
          <tr>
            {keys.map((k) => (
              <th className="px-3 py-2" key={k}>
                {k.replaceAll("_", " ")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {payload.data.map((row, i) => (
            <tr className="border-t border-[var(--hairline)]" key={i}>
              {keys.map((k) => (
                <td className="px-3 py-2 tabular" key={k}>
                  {clean(row[`formatted_${k}`] ?? row[k])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
export function ChartRenderer({ payload }: { payload: ChartT }) {
  if (!payload.data.length)
    return (
      <div className="grid min-h-52 place-items-center text-sm text-[var(--ink-secondary)]">
        No data found for this query.
      </div>
    );
  const x = payload.x_key ?? Object.keys(payload.data[0])[0],
    ys = payload.y_keys.length
      ? payload.y_keys
      : Object.keys(payload.data[0])
          .filter((k) => numeric(payload.data[0][k]))
          .slice(0, 1);
  const type = payload.type;
  const tooltip = {
    contentStyle: {
      background: "var(--ink)",
      color: "var(--accent-on)",
      border: "1px solid rgba(174,194,235,.16)",
      borderRadius: 14,
      boxShadow: "0 18px 45px rgba(0,0,0,.35)",
    },
    labelStyle: { color: "var(--accent-on)" },
  };
  let chart: React.ReactNode;
  if (type === "metric_card") {
    const key = ys[0] ?? Object.keys(payload.data[0])[0];
    chart = (
      <div className="py-8">
        <p className="text-5xl font-bold tracking-tight tabular">
          {clean(payload.data[0][`formatted_${key}`] ?? payload.data[0][key])}
        </p>
        <p className="mt-2 text-sm text-[var(--ink-secondary)]">
          {payload.description}
        </p>
      </div>
    );
  } else if (
    [
      "line",
      "multi_line",
      "anomaly_line",
      "line_with_highlighted_point",
    ].includes(type)
  )
    chart = (
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={payload.data}>
          <CartesianGrid vertical={false} stroke="rgba(174,194,235,.10)" strokeDasharray="4 8" />
          <XAxis dataKey={x} tick={{fill:"var(--ink-secondary)",fontSize:11}} axisLine={false} tickLine={false}/>
          <YAxis width={44} tick={{fill:"var(--ink-secondary)",fontSize:11}} axisLine={false} tickLine={false}/>
          <Tooltip {...tooltip} />
          {ys.map((y) => (
            <Line
              key={y}
              type="monotone"
              dataKey={y}
              stroke={colorFor(y)}
              strokeWidth={3.5}
              dot={type.includes("highlighted") ? { r: 4 } : false}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    );
  else if (type === "area")
    chart = (
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={payload.data}>
          <CartesianGrid vertical={false} stroke="rgba(174,194,235,.10)" strokeDasharray="4 8" />
          <XAxis dataKey={x} tick={{fill:"var(--ink-secondary)",fontSize:11}} axisLine={false} tickLine={false}/>
          <YAxis width={44} tick={{fill:"var(--ink-secondary)",fontSize:11}} axisLine={false} tickLine={false}/>
          <Tooltip {...tooltip} />
          {ys.map((y) => (
            <Area
              key={y}
              type="monotone"
              dataKey={y}
              stroke={colorFor(y)}
              fill={colorFor(y)}
              fillOpacity={0.16}
              isAnimationActive={false}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    );
  else if (["bar", "stacked_bar", "donut"].includes(type))
    chart = (
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={payload.data}>
          <CartesianGrid vertical={false} stroke="rgba(174,194,235,.10)" strokeDasharray="4 8" />
          <XAxis dataKey={x} tick={{fill:"var(--ink-secondary)",fontSize:11}} axisLine={false} tickLine={false}/>
          <YAxis width={44} tick={{fill:"var(--ink-secondary)",fontSize:11}} axisLine={false} tickLine={false}/>
          <Tooltip {...tooltip} />
          {ys.map((y) => (
            <Bar
              key={y}
              dataKey={y}
              stackId={type === "stacked_bar" ? "stack" : undefined}
              fill={colorFor(y)}
              radius={[8, 8, 0, 0]}
              isAnimationActive={false}
            >
              {type === "donut" &&
                payload.data.map((row) => (
                  <Cell key={clean(row[x])} fill={colorFor(clean(row[x]))} />
                ))}
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>
    );
  else if (type === "scatter")
    chart = (
      <ResponsiveContainer width="100%" height={280}>
        <ScatterChart>
          <CartesianGrid stroke="var(--hairline)" />
          <XAxis dataKey={x} />
          <YAxis dataKey={ys[0]} width={44} />
          <Tooltip {...tooltip} />
          <Scatter data={payload.data} fill="var(--accent)" isAnimationActive={false} />
        </ScatterChart>
      </ResponsiveContainer>
    );
  else chart = <DataTable payload={payload} />;
  return (
    <figure
      className="relative min-w-0"
      aria-label={`${payload.title}. ${payload.description}`}
    >
      <figcaption className="mb-4">
        <h3 className="font-bold">{payload.title}</h3>
        <p className="mt-1 text-sm text-[var(--ink-secondary)]">
          {payload.description}
        </p>
      </figcaption>
      {payload.meta.truncated === true && (
        <p className="mb-3 inline-flex items-center gap-2 rounded-full bg-[color-mix(in_srgb,var(--warning)_13%,white)] px-3 py-1 text-xs font-semibold">
          <Info size={14} />
          Showing a representative subset of{" "}
          {clean(payload.meta.original_row_count)} results.
        </p>
      )}
      {chart}
      <details className="mt-3 text-xs text-[var(--ink-secondary)]">
        <summary className="cursor-pointer font-semibold">
          Accessible data preview
        </summary>
        <div className="mt-2">
          <DataTable payload={payload} />
        </div>
      </details>
    </figure>
  );
}
