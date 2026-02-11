import React from "react";
import ReactDOM from "react-dom";
import { documentGridColumns } from "./grids/documents";
import { getFileKey } from "./utils/fileKey";
import { normalizeFile } from "./utils/normalizeFile";
import { useFetchDocuments } from "./hooks/useFetchDocuments";
import { resolveBehaviorByFile } from "./components/DocRevStatusBehaviors";
import DetailPanel from "./components/DetailPanel";

const allColumns = documentGridColumns.map(({ id, label, field, hidden }) => ({
  key: field,
  id,
  label,
  hidden: Boolean(hidden),
}));

const appMeta = {
  name: "Flow Gen2",
  version: "v1.0.0",
  revision: "rev 1",
};

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
  const [hiddenColumnIds, setHiddenColumnIds] = React.useState(() => new Set(["doc_id"]));
  const [columnOrder, setColumnOrder] = React.useState(() => allColumns.map((col) => col.id));
  const [dragColumnId, setDragColumnId] = React.useState(null);
  const visibleColumns = React.useMemo(
    () =>
      columnOrder
        .map((id) => allColumns.find((col) => col.id === id))
        .filter(Boolean)
        .filter((col) => !hiddenColumnIds.has(col.id)),
    [hiddenColumnIds, columnOrder],
  );
  React.useEffect(() => {
    if (visibleColumns.length === 0) {
      setHiddenColumnIds(new Set(["doc_id"]));
    }
  }, [visibleColumns.length]);
  const formatDateTime = React.useCallback((value) => {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    const day = String(date.getDate()).padStart(2, "0");
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const year = date.getFullYear();
    const hour = String(date.getHours()).padStart(2, "0");
    const minute = String(date.getMinutes()).padStart(2, "0");
    return `${day}/${month}/${year}, ${hour}:${minute}`;
  }, []);
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
    background: "var(--color-info-dark)",
    color: "var(--color-primary-contrast)",
    border: "1px solid var(--color-info-strong)",
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
    fontSize: "20px",
  };

  const renderFlowIcon = (label) => {
    const key = String(label || "").toLowerCase().trim();
    if (key.includes("official")) {
      return (
        <svg className="dot__icon" viewBox="0 0 18 18" aria-hidden="true">
          <path d="M4.5 9 L7.5 12 L13.5 6" />
        </svg>
      );
    }
    if (key.includes("ready")) {
      return (
        <svg className="dot__icon" viewBox="0 0 18 18" aria-hidden="true">
          <path d="M5 3.5 V14.5" />
          <path d="M5 4 H13 L11 7 L13 10 H5" />
        </svg>
      );
    }
    if (key.includes("idc")) {
      return (
        <svg className="dot__icon" viewBox="0 0 18 18" aria-hidden="true">
          <path d="M5 3.5 H11 L13.5 6 V14.5 H5 Z" />
          <path d="M11 3.5 V6 H13.5" />
        </svg>
      );
    }
    if (key.includes("indesign")) {
      return (
        <svg className="dot__icon" viewBox="0 0 18 18" aria-hidden="true">
          <path d="M4.5 13.5 L7.5 13 L13.5 7 L11 4.5 L5 10.5 Z" />
          <path d="M10.5 5 L13 7.5" />
        </svg>
      );
    }
    if (key.includes("history")) {
      return (
        <svg className="dot__icon" viewBox="0 0 18 18" aria-hidden="true">
          <path d="M9 4.5 A4.5 4.5 0 1 1 4.5 9" />
          <path d="M4.5 4.5 V9 H9" />
        </svg>
      );
    }
    return (
      <svg className="dot__icon" viewBox="0 0 18 18" aria-hidden="true">
        <path d="M6 7.5 L9 10.5 L12 7.5" />
      </svg>
    );
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
  const [isFlowPanelHidden, setIsFlowPanelHidden] = React.useState(false);
  const containerRef = React.useRef(null);
  const leftPanelRef = React.useRef(null);
  const hasInitializedFlowRef = React.useRef(false);
  const uploadInputRef = React.useRef(null);
  const tableWrapperRef = React.useRef(null);
  const [selectedDocId, setSelectedDocId] = React.useState(null);
  const [selectedDocIds, setSelectedDocIds] = React.useState(new Set());
  const [lastSelectedRowIndex, setLastSelectedRowIndex] = React.useState(null);
  const [copiedDocIds, setCopiedDocIds] = React.useState(new Set());
  const [copyMode, setCopyMode] = React.useState(false);
  const [copiedRows, setCopiedRows] = React.useState([]);
  const [lastCreatedDocIds, setLastCreatedDocIds] = React.useState(new Set());
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

  React.useEffect(() => {
    if (!lastCreatedDocIds.size) return undefined;
    const timeoutId = window.setTimeout(() => {
      setLastCreatedDocIds(new Set());
    }, 10000);
    return () => window.clearTimeout(timeoutId);
  }, [lastCreatedDocIds]);

  React.useEffect(() => {
    hasInitializedFlowRef.current = false;
    setInfoActiveStep(null);
    setInfoActiveSubTab("Files with Comments");
  }, [selectedDocId]);

  React.useEffect(() => {
    if (!lastCreatedDocIds.size) return undefined;
    const ids = Array.from(lastCreatedDocIds);
    let attempts = 0;
    let rafId = 0;

    const tryScroll = () => {
      if (!tableWrapperRef.current) return;
      const targetId = ids.find((id) =>
        tableWrapperRef.current.querySelector(`[data-row-id="${id}"]`),
      );
      if (targetId) {
        const row = tableWrapperRef.current.querySelector(`[data-row-id="${targetId}"]`);
        if (row) {
          row.scrollIntoView({ block: "nearest" });
          return;
        }
      }
      attempts += 1;
      if (attempts < 10) {
        rafId = window.requestAnimationFrame(tryScroll);
      }
    };

    rafId = window.requestAnimationFrame(tryScroll);
    return () => window.cancelAnimationFrame(rafId);
  }, [lastCreatedDocIds]);
  const [pastedRows, setPastedRows] = React.useState([]);
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
  const [revCodeOptions, setRevCodeOptions] = React.useState([]);
  // Fetch revisions for selected document
  React.useEffect(() => {
    const fetchRevisions = async () => {
      if (!selectedDocId) {
        setRevisionOverviews([]);
        return;
      }
      try {
        const res = await fetch(`${apiBase}/documents/${selectedDocId}/revisions`);
        if (!res.ok) throw new Error('Failed to fetch revisions');
        const data = await res.json();
        setRevisionOverviews(Array.isArray(data) ? data : []);
      } catch (err) {
        setRevisionOverviews([]);
      }
    };
    fetchRevisions();
  }, [apiBase, selectedDocId]);
  const [people, setPeople] = React.useState([]);
  // Selected revision row in Revisions tab
  const [selectedRevisionIdx, setSelectedRevisionIdx] = React.useState(null);
  const [sortConfig, setSortConfig] = React.useState({ key: null, direction: null });
  const [columnMenuOpen, setColumnMenuOpen] = React.useState(null);
  const [columnMenuPosition, setColumnMenuPosition] = React.useState({ top: 0, left: 0 });
  const [columnSubmenuOpen, setColumnSubmenuOpen] = React.useState(false);

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

  React.useEffect(() => {
    const handleClickAway = (event) => {
      if (!event.target.closest("[data-column-menu]")) {
        setColumnMenuOpen(null);
      }
    };
    document.addEventListener("mousedown", handleClickAway);
    return () => document.removeEventListener("mousedown", handleClickAway);
  }, []);


  const toggleColumnVisibility = React.useCallback((columnId) => {
    setHiddenColumnIds((prev) => {
      const next = new Set(prev);
      if (next.has(columnId)) {
        next.delete(columnId);
      } else {
        const nonIdColumns = allColumns.filter((col) => col.id !== "doc_id");
        const visibleCount = nonIdColumns.filter((col) => !next.has(col.id)).length;
        if (visibleCount > 1) {
          next.add(columnId);
        }
      }
      return next;
    });
  }, []);


  const handleColumnDragStart = React.useCallback((event, columnId) => {
    setDragColumnId(columnId);
    event.dataTransfer.effectAllowed = "move";
  }, []);

  const handleColumnDragOver = React.useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const handleColumnDrop = React.useCallback(
    (event, targetId) => {
      event.preventDefault();
      if (!dragColumnId || dragColumnId === targetId) return;
      setColumnOrder((prev) => {
        const next = [...prev];
        const fromIndex = next.indexOf(dragColumnId);
        const toIndex = next.indexOf(targetId);
        if (fromIndex === -1 || toIndex === -1) return prev;
        next.splice(fromIndex, 1);
        next.splice(toIndex, 0, dragColumnId);
        return next;
      });
      setDragColumnId(null);
    },
    [dragColumnId],
  );

  const toggleColumnMenu = React.useCallback((event, key) => {
    event?.stopPropagation();
    if (event?.currentTarget) {
      const rect = event.currentTarget.getBoundingClientRect();
      setColumnMenuPosition({
        top: rect.top + window.scrollY - 2,
        left: rect.right + window.scrollX + 6,
      });
    }
    setColumnSubmenuOpen(false);
    setColumnMenuOpen((prev) => (prev === key ? null : key));
  }, []);

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

  const sortedDocuments = React.useMemo(() => {
    if (!sortConfig.key || !sortConfig.direction) return filteredDocuments;
    const sortColumn = visibleColumns.find((col) => col.key === sortConfig.key);
    const getSortValue = (doc) => {
      if (!sortColumn) return doc[sortConfig.key];
      if (sortColumn.id === "rev_percent") {
        const raw =
          Number.isFinite(doc.percentage) && doc.percentage >= 0
            ? doc.percentage
            : Number.parseFloat(doc.rev_percent_display);
        return Number.isFinite(raw) ? raw : null;
      }
      return doc[sortConfig.key];
    };
    const sorted = [...filteredDocuments].sort((a, b) => {
      const aValue = getSortValue(a);
      const bValue = getSortValue(b);
      if (aValue == null && bValue == null) return 0;
      if (aValue == null) return 1;
      if (bValue == null) return -1;
      const aNumber = typeof aValue === "number" ? aValue : Number(aValue);
      const bNumber = typeof bValue === "number" ? bValue : Number(bValue);
      if (Number.isFinite(aNumber) && Number.isFinite(bNumber)) {
        return aNumber - bNumber;
      }
      return String(aValue).localeCompare(String(bValue), undefined, { numeric: true });
    });
    return sortConfig.direction === "asc" ? sorted : sorted.reverse();
  }, [filteredDocuments, sortConfig, visibleColumns]);

  const newDocTypeOptions = React.useMemo(() => {
    if (!newDocValues.discipline_id) return docTypes;
    return docTypes.filter(
      (item) => String(item.ref_discipline_id ?? "") === String(newDocValues.discipline_id),
    );
  }, [docTypes, newDocValues.discipline_id]);

  const handleDeleteDocument = React.useCallback(async () => {
    const idsToDelete =
      selectedDocIds.size > 0
        ? Array.from(selectedDocIds)
        : selectedDoc
          ? [selectedDoc.doc_id ?? selectedDoc.id]
          : [];
    const cleanedIds = idsToDelete.filter(Boolean);
    if (cleanedIds.length === 0) {
      setSaveStatus("error");
      setSaveError("Select a row to delete");
      return;
    }

    if (
      !window.confirm(
        cleanedIds.length === 1
          ? "Delete selected document?"
          : `Delete ${cleanedIds.length} selected documents?`,
      )
    ) {
      return;
    }

    setSaveStatus("saving");
    setSaveError(null);
    try {
      await Promise.all(
        cleanedIds.map(async (docId) => {
          const res = await fetch(`${apiBase}/documents/${docId}`, { method: "DELETE" });
          if (!res.ok) {
            const errorText = await res.text();
            throw new Error(errorText || `Delete failed (${res.status})`);
          }
          await res.json().catch(() => null);
        }),
      );
      setSaveStatus("idle");
      setSelectedDocId(null);
      setSelectedDocIds(new Set());
      setEditRowId(null);
      reloadDocuments();
    } catch (err) {
      setSaveStatus("error");
      setSaveError(err.message || "Unknown error while deleting");
    }
  }, [apiBase, reloadDocuments, selectedDoc, selectedDocIds]);

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
    const buildEmptyPasteRow = () => {
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
      return {
        doc_name_unique: "",
        title: "",
        discipline_id: String(fallbackDisciplineFromType || ""),
        type_id: String(fallbackTypeId || ""),
        jobpack_id: String(selectedDoc?.jobpack_id ?? ""),
        area_id: String(selectedDoc?.area_id ?? areas[0]?.area_id ?? ""),
        unit_id: String(selectedDoc?.unit_id ?? units[0]?.unit_id ?? ""),
        rev_code_id: String(revCodeOptions[0]?.rev_code_id ?? ""),
      };
    };
    const handleAddRows = (count = 3) => {
      if (!project) return;
      setCreateError(null);
      setCreateStatus("idle");
      setCopyMode(false);
      setCopiedDocIds(new Set());
      setCopiedRows([]);
      setIsAdding(false);
      setEditRowId(null);
      const nextRows = Array.from({ length: count }, () => buildEmptyPasteRow());
      setPastedRows((prev) => [...prev, ...nextRows]);
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
    const handleCopy = async () => {
      const selectedRows = sortedDocuments.filter((doc) =>
        selectedDocIds.has(doc.doc_id || doc.doc_name || doc.id),
      );
      if (!selectedRows.length) return;
      setCopiedDocIds(new Set(selectedRows.map((doc) => doc.doc_id || doc.doc_name || doc.id)));
      setCopiedRows(selectedRows);
      setCopyMode(true);
      const headers = visibleColumns.map((col) => col.label);
      const rows = selectedRows.map((doc) =>
        visibleColumns.map((col) => {
          if (col.id === "rev_percent") {
            return doc.rev_percent_display ?? doc.percentage ?? "";
          }
          return doc[col.key] ?? "";
        }),
      );
      const tsv = [headers.join("\t"), ...rows.map((row) => row.join("\t"))].join("\n");
      await navigator.clipboard.writeText(tsv);
    };
    const handleCancelCopy = () => {
      setCopiedDocIds(new Set());
      setCopiedRows([]);
      setCopyMode(false);
    };
    const handlePaste = () => {
      if (!copiedRows.length) return;
      const nextRows = copiedRows.map((doc, index) => {
        const baseName = doc.doc_name_unique || doc.doc_name || "";
        const baseTitle = doc.title || "";
        return {
          doc_name_unique: baseName ? `${baseName}-copy-${index + 1}` : "",
          title: baseTitle,
          discipline_id: String(doc.discipline_id ?? ""),
          type_id: String(doc.type_id ?? ""),
          jobpack_id: String(doc.jobpack_id ?? ""),
          area_id: String(doc.area_id ?? ""),
          unit_id: String(doc.unit_id ?? ""),
          rev_code_id: String(doc.rev_code_id ?? revCodeOptions[0]?.rev_code_id ?? ""),
        };
      });
      setPastedRows(nextRows);
      setCopyMode(false);
      setCopiedDocIds(new Set());
      setIsAdding(false);
      setEditRowId(null);
    };
    const handleCancelPaste = () => {
      setPastedRows([]);
      setCreateError(null);
      setCreateStatus("idle");
    };
    const handleSavePastedRows = async () => {
      if (!project) return;
      if (!pastedRows.length) return;
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
      const revCodeIdFallback = toLookupId(revCodeOptions[0]?.rev_code_id);
      const personId = toLookupId(people[0]?.person_id);

      const invalid = pastedRows.find(
        (row) =>
          !String(row.doc_name_unique || "").trim() ||
          !String(row.title || "").trim() ||
          !row.type_id ||
          !row.area_id ||
          !row.unit_id,
      );
      if (invalid) {
        setCreateStatus("error");
        setCreateError("Please заполните обязательные поля для всех строк.");
        return;
      }

      setCreateStatus("saving");
      setCreateError(null);
      try {
        const createdDocs = await Promise.all(
          pastedRows.map(async (row) => {
            const payload = {
              doc_name_unique: String(row.doc_name_unique || "").trim(),
              title: String(row.title || "").trim(),
              project_id: Number(project),
              type_id: toLookupId(row.type_id),
              area_id: toLookupId(row.area_id),
              unit_id: toLookupId(row.unit_id),
              rev_code_id: toLookupId(row.rev_code_id) || revCodeIdFallback,
              rev_author_id: personId,
              rev_originator_id: personId,
              rev_modifier_id: personId,
              transmital_current_revision: "TR-001",
              planned_start_date: toDateTime(startDate),
              planned_finish_date: toDateTime(finishDate),
            };
            const jobpackId = toLookupId(row.jobpack_id);
            if (jobpackId) payload.jobpack_id = jobpackId;
            const res = await fetch(`${apiBase}/documents`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload),
            });
            if (!res.ok) {
              const errorText = await res.text();
              throw new Error(errorText || `Create failed (${res.status})`);
            }
            return await res.json().catch(() => null);
          }),
        );
        setCreateStatus("saved");
        setPastedRows([]);
        const createdIds = createdDocs
          .map((doc) => doc?.doc_id || doc?.id || doc?.doc_name || null)
          .filter(Boolean);
        setLastCreatedDocIds(new Set(createdIds));
        reloadDocuments();
      } catch (err) {
        setCreateStatus("error");
        setCreateError(err.message || "Paste failed");
      }
    };
    const handleExport = () => {
      if (!project) {
        alert("Select a project to export documents.");
        return;
      }
      if (!sortedDocuments.length) {
        alert("No documents to export.");
        return;
      }
      const escapeCsv = (value) => {
        const stringValue = String(value ?? "");
        if (/[",\n]/.test(stringValue)) {
          return `"${stringValue.replace(/"/g, '""')}"`;
        }
        return stringValue;
      };
      const headers = visibleColumns.map((col) => escapeCsv(col.label));
      const rows = sortedDocuments.map((doc) =>
        visibleColumns.map((col) => {
          if (col.id === "rev_percent") {
            return escapeCsv(doc.rev_percent_display ?? doc.percentage ?? "");
          }
          return escapeCsv(doc[col.key] ?? "");
        }),
      );
      const csv = [headers.join(","), ...rows.map((row) => row.join(","))].join("\n");
      const blob = new Blob([`\ufeff${csv}`], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      const safeProject = String(project || "documents").replace(/[^\w.-]+/g, "_");
      link.download = `documents_${safeProject}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    };
    const handleUndo = () => {};
    const handleRedo = () => {};
    const hasSelection = selectedDocIds.size > 0;
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
            aria-label={editRowId ? "Save changes" : "Create document"}
          >
            <span style={iconStyle}>💾</span>
            <span style={{ marginLeft: "6px" }}>{editRowId ? "Save" : "Create"}</span>
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
            aria-label="Cancel"
          >
            <span style={iconStyle}>✕</span>
            <span style={{ marginLeft: "6px" }}>Cancel</span>
          </button>
        </div>
      );
    }

    if (copyMode) {
      return (
        <div style={{ display: "flex", gap: "4px", alignItems: "center", padding: "0 6px" }}>
          <button
            style={!hasProject ? { ...buttonStyle, ...disabledButtonStyle } : buttonStyle}
            title="Paste rows"
            onClick={handlePaste}
            disabled={!hasProject}
            aria-label="Paste rows"
          >
            <span style={iconStyle}>📋</span>
            <span style={{ marginLeft: "6px" }}>Paste</span>
          </button>
          <button
            style={buttonStyle}
            title="Cancel copy"
            onClick={handleCancelCopy}
            aria-label="Cancel copy"
          >
            <span style={iconStyle}>✕</span>
            <span style={{ marginLeft: "6px" }}>Cancel</span>
          </button>
        </div>
      );
    }
    if (pastedRows.length > 0) {
      return (
        <div style={{ display: "flex", gap: "4px", alignItems: "center", padding: "0 6px" }}>
          <button
            style={buttonStyle}
            title="Save pasted rows"
            onClick={handleSavePastedRows}
            aria-label="Save pasted rows"
          >
            <span style={iconStyle}>💾</span>
            <span style={{ marginLeft: "6px" }}>Save</span>
          </button>
          <button
            style={buttonStyle}
            title="Cancel paste"
            onClick={handleCancelPaste}
            aria-label="Cancel paste"
          >
            <span style={iconStyle}>✕</span>
            <span style={{ marginLeft: "6px" }}>Cancel</span>
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
          aria-label="Add new document"
        >
          <span style={iconStyle}>+</span>
          <span style={{ marginLeft: "6px" }}>Add</span>
        </button>
        <button
          style={!hasSelection ? { ...buttonStyle, ...disabledButtonStyle } : buttonStyle}
          title="Edit selected document"
          onClick={handleEdit}
          disabled={!hasSelection}
          aria-label="Edit selected document"
        >
          <span style={iconStyle}>✎</span>
          <span style={{ marginLeft: "6px" }}>Edit</span>
        </button>
        <button
          style={!hasSelection ? { ...buttonStyle, ...disabledButtonStyle } : buttonStyle}
          title="Delete selected document"
          onClick={handleDelete}
          disabled={!hasSelection}
          aria-label="Delete selected document"
        >
          <span style={iconStyle}>🗑</span>
          <span style={{ marginLeft: "6px" }}>Delete</span>
        </button>
        <button
          style={!hasSelection ? { ...buttonStyle, ...disabledButtonStyle } : buttonStyle}
          title="Copy selected rows"
          onClick={handleCopy}
          disabled={!hasSelection}
          aria-label="Copy selected rows"
        >
          <span style={iconStyle}>⧉</span>
          <span style={{ marginLeft: "6px" }}>Copy</span>
        </button>
        <button
          style={!hasProject ? { ...buttonStyle, ...disabledButtonStyle } : buttonStyle}
          title="Export documents"
          onClick={handleExport}
          disabled={!hasProject}
          aria-label="Export documents"
        >
          <span style={iconStyle}>⬇</span>
          <span style={{ marginLeft: "6px" }}>Export</span>
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
    if (!revCodeOptions.length) missing.push("Revision code");
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
    const revCodeId = toLookupId(revCodeOptions[0]?.rev_code_id);
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
      setLastCreatedDocIds(
        new Set([created?.doc_id ?? created?.id ?? created?.doc_name].filter(Boolean)),
      );
      reloadDocuments();
      setNewDocValues((prev) => ({
        ...prev,
        doc_name_unique: "",
        title: "",
      }));
    } catch (err) {
      setCreateStatus("error");
      setCreateError(err.message || "Unknown error while creating document");
    }
  }, [apiBase, newDocValues, people, project, reloadDocuments, revCodeOptions]);

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
        const response = await fetch(`${apiBase}/files?rev_id=${revisionId}`);
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
            const existingFiles = prev[selectedDocId] && typeof prev[selectedDocId] === 'object' && !Array.isArray(prev[selectedDocId])
              ? prev[selectedDocId]
              : {};
            // Ensure all statusKey values are arrays (except $api)
            const safeFiles = {};
            Object.entries(existingFiles).forEach(([key, value]) => {
              if (key === '$api') {
                safeFiles[key] = value;
              } else {
                safeFiles[key] = Array.isArray(value) ? value : [];
              }
            });
            return {
              ...prev,
              [selectedDocId]: {
                ...safeFiles,
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
        setRevCodeOptions((await readJson(revisionOverviewsRes)) || []);
        setPeople((await readJson(peopleRes)) || []);
      } catch (err) {
        if (!isActive) return;
        console.error("Failed to load lookup data:", err);
        setDocTypes([]);
        setDisciplines([]);
        setJobpacks([]);
        setAreas([]);
        setUnits([]);
        setRevCodeOptions([]);
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
          --color-bg: #f5f6f8;
          --color-surface: #ffffff;
          --color-surface-alt: #f7f8fa;
          --color-surface-muted: #f2f4f7;
          --color-surface-muted-strong: #e4e7eb;
          --color-surface-subtle: #fafbfc;
          --color-border: #d5d9de;
          --color-border-soft: #c9ccd1;
          --color-border-strong: #bfc4ca;
          --color-text: #2f3033;
          --color-text-muted: #6b6f76;
          --color-text-subtle: #8b9096;
          --color-text-strong: #1f2428;
          --color-text-secondary: #4a4f55;
          --color-primary: #2f5fa6;
          --color-primary-contrast: #ffffff;
          --color-primary-soft: #e6eef9;
          --color-primary-outline: rgba(47, 95, 166, 0.18);
          --color-accent: #2f5fa6;
          --color-accent-contrast: #ffffff;
          --color-info: #2f5fa6;
          --color-info-dark: #244c86;
          --color-info-strong: #1f4173;
          --color-info-soft: #e6eef9;
          --color-warning: #b76a00;
          --color-danger: #c62828;
          --color-danger-soft: #fdeeee;
          --color-success: #2e7d32;
          --color-success-dark: #276a2b;
          --color-success-soft: #e9f5ec;
          --color-success-border: #bcdcc3;
          --color-success-border-strong: #9ccaa7;
          --color-success-text: #2e5b34;
          --color-row-selected: #e8f0fe;
          --color-focus: #2f5fa6;
          --color-error: #c62828;
          --color-error-dark: #a31f1f;
          --color-spinner-start: #2f5fa6;
          --color-spinner-end: #3b6fb8;
          color: var(--color-text);
          background: var(--color-bg);
          font-family: "Inter", "SF Pro Display", system-ui, -apple-system, sans-serif;
        }
        * { box-sizing: border-box; }
        body {
          margin: 0;
          background: var(--color-bg);
        }
        button,
        input,
        select,
        textarea {
          font-family: inherit;
        }
        input,
        select,
        textarea {
          border: 1px solid var(--color-border-soft);
          border-radius: 0;
          padding: 6px 8px;
          font-size: 13px;
          color: var(--color-text);
          background: var(--color-surface);
        }
        input,
        select,
        textarea,
        button {
          border-radius: 0 !important;
        }
        input:focus,
        select:focus,
        textarea:focus {
          outline: none;
          border-color: var(--color-focus);
          box-shadow: 0 0 0 2px var(--color-primary-outline);
        }
        button {
          border: 1px solid var(--color-border-soft);
          border-radius: 0;
          padding: 6px 10px;
          font-size: 13px;
          color: var(--color-text);
          background: var(--color-surface-alt);
          cursor: pointer;
          transition: background 0.15s ease, border-color 0.15s ease;
        }
        button:hover {
          background: var(--color-surface-muted);
          border-color: var(--color-border);
        }
        button:active {
          background: var(--color-surface-muted-strong);
        }
        button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
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
        .app-header {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 6px 10px;
          margin: 8px 0 0;
          border-top: 1px solid var(--color-border);
          background: var(--color-surface);
          color: var(--color-text);
          font-size: 13px;
          flex-shrink: 0;
        }
        .app-header__name {
          font-weight: 600;
        }
        .app-header__meta {
          color: var(--color-text-muted);
        }
        .toolbar select {
          border: 1px solid var(--color-border-soft);
          border-radius: 4px;
          padding: 6px 8px;
          font-size: 13px;
          color: var(--color-text);
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
          border-bottom: 1px solid var(--color-border);
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
          border-radius: 0;
          box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
          overflow: hidden;
        }
        .table {
          width: 100%;
          border-collapse: separate;
          border-spacing: 0;
          white-space: nowrap;
          margin: 0 !important;
          padding: 0 !important;
          color: var(--color-text);
          font-size: 13px;
          table-layout: auto;
        }
        .table thead th {
          background: #f5f6f8;
          font-weight: 600;
          text-align: left;
          font-size: 13px;
          color: #2f3033;
          padding: 6px 10px;
          border-bottom: 1px solid #d5d9de;
          border-right: 1px solid #d5d9de;
          white-space: nowrap;
          vertical-align: middle;
          position: sticky;
          top: 0;
          z-index: 2;
        }
        .table thead th:first-child {
          border-left: 1px solid #d5d9de;
        }
        .table thead th input {
          width: 100%;
          margin-top: 6px;
          padding: 6px 8px;
          border: 1px solid #c9ccd1;
          border-radius: 4px;
          font-size: 12px;
          color: #3a3b3f;
          background: #ffffff;
          line-height: 1.4;
        }
        .table td {
          padding: 6px 10px;
          border-bottom: 1px solid #e1e4e8;
          border-right: 1px solid #e1e4e8;
          position: relative;
          font-size: 13px;
          color: #1f2428;
          line-height: 1.4;
          background: #ffffff;
        }
        .table td:first-child {
          border-left: 1px solid #e1e4e8;
        }
        .table tbody tr:nth-child(even) td {
          background: #fafbfc;
        }
        .table tbody tr:hover td {
          background: #eef2f6;
        }
        .table tbody tr.selected td {
          background: #f4f7fd;
        }
        .table tbody tr.selected td:first-child {
          box-shadow: inset 2px 0 0 var(--color-accent);
        }
        .table tbody tr.copied td {
          box-shadow: inset 0 0 0 2px var(--color-accent);
        }
        .table tbody tr.created td {
          background: #e7f4ff;
          box-shadow: inset 0 0 0 1px var(--color-accent);
        }
        .table tbody tr.editing td {
          background: #fff7d6;
          box-shadow: inset 0 0 0 1px var(--color-accent);
        }
        .table tbody tr.editing td:first-child {
          box-shadow: inset 2px 0 0 var(--color-accent), inset 0 0 0 1px var(--color-accent);
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
          margin: 0 !important;
          padding: 0 !important;
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
          border-radius: 0;
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
          background: #f5f6f8;
          padding: 0;
        }
        .detail-tab {
          padding: 6px 12px;
          border: 1px solid var(--color-border);
          border-bottom: none;
          border-radius: 0;
          background: #f5f6f8;
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
          background: #e9ecef;
        }
        .detail-tab.active {
          background: #e0e3e7;
          color: var(--color-text);
          border-color: #d5d9de;
          box-shadow: none;
        }
        .detail-tab-panel {
          border: 1px solid var(--color-border);
          border-top: none;
          border-radius: 0;
          padding: 0 !important;
          margin: 0 !important;
          background: var(--color-surface);
          display: flex;
          flex-direction: column;
          flex: 1;
        }
        .idc-subtabs {
          display: flex;
          gap: 2px;
          border-bottom: 1px solid var(--color-border);
          background: #f5f6f8;
          padding: 0;
        }
        .idc-tab-panel {
          border: none;
          padding: 0 !important;
          margin: 0 !important;
          background: transparent;
          display: flex;
          flex-direction: column;
          flex: 1;
        }
        .flow-card {
          background: var(--color-surface-alt);
          border: 1px solid var(--color-border);
          border-radius: 0;
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
          flex-direction: row;
          flex: 1;
          min-height: 0;
        }
        .flow-steps-column {
          width: 40px;
          border-right: 1px solid var(--color-border);
          display: flex;
          flex-direction: column;
          padding: 4px;
          background: var(--color-surface);
          height: 100%;
        }
        .flow-steps-column .flow-step {
          padding: 4px 2px;
          height: auto;
          justify-content: center;
          border-radius: 0;
          flex: 1 1 0;
          display: flex;
          align-items: center;
        }
        .flow-steps-column .flow-step.active {
          flex: 1 1 0;
          align-items: center;
          justify-content: center;
          padding-top: 0;
          flex-direction: column;
          height: auto;
          background: #e0f0e3;
          border-color: var(--color-success-border-strong);
        }
        .flow-steps-column .flow-step__label,
        .flow-steps-column .flow-step__behavior {
          display: none;
        }
        .flow-content-column {
          flex: 1;
          display: flex;
          flex-direction: column;
          min-width: 0;
          position: relative;
        }
        .flow-content-header {
          padding: 8px 12px;
          height: 32px;
          border-bottom: 1px solid var(--color-border);
          text-align: center;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 14px;
          font-weight: 600;
          color: var(--color-text-strong);
          background: var(--color-surface);
          text-transform: uppercase;
          letter-spacing: 0.5px;
          position: relative;
          padding-right: 36px;
        }
        .flow-header-menu {
          position: absolute;
          right: 0;
          top: 50%;
          transform: translateY(-50%);
          background: transparent;
          border: none;
          cursor: pointer;
          padding: 4px 0;
          font-size: 20px;
          color: var(--color-text-muted);
          transition: color 0.2s;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
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
          border: 1px solid var(--color-border);
          border-bottom: 1px solid var(--color-border);
          width: 100%;
          text-align: left;
          font: inherit;
        }
        .flow-steps-column .flow-step {
          border: 1px solid var(--color-border);
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
          border: 2px solid var(--color-text-muted);
          background: var(--color-surface);
          display: inline-flex;
          align-items: center;
          justify-content: center;
          font-size: 10px;
          color: var(--color-text-muted);
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
          border-color: var(--color-primary);
        }
        .flow-steps-column .flow-step.active .dot {
          border-color: #ffffff;
        }
        .flow-inline-content {
          border-left: none;
          background: var(--color-surface-alt);
          border: none;
          border-radius: 4px;
          margin: 0;
          padding: 0;
          display: flex;
          flex-direction: column;
          flex: 1;
          min-height: 0;
          max-height: 100%;
          overflow: hidden;
        }
        .flow-inline-content * {
          border-radius: 0 !important;
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
          borderRadius: "6px",
          padding: "8px 4px",
          marginBottom: "4px",
          minHeight: "40px",
          boxShadow: "0 1px 2px rgba(15, 23, 42, 0.08)",
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
            flex: isFlowPanelHidden ? "1 1 0" : `${1 - infoRatio} 1 0`,
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
              overflow: "visible",
            }}
          >
            <div className="meta" style={{ display: "none" }}>
              {/* Document register header hidden */}
            </div>
            <div
              className="table-wrapper"
              ref={tableWrapperRef}
              style={{ flex: 1, minHeight: 0, overflow: "auto" }}
            >
              <table className="table">
                <thead>
                  <tr>
                    {visibleColumns.map((col) => {
                      return (
                        <th
                          key={col.key}
                          draggable
                          onDragStart={(event) => handleColumnDragStart(event, col.id)}
                          onDragOver={handleColumnDragOver}
                          onDrop={(event) => handleColumnDrop(event, col.id)}
                          style={{
                            position: "sticky",
                            top: 0,
                            zIndex: 3,
                            width: columnWidths[col.key] ? `${columnWidths[col.key]}px` : undefined,
                            minWidth: columnWidths[col.key]
                              ? `${columnWidths[col.key]}px`
                              : undefined,
                          }}
                        >
                          <div
                            style={{
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "space-between",
                              gap: "6px",
                            }}
                          >
                            <span>{col.label}</span>
                            <div
                              data-column-menu
                              style={{ position: "relative", display: "inline-flex" }}
                            >
                              <button
                                type="button"
                                title={`${col.label} column menu`}
                                aria-label={`${col.label} column menu`}
                                onClick={(event) => toggleColumnMenu(event, col.key)}
                                style={{
                                  border: "none",
                                  background: "transparent",
                                  padding: "0 2px",
                                  lineHeight: 1,
                                  cursor: "pointer",
                                  color: "var(--color-text-muted)",
                                  fontSize: "14px",
                                  display: "inline-flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                }}
                              >
                                ⋮
                              </button>
                              {columnMenuOpen === col.key
                                ? ReactDOM.createPortal(
                                  <div
                                    data-column-menu
                                    onClick={(event) => event.stopPropagation()}
                                    onMouseDown={(event) => event.stopPropagation()}
                                    style={{
                                      position: "fixed",
                                      top: columnMenuPosition.top,
                                      left: columnMenuPosition.left,
                                      background: "var(--color-surface)",
                                      border: "1px solid var(--color-border)",
                                      borderRadius: "0",
                                      boxShadow: "0 6px 14px rgba(0,0,0,0.12)",
                                      zIndex: 5000,
                                      minWidth: "220px",
                                      overflow: "visible",
                                    }}
                                  >
                                  <button
                                    type="button"
                                    onClick={() => {
                                      setSortConfig({ key: col.key, direction: "asc" });
                                      setColumnMenuOpen(null);
                                    }}
                                    onMouseEnter={(event) => {
                                      event.currentTarget.style.background = "var(--color-surface-muted)";
                                    }}
                                    onMouseLeave={(event) => {
                                      event.currentTarget.style.background = "transparent";
                                    }}
                                    style={{
                                      width: "100%",
                                      padding: "8px 12px",
                                      textAlign: "left",
                                      background: "transparent",
                                      border: "none",
                                      cursor: "pointer",
                                      fontSize: "12px",
                                      color: "var(--color-text)",
                                      display: "flex",
                                      alignItems: "center",
                                      gap: "8px",
                                    }}
                                  >
                                    <span style={{ fontSize: "12px" }}>↑</span>
                                    Sort Ascending
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      setSortConfig({ key: col.key, direction: "desc" });
                                      setColumnMenuOpen(null);
                                    }}
                                    onMouseEnter={(event) => {
                                      event.currentTarget.style.background = "var(--color-surface-muted)";
                                    }}
                                    onMouseLeave={(event) => {
                                      event.currentTarget.style.background = "transparent";
                                    }}
                                    style={{
                                      width: "100%",
                                      padding: "8px 12px",
                                      textAlign: "left",
                                      background: "transparent",
                                      border: "none",
                                      cursor: "pointer",
                                      fontSize: "12px",
                                      color: "var(--color-text)",
                                      display: "flex",
                                      alignItems: "center",
                                      gap: "8px",
                                    }}
                                  >
                                    <span style={{ fontSize: "12px" }}>↓</span>
                                    Sort Descending
                                  </button>
                                  <div
                                    style={{
                                      borderTop: "1px solid var(--color-border-soft)",
                                      margin: "2px 0",
                                    }}
                                  />
                                  <div
                                    onClick={() => setColumnSubmenuOpen((prev) => !prev)}
                                    onMouseEnter={(event) => {
                                      event.currentTarget.style.background = "var(--color-surface-muted)";
                                    }}
                                    onMouseLeave={(event) => {
                                      event.currentTarget.style.background = "transparent";
                                    }}
                                    style={{
                                      position: "relative",
                                      padding: "6px 12px",
                                      fontSize: "12px",
                                      display: "flex",
                                      alignItems: "center",
                                      justifyContent: "space-between",
                                      cursor: "pointer",
                                      color: "var(--color-text)",
                                    }}
                                  >
                                    <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                      <span style={{ fontSize: "12px" }}>▥</span>
                                      Columns
                                    </span>
                                    <span style={{ fontSize: "12px", color: "var(--color-text-muted)" }}>▶</span>
                                    {columnSubmenuOpen ? (
                                      <div
                                        onClick={(event) => event.stopPropagation()}
                                        onMouseDown={(event) => event.stopPropagation()}
                                        data-column-menu
                                        style={{
                                          position: "absolute",
                                          top: 0,
                                          left: "100%",
                                          marginLeft: "6px",
                                          background: "var(--color-surface)",
                                          border: "1px solid var(--color-border)",
                                          borderRadius: "0",
                                          boxShadow: "0 6px 14px rgba(0,0,0,0.12)",
                                          zIndex: 5001,
                                          minWidth: "220px",
                                          maxHeight: "260px",
                                          overflowY: "auto",
                                          padding: "8px 12px",
                                        }}
                                      >
                                        <label
                                          style={{
                                            display: "grid",
                                            gridTemplateColumns: "16px 1fr",
                                            alignItems: "center",
                                            columnGap: "8px",
                                            fontSize: "12px",
                                            padding: "4px 0",
                                            cursor: "pointer",
                                            textAlign: "left",
                                            fontWeight: 600,
                                          }}
                                        >
                                          <input
                                            type="checkbox"
                                            checked={
                                              allColumns
                                                .filter((colItem) => colItem.id !== "doc_id")
                                                .every((colItem) => !hiddenColumnIds.has(colItem.id))
                                            }
                                            onClick={(event) => event.stopPropagation()}
                                            onChange={(event) => {
                                              const checked = event.target.checked;
                                              setHiddenColumnIds((prev) => {
                                                const next = new Set(prev);
                                                const nonIdColumns = allColumns.filter(
                                                  (colItem) => colItem.id !== "doc_id",
                                                );
                                                if (checked) {
                                                  nonIdColumns.forEach((colItem) =>
                                                    next.delete(colItem.id),
                                                  );
                                                } else {
                                                  nonIdColumns.forEach((colItem) =>
                                                    next.add(colItem.id),
                                                  );
                                                  if (nonIdColumns.length) {
                                                    next.delete(nonIdColumns[0].id);
                                                  }
                                                }
                                                return next;
                                              });
                                            }}
                                            style={{ margin: 0 }}
                                          />
                                          <span style={{ textAlign: "left" }}>Show All</span>
                                        </label>
                                        <div
                                          style={{
                                            borderTop: "1px solid var(--color-border-soft)",
                                            margin: "4px 0",
                                          }}
                                        />
                                    {columnOrder
                                          .map((id) => allColumns.find((colItem) => colItem.id === id))
                                          .filter(Boolean)
                                          .filter((colItem) => colItem.id !== "doc_id")
                                          .map((colItem) => {
                                          const isVisible = !hiddenColumnIds.has(colItem.id);
                                          return (
                                            <label
                                              key={colItem.id}
                                              style={{
                                                display: "grid",
                                                gridTemplateColumns: "16px 1fr",
                                                alignItems: "center",
                                                columnGap: "8px",
                                                fontSize: "12px",
                                                padding: "4px 0",
                                                cursor: "pointer",
                                                textAlign: "left",
                                              }}
                                            >
                                              <input
                                                type="checkbox"
                                                checked={isVisible}
                                                onClick={(event) => event.stopPropagation()}
                                                onChange={() => toggleColumnVisibility(colItem.id)}
                                                style={{ margin: 0 }}
                                              />
                                              <span style={{ textAlign: "left" }}>{colItem.label}</span>
                                            </label>
                                          );
                                        })}
                                      </div>
                                    ) : null}
                                  </div>
                                  </div>,
                                  document.body,
                                )
                                : null}
                            </div>
                          </div>
                          <input
                            value={filters[col.key] || ""}
                            placeholder="Search..."
                            onChange={(e) => handleFilterChange(col.key, e.target.value)}
                            style={{ width: "100%", marginTop: "6px" }}
                          />
                          <button
                            type="button"
                            onMouseDown={(e) => startColResize(e, col.key)}
                            draggable={false}
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
                      );
                    })}
                  </tr>
                </thead>
                <tbody>
                  {false && isAdding && project && !documentsLoading && (
                    <>
                      <tr className="editing">
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
                                  {revCodeOptions.map((item) => (
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
                  ) : filteredDocuments.length === 0 && pastedRows.length === 0 ? (
                    <tr>
                      <td className="status-row" colSpan={visibleColumns.length}>
                        No documents match your filters.
                      </td>
                    </tr>
                  ) : (
                    <>
                      {sortedDocuments.map((doc, idx) => {
                      const rowId = doc.doc_id || doc.doc_name || doc.id;
                      const isEditing = editRowId === rowId;
                      const isSelected = selectedDocIds.has(rowId);
                      const isCopied = copiedDocIds.has(rowId);
                      const isCreated = lastCreatedDocIds.has(rowId);

                      return (
                        <tr
                          key={rowId}
                          data-row-id={rowId}
                          className={`${isSelected ? "selected" : ""} ${isCopied ? "copied" : ""} ${isEditing ? "editing" : ""} ${isCreated ? "created" : ""}`.trim() || undefined}
                          onClick={(event) => {
                            const isMultiToggle = event.ctrlKey || event.metaKey;
                            const isRange = event.shiftKey;
                            if (isRange && lastSelectedRowIndex !== null) {
                              const start = Math.min(lastSelectedRowIndex, idx);
                              const end = Math.max(lastSelectedRowIndex, idx);
                              const rangeIds = sortedDocuments
                                .slice(start, end + 1)
                                .map((item) => item.doc_id || item.doc_name || item.id);
                              setSelectedDocIds((prev) => {
                                const next = new Set(prev);
                                rangeIds.forEach((id) => next.add(id));
                                return next;
                              });
                            } else if (isMultiToggle) {
                              setSelectedDocIds((prev) => {
                                const next = new Set(prev);
                                if (next.has(rowId)) {
                                  next.delete(rowId);
                                } else {
                                  next.add(rowId);
                                }
                                return next;
                              });
                            } else {
                              setSelectedDocIds(new Set([rowId]));
                            }
                            setSelectedDocId(rowId);
                            setLastSelectedRowIndex(idx);
                            setActiveDetailTab("Revisions");
                            const inDesignStatus = orderedStatuses.find(
                              (s) => s.rev_status_name?.toLowerCase() === "indesign",
                            );
                            if (inDesignStatus) {
                              setInfoActiveStep(String(inDesignStatus.rev_status_id));
                            }
                          }}
                          onDoubleClick={(event) => event.preventDefault()}
                          style={{
                            cursor: "pointer",
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
                      })}
                      {false && isAdding && project && !documentsLoading && (
                        <>
                          <tr className="editing">
                            {visibleColumns.map((col) => {
                              const cellStyle = {
                                width: columnWidths[col.key]
                                  ? `${columnWidths[col.key]}px`
                                  : undefined,
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
                                        setNewDocValues((prev) => ({
                                          ...prev,
                                          title: e.target.value,
                                        }))
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
                                              String(item.ref_discipline_id ?? "") ===
                                              nextDiscipline,
                                          );
                                          const currentTypeMatches = docTypes.find(
                                            (item) =>
                                              String(item.type_id) === String(prev.type_id) &&
                                              String(item.ref_discipline_id ?? "") ===
                                                nextDiscipline,
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
                                        setNewDocValues((prev) => ({
                                          ...prev,
                                          type_id: e.target.value,
                                        }))
                                      }
                                      disabled={createStatus === "saving"}
                                    >
                                      <option value="">Select type...</option>
                                      {docTypes
                                        .filter(
                                          (item) =>
                                            !newDocValues.discipline_id ||
                                            String(item.ref_discipline_id ?? "") ===
                                              String(newDocValues.discipline_id),
                                        )
                                        .map((item) => (
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
                                      {revCodeOptions.map((item) => (
                                        <option
                                          key={item.rev_code_id}
                                          value={String(item.rev_code_id)}
                                        >
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
                      {pastedRows.length > 0 && (
                        <>
                          {pastedRows.map((row, rowIdx) => (
                            <tr key={`paste-${rowIdx}`} className="editing">
                              {visibleColumns.map((col) => {
                                const cellStyle = {
                                  width: columnWidths[col.key]
                                    ? `${columnWidths[col.key]}px`
                                    : undefined,
                                  minWidth: columnWidths[col.key]
                                    ? `${columnWidths[col.key]}px`
                                    : undefined,
                                };
                                const updateRow = (updates) =>
                                  setPastedRows((prev) => {
                                    const next = [...prev];
                                    next[rowIdx] = { ...next[rowIdx], ...updates };
                                    return next;
                                  });

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
                                        value={row.doc_name_unique}
                                        onChange={(e) =>
                                          updateRow({ doc_name_unique: e.target.value })
                                        }
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
                                        value={row.title}
                                        onChange={(e) => updateRow({ title: e.target.value })}
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
                                        value={String(row.discipline_id ?? "")}
                                        onChange={(e) => {
                                          const nextDiscipline = e.target.value;
                                          const nextTypes = docTypes.filter(
                                            (item) =>
                                              String(item.ref_discipline_id ?? "") ===
                                              nextDiscipline,
                                          );
                                          const currentTypeMatches = docTypes.find(
                                            (item) =>
                                              String(item.type_id) === String(row.type_id) &&
                                              String(item.ref_discipline_id ?? "") ===
                                                nextDiscipline,
                                          );
                                          updateRow({
                                            discipline_id: nextDiscipline,
                                            type_id: currentTypeMatches
                                              ? row.type_id
                                              : String(nextTypes[0]?.type_id ?? ""),
                                          });
                                        }}
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
                                        value={String(row.type_id ?? "")}
                                        onChange={(e) =>
                                          updateRow({ type_id: e.target.value })
                                        }
                                      >
                                        <option value="">Select type...</option>
                                        {docTypes
                                          .filter(
                                            (item) =>
                                              !row.discipline_id ||
                                              String(item.ref_discipline_id ?? "") ===
                                                String(row.discipline_id),
                                          )
                                          .map((item) => (
                                            <option
                                              key={item.type_id}
                                              value={String(item.type_id)}
                                            >
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
                                        value={String(row.jobpack_id ?? "")}
                                        onChange={(e) =>
                                          updateRow({ jobpack_id: e.target.value })
                                        }
                                      >
                                        <option value="">Select jobpack...</option>
                                        {jobpacks.map((item) => (
                                          <option
                                            key={item.jobpack_id}
                                            value={String(item.jobpack_id)}
                                          >
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
                                        value={String(row.area_id ?? "")}
                                        onChange={(e) => updateRow({ area_id: e.target.value })}
                                      >
                                        <option value="">Select area...</option>
                                        {areas.map((item) => (
                                          <option
                                            key={item.area_id}
                                            value={String(item.area_id)}
                                          >
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
                                        value={String(row.unit_id ?? "")}
                                        onChange={(e) => updateRow({ unit_id: e.target.value })}
                                      >
                                        <option value="">Select unit...</option>
                                        {units.map((item) => (
                                          <option
                                            key={item.unit_id}
                                            value={String(item.unit_id)}
                                          >
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
                                        value={String(row.rev_code_id ?? "")}
                                        onChange={(e) =>
                                          updateRow({ rev_code_id: e.target.value })
                                        }
                                      >
                                        <option value="">Select rev code...</option>
                                        {revCodeOptions.map((item) => (
                                          <option
                                            key={item.rev_code_id}
                                            value={String(item.rev_code_id)}
                                          >
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
                          ))}
                        </>
                      )}
                      {isAdding && project && !documentsLoading && (
                        <>
                          <tr className="editing">
                            {visibleColumns.map((col) => {
                              const cellStyle = {
                                width: columnWidths[col.key]
                                  ? `${columnWidths[col.key]}px`
                                  : undefined,
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
                                        setNewDocValues((prev) => ({
                                          ...prev,
                                          title: e.target.value,
                                        }))
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
                                              String(item.ref_discipline_id ?? "") ===
                                              nextDiscipline,
                                          );
                                          const currentTypeMatches = docTypes.find(
                                            (item) =>
                                              String(item.type_id) === String(prev.type_id) &&
                                              String(item.ref_discipline_id ?? "") ===
                                                nextDiscipline,
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
                                        setNewDocValues((prev) => ({
                                          ...prev,
                                          type_id: e.target.value,
                                        }))
                                      }
                                      disabled={createStatus === "saving"}
                                    >
                                      <option value="">Select type...</option>
                                      {docTypes
                                        .filter(
                                          (item) =>
                                            !newDocValues.discipline_id ||
                                            String(item.ref_discipline_id ?? "") ===
                                              String(newDocValues.discipline_id),
                                        )
                                        .map((item) => (
                                          <option
                                            key={item.type_id}
                                            value={String(item.type_id)}
                                          >
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
                                        <option
                                          key={item.jobpack_id}
                                          value={String(item.jobpack_id)}
                                        >
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
                                        <option
                                          key={item.area_id}
                                          value={String(item.area_id)}
                                        >
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
                                        <option
                                          key={item.unit_id}
                                          value={String(item.unit_id)}
                                        >
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
                                      {revCodeOptions.map((item) => (
                                        <option
                                          key={item.rev_code_id}
                                          value={String(item.rev_code_id)}
                                        >
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
                    </>
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
              borderRadius: "6px",
              padding: 0,
              boxShadow: "0 1px 2px rgba(15, 23, 42, 0.08)",
              minHeight: 0,
              display: hideWindowsOnDrag || isDetailPanelHidden ? "none" : "flex",
              flexDirection: "column",
              overflow: "hidden",
              position: "relative",
            }}
          >
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
                selectedDoc ? (
                  <div style={{ width: "100%", height: "100%", overflow: "auto", margin: 0, padding: 0, boxSizing: 'border-box' }}>
                    <div className="table-wrapper" style={{ margin: 0, padding: 0, boxSizing: 'border-box' }}>
                      <table className="table">
                        <thead>
                          <tr>
                            <th>Revision</th>
                            <th>Name of revision</th>
                            <th>Revision description</th>
                            <th>Progress %</th>
                            <th>Author</th>
                            <th>Date of revision</th>
                            <th>Plan</th>
                            <th>Actual start</th>
                            <th>Actual finish</th>
                            <th>Forecast deadline</th>
                            <th>Canceled</th>
                          </tr>
                        </thead>
                        <tbody>
                          {revisionOverviews.length === 0 ? (
                            <tr><td colSpan={10} style={{textAlign:'center',color:'var(--color-text-muted)'}}>No revisions found</td></tr>
                          ) : (
                            (() => {
                              // Remove duplicates by rev_id or rev_code_id
                              const seen = new Set();
                              const uniqueRows = revisionOverviews.filter(row => {
                                const key = row.rev_id || row.rev_code_id || row.id || JSON.stringify(row);
                                if (seen.has(key)) return false;
                                seen.add(key);
                                return true;
                              });
                              return uniqueRows.map((row, idx) => (
                                <tr
                                  key={row.rev_id || row.rev_code_id || row.revision_id || row.revision || idx}
                                  className={selectedRevisionIdx === idx ? "selected" : undefined}
                                  style={{
                                    cursor: "pointer",
                                  }}
                                  onClick={() => setSelectedRevisionIdx(idx)}
                                >
                                  <td>{row.rev_code_acronym || row.revision || row.rev_code || row.rev_code_id || ''}</td>
                                  <td>{row.rev_code_name || row.name || row.rev_name || ''}</td>
                                  <td>{row.rev_description || ''}</td>
                                  <td>{row.progress || row.rev_percent || ''}</td>
                                  <td>{row.author || row.rev_author || row.rev_author_name || ''}</td>
                                  <td>
                                    {formatDateTime(
                                      row.date || row.rev_date || row.created_at || "",
                                    )}
                                  </td>
                                  <td>{row.plan || row.plan_date || ''}</td>
                                  <td>{row.actualStart || row.actual_start || ''}</td>
                                  <td>{row.actualFinish || row.actual_finish || ''}</td>
                                  <td>{row.forecast || row.forecast_deadline || ''}</td>
                                  <td>{row.canceled || row.is_canceled ? 'Yes' : ''}</td>
                                </tr>
                              ));
                            })()
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : (
                  <div style={{ padding: "12px", color: "var(--color-text-muted)", fontSize: "13px" }}>
                    Select a document to view revisions.
                  </div>
                )
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
          {!isFlowPanelHidden && (
            <button
              type="button"
              onClick={() => setIsFlowPanelHidden(true)}
              style={{
                position: "relative",
                zIndex: 101,
                width: "8px",
                height: "80px",
                padding: "0",
                background: "var(--color-info)",
                border: "1px solid var(--color-info)",
                borderRadius: "0",
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
              title="Hide document flow"
              aria-label="Hide document flow"
            ></button>
          )}
          {isFlowPanelHidden && (
            <button
              type="button"
              onClick={() => setIsFlowPanelHidden(false)}
              style={{
                position: "relative",
                zIndex: 101,
                width: "8px",
                height: "80px",
                padding: "0",
                background: "var(--color-success)",
                border: "1px solid var(--color-success)",
                borderRadius: "0",
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
              title="Show document flow"
              aria-label="Show document flow"
            ></button>
          )}
        </div>
        <div
          style={{
            flex: isFlowPanelHidden ? "0 0 40px" : `${infoRatio} 1 0`,
            display: hideWindowsOnDrag ? "none" : "flex",
            flexDirection: "column",
            minWidth: 0,
            overflow: "visible",
          }}
        >
          <div
            className="flow-card"
            style={{
              flex: 1,
              border: isFlowPanelHidden ? "none" : undefined,
              boxShadow: isFlowPanelHidden ? "none" : undefined,
              background: isFlowPanelHidden ? "transparent" : undefined,
            }}
          >
            <div className="flow-header" style={{ display: "none" }}>
              DOCUMENT FLOW
            </div>
            <div className="flow-body">
              {revStatusLoading ? (
                <div className="flow-empty">Loading statuses…</div>
              ) : revStatusError ? (
                <div className="flow-empty">{revStatusError}</div>
              ) : orderedStatuses.length === 0 ? (
                <div className="flow-empty">No statuses configured.</div>
              ) : (
                (() => {
                  const activeIsHistory = infoActiveStep === "history";
                  const activeStatus = orderedStatuses.find(
                    (status) => String(status.rev_status_id) === String(infoActiveStep),
                  );
                  const statusKey = activeStatus ? String(activeStatus.rev_status_id) : null;
                  const behaviorName = activeStatus
                    ? behaviorNameById[activeStatus.ui_behavior_id]
                    : null;
                  const behaviorFile = activeStatus
                    ? behaviorFileById[activeStatus.ui_behavior_id]
                    : activeIsHistory
                      ? "HistoryBehavior.jsx"
                      : null;
                  const Behavior =
                    activeIsHistory || activeStatus ? resolveBehaviorByFile(behaviorFile) : null;
                  const isMenuOpen = statusKey ? statusMenuOpen[statusKey] || false : false;

                  return (
                    <>
                      <div className="flow-steps-column">
                        {orderedStatuses.map((status) => {
                          const key = String(status.rev_status_id);
                          const isActive = key === String(infoActiveStep);
                          const behaviorFileItem = behaviorFileById[status.ui_behavior_id];
                          return (
                            <button
                              key={status.rev_status_id}
                              type="button"
                              className={`flow-step ${isActive ? "active" : ""}`}
                              aria-expanded={isActive}
                              data-ui-behavior={behaviorFileItem || "default"}
                              data-final={status.final ? "true" : "false"}
                              onClick={() => {
                                if (!isFlowEnabled) {
                                  return;
                                }
                                setInfoActiveStep(key);
                                setInfoActiveSubTab("Files with Comments");
                              }}
                              disabled={!isFlowEnabled}
                              title={status.rev_status_name}
                            >
                              <span className="dot" style={{ display: "none" }} />
                              <span className="flow-step__label">{status.rev_status_name}</span>
                              <span className="flow-step__behavior" style={{ display: "none" }}>
                                {behaviorFileItem || "Default"}
                              </span>
                            </button>
                          );
                        })}
                        <button
                          type="button"
                          className={`flow-step ${activeIsHistory ? "active" : ""}`}
                          aria-expanded={activeIsHistory}
                          data-ui-behavior="HistoryBehavior.jsx"
                          data-final="false"
                          onClick={() => {
                            if (!isFlowEnabled) {
                              return;
                            }
                            setInfoActiveStep("history");
                          }}
                          disabled={!isFlowEnabled}
                          title="History"
                        >
                          <span className="dot" style={{ display: "none" }} />
                          <span className="flow-step__label">History</span>
                          <span className="flow-step__behavior">History</span>
                        </button>
                      </div>
                      <div
                        className="flow-content-column"
                        style={{ display: isFlowPanelHidden ? "none" : "flex" }}
                      >
                        <div className="flow-content-header">
                          {activeStatus
                            ? activeStatus.rev_status_name
                            : activeIsHistory
                              ? "History"
                              : "Select status"}
                          {activeStatus && isFlowEnabled && (
                            <>
                              <button
                                type="button"
                                className="flow-header-menu"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  if (!statusKey) return;
                                  setStatusMenuOpen((prev) => ({
                                    ...prev,
                                    [statusKey]: !isMenuOpen,
                                  }));
                                }}
                                onMouseEnter={(e) => {
                                  e.currentTarget.style.color = "white";
                                  e.currentTarget.style.background = "var(--color-info)";
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
                                    borderRadius: "0",
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
                                        window.confirm(
                                          `Issue "${activeStatus.rev_status_name}" to IDC?`,
                                        )
                                      ) {
                                        alert(
                                          `Status "${activeStatus.rev_status_name}" issued to IDC`,
                                        );
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
                            </>
                          )}
                        </div>
                        {activeIsHistory && isFlowEnabled && Behavior ? (
                          <div className="flow-inline-content" data-ui-behavior="HistoryBehavior.jsx">
                            <React.Suspense
                              fallback={<div className="flow-empty">Loading behavior…</div>}
                            >
                              <Behavior behaviorName="History" behaviorFile="HistoryBehavior.jsx" />
                            </React.Suspense>
                          </div>
                        ) : activeStatus && isFlowEnabled && Behavior ? (
                          <div className="flow-inline-content" data-ui-behavior={behaviorFile || ""}>
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
                                uploadedFiles={Object.fromEntries(
                                  Object.entries(uploadedFiles).map(([docId, value]) => [
                                    docId,
                                    Array.isArray(value)
                                      ? value
                                      : value && typeof value === "object" && !Array.isArray(value)
                                        ? value
                                        : [],
                                  ]),
                                )}
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
                        ) : (
                          <div className="flow-empty">Select a status to view details.</div>
                        )}
                      </div>
                    </>
                  );
                })()
              )}
            </div>
          </div>
        </div>
      </div>
      <div className="app-header">
        <span className="app-header__name">{appMeta.name}</span>
        <span className="app-header__meta">Version: {appMeta.version}</span>
        <span className="app-header__meta">Revision: {appMeta.revision}</span>
      </div>
    </main>
  );
}

export default App;

App.propTypes = {};
