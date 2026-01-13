import React from "react";
import PropTypes from "prop-types";

const IDCBehavior = ({ selectedDoc, infoActiveSubTab, onSubTabChange }) => {
  const docName = selectedDoc ? `${selectedDoc.doc_name_unique || selectedDoc.title || "Document"}` : "No document selected";
  const docInfo = selectedDoc ? {
    type: selectedDoc.doc_type_name || "N/A",
    area: selectedDoc.area_name || "N/A",
    discipline: selectedDoc.discipline_name || "N/A",
  } : null;

  return (
    <>
      <div className="flow-subtabs" style={{ display: "flex" }}>
        {["Comments", "Distribution list"].map((tab) => (
          <button
            type="button"
            key={tab}
            className={`flow-subtab ${infoActiveSubTab === tab ? "active" : ""}`}
            aria-pressed={infoActiveSubTab === tab}
            onClick={() => onSubTabChange(tab)}
          >
            {tab}
          </button>
        ))}
      </div>
      <div className="flow-section">
        <div style={{ fontSize: "12px", color: "var(--color-text-muted)", marginBottom: "12px" }}>
          <strong>{docName}</strong>
        </div>
        {docInfo && (
          <div style={{ fontSize: "11px", color: "var(--color-text-subtle)", marginBottom: "12px" }}>
            <div>Type: {docInfo.type}</div>
            <div>Area: {docInfo.area}</div>
            <div>Discipline: {docInfo.discipline}</div>
          </div>
        )}
        {infoActiveSubTab === "Comments" ? (
          <>
            <div className="flow-box">
              <h4>Original Files</h4>
              <div style={{ fontSize: "13px", color: "var(--color-text-subtle)" }}>
                No original files uploaded yet
              </div>
            </div>
            <div className="flow-box">
              <div style={{ display: "flex", gap: "8px", marginBottom: "10px" }}>
                {["Files with Comments", "Written Comments"].map((tab) => (
                  <button
                    type="button"
                    key={tab}
                    className="flow-mini-tab"
                    style={{
                      flex: 1,
                      padding: "8px 10px",
                      borderBottom:
                        infoActiveSubTab === tab
                          ? "2px solid var(--color-primary)"
                          : "1px solid var(--color-border)",
                      fontWeight: infoActiveSubTab === tab ? 700 : 500,
                      color:
                        infoActiveSubTab === tab ? "var(--color-primary)" : "var(--color-text)",
                      cursor: "pointer",
                      textAlign: "center",
                      background: "transparent",
                      border: "none",
                    }}
                    aria-pressed={infoActiveSubTab === tab}
                    onClick={() => onSubTabChange(tab)}
                  >
                    {tab}
                  </button>
                ))}
              </div>
              <div
                style={{
                  fontSize: "13px",
                  color: "var(--color-text-subtle)",
                  padding: "12px 0",
                }}
              >
                No files with comments yet
              </div>
            </div>
          </>
        ) : (
          <div className="flow-box">
            <h4>Distribution List</h4>
            <div style={{ fontSize: "13px", color: "var(--color-text-subtle)" }}>
              No distribution list assigned
            </div>
          </div>
        )}
      </div>
    </>
  );
};

IDCBehavior.propTypes = {
  selectedDoc: PropTypes.shape({
    doc_id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    doc_name_unique: PropTypes.string,
    title: PropTypes.string,
    doc_type_name: PropTypes.string,
    area_name: PropTypes.string,
    discipline_name: PropTypes.string,
  }),
  infoActiveSubTab: PropTypes.string.isRequired,
  onSubTabChange: PropTypes.func.isRequired,
};

export default IDCBehavior;
