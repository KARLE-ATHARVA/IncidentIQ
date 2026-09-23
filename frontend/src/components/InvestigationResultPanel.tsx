import type { InvestigationResult } from "../types";

interface InvestigationResultPanelProps {
  result: InvestigationResult;
  onInspectEvidence?: (evidenceId: string) => void;
}

function InvestigationResultPanel({
  result,
  onInspectEvidence,
}: InvestigationResultPanelProps) {
  const confidencePercent = Math.round(result.confidence * 100);

  return (
    <section>
      <h2>AI Investigation Result</h2>

      <p>
        <strong>Reasoning source:</strong>{" "}
        {result.reasoning_source === "ai"
          ? "AI"
          : "Deterministic fallback"}
      </p>

      <hr />

      <h3>Hypothesis</h3>

      <p>{result.hypothesis}</p>

      <p>
        <strong>Confidence:</strong> {confidencePercent}%
      </p>

      <hr />

      <h3>Reasoning</h3>

      <p>{result.reasoning}</p>

      <hr />

      <h3>Supporting Evidence</h3>

      {result.supporting_evidence.length === 0 ? (
        <p>No supporting evidence was returned.</p>
      ) : (
        <div>
          {result.supporting_evidence.map((evidence) => (
            <article key={evidence.evidence_id}>
              <h4>{evidence.title}</h4>

              <p>{evidence.description}</p>

              <p>
                <strong>Source:</strong> {evidence.source_type}
              </p>

              {evidence.timestamp && (
                <p>
                  <strong>Timestamp:</strong>{" "}
                  {new Date(evidence.timestamp).toLocaleString()}
                </p>
              )}

              {onInspectEvidence && (
                <button
                  type="button"
                  onClick={() =>
                    onInspectEvidence(evidence.evidence_id)
                  }
                >
                  Inspect Evidence
                </button>
              )}

              <hr />
            </article>
          ))}
        </div>
      )}

      <h3>Alternative Explanations</h3>

      {result.alternative_explanations.length === 0 ? (
        <p>No alternative explanations provided.</p>
      ) : (
        <ul>
          {result.alternative_explanations.map((alternative, index) => (
            <li key={`${index}-${alternative}`}>
              {alternative}
            </li>
          ))}
        </ul>
      )}

      <h3>Next Steps</h3>

      {result.next_steps.length === 0 ? (
        <p>No next steps provided.</p>
      ) : (
        <ol>
          {result.next_steps.map((step, index) => (
            <li key={`${index}-${step}`}>
              {step}
            </li>
          ))}
        </ol>
      )}

      {result.evaluation && (
        <>
          <hr />

          <h3>Investigation Validation</h3>

          <p>
            <strong>Valid:</strong>{" "}
            {result.evaluation.is_valid ? "Yes" : "No"}
          </p>

          <p>
            <strong>Evidence coverage:</strong>{" "}
            {Math.round(result.evaluation.evidence_coverage * 100)}%
          </p>

          <p>
            <strong>Evidence items:</strong>{" "}
            {result.evaluation.evidence_count}
          </p>

          <p>
            <strong>Supporting evidence:</strong>{" "}
            {result.evaluation.supporting_evidence_count}
          </p>

          {result.evaluation.warnings.length > 0 && (
            <>
              <h4>Warnings</h4>

              <ul>
                {result.evaluation.warnings.map((warning, index) => (
                  <li key={`${index}-${warning}`}>
                    {warning}
                  </li>
                ))}
              </ul>
            </>
          )}
        </>
      )}
    </section>
  );
}

export default InvestigationResultPanel;