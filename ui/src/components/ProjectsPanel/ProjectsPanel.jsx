import React from "react";

const ProjectsPanel = ({ project, setProject, projects, projectsError, cabinetTabs }) => {
  return (
    <div style={{ 
      background: '#f0fbf4',
      border: '1px solid #b6e3c8',
      borderRadius: '8px', 
      padding: '12px 14px', 
      marginBottom: '4px',
      boxShadow: '0 2px 6px rgba(0,0,0,0.08)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <label style={{ fontSize: '13px', fontWeight: 600, color: '#22543d' }}>
          Project:
        </label>
        <select
          value={project}
          onChange={(e) => setProject(e.target.value)}
          aria-label="Select project"
          style={{
            border: '1px solid #8fd19e',
            borderRadius: '8px',
            padding: '7px 10px',
            fontSize: '13px',
            color: '#1f2933',
            background: '#ffffff',
            minWidth: '220px',
            cursor: 'pointer'
          }}
        >
          <option value="">Project number</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.label}
            </option>
          ))}
        </select>
        {projectsError ? <span style={{ fontSize: '12px', color: '#c53030' }}>{projectsError}</span> : null}
        <div className="task-cabinet" style={{ marginLeft: 'auto', padding: 0 }}>
          <div className="task-cabinet__label">Task cabinet:</div>
          {cabinetTabs.map((tab) => (
            <div key={tab.label} className="task-tab">
              <span style={{ color: '#22543d', fontWeight: 600 }}>{tab.label}</span>
              <span className="task-tab__badge" style={{ background: tab.tone }}>{tab.count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ProjectsPanel;
