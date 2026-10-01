import type { InvestigationEvidence } from "../types";

interface InvestigationEvidencePanelProps {
  evidence: InvestigationEvidence;
  onClose: () => void;
}

function formatValue(value: unknown): string {
  if (typeof value === "object" && value !== null) {
    return JSON.stringify(value, null, 2);
  }

  return String(value);
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "medium",
  });
}

function InvestigationEvidencePanel({
  evidence,
  onClose,
}: InvestigationEvidencePanelProps) {
  const sourceDetails = Object.entries(evidence.details);

  return (
    <section className="evidence-inspection">
      <header className="evidence-inspection-header">
        <div>
          <div className="evidence-inspection-eyebrow">
            EVIDENCE PROVENANCE
          </div>

          <h3>Evidence Inspection</h3>

          <p>
            Inspect the original engineering evidence behind the
            investigation.
          </p>
        </div>

        <button
          type="button"
          className="evidence-close-button"
          onClick={onClose}
        >
          Close
        </button>
      </header>

      {/* Evidence identity */}
      <section className="evidence-identity">
        <div className="evidence-identity-top">
          <div>
            <span className="evidence-source-label">
              SOURCE EVIDENCE
            </span>

            <h4>{evidence.title}</h4>
          </div>

          <span className="evidence-source-badge">
            {evidence.source_type}
          </span>
        </div>

        <p>{evidence.description}</p>
      </section>

      {/* Metadata */}
      <section className="evidence-metadata">
        <div className="evidence-metadata-item">
          <span>Source ID</span>
          <code>{evidence.source_id}</code>
        </div>

        {evidence.service_id && (
          <div className="evidence-metadata-item">
            <span>Service ID</span>
            <code>{evidence.service_id}</code>
          </div>
        )}

        {evidence.timestamp && (
          <div className="evidence-metadata-item">
            <span>Event time</span>
            <strong>
              {formatDate(evidence.timestamp)}
            </strong>
          </div>
        )}

        <div className="evidence-metadata-item">
          <span>Collected</span>
          <strong>
            {formatDate(evidence.collected_at)}
          </strong>
        </div>
      </section>

      {/* Source details */}
      <section className="evidence-source-details">
        <div className="evidence-section-heading">
          <div>
            <div className="evidence-section-label">
              RAW CONTEXT
            </div>

            <h4>Source details</h4>
          </div>

          <span>
            {sourceDetails.length}{" "}
            {sourceDetails.length === 1
              ? "field"
              : "fields"}
          </span>
        </div>

        {sourceDetails.length === 0 ? (
          <div className="evidence-empty-details">
            No source-specific details available.
          </div>
        ) : (
          <div className="evidence-detail-list">
            {sourceDetails.map(([key, value]) => (
              <div
                key={key}
                className="evidence-detail-row"
              >
                <div className="evidence-detail-key">
                  {key}
                </div>

                <pre className="evidence-detail-value">
                  {formatValue(value)}
                </pre>
              </div>
            ))}
          </div>
        )}
      </section>

      <footer className="evidence-inspection-footer">
        <span className="evidence-footer-dot" />

        <span>
          This evidence is presented as source context for the
          investigation.
        </span>
      </footer>
    </section>
  );
}

export default InvestigationEvidencePanel;