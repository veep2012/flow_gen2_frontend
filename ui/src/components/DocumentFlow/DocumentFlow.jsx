import React from "react";

const DocumentFlow = ({
  infoActiveStep,
  onStepClick,
  infoActiveSubTab,
  onSubTabChange,
  activeStep,
  uploadedFiles,
  expandedRevisions,
  onRevisionToggle,
  isDraggingUpload,
  uploadDragProps,
  onUploadClick,
  uploadInputRef,
  onFileSelect,
}) => {
  const renderStepContent = () => {
    if (activeStep === "IDC") {
      return (
        <>
          <div className="flow-subtabs" style={{ display: 'flex' }}>
            {["Comments", "Distribution list"].map((tab) => (
              <div
                key={tab}
                className={`flow-subtab ${infoActiveSubTab === tab ? "active" : ""}`}
                onClick={() => onSubTabChange(tab)}
              >
                {tab}
              </div>
            ))}
          </div>
          <div className="flow-section">
            {infoActiveSubTab === "Comments" ? (
              <>
                <div style={{ fontSize: '12px', color: '#52606d' }}>
                  Not document owner or in Distribution list.
                </div>
                <div className="flow-box">
                  <h4>Original Files</h4>
                  <div style={{ fontSize: '13px', color: '#98a2b3' }}>No original files uploaded yet</div>
                </div>
                <div className="flow-box">
                  <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
                    {["Files with Comments", "Written Comments"].map((tab) => (
                      <div
                        key={tab}
                        style={{
                          flex: 1,
                          padding: '8px 10px',
                          borderBottom: infoActiveSubTab === tab ? '2px solid #0f766e' : '1px solid #e2e8f0',
                          fontWeight: infoActiveSubTab === tab ? 700 : 500,
                          color: infoActiveSubTab === tab ? '#0f766e' : '#1f2933',
                          cursor: 'pointer',
                          textAlign: 'center'
                        }}
                        onClick={() => onSubTabChange(tab)}
                      >
                        {tab}
                      </div>
                    ))}
                  </div>
                  <div style={{ fontSize: '13px', color: '#98a2b3', padding: '12px 0' }}>
                    No files with comments yet
                  </div>
                </div>
              </>
            ) : (
              <div className="flow-box">
                <h4>Distribution List</h4>
                <div style={{ fontSize: '13px', color: '#98a2b3' }}>No distribution list assigned</div>
              </div>
            )}
          </div>
        </>
      );
    }

    if (activeStep === "History") {
      return (
        <div style={{ fontSize: '13px', color: '#52606d', padding: '8px 4px' }}>
          No history available yet.
        </div>
      );
    }

    if (activeStep === "Official" || activeStep === "Ready for Issue") {
      return (
        <div style={{ fontSize: '13px', color: '#52606d', padding: '8px 4px' }}>
          No documents available yet.
        </div>
      );
    }

    // InDesign or other steps with upload capability
    return (
      <div style={{ display: 'flex', flexDirection: 'column', flex: 1, gap: '8px' }}>
        {uploadedFiles[activeStep] && uploadedFiles[activeStep].length > 0 ? (
          <div style={{ flex: 1, overflow: 'auto', padding: '8px 0' }}>
            {['Rev A', 'Rev B', 'Rev C'].map((revision, revIdx) => {
              const revFiles = uploadedFiles[activeStep]?.filter(
                (f, idx) => idx >= revIdx * 5 && idx < (revIdx + 1) * 5
              ) || [];
              
              if (!revFiles.length && revIdx > 0) return null;
              
              const revKey = `${activeStep}-${revision}`;
              const isExpanded = expandedRevisions[revKey]?.isOpen !== false;
              
              return (
                <div key={revision} style={{ marginBottom: '4px' }}>
                  <div
                    onClick={() => onRevisionToggle(revKey)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '6px 8px',
                      cursor: 'pointer',
                      color: '#1f2933',
                      fontSize: '13px',
                      fontWeight: 600,
                      userSelect: 'none'
                    }}
                  >
                    <span style={{ fontSize: '12px', width: '16px' }}>
                      {isExpanded ? '▼' : '▶'}
                    </span>
                    <span>{revision}</span>
                  </div>
                  {isExpanded && revFiles.map((file, idx) => (
                    <div
                      key={`${revision}-${idx}`}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '4px 8px 4px 32px',
                        color: '#4d6b8a',
                        fontSize: '12px'
                      }}
                    >
                      <span>📄</span>
                      <span>{file}</span>
                    </div>
                  ))}
                </div>
              );
            })}
            <div style={{ flex: 1 }} />
            <button
              onClick={onUploadClick}
              style={{
                padding: '6px 12px',
                background: '#4d6b8a',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '12px',
                marginTop: '8px',
                alignSelf: 'flex-start'
              }}
            >
              + Add files
            </button>
          </div>
        ) : (
          <>
            <div style={{ flex: 1 }} />
            <div
              className={`flow-upload ${isDraggingUpload ? "dragging" : ""}`}
              {...uploadDragProps(activeStep)}
              onClick={onUploadClick}
            >
              Drag & drop PDF files here<br />or click to browse • Multiple files supported
            </div>
          </>
        )}
        <input
          ref={uploadInputRef}
          type="file"
          multiple
          accept="application/pdf"
          style={{ display: "none" }}
          onChange={(e) => onFileSelect(e, activeStep)}
        />
      </div>
    );
  };

  return (
    <div className="flow-card" style={{ flex: 1 }}>
      <div className="flow-header">DOCUMENT FLOW</div>
      <div className="flow-body">
        {["Official", "Ready for Issue", "IDC", "InDesign", "History"].map((step) => (
          <React.Fragment key={step}>
            <div
              className={`flow-step ${infoActiveStep === step ? "active" : ""}`}
              onClick={() => onStepClick(step)}
            >
              <span className="dot">⦿</span>
              <span>{step}</span>
              {infoActiveStep === step && <span style={{ position: 'absolute', right: 10, color: '#4a5568' }}>⋮</span>}
            </div>
            {infoActiveStep === step && (
              <div className="flow-inline-content">
                {renderStepContent()}
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export default DocumentFlow;
