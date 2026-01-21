import React from "react";
import PropTypes from "prop-types";
import "./InformationTab.css";

const InformationTab = ({ title = "Information", data = {} }) => {
  return (
    <div className="information-tab-container">
      {/* Header */}
      <div className="information-tab-header">
        <h3>{title}</h3>
      </div>

      {/* Content Area */}
      <div className="information-tab-content">
        {Object.keys(data).length === 0 ? (
          <div className="empty-state">
            <p>No information available</p>
          </div>
        ) : (
          <div className="information-list">
            {Object.entries(data).map(([key, value]) => (
              <div key={key} className="information-item">
                <span className="information-label">{key}:</span>
                <span className="information-value">{value}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

InformationTab.propTypes = {
  title: PropTypes.string,
  data: PropTypes.object,
};

export default InformationTab;
