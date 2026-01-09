import React from "react";
import PropTypes from "prop-types";

const DefaultBehavior = ({ behaviorName }) => {
  return (
    <div style={{ fontSize: "13px", color: "var(--color-text-muted)", padding: "8px 4px" }}>
      {behaviorName
        ? `No UI layout mapped for "${behaviorName}".`
        : "No UI layout mapped for this status."}
    </div>
  );
};

DefaultBehavior.propTypes = {
  behaviorName: PropTypes.string,
};

DefaultBehavior.defaultProps = {
  behaviorName: "",
};

export default DefaultBehavior;
