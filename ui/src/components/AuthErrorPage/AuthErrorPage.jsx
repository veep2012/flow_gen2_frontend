import React from "react";
import PropTypes from "prop-types";

const shellStyle = {
  minHeight: "100vh",
  display: "grid",
  placeItems: "center",
  padding: "24px",
  background:
    "radial-gradient(circle at top left, rgba(197, 59, 46, 0.18), transparent 42%), linear-gradient(135deg, #fff8f1 0%, #f4ede1 52%, #e5ddd0 100%)",
  color: "#241a14",
};

const cardStyle = {
  width: "min(100%, 760px)",
  background: "rgba(255, 251, 247, 0.92)",
  border: "1px solid rgba(92, 62, 43, 0.18)",
  borderRadius: "28px",
  padding: "32px",
  boxShadow: "0 24px 70px rgba(65, 40, 24, 0.16)",
  backdropFilter: "blur(10px)",
};

const eyebrowStyle = {
  display: "inline-flex",
  alignItems: "center",
  gap: "8px",
  padding: "6px 12px",
  borderRadius: "999px",
  background: "#f5d7cb",
  color: "#8a2f24",
  fontSize: "12px",
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  fontWeight: 700,
};

const titleStyle = {
  margin: "18px 0 10px",
  fontSize: "clamp(2rem, 4vw, 3.25rem)",
  lineHeight: 1,
  fontWeight: 800,
};

const bodyStyle = {
  margin: 0,
  fontSize: "1rem",
  lineHeight: 1.6,
  color: "#4c372c",
  maxWidth: "58ch",
};

const panelStyle = {
  marginTop: "24px",
  padding: "18px 20px",
  borderRadius: "18px",
  background: "#fff4eb",
  border: "1px solid rgba(138, 47, 36, 0.14)",
};

const actionsStyle = {
  display: "flex",
  flexWrap: "wrap",
  gap: "12px",
  marginTop: "24px",
};

const primaryButtonStyle = {
  border: "none",
  borderRadius: "999px",
  padding: "13px 20px",
  background: "#8a2f24",
  color: "#fffaf5",
  fontWeight: 700,
  cursor: "pointer",
};

const secondaryButtonStyle = {
  borderRadius: "999px",
  padding: "13px 20px",
  background: "transparent",
  color: "#8a2f24",
  border: "1px solid rgba(138, 47, 36, 0.35)",
  fontWeight: 700,
  cursor: "pointer",
};

function describeStatus(status) {
  if (status === 400) {
    return {
      label: "Authentication configuration issue",
      title: "Session verification failed",
      description:
        "Flow received your request, but the authentication details were incomplete or invalid. Refresh your session first. If the problem persists, sign in again so the proxy can rebuild a clean identity context.",
    };
  }
  return {
    label: "Authentication required",
    title: "Sign-in is required",
    description:
      "Your Flow session is no longer trusted for protected API calls. Refresh the page first. If that does not restore access, sign in again to establish a new authenticated session.",
  };
}

function resolveAuthStartBase(rawValue) {
  const value = String(rawValue || "").trim();
  if (!value) {
    return "/oauth2/start";
  }
  try {
    return new URL(value, window.location.origin).toString();
  } catch {
    console.warn("Invalid VITE_AUTH_START_URL, falling back to /oauth2/start");
    return "/oauth2/start";
  }
}

export default function AuthErrorPage({ authError }) {
  const status = Number(authError?.status) || 401;
  const descriptor = describeStatus(status);
  const detail = String(authError?.detail || "").trim();
  const requestId = String(authError?.requestId || "").trim();
  const authStartBase = React.useMemo(
    () => resolveAuthStartBase(import.meta.env.VITE_AUTH_START_URL),
    [],
  );

  const handleRefresh = React.useCallback(() => {
    window.location.reload();
  }, []);

  const handleSignIn = React.useCallback(() => {
    const redirectPath = `${window.location.pathname}${window.location.search}${window.location.hash}`;
    const target = new URL(authStartBase, window.location.origin);
    target.searchParams.set("rd", redirectPath || "/");
    window.location.assign(target.toString());
  }, [authStartBase]);

  return (
    <main style={shellStyle}>
      <section style={cardStyle} aria-labelledby="auth-error-title">
        <div style={eyebrowStyle}>
          <span>Flow access check</span>
          <span aria-hidden="true">/</span>
          <span>{descriptor.label}</span>
        </div>
        <h1 id="auth-error-title" style={titleStyle}>
          {descriptor.title}
        </h1>
        <p style={bodyStyle}>{descriptor.description}</p>

        <div style={panelStyle}>
          <strong>API response</strong>
          <p style={{ ...bodyStyle, marginTop: "10px" }}>
            Status: <strong>{status}</strong>
            {detail ? ` · ${detail}` : ""}
          </p>
          {requestId ? (
            <p style={{ ...bodyStyle, marginTop: "10px" }}>
              Request ID: <code>{requestId}</code>
            </p>
          ) : null}
        </div>

        <div style={actionsStyle}>
          <button type="button" style={primaryButtonStyle} onClick={handleRefresh}>
            Refresh session
          </button>
          <button type="button" style={secondaryButtonStyle} onClick={handleSignIn}>
            Sign in as different user
          </button>
        </div>

        <p style={{ ...bodyStyle, marginTop: "18px", fontSize: "0.95rem" }}>
          If access still fails after re-authentication, contact support and include the request ID
          shown above.
        </p>
      </section>
    </main>
  );
}

AuthErrorPage.propTypes = {
  authError: PropTypes.shape({
    status: PropTypes.number,
    detail: PropTypes.string,
    requestId: PropTypes.string,
  }).isRequired,
};
