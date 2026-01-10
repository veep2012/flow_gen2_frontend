import React from "react";
import PropTypes from "prop-types";

const InDesignBehavior = ({
  statusKey,
  uploadedFiles,
  expandedRevisions,
  onRevisionToggle,
  isDraggingUpload,
  uploadDragProps,
  onUploadClick,
  uploadInputRef,
  onFileSelect,
}) => {
  const files = uploadedFiles[statusKey] || [];
  const dragProps = uploadDragProps(statusKey);

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, gap: "8px" }}>
      {files.length > 0 ? (
        <div style={{ flex: 1, overflow: "auto", padding: "8px 0" }}>
          {["Rev A", "Rev B", "Rev C"].map((revision, revIdx) => {
            const revFiles =
              files.filter((_, idx) => idx >= revIdx * 5 && idx < (revIdx + 1) * 5) || [];

            if (!revFiles.length && revIdx > 0) return null;

            const revKey = `${statusKey}-${revision}`;
            const isExpanded = expandedRevisions[revKey]?.isOpen !== false;

            return (
              <div key={revision} style={{ marginBottom: "4px" }}>
                <button
                  type="button"
                  onClick={() => onRevisionToggle(revKey)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    padding: "6px 8px",
                    cursor: "pointer",
                    color: "var(--color-text)",
                    fontSize: "13px",
                    fontWeight: 600,
                    userSelect: "none",
                    background: "transparent",
                    border: "none",
                    width: "100%",
                    textAlign: "left",
                  }}
                  aria-expanded={isExpanded}
                >
                  <span style={{ fontSize: "12px", width: "16px" }}>{isExpanded ? "▼" : "▶"}</span>
                  <span>{revision}</span>
                </button>
                {isExpanded &&
                  revFiles.map((file, idx) => (
                    <div
                      key={`${revision}-${idx}`}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        padding: "4px 8px 4px 32px",
                        color: "var(--color-accent)",
                        fontSize: "12px",
                      }}
                    >
                      <span>📄</span>
                      <span>{file}</span>
                    </div>
                  ))}
              </div>
            );
          })}
          <div style={{ flex: 1 }} />
          <button
            onClick={onUploadClick}
            style={{
              padding: "6px 12px",
              background: "var(--color-accent)",
              color: "var(--color-surface)",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
              fontSize: "12px",
              marginTop: "8px",
              alignSelf: "flex-start",
            }}
          >
            + Add files
          </button>
        </div>
      ) : (
        <>
          <div style={{ flex: 1 }} />
          <button
            type="button"
            className={`flow-upload ${isDraggingUpload ? "dragging" : ""}`}
            {...dragProps}
            onClick={onUploadClick}
            aria-label="Upload PDF files"
          >
            Drag & drop PDF files here
            <br />
            or click to browse • Multiple files supported
          </button>
        </>
      )}
      <input
        ref={uploadInputRef}
        type="file"
        multiple
        accept="application/pdf"
        style={{ display: "none" }}
        onChange={(e) => onFileSelect(e, statusKey)}
      />
    </div>
  );
};

InDesignBehavior.propTypes = {
  statusKey: PropTypes.string.isRequired,
  uploadedFiles: PropTypes.objectOf(PropTypes.arrayOf(PropTypes.string)).isRequired,
  expandedRevisions: PropTypes.objectOf(
    PropTypes.shape({
      isOpen: PropTypes.bool,
    }),
  ).isRequired,
  onRevisionToggle: PropTypes.func.isRequired,
  isDraggingUpload: PropTypes.bool.isRequired,
  uploadDragProps: PropTypes.func.isRequired,
  onUploadClick: PropTypes.func.isRequired,
  uploadInputRef: PropTypes.shape({ current: PropTypes.instanceOf(Element) }),
  onFileSelect: PropTypes.func.isRequired,
};

export default InDesignBehavior;
