"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { Card } from "../ui/card";
import { useAppStore } from "../../lib/store/useAppStore";
import { autoFormat, formatPercent } from "../../lib/format";

interface ChartProps {
  payload: any;
}

export function DonutChartCard({ payload }: ChartProps) {
  const getCategoryColor = useAppStore(state => state.getCategoryColor);
  
  const yKey = payload.y_keys?.[0] || 'value';
  const xKey = payload.x_key || 'name';

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
          <PieChart margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
            <Pie
              data={payload.data}
              dataKey={yKey}
              nameKey={xKey}
              cx="50%"
              cy="50%"
              innerRadius="60%"
              outerRadius="80%"
              paddingAngle={2}
              stroke="none"
            >
              {payload.data.map((entry: any, index: number) => (
                <Cell key={`cell-${index}`} fill={getCategoryColor(entry[xKey] || `Category ${index}`)} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{ borderRadius: '8px', border: '1px solid var(--hairline)', boxShadow: 'var(--shadow-float)' }}
              itemStyle={{ color: 'var(--ink)' }}
              formatter={(value: any, name: any, props: any) => {
                const proportion = props.payload.proportion;
                if (proportion !== undefined) {
                  return [`${autoFormat(value as number, yKey)} (${formatPercent(proportion)})`, String(name)];
                }
                return [autoFormat(value as number, yKey), String(name)];
              }}
            />
            <Legend 
              verticalAlign="bottom" 
              height={36} 
              iconType="circle"
              formatter={(value) => <span className="text-[var(--ink-secondary)] text-xs ml-1">{value}</span>}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
