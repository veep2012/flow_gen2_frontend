import React from "react";
import PropTypes from "prop-types";

const DetailPanel = ({ activeDetailTab, onTabChange }) => {
  return (
    <div
      style={{
        flex: "1 1 0",
        background: "var(--color-surface)",
        border: "1px solid var(--color-border)",
        borderRadius: "12px",
        padding: 0,
        boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      <div className="detail-tabs">
        {["Revisions", "TAGs", "References", "Plan", "Information"].map((tab) => (
          <button
            key={tab}
            className={`detail-tab ${activeDetailTab === tab ? "active" : ""}`}
            onClick={() => onTabChange(tab)}
          >
            {tab}
          </button>
        ))}
      </div>
      <div
        className="detail-tab-panel"
        style={{
          flex: 1,
          minHeight: 0,
          maxHeight: "300px",
          overflowY: "auto",
          overflowX: "hidden",
          width: "100%",
          boxSizing: "border-box",
        }}
      >
        {activeDetailTab === "Revisions" ? (
          <div style={{ color: "var(--color-text-muted)", fontSize: "13px" }}>
            No revisions yet. A revision will be created automatically when you save a new document.
          </div>
        ) : (
          <div style={{ color: "var(--color-text-muted)", fontSize: "13px" }}>
            {activeDetailTab} content will appear here.
          </div>
        )}
      </div>
    </div>
  );
};

export default DetailPanel;

DetailPanel.propTypes = {
  activeDetailTab: PropTypes.string.isRequired,
  onTabChange: PropTypes.func.isRequired,
};
