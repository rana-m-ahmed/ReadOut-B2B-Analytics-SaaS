"use client";

import { motion } from "framer-motion";
import { Info } from "lucide-react";
import { ChartEmptyState } from "./ChartEmptyState";
import { LineChartCard } from "./LineChartCard";
import { AreaChartCard } from "./AreaChartCard";
import { BarChartCard } from "./BarChartCard";
import { StackedBarChartCard } from "./StackedBarChartCard";
import { DonutChartCard } from "./DonutChartCard";
import { ScatterChartCard } from "./ScatterChartCard";
import { MetricCard } from "../dashboard/MetricCard";
import { chartItemVariants } from "../../lib/motion";

interface ChartRendererProps {
  payload: any; // ChartPayload from backend
}

export function ChartRenderer({ payload }: ChartRendererProps) {
  if (!payload || !payload.data) {
    return (
      <motion.div variants={chartItemVariants} className="w-full h-full">
        <ChartEmptyState type="empty_data" />
      </motion.div>
    );
  }

  const { type, meta, data } = payload;

  if (data.length === 0) {
    return (
      <motion.div variants={chartItemVariants} className="w-full h-full">
        <ChartEmptyState type="empty_data" />
      </motion.div>
    );
  }

  const renderTruncationBanner = () => {
    if (meta?.truncated) {
      return (
        <div className="flex items-center gap-1.5 text-xs text-[var(--warning)] bg-[var(--warning)]/10 px-2 py-1 rounded-full absolute top-4 right-4 z-10 font-medium">
          <Info size={12} />
          Showing {data.length} of {meta.original_row_count} data points
        </div>
      );
    }
    return null;
  };

  const renderChart = () => {
    switch (type) {
      case "line":
        return <LineChartCard payload={payload} />;
      case "multi_line":
        return <AreaChartCard payload={payload} />;
      case "bar":
        return <BarChartCard payload={payload} />;
      case "stacked_bar":
        return <StackedBarChartCard payload={payload} />;
      case "donut":
        return <DonutChartCard payload={payload} />;
      case "scatter":
        return <ScatterChartCard payload={payload} />;
      case "metric_card":
        // Wrap the payload into a mock UseQueryResult to reuse MetricCard
        const mockQueryResult: any = {
          data: {
            summary: payload.description,
            chart: payload,
            query_plan: { metric: payload.y_keys?.[0] }
          },
          isLoading: false,
          isError: false
        };
        return <div className="w-full h-full min-h-[300px] flex"><div className="w-full m-auto"><MetricCard queryResult={mockQueryResult} /></div></div>;
      default:
        return <ChartEmptyState type="unsupported_type" chartType={type} />;
    }
  };

  return (
    <motion.div variants={chartItemVariants} className="w-full h-full relative">
      {renderTruncationBanner()}
      {renderChart()}
    </motion.div>
  );
}
