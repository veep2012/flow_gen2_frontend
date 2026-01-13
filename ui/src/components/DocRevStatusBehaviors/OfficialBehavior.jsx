import React from "react";
import PropTypes from "prop-types";

const OfficialBehavior = ({ selectedDoc }) => {
  if (!selectedDoc) {
    return (
      <div style={{ fontSize: "13px", color: "var(--color-text-muted)", padding: "8px 4px" }}>
        Select a document to view official documents.
      </div>
    );
  }

  const docName = `${selectedDoc.doc_name_unique || selectedDoc.title || "Document"}`;
  const revisionInfo = selectedDoc.rev_code_name || "N/A";

  return (
    <div style={{ fontSize: "13px", color: "var(--color-text-muted)", padding: "8px 4px" }}>
      <div style={{ marginBottom: "12px" }}>
        <strong>{docName}</strong>
        <div style={{ fontSize: "11px", marginTop: "4px" }}>
          Revision: {revisionInfo}
        </div>
      </div>
      <div style={{ fontSize: "12px", color: "var(--color-text-subtle)" }}>
        No official documents available yet.
      </div>
    </div>
  );
};

OfficialBehavior.propTypes = {
  selectedDoc: PropTypes.shape({
    doc_id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    doc_name_unique: PropTypes.string,
    title: PropTypes.string,
    rev_code_name: PropTypes.string,
  }),
};

export default OfficialBehavior;


