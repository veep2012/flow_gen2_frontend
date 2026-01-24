import React from "react";
import { documentGridColumns } from "./grids/documents";
import { getFileKey } from "./utils/fileKey";
import { normalizeFile } from "./utils/normalizeFile";
import { useFetchDocuments } from "./hooks/useFetchDocuments";
import { resolveBehaviorByFile } from "./components/DocRevStatusBehaviors";

const columns = documentGridColumns.map(({ id, label, field, hidden }) => ({
  key: field,
  id,
  label,
  hidden: Boolean(hidden),
}));

const visibleColumns = columns.filter((col) => !col.hidden);

const normalizeApiBase = (raw) => {
  const fallback = "/api/v1";
  const value = (raw || fallback).toString().trim();
  if (!value) return fallback;
  const hasProtocol = /^https?:\/\//i.test(value);
  const prepared = hasProtocol || value.startsWith("/") ? value : `http://${value}`;
  const trimmed = prepared.replace(/\/+$/, "");
  try {
    // Validate; allow relative paths.
    const parsed = new URL(trimmed, window.location.origin);
    return parsed.pathname === trimmed ? trimmed : parsed.href.replace(/\/+$/, "");
  } catch {
    console.warn("Invalid VITE_API_BASE_URL, falling back to default /api/v1");
    return fallback;
  }
};

