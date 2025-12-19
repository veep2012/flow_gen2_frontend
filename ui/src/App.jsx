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

  return (
    <main className="page">
      <style>
        {`
        :root {
          color: #1f2933;
          background: #f5f7fb;
          font-family: "Inter", "SF Pro Display", system-ui, -apple-system, sans-serif;
        }
        * { box-sizing: border-box; }
        body {
          margin: 0;
          background: #f5f7fb;
        }
        .page {
          padding: 24px;
        }
        .toolbar {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 16px;
          color: #52606d;
          font-size: 14px;
        }
        .toolbar select {
          border: 1px solid #d9e2ec;
          border-radius: 8px;
          padding: 8px 10px;
          font-size: 14px;
          color: #1f2933;
          background: #fff;
          min-width: 180px;
        }
        .toolbar .status {
          font-size: 12px;
          color: #c53030;
        }
        .status-row {
          text-align: left;
          padding: 12px;
          color: #52606d;
          font-size: 14px;
          background: #f8fafc;
        }
        .status-row.error {
          color: #c53030;
          background: #fff5f5;
        }
        .progress {
          width: 120px;
          background: #e5e7eb;
          border-radius: 999px;
          height: 20px;
          position: relative;
          overflow: hidden;
          border: 1px solid #e2e8f0;
        }
        .progress__fill {
          position: absolute;
          top: 0;
          left: 0;
          height: 100%;
          background: linear-gradient(90deg, #2f80ed, #4ea1ff);
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
          border: 3px solid #e2e8f0;
          border-top-color: #2f80ed;
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
          background: #fff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          box-shadow:
            0 10px 30px rgba(15, 23, 42, 0.05),
            0 1px 3px rgba(15, 23, 42, 0.08);
          overflow: hidden;
        }
        .table {
          width: 100%;
          border-collapse: collapse;
        }
        .table thead th {
          background: #f8fafc;
          font-weight: 700;
          text-align: left;
          font-size: 14px;
          color: #1f2933;
          padding: 14px 12px 6px;
          border-bottom: 1px solid #e2e8f0;
        }
        .table thead input {
          width: 100%;
          margin-top: 6px;
          padding: 8px 10px;
          border: 1px solid #d9e2ec;
          border-radius: 8px;
          font-size: 13px;
          color: #52606d;
          background: #fff;
        }
        .table tbody tr {
          border-bottom: 1px solid #edf2f7;
        }
        .table tbody tr:last-child {
          border-bottom: none;
        }
        .table td {
          padding: 10px 12px;
          font-size: 14px;
          color: #1f2933;
          line-height: 1.4;
          background: #fff;
        }
        .table tbody tr:hover td {
          background: #f7fafc;
        }
        .meta {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 14px 16px;
          border-bottom: 1px solid #e2e8f0;
        }
        .meta h1 {
          margin: 0;
          font-size: 18px;
          font-weight: 700;
          color: #1f2933;
        }
        .meta .count {
          font-size: 13px;
          color: #52606d;
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
              filteredDocuments.map((doc) => (
                <tr key={doc.doc_id || doc.doc_name || doc.id}>
                  {visibleColumns.map((col) => (
                    <td key={col.key}>{renderCell(doc, col)}</td>
                  ))}
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
