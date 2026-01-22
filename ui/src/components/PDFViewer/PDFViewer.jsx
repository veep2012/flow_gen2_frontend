import React, { useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import PropTypes from "prop-types";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

// Set up worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

const PDFViewer = ({ pdfUrl, fileName, onClose }) => {
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const onLoadSuccess = ({ numPages: num }) => {
    setNumPages(num);
    setIsLoading(false);
  };

  const onLoadError = (err) => {
    setError(`Failed to load PDF: ${err.message}`);
    setIsLoading(false);
  };

  const handlePrevPage = () => {
    setPageNumber((prev) => Math.max(1, prev - 1));
  };

  const handleNextPage = () => {
    setPageNumber((prev) => Math.min(numPages || prev, prev + 1));
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.7)",
        display: "flex",
        flexDirection: "column",
        zIndex: 1000,
        padding: "20px",
      }}
      role="button"
      tabIndex={0}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " " || e.key === "Escape") {
          e.preventDefault();
          onClose();
        }
      }}
    >
      <div
        style={{
          backgroundColor: "white",
          borderRadius: "8px",
          display: "flex",
          flexDirection: "column",
          height: "100%",
          maxWidth: "900px",
          margin: "0 auto",
          width: "100%",
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.15)",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "16px 20px",
            borderBottom: "1px solid #e0e0e0",
            backgroundColor: "#f5f5f5",
          }}
        >
          <h2 style={{ margin: 0, fontSize: "16px", fontWeight: 600 }}>📄 {fileName}</h2>
          <button
            type="button"
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              fontSize: "24px",
              cursor: "pointer",
              padding: "0",
              color: "#666",
              width: "32px",
              height: "32px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              borderRadius: "4px",
              transition: "background-color 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "#e0e0e0";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "transparent";
            }}
            aria-label="Close PDF"
          >
            ✕
          </button>
        </div>

        {/* PDF Content */}
        <div
          style={{
            flex: 1,
            overflow: "auto",
            display: "flex",
            justifyContent: "center",
            alignItems: "flex-start",
            padding: "20px",
            backgroundColor: "#f9f9f9",
          }}
        >
          {isLoading && <div style={{ color: "#666", fontSize: "14px" }}>Loading PDF...</div>}
          {error && <div style={{ color: "#d32f2f", fontSize: "14px" }}>{error}</div>}
          {!isLoading && !error && (
            <Document file={pdfUrl} onLoadSuccess={onLoadSuccess} onLoadError={onLoadError}>
              <Page pageNumber={pageNumber} />
            </Document>
          )}
        </div>

        {/* Footer with Controls */}
        {!error && numPages && (
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "12px 20px",
              borderTop: "1px solid #e0e0e0",
              backgroundColor: "#f5f5f5",
            }}
          >
            <button
              type="button"
              onClick={handlePrevPage}
              disabled={pageNumber <= 1}
              style={{
                padding: "6px 12px",
                backgroundColor: pageNumber <= 1 ? "#e0e0e0" : "#1976d2",
                color: pageNumber <= 1 ? "#999" : "white",
                border: "none",
                borderRadius: "4px",
                cursor: pageNumber <= 1 ? "default" : "pointer",
                fontSize: "13px",
                fontWeight: 500,
              }}
            >
              ← Previous
            </button>
            <span style={{ fontSize: "13px", color: "#666" }}>
              Page {pageNumber} of {numPages}
            </span>
            <button
              type="button"
              onClick={handleNextPage}
              disabled={pageNumber >= numPages}
              style={{
                padding: "6px 12px",
                backgroundColor: pageNumber >= numPages ? "#e0e0e0" : "#1976d2",
                color: pageNumber >= numPages ? "#999" : "white",
                border: "none",
                borderRadius: "4px",
                cursor: pageNumber >= numPages ? "default" : "pointer",
                fontSize: "13px",
                fontWeight: 500,
              }}
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

PDFViewer.propTypes = {
  pdfUrl: PropTypes.string.isRequired,
  fileName: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
};

export default PDFViewer;
