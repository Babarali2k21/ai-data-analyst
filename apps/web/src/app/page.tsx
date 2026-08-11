import { AnalystWorkbench } from "@/components/AnalystWorkbench";

export default function HomePage() {
  return (
    <main className="shell">
      <header className="hero">
        <div className="eyebrow">Olist Analyst</div>
        <h1>Ask the dataset. Get grounded answers.</h1>
        <p>
          Autonomous SQL + stats agent for Brazilian e-commerce data. See the
          analysis trail, findings, charts, and supporting queries — without
          private chain-of-thought.
        </p>
      </header>
      <AnalystWorkbench />
      <footer className="site-footer">
        A product of{" "}
        <a href="https://codelink.systems" target="_blank" rel="noreferrer">
          CodeLink Systems
        </a>
      </footer>
    </main>
  );
}
