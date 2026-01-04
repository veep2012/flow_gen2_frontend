import React from "react";
import { toNumber } from "@utils/number";

/**
 * Hook for managing document editing
 */
export const useDocumentEdit = (apiBase, reloadDocuments) => {
  const [editRowId, setEditRowId] = React.useState(null);
  const [editValues, setEditValues] = React.useState({ doc_name_unique: "", title: "" });
  const [saveError, setSaveError] = React.useState(null);
  const [saveStatus, setSaveStatus] = React.useState("idle");

  const startEdit = React.useCallback(
    (doc) => {
      if (!doc) return;
      const rowId = doc.doc_id || doc.doc_name || doc.doc_name_unique || doc.id;
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

  return {
    editRowId,
    editValues,
    setEditValues,
    saveError,
    setSaveError,
    saveStatus,
    setSaveStatus,
    startEdit,
    cancelEdit,
    applyEdit,
  };
};