function App() {
  const apiBase = normalizeApiBase(import.meta.env.VITE_API_BASE_URL);
  const [revStatuses, setRevStatuses] = React.useState([]);
  const [revStatusBehaviors, setRevStatusBehaviors] = React.useState([]);
  const [revStatusError, setRevStatusError] = React.useState(null);
  const [revStatusLoading, setRevStatusLoading] = React.useState(true);
  const {
    project,
    setProject,
    projects,
    projectsError,
    filters,
    handleFilterChange,
    filteredDocuments,
    documentsError,
    documentsLoading,
    reloadDocuments,
  } = useFetchDocuments({ apiBase, visibleColumns });

  const renderCell = (doc, col) => {
    if (col.id === "rev_percent") {
      const raw =
        Number.isFinite(doc.percentage) && doc.percentage >= 0
          ? doc.percentage
          : Number.parseFloat(doc.rev_percent_display);
      const value = Number.isFinite(raw) ? Math.max(0, Math.min(100, raw)) : null;
      if (value === null) return doc.rev_percent_display || "—";
      return (
        <div className="progress" aria-label={`Revision percent ${value}%`}>
          <div className="progress__fill" style={{ width: `${value}%` }} />
          <div className="progress__label">{`${Math.round(value)}%`}</div>
        </div>
      );
    }
    return doc[col.key];
  };

  const buttonStyle = {
    background: "var(--color-accent)",
    color: "var(--color-accent-contrast)",
    border: "none",
    borderRadius: "4px",
    padding: "3px 6px",
    marginRight: "2px",
    fontSize: "12px",
    fontWeight: 500,
    cursor: "pointer",
    display: "inline-flex",
    alignItems: "center",
    height: "26px",
    boxShadow: "0 1px 2px rgba(0,0,0,0.08)",
    transition: "background 0.2s",
  };
  const disabledButtonStyle = {
    opacity: 0.5,
    cursor: "not-allowed",
    boxShadow: "none",
  };

  const iconStyle = {
    marginRight: "3px",
    fontSize: "12px",
  };

  const [infoRatio, setInfoRatio] = React.useState(0.35);
  const [detailRatio, setDetailRatio] = React.useState(0.25);
  const [columnWidths, setColumnWidths] = React.useState({});
  const [activeDetailTab, setActiveDetailTab] = React.useState("Details");
  const [infoActiveStep, setInfoActiveStep] = React.useState(null);
  const [infoActiveSubTab, setInfoActiveSubTab] = React.useState("Files with Comments");
  const [isDraggingUpload, setIsDraggingUpload] = React.useState(false);
  const [isDraggingBorder, setIsDraggingBorder] = React.useState(false);
  const [isDraggingRow, setIsDraggingRow] = React.useState(false);
  const [hideWindowsOnDrag, setHideWindowsOnDrag] = React.useState(false);
  const [uploadedFiles, setUploadedFiles] = React.useState({});
  const [expandedRevisions, setExpandedRevisions] = React.useState({});
  const [statusMenuOpen, setStatusMenuOpen] = React.useState({});
  const [isDetailPanelHidden, setIsDetailPanelHidden] = React.useState(false);
  const containerRef = React.useRef(null);
  const leftPanelRef = React.useRef(null);
  const hasInitializedFlowRef = React.useRef(false);
  const uploadInputRef = React.useRef(null);
  const [selectedDocId, setSelectedDocId] = React.useState(null);
  const [editRowId, setEditRowId] = React.useState(null);
  const [editValues, setEditValues] = React.useState({
    doc_name_unique: "",
    title: "",
    type_id: "",
    discipline_id: "",
    jobpack_id: "",
    area_id: "",
    unit_id: "",
  });
  const [isAdding, setIsAdding] = React.useState(false);
  const [newDocValues, setNewDocValues] = React.useState({
    doc_name_unique: "",
    title: "",
    discipline_id: "",
    type_id: "",
    jobpack_id: "",
    area_id: "",
    unit_id: "",
  });
  const [createStatus, setCreateStatus] = React.useState("idle");
  const [createError, setCreateError] = React.useState(null);
  const [saveError, setSaveError] = React.useState(null);
  const [saveStatus, setSaveStatus] = React.useState("idle");
  const [selectedFileId, setSelectedFileId] = React.useState(null);
  const [projectMenuOpen, setProjectMenuOpen] = React.useState(false);
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const [userMenuOpen, setUserMenuOpen] = React.useState(false);
  const [docTypes, setDocTypes] = React.useState([]);
  const [disciplines, setDisciplines] = React.useState([]);
  const [jobpacks, setJobpacks] = React.useState([]);
  const [areas, setAreas] = React.useState([]);
  const [units, setUnits] = React.useState([]);
  const [revisionOverviews, setRevisionOverviews] = React.useState([]);
  const [people, setPeople] = React.useState([]);

  const editingDoc = React.useMemo(
    () => filteredDocuments.find((doc) => (doc.doc_id || doc.doc_name || doc.id) === editRowId),
    [filteredDocuments, editRowId],
  );
  const selectedDoc = React.useMemo(
    () => filteredDocuments.find((doc) => (doc.doc_id || doc.doc_name || doc.id) === selectedDocId),
    [filteredDocuments, selectedDocId],
  );
  const isFlowEnabled = Boolean(project && selectedDoc);

  React.useEffect(() => {
    if (!isFlowEnabled) {
      setInfoActiveStep(null);
      setStatusMenuOpen({});
    }
  }, [isFlowEnabled]);

  const lookupOptionsByColumn = React.useMemo(
    () => ({
      doc_type: {
        field: "type_id",
        options:
          editValues.discipline_id && docTypes.length
            ? docTypes.filter(
                (item) => String(item.ref_discipline_id ?? "") === String(editValues.discipline_id),
              )
            : docTypes,
        getLabel: (item) =>
          `${item.doc_type_name || ""}${
            item.discipline_acronym ? ` (${item.discipline_acronym})` : ""
          }`,
        valueKey: "type_id",
        placeholder: "Select type...",
      },
      discipline: {
        field: "discipline_id",
        options: disciplines,
        getLabel: (item) =>
          `${item.discipline_name || ""}${
            item.discipline_acronym ? ` (${item.discipline_acronym})` : ""
          }`,
        valueKey: "discipline_id",
        placeholder: "Select discipline...",
      },
      jobpack: {
        field: "jobpack_id",
        options: jobpacks,
        getLabel: (item) => item.jobpack_name || "",
        valueKey: "jobpack_id",
        placeholder: "Select jobpack...",
      },
      area: {
        field: "area_id",
        options: areas,
        getLabel: (item) =>
          `${item.area_name || ""}${item.area_acronym ? ` (${item.area_acronym})` : ""}`,
        valueKey: "area_id",
        placeholder: "Select area...",
      },
      unit: {
        field: "unit_id",
        options: units,
        getLabel: (item) => item.unit_name || "",
        valueKey: "unit_id",
        placeholder: "Select unit...",
      },
    }),
    [areas, disciplines, docTypes, editValues.discipline_id, jobpacks, units],
  );

  const newDocTypeOptions = React.useMemo(() => {
    if (!newDocValues.discipline_id) return docTypes;
    return docTypes.filter(
      (item) => String(item.ref_discipline_id ?? "") === String(newDocValues.discipline_id),
    );
  }, [docTypes, newDocValues.discipline_id]);

  const handleDeleteDocument = React.useCallback(async () => {
    if (!selectedDoc) {
      setSaveStatus("error");
      setSaveError("Select a row to delete");
      return;
    }

    const docId = selectedDoc.doc_id ?? selectedDoc.id;
    if (!docId) {
      setSaveStatus("error");
      setSaveError("Unable to delete: missing document ID");
      return;
    }

    const docLabel =
      selectedDoc.doc_name_unique || selectedDoc.doc_name || selectedDoc.title || `#${docId}`;
    if (!window.confirm(`Delete document "${docLabel}"?`)) {
      return;
    }

    setSaveStatus("saving");
    setSaveError(null);
    try {
      const res = await fetch(`${apiBase}/documents/${docId}`, { method: "DELETE" });
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText || `Delete failed (${res.status})`);
      }
      await res.json();
      setSaveStatus("idle");
      setSelectedDocId(null);
      setEditRowId(null);
      reloadDocuments();
    } catch (err) {
      setSaveStatus("error");
      setSaveError(err.message || "Unknown error while deleting");
    }
  }, [apiBase, reloadDocuments, selectedDoc]);

  const ToolbarMenu = () => {
    const handleAddNew = () => {
      if (!project) return;
      const fallbackDisciplineId =
        selectedDoc?.discipline_id ?? disciplines[0]?.discipline_id ?? "";
      const fallbackTypeOptions = docTypes.filter(
        (item) => String(item.ref_discipline_id ?? "") === String(fallbackDisciplineId),
      );
      const fallbackTypeId =
        selectedDoc?.type_id ?? fallbackTypeOptions[0]?.type_id ?? docTypes[0]?.type_id ?? "";
      const fallbackDisciplineFromType =
        docTypes.find((item) => item.type_id === fallbackTypeId)?.ref_discipline_id ??
        fallbackDisciplineId;
      setCreateError(null);
      setCreateStatus("idle");
      setIsAdding(true);
      setNewDocValues({
        doc_name_unique: "",
        title: "",
        discipline_id: String(fallbackDisciplineFromType || ""),
        type_id: String(fallbackTypeId || ""),
        jobpack_id: String(selectedDoc?.jobpack_id ?? ""),
        area_id: String(selectedDoc?.area_id ?? areas[0]?.area_id ?? ""),
        unit_id: String(selectedDoc?.unit_id ?? units[0]?.unit_id ?? ""),
      });
    };
    const handleEdit = () => {
      if (!selectedDoc) {
        setSaveStatus("error");
        setSaveError("Select a row to edit");
        return;
      }
      startEdit(selectedDoc);
    };
    const handleDelete = () => handleDeleteDocument();
    const handleExport = () => {};
    const handleUndo = () => {};
    const handleRedo = () => {};
    const hasSelection = Boolean(selectedDoc);
    const hasProject = Boolean(project);

    if (editRowId || isAdding) {
      const isSaving = editRowId ? saveStatus === "saving" : createStatus === "saving";
      return (
        <div style={{ display: "flex", gap: "4px", alignItems: "center", padding: "0 6px" }}>
          <button
            style={isSaving ? { ...buttonStyle, ...disabledButtonStyle } : buttonStyle}
            title={editRowId ? "Save changes" : "Create document"}
            onClick={() => {
              if (editRowId) {
                applyEdit(editingDoc || selectedDoc);
              } else {
                createDocument();
              }
            }}
            disabled={isSaving}
          >
            <span style={iconStyle}>💾</span>
            {editRowId ? "Save" : "Create"}
          </button>
          <button
            style={{
              ...buttonStyle,
              background: "var(--color-border)",
              color: "var(--color-text)",
              ...(isSaving ? disabledButtonStyle : null),
            }}
            title="Cancel"
            onClick={() => {
              if (editRowId) {
                cancelEdit();
              } else {
                setIsAdding(false);
                setCreateError(null);
                setCreateStatus("idle");
              }
            }}
            disabled={isSaving}
          >
            <span style={iconStyle}>✕</span>
            Cancel
          </button>
        </div>
      );
    }

    return (
      <div style={{ display: "flex", gap: "4px", alignItems: "center", padding: "0 6px" }}>
        <button
          style={!hasProject ? { ...buttonStyle, ...disabledButtonStyle } : buttonStyle}
          title="Add new document"
          onClick={handleAddNew}
          disabled={!hasProject}
        >
          <span style={iconStyle}>+</span>
          Add new
        </button>
        <button
          style={!hasSelection ? { ...buttonStyle, ...disabledButtonStyle } : buttonStyle}
          title="Edit selected document"
          onClick={handleEdit}
          disabled={!hasSelection}
        >
          <span style={iconStyle}>✎</span>
          Edit
        </button>
        <button
          style={!hasSelection ? { ...buttonStyle, ...disabledButtonStyle } : buttonStyle}
          title="Delete selected document"
          onClick={handleDelete}
          disabled={!hasSelection}
        >
          <span style={iconStyle}>🗑</span>
          Delete
        </button>
        <button
          style={!hasSelection ? { ...buttonStyle, ...disabledButtonStyle } : buttonStyle}
          title="Export documents"
          onClick={handleExport}
          disabled={!hasSelection}
        >
          <span style={iconStyle}>⬇</span>
          Export to...
        </button>
        <button style={buttonStyle} title="Undo" onClick={handleUndo}>
          <span style={iconStyle}>↶</span>
        </button>
        <button style={buttonStyle} title="Redo" onClick={handleRedo}>
          <span style={iconStyle}>↷</span>
        </button>
      </div>
    );
  };

  const ProjectsPanel = () => {
    return (
      <div
        style={{
          background: "var(--color-success-soft)",
          border: "1px solid var(--color-success-border)",
          borderRadius: "8px",
          padding: "6px 10px",
          marginBottom: "2px",
          boxShadow: "0 2px 6px rgba(0,0,0,0.08)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px", position: "relative" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", position: "relative" }}>
            <button
              type="button"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              style={{
                fontSize: "18px",
                fontWeight: 700,
                lineHeight: "1",
                color: "var(--color-success-text)",
                background: "transparent",
                border: "none",
                cursor: "pointer",
                padding: "4px 8px",
                transition: "transform 0.3s ease",
                transform: sidebarOpen ? "rotate(90deg)" : "rotate(0deg)",
              }}
              title="Toggle menu"
              aria-label="Toggle menu"
            >
              ≣
            </button>

            {projectMenuOpen && (
              <div
                style={{
                  position: "absolute",
                  top: "100%",
                  left: "0",
                  background: "var(--color-surface)",
                  border: "1px solid var(--color-success-border-strong)",
                  borderRadius: "8px",
                  boxShadow: "0 4px 12px rgba(0,0,0,0.12)",
                  minWidth: "200px",
                  zIndex: 1000,
                  marginTop: "8px",
                  overflow: "hidden",
                  animation: "slideDown 0.2s ease",
                }}
              >
                <button
                  type="button"
                  onClick={() => {
                    setProjectMenuOpen(false);
                  }}
                  style={{
                    display: "block",
                    width: "100%",
                    padding: "10px 14px",
                    background: "transparent",
                    border: "none",
                    textAlign: "left",
                    cursor: "pointer",
                    fontSize: "13px",
                    color: "var(--color-text)",
                    transition: "background 0.2s",
                    borderBottom: "1px solid var(--color-border-soft)",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.background = "var(--color-surface-muted)")
                  }
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  + New Project
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setProjectMenuOpen(false);
                  }}
                  style={{
                    display: "block",
                    width: "100%",
                    padding: "10px 14px",
                    background: "transparent",
                    border: "none",
                    textAlign: "left",
                    cursor: "pointer",
                    fontSize: "13px",
                    color: "var(--color-text)",
                    transition: "background 0.2s",
                    borderBottom: "1px solid var(--color-border-soft)",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.background = "var(--color-surface-muted)")
                  }
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  ⚙ Manage Projects
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setProjectMenuOpen(false);
                  }}
                  style={{
                    display: "block",
                    width: "100%",
                    padding: "10px 14px",
                    background: "transparent",
                    border: "none",
                    textAlign: "left",
                    cursor: "pointer",
                    fontSize: "13px",
                    color: "var(--color-text)",
                    transition: "background 0.2s",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.background = "var(--color-surface-muted)")
                  }
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  ⬚ Settings
                </button>
              </div>
            )}

            <label
              htmlFor="project-select"
              style={{ fontSize: "12px", fontWeight: 600, color: "var(--color-success-text)" }}
            >
              Project:
            </label>
          </div>
          <select
            id="project-select"
            value={project}
            onChange={(e) => setProject(e.target.value)}
            aria-label="Select project"
            style={{
              border: "1px solid var(--color-success-border-strong)",
              borderRadius: "8px",
              padding: "7px 10px",
              fontSize: "13px",
              color: "var(--color-text)",
              background: "var(--color-surface)",
              minWidth: "220px",
              cursor: "pointer",
            }}
          >
            <option value="">Project number</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
          {projectsError ? (
            <span style={{ fontSize: "12px", color: "var(--color-danger)" }}>{projectsError}</span>
          ) : null}
          <div className="task-cabinet" style={{ marginLeft: "auto", padding: 0 }}>
            <div className="task-cabinet__label">Task cabinet:</div>
            {cabinetTabs.map((tab) => (
              <div key={tab.label} className="task-tab">
                <span style={{ color: "var(--color-success-text)", fontWeight: 600 }}>
                  {tab.label}
                </span>
                <span className="task-tab__badge" style={{ background: tab.tone }}>
                  {tab.count}
                </span>
              </div>
            ))}
          </div>

          {/* User Avatar */}
          <div
            style={{
              position: "relative",
              marginLeft: "12px",
              display: "flex",
              alignItems: "center",
              gap: "10px",
              cursor: "pointer",
            }}
          >
            <input
              type="file"
              id="avatar-upload"
              accept="image/*"
              style={{ display: "none" }}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  const reader = new FileReader();
                  reader.onload = (event) => {
                    const img = document.querySelector('[id="avatar-img"]');
                    if (img) {
                      img.src = event.target?.result;
                    }
                  };
                  reader.readAsDataURL(file);
                }
              }}
            />
            <button
              type="button"
              onClick={() => document.getElementById("avatar-upload").click()}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: "32px",
                height: "32px",
                borderRadius: "50%",
                background: "transparent",
                border: "2px solid var(--color-primary-soft)",
                cursor: "pointer",
                padding: "0",
                transition: "all 0.3s ease",
                overflow: "hidden",
                flexShrink: 0,
                boxShadow: "0 2px 6px rgba(0,0,0,0.08)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
                e.currentTarget.style.transform = "scale(1.08)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = "0 2px 6px rgba(0,0,0,0.08)";
                e.currentTarget.style.transform = "scale(1)";
              }}
              title="Change avatar"
              aria-label="Change avatar"
            >
              <img
                id="avatar-img"
                src="https://api.dicebear.com/7.x/avataaars/svg?seed=Konstantin"
                alt="User avatar"
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                  borderRadius: "50%",
                }}
              />
            </button>

            <button
              type="button"
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "1px",
                justifyContent: "center",
                cursor: "pointer",
                background: "none",
                border: "none",
                padding: 0,
                textAlign: "left",
              }}
              onClick={() => setUserMenuOpen(!userMenuOpen)}
            >
              <div
                style={{
                  fontSize: "11px",
                  fontWeight: 700,
                  color: "var(--color-text)",
                  lineHeight: "1.3",
                  letterSpacing: "-0.3px",
                }}
              >
                Konstantin Ni
              </div>
              <div
                style={{
                  fontSize: "10px",
                  color: "var(--color-text-muted)",
                  lineHeight: "1.2",
                  fontWeight: 500,
                }}
              >
                Designer
              </div>
            </button>

            {userMenuOpen && (
              <div
                style={{
                  position: "absolute",
                  top: "100%",
                  right: "0",
                  background: "var(--color-surface)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "8px",
                  boxShadow: "0 4px 12px rgba(0,0,0,0.12)",
                  minWidth: "200px",
                  zIndex: 1000,
                  marginTop: "8px",
                  overflow: "hidden",
                  animation: "slideDown 0.2s ease",
                }}
              >
                <div
                  style={{
                    padding: "12px 16px",
                    borderBottom: "1px solid var(--color-border-soft)",
                  }}
                >
                  <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--color-text)" }}>
                    John Doe
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>
                    john.doe@example.com
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => {
                    setUserMenuOpen(false);
                  }}
                  style={{
                    display: "block",
                    width: "100%",
                    padding: "10px 16px",
                    background: "transparent",
                    border: "none",
                    textAlign: "left",
                    cursor: "pointer",
                    fontSize: "13px",
                    color: "var(--color-text)",
                    transition: "background 0.2s",
                    borderBottom: "1px solid var(--color-border-soft)",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.background = "var(--color-surface-muted)")
                  }
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  👤 My Profile
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setUserMenuOpen(false);
                  }}
                  style={{
                    display: "block",
                    width: "100%",
                    padding: "10px 16px",
                    background: "transparent",
                    border: "none",
                    textAlign: "left",
                    cursor: "pointer",
                    fontSize: "13px",
                    color: "var(--color-text)",
                    transition: "background 0.2s",
                    borderBottom: "1px solid var(--color-border-soft)",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.background = "var(--color-surface-muted)")
                  }
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  ⚙ Settings
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setUserMenuOpen(false);
                  }}
                  style={{
                    display: "block",
                    width: "100%",
                    padding: "10px 16px",
                    background: "transparent",
                    border: "none",
                    textAlign: "left",
                    cursor: "pointer",
                    fontSize: "13px",
                    color: "var(--color-danger)",
                    transition: "background 0.2s",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.background = "var(--color-danger-soft)")
                  }
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  🚪 Logout
                </button>
              </div>
            )}
          </div>

          {/* FLOW Logo */}
          <div
            style={{
              marginLeft: "16px",
              paddingLeft: "12px",
              borderLeft: "1px solid var(--color-success-border-strong)",
              display: "flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            <span
              style={{
                fontSize: "14px",
                fontWeight: 800,
                color: "var(--color-success-text)",
                letterSpacing: "0.5px",
                textTransform: "uppercase",
              }}
            >
              FLOW
            </span>
          </div>
        </div>
      </div>
    );
  };

  const cabinetTabs = React.useMemo(
    () => [
      { label: "My tasks", count: 3, tone: "var(--color-focus)" },
      { label: "In review", count: 7, tone: "var(--color-warning)" },
      { label: "Completed", count: 12, tone: "var(--color-success)" },
    ],
    [],
  );

  const startColResize = React.useCallback(
    (event, columnKey) => {
      event.preventDefault();
      const th = event.currentTarget?.parentElement;
      const baseWidth = columnWidths[columnKey] ?? th?.getBoundingClientRect().width ?? 140;
      const startX = event.clientX;

      const handleMove = (moveEvent) => {
        const delta = moveEvent.clientX - startX;
        const nextWidth = Math.max(80, Math.round(baseWidth + delta));
        setColumnWidths((prev) => ({ ...prev, [columnKey]: nextWidth }));
      };

      const handleUp = () => {
        window.removeEventListener("mousemove", handleMove);
        window.removeEventListener("mouseup", handleUp);
      };

      window.addEventListener("mousemove", handleMove);
      window.addEventListener("mouseup", handleUp);
    },
    [columnWidths],
  );

  const startBorderResize = React.useCallback(
    (event) => {
      event.preventDefault();
      setIsDraggingBorder(true);
      setHideWindowsOnDrag(true);
      const container = containerRef.current;
      if (!container) return;

      const containerWidth = container.getBoundingClientRect().width;
      const startX = event.clientX;
      const startRatio = infoRatio;

      const handleMove = (moveEvent) => {
        const delta = startX - moveEvent.clientX;
        const deltaRatio = delta / containerWidth;
        const nextRatio = Math.max(0.15, Math.min(0.85, startRatio + deltaRatio));
        setInfoRatio(nextRatio);
      };

      const handleUp = () => {
        setIsDraggingBorder(false);
        setHideWindowsOnDrag(false);
        window.removeEventListener("mousemove", handleMove);
        window.removeEventListener("mouseup", handleUp);
      };

      window.addEventListener("mousemove", handleMove);
      window.addEventListener("mouseup", handleUp);
    },
    [infoRatio],
  );

  const startRowResize = React.useCallback(
    (event) => {
      event.preventDefault();
      setIsDraggingRow(true);
      const container = leftPanelRef.current;
      if (!container) return;

      const containerHeight = container.getBoundingClientRect().height;
      const startY = event.clientY;
      const startRatio = detailRatio;

      const handleMove = (moveEvent) => {
        const delta = startY - moveEvent.clientY;
        const deltaRatio = delta / containerHeight;
        const nextRatio = Math.max(0.2, Math.min(0.8, startRatio + deltaRatio));
        setDetailRatio(nextRatio);
      };

      const handleUp = () => {
        setIsDraggingRow(false);
        window.removeEventListener("mousemove", handleMove);
        window.removeEventListener("mouseup", handleUp);
      };

      window.addEventListener("mousemove", handleMove);
      window.addEventListener("mouseup", handleUp);
    },
    [detailRatio],
  );

  const startEdit = React.useCallback((doc) => {
    if (!doc) return;
    const rowId = doc.doc_id || doc.doc_name || doc.doc_name_unique || doc.id;
    setSelectedDocId(rowId);
    setEditRowId(rowId);
    setSaveError(null);
    setSaveStatus("idle");
    setEditValues({
      doc_name_unique: doc.doc_name || doc.doc_name_unique || "",
      title: doc.title || "",
      type_id: doc.type_id ?? doc.doc_type_id ?? "",
      discipline_id: doc.discipline_id ?? "",
      jobpack_id: doc.jobpack_id ?? "",
      area_id: doc.area_id ?? "",
      unit_id: doc.unit_id ?? "",
    });
  }, []);

  const cancelEdit = React.useCallback(() => {
    setEditRowId(null);
    setSaveError(null);
    setSaveStatus("idle");
  }, []);

  const applyEdit = React.useCallback(
    async (doc) => {
      if (!doc) return;

      // Build minimal payload - only include fields that are actually being changed
      const docId = Number(doc.doc_id || doc.id);
      if (!docId) {
        setSaveStatus("error");
        setSaveError("Missing document ID");
        return;
      }
      const payload = {};

      // Add edited fields only if they have actual content
      const docName = String(editValues.doc_name_unique || "").trim();
      const docTitle = String(editValues.title || "").trim();
      const toLookupId = (value) => {
        const parsed = Number(value);
        return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
      };

      if (docName) {
        payload.doc_name_unique = docName;
      }
      if (docTitle) {
        payload.title = docTitle;
      }
      const typeId = toLookupId(editValues.type_id);
      const jobpackId = toLookupId(editValues.jobpack_id);
      const areaId = toLookupId(editValues.area_id);
      const unitId = toLookupId(editValues.unit_id);
      if (typeId) payload.type_id = typeId;
      if (jobpackId) payload.jobpack_id = jobpackId;
      if (areaId) payload.area_id = areaId;
      if (unitId) payload.unit_id = unitId;

      if (!Object.keys(payload).length) {
        setSaveStatus("error");
        setSaveError("No changes to save");
        return;
      }

      setSaveStatus("saving");
      setSaveError(null);

      try {
        const res = await fetch(`${apiBase}/documents/${docId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          const errorText = await res.text();
          console.error("API Error Response:", errorText);
          throw new Error(errorText || `Update failed (${res.status})`);
        }

        setSaveStatus("saved");
        setEditRowId(null);
        reloadDocuments();
      } catch (err) {
        console.error("Save error:", err);
        setSaveStatus("error");
        setSaveError(err.message || "Unknown error while saving");
      }
    },
    [apiBase, editValues, reloadDocuments],
  );

  const createDocument = React.useCallback(async () => {
    if (!project) return;

    const trimmedName = String(newDocValues.doc_name_unique || "").trim();
    const trimmedTitle = String(newDocValues.title || "").trim();
    const missing = [];
    if (!trimmedName) missing.push("Document name");
    if (!trimmedTitle) missing.push("Title");
    if (!newDocValues.type_id) missing.push("Type");
    if (!newDocValues.area_id) missing.push("Area");
    if (!newDocValues.unit_id) missing.push("Unit");
    if (!revisionOverviews.length) missing.push("Revision code");
    if (!people.length) {
      missing.push("Revision author");
      missing.push("Revision originator");
      missing.push("Revision modifier");
    }
    if (missing.length) {
      setCreateStatus("error");
      setCreateError(`Missing required fields: ${missing.join(", ")}`);
      return;
    }

    const toLookupId = (value) => {
      const parsed = Number(value);
      return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
    };
    const toDateTime = (dateValue) => `${dateValue}T00:00:00Z`;
    const today = new Date();
    const startDate = today.toISOString().slice(0, 10);
    const finishDate = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000)
      .toISOString()
      .slice(0, 10);
    const revCodeId = toLookupId(revisionOverviews[0]?.rev_code_id);
    const personId = toLookupId(people[0]?.person_id);

    const payload = {
      doc_name_unique: trimmedName,
      title: trimmedTitle,
      project_id: Number(project),
      type_id: toLookupId(newDocValues.type_id),
      area_id: toLookupId(newDocValues.area_id),
      unit_id: toLookupId(newDocValues.unit_id),
      rev_code_id: revCodeId,
      rev_author_id: personId,
      rev_originator_id: personId,
      rev_modifier_id: personId,
      transmital_current_revision: "TR-001",
      planned_start_date: toDateTime(startDate),
      planned_finish_date: toDateTime(finishDate),
    };
    const jobpackId = toLookupId(newDocValues.jobpack_id);
    if (jobpackId) payload.jobpack_id = jobpackId;

    setCreateStatus("saving");
    setCreateError(null);

    try {
      const res = await fetch(`${apiBase}/documents`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText || `Create failed (${res.status})`);
      }
      const created = await res.json();
      setCreateStatus("saved");
      setIsAdding(false);
      setSelectedDocId(created?.doc_id ?? null);
      reloadDocuments();
    } catch (err) {
      setCreateStatus("error");
      setCreateError(err.message || "Unknown error while creating document");
    }
  }, [apiBase, newDocValues, people, project, reloadDocuments, revisionOverviews]);

  const handleUploadFiles = React.useCallback(
    async (files, statusKey) => {
      const list = Array.from(files || []);
      if (!list.length || !statusKey || !selectedDocId || !selectedDoc) return;

      // Get the revision ID from the selected document
      const revisionId = selectedDoc.rev_current_id;
      if (!revisionId) {
        alert("No current revision found. Please create a revision first.");
        return;
      }

      // Get the document number from the selected document
      const documentNumber = selectedDoc.doc_name_unique || selectedDoc.title || "";

      // Upload each file to the API
      for (const file of list) {
        try {
          const formData = new FormData();
          formData.append("rev_id", revisionId);
          formData.append("file", file);

          const response = await fetch(`${apiBase}/files/`, {
            method: "POST",
            body: formData,
          });

          if (!response.ok) {
            const errorText = await response.text();
            console.error(`Upload failed for ${file.name}:`, errorText);
            alert(`Failed to upload ${file.name}: ${errorText || response.statusText}`);
            continue;
          }

          const fileData = await response.json();

          // Store the file object with document number and API response
          setUploadedFiles((prev) => {
            const currentFiles = prev[selectedDocId]?.[statusKey] || [];
            const fileObject = normalizeFile(fileData, {
              documentNumber,
              uploadedAt: new Date().toISOString(),
            });
            const localFileObject = normalizeFile(file, {
              documentNumber,
              uploadedAt: new Date().toISOString(),
            });
            const nextFiles = currentFiles.filter((existing) => {
              if (!existing) return false;
              const existingId = existing.fileId ?? existing.id ?? null;
              const incomingId = localFileObject.fileId ?? localFileObject.id ?? null;
              if (incomingId && existingId) {
                return existingId !== incomingId;
              }
              const existingName = existing.name ?? existing.filename ?? "";
              const existingDocNumber = existing.documentNumber ?? "";
              return !(
                existingName &&
                existingName === localFileObject.name &&
                existingDocNumber === (localFileObject.documentNumber ?? "")
              );
            });
            return {
              ...prev,
              [selectedDocId]: {
                ...(prev[selectedDocId] || {}),
                [statusKey]: [...nextFiles, fileObject],
              },
            };
          });
        } catch (err) {
          console.error(`Error uploading ${file.name}:`, err);
          alert(`Error uploading ${file.name}: ${err.message}`);
        }
      }

      // Auto-expand the revision tree
      setExpandedRevisions((prev) => ({
        ...prev,
        [statusKey]: { ...prev[statusKey], isOpen: true },
      }));
    },
    [selectedDocId, selectedDoc, apiBase],
  );

  const handleUploadDrop = React.useCallback(
    (e, statusKey) => {
      e.preventDefault();
      setIsDraggingUpload(false);
      handleUploadFiles(e.dataTransfer?.files, statusKey);
    },
    [handleUploadFiles],
  );

  const handleUploadSelect = React.useCallback(
    (e, statusKey) => {
      handleUploadFiles(e.target.files, statusKey);
      e.target.value = "";
    },
    [handleUploadFiles],
  );

  const buildUploadDragProps = React.useCallback(
    (statusKey) => ({
      onDragOver: (e) => {
        e.preventDefault();
        setIsDraggingUpload(true);
      },
      onDragLeave: () => setIsDraggingUpload(false),
      onDrop: (e) => handleUploadDrop(e, statusKey),
    }),
    [handleUploadDrop],
  );

  // Handle file selection (single click)
  const getFileId = React.useCallback(
    (file) => (typeof file === "object" ? (file.fileId ?? file.id ?? null) : null),
    [],
  );

  const handleSelectFile = React.useCallback((file) => {
    // Set the selected file ID for visual indication
    setSelectedFileId(getFileKey(file));
  }, []);

  // Handle file download (double click)
  const handleDownloadFile = React.useCallback(
    async (file) => {
      // Handle both string and object file formats
      const fileName = typeof file === "string" ? file : file.name;
      const fileId = getFileId(file);
      const documentNumber = typeof file === "object" ? file.documentNumber : null;
      const displayName = documentNumber ? `${documentNumber} - ${fileName}` : fileName;

      if (!fileId) {
        alert(`File not uploaded yet: ${displayName}\n\nPlease wait for the upload to complete.`);
        return;
      }

      try {
        // Download file from API
        const downloadUrl = `${apiBase}/files/${fileId}/download`;
        const response = await fetch(downloadUrl);

        if (!response.ok) {
          throw new Error(`Download failed: ${response.statusText}`);
        }

        // Get the blob and create a download link
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } catch (err) {
        console.error(`Error downloading file ${displayName}:`, err);
        alert(`Failed to download ${displayName}: ${err.message}`);
      }
    },
    [apiBase, getFileId],
  );

  const handleDeleteFile = React.useCallback(
    async (file) => {
      // Handle both string and object file formats
      const fileName = typeof file === "string" ? file : file.name;
      const fileId = getFileId(file);
      const documentNumber = typeof file === "object" ? file.documentNumber : null;
      const displayName = documentNumber ? `${documentNumber} - ${fileName}` : fileName;

      if (!fileId) {
        alert(`File not uploaded yet: ${displayName}\n\nCannot delete local files.`);
        return;
      }

      if (!window.confirm(`Are you sure you want to delete "${displayName}"?`)) {
        return;
      }

      try {
        const response = await fetch(`${apiBase}/files/${fileId}`, {
          method: "DELETE",
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(errorText || `Delete failed: ${response.statusText}`);
        }

        // Remove from state
        setUploadedFiles((prev) => {
          const updated = { ...prev };
          if (updated[selectedDocId]) {
            // Remove from API files
            if (updated[selectedDocId]["$api"]) {
              updated[selectedDocId]["$api"] = updated[selectedDocId]["$api"].filter(
                (f) => f.fileId !== fileId,
              );
            }
            // Remove from status-specific files
            Object.keys(updated[selectedDocId]).forEach((statusKey) => {
              if (statusKey !== "$api" && Array.isArray(updated[selectedDocId][statusKey])) {
                updated[selectedDocId][statusKey] = updated[selectedDocId][statusKey].filter(
                  (f) => {
                    const fId = typeof f === "object" ? f.fileId : null;
                    return fId !== fileId;
                  },
                );
              }
            });
          }
          return updated;
        });
      } catch (err) {
        console.error(`Error deleting file ${displayName}:`, err);
        alert(`Failed to delete ${displayName}: ${err.message}`);
      }
    },
    [apiBase, getFileId, selectedDocId],
  );

  const handleRevisionToggle = React.useCallback((revKey) => {
    setExpandedRevisions((prev) => ({
      ...prev,
      [revKey]: { ...prev[revKey], isOpen: !prev[revKey]?.isOpen },
    }));
  }, []);

  // Sync document selection with uploaded files and revisions
  React.useEffect(() => {
    if (!selectedDocId || !selectedDoc) {
      setInfoActiveStep(null);
      return;
    }

    // Fetch files from API for the selected document's current revision
    const fetchFilesForRevision = async () => {
      const revisionId = selectedDoc.rev_current_id;
      if (!revisionId) return;

      try {
        const response = await fetch(`${apiBase}/files/list?rev_id=${revisionId}`);
        if (!response.ok) {
          if (response.status === 404) {
            // No files for this revision yet - keep existing local files
            return;
          }
          throw new Error(`Failed to load files (${response.status})`);
        }

        const files = await response.json();

        // Convert API files to our file object format
        // Store all API files in a special "$api" key to keep them persistent across all statuses
        const apiFiles = [];
        if (Array.isArray(files) && files.length > 0) {
          files.forEach((apiFile) => {
            apiFiles.push(
              normalizeFile(apiFile, {
                documentNumber: selectedDoc.doc_name_unique || selectedDoc.title,
                uploadedAt: new Date().toISOString(),
                isFromApi: true,
              }),
            );
          });

          // Update uploadedFiles with fetched files in a persistent location
          setUploadedFiles((prev) => {
            const existingFiles = prev[selectedDocId] || {};
            return {
              ...prev,
              [selectedDocId]: {
                ...existingFiles,
                $api: apiFiles, // Store API files in special $api key
              },
            };
          });
        }
      } catch (err) {
        console.error("Failed to fetch files for revision:", err);
      }
    };

    fetchFilesForRevision();
    // When a document is selected, automatically show the current flow step
  }, [selectedDocId, selectedDoc, apiBase]);

  React.useEffect(() => {
    let isActive = true;
    const fetchLookups = async () => {
      setRevStatusLoading(true);
      setRevStatusError(null);
      try {
        const [statusRes, behaviorRes] = await Promise.all([
          fetch(`${apiBase}/lookups/doc_rev_statuses`),
          fetch(`${apiBase}/lookups/doc_rev_status_ui_behaviors`),
        ]);
        if (!statusRes.ok && statusRes.status !== 404) {
          throw new Error(`Failed to load statuses (${statusRes.status})`);
        }
        if (!behaviorRes.ok && behaviorRes.status !== 404) {
          throw new Error(`Failed to load status behaviors (${behaviorRes.status})`);
        }
        const statuses = statusRes.status === 404 ? [] : await statusRes.json();
        const behaviors = behaviorRes.status === 404 ? [] : await behaviorRes.json();
        if (isActive) {
          setRevStatuses(Array.isArray(statuses) ? statuses : []);
          setRevStatusBehaviors(Array.isArray(behaviors) ? behaviors : []);
        }
      } catch (err) {
        if (isActive) {
          setRevStatusError(err instanceof Error ? err.message : "Failed to load statuses");
        }
      } finally {
        if (isActive) {
          setRevStatusLoading(false);
        }
      }
    };

    fetchLookups();
    return () => {
      isActive = false;
    };
  }, [apiBase]);

  React.useEffect(() => {
    let isActive = true;
    const loadLookups = async () => {
      try {
        const [
          docTypesRes,
          disciplinesRes,
          jobpacksRes,
          areasRes,
          unitsRes,
          revisionOverviewsRes,
          peopleRes,
        ] = await Promise.all([
          fetch(`${apiBase}/documents/doc_types`),
          fetch(`${apiBase}/lookups/disciplines`),
          fetch(`${apiBase}/lookups/jobpacks`),
          fetch(`${apiBase}/lookups/areas`),
          fetch(`${apiBase}/lookups/units`),
          fetch(`${apiBase}/documents/revision_overview`),
          fetch(`${apiBase}/people/persons`),
        ]);

        const readJson = async (res) => (res.status === 404 ? [] : await res.json());
        if (!isActive) return;
        setDocTypes((await readJson(docTypesRes)) || []);
        setDisciplines((await readJson(disciplinesRes)) || []);
        setJobpacks((await readJson(jobpacksRes)) || []);
        setAreas((await readJson(areasRes)) || []);
        setUnits((await readJson(unitsRes)) || []);
        setRevisionOverviews((await readJson(revisionOverviewsRes)) || []);
        setPeople((await readJson(peopleRes)) || []);
      } catch (err) {
        if (!isActive) return;
        console.error("Failed to load lookup data:", err);
        setDocTypes([]);
        setDisciplines([]);
        setJobpacks([]);
        setAreas([]);
        setUnits([]);
        setRevisionOverviews([]);
        setPeople([]);
      }
    };

    loadLookups();
    return () => {
      isActive = false;
    };
  }, [apiBase]);

  const behaviorNameById = React.useMemo(() => {
    return Object.fromEntries(
      (revStatusBehaviors || []).map((behavior) => [
        behavior.ui_behavior_id,
        behavior.ui_behavior_name,
      ]),
    );
  }, [revStatusBehaviors]);
  const behaviorFileById = React.useMemo(() => {
    return Object.fromEntries(
      (revStatusBehaviors || []).map((behavior) => [
        behavior.ui_behavior_id,
        behavior.ui_behavior_file,
      ]),
    );
  }, [revStatusBehaviors]);

  const orderedStatuses = React.useMemo(() => {
    // Always use global revisions for the flow - each document follows the same workflow
    if (!Array.isArray(revStatuses) || revStatuses.length === 0) return [];

    const byId = new Map();
    const referenced = new Set();
    revStatuses.forEach((status) => {
      byId.set(status.rev_status_id, status);
      if (status.next_rev_status_id) {
        referenced.add(status.next_rev_status_id);
      }
    });

    // Prefer explicit start flag if available, fall back to inferred start.
    let start = revStatuses.find((status) => status.start);
    if (!start) {
      start = revStatuses.find((status) => !referenced.has(status.rev_status_id));
    }
    if (!start) {
      return [...revStatuses].sort((a, b) => a.rev_status_name.localeCompare(b.rev_status_name));
    }

    const ordered = [];
    const visited = new Set();
    let current = start;
    while (current && !visited.has(current.rev_status_id)) {
      ordered.push(current);
      visited.add(current.rev_status_id);
      current = current.next_rev_status_id ? byId.get(current.next_rev_status_id) : null;
    }

    if (ordered.length !== revStatuses.length) {
      revStatuses.forEach((status) => {
        if (!visited.has(status.rev_status_id)) {
          ordered.push(status);
        }
      });
    }
    return ordered;
  }, [revStatuses]);

  React.useEffect(() => {
    if (orderedStatuses.length === 0) return;

    // Auto-select first status when document is selected and no step is active
    if (
      selectedDoc &&
      selectedDoc.rev_current_id &&
      infoActiveStep === null &&
      !hasInitializedFlowRef.current
    ) {
      const firstStatus = orderedStatuses[0];
      if (firstStatus) {
        setInfoActiveStep(String(firstStatus.rev_status_id));
        hasInitializedFlowRef.current = true;
        return;
      }
    }

    if (infoActiveStep === null) {
      hasInitializedFlowRef.current = true;
      return;
    }
    const exists =
      orderedStatuses.some((s) => String(s.rev_status_id) === infoActiveStep) ||
      infoActiveStep === "history";
    if (exists) return;
    setInfoActiveStep(null);
    hasInitializedFlowRef.current = true;
  }, [orderedStatuses, infoActiveStep, selectedDoc]);

  return (
    <main
      className="page"
      style={{ height: "100vh", display: "flex", flexDirection: "column", overflow: "hidden" }}
    >
      <style>
        {`
        :root {
          --color-bg: #f0f2f5;
          --color-surface: #ffffff;
          --color-surface-alt: #fafbfc;
          --color-surface-muted: #f5f6f8;
          --color-surface-muted-strong: #e8eaed;
          --color-surface-subtle: #f9fafb;
          --color-border: #d5d9de;
          --color-border-soft: #dadde0;
          --color-border-strong: #cdd0d5;
          --color-text: #0a0e27;
          --color-text-muted: #65676b;
          --color-text-subtle: #8a8d91;
          --color-text-strong: #1d1f26;
          --color-text-secondary: #484a4f;
          --color-primary: #1a5f7a;
          --color-primary-contrast: #ffffff;
          --color-primary-soft: #e7f3f7;
          --color-primary-outline: rgba(26, 95, 122, 0.15);
          --color-accent: #3d5a80;
          --color-accent-contrast: #ffffff;
          --color-info: #2563eb;
          --color-info-dark: #1d4ed8;
          --color-info-strong: #1e40af;
          --color-info-soft: #eff6ff;
          --color-warning: #d97706;
          --color-danger: #dc2626;
          --color-danger-soft: #fef2f2;
          --color-success: #059669;
          --color-success-dark: #047857;
          --color-success-soft: #ecfdf5;
          --color-success-border: #a7f3d0;
          --color-success-border-strong: #6ee7b7;
          --color-success-text: #065f46;
          --color-row-selected: #f0f4ff;
          --color-focus: #1d4ed8;
          --color-error: #dc2626;
          --color-error-dark: #b91c1c;
          --color-spinner-start: #2563eb;
          --color-spinner-end: #3b82f6;
          color: var(--color-text);
          background: var(--color-bg);
          font-family: "Inter", "SF Pro Display", system-ui, -apple-system, sans-serif;
        }
        * { box-sizing: border-box; }
        body {
          margin: 0;
          background: var(--color-bg);
        }
        .page {
          padding: 8px;
        }
        .toolbar {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 12px;
          color: var(--color-text-muted);
          font-size: 14px;
        }
        .toolbar select {
          border: 1px solid var(--color-border-soft);
          border-radius: 8px;
          padding: 6px 8px;
          font-size: 13px;
          color: var(--color-text-muted);
          background: var(--color-surface);
        }
        .toolbar button {
          display: inline-flex;
          align-items: center;
          gap: 6px;
        }
        .toolbar .status {
          font-size: 12px;
          color: var(--color-danger);
        }
        .status-row {
          text-align: left;
          padding: 6px;
          color: var(--color-text-muted);
          font-size: 14px;
          background: var(--color-surface-alt);
        }
        .status-row.error {
          color: var(--color-danger);
          background: var(--color-surface)5f5;
        }
        .progress {
          width: 120px;
          background: var(--color-surface-muted-strong);
          border-radius: 999px;
          height: 20px;
          position: relative;
          overflow: hidden;
          border: 1px solid var(--color-border);
        }
        .progress__fill {
          position: absolute;
          top: 0;
          left: 0;
          height: 100%;
          background: linear-gradient(90deg, var(--color-spinner-start), var(--color-spinner-end));
          border-radius: 999px;
          transition: width 180ms ease;
        }
        .progress__label {
          position: absolute;
          inset: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 12px;
          font-weight: 600;
          color: var(--color-surface);
          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.25);
        }
        .spinner {
          width: 22px;
          height: 22px;
          border: 3px solid var(--color-border);
          border-top-color: var(--color-spinner-start);
          border-radius: 50%;
          display: inline-block;
          animation: spin 0.8s linear infinite;
        }
        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }
        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }
        .card {
          background: var(--color-surface);
          border: 1px solid var(--color-border);
          border-radius: 12px;
          box-shadow:
            0 10px 30px rgba(15, 23, 42, 0.05),
            0 1px 3px rgba(15, 23, 42, 0.08);
          overflow: hidden;
        }
        .table {
          width: 100%;
          border-collapse: collapse;
          white-space: nowrap;
        }
        .table thead th {
          background: var(--color-surface-alt);
          font-weight: 700;
          text-align: left;
          font-size: 14px;
          color: var(--color-text);
          padding: 6px 8px 2px;
          border-bottom: 1px solid var(--color-border);
          white-space: nowrap;
          border-right: 1px solid var(--color-border);
        }
        .table thead th:not(:first-child) {
          border-left: 1px solid var(--color-border);
        }
        .table thead input {
          width: 100%;
          margin-top: 2px;
          padding: 4px 8px;
          border: 1px solid var(--color-border-soft);
          border-radius: 8px;
          font-size: 13px;
          color: var(--color-text-muted);
          background: var(--color-surface);
          caret-color: transparent; /* Hide blinking text cursor in header filters */
          line-height: 1.4;
        }
        .table td {
          padding: 4px 8px;
          border-bottom: 1px solid var(--color-border);
          position: relative;
          font-size: 13px;
          color: var(--color-text);
          line-height: 1.4;
        }
        .table td:not(:first-child) {
          border-left: 1px solid var(--color-border);
        }
        .table tbody tr {
          border-bottom: 1px solid var(--color-border);
        }
        .table tbody tr:hover td {
          background: var(--color-surface-subtle);
        }
        .meta {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 14px 16px;
          border-bottom: 1px solid var(--color-border);
        }
        .meta h1 {
          margin: 0;
          font-size: 20px;
          font-weight: 700;
          color: var(--color-text);
        }
        .meta .count {
          font-size: 14px;
          color: var(--color-text-muted);
        }
        .table-wrapper {
          width: 100%;
          height: 100%;
          overflow: auto;
        }
        .task-cabinet {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 8px 10px;
        }
        .task-cabinet__label {
          font-size: 14px;
          font-weight: 600;
          color: var(--color-success-text);
          min-width: 92px;
        }
        .task-tab {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          background: var(--color-surface);
          border: 1px solid var(--color-success-border-strong);
          border-radius: 6px;
          padding: 4px 8px;
          font-size: 12px;
          font-weight: 600;
          color: var(--color-text);
          box-shadow: none;
          cursor: default;
        }
        .task-tab__badge {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 16px;
          height: 16px;
          padding: 0 4px;
          border-radius: 4px;
          font-weight: 700;
          font-size: 10px;
          color: var(--color-surface);
        }
        .detail-tabs {
          display: flex;
          gap: 2px;
          border-bottom: 1px solid var(--color-border);
          background: transparent;
          padding: 0;
        }
        .detail-tab {
          padding: 6px 12px;
          border: 1px solid var(--color-border);
          border-bottom: none;
          border-radius: 6px 6px 0 0;
          background: var(--color-border);
          font-size: 12px;
          font-weight: 500;
          cursor: pointer;
          color: var(--color-text);
          transition: all 0.2s ease;
          line-height: 1.4;
          height: 28px;
          display: flex;
          align-items: center;
        }
        .detail-tab:hover {
          background: var(--color-border-strong);
        }
        .detail-tab.active {
          background: var(--color-accent);
          color: var(--color-accent-contrast);
          border-color: var(--color-accent);
        }
        .detail-tab-panel {
          border: 1px solid var(--color-border);
          border-top: none;
          border-radius: 0;
          padding: 16px;
          background: var(--color-surface);
          display: flex;
          flex-direction: column;
          flex: 1;
        }
        .flow-card {
          background: var(--color-surface-alt);
          border: 1px solid var(--color-border);
          border-radius: 12px;
          box-shadow: 0 1px 2px rgba(0,0,0,0.04);
          display: flex;
          flex-direction: column;
          height: 100%;
          overflow: hidden;
        }
        .flow-header {
          padding: 12px 14px;
          font-size: 16px;
          font-weight: 700;
          color: var(--color-text-strong);
          border-bottom: 1px solid var(--color-border);
        }
        .flow-body {
          display: flex;
          flex-direction: column;
          flex: 1;
          min-height: 0;
        }
        .flow-empty {
          padding: 12px 14px;
          font-size: 14px;
          color: var(--color-text-muted);
        }
        .flow-step {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 12px 14px 12px 30px;
          cursor: pointer;
          color: var(--color-text);
          font-size: 13px;
          position: relative;
          background: var(--color-surface);
          border: none;
          border-bottom: 1px solid var(--color-border);
          width: 100%;
          text-align: left;
          font: inherit;
        }
        .flow-step:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .flow-step__label {
          font-weight: 600;
          text-transform: uppercase;
          font-size: 13px;
        }
        .flow-step__behavior {
          margin-left: auto;
          font-size: 11px;
          color: var(--color-text-subtle);
          background: var(--color-surface-muted);
          border: 1px solid var(--color-border);
          border-radius: 999px;
          padding: 2px 8px;
        }
        .flow-step[data-final="true"] {
          background: #ecfdf3;
        }
        .flow-step[data-final="true"] .dot {
          border-color: #16a34a;
          color: #16a34a;
        }
        .flow-step[data-final="true"].active .dot {
          background: #16a34a;
          box-shadow: 0 0 0 3px rgba(22,163,74,0.2);
        }
        .flow-step[data-ui-behavior="HistoryBehavior.jsx"] {
          background: #fef9c3;
        }
        .flow-step[data-ui-behavior="HistoryBehavior.jsx"] .dot {
          border-color: #d97706;
          color: #d97706;
          background: #fff7d6;
        }
        .flow-step[data-ui-behavior="HistoryBehavior.jsx"].active .dot {
          box-shadow: 0 0 0 3px rgba(217,119,6,0.2);
        }
        .flow-step[data-ui-behavior="HistoryBehavior.jsx"] .dot__icon {
          stroke-linecap: square;
          stroke-linejoin: miter;
        }
        .flow-step::before {
          content: none;
        }
        .flow-step .dot {
          width: 16px;
          height: 16px;
          border-radius: 50%;
          border: 2px solid var(--color-primary);
          background: var(--color-surface);
          display: inline-flex;
          align-items: center;
          justify-content: center;
          font-size: 10px;
          color: var(--color-primary);
          z-index: 1;
          position: relative;
        }
        .flow-step .dot__icon {
          width: 12px;
          height: 12px;
          stroke: currentColor;
          stroke-width: 2;
          fill: none;
          stroke-linecap: round;
          stroke-linejoin: round;
        }
        .flow-step .dot__inner {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: currentColor;
          display: inline-block;
        }
        .flow-step.active .dot {
          background: var(--color-primary);
          color: var(--color-surface);
          box-shadow: 0 0 0 3px rgba(15,118,110,0.15);
        }
        .flow-step[data-final="true"] .dot {
          width: 22px;
          height: 22px;
          border-width: 3px;
        }
        .flow-inline-content {
          border-left: 4px solid var(--color-primary);
          background: var(--color-surface-alt);
          border: 1px solid var(--color-border);
          border-radius: 10px;
          margin: 4px 8px 10px 8px;
          padding: 0;
          display: flex;
          flex-direction: column;
          flex: 1;
          min-height: 0;
          max-height: 100%;
          overflow: hidden;
        }
        .flow-subtabs {
          display: flex;
          gap: 2px;
          border-bottom: 1px solid var(--color-border);
          background: transparent;
          padding: 8px 12px 0;
        }
        .flow-subtab {
          padding: 6px 12px;
          border: 1px solid var(--color-border);
          border-bottom: none;
          border-radius: 6px 6px 0 0;
          background: var(--color-border);
          font-size: 12px;
          font-weight: 500;
          cursor: pointer;
          color: var(--color-text);
          transition: all 0.2s ease;
          line-height: 1.4;
          height: 28px;
          display: flex;
          align-items: center;
        }
        .flow-subtab:hover {
          background: var(--color-border-strong);
        }
        .flow-subtab.active {
          background: var(--color-accent);
          color: var(--color-accent-contrast);
          border-color: var(--color-accent);
        }
        .flow-subtab:last-child { border-right: none; }
        .flow-mini-tabs {
          display: flex;
          gap: 2px;
          border-bottom: 1px solid var(--color-border);
          background: transparent;
          padding: 0 12px 0;
          margin-bottom: 8px;
          margin-left: -12px;
          margin-right: -12px;
        }
        .flow-mini-tab {
          padding: 6px 12px;
          border: 1px solid var(--color-border);
          border-bottom: none;
          border-radius: 6px 6px 0 0;
          background: var(--color-border);
          font-size: 12px;
          font-weight: 500;
          cursor: pointer;
          color: var(--color-text);
          flex: 1;
          text-align: center;
          transition: all 0.2s ease;
          line-height: 1.4;
          height: 28px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .flow-mini-tab:hover {
          background: var(--color-border-strong);
        }
        .flow-mini-tab.active {
          background: var(--color-accent);
          color: var(--color-accent-contrast);
          border-color: var(--color-accent);
        }
        .flow-section {
          padding: 6px 0 0 0;
          background: transparent;
          border: none;
          gap: 8px;
          display: flex;
          flex-direction: column;
          flex: 1;
        }
        .flow-box {
          border: 1px solid var(--color-border-soft);
          border-radius: 10px;
          background: var(--color-surface);
          padding: 12px;
          margin: 0 12px;
        }
        .flow-upload {
          border: 2px dashed var(--color-border-strong);
          border-radius: 12px;
          padding: 60px 40px;
          text-align: center;
          color: var(--color-accent);
          font-size: 18px;
          line-height: 1.8;
          background: var(--color-surface);
          transition: background 0.15s, border-color 0.15s, color 0.15s;
          font: inherit;
          min-height: 180px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
        }
        .flow-upload:focus,
        .flow-upload:focus-visible {
          background: var(--color-info-soft);
          border-color: var(--color-info);
          color: var(--color-info-strong);
          outline: 2px solid var(--color-focus);
          outline-offset: 2px;
        }
        .flow-upload:hover {
          background: var(--color-info-soft);
          border-color: var(--color-info);
          color: var(--color-info-strong);
        }
        .flow-step:focus-visible,
        .flow-subtab:focus-visible,
        .flow-upload:focus-visible,
        .flow-mini-tab:focus-visible {
          outline: 2px solid var(--color-focus);
          outline-offset: 2px;
        }
        .flow-upload.dragging {
          background: var(--color-info-soft);
          border-color: var(--color-info);
          color: var(--color-info-strong);
        }
        body {
          user-select: none;
          -webkit-user-select: none;
          -moz-user-select: none;
          -ms-user-select: none;
        }
        @media (max-width: 960px) {
          .table {
            display: block;
            overflow-x: auto;
            white-space: nowrap;
          }
        }
      `}
      </style>

      {/* Sidebar Overlay */}
      {sidebarOpen && (
        <div
          role="button"
          tabIndex={0}
          onClick={() => setSidebarOpen(false)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              setSidebarOpen(false);
            }
          }}
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.4)",
            zIndex: 998,
            animation: "fadeIn 0.2s ease",
          }}
        />
      )}

      {/* Sidebar Menu */}
      <div
        style={{
          position: "fixed",
          left: 0,
          top: 0,
          bottom: 0,
          width: "280px",
          background: "var(--color-surface)",
          border: "1px solid var(--color-border)",
          borderRadius: "0 12px 12px 0",
          boxShadow: sidebarOpen ? "4px 0 12px rgba(0,0,0,0.15)" : "none",
          zIndex: 999,
          transform: sidebarOpen ? "translateX(0)" : "translateX(-100%)",
          transition: "transform 0.3s ease",
          overflow: "auto",
          padding: "20px 0",
        }}
      >
        <div style={{ paddingBottom: "20px", borderBottom: "1px solid var(--color-border)" }}>
          <div
            style={{
              padding: "0 20px",
              marginBottom: "20px",
              fontSize: "18px",
              fontWeight: 700,
              color: "var(--color-text)",
            }}
          >
            Menu
          </div>
        </div>

        <div style={{ padding: "12px 12px" }}>
          <button
            onClick={() => {
              setSidebarOpen(false);
            }}
            style={{
              display: "block",
              width: "100%",
              padding: "12px 16px",
              background: "transparent",
              border: "1px solid var(--color-border-soft)",
              borderRadius: "8px",
              textAlign: "left",
              cursor: "pointer",
              fontSize: "14px",
              color: "var(--color-text)",
              marginBottom: "8px",
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "var(--color-primary-soft)";
              e.currentTarget.style.borderColor = "var(--color-primary)";
              e.currentTarget.style.color = "var(--color-primary)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
              e.currentTarget.style.borderColor = "var(--color-border-soft)";
              e.currentTarget.style.color = "var(--color-text)";
            }}
          >
            📁 Projects
          </button>

          <button
            onClick={() => {
              setSidebarOpen(false);
            }}
            style={{
              display: "block",
              width: "100%",
              padding: "12px 16px",
              background: "transparent",
              border: "1px solid var(--color-border-soft)",
              borderRadius: "8px",
              textAlign: "left",
              cursor: "pointer",
              fontSize: "14px",
              color: "var(--color-text)",
              marginBottom: "8px",
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "var(--color-primary-soft)";
              e.currentTarget.style.borderColor = "var(--color-primary)";
              e.currentTarget.style.color = "var(--color-primary)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
              e.currentTarget.style.borderColor = "var(--color-border-soft)";
              e.currentTarget.style.color = "var(--color-text)";
            }}
          >
            📄 Documents
          </button>

          <button
            onClick={() => {
              setSidebarOpen(false);
            }}
            style={{
              display: "block",
              width: "100%",
              padding: "12px 16px",
              background: "transparent",
              border: "1px solid var(--color-border-soft)",
              borderRadius: "8px",
              textAlign: "left",
              cursor: "pointer",
              fontSize: "14px",
              color: "var(--color-text)",
              marginBottom: "8px",
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "var(--color-primary-soft)";
              e.currentTarget.style.borderColor = "var(--color-primary)";
              e.currentTarget.style.color = "var(--color-primary)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
              e.currentTarget.style.borderColor = "var(--color-border-soft)";
              e.currentTarget.style.color = "var(--color-text)";
            }}
          >
            🔄 Workflows
          </button>

          <button
            onClick={() => {
              setSidebarOpen(false);
            }}
            style={{
              display: "block",
              width: "100%",
              padding: "12px 16px",
              background: "transparent",
              border: "1px solid var(--color-border-soft)",
              borderRadius: "8px",
              textAlign: "left",
              cursor: "pointer",
              fontSize: "14px",
              color: "var(--color-text)",
              marginBottom: "8px",
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "var(--color-primary-soft)";
              e.currentTarget.style.borderColor = "var(--color-primary)";
              e.currentTarget.style.color = "var(--color-primary)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
              e.currentTarget.style.borderColor = "var(--color-border-soft)";
              e.currentTarget.style.color = "var(--color-text)";
            }}
          >
            ⚙ Settings
          </button>
        </div>
      </div>

      {/* Main Content */}
      <ProjectsPanel />
      <div
        style={{
          background: "var(--color-surface)",
          border: "1px solid var(--color-border)",
          borderRadius: "8px",
          padding: "8px 4px",
          marginBottom: "4px",
          minHeight: "40px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px", width: "100%" }}>
          <ToolbarMenu />
        </div>

        {/* Save Status */}
        {saveStatus === "saving" ? (
          <span className="status" style={{ marginLeft: 8 }}>
            Saving...
          </span>
        ) : saveStatus === "error" ? (
          <span className="status" style={{ marginLeft: 8, color: "var(--color-danger)" }}>
            {saveError}
          </span>
        ) : null}
      </div>
      <div
        ref={containerRef}
        style={{ display: "flex", gap: "0px", flex: 1, minHeight: 0, alignItems: "stretch" }}
      >
        <div
          style={{
            flex: `${1 - infoRatio} 1 0`,
            display: "flex",
            flexDirection: "column",
            gap: "4px",
            minHeight: 0,
            minWidth: 0,
          }}
          ref={leftPanelRef}
        >
          <div
            className="card"
            style={{
              flex: isDetailPanelHidden ? "1 1 0" : `${1 - detailRatio} 1 0`,
              minHeight: 0,
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div className="meta" style={{ display: "none" }}>
              {/* Document register header hidden */}
            </div>
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    {visibleColumns.map((col) => (
                      <th
                        key={col.key}
                        style={{
                          position: "relative",
                          width: columnWidths[col.key] ? `${columnWidths[col.key]}px` : undefined,
                          minWidth: columnWidths[col.key]
                            ? `${columnWidths[col.key]}px`
                            : undefined,
                        }}
                      >
                        <div>{col.label}</div>
                        <input
                          value={filters[col.key]}
                          placeholder="Search..."
                          onChange={(e) => handleFilterChange(col.key, e.target.value)}
                        />
                        <button
                          type="button"
                          onMouseDown={(e) => startColResize(e, col.key)}
                          style={{
                            position: "absolute",
                            top: 0,
                            right: 0,
                            width: "6px",
                            height: "100%",
                            cursor: "col-resize",
                            background: "transparent",
                            border: "none",
                            padding: 0,
                          }}
                          title="Drag to resize column"
                          aria-label={`Resize column ${col.label}`}
                        />
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {isAdding && project && !documentsLoading && (
                    <>
                      <tr>
                        {visibleColumns.map((col) => {
                          const cellStyle = {
                            width: columnWidths[col.key] ? `${columnWidths[col.key]}px` : undefined,
                            minWidth: columnWidths[col.key]
                              ? `${columnWidths[col.key]}px`
                              : undefined,
                          };

                          if (col.id === "doc_name") {
                            return (
                              <td key={col.key} style={cellStyle}>
                                <input
                                  style={{
                                    width: "100%",
                                    padding: "6px 8px",
                                    borderRadius: "8px",
                                    border: "1px solid var(--color-border-strong)",
                                  }}
                                  value={newDocValues.doc_name_unique}
                                  onChange={(e) =>
                                    setNewDocValues((prev) => ({
                                      ...prev,
                                      doc_name_unique: e.target.value,
                                    }))
                                  }
                                  disabled={createStatus === "saving"}
                                  placeholder="Document name"
                                />
                              </td>
                            );
                          }

                          if (col.id === "title") {
                            return (
                              <td key={col.key} style={cellStyle}>
                                <input
                                  style={{
                                    width: "100%",
                                    padding: "6px 8px",
                                    borderRadius: "8px",
                                    border: "1px solid var(--color-border-strong)",
                                  }}
                                  value={newDocValues.title}
                                  onChange={(e) =>
                                    setNewDocValues((prev) => ({ ...prev, title: e.target.value }))
                                  }
                                  disabled={createStatus === "saving"}
                                  placeholder="Title"
                                />
                              </td>
                            );
                          }

                          if (col.id === "discipline") {
                            return (
                              <td key={col.key} style={cellStyle}>
                                <select
                                  style={{
                                    width: "100%",
                                    padding: "6px 8px",
                                    borderRadius: "8px",
                                    border: "1px solid var(--color-border-strong)",
                                    background: "var(--color-surface)",
                                  }}
                                  value={String(newDocValues.discipline_id ?? "")}
                                  onChange={(e) =>
                                    setNewDocValues((prev) => {
                                      const nextDiscipline = e.target.value;
                                      const nextTypes = docTypes.filter(
                                        (item) =>
                                          String(item.ref_discipline_id ?? "") === nextDiscipline,
                                      );
                                      const currentTypeMatches = docTypes.find(
                                        (item) =>
                                          String(item.type_id) === String(prev.type_id) &&
                                          String(item.ref_discipline_id ?? "") === nextDiscipline,
                                      );
                                      return {
                                        ...prev,
                                        discipline_id: nextDiscipline,
                                        type_id: currentTypeMatches
                                          ? prev.type_id
                                          : String(nextTypes[0]?.type_id ?? ""),
                                      };
                                    })
                                  }
                                  disabled={createStatus === "saving"}
                                >
                                  <option value="">Select discipline...</option>
                                  {disciplines.map((item) => (
                                    <option
                                      key={item.discipline_id}
                                      value={String(item.discipline_id)}
                                    >
                                      {item.discipline_name}
                                      {item.discipline_acronym
                                        ? ` (${item.discipline_acronym})`
                                        : ""}
                                    </option>
                                  ))}
                                </select>
                              </td>
                            );
                          }

                          if (col.id === "doc_type") {
                            return (
                              <td key={col.key} style={cellStyle}>
                                <select
                                  style={{
                                    width: "100%",
                                    padding: "6px 8px",
                                    borderRadius: "8px",
                                    border: "1px solid var(--color-border-strong)",
                                    background: "var(--color-surface)",
                                  }}
                                  value={String(newDocValues.type_id ?? "")}
                                  onChange={(e) =>
                                    setNewDocValues((prev) => {
                                      const nextType = e.target.value;
                                      const selectedType = docTypes.find(
                                        (item) => String(item.type_id) === nextType,
                                      );
                                      return {
                                        ...prev,
                                        type_id: nextType,
                                        discipline_id:
                                          selectedType?.ref_discipline_id ?? prev.discipline_id,
                                      };
                                    })
                                  }
                                  disabled={createStatus === "saving"}
                                >
                                  <option value="">Select type...</option>
                                  {newDocTypeOptions.map((item) => (
                                    <option key={item.type_id} value={String(item.type_id)}>
                                      {item.doc_type_name}
                                      {item.discipline_acronym
                                        ? ` (${item.discipline_acronym})`
                                        : ""}
                                    </option>
                                  ))}
                                </select>
                              </td>
                            );
                          }

                          if (col.id === "jobpack") {
                            return (
                              <td key={col.key} style={cellStyle}>
                                <select
                                  style={{
                                    width: "100%",
                                    padding: "6px 8px",
                                    borderRadius: "8px",
                                    border: "1px solid var(--color-border-strong)",
                                    background: "var(--color-surface)",
                                  }}
                                  value={String(newDocValues.jobpack_id ?? "")}
                                  onChange={(e) =>
                                    setNewDocValues((prev) => ({
                                      ...prev,
                                      jobpack_id: e.target.value,
                                    }))
                                  }
                                  disabled={createStatus === "saving"}
                                >
                                  <option value="">Select jobpack...</option>
                                  {jobpacks.map((item) => (
                                    <option key={item.jobpack_id} value={String(item.jobpack_id)}>
                                      {item.jobpack_name}
                                    </option>
                                  ))}
                                </select>
                              </td>
                            );
                          }

                          if (col.id === "area") {
                            return (
                              <td key={col.key} style={cellStyle}>
                                <select
                                  style={{
                                    width: "100%",
                                    padding: "6px 8px",
                                    borderRadius: "8px",
                                    border: "1px solid var(--color-border-strong)",
                                    background: "var(--color-surface)",
                                  }}
                                  value={String(newDocValues.area_id ?? "")}
                                  onChange={(e) =>
                                    setNewDocValues((prev) => ({
                                      ...prev,
                                      area_id: e.target.value,
                                    }))
                                  }
                                  disabled={createStatus === "saving"}
                                >
                                  <option value="">Select area...</option>
                                  {areas.map((item) => (
                                    <option key={item.area_id} value={String(item.area_id)}>
                                      {item.area_name}
                                      {item.area_acronym ? ` (${item.area_acronym})` : ""}
                                    </option>
                                  ))}
                                </select>
                              </td>
                            );
                          }

                          if (col.id === "unit") {
                            return (
                              <td key={col.key} style={cellStyle}>
                                <select
                                  style={{
                                    width: "100%",
                                    padding: "6px 8px",
                                    borderRadius: "8px",
                                    border: "1px solid var(--color-border-strong)",
                                    background: "var(--color-surface)",
                                  }}
                                  value={String(newDocValues.unit_id ?? "")}
                                  onChange={(e) =>
                                    setNewDocValues((prev) => ({
                                      ...prev,
                                      unit_id: e.target.value,
                                    }))
                                  }
                                  disabled={createStatus === "saving"}
                                >
                                  <option value="">Select unit...</option>
                                  {units.map((item) => (
                                    <option key={item.unit_id} value={String(item.unit_id)}>
                                      {item.unit_name}
                                    </option>
                                  ))}
                                </select>
                              </td>
                            );
                          }

                          if (col.id === "rev_code") {
                            return (
                              <td key={col.key} style={cellStyle}>
                                <select
                                  style={{
                                    width: "100%",
                                    padding: "6px 8px",
                                    borderRadius: "8px",
                                    border: "1px solid var(--color-border-strong)",
                                    background: "var(--color-surface)",
                                  }}
                                  value={String(newDocValues.rev_code_id ?? "")}
                                  onChange={(e) =>
                                    setNewDocValues((prev) => ({
                                      ...prev,
                                      rev_code_id: e.target.value,
                                    }))
                                  }
                                  disabled={createStatus === "saving"}
                                >
                                  <option value="">Select rev code...</option>
                                  {revisionOverviews.map((item) => (
                                    <option key={item.rev_code_id} value={String(item.rev_code_id)}>
                                      {item.rev_code_acronym
                                        ? `${item.rev_code_acronym} (${item.rev_code_name})`
                                        : item.rev_code_name}
                                    </option>
                                  ))}
                                </select>
                              </td>
                            );
                          }

                          return (
                            <td key={col.key} style={cellStyle}>
                              —
                            </td>
                          );
                        })}
                      </tr>
                      {createError && (
                        <tr>
                          <td
                            colSpan={visibleColumns.length}
                            style={{ color: "var(--color-danger)", padding: "6px 10px" }}
                          >
                            {createError}
                          </td>
                        </tr>
                      )}
                    </>
                  )}
                  {documentsLoading ? (
                    <tr>
                      <td className="status-row" colSpan={visibleColumns.length}>
                        <span className="spinner" aria-label="Loading documents" />
                      </td>
                    </tr>
                  ) : documentsError ? (
                    <tr>
                      <td className="status-row error" colSpan={visibleColumns.length}>
                        {documentsError}
                      </td>
                    </tr>
                  ) : !project ? (
                    <tr>
                      <td className="status-row" colSpan={visibleColumns.length}>
                        Select a project to load documents.
                      </td>
                    </tr>
                  ) : filteredDocuments.length === 0 ? (
                    <tr>
                      <td className="status-row" colSpan={visibleColumns.length}>
                        No documents match your filters.
                      </td>
                    </tr>
                  ) : (
                    filteredDocuments.map((doc) => {
                      const rowId = doc.doc_id || doc.doc_name || doc.id;
                      const isEditing = editRowId === rowId;

                      return (
                        <tr
                          key={rowId}
                          onClick={() => {
                            setSelectedDocId(rowId);
                            // Find and expand InDesign tab
                            const inDesignStatus = orderedStatuses.find(
                              (s) => s.rev_status_name?.toLowerCase() === "indesign",
                            );
                            if (inDesignStatus) {
                              setInfoActiveStep(String(inDesignStatus.rev_status_id));
                            }
                          }}
                          onDoubleClick={() => startEdit(doc)}
                          style={{
                            background:
                              selectedDocId === rowId ? "var(--color-row-selected)" : undefined,
                          }}
                        >
                          {visibleColumns.map((col) => {
                            const isEditable = col.id === "doc_name" || col.id === "title";
                            const selectConfig = lookupOptionsByColumn[col.id];
                            const value = renderCell(doc, col);

                            if (isEditing && (isEditable || selectConfig)) {
                              return (
                                <td
                                  key={col.key}
                                  style={{
                                    width: columnWidths[col.key]
                                      ? `${columnWidths[col.key]}px`
                                      : undefined,
                                    minWidth: columnWidths[col.key]
                                      ? `${columnWidths[col.key]}px`
                                      : undefined,
                                  }}
                                >
                                  {selectConfig ? (
                                    <select
                                      style={{
                                        width: "100%",
                                        padding: "6px 8px",
                                        borderRadius: "8px",
                                        border: "1px solid var(--color-border-strong)",
                                        background: "var(--color-surface)",
                                      }}
                                      value={String(editValues[selectConfig.field] ?? "")}
                                      onChange={(e) =>
                                        setEditValues((prev) => {
                                          const nextValue = e.target.value;
                                          if (selectConfig.field === "type_id") {
                                            const selectedType = selectConfig.options.find(
                                              (item) =>
                                                String(item[selectConfig.valueKey]) === nextValue,
                                            );
                                            return {
                                              ...prev,
                                              type_id: nextValue,
                                              discipline_id:
                                                selectedType?.ref_discipline_id ??
                                                prev.discipline_id,
                                            };
                                          }
                                          if (selectConfig.field === "discipline_id") {
                                            const nextTypes = docTypes.filter(
                                              (item) =>
                                                String(item.ref_discipline_id ?? "") === nextValue,
                                            );
                                            const currentTypeMatches = docTypes.find(
                                              (item) =>
                                                String(item.type_id) === String(prev.type_id) &&
                                                String(item.ref_discipline_id ?? "") === nextValue,
                                            );
                                            return {
                                              ...prev,
                                              discipline_id: nextValue,
                                              type_id: currentTypeMatches
                                                ? prev.type_id
                                                : String(nextTypes[0]?.type_id ?? ""),
                                            };
                                          }
                                          return {
                                            ...prev,
                                            [selectConfig.field]: nextValue,
                                          };
                                        })
                                      }
                                    >
                                      <option value="">{selectConfig.placeholder}</option>
                                      {selectConfig.options.map((item) => {
                                        const optionValue = item[selectConfig.valueKey];
                                        return (
                                          <option key={optionValue} value={String(optionValue)}>
                                            {selectConfig.getLabel(item)}
                                          </option>
                                        );
                                      })}
                                    </select>
                                  ) : (
                                    <input
                                      style={{
                                        width: "100%",
                                        padding: "6px 8px",
                                        borderRadius: "8px",
                                        border: "1px solid var(--color-border-strong)",
                                      }}
                                      value={
                                        col.id === "doc_name"
                                          ? editValues.doc_name_unique
                                          : editValues.title
                                      }
                                      onChange={(e) =>
                                        setEditValues((prev) => ({
                                          ...prev,
                                          [col.id === "doc_name" ? "doc_name_unique" : "title"]:
                                            e.target.value,
                                        }))
                                      }
                                    />
                                  )}
                                </td>
                              );
                            }

                            return (
                              <td
                                key={col.key}
                                style={{
                                  width: columnWidths[col.key]
                                    ? `${columnWidths[col.key]}px`
                                    : undefined,
                                  minWidth: columnWidths[col.key]
                                    ? `${columnWidths[col.key]}px`
                                    : undefined,
                                }}
                              >
                                {value}
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
          <div
            style={{
              position: "relative",
              height: "8px",
              display: "flex",
              alignItems: "center",
              justifyContent: "flex-start",
            }}
          >
            <button
              type="button"
              onMouseDown={startRowResize}
              onKeyDown={(event) => {
                if (event.key === "ArrowUp") {
                  setDetailRatio((prev) => Math.max(0.2, prev - 0.02));
                  event.preventDefault();
                }
                if (event.key === "ArrowDown") {
                  setDetailRatio((prev) => Math.min(0.8, prev + 0.02));
                  event.preventDefault();
                }
              }}
              style={{
                width: "100%",
                height: "100%",
                background: isDraggingRow ? "var(--color-info)" : "var(--color-border)",
                cursor: "row-resize",
                transition: isDraggingRow ? "none" : "background 0.2s",
                userSelect: "none",
                padding: 0,
                border: "none",
                position: "absolute",
              }}
              title="Drag to resize panels"
              aria-label="Resize panels"
            />
            {!isDetailPanelHidden && (
              <button
                type="button"
                onClick={() => setIsDetailPanelHidden(!isDetailPanelHidden)}
                style={{
                  position: "relative",
                  zIndex: 101,
                  width: "80px",
                  height: "8px",
                  padding: "0",
                  background: "var(--color-info)",
                  border: "1px solid var(--color-info)",
                  borderRadius: "4px",
                  cursor: "pointer",
                  fontSize: "12px",
                  color: "white",
                  fontWeight: "bold",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  transition: "all 0.2s",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "var(--color-info-dark)";
                  e.currentTarget.style.boxShadow = "0 2px 6px rgba(0,0,0,0.2)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "var(--color-info)";
                  e.currentTarget.style.boxShadow = "none";
                }}
                title="Hide revisions"
                aria-label="Hide revisions"
              ></button>
            )}
            {isDetailPanelHidden && (
              <button
                type="button"
                onClick={() => setIsDetailPanelHidden(!isDetailPanelHidden)}
                style={{
                  position: "relative",
                  zIndex: 101,
                  width: "80px",
                  height: "8px",
                  padding: "0",
                  background: "var(--color-success)",
                  border: "1px solid var(--color-success)",
                  borderRadius: "4px",
                  cursor: "pointer",
                  fontSize: "12px",
                  color: "white",
                  fontWeight: "bold",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  transition: "all 0.2s",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "var(--color-success-dark)";
                  e.currentTarget.style.boxShadow = "0 2px 6px rgba(0,0,0,0.2)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "var(--color-success)";
                  e.currentTarget.style.boxShadow = "none";
                }}
                title="Show revisions"
                aria-label="Show revisions"
              ></button>
            )}
          </div>
          <div
            style={{
              flex: isDetailPanelHidden ? "0 0 0" : `${detailRatio} 1 0`,
              background: "var(--color-surface)",
              border: "1px solid var(--color-border)",
              borderRadius: "12px",
              padding: 0,
              boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
              minHeight: 0,
              display: hideWindowsOnDrag || isDetailPanelHidden ? "none" : "flex",
              flexDirection: "column",
              overflow: "hidden",
              position: "relative",
            }}
          >
            <div className="detail-tabs">
              {["Details", "TAGs", "References", "Plan", "Information"].map((tab) => (
                <button
                  key={tab}
                  className={`detail-tab ${activeDetailTab === tab ? "active" : ""}`}
                  onClick={() => setActiveDetailTab(tab)}
                >
                  {tab}
                </button>
              ))}
            </div>
            <div className="detail-tab-panel" style={{ flex: 1 }}>
              {activeDetailTab === "Details" ? (
                <div
                  style={{ padding: "12px", color: "var(--color-text-muted)", fontSize: "13px" }}
                >
                  {selectedDoc ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                      <div>
                        <div
                          style={{
                            fontWeight: 600,
                            color: "var(--color-text)",
                            marginBottom: "4px",
                          }}
                        >
                          Current Revision ID
                        </div>
                        <div
                          style={{
                            fontSize: "16px",
                            fontWeight: 700,
                            color: "var(--color-accent)",
                            padding: "8px 12px",
                            background: "var(--color-accent-soft)",
                            borderRadius: "6px",
                          }}
                        >
                          {selectedDoc.rev_current_id || "N/A"}
                        </div>
                      </div>
                      {selectedDoc.rev_seq_num && (
                        <div>
                          <div
                            style={{
                              fontWeight: 600,
                              color: "var(--color-text)",
                              marginBottom: "4px",
                            }}
                          >
                            Sequence Number
                          </div>
                          <div style={{ fontSize: "14px" }}>{selectedDoc.rev_seq_num}</div>
                        </div>
                      )}
                      {selectedDoc.rev_code_name && (
                        <div>
                          <div
                            style={{
                              fontWeight: 600,
                              color: "var(--color-text)",
                              marginBottom: "4px",
                            }}
                          >
                            Revision Code
                          </div>
                          <div style={{ fontSize: "14px" }}>{selectedDoc.rev_code_name}</div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div>Select a document to view revisions.</div>
                  )}
                </div>
              ) : (
                <div style={{ color: "var(--color-text-muted)", fontSize: "13px" }}>
                  {activeDetailTab} content will appear here.
                </div>
              )}
            </div>
          </div>
        </div>
        <div
          style={{
            position: "relative",
            width: "8px",
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "center",
          }}
        >
          <button
            type="button"
            onMouseDown={startBorderResize}
            onKeyDown={(event) => {
              if (event.key === "ArrowLeft") {
                setInfoRatio((prev) => Math.min(0.85, prev + 0.02));
                event.preventDefault();
              }
              if (event.key === "ArrowRight") {
                setInfoRatio((prev) => Math.max(0.15, prev - 0.02));
                event.preventDefault();
              }
            }}
            style={{
              width: "100%",
              height: "100%",
              background: isDraggingBorder ? "var(--color-info)" : "var(--color-border)",
              cursor: "col-resize",
              transition: isDraggingBorder ? "none" : "background 0.2s",
              userSelect: "none",
              padding: 0,
              border: "none",
              position: "absolute",
            }}
            title="Drag to resize panels"
            aria-label="Resize panels"
          />
        </div>
        <div
          style={{
            flex: `${infoRatio} 1 0`,
            display: "flex",
            flexDirection: "column",
            minWidth: 0,
            overflow: "visible",
          }}
        >
          <div className="flow-card" style={{ flex: 1 }}>
            <div className="flow-header">DOCUMENT FLOW</div>
            <div className="flow-body">
              {revStatusLoading ? (
                <div className="flow-empty">Loading statuses…</div>
              ) : revStatusError ? (
                <div className="flow-empty">{revStatusError}</div>
              ) : orderedStatuses.length === 0 ? (
                <div className="flow-empty">No statuses configured.</div>
              ) : (
                orderedStatuses.map((status) => {
                  const behaviorName = behaviorNameById[status.ui_behavior_id];
                  const behaviorFile = behaviorFileById[status.ui_behavior_id];
                  const behaviorFileLabel =
                    typeof behaviorFile === "string"
                      ? behaviorFile.replace(/\.jsx$/i, "")
                      : behaviorFile;
                  const Behavior = resolveBehaviorByFile(behaviorFile);
                  const statusKey = String(status.rev_status_id);
                  const isActive = infoActiveStep === statusKey;
                  const panelId = `flow-panel-${statusKey}`;
                  const isMenuOpen = statusMenuOpen[statusKey] || false;

                  return (
                    <React.Fragment key={status.rev_status_id}>
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          gap: "4px",
                          position: "relative",
                        }}
                      >
                        <button
                          type="button"
                          className={`flow-step ${isActive ? "active" : ""}`}
                          aria-expanded={isActive}
                          aria-controls={panelId}
                          data-ui-behavior={behaviorFile || "default"}
                          data-final={status.final ? "true" : "false"}
                          onClick={() => {
                            if (!isFlowEnabled) {
                              return;
                            }
                            if (isActive) {
                              setInfoActiveStep(null);
                              return;
                            }
                            setInfoActiveStep(statusKey);
                            setInfoActiveSubTab("Files with Comments");
                          }}
                          style={{ flex: 1 }}
                          disabled={!isFlowEnabled}
                        >
                          <span className="dot">
                            {status.final ? (
                              <span className="dot__inner" aria-hidden="true" />
                            ) : (
                              <svg className="dot__icon" viewBox="0 0 18 18" aria-hidden="true">
                                <path d="M6 7.5 L9 10.5 L12 7.5" />
                              </svg>
                            )}
                          </span>
                          <span className="flow-step__label">{status.rev_status_name}</span>
                          <span className="flow-step__behavior" style={{ display: "none" }}>
                            {behaviorFileLabel || "Default"}
                          </span>
                        </button>
                        {isActive && isFlowEnabled && (
                          <div
                            style={{
                              position: "relative",
                            }}
                          >
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                setStatusMenuOpen((prev) => ({
                                  ...prev,
                                  [statusKey]: !isMenuOpen,
                                }));
                              }}
                              style={{
                                background: "transparent",
                                border: "none",
                                cursor: "pointer",
                                padding: "6px 12px",
                                fontSize: "20px",
                                color: "var(--color-text-muted)",
                                transition: "color 0.2s",
                              }}
                              onMouseEnter={(e) => {
                                e.currentTarget.style.color = "white";
                                e.currentTarget.style.background = "var(--color-info)";
                                e.currentTarget.style.borderRadius = "4px";
                              }}
                              onMouseLeave={(e) => {
                                e.currentTarget.style.color = "var(--color-text-muted)";
                                e.currentTarget.style.background = "transparent";
                              }}
                              title="Status menu"
                              aria-label="Status menu"
                              disabled={!isFlowEnabled}
                            >
                              ⋮
                            </button>
                            {isMenuOpen && (
                              <div
                                style={{
                                  position: "absolute",
                                  top: "100%",
                                  right: 0,
                                  background: "var(--color-surface)",
                                  border: "1px solid var(--color-border)",
                                  borderRadius: "6px",
                                  boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                                  minWidth: "180px",
                                  zIndex: 1000,
                                  marginTop: "4px",
                                }}
                              >
                                <button
                                  type="button"
                                  onClick={() => {
                                    if (
                                      window.confirm(`Issue "${status.rev_status_name}" to IDC?`)
                                    ) {
                                      alert(`Status "${status.rev_status_name}" issued to IDC`);
                                    }
                                    setStatusMenuOpen((prev) => ({ ...prev, [statusKey]: false }));
                                  }}
                                  style={{
                                    display: "block",
                                    width: "100%",
                                    padding: "10px 16px",
                                    background: "transparent",
                                    border: "none",
                                    textAlign: "left",
                                    cursor: "pointer",
                                    fontSize: "13px",
                                    color: "var(--color-text)",
                                    transition: "background 0.2s",
                                  }}
                                  onMouseEnter={(e) => {
                                    e.currentTarget.style.background = "var(--color-background)";
                                  }}
                                  onMouseLeave={(e) => {
                                    e.currentTarget.style.background = "transparent";
                                  }}
                                >
                                  Issue to IDC
                                </button>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                      {isActive && isFlowEnabled && (
                        <div
                          id={panelId}
                          className="flow-inline-content"
                          data-ui-behavior={behaviorFile || ""}
                        >
                          <React.Suspense
                            fallback={<div className="flow-empty">Loading behavior…</div>}
                          >
                            <Behavior
                              selectedDoc={selectedDoc}
                              behaviorName={behaviorName}
                              behaviorFile={behaviorFile}
                              statusKey={statusKey}
                              infoActiveSubTab={infoActiveSubTab}
                              onSubTabChange={setInfoActiveSubTab}
                              uploadedFiles={uploadedFiles}
                              expandedRevisions={expandedRevisions}
                              onRevisionToggle={handleRevisionToggle}
                              isDraggingUpload={isDraggingUpload}
                              uploadDragProps={buildUploadDragProps}
                              onUploadClick={() => uploadInputRef.current?.click()}
                              uploadInputRef={uploadInputRef}
                              onFileSelect={handleUploadSelect}
                              onSelectFile={handleSelectFile}
                              onDownloadFile={handleDownloadFile}
                              onDeleteFile={handleDeleteFile}
                              selectedFileId={selectedFileId}
                              apiBase={apiBase}
                            />
                          </React.Suspense>
                        </div>
                      )}
                    </React.Fragment>
                  );
                })
              )}
              {!revStatusLoading && !revStatusError && (
                <>
                  <button
                    type="button"
                    className={`flow-step ${infoActiveStep === "history" ? "active" : ""}`}
                    aria-expanded={infoActiveStep === "history"}
                    aria-controls="flow-panel-history"
                    data-ui-behavior="HistoryBehavior.jsx"
                    data-final="false"
                    onClick={() => {
                      if (!isFlowEnabled) {
                        return;
                      }
                      if (infoActiveStep === "history") {
                        setInfoActiveStep(null);
                        return;
                      }
                      setInfoActiveStep("history");
                    }}
                    disabled={!isFlowEnabled}
                  >
                    <span className="dot">
                      <svg className="dot__icon" viewBox="0 0 18 18" aria-hidden="true">
                        <path d="M5 4 H13 V14 H5 Z" />
                        <path d="M7 7 H11" />
                        <path d="M7 10 H11" />
                      </svg>
                    </span>
                    <span className="flow-step__label">History</span>
                    <span className="flow-step__behavior">History</span>
                  </button>
                  {infoActiveStep === "history" && isFlowEnabled && (
                    <div
                      id="flow-panel-history"
                      className="flow-inline-content"
                      data-ui-behavior="HistoryBehavior.jsx"
                    >
                      <React.Suspense
                        fallback={<div className="flow-empty">Loading behavior…</div>}
                      >
                        {(() => {
                          const Behavior = resolveBehaviorByFile("HistoryBehavior.jsx");
                          return (
                            <Behavior behaviorName="History" behaviorFile="HistoryBehavior.jsx" />
                          );
                        })()}
                      </React.Suspense>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

export default App;

App.propTypes = {};
