import React, { useMemo, useState } from "react";

const columns = [
  { key: "documentNumber", label: "Document number" },
  { key: "fileNumber", label: "Saved to file nr" },
  { key: "title", label: "Title" },
  { key: "jobPack", label: "Job pack name" },
  { key: "discipline", label: "Discipline" },
  { key: "disciplineAcronym", label: "Discipline acronym" },
  { key: "docType", label: "Doc type" },
];

const documents = [
  {
    documentNumber: "VEM-ME-DRW-0001",
    fileNumber: "FILE-2024-001",
    title: "P&ID Main Process Flow",
    jobPack: "Process Engineering Package",
    discipline: "Mechanical",
    disciplineAcronym: "MECH",
    docType: "Drawing",
  },
  {
    documentNumber: "VEM-EL-SPEC-0045",
    fileNumber: "FILE-2024-002",
    title: "Electrical Load Analysis",
    jobPack: "Electrical Design Package",
    discipline: "Electrical",
    disciplineAcronym: "ELEC",
    docType: "Specification",
  },
  {
    documentNumber: "VEM-IN-DRW-0123",
    fileNumber: "FILE-2024-003",
    title: "Instrument Hook-up Diagrams",
    jobPack: "Instrumentation Package",
    discipline: "Instrumentation",
    disciplineAcronym: "INST",
    docType: "Drawing",
  },
  {
    documentNumber: "VEM-ST-CALC-0067",
    fileNumber: "FILE-2024-004",
    title: "Structural Load Calculations",
    jobPack: "Structural Engineering Package",
    discipline: "Structural",
    disciplineAcronym: "STRU",
    docType: "Calculation",
  },
  {
    documentNumber: "VEM-PI-RPT-0089",
    fileNumber: "FILE-2024-005",
    title: "Piping Stress Analysis Report",
    jobPack: "Piping Design Package",
    discipline: "Piping",
    disciplineAcronym: "PIPE",
    docType: "Report",
  },
  {
    documentNumber: "VEM-CV-DRW-0234",
    fileNumber: "FILE-2024-006",
    title: "Civil Foundation Layout",
    jobPack: "Civil Engineering Package",
    discipline: "Civil",
    disciplineAcronym: "CIVL",
    docType: "Drawing",
  },
  {
    documentNumber: "VEM-AR-DRW-0156",
    fileNumber: "FILE-2024-007",
    title: "Architectural Floor Plans",
    jobPack: "Architecture Package",
    discipline: "Architecture",
    disciplineAcronym: "ARCH",
    docType: "Drawing",
  },
  {
    documentNumber: "VEM-PR-SPEC-0078",
    fileNumber: "FILE-2024-008",
    title: "Process Equipment Datasheet",
    jobPack: "Process Engineering Package",
    discipline: "Process",
    disciplineAcronym: "PROC",
    docType: "Specification",
  },
  {
    documentNumber: "VEM-ME-CALC-0199",
    fileNumber: "FILE-2024-009",
    title: "HVAC Heat Load Calculation",
    jobPack: "Mechanical HVAC Package",
    discipline: "Mechanical",
    disciplineAcronym: "MECH",
    docType: "Calculation",
  },
  {
    documentNumber: "VEM-EL-DRW-0267",
    fileNumber: "FILE-2024-010",
    title: "Single Line Diagram MV Switchgear",
    jobPack: "Electrical Power Package",
    discipline: "Electrical",
    disciplineAcronym: "ELEC",
    docType: "Drawing",
  },
  {
    documentNumber: "VEM-ME-DRW-0302",
    fileNumber: "FILE-2024-011",
    title: "Equipment Layout Plan",
    jobPack: "Mechanical Equipment Package",
    discipline: "Mechanical",
    disciplineAcronym: "MECH",
    docType: "Drawing",
  },
  {
    documentNumber: "VEM-IN-SPEC-0145",
    fileNumber: "FILE-2024-012",
    title: "Control Valve Specification",
    jobPack: "Instrumentation Package",
    discipline: "Instrumentation",
    disciplineAcronym: "INST",
    docType: "Specification",
  },
  {
    documentNumber: "VEM-PI-DRW-0278",
    fileNumber: "FILE-2024-013",
    title: "Piping Isometric Drawings",
    jobPack: "Piping Design Package",
    discipline: "Piping",
    disciplineAcronym: "PIPE",
    docType: "Drawing",
  },
  {
    documentNumber: "VEM-ST-DRW-0189",
    fileNumber: "FILE-2024-014",
    title: "Steel Structure General Arrangement",
    jobPack: "Structural Engineering Package",
    discipline: "Structural",
    disciplineAcronym: "STRU",
    docType: "Drawing",
  },
  {
    documentNumber: "VEM-EL-CALC-0321",
    fileNumber: "FILE-2024-015",
    title: "Cable Sizing Calculation",
    jobPack: "Electrical Power Package",
    discipline: "Electrical",
    disciplineAcronym: "ELEC",
    docType: "Calculation",
  },
  {
    documentNumber: "VEM-CV-SPEC-0234",
    fileNumber: "FILE-2024-016",
    title: "Concrete Mix Design Specification",
    jobPack: "Civil Engineering Package",
    discipline: "Civil",
    disciplineAcronym: "CIVL",
    docType: "Specification",
  },
  {
    documentNumber: "VEM-AR-SPEC-0167",
    fileNumber: "FILE-2024-017",
    title: "Interior Finishes Specification",
    jobPack: "Architecture Package",
    discipline: "Architecture",
    disciplineAcronym: "ARCH",
    docType: "Specification",
  },
  {
    documentNumber: "VEM-PR-RPT-0201",
    fileNumber: "FILE-2024-018",
    title: "Process Safety Analysis Report",
    jobPack: "Process Engineering Package",
    discipline: "Process",
    disciplineAcronym: "PROC",
    docType: "Report",
  },
];

