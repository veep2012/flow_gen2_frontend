import React from "react";
import { documentGridColumns } from "./grids/documents";
import { useFetchDocuments } from "./hooks/useFetchDocuments";

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
    new URL(trimmed, window.location.origin);
    return trimmed;
  } catch (_err) {
    console.warn("Invalid VITE_API_BASE_URL, falling back to default /api/v1");
    return fallback;
  }
};

function App() {
  const apiBase = normalizeApiBase(import.meta.env.VITE_API_BASE_URL);
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
    background: 'var(--color-accent)',
    color: 'var(--color-accent-contrast)',
    border: 'none',
    borderRadius: '4px',
    padding: '6px 12px',
    marginRight: '2px',
    fontSize: '13px',
    fontWeight: 500,
    cursor: 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
    boxShadow: '0 1px 2px rgba(0,0,0,0.08)',
    transition: 'background 0.2s',
  };

  const iconStyle = {
    marginRight: '5px',
    fontSize: '14px',
  };

  const [infoRatio, setInfoRatio] = React.useState(0.35);
  const [columnWidths, setColumnWidths] = React.useState({});
  const [activeDetailTab, setActiveDetailTab] = React.useState("Revisions");
  const [infoActiveStep, setInfoActiveStep] = React.useState("IDC");
  const [infoActiveSubTab, setInfoActiveSubTab] = React.useState("Comments");
  const [isDraggingUpload, setIsDraggingUpload] = React.useState(false);
  const [isDraggingBorder, setIsDraggingBorder] = React.useState(false);
  const [uploadedFiles, setUploadedFiles] = React.useState({});
  const [expandedRevisions, setExpandedRevisions] = React.useState({});
  const containerRef = React.useRef(null);
  const uploadInputRef = React.useRef(null);
  const [selectedDocId, setSelectedDocId] = React.useState(null);
  const [editRowId, setEditRowId] = React.useState(null);
  const [editValues, setEditValues] = React.useState({ doc_name_unique: "", title: "" });
  const [saveError, setSaveError] = React.useState(null);
  const [saveStatus, setSaveStatus] = React.useState("idle");

  const editingDoc = React.useMemo(
    () => filteredDocuments.find((doc) => (doc.doc_id || doc.doc_name || doc.id) === editRowId),
    [filteredDocuments, editRowId],
  );

  const ToolbarMenu = () => {
    const handleAddNew = () => console.log('Add new clicked');
    const handleEdit = () => {
      if (!selectedDoc) {
        setSaveStatus("error");
        setSaveError("Select a row to edit");
        return;
      }
      startEdit(selectedDoc);
    };
    const handleDelete = () => console.log('Delete clicked');
    const handleExport = () => console.log('Export clicked');
    const handleUndo = () => console.log('Undo clicked');
    const handleRedo = () => console.log('Redo clicked');

    if (editRowId) {
      return (
        <div style={{ display: 'flex', gap: '4px', alignItems: 'center', padding: '0 6px' }}>
          <button
            style={buttonStyle}
            title="Save changes"
            onClick={() => applyEdit(editingDoc || selectedDoc)}
            disabled={saveStatus === "saving"}
          >
            <span style={iconStyle}>💾</span>
            Save
          </button>
          <button
            style={{ ...buttonStyle, background: 'var(--color-border)', color: 'var(--color-text)' }}
            title="Cancel editing"
            onClick={cancelEdit}
            disabled={saveStatus === "saving"}
          >
            <span style={iconStyle}>✕</span>
            Cancel
          </button>
        </div>
      );
    }

    return (
      <div style={{ display: 'flex', gap: '4px', alignItems: 'center', padding: '0 6px' }}>
        <button style={buttonStyle} title="Add new document" onClick={handleAddNew}>
          <span style={iconStyle}>+</span>
          Add new
        </button>
        <button style={buttonStyle} title="Edit selected document" onClick={handleEdit}>
          <span style={iconStyle}>✎</span>
          Edit
        </button>
        <button style={buttonStyle} title="Delete selected document" onClick={handleDelete}>
          <span style={iconStyle}>🗑</span>
          Delete
        </button>
        <button style={buttonStyle} title="Export documents" onClick={handleExport}>
          <span style={iconStyle}>⬇</span>
          Export to...
        </button>
        <button style={{ ...buttonStyle, padding: '6px 10px' }} title="Undo" onClick={handleUndo}>
          <span style={iconStyle}>↶</span>
        </button>
        <button style={{ ...buttonStyle, padding: '6px 10px' }} title="Redo" onClick={handleRedo}>
          <span style={iconStyle}>↷</span>
        </button>
      </div>
    );
  };

  const ProjectsPanel = () => {
    return (
      <div style={{ 
        background: 'var(--color-success-soft)',
        border: '1px solid var(--color-success-border)',
        borderRadius: '8px', 
        padding: '12px 14px', 
        marginBottom: '4px',
        boxShadow: '0 2px 6px rgba(0,0,0,0.08)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <label style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-success-text)' }}>
            Project:
          </label>
          <select
            value={project}
            onChange={(e) => setProject(e.target.value)}
            aria-label="Select project"
            style={{
              border: '1px solid var(--color-success-border-strong)',
              borderRadius: '8px',
              padding: '7px 10px',
              fontSize: '13px',
              color: 'var(--color-text)',
              background: 'var(--color-surface)',
              minWidth: '220px',
              cursor: 'pointer'
            }}
          >
            <option value="">Project number</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
          {projectsError ? <span style={{ fontSize: '12px', color: 'var(--color-danger)' }}>{projectsError}</span> : null}
          <div className="task-cabinet" style={{ marginLeft: 'auto', padding: 0 }}>
            <div className="task-cabinet__label">Task cabinet:</div>
            {cabinetTabs.map((tab) => (
              <div key={tab.label} className="task-tab">
                <span style={{ color: 'var(--color-success-text)', fontWeight: 600 }}>{tab.label}</span>
                <span className="task-tab__badge" style={{ background: tab.tone }}>{tab.count}</span>
              </div>
            ))}
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
        window.removeEventListener("mousemove", handleMove);
        window.removeEventListener("mouseup", handleUp);
      };

      window.addEventListener("mousemove", handleMove);
      window.addEventListener("mouseup", handleUp);
    },
    [infoRatio],
  );

  const startEdit = React.useCallback(
    (doc) => {
      if (!doc) return;
      const rowId = doc.doc_id || doc.doc_name || doc.doc_name_unique || doc.id;
      setSelectedDocId(rowId);
      setEditRowId(rowId);
      setSaveError(null);
      setSaveStatus("idle");
      setEditValues({
        doc_name_unique: doc.doc_name || doc.doc_name_unique || "",
        title: doc.title || "",
      });
    },
    [],
  );

  const cancelEdit = React.useCallback(() => {
    setEditRowId(null);
    setSaveError(null);
    setSaveStatus("idle");
  }, []);

  const applyEdit = React.useCallback(
    async (doc) => {
      if (!doc) return;
      const toNumber = (value) => {
        const num = Number(value);
        return Number.isFinite(num) ? num : 0;
      };

      const payload = {
        doc_id: toNumber(doc.doc_id ?? doc.id ?? 0),
        doc_name_unique: editValues.doc_name_unique || doc.doc_name_unique || doc.doc_name || "",
        title: editValues.title ?? doc.title ?? "",
        project_id: toNumber(doc.project_id ?? doc.project ?? 0),
        jobpack_id: toNumber(doc.jobpack_id ?? 0),
        type_id: toNumber(doc.type_id ?? doc.doc_type_id ?? doc.doc_type ?? 0),
        area_id: toNumber(doc.area_id ?? 0),
        unit_id: toNumber(doc.unit_id ?? 0),
        rev_actual_id: toNumber(doc.rev_actual_id ?? 0),
        rev_current_id: toNumber(doc.rev_current_id ?? 0),
      };

      setSaveStatus("saving");
      setSaveError(null);

      try {
        const res = await fetch(`${apiBase}/documents/update`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          const text = await res.text();
          throw new Error(text || `Update failed (${res.status})`);
        }

        setSaveStatus("saved");
        setEditRowId(null);
        reloadDocuments();
      } catch (err) {
        setSaveStatus("error");
        setSaveError(err.message || "Unknown error while saving");
      }
    },
    [apiBase, editValues, reloadDocuments],
  );

  const handleUploadFiles = (files) => {
    const list = Array.from(files || []);
    if (!list.length) return;
    
    const step = infoActiveStep;
    const fileNames = list.map(f => f.name);
    
    setUploadedFiles(prev => ({
      ...prev,
      [step]: [...(prev[step] || []), ...fileNames]
    }));
    
    // Auto-expand the revision tree
    setExpandedRevisions(prev => ({
      ...prev,
      [step]: { ...prev[step], isOpen: true }
    }));
  };

  const handleUploadDrop = (e) => {
    e.preventDefault();
    setIsDraggingUpload(false);
    handleUploadFiles(e.dataTransfer?.files);
  };

  const handleUploadSelect = (e) => {
    handleUploadFiles(e.target.files);
    e.target.value = "";
  };

  const uploadDragProps = {
    onDragOver: (e) => { e.preventDefault(); setIsDraggingUpload(true); },
    onDragLeave: () => setIsDraggingUpload(false),
    onDrop: handleUploadDrop,
  };

  return (
    <main className="page" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <style>
        {`
        :root {
          --color-bg: #f5f7fb;
          --color-surface: #ffffff;
          --color-surface-alt: #f8fafc;
          --color-surface-muted: #f1f5f9;
          --color-surface-muted-strong: #e5e7eb;
          --color-surface-subtle: #f7fafc;
          --color-border: #e2e8f0;
          --color-border-soft: #d9e2ec;
          --color-border-strong: #cbd5e0;
          --color-text: #1f2933;
          --color-text-muted: #52606d;
          --color-text-subtle: #98a2b3;
          --color-text-strong: #344155;
          --color-text-secondary: #4a5568;
          --color-primary: #0f766e;
          --color-primary-contrast: #ffffff;
          --color-primary-soft: #eef6f4;
          --color-primary-outline: rgba(15, 118, 110, 0.15);
          --color-accent: #4d6b8a;
          --color-accent-contrast: #ffffff;
          --color-info: #3b82f6;
          --color-info-strong: #1e3a8a;
          --color-info-soft: #ecf4ff;
          --color-warning: #dd6b20;
          --color-danger: #c53030;
          --color-danger-soft: #fff5f5;
          --color-success: #16a34a;
          --color-success-soft: #f0fbf4;
          --color-success-border: #b6e3c8;
          --color-success-border-strong: #8fd19e;
          --color-success-text: #22543d;
          --color-row-selected: #f0f4ff;
          --color-focus: #2563eb;
          --color-spinner-start: #2f80ed;
          --color-spinner-end: #4ea1ff;
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
          margin-top: 4px;
          padding: 6px 8px;
          border: 1px solid var(--color-border-soft);
          border-radius: 8px;
          font-size: 13px;
          color: var(--color-text-muted);
          background: var(--color-surface);
          caret-color: transparent; /* Hide blinking text cursor in header filters */
        }
        .table td {
          padding: 6px 8px;
          border-bottom: 1px solid var(--color-border);
          position: relative;
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
          font-size: 18px;
          font-weight: 700;
          color: var(--color-text);
        }
        .meta .count {
          font-size: 13px;
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
          font-size: 13px;
          font-weight: 600;
          color: var(--color-success-text);
          min-width: 92px;
        }
        .task-tab {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          background: var(--color-surface);
          border: 1px solid var(--color-success-border-strong);
          border-radius: 8px;
          padding: 7px 10px;
          font-size: 13px;
          font-weight: 600;
          color: var(--color-text);
          box-shadow: none;
          cursor: default;
        }
        .task-tab__badge {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 22px;
          height: 22px;
          padding: 0 6px;
          border-radius: 6px;
          font-weight: 700;
          font-size: 12px;
          color: var(--color-surface);
        }
        .detail-tabs {
          display: flex;
          gap: 2px;
          border-bottom: 1px solid var(--color-border);
          background: var(--color-surface-alt);
          padding: 4px 6px 0;
        }
        .detail-tab {
          padding: 8px 12px;
          border: 1px solid var(--color-border);
          border-bottom: none;
          border-radius: 10px 10px 0 0;
          background: var(--color-surface-muted);
          font-size: 13px;
          cursor: pointer;
          color: var(--color-text);
        }
        .detail-tab.active {
          background: var(--color-surface);
          font-weight: 600;
          color: var(--color-text);
        }
        .detail-tab-panel {
          border: 1px solid var(--color-border);
          border-top: none;
          border-radius: 0 0 12px 12px;
          padding: 16px;
          background: var(--color-surface);
          min-height: 180px;
          display: flex;
          flex-direction: column;
          flex: 1;
          height: 100%;
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
          font-size: 14px;
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
        }
        .flow-step.active .dot {
          background: var(--color-primary);
          color: var(--color-surface);
          box-shadow: 0 0 0 3px rgba(15,118,110,0.15);
        }
        .flow-inline-content {
          border-left: 4px solid var(--color-primary);
          background: var(--color-surface-alt);
          border: 1px solid var(--color-border);
          border-radius: 10px;
          margin: 4px 8px 10px 8px;
          padding: 10px 12px;
          display: flex;
          flex-direction: column;
          flex: 1;
        }
        .flow-subtabs {
          margin: 0 0 8px 0;
          border: 1px solid var(--color-border);
          border-radius: 8px;
          overflow: hidden;
        }
        .flow-subtab {
          flex: 1;
          padding: 10px;
          text-align: center;
          font-size: 13px;
          cursor: pointer;
          color: var(--color-text);
          background: var(--color-surface);
          border: none;
          border-right: 1px solid var(--color-border);
          font: inherit;
        }
        .flow-subtab.active {
          font-weight: 700;
          color: var(--color-primary);
          box-shadow: inset 0 -3px 0 var(--color-primary);
          background: var(--color-primary-soft);
        }
        .flow-subtab:last-child { border-right: none; }
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
        }
        .flow-upload {
          border: 1px dashed var(--color-border-strong);
          border-radius: 12px;
          padding: 18px;
          text-align: center;
          color: var(--color-accent);
          font-size: 13px;
          background: var(--color-surface);
          transition: background 0.15s, border-color 0.15s, color 0.15s;
          font: inherit;
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
      <ProjectsPanel />
      <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: '8px', padding: '8px 4px', marginBottom: '4px', minHeight: '40px' }}>
        <ToolbarMenu />
        {saveStatus === "saving" ? (
          <span className="status" style={{ marginLeft: 8 }}>Saving...</span>
        ) : saveStatus === "saved" ? (
          <span className="status" style={{ marginLeft: 8, color: 'var(--color-success)' }}>Saved</span>
        ) : saveStatus === "error" ? (
          <span className="status" style={{ marginLeft: 8, color: 'var(--color-danger)' }}>{saveError}</span>
        ) : null}
      </div>
      <div
        ref={containerRef}
        style={{ display: 'flex', gap: '0px', flex: 1, minHeight: 0, alignItems: 'stretch' }}
      >
        <div style={{ flex: `${1 - infoRatio} 1 0`, display: 'flex', flexDirection: 'column', gap: '4px', minHeight: 0, minWidth: 0 }}>
          <div className="card" style={{ flex: '4 1 0', minHeight: 0, display: 'flex', flexDirection: 'column' }}>
            <div className="meta" style={{ display: 'none' }}>
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
                          position: 'relative',
                          width: columnWidths[col.key] ? `${columnWidths[col.key]}px` : undefined,
                          minWidth: columnWidths[col.key] ? `${columnWidths[col.key]}px` : undefined
                        }}
                      >
                        <div>{col.label}</div>
                        <input
                          value={filters[col.key]}
                          placeholder="Search..."
                          onChange={(e) => handleFilterChange(col.key, e.target.value)}
                        />
                        <span
                          onMouseDown={(e) => startColResize(e, col.key)}
                          style={{
                            position: 'absolute',
                            top: 0,
                            right: 0,
                            width: '6px',
                            height: '100%',
                            cursor: 'col-resize'
                          }}
                          title="Drag to resize column"
                        />
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
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
                          onClick={() => setSelectedDocId(rowId)}
                          onDoubleClick={() => startEdit(doc)}
                          style={{ background: selectedDocId === rowId ? 'var(--color-row-selected)' : undefined }}
                        >
                          {visibleColumns.map((col) => {
                            const isEditable = col.id === "doc_name" || col.id === "title";
                            const value = renderCell(doc, col);

                            if (isEditing && isEditable) {
                              return (
                                <td
                                  key={col.key}
                                  style={{
                                    width: columnWidths[col.key] ? `${columnWidths[col.key]}px` : undefined,
                                    minWidth: columnWidths[col.key] ? `${columnWidths[col.key]}px` : undefined
                                  }}
                                >
                                  <input
                                    style={{ width: '100%', padding: '6px 8px', borderRadius: '8px', border: '1px solid var(--color-border-strong)' }}
                                    value={col.id === "doc_name" ? editValues.doc_name_unique : editValues.title}
                                    onChange={(e) =>
                                      setEditValues((prev) => ({
                                        ...prev,
                                        [col.id === "doc_name" ? "doc_name_unique" : "title"]: e.target.value,
                                      }))
                                    }
                                  />
                                </td>
                              );
                            }

                            return (
                              <td
                                key={col.key}
                                style={{
                                  width: columnWidths[col.key] ? `${columnWidths[col.key]}px` : undefined,
                                  minWidth: columnWidths[col.key] ? `${columnWidths[col.key]}px` : undefined
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
          <div style={{ 
            flex: '1 1 0',
            background: 'var(--color-surface)', 
            border: '1px solid var(--color-border)', 
            borderRadius: '12px', 
            padding: 0, 
            boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
            minHeight: 0,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
          }}>
            <div className="detail-tabs">
              {["Revisions", "TAGs", "References", "Plan", "Information"].map((tab) => (
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
              {activeDetailTab === "Revisions" ? (
                <div style={{ color: 'var(--color-text-muted)', fontSize: '13px' }}>
                  No revisions yet. A revision will be created automatically when you save a new document.
                </div>
              ) : (
                <div style={{ color: 'var(--color-text-muted)', fontSize: '13px' }}>
                  {activeDetailTab} content will appear here.
                </div>
              )}
            </div>
          </div>
        </div>
        <div
          onMouseDown={startBorderResize}
          style={{
            width: '8px',
            background: isDraggingBorder ? 'var(--color-info)' : 'var(--color-border)',
            cursor: 'col-resize',
            transition: isDraggingBorder ? 'none' : 'background 0.2s',
            userSelect: 'none',
          }}
          title="Drag to resize panels"
        />
        <div style={{ flex: `${infoRatio} 1 0`, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
          <div className="flow-card" style={{ flex: 1 }}>
            <div className="flow-header">DOCUMENT FLOW</div>
            <div className="flow-body">
              {["Official", "Ready for Issue", "IDC", "InDesign", "History"].map((step, idx, arr) => (
                <React.Fragment key={step}>
                  <button
                    type="button"
                    className={`flow-step ${infoActiveStep === step ? "active" : ""}`}
                    aria-expanded={infoActiveStep === step}
                    onClick={() => {
                      if (infoActiveStep === step) {
                        setInfoActiveStep(null);
                        return;
                      }
                      setInfoActiveStep(step);
                      setInfoActiveSubTab("Comments");
                    }}
                  >
                    <span className="dot">⦿</span>
                    <span>{step}</span>
                    {infoActiveStep === step && <span style={{ position: 'absolute', right: 10, color: 'var(--color-text-secondary)' }}>⋮</span>}
                  </button>
                  {infoActiveStep === step && (
                    <div className="flow-inline-content">
                      {step === "IDC" ? (
                        <>
                          <div className="flow-subtabs" style={{ display: 'flex' }}>
                            {["Comments", "Distribution list"].map((tab) => (
                              <div
                                key={tab}
                                className={`flow-subtab ${infoActiveSubTab === tab ? "active" : ""}`}
                                onClick={() => setInfoActiveSubTab(tab)}
                              >
                                {tab}
                              </div>
                            ))}
                          </div>
                          <div className="flow-section">
                            {infoActiveSubTab === "Comments" ? (
                              <>
                                <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
                                  Not document owner or in Distribution list.
                                </div>
                                <div className="flow-box">
                                  <h4>Original Files</h4>
                                  <div style={{ fontSize: '13px', color: 'var(--color-text-subtle)' }}>No original files uploaded yet</div>
                                </div>
                                <div className="flow-box">
                                  <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
                                    {["Files with Comments", "Written Comments"].map((tab) => (
                                      <button
                                        type="button"
                                        key={tab}
                                        className="flow-mini-tab"
                                        style={{
                                          flex: 1,
                                          padding: '8px 10px',
                                          borderBottom: infoActiveSubTab === tab ? '2px solid var(--color-primary)' : '1px solid var(--color-border)',
                                          fontWeight: infoActiveSubTab === tab ? 700 : 500,
                                          color: infoActiveSubTab === tab ? 'var(--color-primary)' : 'var(--color-text)',
                                          cursor: 'pointer',
                                          textAlign: 'center',
                                          background: 'transparent',
                                          border: 'none'
                                        }}
                                        aria-pressed={infoActiveSubTab === tab}
                                        onClick={() => setInfoActiveSubTab(tab)}
                                      >
                                        {tab}
                                      </button>
                                    ))}
                                  </div>
                                  <div style={{ fontSize: '13px', color: 'var(--color-text-subtle)', padding: '12px 0' }}>
                                    No files with comments yet
                                  </div>
                                </div>
                              </>
                            ) : (
                              <div className="flow-box">
                                <h4>Distribution List</h4>
                                <div style={{ fontSize: '13px', color: 'var(--color-text-subtle)' }}>No distribution list assigned</div>
                              </div>
                            )}
                          </div>
                        </>
                      ) : step === "History" ? (
                        <div style={{ fontSize: '13px', color: 'var(--color-text-muted)', padding: '8px 4px' }}>
                          No history available yet.
                        </div>
                      ) : step === "Official" || step === "Ready for Issue" ? (
                        <div style={{ fontSize: '13px', color: 'var(--color-text-muted)', padding: '8px 4px' }}>
                          No documents available yet.
                        </div>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, gap: '8px' }}>
                          {uploadedFiles[step] && uploadedFiles[step].length > 0 ? (
                            <div style={{ flex: 1, overflow: 'auto', padding: '8px 0' }}>
                              {['Rev A', 'Rev B', 'Rev C'].map((revision, revIdx) => {
                                const revFiles = uploadedFiles[step]?.filter(
                                  (f, idx) => idx >= revIdx * 5 && idx < (revIdx + 1) * 5
                                ) || [];
                                
                                if (!revFiles.length && revIdx > 0) return null;
                                
                                const revKey = `${step}-${revision}`;
                                const isExpanded = expandedRevisions[revKey]?.isOpen !== false;
                                
                                return (
                                  <div key={revision} style={{ marginBottom: '4px' }}>
                                    <div
                                      onClick={() => {
                                        setExpandedRevisions(prev => ({
                                          ...prev,
                                          [revKey]: { ...prev[revKey], isOpen: !isExpanded }
                                        }));
                                      }}
                                      style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px',
                                        padding: '6px 8px',
                                        cursor: 'pointer',
                                        color: 'var(--color-text)',
                                        fontSize: '13px',
                                        fontWeight: 600,
                                        userSelect: 'none'
                                      }}
                                    >
                                      <span style={{ fontSize: '12px', width: '16px' }}>
                                        {isExpanded ? '▼' : '▶'}
                                      </span>
                                      <span>{revision}</span>
                                    </div>
                                    {isExpanded && revFiles.map((file, idx) => (
                                      <div
                                        key={`${revision}-${idx}`}
                                        style={{
                                          display: 'flex',
                                          alignItems: 'center',
                                          gap: '6px',
                                          padding: '4px 8px 4px 32px',
                                          color: 'var(--color-accent)',
                                          fontSize: '12px'
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
                                onClick={() => uploadInputRef.current?.click()}
                                style={{
                                  padding: '6px 12px',
                                  background: 'var(--color-accent)',
                                  color: 'var(--color-surface)',
                                  border: 'none',
                                  borderRadius: '6px',
                                  cursor: 'pointer',
                                  fontSize: '12px',
                                  marginTop: '8px',
                                  alignSelf: 'flex-start'
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
                                {...uploadDragProps}
                                onClick={() => uploadInputRef.current?.click()}
                                aria-label="Upload PDF files"
                              >
                                Drag & drop PDF files here<br />or click to browse • Multiple files supported
                              </button>
                            </>
                          )}
                          <input
                            ref={uploadInputRef}
                            type="file"
                            multiple
                            accept="application/pdf"
                            style={{ display: "none" }}
                            onChange={handleUploadSelect}
                          />
                        </div>
                      )}
                    </div>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

export default App;
