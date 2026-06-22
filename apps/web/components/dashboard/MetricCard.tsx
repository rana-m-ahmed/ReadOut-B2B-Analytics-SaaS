"use client";

import { useMemo } from "react";
import { UseQueryResult } from "@tanstack/react-query";
import { AskResponse } from "../../lib/api/client";
import { Card } from "../ui/card";
import { Skeleton } from "../ui/skeleton";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../ui/tooltip";
import { LineChart, Line, ResponsiveContainer, BarChart, Bar } from "recharts";
import { AlertCircle, ArrowDown, ArrowUp, Minus, Info } from "lucide-react";
import clsx from "clsx";
import { autoFormat, formatPercent } from "../../lib/format";

export function MetricCard({ 
  queryResult 
}: { 
  queryResult: UseQueryResult<AskResponse, Error> 
}) {
  const { data, isLoading, isError } = queryResult;

  const formattedData = useMemo(() => {
    if (!data?.chart || !data.chart.data || data.chart.data.length === 0) return null;
    
    const chart = data.chart;
    const yKey = chart.y_keys?.[0] || 'value';
    const firstRow = chart.data[0];
    
    let value: string | number = "";
    if (chart.data.length > 0 && chart.y_keys && chart.y_keys.length > 0) {
      const primaryKey = chart.y_keys[0];
      const val = chart.data[0][primaryKey];
      if (typeof val === 'number') {
        value = autoFormat(val, primaryKey);
      } else {
        value = String(val);
      }
    }
    
    let label = data.query_plan?.metric || yKey;
    if (label === 'value' && chart.description) {
      label = chart.description;
    }
    // Simple format for snake_case
    label = label.replace(/_/g, ' ');

    let deltaPercent: number | null = null;
    let formattedDelta = '';
    if ('delta_percent' in firstRow && firstRow.delta_percent !== null) {
      deltaPercent = Number(firstRow.delta_percent) * 100;
      formattedDelta = formatPercent(Math.abs(deltaPercent));
    }

    const isTrendDown = deltaPercent !== null && deltaPercent < 0;
    const isTrendUp = deltaPercent !== null && deltaPercent > 0;

    const canPlot = chart.data.length > 1;

    return {
      label,
      value: typeof value === 'number' ? (value as number).toLocaleString(undefined, { maximumFractionDigits: 1 }) : String(value),
      deltaPercent,
      isTrendDown,
      isTrendUp,
      formattedDelta,
      canPlot,
      chartData: chart.data,
      yKey,
      chartType: chart.type || 'line',
      summary: data.summary || "No calculation details available."
    };
  }, [data]);

  if (isLoading) {
    return (
      <Card className="p-4 flex flex-col gap-3 min-w-[240px] border-[var(--hairline)] shadow-sm">
        <Skeleton className="h-4 w-24 rounded" />
        <Skeleton className="h-8 w-32 rounded" />
        <Skeleton className="h-12 w-full rounded" />
      </Card>
    );
  }

  if (isError || !data || data.clarification_required || !formattedData) {
    return (
      <Card className="p-4 flex flex-col justify-center gap-2 min-w-[240px] border-[var(--hairline)] shadow-sm bg-[var(--surface-subtle)]/50">
        <div className="flex items-center text-[var(--ink-secondary)] text-sm gap-2">
          <AlertCircle size={16} />
          <span>Metric unavailable</span>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-4 flex flex-col gap-1 min-w-[240px] border-[var(--hairline)] shadow-sm hover:shadow-md transition-shadow" data-testid="metric-card">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--ink-secondary)] capitalize truncate" title={formattedData.label} data-testid="metric-label">
          {formattedData.label}
        </h3>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger className="text-[var(--ink-secondary)] hover:text-[var(--ink)] transition-colors">
              <Info size={14} />
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-[250px] text-xs">
              <p>{formattedData.summary}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      <div className="flex items-baseline gap-2 mt-1">
        <span className="text-2xl font-bold font-mono tracking-tight text-[var(--ink)]" data-testid="metric-value">
          {formattedData.value}
        </span>
        
        {formattedData.deltaPercent !== null ? (
          <span className={clsx(
            "text-xs font-semibold flex items-center px-1.5 py-0.5 rounded-full",
            formattedData.isTrendUp ? "bg-[var(--success)]/10 text-[var(--success)]" : 
            formattedData.isTrendDown ? "bg-[var(--danger)]/10 text-[var(--danger)]" : 
            "bg-[var(--ink-secondary)]/10 text-[var(--ink-secondary)]"
          )}>
            {formattedData.isTrendUp ? <ArrowUp size={12} className="mr-0.5" /> : 
             formattedData.isTrendDown ? <ArrowDown size={12} className="mr-0.5" /> : 
             <Minus size={12} className="mr-0.5" />}
            {formattedData.formattedDelta}
          </span>
        ) : (
          <span className="text-xs text-[var(--ink-secondary)] font-medium" title="Comparison delta not available for this metric.">
            No delta
          </span>
        )}
      </div>

      <div className="h-12 w-full mt-3 opacity-80 pointer-events-none">
        {formattedData.canPlot ? (
          <ResponsiveContainer width="100%" height="100%">
            {formattedData.chartType === 'bar' ? (
              <BarChart data={formattedData.chartData}>
                <Bar dataKey={formattedData.yKey} fill="var(--accent)" radius={[2, 2, 0, 0]} />
              </BarChart>
            ) : (
              <LineChart data={formattedData.chartData}>
                <Line 
                  type="monotone" 
                  dataKey={formattedData.yKey} 
                  stroke="var(--accent)" 
                  strokeWidth={2} 
                  dot={false} 
                  isAnimationActive={false} 
                />
              </LineChart>
            )}
          </ResponsiveContainer>
        ) : (
          <div className="w-full h-full flex items-center justify-center border border-dashed border-[var(--hairline)] rounded text-xs text-[var(--ink-secondary)]/50">
            Scalar only
          </div>
        )}
      </div>
    </Card>
  );
}
