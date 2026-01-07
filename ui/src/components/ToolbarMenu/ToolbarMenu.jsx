import React from "react";

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

const ToolbarMenu = ({
  editRowId,
  onSave,
  onCancel,
  onAddNew,
  onEdit,
  onDelete,
  onExport,
  onUndo,
  onRedo,
  isSaving,
}) => {
  if (editRowId) {
    return (
      <div style={{ display: 'flex', gap: '4px', alignItems: 'center', padding: '0 6px' }}>
        <button
          style={buttonStyle}
          title="Save changes"
          onClick={onSave}
          disabled={isSaving}
        >
          <span style={iconStyle}>💾</span>
          Save
        </button>
        <button
          style={{ ...buttonStyle, background: 'var(--color-border)', color: 'var(--color-text)' }}
          title="Cancel editing"
          onClick={onCancel}
          disabled={isSaving}
        >
          <span style={iconStyle}>✕</span>
          Cancel
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', gap: '4px', alignItems: 'center', padding: '0 6px' }}>
      <button style={buttonStyle} title="Add new document" onClick={onAddNew}>
        <span style={iconStyle}>+</span>
        Add new
      </button>
      <button style={buttonStyle} title="Edit selected document" onClick={onEdit}>
        <span style={iconStyle}>✎</span>
        Edit
      </button>
      <button style={buttonStyle} title="Delete selected document" onClick={onDelete}>
        <span style={iconStyle}>🗑</span>
        Delete
      </button>
      <button style={buttonStyle} title="Export documents" onClick={onExport}>
        <span style={iconStyle}>⬇</span>
        Export to...
      </button>
      <button style={{ ...buttonStyle, padding: '6px 10px' }} title="Undo" onClick={onUndo}>
        <span style={iconStyle}>↶</span>
      </button>
      <button style={{ ...buttonStyle, padding: '6px 10px' }} title="Redo" onClick={onRedo}>
        <span style={iconStyle}>↷</span>
      </button>
    </div>
  );
};

export default ToolbarMenu;
