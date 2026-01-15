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
  onSelectFile,
  onDownloadFile,
  onDeleteFile,
  selectedFileId,
}) => {
  // Get files for the current document and status
  const docId = selectedDoc?.doc_id;
  // Get API-persisted files (single source of truth from database)
  const apiFiles = (docId && uploadedFiles[docId]?.["$api"]) || [];
  // Get local status files (not yet synced to API)
  const statusFiles = (docId && uploadedFiles[docId]?.[statusKey]) || [];
  
  // Filter API files that haven't been issued to other statuses
  const availableApiFiles = apiFiles.filter(f => !f.issuedStatus || f.issuedStatus === statusKey);
  
  // Deduplicate: only include status files that aren't already in API files
  const apiFileIds = new Set(availableApiFiles.map(f => f.fileId).filter(Boolean));
  const apiFileNames = new Set(availableApiFiles.map(f => f.name));
  const localOnlyFiles = statusFiles.filter(f => {
    const fileId = typeof f === "object" ? f.fileId : null;
    const fileName = typeof f === "object" ? f.name : f;
    // Include only if not in API by fileId or filename
    return fileId ? !apiFileIds.has(fileId) : !apiFileNames.has(fileName);
  });
  
  const allFiles = [...availableApiFiles, ...localOnlyFiles];
  
  // Debug logging
  React.useEffect(() => {
    console.log("InDesignBehavior - statusKey:", statusKey, "allFiles:", allFiles, "apiFiles:", apiFiles, "statusFiles:", statusFiles);
  }, [allFiles, statusKey, apiFiles, statusFiles]);
  
  const dragProps = uploadDragProps(statusKey);
  const docName = selectedDoc ? `${selectedDoc.doc_name_unique || selectedDoc.title || "Document"}` : "No document selected";

  // Organize files by revision letter (RevA, RevB, RevC) - case insensitive
  const filesByRevision = {
    "Rev A": [],
    "Rev B": [],
    "Rev C": [],
    "Other": [],
  };

  allFiles.forEach((file) => {
    const fileName = typeof file === "string" ? file : file.name;
    const fileNameLower = fileName.toLowerCase();
    if (fileNameLower.includes("reva")) {
      filesByRevision["Rev A"].push(file);
    } else if (fileNameLower.includes("revb")) {
      filesByRevision["Rev B"].push(file);
    } else if (fileNameLower.includes("revc")) {
      filesByRevision["Rev C"].push(file);
    } else {
      filesByRevision["Other"].push(file);
    }
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, gap: "8px", minHeight: 0 }}>
      {/* File list area - takes remaining space and scrolls */}
      <div style={{ flex: 1, overflow: "auto", padding: "8px 0", minHeight: 0 }}>
        {allFiles.length > 0 ? (
          <>
            {["Rev A", "Rev B", "Rev C", "Other"].map((revision) => {
              const revFiles = filesByRevision[revision] || [];

              if (!revFiles.length) return null;

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
                    <span style={{ fontSize: "16px", width: "20px", display: "flex", alignItems: "center", justifyContent: "center" }}>
                      {isExpanded ? "📂" : "📁"}
                    </span>
                    <span style={{ display: "flex", alignItems: "center" }}>{revision}</span>
                  </button>
                  <div style={{ position: "relative" }}>
                    {isExpanded &&
                      revFiles.map((file, idx) => {
                      // Handle both string and object file formats
                      const fileName = typeof file === "string" ? file : file.name;
                      const documentNumber = typeof file === "object" ? file.documentNumber : null;
                      const displayName = documentNumber ? `${documentNumber} - ${fileName}` : fileName;
                      const fileIcon = getFileIcon(fileName);
                      const fileTypeLabel = getFileTypeLabel(fileName);
                      const isLastFile = idx === revFiles.length - 1;
                      const treeChar = isLastFile ? "└─ ─ " : "├─ ─ ";

                      return (
                        <div
                          key={`${revision}-${idx}`}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "0px",
                            padding: "4px 8px 4px 8px",
                            fontSize: "12px",
                            background: "transparent",
                            transition: "background 0.2s",
                            marginLeft: "8px",
                            overflow: "hidden",
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = "rgba(0,0,0,0.05)";
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = "transparent";
                          }}
                        >
                          {!isLastFile && (
                            <div
                              style={{
                                width: "1px",
                                height: "28px",
                                background: "var(--color-border)",
                                position: "absolute",
                                left: "25px",
                                top: "100%",
                                zIndex: "1",
                                clipPath: "inset(0 0 0 10px)",
                              }}
                            />
                          )}
                          <span style={{ color: "var(--color-text-muted)", fontSize: "12px", fontFamily: "monospace", minWidth: "20px" }}>
                            {treeChar}
                          </span>
                          <button
                            type="button"
                            onClick={() => onSelectFile(file)}
                            onDoubleClick={() => onDownloadFile(file)}
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "6px",
                              padding: "4px 8px",
                              color: selectedFileId === `${file.fileId}-${file.name}` || selectedFileId === fileName ? "var(--color-accent-hover)" : "var(--color-accent)",
                              background: selectedFileId === `${file.fileId}-${file.name}` || selectedFileId === fileName ? "rgba(59, 130, 246, 0.1)" : "transparent",
                              border: selectedFileId === `${file.fileId}-${file.name}` || selectedFileId === fileName ? "1px solid var(--color-accent)" : "none",
                              cursor: "pointer",
                              textAlign: "left",
                              flex: 1,
                              transition: "all 0.2s",
                              borderRadius: "4px",
                            }}
                            onMouseEnter={(e) => {
                              if (selectedFileId !== `${file.fileId}-${file.name}` && selectedFileId !== fileName) {
                                e.currentTarget.style.color = "var(--color-accent-hover)";
                                e.currentTarget.style.background = "rgba(0,0,0,0.05)";
                              }
                            }}
                            onMouseLeave={(e) => {
                              if (selectedFileId !== `${file.fileId}-${file.name}` && selectedFileId !== fileName) {
                                e.currentTarget.style.color = "var(--color-accent)";
                                e.currentTarget.style.background = "transparent";
                              }
                            }}
                            title={`${fileTypeLabel} - Click to select, double-click to download ${displayName}`}
                          >
                            <span>
                              {typeof fileIcon === "string" && !fileIcon.includes(".") ? (
                                fileIcon
                              ) : (
                                <img 
                                  src={fileIcon} 
                                  alt="file icon" 
                                  style={{ width: "16px", height: "16px" }} 
                                />
                              )}
                            </span>
                            <span>{displayName}</span>
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
  onSelectFile: PropTypes.func.isRequired,
  onDownloadFile: PropTypes.func.isRequired,
  onDeleteFile: PropTypes.func.isRequired,
  selectedFileId: PropTypes.string,
};

export default InDesignBehavior;
