import React from "react";

const DetailPanel = ({ activeDetailTab, onTabChange }) => {
  return (
    <div style={{ 
      flex: '1 1 0',
      background: '#fff', 
      border: '1px solid #e2e8f0', 
      borderRadius: '12px', 
      padding: 0, 
      boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
      minHeight: 0,
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden'
    }}>
      <div className="detail-tabs">
        {["Revisions", "TAGs", "References", "Plan", "Information"].map((tab) => (
          <button
            key={tab}
            className={`detail-tab ${activeDetailTab === tab ? "active" : ""}`}
            onClick={() => onTabChange(tab)}
          >
            {tab}
          </button>
        ))}
      </div>
      <div className="detail-tab-panel" style={{ flex: 1 }}>
        {activeDetailTab === "Revisions" ? (
          <div style={{ color: '#52606d', fontSize: '13px' }}>
            No revisions yet. A revision will be created automatically when you save a new document.
          </div>
        ) : (
          <div style={{ color: '#52606d', fontSize: '13px' }}>
            {activeDetailTab} content will appear here.
          </div>
        )}
      </div>
    </div>
  );
};

export default DetailPanel;
