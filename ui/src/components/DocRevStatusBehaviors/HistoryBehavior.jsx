import React from "react";
import PropTypes from "prop-types";

const HistoryBehavior = ({ selectedDoc }) => {
  if (!selectedDoc) {
    return (
      <div style={{ fontSize: "13px", color: "var(--color-text-muted)", padding: "8px 4px" }}>
        Select a document to view its revision history.
      </div>
    );
  }

  return (
    <div style={{ fontSize: "13px", color: "var(--color-text-muted)", padding: "8px 4px" }}>
      <div style={{ fontSize: "12px", color: "var(--color-text-subtle)" }}>
        No revision history available yet.
      </div>
    </div>
  );
};

HistoryBehavior.propTypes = {
  selectedDoc: PropTypes.shape({
    doc_id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    doc_name_unique: PropTypes.string,
    title: PropTypes.string,
    rev_seq_num: PropTypes.number,
  }),
};

export default HistoryBehavior;


