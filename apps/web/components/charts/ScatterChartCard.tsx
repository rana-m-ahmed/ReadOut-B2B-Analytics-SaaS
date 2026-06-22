"use client";

import { ScatterChart, Scatter, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { Card } from "../ui/card";
import { autoFormat } from "../../lib/format";

interface ChartProps {
  payload: any;
}

export function ScatterChartCard({ payload }: ChartProps) {
  const yKey = payload.y_keys?.[0] || 'value';
  const xKey = payload.x_key || 'x';

  return (
    <Card className="w-full h-full min-h-[300px] flex flex-col p-6 border-[var(--hairline)] shadow-sm bg-[var(--surface)]">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-[var(--ink)]">{payload.title}</h3>
        {payload.description && (
          <p className="text-sm text-[var(--ink-secondary)]">{payload.description}</p>
        )}
      </div>

      <div className="flex-1 min-h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
            <XAxis 
              dataKey={xKey} 
              type="number"
              name={xKey.replace(/_/g, ' ')}
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: "var(--ink-secondary)", fontSize: 12 }} 
              dy={10}
              tickFormatter={(value) => autoFormat(value, xKey)}
            />
            <YAxis 
              dataKey={yKey} 
              type="number"
              name={yKey.replace(/_/g, ' ')}
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: "var(--ink-secondary)", fontSize: 12 }}
              tickFormatter={(value) => autoFormat(value, yKey)}
            />
            <Tooltip 
              cursor={{ strokeDasharray: '3 3', stroke: 'var(--ink-secondary)', opacity: 0.5 }}
              contentStyle={{ borderRadius: '8px', border: '1px solid var(--hairline)', boxShadow: 'var(--shadow-float)' }}
              labelStyle={{ display: 'none' }}
              formatter={(value: any, name: any) => [autoFormat(value as number, name), String(name)]}
            />
            <Scatter name={payload.title} data={payload.data} fill="var(--accent)" />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
