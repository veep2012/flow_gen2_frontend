import React from "react";
import PropTypes from "prop-types";

const DefaultBehavior = ({ behaviorName = "", behaviorFile = "" }) => {
  return (
    <div style={{ fontSize: "13px", color: "var(--color-text-muted)", padding: "8px 4px" }}>
      {behaviorName
        ? `No UI layout mapped for "${behaviorName}".`
        : "No UI layout mapped for this status."}
      {behaviorFile ? (
        <span style={{ display: "block", marginTop: "6px", fontSize: "12px" }}>
          Behavior key: <span title={behaviorFile}>{behaviorFile}</span>
        </span>
      ) : null}
    </div>
  );
};

DefaultBehavior.propTypes = {
  behaviorName: PropTypes.string,
  behaviorFile: PropTypes.string,
};

export default DefaultBehavior;
