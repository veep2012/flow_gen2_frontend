import React from "react";
import PropTypes from "prop-types";

const DefaultBehavior = ({ selectedDoc, behaviorName = "", behaviorFile = "" }) => {
  const docName = selectedDoc ? `${selectedDoc.doc_name_unique || selectedDoc.title || "Document"}` : "No document selected";

  return (
    <div style={{ fontSize: "13px", color: "var(--color-text-muted)", padding: "8px 4px" }}>
      <div style={{ marginBottom: "8px" }}>
        <strong>{docName}</strong>
      </div>
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
  selectedDoc: PropTypes.shape({
    doc_id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    doc_name_unique: PropTypes.string,
    title: PropTypes.string,
  }),
  behaviorName: PropTypes.string,
  behaviorFile: PropTypes.string,
};

export default DefaultBehavior;
