import React from "react";
import PropTypes from "prop-types";

const ResizableBorder = ({ onMouseDown, isDragging }) => {
  return (
    <button
      type="button"
      onMouseDown={onMouseDown}
      style={{
        width: "8px",
        background: isDragging ? "var(--color-info)" : "var(--color-border)",
        cursor: "col-resize",
        transition: isDragging ? "none" : "background 0.2s",
        userSelect: "none",
        border: "none",
        padding: 0,
      }}
      title="Drag to resize panels"
      aria-label="Resize panels"
    />
  );
};

export default ResizableBorder;

ResizableBorder.propTypes = {
  onMouseDown: PropTypes.func.isRequired,
  isDragging: PropTypes.bool.isRequired,
};
