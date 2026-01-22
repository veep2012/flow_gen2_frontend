import React from "react";
import PropTypes from "prop-types";
import "./ActionTab.css";

const ActionTab = ({ title = "Action Tab", onAdd, onRemove, onSend }) => {
  const [isDisabled] = React.useState(true);

  const handleAdd = () => {
    onAdd?.();
  };

  const handleRemove = () => {
    onRemove?.();
  };

  const handleSend = () => {
    onSend?.();
  };

  return (
    <div className="action-tab-container">
      {/* Header with Buttons */}
      <div className="action-tab-header">
        <h3>{title}</h3>
        <div className="button-group">
          <button className="btn-add" onClick={handleAdd} disabled={isDisabled} title="Add">
            + Add
          </button>
          <button
            className="btn-remove"
            onClick={handleRemove}
            disabled={isDisabled}
            title="Remove"
          >
            ⊖ Remove
          </button>
          <button className="btn-send" onClick={handleSend} disabled={isDisabled} title="Send">
            ✓ Send
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="action-tab-content">
        <p>
          No documents sent yet. Add recipients and click &quot;Send&quot; to start the
          distribution.
        </p>
      </div>
    </div>
  );
};

ActionTab.propTypes = {
  title: PropTypes.string,
  onAdd: PropTypes.func,
  onRemove: PropTypes.func,
  onSend: PropTypes.func,
};

export default ActionTab;
