import React from "react";
import PropTypes from "prop-types";

const InDesignBehavior = ({
  selectedDoc,
  statusKey,
  uploadedFiles,
  expandedRevisions,
  onRevisionToggle,
  isDraggingUpload,
  uploadDragProps,
  onUploadClick,
  uploadInputRef,
  onFileSelect,
  onOpenFile,
}) => {
  // Get files for the current document and status
  const docId = selectedDoc?.doc_id;
  const files = (docId && uploadedFiles[docId]?.[statusKey]) || [];
  const dragProps = uploadDragProps(statusKey);
  const docName = selectedDoc ? `${selectedDoc.doc_name_unique || selectedDoc.title || "Document"}` : "No document selected";

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, gap: "8px", minHeight: 0 }}>
      {/* Document info header */}
      <div style={{ fontSize: "11px", color: "var(--color-text-subtle)", padding: "8px 0", borderBottom: "1px solid var(--color-border)" }}>
        <strong>{docName}</strong>
        {selectedDoc && (
          <>
            <div>Revision: {selectedDoc.rev_code_name || "N/A"}</div>
            <div>Progress: {selectedDoc.percentage !== null ? `${selectedDoc.percentage}%` : "N/A"}</div>
          </>
        )}
      </div>
      {/* File list area - takes remaining space and scrolls */}
      <div style={{ flex: 1, overflow: "auto", padding: "8px 0", minHeight: 0 }}>
        {files.length > 0 ? (
          <>
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
                    <span style={{ fontSize: "12px", width: "16px" }}>
                      {isExpanded ? "▼" : "▶"}
                    </span>
                    <span>{revision}</span>
                  </button>
                  {isExpanded &&
                    revFiles.map((file, idx) => {
                      // Handle both string and object file formats
                      const fileName = typeof file === "string" ? file : file.name;
                      const documentNumber = typeof file === "object" ? file.documentNumber : null;
                      const displayName = documentNumber ? `${documentNumber} - ${fileName}` : fileName;

                      return (
                        <button
                          key={`${revision}-${idx}`}
                          type="button"
                          onClick={() => onOpenFile(file)}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "6px",
                            padding: "4px 8px 4px 32px",
                            color: "var(--color-accent)",
                            fontSize: "12px",
                            background: "transparent",
                            border: "none",
                            cursor: "pointer",
                            textAlign: "left",
                            width: "100%",
                            transition: "background 0.2s",
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = "rgba(0,0,0,0.05)";
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = "transparent";
                          }}
                          title={`Click to open ${displayName}`}
                        >
                          <span>📄</span>
                          <span style={{ textDecoration: "underline" }}>{displayName}</span>
                        </button>
                      );
                    })}
                </div>
              );
            })}
          </>
        ) : (
          <div style={{ color: "var(--color-text-muted)", fontSize: "13px", padding: "8px" }}>
            No files added yet
          </div>
        )}
      </div>

      {/* Drag and drop area - always at bottom */}
      <button
        type="button"
        className={`flow-upload ${isDraggingUpload ? "dragging" : ""}`}
        {...dragProps}
        onClick={onUploadClick}
        aria-label="Upload PDF files"
        style={{
          padding: "16px",
          flexShrink: 0,
        }}
      >
        Drag & drop PDF files here
        <br />
        or click to browse • Multiple files supported
      </button>
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
  selectedDoc: PropTypes.shape({
    doc_id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    doc_name_unique: PropTypes.string,
    title: PropTypes.string,
  }),
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
  onOpenFile: PropTypes.func.isRequired,
};

export default InDesignBehavior;
