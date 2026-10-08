import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { login } from "../api";

function LoginPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setLoading(true);
    setError("");

    try {
      const data = await login(
        email.trim(),
        password,
      );

      localStorage.setItem(
        "access_token",
        data.access_token,
      );

      navigate("/home");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to sign in.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <section className="login-brand-panel">
        <div className="login-brand-content">
          <div className="login-logo">IQ</div>

          <div className="login-brand-name">
            IncidentIQ
          </div>

          <div className="login-eyebrow">
            ENGINEERING INCIDENT INTELLIGENCE
          </div>

          <h1>
            Investigate incidents
            <br />
            with <span>evidence.</span>
          </h1>

          <p className="login-value-proposition">
            IncidentIQ connects telemetry, timelines,
            deployments, historical incidents, and
            AI-assisted reasoning into one structured
            investigation workflow.
          </p>

          <div className="login-principles">
            <div className="login-principle">
              <div className="login-principle-icon">
                01
              </div>

              <div>
                <strong>
                  Connect the signals
                </strong>

                <p>
                  Bring logs, metrics, deployments,
                  and incident events together.
                </p>
              </div>
            </div>

            <div className="login-principle">
              <div className="login-principle-icon">
                02
              </div>

              <div>
                <strong>
                  Investigate the evidence
                </strong>

                <p>
                  Reconstruct what happened and
                  inspect the evidence behind it.
                </p>
              </div>
            </div>

            <div className="login-principle">
              <div className="login-principle-icon">
                03
              </div>

              <div>
                <strong>
                  Reason with context
                </strong>

                <p>
                  Generate hypotheses with supporting
                  evidence and alternative explanations.
                </p>
              </div>
            </div>
          </div>

          <div className="login-tagline">
            <span className="login-tagline-line" />

            <span>
              Evidence before conclusion.
            </span>
          </div>
        </div>
      </section>

      <section className="login-form-panel">
        <div className="login-form-wrapper">
          <div className="login-mobile-brand">
            <div className="login-logo">
              IQ
            </div>

            <span>IncidentIQ</span>
          </div>

          <div className="login-form-header">
            <p className="login-form-eyebrow">
              ENGINEERING WORKSPACE
            </p>

            <h2>Welcome back</h2>

            <p>
              Sign in to continue investigating
              incidents.
            </p>
          </div>

          <form
            onSubmit={handleSubmit}
            className="login-form"
          >
            <div className="login-field">
              <label htmlFor="email">
                Email
              </label>

              <input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                placeholder="engineer@example.com"
                required
              />
            </div>

            <div className="login-field">
              <div className="login-password-label">
                <label htmlFor="password">
                  Password
                </label>
              </div>

              <input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                placeholder="Enter your password"
                required
              />
            </div>

            {error && (
              <div className="login-error">
                <strong>Sign in failed</strong>

                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              className="login-submit"
              disabled={loading}
            >
              {loading
                ? "Signing in..."
                : "Sign in to IncidentIQ"}
            </button>
          </form>

          <div className="login-security-note">
            <span className="login-security-dot" />

            <span>
              Secure engineering workspace
            </span>
          </div>
        </div>
      </section>
    </div>
  );
}

export default LoginPage;
