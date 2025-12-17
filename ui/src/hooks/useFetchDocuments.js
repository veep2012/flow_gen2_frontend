import { useCallback, useEffect, useMemo, useState } from "react";
import { mapDocumentRow } from "../grids/documents";

export function useFetchDocuments({ apiBase = "/api/v1", visibleColumns }) {
  const normalizedBase = useMemo(
    () => (apiBase || "/api/v1").replace(/\/+$/, ""),
    [apiBase],
  );

  const createEmptyFilters = useCallback(
    () => Object.fromEntries(visibleColumns.map((col) => [col.key, ""])),
    [visibleColumns],
  );

  const [filters, setFilters] = useState(createEmptyFilters);
  const [project, setProject] = useState("");
  const [projects, setProjects] = useState([]);
  const [projectsError, setProjectsError] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [documentsError, setDocumentsError] = useState(null);
  const [documentsLoading, setDocumentsLoading] = useState(false);

  const handleFilterChange = useCallback((key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }, []);

  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) =>
      visibleColumns.every((col) => {
        const value = String(doc[col.key] ?? "").toLowerCase();
        const filterValue = filters[col.key].trim().toLowerCase();
        return value.includes(filterValue);
      }),
    );
  }, [filters, documents, visibleColumns]);

  useEffect(() => {
    const extractProjects = (data) => {
      const candidates = [
        data,
        data?.items,
        data?.results,
        data?.projects,
        data?.data,
      ].find(Array.isArray);

      const source = candidates ?? [];
      return source.map((item) => {
        if (typeof item === "string" || typeof item === "number") {
          return { id: String(item), label: String(item) };
        }
        const id =
          item?.id ??
          item?.project_id ??
          item?.value ??
          item?.code ??
          item?.name ??
          item?.number;
        const label =
          item?.name ??
          item?.project_name ??
          item?.label ??
          item?.title ??
          item?.code ??
          item?.id ??
          item?.project_id ??
          item?.number ??
          id;
        return { id: String(id ?? ""), label: String(label ?? "") };
      });
    };

    let active = true;
    fetch(`${normalizedBase}/lookups/projects`)
      .then((res) => {
        if (res.status === 404) {
          return [];
        }
        if (!res.ok) {
          const err = new Error(`Failed to load projects (${res.status})`);
          err.type = "api";
          err.status = res.status;
          throw err;
        }
        return res.json();
      })
      .then((data) => {
        if (!active) return;
        const normalized = extractProjects(data).filter((p) => p.id && p.label);
        setProjects(normalized);
        setProjectsError(normalized.length === 0 ? "No projects found" : null);
      })
      .catch((err) => {
        if (!active) return;
        if (err.name === "AbortError") return;
        const message =
          err.type === "api"
            ? err.message
            : `Network error while loading projects: ${err.message || "Unknown error"}`;
        setProjectsError(message);
      });
    return () => {
      active = false;
    };
  }, [normalizedBase]);

  useEffect(() => {
    if (!project) {
      setDocuments([]);
      setDocumentsError(null);
      return;
    }

    const controller = new AbortController();
    const { signal } = controller;
    setDocuments([]);
    setFilters(createEmptyFilters());
    setDocumentsLoading(true);
    setDocumentsError(null);

    fetch(`${normalizedBase}/documents/docs?project_id=${encodeURIComponent(project)}`, { signal })
      .then((res) => {
        if (res.status === 404) {
          return [];
        }
        if (!res.ok) {
          const err = new Error(`Failed to load documents (${res.status})`);
          err.type = "api";
          err.status = res.status;
          throw err;
        }
        return res.json();
      })
      .then((data) => {
        const normalized = Array.isArray(data) ? data : [];
        const mapped = normalized.map((doc, index) => {
          const row = mapDocumentRow(doc);
          if (!row.doc_id && row.doc_name_unique) {
            row.doc_id = row.doc_name_unique;
          }
          if (!row.doc_id) {
            row.doc_id = `row-${index}`;
          }
          return row;
        });
        setDocuments(mapped);
        setDocumentsError(mapped.length === 0 ? "No documents found for project" : null);
      })
      .catch((err) => {
        if (signal.aborted || err.name === "AbortError") return;
        const message =
          err.type === "api"
            ? err.message
            : `Network error while loading documents: ${err.message || "Unknown error"}`;
        setDocumentsError(message);
      })
      .finally(() => {
        if (signal.aborted) return;
        setDocumentsLoading(false);
      });

    return () => controller.abort();
  }, [project, normalizedBase, createEmptyFilters]);

  return {
    project,
    setProject,
    projects,
    projectsError,
    filters,
    handleFilterChange,
    documents,
    filteredDocuments,
    documentsError,
    documentsLoading,
  };
}
