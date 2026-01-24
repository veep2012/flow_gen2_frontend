import React from "react";

/**
 * Hook for managing document editing
 */
export const useDocumentEdit = (apiBase, reloadDocuments) => {
  const [editRowId, setEditRowId] = React.useState(null);
  const [editValues, setEditValues] = React.useState({ doc_name_unique: "", title: "" });
  const [saveError, setSaveError] = React.useState(null);
  const [saveStatus, setSaveStatus] = React.useState("idle");

  const startEdit = React.useCallback((doc) => {
    if (!doc) return;
    const rowId = doc.doc_id || doc.doc_name || doc.doc_name_unique || doc.id;
    setEditRowId(rowId);
    setSaveError(null);
    setSaveStatus("idle");
    setEditValues({
      doc_name_unique: doc.doc_name || doc.doc_name_unique || "",
      title: doc.title || "",
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

      const docId = Number(doc.doc_id ?? doc.id ?? 0);
      if (!docId) {
        setSaveStatus("error");
        setSaveError("Missing document ID");
        return;
      }

      const payload = {};
      const docName = String(editValues.doc_name_unique || "").trim();
      const docTitle = String(editValues.title || "").trim();
      if (docName) payload.doc_name_unique = docName;
      if (docTitle) payload.title = docTitle;
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
