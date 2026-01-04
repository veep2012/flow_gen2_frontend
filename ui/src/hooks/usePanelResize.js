import React from "react";

/**
 * Hook for managing panel border resize
 */
export const usePanelResize = (initialRatio = 0.35) => {
  const [infoRatio, setInfoRatio] = React.useState(initialRatio);
  const [isDraggingBorder, setIsDraggingBorder] = React.useState(false);
  const containerRef = React.useRef(null);

  const startBorderResize = React.useCallback(
    (event) => {
      event.preventDefault();
      setIsDraggingBorder(true);
      const container = containerRef.current;
      if (!container) return;
      
      const containerWidth = container.getBoundingClientRect().width;
      const startX = event.clientX;
      const startRatio = infoRatio;

      const handleMove = (moveEvent) => {
        const delta = startX - moveEvent.clientX;
        const deltaRatio = delta / containerWidth;
        const nextRatio = Math.max(0.15, Math.min(0.85, startRatio + deltaRatio));
        setInfoRatio(nextRatio);
      };

      const handleUp = () => {
        setIsDraggingBorder(false);
        window.removeEventListener("mousemove", handleMove);
        window.removeEventListener("mouseup", handleUp);
      };

      window.addEventListener("mousemove", handleMove);
      window.addEventListener("mouseup", handleUp);
    },
    [infoRatio],
  );

  return {
    infoRatio,
    setInfoRatio,
    isDraggingBorder,
    setIsDraggingBorder,
    containerRef,
    startBorderResize,
  };
};
