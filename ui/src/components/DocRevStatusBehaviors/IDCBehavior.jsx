import React from "react";
import PropTypes from "prop-types";
import { getFileIcon, getFileTypeLabel } from "../../utils/fileIcons";

const IDCBehavior = ({ selectedDoc, infoActiveSubTab, onSubTabChange, uploadedFiles = {}, expandedRevisions = {}, onRevisionToggle, onSelectFile, onDownloadFile, selectedFileId }) => {
  const docName = selectedDoc ? `${selectedDoc.doc_name_unique || selectedDoc.title || "Document"}` : "No document selected";
  const docId = selectedDoc?.doc_id;
  const docInfo = selectedDoc ? {
    type: selectedDoc.doc_type_name || "N/A",
    area: selectedDoc.area_name || "N/A",
    discipline: selectedDoc.discipline_name || "N/A",
  } : null;

  // Get files from IDC status (statusKey "2" - copied from InDesign when "Issue to IDC" is clicked)
  const idcLocalFiles = (docId && uploadedFiles[docId]?.["2"]) || [];
  
  // Also get API files that have been issued to IDC (issuedStatus = "2")
  const apiFiles = (docId && uploadedFiles[docId]?.["$api"]) || [];
  const issuedApiFiles = Array.isArray(apiFiles) ? apiFiles.filter(f => f.issuedStatus === "2") : [];
  
  const idcFiles = [...issuedApiFiles, ...(Array.isArray(idcLocalFiles) ? idcLocalFiles : [])];

  // Organize files by revision letter (RevA, RevB, RevC) - case insensitive
  const filesByRevision = {
    "Rev A": [],
    "Rev B": [],
    "Rev C": [],
    "Other": [],
  };

  idcFiles.forEach((file) => {
    const fileName = typeof file === "string" ? file : file.name;
    const fileNameLower = (fileName || "").toLowerCase();
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
    <>
      <div className="flow-subtabs" style={{ display: "flex" }}>
        {["Comments", "Distribution list"].map((tab) => {
          const isActive = tab === "Comments" 
            ? (infoActiveSubTab === "Comments" || infoActiveSubTab === "Files with Comments" || infoActiveSubTab === "Written Comments")
            : infoActiveSubTab === tab;
          return (
            <button
              type="button"
              key={tab}
              className={`flow-subtab ${isActive ? "active" : ""}`}
              aria-pressed={isActive}
              onClick={() => {
                if (tab === "Comments") {
                  // If already in a mini-tab state, keep it; otherwise set to Comments
                  if (!["Files with Comments", "Written Comments"].includes(infoActiveSubTab)) {
                    onSubTabChange("Comments");
                  }
                } else {
                  onSubTabChange(tab);
                }
              }}
            >
              {tab}
            </button>
          );
        })}
      </div>
      <div className="detail-tab-panel" style={{ display: "flex", flexDirection: "column", gap: "0", padding: "0", borderBottomLeftRadius: "10px", borderBottomRightRadius: "10px", overflow: "hidden" }}>
        {infoActiveSubTab === "Comments" || infoActiveSubTab === "Files with Comments" || infoActiveSubTab === "Written Comments" ? (
          <>
            {docInfo && (
              <div style={{ fontSize: "11px", color: "var(--color-text-subtle)", marginBottom: "12px", display: "none" }}>
                <div>Type: {docInfo.type}</div>
                <div>Area: {docInfo.area}</div>
                <div>Discipline: {docInfo.discipline}</div>
              </div>
            )}
            <div className="flow-box" style={{ flex: "0 0 auto", borderRadius: "0px", margin: "0", padding: "0", marginBottom: "-1px", display: "flex", flexDirection: "column" }}>
              <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-text)", padding: "12px", background: "var(--color-surface-alt)", borderBottom: "1px solid rgba(0, 0, 0, 0.08)", margin: "0" }}>
                Original Files
              </div>
              <div style={{ padding: "12px" }}>
                {idcFiles.length > 0 ? (
                  <div style={{ fontSize: "13px" }}>
                    {["Rev A", "Rev B", "Rev C", "Other"].map((revision) => {
                      const revFiles = filesByRevision[revision] || [];

                      if (!revFiles.length) return null;

                      const revKey = `2-${revision}`;
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
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div style={{ fontSize: "13px", color: "var(--color-text-subtle)" }}>
                    No original files uploaded yet
                  </div>
                )}
              </div>
            </div>
            <div className="flow-box" style={{ flex: "1 1 auto", minHeight: 0, display: "flex", flexDirection: "column", borderRadius: "0px", margin: "0", padding: "12px", marginTop: "-1px" }}>
              <div className="flow-mini-tabs" style={{ flex: "0 0 auto" }}>
                {["Files with Comments", "Written Comments"].map((tab) => {
                  const isActive = infoActiveSubTab === tab;
                  return (
                    <button
                      type="button"
                      key={tab}
                      className={`flow-mini-tab ${isActive ? "active" : ""}`}
                      aria-pressed={isActive}
                      onClick={() => {
                        onSubTabChange(tab);
                      }}
                    >
                      {tab}
                    </button>
                  );
                })}
              </div>
              <div
                style={{
                  fontSize: "13px",
                  color: "var(--color-text-subtle)",
                  padding: "12px 0",
                  flex: "1 1 auto",
                  minHeight: 0,
                  overflow: "auto",
                }}
              >
                No files with comments yet
              </div>
            </div>
          </>
        ) : (
          <div className="flow-box" style={{ borderRadius: "0px", margin: "0" }}>
            <h4>Distribution List</h4>
            <div style={{ fontSize: "13px", color: "var(--color-text-subtle)" }}>
              No distribution list assigned
            </div>
          </div>
        )}
      </div>
    </>
  );
};

IDCBehavior.propTypes = {
  selectedDoc: PropTypes.shape({
    doc_id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    doc_name_unique: PropTypes.string,
    title: PropTypes.string,
    doc_type_name: PropTypes.string,
    area_name: PropTypes.string,
    discipline_name: PropTypes.string,
  }),
  infoActiveSubTab: PropTypes.string.isRequired,
  onSubTabChange: PropTypes.func.isRequired,
  uploadedFiles: PropTypes.object,
  expandedRevisions: PropTypes.object,
  onRevisionToggle: PropTypes.func,
  onSelectFile: PropTypes.func,
  onDownloadFile: PropTypes.func,
  selectedFileId: PropTypes.string,
};

export default IDCBehavior;
