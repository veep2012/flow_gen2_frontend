import React, { useEffect, useState } from "react";
import { documentGridColumns, mapDocumentRow } from "./grids/documents";
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
    setDocuments,
    documentsError,
    documentsLoading,
  } = useFetchDocuments({ apiBase, visibleColumns });
  const [openMenuId, setOpenMenuId] = useState(null);
  const [editRowId, setEditRowId] = useState(null);
  const [editValues, setEditValues] = useState({
    doc_name_unique: "",
    title: "",
    type_id: "",
    discipline_id: "",
    jobpack_id: "",
    area_id: "",
    unit_id: "",
  });
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState("");
  const [lookups, setLookups] = useState({
    docTypes: [],
    disciplines: [],
    jobpacks: [],
    units: [],
    areas: [],
  });
  const [lookupsError, setLookupsError] = useState("");

  useEffect(() => {
    let active = true;
    const fetchList = async (path) => {
      const response = await fetch(`${apiBase}${path}`);
      if (response.status === 404) return [];
      if (!response.ok) {
        throw new Error(`Failed to load ${path} (${response.status})`);
      }
      return response.json();
    };

    Promise.all([
      fetchList("/documents/doc_types"),
      fetchList("/lookups/disciplines"),
      fetchList("/lookups/jobpacks"),
      fetchList("/lookups/units"),
      fetchList("/lookups/areas"),
    ])
      .then(([docTypes, disciplines, jobpacks, units, areas]) => {
        if (!active) return;
        setLookups({ docTypes, disciplines, jobpacks, units, areas });
        setLookupsError("");
      })
      .catch((err) => {
        if (!active) return;
        setLookupsError(err.message || "Failed to load lookup data.");
      });

    return () => {
      active = false;
    };
  }, [apiBase]);

  useEffect(() => {
    const handleClick = () => setOpenMenuId(null);
    window.addEventListener("click", handleClick);
    return () => window.removeEventListener("click", handleClick);
  }, []);

  const toggleMenu = (id) => {
    setOpenMenuId((prev) => (prev === id ? null : id));
  };

  const actionRowId = (doc) =>
    doc.doc_id || doc.doc_name || doc.id || doc.doc_name_unique;

  const startEdit = (doc) => {
    setEditError("");
    setEditRowId(actionRowId(doc));
    setEditValues({
      doc_name_unique: doc.doc_name_unique || "",
      title: doc.title || "",
      type_id: doc.type_id ? String(doc.type_id) : "",
      discipline_id: doc.discipline_id ? String(doc.discipline_id) : "",
      jobpack_id: doc.jobpack_id ? String(doc.jobpack_id) : "",
      area_id: doc.area_id ? String(doc.area_id) : "",
      unit_id: doc.unit_id ? String(doc.unit_id) : "",
    });
    setOpenMenuId(null);
  };

  const cancelEdit = () => {
    setEditError("");
    setEditRowId(null);
    setEditValues({
      doc_name_unique: "",
      title: "",
      type_id: "",
      discipline_id: "",
      jobpack_id: "",
      area_id: "",
      unit_id: "",
    });
  };

  const saveEdit = async (doc) => {
    const payload = { doc_id: doc.doc_id };
    const toInt = (value) => (value === "" || value === null ? null : Number(value));
    const nextTypeId = toInt(editValues.type_id);
    const nextAreaId = toInt(editValues.area_id);
    const nextUnitId = toInt(editValues.unit_id);
    const nextJobpackId = toInt(editValues.jobpack_id);

    if (editValues.doc_name_unique !== doc.doc_name_unique) {
      payload.doc_name_unique = editValues.doc_name_unique.trim();
    }
    if (editValues.title !== doc.title) {
      payload.title = editValues.title.trim();
    }
    if (nextTypeId !== doc.type_id) {
      payload.type_id = nextTypeId;
    }
    if (nextAreaId !== doc.area_id) {
      payload.area_id = nextAreaId;
    }
    if (nextUnitId !== doc.unit_id) {
      payload.unit_id = nextUnitId;
    }
    if (nextJobpackId !== (doc.jobpack_id ?? null)) {
      payload.jobpack_id = nextJobpackId;
    }
    if (Object.keys(payload).length === 1) {
      cancelEdit();
      return;
    }
    if (!payload.doc_name_unique && payload.doc_name_unique !== undefined) {
      setEditError("Name is required.");
      return;
    }
    if (!payload.title && payload.title !== undefined) {
      setEditError("Title is required.");
      return;
    }
    if (payload.type_id === null) {
      setEditError("Type is required.");
      return;
    }
    if (payload.area_id === null) {
      setEditError("Area is required.");
      return;
    }
    if (payload.unit_id === null) {
      setEditError("Unit is required.");
      return;
    }

    setEditSaving(true);
    setEditError("");
    try {
      const response = await fetch(`${apiBase}/documents/update`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        const message =
          detail?.detail || `Failed to update document (${response.status})`;
        throw new Error(message);
      }
      const updated = await response.json();
      setDocuments((prev) =>
        prev.map((row) => {
          if (actionRowId(row) !== actionRowId(doc)) return row;
          const mapped = mapDocumentRow({ ...row, ...updated });
          return mapped;
        }),
      );
      cancelEdit();
    } catch (err) {
      setEditError(err.message || "Failed to update document.");
    } finally {
      setEditSaving(false);
    }
  };

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

  return (
    <main className="page">
      <style>
        {`
        :root {
          color: #1b2a44;
          background: #e3edff;
          font-family: "Inter", "SF Pro Display", system-ui, -apple-system, sans-serif;
        }
        * { box-sizing: border-box; }
        body {
          margin: 0;
          background: #e3edff;
        }
        .page {
          padding: 24px;
        }
        .toolbar {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 16px;
          color: #2f4666;
          font-size: 14px;
        }
        .toolbar select {
          border: 1px solid #b8ccf0;
          border-radius: 8px;
          padding: 8px 10px;
          font-size: 14px;
          color: #1b2a44;
          background: #f1f6ff;
          min-width: 180px;
        }
        .toolbar .status {
          font-size: 12px;
          color: #c53030;
        }
        .status-row {
          text-align: left;
          padding: 12px;
          color: #2f4666;
          font-size: 14px;
          background: #e9f1ff;
        }
        .status-row.error {
          color: #c53030;
          background: #fff5f5;
        }
        .progress {
          width: 120px;
          background: #cfe0ff;
          border-radius: 999px;
          height: 20px;
          position: relative;
          overflow: hidden;
          border: 1px solid #b6ccf3;
        }
        .progress__fill {
          position: absolute;
          top: 0;
          left: 0;
          height: 100%;
          background: linear-gradient(90deg, #1f5ed6, #5a9bff);
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
          color: #fff;
          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.25);
        }
        .spinner {
          width: 22px;
          height: 22px;
          border: 3px solid #c6d8ff;
          border-top-color: #1f5ed6;
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
          background: #f9fbff;
          border: 1px solid #c2d4f6;
          border-radius: 12px;
          box-shadow:
            0 16px 32px rgba(30, 64, 175, 0.12),
            0 4px 10px rgba(30, 64, 175, 0.14);
          overflow: hidden;
        }
        .table {
          width: 100%;
          border-collapse: collapse;
        }
        .table thead th {
          background: #dbe8ff;
          font-weight: 700;
          text-align: left;
          font-size: 14px;
          color: #1b2a44;
          padding: 14px 12px 6px;
          border-bottom: 1px solid #b6ccf3;
        }
        .table thead input {
          width: 100%;
          margin-top: 6px;
          padding: 8px 10px;
          border: 1px solid #b8ccf0;
          border-radius: 8px;
          font-size: 13px;
          color: #2f4666;
          background: #f1f6ff;
        }
        .table tbody tr {
          border-bottom: 1px solid #d2e1ff;
        }
        .table tbody tr:last-child {
          border-bottom: none;
        }
        .table td {
          padding: 10px 12px;
          font-size: 14px;
          color: #1b2a44;
          line-height: 1.4;
          background: #f9fbff;
        }
        .table tbody tr:hover td {
          background: #e7f0ff;
        }
        .actions-cell {
          width: 44px;
          text-align: right;
          position: relative;
        }
        .actions-cell.editing {
          width: 140px;
        }
        .menu-trigger {
          border: none;
          background: transparent;
          width: 32px;
          height: 32px;
          border-radius: 8px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          color: #2f4666;
        }
        .menu-trigger:hover {
          background: #e1ebff;
        }
        .row-menu {
          position: absolute;
          right: 8px;
          top: 42px;
          min-width: 140px;
          background: #f9fbff;
          border: 1px solid #c2d4f6;
          border-radius: 10px;
          box-shadow:
            0 12px 24px rgba(15, 23, 42, 0.12),
            0 2px 6px rgba(15, 23, 42, 0.08);
          padding: 6px;
          z-index: 10;
        }
        .row-menu button {
          width: 100%;
          border: none;
          background: transparent;
          text-align: left;
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 10px;
          border-radius: 8px;
          font-size: 13px;
          color: #1b2a44;
          cursor: pointer;
        }
        .row-menu button:hover {
          background: #e7f0ff;
        }
        .row-menu .danger {
          color: #c53030;
        }
        .inline-input {
          width: 100%;
          padding: 6px 8px;
          border-radius: 8px;
          border: 1px solid #b8ccf0;
          font-size: 13px;
          color: #1b2a44;
          background: #f1f6ff;
        }
        .edit-actions {
          display: inline-flex;
          gap: 8px;
        }
        .edit-actions button {
          border: none;
          background: #1f5ed6;
          color: #fff;
          padding: 6px 10px;
          border-radius: 8px;
          font-size: 12px;
          cursor: pointer;
        }
        .edit-actions button.secondary {
          background: #d7e3ff;
          color: #1b2a44;
        }
        .edit-error {
          margin-top: 6px;
          font-size: 12px;
          color: #c53030;
          text-align: right;
        }
        .lookup-hint {
          margin-left: 8px;
          font-size: 12px;
          color: #c53030;
        }
        .meta {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 14px 16px;
          border-bottom: 1px solid #c2d4f6;
        }
        .meta h1 {
          margin: 0;
          font-size: 18px;
          font-weight: 700;
          color: #1b2a44;
        }
        .meta .count {
          font-size: 13px;
          color: #2f4666;
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
        <div className="toolbar">
          <span>Projects</span>
        <select
          value={project}
          onChange={(e) => setProject(e.target.value)}
          aria-label="Select project"
        >
          <option value="">Project number</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.label}
            </option>
          ))}
        </select>
        {projectsError ? <span className="status">{projectsError}</span> : null}
        {lookupsError ? <span className="lookup-hint">{lookupsError}</span> : null}
      </div>
      <div className="card">
        <div className="meta">
          <h1>Document register</h1>
          <span className="count">{filteredDocuments.length} items</span>
        </div>
        <table className="table">
          <thead>
            <tr>
              {visibleColumns.map((col) => (
                <th key={col.key}>
                  <div>{col.label}</div>
                  <input
                    value={filters[col.key]}
                    placeholder="Search..."
                    onChange={(e) => handleFilterChange(col.key, e.target.value)}
                  />
                </th>
              ))}
              <th className="actions-cell" aria-label="Row actions" />
            </tr>
          </thead>
          <tbody>
            {documentsLoading ? (
              <tr>
                <td className="status-row" colSpan={visibleColumns.length + 1}>
                  <span className="spinner" aria-label="Loading documents" />
                </td>
              </tr>
            ) : documentsError ? (
              <tr>
                <td className="status-row error" colSpan={visibleColumns.length + 1}>
                  {documentsError}
                </td>
              </tr>
            ) : !project ? (
              <tr>
                <td className="status-row" colSpan={visibleColumns.length + 1}>
                  Select a project to load documents.
                </td>
              </tr>
            ) : filteredDocuments.length === 0 ? (
              <tr>
                <td className="status-row" colSpan={visibleColumns.length + 1}>
                  No documents match your filters.
                </td>
              </tr>
            ) : (
              filteredDocuments.map((doc) => (
                <tr key={actionRowId(doc)}>
                  {visibleColumns.map((col) => (
                    <td key={col.key}>
                      {editRowId === actionRowId(doc) &&
                      (col.key === "doc_name" || col.key === "title") ? (
                        <input
                          className="inline-input"
                          value={
                            col.key === "doc_name"
                              ? editValues.doc_name_unique
                              : editValues.title
                          }
                          onChange={(event) => {
                            const value = event.target.value;
                            setEditValues((prev) => ({
                              ...prev,
                              [col.key === "doc_name" ? "doc_name_unique" : "title"]:
                                value,
                            }));
                          }}
                        />
                      ) : editRowId === actionRowId(doc) &&
                        col.key === "doc_type_display" ? (
                        <select
                          className="inline-input"
                          value={editValues.type_id}
                          onChange={(event) => {
                            const value = event.target.value;
                            const match = lookups.docTypes.find(
                              (item) => String(item.type_id) === value,
                            );
                            setEditValues((prev) => ({
                              ...prev,
                              type_id: value,
                              discipline_id: match
                                ? String(match.ref_discipline_id)
                                : prev.discipline_id,
                            }));
                          }}
                        >
                          {lookups.docTypes.map((item) => (
                            <option key={item.type_id} value={String(item.type_id)}>
                              {item.doc_type_name}
                              {item.discipline_acronym ? ` (${item.discipline_acronym})` : ""}
                            </option>
                          ))}
                        </select>
                      ) : editRowId === actionRowId(doc) &&
                        col.key === "discipline_display" ? (
                        <select
                          className="inline-input"
                          value={editValues.discipline_id}
                          onChange={(event) => {
                            const value = event.target.value;
                            const candidate = lookups.docTypes.find(
                              (item) => String(item.ref_discipline_id) === value,
                            );
                            setEditValues((prev) => ({
                              ...prev,
                              discipline_id: value,
                              type_id: candidate ? String(candidate.type_id) : prev.type_id,
                            }));
                          }}
                        >
                          {lookups.disciplines.map((item) => (
                            <option
                              key={item.discipline_id}
                              value={String(item.discipline_id)}
                            >
                              {item.discipline_name}
                              {item.discipline_acronym ? ` (${item.discipline_acronym})` : ""}
                            </option>
                          ))}
                        </select>
                      ) : editRowId === actionRowId(doc) &&
                        col.key === "jobpack_display" ? (
                        <select
                          className="inline-input"
                          value={editValues.jobpack_id}
                          onChange={(event) =>
                            setEditValues((prev) => ({
                              ...prev,
                              jobpack_id: event.target.value,
                            }))
                          }
                        >
                          <option value="">None</option>
                          {lookups.jobpacks.map((item) => (
                            <option key={item.jobpack_id} value={String(item.jobpack_id)}>
                              {item.jobpack_name}
                            </option>
                          ))}
                        </select>
                      ) : editRowId === actionRowId(doc) &&
                        col.key === "area_display" ? (
                        <select
                          className="inline-input"
                          value={editValues.area_id}
                          onChange={(event) =>
                            setEditValues((prev) => ({
                              ...prev,
                              area_id: event.target.value,
                            }))
                          }
                        >
                          {lookups.areas.map((item) => (
                            <option key={item.area_id} value={String(item.area_id)}>
                              {item.area_name}
                              {item.area_acronym ? ` (${item.area_acronym})` : ""}
                            </option>
                          ))}
                        </select>
                      ) : editRowId === actionRowId(doc) &&
                        col.key === "unit_display" ? (
                        <select
                          className="inline-input"
                          value={editValues.unit_id}
                          onChange={(event) =>
                            setEditValues((prev) => ({
                              ...prev,
                              unit_id: event.target.value,
                            }))
                          }
                        >
                          {lookups.units.map((item) => (
                            <option key={item.unit_id} value={String(item.unit_id)}>
                              {item.unit_name}
                            </option>
                          ))}
                        </select>
                      ) : (
                        renderCell(doc, col)
                      )}
                    </td>
                  ))}
                  <td className={`actions-cell${editRowId === actionRowId(doc) ? " editing" : ""}`}>
                    {editRowId === actionRowId(doc) ? (
                      <>
                        <div className="edit-actions">
                          <button
                            type="button"
                            onClick={() => saveEdit(doc)}
                            disabled={editSaving}
                          >
                            Save
                          </button>
                          <button
                            type="button"
                            className="secondary"
                            onClick={cancelEdit}
                            disabled={editSaving}
                          >
                            Cancel
                          </button>
                        </div>
                        {editError ? <div className="edit-error">{editError}</div> : null}
                      </>
                    ) : (
                      <>
                        <button
                          type="button"
                          className="menu-trigger"
                          aria-label="Row actions"
                          onClick={(event) => {
                            event.stopPropagation();
                            toggleMenu(actionRowId(doc));
                          }}
                        >
                          <svg
                            viewBox="0 0 24 24"
                            width="18"
                            height="18"
                            fill="currentColor"
                            aria-hidden="true"
                          >
                            <circle cx="12" cy="5" r="2" />
                            <circle cx="12" cy="12" r="2" />
                            <circle cx="12" cy="19" r="2" />
                          </svg>
                        </button>
                        {openMenuId === actionRowId(doc) ? (
                          <div
                            className="row-menu"
                            role="menu"
                            onClick={(event) => event.stopPropagation()}
                          >
                            <button
                              type="button"
                              role="menuitem"
                              onClick={() => startEdit(doc)}
                            >
                              <svg
                                viewBox="0 0 24 24"
                                width="16"
                                height="16"
                                fill="currentColor"
                                aria-hidden="true"
                              >
                                <path d="M3 17.25V21h3.75L17.8 9.94l-3.75-3.75L3 17.25z" />
                                <path d="M20.7 7.04a1 1 0 0 0 0-1.42l-2.33-2.33a1 1 0 0 0-1.42 0l-1.83 1.83 3.75 3.75 1.83-1.83z" />
                              </svg>
                              Edit
                            </button>
                            <button type="button" role="menuitem" className="danger">
                              <svg
                                viewBox="0 0 24 24"
                                width="16"
                                height="16"
                                fill="currentColor"
                                aria-hidden="true"
                              >
                                <path d="M6 7h12l-1 14H7L6 7zm3-3h6l1 2H8l1-2z" />
                              </svg>
                              Delete
                            </button>
                          </div>
                        ) : null}
                      </>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}

export default App;
