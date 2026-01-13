import React from "react";
import PropTypes from "prop-types";
import { getFileIcon, getFileTypeLabel } from "../../utils/fileIcons";

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
  onDeleteFile,
}) => {
  // Get files for the current document and status
  const docId = selectedDoc?.doc_id;
  // Get API-persisted files (single source of truth from database)
  const apiFiles = (docId && uploadedFiles[docId]?.["$api"]) || [];
  // Get local status files (not yet synced to API)
  const statusFiles = (docId && uploadedFiles[docId]?.[statusKey]) || [];
  
  // Deduplicate: only include status files that aren't already in API files
  const apiFileIds = new Set(apiFiles.map(f => f.fileId).filter(Boolean));
  const apiFileNames = new Set(apiFiles.map(f => f.name));
  const localOnlyFiles = statusFiles.filter(f => {
    const fileId = typeof f === "object" ? f.fileId : null;
    const fileName = typeof f === "object" ? f.name : f;
    // Include only if not in API by fileId or filename
    return fileId ? !apiFileIds.has(fileId) : !apiFileNames.has(fileName);
  });
  
  const allFiles = [...apiFiles, ...localOnlyFiles];
  const dragProps = uploadDragProps(statusKey);
  const docName = selectedDoc ? `${selectedDoc.doc_name_unique || selectedDoc.title || "Document"}` : "No document selected";

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, gap: "8px", minHeight: 0 }}>
      {/* File list area - takes remaining space and scrolls */}
      <div style={{ flex: 1, overflow: "auto", padding: "8px 0", minHeight: 0 }}>
        {allFiles.length > 0 ? (
          <>
            {["Rev A", "Rev B", "Rev C"].map((revision, revIdx) => {
              const revFiles =
                allFiles.filter((_, idx) => idx >= revIdx * 5 && idx < (revIdx + 1) * 5) || [];

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
                      const fileIcon = getFileIcon(fileName);
                      const fileTypeLabel = getFileTypeLabel(fileName);

                      return (
                        <div
                          key={`${revision}-${idx}`}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "4px",
                            padding: "4px 8px 4px 32px",
                            fontSize: "12px",
                            background: "transparent",
                            transition: "background 0.2s",
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = "rgba(0,0,0,0.05)";
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = "transparent";
                          }}
                        >
                          <button
                            type="button"
                            onClick={() => onOpenFile(file)}
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "6px",
                              padding: "4px 8px",
                              color: "var(--color-accent)",
                              background: "transparent",
                              border: "none",
                              cursor: "pointer",
                              textAlign: "left",
                              flex: 1,
                              transition: "color 0.2s",
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.color = "var(--color-accent-hover)";
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.color = "var(--color-accent)";
                            }}
                            title={`${fileTypeLabel} - Click to open ${displayName}`}
                          >
                            <span>{fileIcon}</span>
                            <span style={{ textDecoration: "underline" }}>{displayName}</span>
                          </button>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              onDeleteFile(file);
                            }}
                            style={{
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              width: "20px",
                              height: "20px",
                              padding: "0",
                              color: "var(--color-danger)",
                              background: "transparent",
                              border: "none",
                              cursor: "pointer",
                              fontSize: "12px",
                              transition: "opacity 0.2s",
                              opacity: "0.6",
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.opacity = "1";
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.opacity = "0.6";
                            }}
                            title={`Delete ${displayName}`}
                          >
                            ✕
                          </button>
                        </div>
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
  onDeleteFile: PropTypes.func.isRequired,
};

export default InDesignBehavior;
