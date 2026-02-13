import React from "react";
import PropTypes from "prop-types";
import { getFileIcon, getFileTypeLabel } from "../../utils/fileIcons";
import DistributionList from "../DistributionList/DistributionList";
import { getFileKey } from "../../utils/fileKey";

const IDCBehavior = ({
  selectedDoc,
  statusKey,
  infoActiveSubTab,
  onSubTabChange,
  uploadedFiles = {},
  expandedRevisions = {},
  onRevisionToggle,
  onSelectFile,
  onDownloadFile,
  selectedFileId,
  apiBase = "/api/v1",
}) => {
  const [commentText, setCommentText] = React.useState("");
  const [comments, setComments] = React.useState([]);

  const docId = selectedDoc?.doc_id;
  const docInfo = selectedDoc
    ? {
        type: selectedDoc.doc_type_name || "N/A",
        area: selectedDoc.area_name || "N/A",
        discipline: selectedDoc.discipline_name || "N/A",
      }
    : null;
  const currentRevStatusKey =
    selectedDoc?.rev_status_id != null ? String(selectedDoc.rev_status_id) : null;

  const idcLocalFiles = (docId && uploadedFiles[docId]?.[statusKey]) || [];

  // API files without explicit issued status belong to the current revision status only.
  const apiFiles = (docId && uploadedFiles[docId]?.["$api"]) || [];
  const issuedApiFiles = Array.isArray(apiFiles)
    ? apiFiles.filter((f) => {
        const issued = f?.issuedStatus ?? f?.issued_status ?? null;
        if (issued !== null && issued !== undefined && String(issued) !== "") {
          return String(issued) === String(statusKey);
        }
        return currentRevStatusKey === String(statusKey);
      })
    : [];

  const idcFiles = [...issuedApiFiles, ...(Array.isArray(idcLocalFiles) ? idcLocalFiles : [])];

  // Organize files by revision letter (RevA, RevB, RevC) - case insensitive
  const filesByRevision = {
    "Rev A": [],
    "Rev B": [],
    "Rev C": [],
    Other: [],
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
      <div className="idc-subtabs" style={{ display: "flex" }}>
        {["Comments", "Distribution list"].map((tab) => {
          const isActive =
            tab === "Comments"
              ? infoActiveSubTab === "Comments" ||
                infoActiveSubTab === "Files with Comments" ||
                infoActiveSubTab === "Written Comments"
              : infoActiveSubTab === tab;
          return (
            <button
              type="button"
              key={tab}
              className={`detail-tab ${isActive ? "active" : ""}`}
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
      <div
        className="idc-tab-panel"
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "0",
          padding: "12px",
          borderBottomLeftRadius: "0",
          borderBottomRightRadius: "0",
          overflow: "hidden",
          fontSize: "13px",
          color: "var(--color-text-muted)",
          flex: "1",
          minHeight: 0,
          height: "100%",
          maxHeight: "100%",
        }}
      >
        {infoActiveSubTab === "Comments" ||
        infoActiveSubTab === "Files with Comments" ||
        infoActiveSubTab === "Written Comments" ? (
          <>
            {docInfo && (
              <div
                style={{
                  fontSize: "11px",
                  color: "var(--color-text-subtle)",
                  marginBottom: "12px",
                  display: "none",
                }}
              >
                <div>Type: {docInfo.type}</div>
                <div>Area: {docInfo.area}</div>
                <div>Discipline: {docInfo.discipline}</div>
              </div>
            )}
            <div
              className="flow-box"
              style={{
                flex: "0 0 40%",
                borderRadius: "0px",
                marginTop: "0",
                marginRight: "0",
                marginLeft: "0",
                marginBottom: "-1px",
                padding: "0",
                display: "flex",
                flexDirection: "column",
                minHeight: 0,
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  fontSize: "13px",
                  fontWeight: 600,
                  color: "var(--color-text)",
                  padding: "12px",
                  background: "var(--color-surface-alt)",
                  borderBottom: "1px solid rgba(0, 0, 0, 0.08)",
                  marginTop: "0",
                  marginRight: "0",
                  marginBottom: "0",
                  marginLeft: "0",
                  flex: "0 0 auto",
                }}
              >
                Original Files
              </div>
              <div style={{ padding: "12px", flex: "1", minHeight: 0, overflow: "auto" }}>
                {idcFiles.length > 0 ? (
                  <div style={{ fontSize: "13px" }}>
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
                            <span
                              style={{
                                fontSize: "16px",
                                width: "20px",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                              }}
                            >
                              {isExpanded ? "📂" : "📁"}
                            </span>
                            <span style={{ display: "flex", alignItems: "center" }}>
                              {revision}
                            </span>
                          </button>
                          <div style={{ position: "relative" }}>
                            {isExpanded &&
                              revFiles.map((file, idx) => {
                                const fileName = typeof file === "string" ? file : file.name;
                                const documentNumber =
                                  typeof file === "object" ? file.documentNumber : null;
                                const displayName = documentNumber
                                  ? `${documentNumber} - ${fileName}`
                                  : fileName;
                                const fileIcon = getFileIcon(fileName);
                                const fileTypeLabel = getFileTypeLabel(fileName);
                                const isLastFile = idx === revFiles.length - 1;
                                const treeChar = isLastFile ? "└─ ─ " : "├─ ─ ";
                                const fileKey = getFileKey(file, idx);
                                const selectedKey = getFileKey(file);

                                return (
                                  <div
                                    key={`${revision}-${fileKey}`}
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
                                    <span
                                      style={{
                                        color: "var(--color-text-muted)",
                                        fontSize: "12px",
                                        fontFamily: "monospace",
                                        minWidth: "20px",
                                      }}
                                    >
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
                                        color:
                                          selectedFileId === selectedKey
                                            ? "var(--color-accent-hover)"
                                            : "var(--color-accent)",
                                        background:
                                          selectedFileId === selectedKey
                                            ? "rgba(59, 130, 246, 0.1)"
                                            : "transparent",
                                        border:
                                          selectedFileId === selectedKey
                                            ? "1px solid var(--color-accent)"
                                            : "none",
                                        cursor: "pointer",
                                        textAlign: "left",
                                        flex: 1,
                                        transition: "all 0.2s",
                                        borderRadius: "4px",
                                      }}
                                      onMouseEnter={(e) => {
                                        if (selectedFileId !== selectedKey) {
                                          e.currentTarget.style.color = "var(--color-accent-hover)";
                                          e.currentTarget.style.background = "rgba(0,0,0,0.05)";
                                        }
                                      }}
                                      onMouseLeave={(e) => {
                                        if (selectedFileId !== selectedKey) {
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
                  <div
                    style={{
                      fontSize: "13px",
                      color: "var(--color-text-subtle)",
                      minHeight: "auto",
                      maxHeight: "25%",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    No original files uploaded yet
                  </div>
                )}
              </div>
            </div>
            <div
              className="flow-box"
              style={{
                flex: "1 1 auto",
                minHeight: 0,
                maxHeight: "60%",
                display: "flex",
                flexDirection: "column",
                borderRadius: "0px",
                margin: "0",
                padding: "12px",
                marginTop: "-1px",
                overflow: "hidden",
              }}
            >
              <div className="detail-tabs" style={{ flex: "0 0 auto" }}>
                {["Files with Comments", "Written Comments"].map((tab) => {
                  const isActive = infoActiveSubTab === tab;
                  return (
                    <button
                      type="button"
                      key={tab}
                      className={`detail-tab ${isActive ? "active" : ""}`}
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
                  padding: "12px",
                  flex: "1 1 auto",
                  minHeight: 0,
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                  overflow: "auto",
                }}
              >
                {infoActiveSubTab === "Written Comments" ? (
                  <>
                    <div>
                      <label
                        htmlFor="idc-comment-text"
                        style={{
                          display: "block",
                          fontWeight: 600,
                          marginBottom: "6px",
                          color: "var(--color-text)",
                        }}
                      >
                        Your Comment
                      </label>
                      <textarea
                        id="idc-comment-text"
                        placeholder="Write your comment here..."
                        value={commentText}
                        onChange={(e) => setCommentText(e.target.value)}
                        style={{
                          width: "100%",
                          padding: "8px 12px",
                          border: "1px solid var(--color-border)",
                          borderRadius: "4px",
                          fontSize: "13px",
                          fontFamily: "inherit",
                          resize: "none",
                          minHeight: "60px",
                          boxSizing: "border-box",
                          color: "var(--color-text)",
                          backgroundColor: "var(--color-surface)",
                        }}
                      />
                    </div>
                    {commentText.trim() && (
                      <div style={{ display: "flex", gap: "8px", flex: "0 0 auto" }}>
                        <button
                          onClick={() => {
                            setCommentText("");
                          }}
                          style={{
                            flex: 1,
                            padding: "6px 12px",
                            background: "#6b7280",
                            color: "white",
                            border: "none",
                            borderRadius: "4px",
                            fontSize: "13px",
                            fontWeight: 600,
                            cursor: "pointer",
                            transition: "all 0.2s",
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = "#4b5563";
                            e.currentTarget.style.boxShadow = "0 4px 12px rgba(0, 0, 0, 0.3)";
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = "#6b7280";
                            e.currentTarget.style.boxShadow = "0 2px 6px rgba(0, 0, 0, 0.2)";
                          }}
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() => {
                            const now = new Date();
                            const dateStr = now.toLocaleDateString("en-US", {
                              year: "numeric",
                              month: "short",
                              day: "numeric",
                            });
                            const timeStr = now.toLocaleTimeString("en-US", {
                              hour: "2-digit",
                              minute: "2-digit",
                            });
                            const newComment = {
                              id: Date.now(),
                              text: commentText,
                              user: "Current User",
                              date: `${dateStr} at ${timeStr}`,
                            };
                            setComments([newComment, ...comments]);
                            setCommentText("");
                          }}
                          style={{
                            flex: 1,
                            padding: "6px 12px",
                            background: "#16a34a",
                            color: "white",
                            border: "none",
                            borderRadius: "4px",
                            fontSize: "13px",
                            fontWeight: 600,
                            cursor: "pointer",
                            transition: "all 0.2s",
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = "#15803d";
                            e.currentTarget.style.boxShadow = "0 4px 12px rgba(0, 0, 0, 0.3)";
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = "#16a34a";
                            e.currentTarget.style.boxShadow = "0 2px 6px rgba(0, 0, 0, 0.2)";
                          }}
                        >
                          Add Comment
                        </button>
                      </div>
                    )}
                    <div
                      style={{
                        flex: "1 1 auto",
                        minHeight: 0,
                        overflow: "auto",
                        paddingRight: "6px",
                      }}
                    >
                      {comments.length > 0 ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                          {comments.map((comment) => (
                            <div
                              key={comment.id}
                              style={{
                                padding: "12px",
                                background: "var(--color-surface-alt)",
                                borderRadius: "4px",
                                borderLeft: "3px solid var(--color-accent)",
                                position: "relative",
                              }}
                            >
                              <div
                                style={{
                                  display: "flex",
                                  justifyContent: "space-between",
                                  marginBottom: "8px",
                                  alignItems: "flex-start",
                                }}
                              >
                                <div
                                  style={{
                                    fontWeight: 600,
                                    color: "var(--color-text)",
                                    fontSize: "13px",
                                  }}
                                >
                                  {comment.user}
                                </div>
                                <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                                  <div
                                    style={{ fontSize: "12px", color: "var(--color-text-muted)" }}
                                  >
                                    {comment.date}
                                  </div>
                                  <button
                                    onClick={() => {
                                      setComments(comments.filter((c) => c.id !== comment.id));
                                    }}
                                    style={{
                                      padding: "3px 6px",
                                      background: "#ef4444",
                                      color: "white",
                                      border: "none",
                                      borderRadius: "3px",
                                      fontSize: "11px",
                                      fontWeight: 600,
                                      cursor: "pointer",
                                      transition: "all 0.2s",
                                    }}
                                    onMouseEnter={(e) => {
                                      e.currentTarget.style.background = "#dc2626";
                                    }}
                                    onMouseLeave={(e) => {
                                      e.currentTarget.style.background = "#ef4444";
                                    }}
                                    title="Delete this comment"
                                  >
                                    ✕ Delete
                                  </button>
                                </div>
                              </div>
                              <div
                                style={{
                                  fontSize: "13px",
                                  color: "var(--color-text)",
                                  lineHeight: "1.5",
                                  whiteSpace: "pre-wrap",
                                  wordBreak: "break-word",
                                }}
                              >
                                {comment.text}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div
                          style={{
                            fontSize: "12px",
                            color: "var(--color-text-muted)",
                            textAlign: "center",
                            paddingTop: "12px",
                          }}
                        >
                          No comments yet
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <div style={{ overflow: "auto" }}>No files with comments yet</div>
                )}
              </div>
            </div>
          </>
        ) : (
          <DistributionList docId={docId} apiBase={apiBase} />
        )}
      </div>
    </>
  );
};

IDCBehavior.propTypes = {
  selectedDoc: PropTypes.shape({
    doc_id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    rev_status_id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    doc_name_unique: PropTypes.string,
    title: PropTypes.string,
    doc_type_name: PropTypes.string,
    area_name: PropTypes.string,
    discipline_name: PropTypes.string,
  }),
  statusKey: PropTypes.string.isRequired,
  infoActiveSubTab: PropTypes.string.isRequired,
  onSubTabChange: PropTypes.func.isRequired,
  uploadedFiles: PropTypes.objectOf(
    PropTypes.arrayOf(
      PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.shape({
          fileId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
          id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
          name: PropTypes.string,
          documentNumber: PropTypes.string,
        }),
      ]),
    ),
  ),
  expandedRevisions: PropTypes.object,
  onRevisionToggle: PropTypes.func,
  onSelectFile: PropTypes.func,
  onDownloadFile: PropTypes.func,
  selectedFileId: PropTypes.string,
  apiBase: PropTypes.string,
};

export default IDCBehavior;
