import React from "react";

/**
 * Hook for managing file uploads
 */
export const useUploadedFiles = () => {
  const [uploadedFiles, setUploadedFiles] = React.useState({});
  const [expandedRevisions, setExpandedRevisions] = React.useState({});
  const [isDraggingUpload, setIsDraggingUpload] = React.useState(false);
  const uploadInputRef = React.useRef(null);

  const handleUploadFiles = (files, currentStep) => {
    const list = Array.from(files || []);
    if (!list.length) return;

    const fileNames = list.map((f) => f.name);

    setUploadedFiles((prev) => ({
      ...prev,
      [currentStep]: [...(prev[currentStep] || []), ...fileNames],
    }));

    setExpandedRevisions((prev) => ({
      ...prev,
      [`${currentStep}-Rev A`]: { ...prev[`${currentStep}-Rev A`], isOpen: true },
    }));
  };

  const handleUploadDrop = (e, currentStep) => {
    e.preventDefault();
    setIsDraggingUpload(false);
    handleUploadFiles(e.dataTransfer?.files, currentStep);
  };

  const handleUploadSelect = (e, currentStep) => {
    handleUploadFiles(e.target.files, currentStep);
    e.target.value = "";
  };

  const uploadDragProps = (currentStep) => ({
    onDragOver: (e) => {
      e.preventDefault();
      setIsDraggingUpload(true);
    },
    onDragLeave: () => setIsDraggingUpload(false),
    onDrop: (e) => handleUploadDrop(e, currentStep),
  });

  const toggleRevisionExpanded = (revisionKey) => {
    setExpandedRevisions((prev) => ({
      ...prev,
      [revisionKey]: { ...prev[revisionKey], isOpen: !prev[revisionKey]?.isOpen },
    }));
  };

  return {
    uploadedFiles,
    setUploadedFiles,
    expandedRevisions,
    setExpandedRevisions,
    isDraggingUpload,
    setIsDraggingUpload,
    uploadInputRef,
    handleUploadFiles,
    handleUploadDrop,
    handleUploadSelect,
    uploadDragProps,
    toggleRevisionExpanded,
  };
};
