import React from "react";

const ResizableBorder = ({ onMouseDown, isDragging }) => {
  return (
    <div
      onMouseDown={onMouseDown}
      style={{
        width: '8px',
        background: isDragging ? 'var(--color-info)' : 'var(--color-border)',
        cursor: 'col-resize',
        transition: isDragging ? 'none' : 'background 0.2s',
        userSelect: 'none',
      }}
      title="Drag to resize panels"
    />
  );
};

export default ResizableBorder;
