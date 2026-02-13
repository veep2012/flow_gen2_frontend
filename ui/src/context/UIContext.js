import React from "react";
import PropTypes from "prop-types";

/**
 * Context for UI state management
 * Handles tab selection, step selection, etc.
 */
const UIContext = React.createContext();

export const UIProvider = ({ children }) => {
  const [activeDetailTab, setActiveDetailTab] = React.useState("Revisions");
  const [infoActiveStep, setInfoActiveStep] = React.useState("IDC");
  const [infoActiveSubTab, setInfoActiveSubTab] = React.useState("Comments");
  const [selectedDocId, setSelectedDocId] = React.useState(null);

  const value = {
    activeDetailTab,
    setActiveDetailTab,
    infoActiveStep,
    setInfoActiveStep,
    infoActiveSubTab,
    setInfoActiveSubTab,
    selectedDocId,
    setSelectedDocId,
  };

  return <UIContext.Provider value={value}>{children}</UIContext.Provider>;
};

UIProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

export const useUI = () => {
  const context = React.useContext(UIContext);
  if (!context) {
    throw new Error("useUI must be used within UIProvider");
  }
  return context;
};

export default UIContext;
