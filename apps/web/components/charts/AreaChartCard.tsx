"use client";

import { AreaChart, Area, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts";
import { Card } from "../ui/card";
import { useAppStore } from "../../lib/store/useAppStore";
import { autoFormat } from "../../lib/format";

interface ChartProps {
  payload: any;
}

export function AreaChartCard({ payload }: ChartProps) {
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
          <AreaChart data={payload.data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
            <defs>
              {yKeys.map((key: string) => {
                const color = yKeys.length === 1 ? "var(--accent)" : getCategoryColor(key);
                return (
                  <linearGradient key={`grad-${key}`} id={`grad-${key}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={color} stopOpacity={0.3}/>
                    <stop offset="95%" stopColor={color} stopOpacity={0}/>
                  </linearGradient>
                )
              })}
            </defs>
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
              contentStyle={{ borderRadius: '8px', border: '1px solid var(--hairline)', boxShadow: 'var(--shadow-float)' }}
              itemStyle={{ color: 'var(--ink)' }}
              labelStyle={{ color: 'var(--ink-secondary)', marginBottom: '4px' }}
              formatter={(value: any, name: any) => [autoFormat(value as number, name), String(name).replace(/_/g, ' ')]}
            />
            {yKeys.map((key: string) => {
              const color = yKeys.length === 1 ? "var(--accent)" : getCategoryColor(key);
              return (
                <Area 
                  key={key} 
                  type="monotone" 
                  dataKey={key} 
                  stroke={color}
                  fill={`url(#grad-${key})`}
                  strokeWidth={2} 
                />
              );
            })}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
