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
  const [fileContextMenu, setFileContextMenu] = React.useState(null);
  const [commentedFiles, setCommentedFiles] = React.useState([]);
  const [commentedFilesLoading, setCommentedFilesLoading] = React.useState(false);
  const [commentedFilesError, setCommentedFilesError] = React.useState("");
  const [commentedSourceName, setCommentedSourceName] = React.useState("");
  const [commentedSourceFile, setCommentedSourceFile] = React.useState(null);
  const [userNameById, setUserNameById] = React.useState({});
  const [currentUserId, setCurrentUserId] = React.useState(1);
  const fileContextMenuRef = React.useRef(null);

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

  const issuedApiFiles = React.useMemo(
    () =>
      // API files without explicit issued status belong to the current revision status only.
      Array.isArray(uploadedFiles?.[docId]?.["$api"])
        ? uploadedFiles[docId]["$api"].filter((f) => {
            const issued = f?.issuedStatus ?? f?.issued_status ?? null;
            if (issued !== null && issued !== undefined && String(issued) !== "") {
              return String(issued) === String(statusKey);
            }
            return currentRevStatusKey === String(statusKey);
          })
        : [],
    [docId, uploadedFiles, statusKey, currentRevStatusKey],
  );

  const idcFiles = React.useMemo(() => {
    const localFiles = Array.isArray(uploadedFiles?.[docId]?.[statusKey])
      ? uploadedFiles[docId][statusKey]
      : [];
    const apiIds = new Set(issuedApiFiles.map((f) => f?.fileId ?? f?.id).filter(Boolean));
    const apiNames = new Set(
      issuedApiFiles.map((f) => String(f?.name ?? f?.filename ?? "").trim()).filter(Boolean),
    );

    const localOnly = localFiles.filter((f) => {
      const fileId = f && typeof f === "object" ? (f.fileId ?? f.id ?? null) : null;
      const fileName =
        f && typeof f === "object" ? String(f.name ?? f.filename ?? "").trim() : String(f || "");
      if (fileId) {
        return !apiIds.has(fileId);
      }
      return fileName ? !apiNames.has(fileName) : true;
    });

    return [...issuedApiFiles, ...localOnly];
  }, [docId, uploadedFiles, statusKey, issuedApiFiles]);

  const getSourceFileId = React.useCallback(
    (file) => (file && typeof file === "object" ? (file.fileId ?? file.id ?? null) : null),
    [],
  );

  const loadCommentedFiles = React.useCallback(
    async (file) => {
      const sourceFileId = getSourceFileId(file);
      const sourceName =
        file && typeof file === "object"
          ? String(file.name ?? file.filename ?? "Selected file")
          : String(file || "Selected file");

      if (!sourceFileId) {
        setCommentedFiles([]);
        setCommentedSourceFile(file);
        setCommentedSourceName(sourceName);
        setCommentedFilesError("Selected file must be uploaded before loading commented copies.");
        onSubTabChange("Files with Comments");
        return;
      }

      setCommentedFilesLoading(true);
      setCommentedFilesError("");
      setCommentedSourceFile(file);
      setCommentedSourceName(sourceName);
      onSubTabChange("Files with Comments");
      try {
        const response = await fetch(
          `${apiBase}/files/commented/list?file_id=${encodeURIComponent(String(sourceFileId))}`,
          {
            headers: { Accept: "application/json" },
          },
        );
        if (!response.ok) {
          const errorText = await response.text().catch(() => "");
          throw new Error(errorText || `Failed to load commented files (${response.status})`);
        }
        const payload = await response.json();
        const list = Array.isArray(payload)
          ? payload
          : Array.isArray(payload?.items)
            ? payload.items
            : Array.isArray(payload?.results)
              ? payload.results
              : [];
        setCommentedFiles(list);
      } catch (err) {
        setCommentedFiles([]);
        setCommentedFilesError(
          err instanceof Error ? err.message : "Failed to load commented files",
        );
      } finally {
        setCommentedFilesLoading(false);
      }
    },
    [apiBase, getSourceFileId, onSubTabChange],
  );

  const copyFileForComments = React.useCallback(
    async (file) => {
      const sourceFileId = getSourceFileId(file);
      const sourceName =
        file && typeof file === "object"
          ? String(file.name ?? file.filename ?? "selected-file.pdf")
          : String(file || "selected-file.pdf");

      if (!sourceFileId) {
        setCommentedFilesError("Selected file must be uploaded before creating commented copy.");
        onSubTabChange("Files with Comments");
        return;
      }

      setCommentedFilesLoading(true);
      setCommentedFilesError("");
      setCommentedSourceFile(file);
      setCommentedSourceName(sourceName);
      onSubTabChange("Files with Comments");

      try {
        const downloadResponse = await fetch(
          `${apiBase}/files/${encodeURIComponent(String(sourceFileId))}/download`,
          {
            headers: { Accept: "application/octet-stream" },
          },
        );
        if (!downloadResponse.ok) {
          const errorText = await downloadResponse.text().catch(() => "");
          throw new Error(
            errorText || `Failed to download source file (${downloadResponse.status})`,
          );
        }
        const blob = await downloadResponse.blob();
        const uploadFile = new File([blob], sourceName, {
          type: blob.type || "application/pdf",
        });
        const formData = new FormData();
        formData.append("file_id", String(sourceFileId));
        formData.append("user_id", String(currentUserId));
        formData.append("file", uploadFile);

        const createResponse = await fetch(`${apiBase}/files/commented`, {
          method: "POST",
          headers: { Accept: "application/json" },
          body: formData,
        });
        if (!createResponse.ok) {
          const errorText = await createResponse.text().catch(() => "");
          throw new Error(
            errorText || `Failed to create commented copy (${createResponse.status})`,
          );
        }
        await createResponse.json().catch(() => ({}));
        await loadCommentedFiles(file);
      } catch (err) {
        setCommentedFilesError(
          err instanceof Error ? err.message : "Failed to create commented copy",
        );
        setCommentedFilesLoading(false);
      }
    },
    [apiBase, currentUserId, getSourceFileId, loadCommentedFiles, onSubTabChange],
  );

  React.useEffect(() => {
    if (!fileContextMenu) return undefined;
    const closeMenu = (event) => {
      if (fileContextMenuRef.current?.contains(event.target)) {
        return;
      }
      setFileContextMenu(null);
    };
    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        setFileContextMenu(null);
      }
    };
    window.addEventListener("click", closeMenu);
    window.addEventListener("contextmenu", closeMenu);
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("click", closeMenu);
      window.removeEventListener("contextmenu", closeMenu);
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [fileContextMenu]);

  React.useEffect(() => {
    let isActive = true;
    const loadUsers = async () => {
      try {
        const usersRes = await fetch(`${apiBase}/people/users`, {
          headers: { Accept: "application/json" },
        });
        if (usersRes.ok) {
          const users = await usersRes.json();
          if (isActive && Array.isArray(users)) {
            const byId = Object.fromEntries(
              users.map((u) => [
                String(u.user_id),
                String(u.person_name || u.user_acronym || `User ${u.user_id}`),
              ]),
            );
            setUserNameById(byId);
          }
        }
      } catch {
        // Optional lookup data; use fallback labels.
      }

      try {
        const currentRes = await fetch(`${apiBase}/people/users/current_user`, {
          headers: { Accept: "application/json" },
        });
        if (currentRes.ok) {
          const current = await currentRes.json();
          const resolved = Number(current?.user_id);
          if (isActive && Number.isFinite(resolved) && resolved > 0) {
            setCurrentUserId(resolved);
          }
        }
      } catch {
        const envUserId = Number(import.meta.env.VITE_APP_USER_ID || 1);
        if (isActive && Number.isFinite(envUserId) && envUserId > 0) {
          setCurrentUserId(envUserId);
        }
      }
    };

    loadUsers();
    return () => {
      isActive = false;
    };
  }, [apiBase]);

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
                                      onContextMenu={(event) => {
                                        event.preventDefault();
                                        event.stopPropagation();
                                        setFileContextMenu({
                                          x: event.clientX,
                                          y: event.clientY,
                                          file,
                                        });
                                      }}
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
                  <div style={{ overflow: "auto" }}>
                    {commentedFilesLoading ? (
                      <div style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>
                        Loading commented files...
                      </div>
                    ) : commentedFilesError ? (
                      <div style={{ fontSize: "12px", color: "var(--color-danger)" }}>
                        {commentedFilesError}
                      </div>
                    ) : commentedSourceFile ? (
                      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                        <div style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>
                          Source: {commentedSourceName || "Selected file"}
                        </div>
                        <button
                          type="button"
                          onClick={() => onDownloadFile(commentedSourceFile)}
                          style={{
                            width: "100%",
                            textAlign: "left",
                            padding: "8px 10px",
                            border: "1px solid var(--color-border)",
                            background: "var(--color-surface-muted)",
                            color: "var(--color-text)",
                            cursor: "pointer",
                            fontSize: "12px",
                            fontWeight: 600,
                          }}
                          title="Open source file"
                        >
                          Original: {commentedSourceName || "Selected file"}
                        </button>
                        {commentedFiles.length === 0 && (
                          <div style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>
                            No commented copies in database yet for this file.
                          </div>
                        )}
                        {commentedFiles.map((item) => {
                          const displayName =
                            item?.filename || `Commented file #${item?.id ?? "-"}`;
                          const createdAt = item?.created_at ? new Date(item.created_at) : null;
                          const createdText =
                            createdAt && !Number.isNaN(createdAt.getTime())
                              ? createdAt.toLocaleString()
                              : "Unknown date";
                          const userText =
                            userNameById[String(item?.user_id)] ||
                            (item?.user_id ? `User ${item.user_id}` : "Unknown user");
                          return (
                            <button
                              type="button"
                              key={String(item?.id ?? displayName)}
                              onClick={() =>
                                window.open(
                                  `${apiBase}/files/commented/download?file_id=${encodeURIComponent(
                                    String(item?.id ?? ""),
                                  )}`,
                                  "_blank",
                                )
                              }
                              style={{
                                width: "100%",
                                textAlign: "left",
                                padding: "8px 10px",
                                border: "1px solid var(--color-border)",
                                background: "var(--color-surface)",
                                color: "var(--color-text)",
                                cursor: "pointer",
                                fontSize: "12px",
                              }}
                              title="Download commented file"
                            >
                              <div style={{ fontWeight: 600 }}>{displayName}</div>
                              <div style={{ fontSize: "11px", color: "var(--color-text-muted)" }}>
                                {createdText} • {userText}
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    ) : (
                      <div style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>
                        No files with comments yet
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
            {fileContextMenu && (
              <div
                ref={fileContextMenuRef}
                style={{
                  position: "fixed",
                  left: `${fileContextMenu.x}px`,
                  top: `${fileContextMenu.y}px`,
                  minWidth: "170px",
                  background: "var(--color-surface)",
                  border: "1px solid var(--color-border)",
                  boxShadow: "0 6px 18px rgba(0,0,0,0.2)",
                  zIndex: 7000,
                  padding: "4px",
                }}
                onContextMenu={(event) => event.preventDefault()}
              >
                <button
                  type="button"
                  style={{
                    width: "100%",
                    background: "transparent",
                    border: "none",
                    textAlign: "left",
                    padding: "8px 10px",
                    fontSize: "12px",
                    color: "var(--color-text)",
                    cursor: "pointer",
                  }}
                  onClick={() => {
                    onSelectFile(fileContextMenu.file);
                    copyFileForComments(fileContextMenu.file);
                    setFileContextMenu(null);
                  }}
                >
                  Copy for comments
                </button>
                <button
                  type="button"
                  style={{
                    width: "100%",
                    background: "transparent",
                    border: "none",
                    textAlign: "left",
                    padding: "8px 10px",
                    fontSize: "12px",
                    color: "var(--color-text)",
                    cursor: "pointer",
                  }}
                  onClick={() => {
                    onDownloadFile(fileContextMenu.file);
                    setFileContextMenu(null);
                  }}
                >
                  Download file
                </button>
              </div>
            )}
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
