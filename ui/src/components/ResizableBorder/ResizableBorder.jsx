import React from "react";

const ResizableBorder = ({ onMouseDown, isDragging }) => {
  return (
    <div
      onMouseDown={onMouseDown}
      style={{
        width: '8px',
        background: isDragging ? '#3b82f6' : '#e2e8f0',
        cursor: 'col-resize',
        transition: isDragging ? 'none' : 'background 0.2s',
        userSelect: 'none',
      }}
      title="Drag to resize panels"
    />
  );
};

export default ResizableBorder;