function App() {
  const [filters, setFilters] = useState(
    () => Object.fromEntries(columns.map((col) => [col.key, ""])),
  );

  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) =>
      columns.every((col) => {
        const value = String(doc[col.key] ?? "").toLowerCase();
        const filterValue = filters[col.key].trim().toLowerCase();
        return value.includes(filterValue);
      }),
    );
  }, [filters]);

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <main className="page">
      <style>
        {`
        :root {
          color: #1f2933;
          background: #f5f7fb;
          font-family: "Inter", "SF Pro Display", system-ui, -apple-system, sans-serif;
        }
        * { box-sizing: border-box; }
        body {
          margin: 0;
          background: #f5f7fb;
        }
        .page {
          padding: 24px;
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
        }
        .table thead th {
          background: #f8fafc;
          font-weight: 700;
          text-align: left;
          font-size: 14px;
          color: #1f2933;
          padding: 14px 12px 6px;
          border-bottom: 1px solid #e2e8f0;
        }
        .table thead input {
          width: 100%;
          margin-top: 6px;
          padding: 8px 10px;
          border: 1px solid #d9e2ec;
          border-radius: 8px;
          font-size: 13px;
          color: #52606d;
          background: #fff;
        }
        .table tbody tr {
          border-bottom: 1px solid #edf2f7;
        }
        .table tbody tr:last-child {
          border-bottom: none;
        }
        .table td {
          padding: 10px 12px;
          font-size: 14px;
          color: #1f2933;
          line-height: 1.4;
          background: #fff;
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
        @media (max-width: 960px) {
          .table {
            display: block;
            overflow-x: auto;
            white-space: nowrap;
          }
        }
      `}
      </style>
      <div className="card">
        <div className="meta">
          <h1>Document register</h1>
          <span className="count">{filteredDocuments.length} items</span>
        </div>
        <table className="table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col.key}>
                  <div>{col.label}</div>
                  <input
                    value={filters[col.key]}
                    placeholder="Search..."
                    onChange={(e) => handleFilterChange(col.key, e.target.value)}
                  />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredDocuments.map((doc) => (
              <tr key={doc.documentNumber}>
                {columns.map((col) => (
                  <td key={col.key}>{doc[col.key]}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}

export default App;
