"use client";

export function ResultTable({
  columns,
  rows,
}: {
  columns?: string[];
  rows?: Array<Record<string, unknown>>;
}) {
  if (!rows?.length) {
    return <p className="muted">No tabular rows returned.</p>;
  }
  const cols = columns?.length ? columns : Object.keys(rows[0] || {});
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {cols.map((col) => (
              <th key={col}>{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 25).map((row, index) => (
            <tr key={index}>
              {cols.map((col) => (
                <td key={col}>{String(row[col] ?? "")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
