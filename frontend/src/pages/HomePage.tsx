import { useNavigate } from "react-router-dom";

const workflow = [
  "Detect",
  "Correlate",
  "Investigate",
  "Reason",
  "Resolve",
];

const connections = [
  ["Telemetry", "Metrics and event signals"],
  ["Deployments", "Engineering changes in context"],
  ["Logs", "Operational failure evidence"],
  ["Historical incidents", "Prior investigation context"],
  ["AI investigation", "Grounded working hypotheses"],
];

function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="page home-page">
      <section className="home-hero page-enter">
        <div className="home-hero-copy">
          <p className="section-eyebrow">INCIDENT INTELLIGENCE</p>
          <h1>Investigate incidents with evidence.</h1>
          <p>
            IncidentIQ connects telemetry, deployments, historical
            incidents, and AI-assisted reasoning into one
            evidence-first investigation workflow.
          </p>

          <div className="home-hero-actions">
            <button
              type="button"
              className="button button-primary"
              onClick={() => navigate("/dashboard")}
            >
              Open Dashboard
            </button>
            <button
              type="button"
              className="button button-secondary"
              onClick={() => navigate("/projects")}
            >
              Explore Incidents
            </button>
          </div>
        </div>

        <div className="home-workflow" aria-label="Investigation workflow">
          <span className="home-workflow-label">WORKFLOW</span>
          <div className="home-workflow-steps">
            {workflow.map((step, index) => (
              <div key={step} className="home-workflow-step">
                <span>{String(index + 1).padStart(2, "0")}</span>
                <strong>{step}</strong>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="home-section page-enter">
        <div className="section-heading">
          <div>
            <p className="section-eyebrow">CONNECTED CONTEXT</p>
            <h2>What IncidentIQ connects</h2>
          </div>
          <p>
            Investigation starts with the signals engineers already use
            to understand change and impact.
          </p>
        </div>

        <div className="connection-grid">
          {connections.map(([title, description], index) => (
            <article key={title} className="connection-item">
              <span>{String(index + 1).padStart(2, "0")}</span>
              <div>
                <h3>{title}</h3>
                <p>{description}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="home-section home-principles page-enter">
        <div className="section-heading">
          <div>
            <p className="section-eyebrow">WHY INCIDENTIQ</p>
            <h2>Evidence before conclusions.</h2>
          </div>
        </div>

        <div className="principle-grid">
          <article>
            <h3>Evidence before conclusions</h3>
            <p>Keep hypotheses connected to the source signals that support them.</p>
          </article>
          <article>
            <h3>Explainable detection</h3>
            <p>Move from abnormal behavior to a structured incident context.</p>
          </article>
          <article>
            <h3>Historical context</h3>
            <p>Use prior incidents as context, not as proof of causality.</p>
          </article>
          <article>
            <h3>Human-in-the-loop reasoning</h3>
            <p>Review evidence, alternatives, and next steps before deciding.</p>
          </article>
        </div>
      </section>

      <section className="home-explore page-enter">
        <div>
          <p className="section-eyebrow">EXPLORE</p>
          <h2>Choose an investigation surface.</h2>
        </div>
        <div className="home-explore-links">
          <button type="button" onClick={() => navigate("/dashboard")}>
            <span>01</span><strong>Dashboard</strong><i>Operational overview →</i>
          </button>
          <button type="button" onClick={() => navigate("/projects")}>
            <span>02</span><strong>Incidents</strong><i>Choose a project →</i>
          </button>
          <button type="button" onClick={() => navigate("/projects")}>
            <span>03</span><strong>Production Simulator</strong><i>Run a scenario →</i>
          </button>
        </div>
      </section>
    </div>
  );
}

export default HomePage;
