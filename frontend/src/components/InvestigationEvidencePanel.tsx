import type { InvestigationEvidence } from "../types";

interface InvestigationEvidencePanelProps {
  evidence: InvestigationEvidence;
  onClose: () => void;
}

function InvestigationEvidencePanel({
  evidence,
  onClose,
}: InvestigationEvidencePanelProps) {
  return (
    <section>
      <h3>Evidence Inspection</h3>

      <p>
        <strong>Title:</strong> {evidence.title}
      </p>

      <p>
        <strong>Source type:</strong> {evidence.source_type}
      </p>

      <p>
        <strong>Source ID:</strong> {evidence.source_id}
      </p>

      {evidence.service_id && (
        <p>
          <strong>Service ID:</strong> {evidence.service_id}
        </p>
      )}

      {evidence.timestamp && (
        <p>
          <strong>Event time:</strong>{" "}
          {new Date(evidence.timestamp).toLocaleString()}
        </p>
      )}

      <p>
        <strong>Collected:</strong>{" "}
        {new Date(evidence.collected_at).toLocaleString()}
      </p>

      <p>
        <strong>Description:</strong> {evidence.description}
      </p>

      <h4>Source Details</h4>

      {Object.entries(evidence.details).length === 0 ? (
        <p>No source-specific details available.</p>
      ) : (
        <dl>
          {Object.entries(evidence.details).map(
            ([key, value]) => (
              <div key={key}>
                <dt>
                  <strong>{key}</strong>
                </dt>

                <dd>
                  {typeof value === "object"
                    ? JSON.stringify(value)
                    : String(value)}
                </dd>
              </div>
            ),
          )}
        </dl>
      )}

      <button type="button" onClick={onClose}>
        Close Evidence
      </button>
    </section>
  );
}

export default InvestigationEvidencePanel;