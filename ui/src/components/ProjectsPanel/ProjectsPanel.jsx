import React from "react";
import PropTypes from "prop-types";

const ProjectsPanel = ({ project, setProject, projects, projectsError, cabinetTabs, userMenuOpen, setUserMenuOpen }) => {
  return (
    <div
      style={{
        background: "var(--color-success-soft)",
        border: "1px solid var(--color-success-border)",
        borderRadius: "8px",
        padding: "12px 14px",
        marginBottom: "4px",
        boxShadow: "0 2px 6px rgba(0,0,0,0.08)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <label
          htmlFor="projects-panel-select"
          style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-success-text)" }}
        >
          Project:
        </label>
        <select
          id="projects-panel-select"
          value={project}
          onChange={(e) => setProject(e.target.value)}
          aria-label="Select project"
          style={{
            border: "1px solid var(--color-success-border-strong)",
            borderRadius: "8px",
            padding: "7px 10px",
            fontSize: "13px",
            color: "var(--color-text)",
            background: "var(--color-surface)",
            minWidth: "220px",
            cursor: "pointer",
          }}
        >
          <option value="">Project number</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.label}
            </option>
          ))}
        </select>
        {projectsError ? (
          <span style={{ fontSize: "12px", color: "var(--color-danger)" }}>{projectsError}</span>
        ) : null}
        <div className="task-cabinet" style={{ marginLeft: "auto", padding: 0 }}>
          <div className="task-cabinet__label">Task cabinet:</div>
          {cabinetTabs.map((tab) => (
            <div key={tab.label} className="task-tab">
              <span style={{ color: "var(--color-success-text)", fontWeight: 600 }}>
                {tab.label}
              </span>
              <span className="task-tab__badge" style={{ background: tab.tone }}>
                {tab.count}
              </span>
            </div>
          ))}
        </div>
        
        {/* User Avatar */}
        <div style={{ position: "relative", marginLeft: "12px" }}>
          <button
            type="button"
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "36px",
              height: "36px",
              borderRadius: "50%",
              background: "var(--color-primary)",
              color: "white",
              border: "2px solid var(--color-primary-soft)",
              cursor: "pointer",
              fontSize: "16px",
              fontWeight: 700,
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.15)";
              e.currentTarget.style.transform = "scale(1.05)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = "none";
              e.currentTarget.style.transform = "scale(1)";
            }}
            title="User menu"
            aria-label="User menu"
          >
            👤
          </button>
          
          {userMenuOpen && (
            <div
              style={{
                position: "absolute",
                top: "100%",
                right: "0",
                background: "var(--color-surface)",
                border: "1px solid var(--color-border)",
                borderRadius: "8px",
                boxShadow: "0 4px 12px rgba(0,0,0,0.12)",
                minWidth: "200px",
                zIndex: 1000,
                marginTop: "8px",
                overflow: "hidden",
                animation: "slideDown 0.2s ease"
              }}
            >
              <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--color-border-soft)" }}>
                <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--color-text)" }}>John Doe</div>
                <div style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>john.doe@example.com</div>
              </div>
              
              <button
                type="button"
                onClick={() => { console.log("Profile"); setUserMenuOpen(false); }}
                style={{
                  display: "block",
                  width: "100%",
                  padding: "10px 16px",
                  background: "transparent",
                  border: "none",
                  textAlign: "left",
                  cursor: "pointer",
                  fontSize: "13px",
                  color: "var(--color-text)",
                  transition: "background 0.2s",
                  borderBottom: "1px solid var(--color-border-soft)",
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = "var(--color-surface-muted)"}
                onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
              >
                👤 My Profile
              </button>
              
              <button
                type="button"
                onClick={() => { console.log("Settings"); setUserMenuOpen(false); }}
                style={{
                  display: "block",
                  width: "100%",
                  padding: "10px 16px",
                  background: "transparent",
                  border: "none",
                  textAlign: "left",
                  cursor: "pointer",
                  fontSize: "13px",
                  color: "var(--color-text)",
                  transition: "background 0.2s",
                  borderBottom: "1px solid var(--color-border-soft)",
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = "var(--color-surface-muted)"}
                onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
              >
                ⚙ Settings
              </button>
              
              <button
                type="button"
                onClick={() => { console.log("Logout"); setUserMenuOpen(false); }}
                style={{
                  display: "block",
                  width: "100%",
                  padding: "10px 16px",
                  background: "transparent",
                  border: "none",
                  textAlign: "left",
                  cursor: "pointer",
                  fontSize: "13px",
                  color: "var(--color-danger)",
                  transition: "background 0.2s",
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = "var(--color-danger-soft)"}
                onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
              >
                🚪 Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProjectsPanel;

ProjectsPanel.propTypes = {
  project: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  setProject: PropTypes.func.isRequired,
  projects: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
      label: PropTypes.string.isRequired,
    }),
  ).isRequired,
  projectsError: PropTypes.string,
  cabinetTabs: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.string.isRequired,
      count: PropTypes.number.isRequired,
      tone: PropTypes.string.isRequired,
    }),
  ).isRequired,
  userMenuOpen: PropTypes.bool.isRequired,
  setUserMenuOpen: PropTypes.func.isRequired,
};
