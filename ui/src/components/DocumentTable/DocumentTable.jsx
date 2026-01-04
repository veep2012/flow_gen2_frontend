import React from "react";

const DocumentTable = ({
  visibleColumns,
  columnWidths,
  filters,
  onFilterChange,
  onColumnResize,
  documentsLoading,
  documentsError,
  project,
  filteredDocuments,
  selectedDocId,
  onRowSelect,
  onRowDoubleClick,
  editRowId,
  editValues,
  onEditValuesChange,
  renderCell,
}) => {
  return (
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
                    onChange={(e) => onFilterChange(col.key, e.target.value)}
                  />
                  <span
                    onMouseDown={(e) => onColumnResize(e, col.key)}
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
                    onClick={() => onRowSelect(rowId)}
                    onDoubleClick={() => onRowDoubleClick(doc)}
                    style={{ background: selectedDocId === rowId ? '#f0f4ff' : undefined }}
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
                              style={{ width: '100%', padding: '6px 8px', borderRadius: '8px', border: '1px solid #cbd5e0' }}
                              value={col.id === "doc_name" ? editValues.doc_name_unique : editValues.title}
                              onChange={(e) =>
                                onEditValuesChange(prev => ({
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
  );
};

export default DocumentTable;
