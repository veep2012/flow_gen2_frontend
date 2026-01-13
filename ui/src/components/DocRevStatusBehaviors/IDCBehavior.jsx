import React from "react";
import PropTypes from "prop-types";
import { getFileIcon, getFileTypeLabel } from "../../utils/fileIcons";

const IDCBehavior = ({ selectedDoc, infoActiveSubTab, onSubTabChange, uploadedFiles, expandedRevisions, onRevisionToggle, onOpenFile }) => {
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
  const issuedApiFiles = apiFiles.filter(f => f.issuedStatus === "2");
  
  const idcFiles = [...issuedApiFiles, ...idcLocalFiles];

  // Organize files by revision letter (RevA, RevB, RevC) - case insensitive
  const filesByRevision = {
    "Rev A": [],
    "Rev B": [],
    "Rev C": [],
    "Other": [],
  };

  idcFiles.forEach((file) => {
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
    <>
      <div className="flow-subtabs" style={{ display: "flex" }}>
        {["Comments", "Distribution list"].map((tab) => (
          <button
            type="button"
            key={tab}
            className={`flow-subtab ${infoActiveSubTab === tab ? "active" : ""}`}
            aria-pressed={infoActiveSubTab === tab}
            onClick={() => onSubTabChange(tab)}
          >
            {tab}
          </button>
        ))}
      </div>
      <div className="flow-section">
        {docInfo && (
          <div style={{ fontSize: "11px", color: "var(--color-text-subtle)", marginBottom: "12px" }}>
            <div>Type: {docInfo.type}</div>
            <div>Area: {docInfo.area}</div>
            <div>Discipline: {docInfo.discipline}</div>
          </div>
        )}
        {infoActiveSubTab === "Comments" ? (
          <>
            <div className="flow-box">
              <h4>Original Files</h4>
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
                                  <span style={{ textDecoration: "underline" }}>{displayName}</span>
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
            <div className="flow-box">
              <div style={{ display: "flex", gap: "8px", marginBottom: "10px" }}>
                {["Files with Comments", "Written Comments"].map((tab) => (
                  <button
                    type="button"
                    key={tab}
                    className="flow-mini-tab"
                    style={{
                      flex: 1,
                      padding: "8px 10px",
                      borderBottom:
                        infoActiveSubTab === tab
                          ? "2px solid var(--color-primary)"
                          : "1px solid var(--color-border)",
                      fontWeight: infoActiveSubTab === tab ? 700 : 500,
                      color:
                        infoActiveSubTab === tab ? "var(--color-primary)" : "var(--color-text)",
                      cursor: "pointer",
                      textAlign: "center",
                      background: "transparent",
                      border: "none",
                    }}
                    aria-pressed={infoActiveSubTab === tab}
                    onClick={() => onSubTabChange(tab)}
                  >
                    {tab}
                  </button>
                ))}
              </div>
              <div
                style={{
                  fontSize: "13px",
                  color: "var(--color-text-subtle)",
                  padding: "12px 0",
                }}
              >
                No files with comments yet
              </div>
            </div>
          </>
        ) : (
          <div className="flow-box">
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
  onOpenFile: PropTypes.func,
};

export default IDCBehavior;
