"use client";

import { BarChart, Bar, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { Card } from "../ui/card";
import { useAppStore } from "../../lib/store/useAppStore";
import { autoFormat } from "../../lib/format";

interface ChartProps {
  payload: any;
}

export function BarChartCard({ payload }: ChartProps) {
  const getCategoryColor = useAppStore(state => state.getCategoryColor);
  
  const yKeys = payload.y_keys || [];
  const xKey = payload.x_key;

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
          <BarChart data={payload.data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
            <XAxis 
              dataKey={xKey} 
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: "var(--ink-secondary)", fontSize: 12 }} 
              dy={10}
            />
            <YAxis 
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: "var(--ink-secondary)", fontSize: 12 }}
              tickFormatter={(value) => autoFormat(value, yKeys[0] || 'value')}
            />
            <Tooltip 
              cursor={{ fill: 'var(--surface-subtle)', opacity: 0.4 }}
              contentStyle={{ borderRadius: '8px', border: '1px solid var(--hairline)', boxShadow: 'var(--shadow-float)' }}
              itemStyle={{ color: 'var(--ink)' }}
              labelStyle={{ color: 'var(--ink-secondary)', marginBottom: '4px' }}
              formatter={(value: any, name: any) => [autoFormat(value as number, name), String(name).replace(/_/g, ' ')]}
            />
            {yKeys.map((key: string) => (
              <Bar 
                key={key} 
                dataKey={key} 
                fill={yKeys.length === 1 ? "var(--accent)" : getCategoryColor(key)} 
                radius={[4, 4, 0, 0]}
                maxBarSize={60}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
