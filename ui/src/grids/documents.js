export const documentGridColumns = [
  { id: "doc_id", label: "ID", field: "doc_id", hidden: true },
  { id: "doc_name", label: "Name", field: "doc_name" },
  { id: "title", label: "Title", field: "title" },
  { id: "doc_type", label: "Type", field: "doc_type_display" },
  { id: "discipline", label: "Discipline", field: "discipline_display" },
  { id: "jobpack", label: "Jobpack", field: "jobpack_display" },
  { id: "area", label: "Area", field: "area_display" },
  { id: "unit", label: "Unit", field: "unit_display" },
  { id: "rev_current_id", label: "Current rev", field: "rev_current_id", hidden: true },
  { id: "rev_seq_num", label: "Rev seq", field: "rev_seq_num", hidden: true },
  { id: "rev_code", label: "Rev code", field: "rev_code_display" },
  { id: "rev_percent", label: "Rev %", field: "rev_percent_display" },
];

/**
 * Map API document payload to a grid-friendly row.
 */
export function mapDocumentRow(doc) {
  const docName = doc.doc_name_uq || doc.doc_name_unique || "";
  const docTypeDisplay = doc.doc_type_name
    ? `${doc.doc_type_name}${doc.discipline_acronym ? ` (${doc.discipline_acronym})` : ""}`
    : "";
  const disciplineDisplay = doc.discipline_name
    ? `${doc.discipline_name}${doc.discipline_acronym ? ` (${doc.discipline_acronym})` : ""}`
    : "";
  const jobpackDisplay = doc.jobpack_name || (doc.jobpack_id ? `Jobpack ${doc.jobpack_id}` : "");
  const areaDisplay = doc.area_name
    ? `${doc.area_name}${doc.area_acronym ? ` (${doc.area_acronym})` : ""}`
    : "";
  const unitDisplay = doc.unit_name || (doc.unit_id ? `Unit ${doc.unit_id}` : "");
  const revCodeDisplay = doc.rev_code_acronym
    ? `${doc.rev_code_acronym}${doc.rev_code_name ? ` (${doc.rev_code_name})` : ""}`
    : doc.rev_code_name || "—";
  const revStatusDisplay =
    doc.rev_status_name || (doc.rev_status_id ? `Status ${doc.rev_status_id}` : "—");
  const revPercentDisplay =
    doc.percentage === null || doc.percentage === undefined ? "—" : `${doc.percentage}%`;

  const mapped = {
    ...doc,
    doc_name: docName,
    doc_type_display: docTypeDisplay,
    discipline_display: disciplineDisplay,
    jobpack_display: jobpackDisplay,
    area_display: areaDisplay,
    unit_display: unitDisplay,
    rev_code_display: revCodeDisplay,
    rev_status_display: revStatusDisplay,
    rev_percent_display: revPercentDisplay,
  };

  // Ensure every column field exists on the row (defaults to raw value or null)
  documentGridColumns.forEach(({ field }) => {
    if (!(field in mapped)) {
      mapped[field] = doc[field] ?? null;
    }
  });

  return mapped;
}
