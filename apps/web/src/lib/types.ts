export type AnalysisMode = "agent" | "sql";

export type ChartSpec = {
  type: "line" | "bar" | "scatter" | "hist";
  x: string;
  y?: string | null;
  title: string;
  series?: Array<{ x: unknown; y: unknown }>;
  image_path?: string;
};

export type AnalysisResponse = {
  question: string;
  answer: string;
  mode: AnalysisMode;
  sql?: string | null;
  plan?: Record<string, unknown>;
  activity: string[];
  supporting_sql: string[];
  critic_passed?: boolean | null;
  critic_feedback?: string;
  failure_type?: string;
  recovery_action?: string;
  recovery_history?: string[];
  iteration: number;
  model: string;
  query_result: {
    columns?: string[];
    rows?: Array<Record<string, unknown>>;
    row_count?: number;
  };
  python_result?: Record<string, unknown>;
  charts: ChartSpec[];
  chart_paths: string[];
};

export type HealthResponse = {
  status: string;
  duckdb_ready: boolean;
  model: string;
  dataset: string;
};

export type DatasetInfoResponse = {
  dataset: string;
  tables: string[];
  duckdb_path: string;
};
