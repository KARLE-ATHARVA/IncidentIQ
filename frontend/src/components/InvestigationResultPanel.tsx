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

  const reasoningSource =
    result.reasoning_source === "ai"
      ? "AI reasoning"
      : "Deterministic fallback";

  const confidenceLabel =
    confidencePercent >= 80
      ? "High confidence"
      : confidencePercent >= 60
        ? "Moderate confidence"
        : "Low confidence";

  return (
    <section className="investigation-result">
      {/* Header */}
      <header className="investigation-result-header">
        <div>
          <div className="investigation-result-eyebrow">
            AI-ASSISTED INVESTIGATION
          </div>

          <h2>Investigation Result</h2>

          <p>
            Evidence-backed reasoning generated from the incident
            context.
          </p>
        </div>

        <div className="investigation-result-source">
          <span className="investigation-source-dot" />
          {reasoningSource}
        </div>
      </header>

      {/* Hypothesis */}
      <section className="investigation-hypothesis">
        <div className="investigation-hypothesis-header">
          <div>
            <div className="investigation-section-label">
              WORKING HYPOTHESIS
            </div>

            <h3>{confidenceLabel}</h3>
          </div>

          <div className="investigation-confidence">
            <strong>{confidencePercent}%</strong>
            <span>confidence</span>
          </div>
        </div>

        <p className="investigation-hypothesis-text">
          {result.hypothesis}
        </p>

        <div className="investigation-confidence-track">
          <div
            className="investigation-confidence-fill"
            style={{
              width: `${confidencePercent}%`,
            }}
          />
        </div>

        <div className="investigation-hypothesis-note">
          <span>ⓘ</span>
          <span>
            This is an investigation hypothesis, not a confirmed
            root cause.
          </span>
        </div>
      </section>

      {/* Reasoning */}
      <section className="investigation-section">
        <div className="investigation-section-heading">
          <div>
            <div className="investigation-section-label">
              REASONING
            </div>

            <h3>Why this hypothesis?</h3>
          </div>
        </div>

        <div className="investigation-reasoning">
          {result.reasoning}
        </div>
      </section>

      {/* Supporting Evidence */}
      <section className="investigation-section">
        <div className="investigation-section-heading">
          <div>
            <div className="investigation-section-label">
              EVIDENCE
            </div>

            <h3>Supporting evidence</h3>
          </div>

          <span className="investigation-count">
            {result.supporting_evidence.length}{" "}
            {result.supporting_evidence.length === 1
              ? "item"
              : "items"}
          </span>
        </div>

        {result.supporting_evidence.length === 0 ? (
          <div className="investigation-no-evidence">
            <strong>No supporting evidence returned.</strong>
            <span>
              The hypothesis should be treated with additional
              uncertainty until evidence is available.
            </span>
          </div>
        ) : (
          <div className="investigation-evidence-list">
            {result.supporting_evidence.map((evidence) => (
              <article
                key={evidence.evidence_id}
                className="investigation-evidence-item"
              >
                <div className="investigation-evidence-main">
                  <div className="investigation-evidence-heading">
                    <div>
                      <h4>{evidence.title}</h4>

                      <span className="investigation-evidence-type">
                        {evidence.source_type}
                      </span>
                    </div>

                    {onInspectEvidence && (
                      <button
                        type="button"
                        className="investigation-inspect-button"
                        onClick={() =>
                          onInspectEvidence(
                            evidence.evidence_id,
                          )
                        }
                      >
                        Inspect →
                      </button>
                    )}
                  </div>

                  <p>{evidence.description}</p>

                  {evidence.timestamp && (
                    <span className="investigation-evidence-time">
                      Event time ·{" "}
                      {new Date(
                        evidence.timestamp,
                      ).toLocaleString()}
                    </span>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      {/* Alternatives + Next Steps */}
      <div className="investigation-bottom-grid">
        <section className="investigation-section">
          <div className="investigation-section-heading">
            <div>
              <div className="investigation-section-label">
                UNCERTAINTY
              </div>

              <h3>Alternative explanations</h3>
            </div>
          </div>

          {result.alternative_explanations.length === 0 ? (
            <div className="investigation-muted-state">
              No alternative explanations provided.
            </div>
          ) : (
            <div className="investigation-alternatives">
              {result.alternative_explanations.map(
                (alternative, index) => (
                  <div
                    key={`${index}-${alternative}`}
                    className="investigation-alternative"
                  >
                    <span>{String(index + 1).padStart(2, "0")}</span>
                    <p>{alternative}</p>
                  </div>
                ),
              )}
            </div>
          )}
        </section>

        <section className="investigation-section">
          <div className="investigation-section-heading">
            <div>
              <div className="investigation-section-label">
                ACTION
              </div>

              <h3>Recommended next steps</h3>
            </div>
          </div>

          {result.next_steps.length === 0 ? (
            <div className="investigation-muted-state">
              No next steps provided.
            </div>
          ) : (
            <div className="investigation-next-steps">
              {result.next_steps.map((step, index) => (
                <div
                  key={`${index}-${step}`}
                  className="investigation-next-step"
                >
                  <span>{index + 1}</span>
                  <p>{step}</p>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      {/* Validation */}
      {result.evaluation && (
        <section className="investigation-validation">
          <div className="investigation-validation-header">
            <div>
              <div className="investigation-section-label">
                RELIABILITY
              </div>

              <h3>Investigation validation</h3>

              <p>
                Structural and evidence validation of the generated
                result.
              </p>
            </div>

            <span
              className={
                result.evaluation.is_valid
                  ? "investigation-validation-status valid"
                  : "investigation-validation-status invalid"
              }
            >
              <span />
              {result.evaluation.is_valid
                ? "Valid"
                : "Invalid"}
            </span>
          </div>

          <div className="investigation-validation-grid">
            <div>
              <span>Evidence coverage</span>
              <strong>
                {Math.round(
                  result.evaluation.evidence_coverage * 100,
                )}
                %
              </strong>
            </div>

            <div>
              <span>Evidence items</span>
              <strong>
                {result.evaluation.evidence_count}
              </strong>
            </div>

            <div>
              <span>Supporting evidence</span>
              <strong>
                {result.evaluation.supporting_evidence_count}
              </strong>
            </div>
          </div>

          {result.evaluation.warnings.length > 0 && (
            <div className="investigation-warnings">
              <strong>Validation warnings</strong>

              <ul>
                {result.evaluation.warnings.map(
                  (warning, index) => (
                    <li key={`${index}-${warning}`}>
                      {warning}
                    </li>
                  ),
                )}
              </ul>
            </div>
          )}
        </section>
      )}
    </section>
  );
}

export default InvestigationResultPanel;