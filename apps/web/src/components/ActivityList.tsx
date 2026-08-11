"use client";

export function ActivityList({ steps }: { steps: string[] }) {
  if (!steps?.length) {
    return <p className="muted">No agent activity yet.</p>;
  }
  return (
    <ul className="activity">
      {steps.map((step, index) => (
        <li key={`${index}-${step}`}>
          <span className="check">✓</span>
          <span>{step}</span>
        </li>
      ))}
    </ul>
  );
}
