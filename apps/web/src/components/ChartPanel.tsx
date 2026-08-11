"use client";

import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { chartImageUrl } from "@/lib/api";
import type { ChartSpec } from "@/lib/types";

function toChartData(spec: ChartSpec) {
  return (spec.series || []).map((point) => ({
    x: String(point.x ?? ""),
    y:
      typeof point.y === "number"
        ? point.y
        : Number(point.y ?? point.x ?? 0) || 0,
  }));
}

function shouldUseHorizontalBars(data: { x: string; y: number }[]) {
  if (data.length > 8) return true;
  return data.some((row) => row.x.length > 12);
}

export function ChartPanel({ charts }: { charts: ChartSpec[] }) {
  const items = useMemo(() => charts || [], [charts]);
  if (!items.length) {
    return <p className="muted">No chartable series for this answer.</p>;
  }

  return (
    <div className="chart-grid">
      {items.map((chart) => {
        const data = toChartData(chart);
        const png = chartImageUrl(chart.image_path);
        const horizontal = chart.type === "bar" && shouldUseHorizontalBars(data);
        const chartHeight = horizontal ? Math.max(280, data.length * 28 + 48) : 280;
        return (
          <div className="chart-card" key={`${chart.title}-${chart.type}-${chart.x}`}>
            <h3>
              {chart.title} · {chart.type}
            </h3>
            {data.length > 0 ? (
              <div style={{ width: "100%", height: chartHeight }}>
                <ResponsiveContainer>
                  {chart.type === "line" ? (
                    <LineChart data={data}>
                      <CartesianGrid stroke="rgba(142,172,184,0.2)" />
                      <XAxis dataKey="x" stroke="#8eacb8" interval={0} angle={-30} textAnchor="end" height={70} />
                      <YAxis stroke="#8eacb8" />
                      <Tooltip />
                      <Line type="monotone" dataKey="y" stroke="#2ec4b6" strokeWidth={2} />
                    </LineChart>
                  ) : chart.type === "scatter" ? (
                    <ScatterChart>
                      <CartesianGrid stroke="rgba(142,172,184,0.2)" />
                      <XAxis dataKey="x" stroke="#8eacb8" name={chart.x} />
                      <YAxis dataKey="y" stroke="#8eacb8" name={chart.y || "y"} />
                      <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                      <Scatter data={data} fill="#f4a261" />
                    </ScatterChart>
                  ) : horizontal ? (
                    <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16, top: 8, bottom: 8 }}>
                      <CartesianGrid stroke="rgba(142,172,184,0.2)" horizontal={false} />
                      <XAxis type="number" stroke="#8eacb8" />
                      <YAxis
                        type="category"
                        dataKey="x"
                        stroke="#8eacb8"
                        width={150}
                        interval={0}
                        tick={{ fontSize: 11 }}
                      />
                      <Tooltip />
                      <Bar dataKey="y" fill="#2ec4b6" radius={[0, 6, 6, 0]} />
                    </BarChart>
                  ) : (
                    <BarChart data={data} margin={{ bottom: 48 }}>
                      <CartesianGrid stroke="rgba(142,172,184,0.2)" />
                      <XAxis
                        dataKey="x"
                        stroke="#8eacb8"
                        interval={0}
                        angle={-35}
                        textAnchor="end"
                        height={70}
                        tick={{ fontSize: 11 }}
                      />
                      <YAxis stroke="#8eacb8" />
                      <Tooltip />
                      <Bar dataKey="y" fill="#2ec4b6" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  )}
                </ResponsiveContainer>
              </div>
            ) : null}
            {png ? <img src={png} alt={chart.title} style={{ marginTop: data.length ? 12 : 0 }} /> : null}
          </div>
        );
      })}
    </div>
  );
}
