import React from "react";

/**
 * Hook for managing column resizing in table
 */
export const useTableColumnResize = () => {
  const [columnWidths, setColumnWidths] = React.useState({});

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

  return {
    columnWidths,
    setColumnWidths,
    startColResize,
  };
};
