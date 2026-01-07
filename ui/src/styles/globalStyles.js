/**
 * Global application styles
 * Returns a CSS string to be used in <style> tag
 */
export const globalStyles = `
  :root {
    color: #1f2933;
    background: #f5f7fb;
    font-family: "Inter", "SF Pro Display", system-ui, -apple-system, sans-serif;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: #f5f7fb;
    user-select: none;
    -webkit-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
  }
  .page {
    padding: 8px;
  }
  .toolbar {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
    color: #52606d;
    font-size: 14px;
  }
  .toolbar select {
    border: 1px solid #d9e2ec;
    border-radius: 8px;
    padding: 6px 8px;
    font-size: 13px;
    color: #52606d;
    background: #fff;
  }
  .toolbar button {
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .toolbar .status {
    font-size: 12px;
    color: #c53030;
  }
  .status-row {
    text-align: left;
    padding: 6px;
    color: #52606d;
    font-size: 14px;
    background: #f8fafc;
  }
  .status-row.error {
    color: #c53030;
    background: #fff5f5;
  }
  .progress {
    width: 120px;
    background: #e5e7eb;
    border-radius: 999px;
    height: 20px;
    position: relative;
    overflow: hidden;
    border: 1px solid #e2e8f0;
  }
  .progress__fill {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    background: linear-gradient(90deg, #2f80ed, #4ea1ff);
    border-radius: 999px;
    transition: width 180ms ease;
  }
  .progress__label {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 600;
    color: #fff;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.25);
  }
  .spinner {
    width: 22px;
    height: 22px;
    border: 3px solid #e2e8f0;
    border-top-color: #2f80ed;
    border-radius: 50%;
    display: inline-block;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
  .card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    box-shadow:
      0 10px 30px rgba(15, 23, 42, 0.05),
      0 1px 3px rgba(15, 23, 42, 0.08);
    overflow: hidden;
  }
  .table {
    width: 100%;
    border-collapse: collapse;
    white-space: nowrap;
  }
  .table thead th {
    background: #f8fafc;
    font-weight: 700;
    text-align: left;
    font-size: 14px;
    color: #1f2933;
    padding: 6px 8px 2px;
    border-bottom: 1px solid #e2e8f0;
    white-space: nowrap;
    border-right: 1px solid #e2e8f0;
  }
  .table thead th:not(:first-child) {
    border-left: 1px solid #e2e8f0;
  }
  .table thead input {
    width: 100%;
    margin-top: 4px;
    padding: 6px 8px;
    border: 1px solid #d9e2ec;
    border-radius: 8px;
    font-size: 13px;
    color: #52606d;
    background: #fff;
    caret-color: transparent;
  }
  .table td {
    padding: 6px 8px;
    border-bottom: 1px solid #e2e8f0;
    position: relative;
  }
  .table td:not(:first-child) {
    border-left: 1px solid #e2e8f0;
  }
  .table tbody tr {
    border-bottom: 1px solid #e2e8f0;
  }
  .table tbody tr:hover td {
    background: #f7fafc;
  }
  .meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 16px;
    border-bottom: 1px solid #e2e8f0;
  }
  .meta h1 {
    margin: 0;
    font-size: 18px;
    font-weight: 700;
    color: #1f2933;
  }
  .meta .count {
    font-size: 13px;
    color: #52606d;
  }
  .table-wrapper {
    width: 100%;
    height: 100%;
    overflow: auto;
  }
  .task-cabinet {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 10px;
  }
  .task-cabinet__label {
    font-size: 13px;
    font-weight: 600;
    color: #22543d;
    min-width: 92px;
  }
  .task-tab {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #ffffff;
    border: 1px solid #8fd19e;
    border-radius: 8px;
    padding: 7px 10px;
    font-size: 13px;
    font-weight: 600;
    color: #1f2933;
    box-shadow: none;
    cursor: default;
  }
  .task-tab__badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 22px;
    height: 22px;
    padding: 0 6px;
    border-radius: 6px;
    font-weight: 700;
    font-size: 12px;
    color: #fff;
  }
  .detail-tabs {
    display: flex;
    gap: 2px;
    border-bottom: 1px solid #e2e8f0;
    background: #f8fafc;
    padding: 4px 6px 0;
  }
  .detail-tab {
    padding: 8px 12px;
    border: 1px solid #e2e8f0;
    border-bottom: none;
    border-radius: 10px 10px 0 0;
    background: #f1f5f9;
    font-size: 13px;
    cursor: pointer;
    color: #1f2933;
  }
  .detail-tab.active {
    background: #fff;
    font-weight: 600;
    color: #1f2933;
  }
  .detail-tab-panel {
    border: 1px solid #e2e8f0;
    border-top: none;
    border-radius: 0 0 12px 12px;
    padding: 16px;
    background: #fff;
    min-height: 180px;
    display: flex;
    flex-direction: column;
    flex: 1;
    height: 100%;
  }
  .flow-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
  }
  .flow-header {
    padding: 12px 14px;
    font-size: 14px;
    font-weight: 700;
    color: #344155;
    border-bottom: 1px solid #e2e8f0;
  }
  .flow-body {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
  }
  .flow-step {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 14px 12px 30px;
    cursor: pointer;
    color: #1f2933;
    font-size: 13px;
    position: relative;
    background: #fff;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    width: 100%;
    text-align: left;
    font: inherit;
  }
  .flow-step::before {
    content: none;
  }
  .flow-step .dot {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    border: 2px solid #0f766e;
    background: #fff;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    color: #0f766e;
    z-index: 1;
  }
  .flow-step.active .dot {
    background: #0f766e;
    color: #fff;
    box-shadow: 0 0 0 3px rgba(15,118,110,0.15);
  }
  .flow-inline-content {
    border-left: 4px solid #0f766e;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    margin: 4px 8px 10px 8px;
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    flex: 1;
  }
  .flow-subtabs {
    margin: 0 0 8px 0;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    overflow: hidden;
  }
  .flow-subtab {
    flex: 1;
    padding: 10px;
    text-align: center;
    font-size: 13px;
    cursor: pointer;
    color: #1f2933;
    background: #fff;
    border: none;
    border-right: 1px solid #e2e8f0;
    font: inherit;
  }
  .flow-subtab.active {
    font-weight: 700;
    color: #0f766e;
    box-shadow: inset 0 -3px 0 #0f766e;
    background: #eef6f4;
  }
  .flow-subtab:last-child { border-right: none; }
  .flow-section {
    padding: 6px 0 0 0;
    background: transparent;
    border: none;
    gap: 8px;
    display: flex;
    flex-direction: column;
    flex: 1;
  }
  .flow-box {
    border: 1px solid #d9e2ec;
    border-radius: 10px;
    background: #fff;
    padding: 12px;
  }
  .flow-upload {
    border: 1px dashed #cbd5e0;
    border-radius: 12px;
    padding: 18px;
    text-align: center;
    color: #4d6b8a;
    font-size: 13px;
    background: #fff;
    transition: background 0.15s, border-color 0.15s, color 0.15s;
    font: inherit;
  }
  .flow-upload.dragging {
    background: #ecf4ff;
    border-color: #3b82f6;
    color: #1e3a8a;
  }
  .flow-step:focus-visible,
  .flow-subtab:focus-visible,
  .flow-upload:focus-visible,
  .flow-mini-tab:focus-visible {
    outline: 2px solid #2563eb;
    outline-offset: 2px;
  }
  @media (max-width: 960px) {
    .table {
      display: block;
      overflow-x: auto;
      white-space: nowrap;
    }
  }
`;
