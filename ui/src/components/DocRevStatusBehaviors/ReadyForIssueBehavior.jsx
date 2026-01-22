import React from "react";
import PropTypes from "prop-types";

const ReadyForIssueBehavior = ({ selectedDoc }) => {
  if (!selectedDoc) {
    return (
      <div style={{ fontSize: "13px", color: "var(--color-text-muted)", padding: "8px 4px" }}>
        Select a document to view ready-for-issue information.
      </div>
    );
  }

  return (
    <div style={{ fontSize: "13px", color: "var(--color-text-muted)", padding: "8px 4px" }}>
      <div style={{ fontSize: "12px", color: "var(--color-text-subtle)" }}>
        Document is not yet ready for issue.
      </div>
    </div>
  );
};

ReadyForIssueBehavior.propTypes = {
  selectedDoc: PropTypes.shape({
    doc_id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    doc_name_unique: PropTypes.string,
    title: PropTypes.string,
    percentage: PropTypes.number,
  }),
};

export default ReadyForIssueBehavior;
