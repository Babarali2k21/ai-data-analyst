"use client";

import type { FormEvent } from "react";
import { useEffect, useState, useTransition } from "react";
import { fetchDataset, fetchHealth, runAnalysis } from "@/lib/api";
import type {
  AnalysisMode,
  AnalysisResponse,
  DatasetInfoResponse,
  HealthResponse,
} from "@/lib/types";
import { ActivityList } from "./ActivityList";
import { ChartPanel } from "./ChartPanel";
import { ResultTable } from "./ResultTable";

const EXAMPLES = [
  "How many orders were delivered?",
  "What are the top 5 product categories by revenue?",
  "What is the correlation between item price and freight_value?",
];

export function AnalystWorkbench() {
  const [question, setQuestion] = useState(EXAMPLES[1]);
  const [mode, setMode] = useState<AnalysisMode>("agent");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [dataset, setDataset] = useState<DatasetInfoResponse | null>(null);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [h, d] = await Promise.all([fetchHealth(), fetchDataset()]);
        if (!cancelled) {
          setHealth(h);
          setDataset(d);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Could not reach API. Start it with `make api`.",
          );
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    startTransition(async () => {
      try {
        const response = await runAnalysis(question.trim(), mode);
        setResult(response);
      } catch (err) {
        setResult(null);
        setError(err instanceof Error ? err.message : "Analysis failed");
      }
    });
  }

  return (
    <div className="stack">
      <div className="meta-row">
        <span className={`pill ${health?.duckdb_ready ? "ok" : "warn"}`}>
          Dataset <strong>{health?.dataset || "olist"}</strong>
          {health ? ` · ${health.duckdb_ready ? "ready" : "unavailable"}` : ""}
        </span>
        <span className="pill">
          Model <strong>{health?.model || "—"}</strong>
        </span>
        <span className="pill">
          Tables <strong>{dataset?.tables?.length ?? "—"}</strong>
        </span>
      </div>

      {dataset?.tables?.length ? (
        <p className="muted" style={{ margin: 0 }}>
          Loaded: {dataset.tables.join(", ")}
        </p>
      ) : null}

      <form className="panel ask-panel" onSubmit={onSubmit}>
        <label>
          Question
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask something about Olist orders, revenue, reviews..."
            required
            minLength={3}
          />
        </label>
        <div className="controls">
          <label>
            Mode
            <select
              value={mode}
              onChange={(event) => setMode(event.target.value as AnalysisMode)}
            >
              <option value="agent">Agent (planner + critic)</option>
              <option value="sql">SQL only</option>
            </select>
          </label>
          <button type="submit" disabled={pending || question.trim().length < 3}>
            {pending ? "Analyzing…" : "Run analysis"}
          </button>
        </div>
        <div className="examples">
          {EXAMPLES.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => setQuestion(example)}
            >
              {example}
            </button>
          ))}
        </div>
      </form>

      {error ? <p className="error">{error}</p> : null}

      {result ? (
        <>
          <section className="panel section">
            <h2>Analysis</h2>
            <ActivityList steps={result.activity} />
            <p className="muted" style={{ marginTop: "0.85rem" }}>
              Iterations: {result.iteration}
              {result.critic_passed != null
                ? ` · Critic: ${result.critic_passed ? "PASS" : "FAIL"}`
                : ""}
              {result.model ? ` · ${result.model}` : ""}
            </p>
          </section>

          <section className="panel section">
            <h2>Findings</h2>
            <p className="findings">{result.answer}</p>
          </section>

          <section className="panel section">
            <h2>Charts</h2>
            <ChartPanel charts={result.charts || []} />
          </section>

          <section className="panel section">
            <h2>Supporting queries</h2>
            {(result.supporting_sql?.length
              ? result.supporting_sql
              : result.sql
                ? [result.sql]
                : []
            ).map((sql) => (
              <pre className="sql-block" key={sql}>
                {sql}
              </pre>
            ))}
            {!result.sql && !(result.supporting_sql || []).length ? (
              <p className="muted">No SQL captured.</p>
            ) : null}
          </section>

          <section className="panel section">
            <h2>Result rows</h2>
            <ResultTable
              columns={result.query_result?.columns}
              rows={result.query_result?.rows}
            />
          </section>
        </>
      ) : null}
    </div>
  );
}
