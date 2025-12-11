import { useEffect, useMemo, useState } from "react";

const API_BASE = (() => {
  const configured = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "");
  if (configured) return configured;
  if (typeof window !== "undefined") {
    const { protocol, hostname, port } = window.location;
    const portPart = port ? `:${port}` : "";
    return `${protocol}//${hostname}${portPart}`;
  }
  return "http://localhost:5556";
})();

function useAreas() {
  const [areas, setAreas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAreas = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/v1/lookups/areas`);
      if (!res.ok) {
        throw new Error(`API error ${res.status}`);
      }
      const data = await res.json();
      setAreas(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAreas();
  }, []);

  return { areas, loading, error, fetchAreas, setAreas };
}

function useDisciplines() {
  const [disciplines, setDisciplines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDisciplines = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/v1/lookups/disciplines`);
      if (!res.ok) {
        throw new Error(`API error ${res.status}`);
      }
      const data = await res.json();
      setDisciplines(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDisciplines();
  }, []);

  return { disciplines, loading, error, fetchDisciplines, setDisciplines };
}

function useProjects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/v1/lookups/projects`);
      if (!res.ok) {
        throw new Error(`API error ${res.status}`);
      }
      const data = await res.json();
      setProjects(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  return { projects, loading, error, fetchProjects, setProjects };
}

function useUnits() {
  const [units, setUnits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchUnits = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/v1/lookups/units`);
      if (!res.ok) {
        throw new Error(`API error ${res.status}`);
      }
      const data = await res.json();
      setUnits(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUnits();
  }, []);

  return { units, loading, error, fetchUnits, setUnits };
}

function useJobpacks() {
  const [jobpacks, setJobpacks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchJobpacks = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/v1/lookups/jobpacks`);
      if (!res.ok) {
        throw new Error(`API error ${res.status}`);
      }
      const data = await res.json();
      setJobpacks(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobpacks();
  }, []);

  return { jobpacks, loading, error, fetchJobpacks, setJobpacks };
}

function useDocTypes() {
  const [docTypes, setDocTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDocTypes = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/v1/documents/doc_types`);
      if (!res.ok) {
        throw new Error(`API error ${res.status}`);
      }
      const data = await res.json();
      setDocTypes(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocTypes();
  }, []);

  return { docTypes, loading, error, fetchDocTypes, setDocTypes };
}

function useDocsByProject() {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchDocs = async (projectId) => {
    if (!projectId) {
      setDocs([]);
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${API_BASE}/api/v1/documents/docs?project_id=${projectId}`);
      if (res.status === 404) {
        setDocs([]);
        return;
      }
      if (!res.ok) {
        throw new Error(`API error ${res.status}`);
      }
      const data = await res.json();
      setDocs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return { docs, loading, error, fetchDocs, setDocs };
}

function useRoles() {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchRoles = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/v1/people/roles`);
      if (!res.ok) {
        throw new Error(`API error ${res.status}`);
      }
      const data = await res.json();
      setRoles(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoles();
  }, []);

  return { roles, loading, error, fetchRoles, setRoles };
}

function useMilestones() {
  const [milestones, setMilestones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchMilestones = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/v1/lookups/doc_rev_milestones`);
      if (!res.ok) {
        throw new Error(`API error ${res.status}`);
      }
      const data = await res.json();
      setMilestones(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMilestones();
  }, []);

  return { milestones, loading, error, fetchMilestones, setMilestones };
}

function useRevisionOverview() {
  const [revisionOverview, setRevisionOverview] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchRevisionOverview = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/v1/lookups/revision_overview`);
      if (!res.ok) {
        throw new Error(`API error ${res.status}`);
      }
      const data = await res.json();
      setRevisionOverview(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRevisionOverview();
  }, []);

  return { revisionOverview, loading, error, fetchRevisionOverview, setRevisionOverview };
}

function useDocRevStatuses() {
  const [statuses, setStatuses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStatuses = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/v1/lookups/doc_rev_statuses`);
      if (!res.ok) {
        throw new Error(`API error ${res.status}`);
      }
      const data = await res.json();
      setStatuses(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatuses();
  }, []);

  return { statuses, loading, error, fetchStatuses, setStatuses };
}

function usePersons() {
  const [persons, setPersons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchPersons = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${API_BASE}/api/v1/people/persons`);
      if (res.status === 404) {
        setPersons([]);
        return;
      }
      if (!res.ok) {
        throw new Error(`API error ${res.status}`);
      }
      const data = await res.json();
      setPersons(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPersons();
  }, []);

  return { persons, loading, error, fetchPersons, setPersons };
}

function useUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${API_BASE}/api/v1/people/users`);
      if (res.status === 404) {
        setUsers([]);
        return;
      }
      if (!res.ok) {
        throw new Error(`API error ${res.status}`);
      }
      const data = await res.json();
      setUsers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  return { users, loading, error, fetchUsers, setUsers };
}

function usePermissions() {
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchPermissions = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${API_BASE}/api/v1/people/permissions`);
      if (res.status === 404) {
        setPermissions([]);
        return;
      }
      if (!res.ok) {
        throw new Error(`API error ${res.status}`);
      }
      const data = await res.json();
      setPermissions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPermissions();
  }, []);

  return { permissions, loading, error, fetchPermissions, setPermissions };
}

export default function App() {
  const { areas, loading, error, fetchAreas, setAreas } = useAreas();
  const {
    disciplines,
    loading: disciplinesLoading,
    error: disciplinesError,
    fetchDisciplines,
    setDisciplines,
  } = useDisciplines();
  const {
    projects,
    loading: projectsLoading,
    error: projectsError,
    fetchProjects,
    setProjects,
  } = useProjects();
  const { docs, loading: docsLoading, error: docsError, fetchDocs, setDocs } = useDocsByProject();
  const { units, loading: unitsLoading, error: unitsError, fetchUnits, setUnits } = useUnits();
  const {
    jobpacks,
    loading: jobpacksLoading,
    error: jobpacksError,
    fetchJobpacks,
    setJobpacks,
  } = useJobpacks();
  const {
    docTypes,
    loading: docTypesLoading,
    error: docTypesError,
    fetchDocTypes,
    setDocTypes,
  } = useDocTypes();
  const { roles, loading: rolesLoading, error: rolesError, fetchRoles, setRoles } = useRoles();
  const {
    milestones,
    loading: milestonesLoading,
    error: milestonesError,
    fetchMilestones,
    setMilestones,
  } = useMilestones();
  const {
    revisionOverview,
    loading: revisionOverviewLoading,
    error: revisionOverviewError,
    fetchRevisionOverview,
    setRevisionOverview,
  } = useRevisionOverview();
  const {
    statuses,
    loading: statusesLoading,
    error: statusesError,
    fetchStatuses,
    setStatuses,
  } = useDocRevStatuses();
  const {
    persons,
    loading: personsLoading,
    error: personsError,
    fetchPersons,
    setPersons,
  } = usePersons();
  const {
    users,
    loading: usersLoading,
    error: usersError,
    fetchUsers,
    setUsers,
  } = useUsers();
  const {
    permissions,
    loading: permissionsLoading,
    error: permissionsError,
    fetchPermissions,
    setPermissions,
  } = usePermissions();
  const [docProjectId, setDocProjectId] = useState("");
  useEffect(() => {
    if (projects.length > 0 && docProjectId === "") {
      const firstProjectId = projects[0].project_id;
      setDocProjectId(String(firstProjectId));
      fetchDocs(firstProjectId);
    }
  }, [projects, docProjectId]);
  const availablePersons = useMemo(
    () => persons.filter((p) => !users.some((u) => u.person_id === p.person_id)),
    [persons, users],
  );
  const areaById = useMemo(
    () => Object.fromEntries(areas.map((a) => [a.area_id, a.area_name])),
    [areas],
  );
  const unitById = useMemo(
    () => Object.fromEntries(units.map((u) => [u.unit_id, u.unit_name])),
    [units],
  );
  const docTypeById = useMemo(
    () => Object.fromEntries(docTypes.map((t) => [t.type_id, t.doc_type_name])),
    [docTypes],
  );
  const jobpackById = useMemo(
    () => Object.fromEntries(jobpacks.map((j) => [j.jobpack_id, j.jobpack_name])),
    [jobpacks],
  );
  const [createForm, setCreateForm] = useState({ area_name: "", area_acronym: "" });
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({ area_name: "", area_acronym: "" });
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [discCreateForm, setDiscCreateForm] = useState({
    discipline_name: "",
    discipline_acronym: "",
  });
  const [discEditingId, setDiscEditingId] = useState(null);
  const [discForm, setDiscForm] = useState({
    discipline_name: "",
    discipline_acronym: "",
  });
  const [discSaving, setDiscSaving] = useState(false);
  const [discSaveError, setDiscSaveError] = useState("");
  const [projectCreateForm, setProjectCreateForm] = useState({ project_name: "" });
  const [projectEditingId, setProjectEditingId] = useState(null);
  const [projectForm, setProjectForm] = useState({ project_name: "" });
  const [projectSaving, setProjectSaving] = useState(false);
  const [projectSaveError, setProjectSaveError] = useState("");
  const [unitCreateForm, setUnitCreateForm] = useState({ unit_name: "" });
  const [unitEditingId, setUnitEditingId] = useState(null);
  const [unitForm, setUnitForm] = useState({ unit_name: "" });
  const [unitSaving, setUnitSaving] = useState(false);
  const [unitSaveError, setUnitSaveError] = useState("");
  const [jobpackCreateForm, setJobpackCreateForm] = useState({ jobpack_name: "" });
  const [jobpackEditingId, setJobpackEditingId] = useState(null);
  const [jobpackForm, setJobpackForm] = useState({ jobpack_name: "" });
  const [jobpackSaving, setJobpackSaving] = useState(false);
  const [jobpackSaveError, setJobpackSaveError] = useState("");
  const [roleCreateForm, setRoleCreateForm] = useState({ role_name: "" });
  const [roleEditingId, setRoleEditingId] = useState(null);
  const [roleForm, setRoleForm] = useState({ role_name: "" });
  const [roleSaving, setRoleSaving] = useState(false);
  const [roleSaveError, setRoleSaveError] = useState("");
  const [milestoneCreateForm, setMilestoneCreateForm] = useState({
    milestone_name: "",
    progress: "",
  });
  const [milestoneEditingId, setMilestoneEditingId] = useState(null);
  const [milestoneForm, setMilestoneForm] = useState({ milestone_name: "", progress: "" });
  const [milestoneSaving, setMilestoneSaving] = useState(false);
  const [milestoneSaveError, setMilestoneSaveError] = useState("");
  const [revCreateForm, setRevCreateForm] = useState({
    rev_code_name: "",
    rev_code_acronym: "",
    rev_description: "",
    percentage: "",
  });
  const [revEditingId, setRevEditingId] = useState(null);
  const [revForm, setRevForm] = useState({
    rev_code_name: "",
    rev_code_acronym: "",
    rev_description: "",
    percentage: "",
  });
  const [revSaving, setRevSaving] = useState(false);
  const [revSaveError, setRevSaveError] = useState("");
  const [statusCreateForm, setStatusCreateForm] = useState({ rev_status_name: "" });
  const [statusEditingId, setStatusEditingId] = useState(null);
  const [statusForm, setStatusForm] = useState({ rev_status_name: "" });
  const [statusSaving, setStatusSaving] = useState(false);
  const [statusSaveError, setStatusSaveError] = useState("");
  const [personCreateForm, setPersonCreateForm] = useState({ person_name: "", photo_s3_uid: "" });
  const [personEditingId, setPersonEditingId] = useState(null);
  const [personForm, setPersonForm] = useState({ person_name: "", photo_s3_uid: "" });
  const [personSaving, setPersonSaving] = useState(false);
  const [personSaveError, setPersonSaveError] = useState("");
  const [userCreateForm, setUserCreateForm] = useState({
    person_id: "",
    user_acronym: "",
    role_id: "",
  });
  const [userEditingId, setUserEditingId] = useState(null);
  const [userForm, setUserForm] = useState({ person_id: "", user_acronym: "", role_id: "" });
  const [userSaving, setUserSaving] = useState(false);
  const [userSaveError, setUserSaveError] = useState("");
  const [permissionCreateForm, setPermissionCreateForm] = useState({
    user_id: "",
    project_id: "",
    discipline_id: "",
  });
  const [permissionSaving, setPermissionSaving] = useState(false);
  const [permissionSaveError, setPermissionSaveError] = useState("");
  const [permissionEditingKey, setPermissionEditingKey] = useState(null);
  const [permissionForm, setPermissionForm] = useState({ project_id: "", discipline_id: "" });
  const [activeTab, setActiveTab] = useState("lookups");
  const header = useMemo(() => {
    const areaLabel = loading ? "Loading areas…" : error ? "Areas unavailable" : `${areas.length} Areas`;
    const discLabel = disciplinesLoading
      ? "Loading disciplines…"
      : disciplinesError
        ? "Disciplines unavailable"
        : `${disciplines.length} Disciplines`;
    const projectLabel = projectsLoading
      ? "Loading projects…"
      : projectsError
        ? "Projects unavailable"
        : `${projects.length} Projects`;
    const unitLabel = unitsLoading
      ? "Loading units…"
      : unitsError
        ? "Units unavailable"
        : `${units.length} Units`;
    const jobpackLabel = jobpacksLoading
      ? "Loading jobpacks…"
      : jobpacksError
        ? "Jobpacks unavailable"
        : `${jobpacks.length} Jobpacks`;
    const roleLabel = rolesLoading
      ? "Loading roles…"
      : rolesError
        ? "Roles unavailable"
        : `${roles.length} Roles`;
    const milestoneLabel = milestonesLoading
      ? "Loading milestones…"
      : milestonesError
        ? "Milestones unavailable"
        : `${milestones.length} Milestones`;
    const revisionLabel = revisionOverviewLoading
      ? "Loading revisions…"
      : revisionOverviewError
        ? "Revisions unavailable"
        : `${revisionOverview.length} Revision codes`;
    const statusLabel = statusesLoading
      ? "Loading statuses…"
      : statusesError
        ? "Statuses unavailable"
        : `${statuses.length} Rev statuses`;
    const personsLabel = personsLoading
      ? "Loading persons…"
      : personsError
        ? "Persons unavailable"
        : `${persons.length} Persons`;
    const usersLabel = usersLoading
      ? "Loading users…"
      : usersError
        ? "Users unavailable"
        : `${users.length} Users`;
    const permissionsLabel = permissionsLoading
      ? "Loading permissions…"
      : permissionsError
        ? "Permissions unavailable"
        : `${permissions.length} Permissions`;
    return `${areaLabel} • ${discLabel} • ${projectLabel} • ${unitLabel} • ${jobpackLabel} • ${roleLabel} • ${milestoneLabel} • ${revisionLabel} • ${statusLabel} • ${personsLabel} • ${usersLabel} • ${permissionsLabel}`;
  }, [
    areas.length,
    disciplines.length,
    projects.length,
    units.length,
    jobpacks.length,
    roles.length,
    milestones.length,
    revisionOverview.length,
    statuses.length,
    loading,
    error,
    disciplinesLoading,
    disciplinesError,
    projectsLoading,
    projectsError,
    unitsLoading,
    unitsError,
    jobpacksLoading,
    jobpacksError,
    rolesLoading,
    rolesError,
    milestonesLoading,
    milestonesError,
    revisionOverviewLoading,
    revisionOverviewError,
    statusesLoading,
    statusesError,
    persons.length,
    personsLoading,
    personsError,
    users.length,
    usersLoading,
    usersError,
    permissions.length,
    permissionsLoading,
    permissionsError,
  ]);

  return (
    <div className="page">
      <div className="hero">
        <div>
          <p className="eyebrow">Flow Docs</p>
          <h1>Project lookups</h1>
          <p className="lede">
            Lightweight UI to inspect lookup tables served by the FastAPI backend. Switch tabs to
            separate lookups from future person/user management.
          </p>
          <p className="hint">API base: {API_BASE}</p>
        </div>
        <div className="pill">{header}</div>
      </div>

      <div className="tabs" role="tablist" aria-label="Test UI sections">
        <button
          id="lookups-tab"
          className={`tab ${activeTab === "lookups" ? "is-active" : ""}`}
          role="tab"
          aria-selected={activeTab === "lookups"}
          aria-controls="lookups-pane"
          onClick={() => setActiveTab("lookups")}
        >
          Lookups
        </button>
        <button
          id="docs-tab"
          className={`tab ${activeTab === "documents" ? "is-active" : ""}`}
          role="tab"
          aria-selected={activeTab === "documents"}
          aria-controls="docs-pane"
          onClick={() => setActiveTab("documents")}
        >
          Documents / Revisions
        </button>
        <button
          id="people-tab"
          className={`tab ${activeTab === "people" ? "is-active" : ""}`}
          role="tab"
          aria-selected={activeTab === "people"}
          aria-controls="people-pane"
          onClick={() => setActiveTab("people")}
        >
          Persons / Users
        </button>
      </div>

      {activeTab === "lookups" ? (
        <>
          <section className="panel" id="lookups-pane" role="tabpanel" aria-labelledby="lookups-tab">
            <div className="panel-header">
              <h2>Areas</h2>
              <span className="status">
                {loading ? "Loading…" : error ? "Error" : "Ready"}
              </span>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {saveError && <div className="alert alert-error">{saveError}</div>}
        {!error && areas.length === 0 && !loading && (
          <div className="alert">No areas available</div>
        )}

        <div className="panel subpanel">
          <h3>Add area</h3>
          <div className="create-row">
            <input
              className="input"
              placeholder="Area name"
              value={createForm.area_name}
              onChange={(e) => setCreateForm((f) => ({ ...f, area_name: e.target.value }))}
            />
            <input
              className="input"
              placeholder="Acronym"
              value={createForm.area_acronym}
              onChange={(e) => setCreateForm((f) => ({ ...f, area_acronym: e.target.value }))}
            />
            <button
              className="btn"
              disabled={saving || !createForm.area_name || !createForm.area_acronym}
              onClick={async () => {
                setSaveError("");
                setSaving(true);
                try {
                  const res = await fetch(`${API_BASE}/api/v1/lookups/areas/insert`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(createForm),
                  });
                  if (!res.ok) {
                    const detail = await res.json().catch(() => ({}));
                    throw new Error(detail.detail || `Create failed (${res.status})`);
                  }
                  const created = await res.json();
                  setAreas((prev) => [...prev, created]);
                  setCreateForm({ area_name: "", area_acronym: "" });
                } catch (err) {
                  setSaveError(err instanceof Error ? err.message : "Create failed");
                } finally {
                  setSaving(false);
                }
              }}
            >
              {saving ? "Saving…" : "Add"}
            </button>
          </div>
        </div>

        <div className="table">
          <div className="table-head">
            <span>ID</span>
            <span>Name</span>
            <span>Acronym</span>
            <span>Actions</span>
          </div>
          <div className="table-body">
            {areas.map((area) => (
              <div className="table-row" key={area.area_id}>
                <span>{area.area_id}</span>
                {editingId === area.area_id ? (
                  <>
                    <input
                      className="input"
                      value={form.area_name}
                      onChange={(e) => setForm((f) => ({ ...f, area_name: e.target.value }))}
                    />
                    <input
                      className="input"
                      value={form.area_acronym}
                      onChange={(e) =>
                        setForm((f) => ({ ...f, area_acronym: e.target.value }))
                      }
                    />
                  </>
                ) : (
                  <>
                    <span>{area.area_name}</span>
                    <span className="tag">{area.area_acronym}</span>
                  </>
                )}
                <span className="actions">
                  {editingId === area.area_id ? (
                    <>
                      <button
                        className="btn"
                        disabled={saving}
                        onClick={async () => {
                          setSaveError("");
                          setSaving(true);
                          try {
                            const res = await fetch(`${API_BASE}/api/v1/lookups/areas/update`, {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({
                                area_id: area.area_id,
                                area_name: form.area_name,
                                area_acronym: form.area_acronym,
                              }),
                            });
                            if (!res.ok) {
                              const detail = await res.json().catch(() => ({}));
                              throw new Error(detail.detail || `Save failed (${res.status})`);
                            }
                            const updated = await res.json();
                            setAreas((prev) =>
                              prev.map((it) => (it.area_id === area.area_id ? updated : it)),
                            );
                            setEditingId(null);
                          } catch (err) {
                            setSaveError(err instanceof Error ? err.message : "Save failed");
                          } finally {
                            setSaving(false);
                          }
                        }}
                      >
                        {saving ? "Saving…" : "Save"}
                      </button>
                      <button
                        className="btn btn-ghost"
                        disabled={saving}
                        onClick={() => {
                          setEditingId(null);
                          setSaveError("");
                        }}
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        className="btn"
                        onClick={() => {
                          setEditingId(area.area_id);
                          setForm({
                            area_name: area.area_name,
                            area_acronym: area.area_acronym,
                          });
                        }}
                      >
                        Edit
                      </button>
                      <button
                        className="btn btn-ghost"
                        disabled={saving}
                        onClick={async () => {
                          setSaveError("");
                          setSaving(true);
                          try {
                            const res = await fetch(`${API_BASE}/api/v1/lookups/areas/delete`, {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({ area_id: area.area_id }),
                            });
                            if (!res.ok) {
                              const detail = await res.json().catch(() => ({}));
                              throw new Error(detail.detail || `Delete failed (${res.status})`);
                            }
                            setAreas((prev) => prev.filter((it) => it.area_id !== area.area_id));
                          } catch (err) {
                            setSaveError(err instanceof Error ? err.message : "Delete failed");
                          } finally {
                            setSaving(false);
                          }
                        }}
                      >
                        Delete
                      </button>
                    </>
                  )}
                </span>
              </div>
            ))}
            {loading && (
              <div className="table-row muted">
                <span colSpan={4}>Fetching…</span>
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Revision overview</h2>
          <span className="status">
            {revisionOverviewLoading ? "Loading…" : revisionOverviewError ? "Error" : "Ready"}
          </span>
        </div>

        {revisionOverviewError && <div className="alert alert-error">{revisionOverviewError}</div>}
        {revSaveError && <div className="alert alert-error">{revSaveError}</div>}
        {!revisionOverviewError && revisionOverview.length === 0 && !revisionOverviewLoading && (
          <div className="alert">No revision codes available</div>
        )}

        <div className="panel subpanel">
          <h3>Add revision code</h3>
          <div className="create-row rev-create">
            <input
              className="input"
              placeholder="Code name"
              value={revCreateForm.rev_code_name}
              onChange={(e) => setRevCreateForm((f) => ({ ...f, rev_code_name: e.target.value }))}
            />
            <input
              className="input"
              placeholder="Acronym"
              value={revCreateForm.rev_code_acronym}
              onChange={(e) =>
                setRevCreateForm((f) => ({ ...f, rev_code_acronym: e.target.value }))
              }
            />
            <input
              className="input"
              placeholder="Description"
              value={revCreateForm.rev_description}
              onChange={(e) =>
                setRevCreateForm((f) => ({ ...f, rev_description: e.target.value }))
              }
            />
            <input
              className="input"
              type="number"
              placeholder="Percent"
              value={revCreateForm.percentage}
              onChange={(e) =>
                setRevCreateForm((f) => ({
                  ...f,
                  percentage: e.target.value === "" ? "" : Number(e.target.value),
                }))
              }
            />
            <button
              className="btn"
              disabled={
                revSaving ||
                !revCreateForm.rev_code_name ||
                !revCreateForm.rev_code_acronym ||
                !revCreateForm.rev_description
              }
              onClick={async () => {
                setRevSaveError("");
                setRevSaving(true);
                try {
                  const res = await fetch(`${API_BASE}/api/v1/lookups/revision_overview/insert`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      rev_code_name: revCreateForm.rev_code_name,
                      rev_code_acronym: revCreateForm.rev_code_acronym,
                      rev_description: revCreateForm.rev_description,
                      percentage:
                        revCreateForm.percentage === "" ? null : Number(revCreateForm.percentage),
                    }),
                  });
                  if (!res.ok) {
                    const detail = await res.json().catch(() => ({}));
                    throw new Error(detail.detail || `Create failed (${res.status})`);
                  }
                  const created = await res.json();
                  setRevisionOverview((prev) => [...prev, created]);
                  setRevCreateForm({
                    rev_code_name: "",
                    rev_code_acronym: "",
                    rev_description: "",
                    percentage: "",
                  });
                } catch (err) {
                  setRevSaveError(err instanceof Error ? err.message : "Create failed");
                } finally {
                  setRevSaving(false);
                }
              }}
            >
              {revSaving ? "Saving…" : "Add"}
            </button>
          </div>
        </div>

        <div className="table rev-table">
          <div className="table-head rev-head">
            <span>ID</span>
            <span>Name</span>
            <span>Acronym</span>
            <span>Description</span>
            <span>Percent</span>
            <span>Actions</span>
          </div>
          <div className="table-body">
            {revisionOverview.map((rev) => (
              <div className="table-row rev-row" key={rev.rev_code_id}>
                <span>{rev.rev_code_id}</span>
                {revEditingId === rev.rev_code_id ? (
                  <>
                    <input
                      className="input"
                      value={revForm.rev_code_name}
                      onChange={(e) =>
                        setRevForm((f) => ({ ...f, rev_code_name: e.target.value }))
                      }
                    />
                    <input
                      className="input"
                      value={revForm.rev_code_acronym}
                      onChange={(e) =>
                        setRevForm((f) => ({ ...f, rev_code_acronym: e.target.value }))
                      }
                    />
                    <input
                      className="input"
                      value={revForm.rev_description}
                      onChange={(e) =>
                        setRevForm((f) => ({ ...f, rev_description: e.target.value }))
                      }
                    />
                    <input
                      className="input"
                      type="number"
                      value={revForm.percentage}
                      onChange={(e) =>
                        setRevForm((f) => ({
                          ...f,
                          percentage: e.target.value === "" ? "" : Number(e.target.value),
                        }))
                      }
                    />
                  </>
                ) : (
                  <>
                    <span>{rev.rev_code_name}</span>
                    <span className="tag">{rev.rev_code_acronym}</span>
                    <span>{rev.rev_description}</span>
                    <span className="tag">
                      {rev.percentage === null || rev.percentage === undefined
                        ? "—"
                        : `${rev.percentage}%`}
                    </span>
                  </>
                )}
                <span className="actions">
                  {revEditingId === rev.rev_code_id ? (
                    <>
                      <button
                        className="btn"
                        disabled={revSaving}
                        onClick={async () => {
                          setRevSaveError("");
                          setRevSaving(true);
                          try {
                            const res = await fetch(
                              `${API_BASE}/api/v1/lookups/revision_overview/update`,
                              {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                  rev_code_id: rev.rev_code_id,
                                  rev_code_name: revForm.rev_code_name,
                                  rev_code_acronym: revForm.rev_code_acronym,
                                  rev_description: revForm.rev_description,
                                  percentage:
                                    revForm.percentage === "" ? null : Number(revForm.percentage),
                                }),
                              },
                            );
                            if (!res.ok) {
                              const detail = await res.json().catch(() => ({}));
                              throw new Error(detail.detail || `Save failed (${res.status})`);
                            }
                            const updated = await res.json();
                            setRevisionOverview((prev) =>
                              prev.map((it) => (it.rev_code_id === rev.rev_code_id ? updated : it)),
                            );
                            setRevEditingId(null);
                          } catch (err) {
                            setRevSaveError(err instanceof Error ? err.message : "Save failed");
                          } finally {
                            setRevSaving(false);
                          }
                        }}
                      >
                        {revSaving ? "Saving…" : "Save"}
                      </button>
                      <button
                        className="btn btn-ghost"
                        disabled={revSaving}
                        onClick={() => {
                          setRevEditingId(null);
                          setRevSaveError("");
                        }}
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        className="btn"
                        onClick={() => {
                          setRevEditingId(rev.rev_code_id);
                          setRevForm({
                            rev_code_name: rev.rev_code_name,
                            rev_code_acronym: rev.rev_code_acronym,
                            rev_description: rev.rev_description,
                            percentage:
                              rev.percentage === null || rev.percentage === undefined
                                ? ""
                                : rev.percentage,
                          });
                        }}
                      >
                        Edit
                      </button>
                      <button
                        className="btn btn-ghost"
                        disabled={revSaving}
                        onClick={async () => {
                          setRevSaveError("");
                          setRevSaving(true);
                          try {
                            const res = await fetch(
                              `${API_BASE}/api/v1/lookups/revision_overview/delete`,
                              {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ rev_code_id: rev.rev_code_id }),
                              },
                            );
                            if (!res.ok) {
                              const detail = await res.json().catch(() => ({}));
                              throw new Error(detail.detail || `Delete failed (${res.status})`);
                            }
                            setRevisionOverview((prev) =>
                              prev.filter((it) => it.rev_code_id !== rev.rev_code_id),
                            );
                          } catch (err) {
                            setRevSaveError(err instanceof Error ? err.message : "Delete failed");
                          } finally {
                            setRevSaving(false);
                          }
                        }}
                      >
                        Delete
                      </button>
                    </>
                  )}
                </span>
              </div>
            ))}
            {revisionOverviewLoading && (
              <div className="table-row muted">
                <span colSpan={6}>Fetching…</span>
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Doc revision statuses</h2>
          <span className="status">
            {statusesLoading ? "Loading…" : statusesError ? "Error" : "Ready"}
          </span>
        </div>

        {statusesError && <div className="alert alert-error">{statusesError}</div>}
        {statusSaveError && <div className="alert alert-error">{statusSaveError}</div>}
        {!statusesError && statuses.length === 0 && !statusesLoading && (
          <div className="alert">No statuses available</div>
        )}

        <div className="panel subpanel">
          <h3>Add status</h3>
          <div className="create-row">
            <input
              className="input"
              placeholder="Status name"
              value={statusCreateForm.rev_status_name}
              onChange={(e) =>
                setStatusCreateForm((f) => ({ ...f, rev_status_name: e.target.value }))
              }
            />
            <div />
            <button
              className="btn"
              disabled={statusSaving || !statusCreateForm.rev_status_name}
              onClick={async () => {
                setStatusSaveError("");
                setStatusSaving(true);
                try {
                  const res = await fetch(`${API_BASE}/api/v1/lookups/doc_rev_statuses/insert`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      rev_status_name: statusCreateForm.rev_status_name,
                    }),
                  });
                  if (!res.ok) {
                    const detail = await res.json().catch(() => ({}));
                    throw new Error(detail.detail || `Create failed (${res.status})`);
                  }
                  const created = await res.json();
                  setStatuses((prev) => [...prev, created]);
                  setStatusCreateForm({ rev_status_name: "" });
                } catch (err) {
                  setStatusSaveError(err instanceof Error ? err.message : "Create failed");
                } finally {
                  setStatusSaving(false);
                }
              }}
            >
              {statusSaving ? "Saving…" : "Add"}
            </button>
          </div>
        </div>

        <div className="table">
          <div className="table-head">
            <span>ID</span>
            <span>Name</span>
            <span className="hide-on-small" />
            <span>Actions</span>
          </div>
          <div className="table-body">
            {statuses.map((status) => (
              <div className="table-row" key={status.rev_status_id}>
                <span>{status.rev_status_id}</span>
                {statusEditingId === status.rev_status_id ? (
                  <>
                    <input
                      className="input"
                      value={statusForm.rev_status_name}
                      onChange={(e) =>
                        setStatusForm((f) => ({ ...f, rev_status_name: e.target.value }))
                      }
                    />
                    <div />
                  </>
                ) : (
                  <>
                    <span>{status.rev_status_name}</span>
                    <span className="hide-on-small" />
                  </>
                )}
                <span className="actions">
                  {statusEditingId === status.rev_status_id ? (
                    <>
                      <button
                        className="btn"
                        disabled={statusSaving}
                        onClick={async () => {
                          setStatusSaveError("");
                          setStatusSaving(true);
                          try {
                            const res = await fetch(
                              `${API_BASE}/api/v1/lookups/doc_rev_statuses/update`,
                              {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                  rev_status_id: status.rev_status_id,
                                  rev_status_name: statusForm.rev_status_name,
                                }),
                              },
                            );
                            if (!res.ok) {
                              const detail = await res.json().catch(() => ({}));
                              throw new Error(detail.detail || `Save failed (${res.status})`);
                            }
                            const updated = await res.json();
                            setStatuses((prev) =>
                              prev.map((it) =>
                                it.rev_status_id === status.rev_status_id ? updated : it,
                              ),
                            );
                            setStatusEditingId(null);
                          } catch (err) {
                            setStatusSaveError(err instanceof Error ? err.message : "Save failed");
                          } finally {
                            setStatusSaving(false);
                          }
                        }}
                      >
                        {statusSaving ? "Saving…" : "Save"}
                      </button>
                      <button
                        className="btn btn-ghost"
                        disabled={statusSaving}
                        onClick={() => {
                          setStatusEditingId(null);
                          setStatusSaveError("");
                        }}
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        className="btn"
                        onClick={() => {
                          setStatusEditingId(status.rev_status_id);
                          setStatusForm({ rev_status_name: status.rev_status_name });
                        }}
                      >
                        Edit
                      </button>
                      <button
                        className="btn btn-ghost"
                        disabled={statusSaving}
                        onClick={async () => {
                          setStatusSaveError("");
                          setStatusSaving(true);
                          try {
                            const res = await fetch(
                              `${API_BASE}/api/v1/lookups/doc_rev_statuses/delete`,
                              {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ rev_status_id: status.rev_status_id }),
                              },
                            );
                            if (!res.ok) {
                              const detail = await res.json().catch(() => ({}));
                              throw new Error(detail.detail || `Delete failed (${res.status})`);
                            }
                            setStatuses((prev) =>
                              prev.filter((it) => it.rev_status_id !== status.rev_status_id),
                            );
                          } catch (err) {
                            setStatusSaveError(err instanceof Error ? err.message : "Delete failed");
                          } finally {
                            setStatusSaving(false);
                          }
                        }}
                      >
                        Delete
                      </button>
                    </>
                  )}
                </span>
              </div>
            ))}
            {statusesLoading && (
              <div className="table-row muted">
                <span colSpan={4}>Fetching…</span>
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Jobpacks</h2>
          <span className="status">
            {jobpacksLoading ? "Loading…" : jobpacksError ? "Error" : "Ready"}
          </span>
        </div>

        {jobpacksError && <div className="alert alert-error">{jobpacksError}</div>}
        {jobpackSaveError && <div className="alert alert-error">{jobpackSaveError}</div>}
        {!jobpacksError && jobpacks.length === 0 && !jobpacksLoading && (
          <div className="alert">No jobpacks available</div>
        )}

        <div className="panel subpanel">
          <h3>Add jobpack</h3>
          <div className="create-row">
            <input
              className="input"
              placeholder="Jobpack name"
              value={jobpackCreateForm.jobpack_name}
              onChange={(e) =>
                setJobpackCreateForm((f) => ({ ...f, jobpack_name: e.target.value }))
              }
            />
            <div />
            <button
              className="btn"
              disabled={jobpackSaving || !jobpackCreateForm.jobpack_name}
              onClick={async () => {
                setJobpackSaveError("");
                setJobpackSaving(true);
                try {
                  const res = await fetch(`${API_BASE}/api/v1/lookups/jobpacks/insert`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(jobpackCreateForm),
                  });
                  if (!res.ok) {
                    const detail = await res.json().catch(() => ({}));
                    throw new Error(detail.detail || `Create failed (${res.status})`);
                  }
                  const created = await res.json();
                  setJobpacks((prev) => [...prev, created]);
                  setJobpackCreateForm({ jobpack_name: "" });
                } catch (err) {
                  setJobpackSaveError(err instanceof Error ? err.message : "Create failed");
                } finally {
                  setJobpackSaving(false);
                }
              }}
            >
              {jobpackSaving ? "Saving…" : "Add"}
            </button>
          </div>
        </div>

        <div className="table">
          <div className="table-head">
            <span>ID</span>
            <span>Name</span>
            <span className="hide-on-small" />
            <span>Actions</span>
          </div>
          <div className="table-body">
            {jobpacks.map((jobpack) => (
              <div className="table-row" key={jobpack.jobpack_id}>
                <span>{jobpack.jobpack_id}</span>
                {jobpackEditingId === jobpack.jobpack_id ? (
                  <>
                    <input
                      className="input"
                      value={jobpackForm.jobpack_name}
                      onChange={(e) =>
                        setJobpackForm((f) => ({ ...f, jobpack_name: e.target.value }))
                      }
                    />
                    <div />
                  </>
                ) : (
                  <>
                    <span>{jobpack.jobpack_name}</span>
                    <span className="hide-on-small" />
                  </>
                )}
                <span className="actions">
                  {jobpackEditingId === jobpack.jobpack_id ? (
                    <>
                      <button
                        className="btn"
                        disabled={jobpackSaving}
                        onClick={async () => {
                          setJobpackSaveError("");
                          setJobpackSaving(true);
                          try {
                            const res = await fetch(`${API_BASE}/api/v1/lookups/jobpacks/update`, {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({
                                jobpack_id: jobpack.jobpack_id,
                                jobpack_name: jobpackForm.jobpack_name,
                              }),
                            });
                            if (!res.ok) {
                              const detail = await res.json().catch(() => ({}));
                              throw new Error(detail.detail || `Save failed (${res.status})`);
                            }
                            const updated = await res.json();
                            setJobpacks((prev) =>
                              prev.map((it) =>
                                it.jobpack_id === jobpack.jobpack_id ? updated : it,
                              ),
                            );
                            setJobpackEditingId(null);
                          } catch (err) {
                            setJobpackSaveError(err instanceof Error ? err.message : "Save failed");
                          } finally {
                            setJobpackSaving(false);
                          }
                        }}
                      >
                        {jobpackSaving ? "Saving…" : "Save"}
                      </button>
                      <button
                        className="btn btn-ghost"
                        disabled={jobpackSaving}
                        onClick={() => {
                          setJobpackEditingId(null);
                          setJobpackSaveError("");
                        }}
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        className="btn"
                        onClick={() => {
                          setJobpackEditingId(jobpack.jobpack_id);
                          setJobpackForm({ jobpack_name: jobpack.jobpack_name });
                        }}
                      >
                        Edit
                      </button>
                      <button
                        className="btn btn-ghost"
                        disabled={jobpackSaving}
                        onClick={async () => {
                          setJobpackSaveError("");
                          setJobpackSaving(true);
                          try {
                            const res = await fetch(`${API_BASE}/api/v1/lookups/jobpacks/delete`, {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({ jobpack_id: jobpack.jobpack_id }),
                            });
                            if (!res.ok) {
                              const detail = await res.json().catch(() => ({}));
                              throw new Error(detail.detail || `Delete failed (${res.status})`);
                            }
                            setJobpacks((prev) =>
                              prev.filter((it) => it.jobpack_id !== jobpack.jobpack_id),
                            );
                          } catch (err) {
                            setJobpackSaveError(err instanceof Error ? err.message : "Delete failed");
                          } finally {
                            setJobpackSaving(false);
                          }
                        }}
                      >
                        Delete
                      </button>
                    </>
                  )}
                </span>
              </div>
            ))}
            {jobpacksLoading && (
              <div className="table-row muted">
                <span colSpan={4}>Fetching…</span>
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Roles</h2>
          <span className="status">{rolesLoading ? "Loading…" : rolesError ? "Error" : "Ready"}</span>
        </div>

        {rolesError && <div className="alert alert-error">{rolesError}</div>}
        {roleSaveError && <div className="alert alert-error">{roleSaveError}</div>}
        {!rolesError && roles.length === 0 && !rolesLoading && (
          <div className="alert">No roles available</div>
        )}

        <div className="panel subpanel">
          <h3>Add role</h3>
          <div className="create-row">
            <input
              className="input"
              placeholder="Role name"
              value={roleCreateForm.role_name}
              onChange={(e) => setRoleCreateForm((f) => ({ ...f, role_name: e.target.value }))}
            />
            <button
              className="btn"
              disabled={roleSaving || !roleCreateForm.role_name}
              onClick={async () => {
                setRoleSaveError("");
                  setRoleSaving(true);
                  try {
                    const res = await fetch(`${API_BASE}/api/v1/people/roles/insert`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({
                        role_name: roleCreateForm.role_name,
                      }),
                  });
                  if (!res.ok) {
                    const detail = await res.json().catch(() => ({}));
                    throw new Error(detail.detail || `Create failed (${res.status})`);
                  }
                  const created = await res.json();
                  setRoles((prev) => [...prev, created]);
                  setRoleCreateForm({ role_name: "" });
                } catch (err) {
                  setRoleSaveError(err instanceof Error ? err.message : "Create failed");
                } finally {
                  setRoleSaving(false);
                }
              }}
            >
              {roleSaving ? "Saving…" : "Add"}
            </button>
          </div>
        </div>

        <div className="table">
          <div className="table-head">
            <span>ID</span>
            <span>Name</span>
            <span className="hide-on-small" />
            <span>Actions</span>
          </div>
          <div className="table-body">
            {roles.map((role) => (
              <div className="table-row" key={role.role_id}>
                <span>{role.role_id}</span>
                {roleEditingId === role.role_id ? (
                  <>
                    <input
                      className="input"
                      value={roleForm.role_name}
                      onChange={(e) => setRoleForm((f) => ({ ...f, role_name: e.target.value }))}
                    />
                    <div />
                  </>
                ) : (
                  <>
                    <span>{role.role_name}</span>
                    <span className="hide-on-small" />
                  </>
                )}
                <span className="actions">
                  {roleEditingId === role.role_id ? (
                    <>
                      <button
                        className="btn"
                        disabled={roleSaving}
                        onClick={async () => {
                            setRoleSaveError("");
                            setRoleSaving(true);
                            try {
                              const res = await fetch(`${API_BASE}/api/v1/people/roles/update`, {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                  role_id: role.role_id,
                                  role_name: roleForm.role_name,
                              }),
                            });
                            if (!res.ok) {
                              const detail = await res.json().catch(() => ({}));
                              throw new Error(detail.detail || `Save failed (${res.status})`);
                            }
                            const updated = await res.json();
                            setRoles((prev) =>
                              prev.map((it) => (it.role_id === role.role_id ? updated : it)),
                            );
                            setRoleEditingId(null);
                          } catch (err) {
                            setRoleSaveError(err instanceof Error ? err.message : "Save failed");
                          } finally {
                            setRoleSaving(false);
                          }
                        }}
                      >
                        {roleSaving ? "Saving…" : "Save"}
                      </button>
                      <button
                        className="btn btn-ghost"
                        disabled={roleSaving}
                        onClick={() => {
                          setRoleEditingId(null);
                          setRoleSaveError("");
                        }}
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        className="btn"
                        onClick={() => {
                          setRoleEditingId(role.role_id);
                          setRoleForm({ role_name: role.role_name });
                        }}
                      >
                        Edit
                      </button>
                      <button
                        className="btn btn-ghost"
                        disabled={roleSaving}
                        onClick={async () => {
                            setRoleSaveError("");
                            setRoleSaving(true);
                            try {
                              const res = await fetch(`${API_BASE}/api/v1/people/roles/delete`, {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ role_id: role.role_id }),
                              });
                            if (!res.ok) {
                              const detail = await res.json().catch(() => ({}));
                              throw new Error(detail.detail || `Delete failed (${res.status})`);
                            }
                            setRoles((prev) => prev.filter((it) => it.role_id !== role.role_id));
                          } catch (err) {
                            setRoleSaveError(err instanceof Error ? err.message : "Delete failed");
                          } finally {
                            setRoleSaving(false);
                          }
                        }}
                      >
                        Delete
                      </button>
                    </>
                  )}
                </span>
              </div>
            ))}
            {rolesLoading && (
              <div className="table-row muted">
                <span colSpan={4}>Fetching…</span>
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Doc revision milestones</h2>
          <span className="status">
            {milestonesLoading ? "Loading…" : milestonesError ? "Error" : "Ready"}
          </span>
        </div>

        {milestonesError && <div className="alert alert-error">{milestonesError}</div>}
        {milestoneSaveError && <div className="alert alert-error">{milestoneSaveError}</div>}
        {!milestonesError && milestones.length === 0 && !milestonesLoading && (
          <div className="alert">No milestones available</div>
        )}

        <div className="panel subpanel">
          <h3>Add milestone</h3>
          <div className="create-row">
            <input
              className="input"
              placeholder="Milestone name"
              value={milestoneCreateForm.milestone_name}
              onChange={(e) =>
                setMilestoneCreateForm((f) => ({ ...f, milestone_name: e.target.value }))
              }
            />
            <input
              className="input"
              type="number"
              placeholder="Progress (%)"
              value={milestoneCreateForm.progress}
              onChange={(e) =>
                setMilestoneCreateForm((f) => ({
                  ...f,
                  progress: e.target.value === "" ? "" : Number(e.target.value),
                }))
              }
            />
            <button
              className="btn"
              disabled={milestoneSaving || !milestoneCreateForm.milestone_name}
              onClick={async () => {
                setMilestoneSaveError("");
                setMilestoneSaving(true);
                try {
                  const res = await fetch(`${API_BASE}/api/v1/lookups/doc_rev_milestones/insert`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      milestone_name: milestoneCreateForm.milestone_name,
                      progress:
                        milestoneCreateForm.progress === "" ? null : Number(milestoneCreateForm.progress),
                    }),
                  });
                  if (!res.ok) {
                    const detail = await res.json().catch(() => ({}));
                    throw new Error(detail.detail || `Create failed (${res.status})`);
                  }
                  const created = await res.json();
                  setMilestones((prev) => [...prev, created]);
                  setMilestoneCreateForm({ milestone_name: "", progress: "" });
                } catch (err) {
                  setMilestoneSaveError(err instanceof Error ? err.message : "Create failed");
                } finally {
                  setMilestoneSaving(false);
                }
              }}
            >
              {milestoneSaving ? "Saving…" : "Add"}
            </button>
          </div>
        </div>

        <div className="table">
          <div className="table-head">
            <span>ID</span>
            <span>Name</span>
            <span>Progress</span>
            <span>Actions</span>
          </div>
          <div className="table-body">
            {milestones.map((milestone) => (
              <div className="table-row" key={milestone.milestone_id}>
                <span>{milestone.milestone_id}</span>
                {milestoneEditingId === milestone.milestone_id ? (
                  <>
                    <input
                      className="input"
                      value={milestoneForm.milestone_name}
                      onChange={(e) =>
                        setMilestoneForm((f) => ({ ...f, milestone_name: e.target.value }))
                      }
                    />
                    <input
                      className="input"
                      type="number"
                      value={milestoneForm.progress}
                      onChange={(e) =>
                        setMilestoneForm((f) => ({
                          ...f,
                          progress: e.target.value === "" ? "" : Number(e.target.value),
                        }))
                      }
                    />
                  </>
                ) : (
                  <>
                    <span>{milestone.milestone_name}</span>
                    <span className="tag">
                      {milestone.progress === null || milestone.progress === undefined
                        ? "—"
                        : `${milestone.progress}%`}
                    </span>
                  </>
                )}
                <span className="actions">
                  {milestoneEditingId === milestone.milestone_id ? (
                    <>
                      <button
                        className="btn"
                        disabled={milestoneSaving}
                        onClick={async () => {
                          setMilestoneSaveError("");
                          setMilestoneSaving(true);
                          try {
                            const res = await fetch(
                              `${API_BASE}/api/v1/lookups/doc_rev_milestones/update`,
                              {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                  milestone_id: milestone.milestone_id,
                                  milestone_name: milestoneForm.milestone_name,
                                  progress:
                                    milestoneForm.progress === "" ? null : Number(milestoneForm.progress),
                                }),
                              },
                            );
                            if (!res.ok) {
                              const detail = await res.json().catch(() => ({}));
                              throw new Error(detail.detail || `Save failed (${res.status})`);
                            }
                            const updated = await res.json();
                            setMilestones((prev) =>
                              prev.map((it) =>
                                it.milestone_id === milestone.milestone_id ? updated : it,
                              ),
                            );
                            setMilestoneEditingId(null);
                          } catch (err) {
                            setMilestoneSaveError(err instanceof Error ? err.message : "Save failed");
                          } finally {
                            setMilestoneSaving(false);
                          }
                        }}
                      >
                        {milestoneSaving ? "Saving…" : "Save"}
                      </button>
                      <button
                        className="btn btn-ghost"
                        disabled={milestoneSaving}
                        onClick={() => {
                          setMilestoneEditingId(null);
                          setMilestoneSaveError("");
                        }}
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        className="btn"
                        onClick={() => {
                          setMilestoneEditingId(milestone.milestone_id);
                          setMilestoneForm({
                            milestone_name: milestone.milestone_name,
                            progress:
                              milestone.progress === null || milestone.progress === undefined
                                ? ""
                                : milestone.progress,
                          });
                        }}
                      >
                        Edit
                      </button>
                      <button
                        className="btn btn-ghost"
                        disabled={milestoneSaving}
                        onClick={async () => {
                          setMilestoneSaveError("");
                          setMilestoneSaving(true);
                          try {
                            const res = await fetch(
                              `${API_BASE}/api/v1/lookups/doc_rev_milestones/delete`,
                              {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ milestone_id: milestone.milestone_id }),
                              },
                            );
                            if (!res.ok) {
                              const detail = await res.json().catch(() => ({}));
                              throw new Error(detail.detail || `Delete failed (${res.status})`);
                            }
                            setMilestones((prev) =>
                              prev.filter((it) => it.milestone_id !== milestone.milestone_id),
                            );
                          } catch (err) {
                            setMilestoneSaveError(err instanceof Error ? err.message : "Delete failed");
                          } finally {
                            setMilestoneSaving(false);
                          }
                        }}
                      >
                        Delete
                      </button>
                    </>
                  )}
                </span>
              </div>
            ))}
            {milestonesLoading && (
              <div className="table-row muted">
                <span colSpan={4}>Fetching…</span>
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Projects</h2>
          <span className="status">
            {projectsLoading ? "Loading…" : projectsError ? "Error" : "Ready"}
          </span>
        </div>

        {projectsError && <div className="alert alert-error">{projectsError}</div>}
        {projectSaveError && <div className="alert alert-error">{projectSaveError}</div>}
        {!projectsError && projects.length === 0 && !projectsLoading && (
          <div className="alert">No projects available</div>
        )}

        <div className="panel subpanel">
          <h3>Add project</h3>
          <div className="create-row">
            <input
              className="input"
              placeholder="Project name"
              value={projectCreateForm.project_name}
              onChange={(e) =>
                setProjectCreateForm((f) => ({ ...f, project_name: e.target.value }))
              }
            />
            <div />
            <button
              className="btn"
              disabled={projectSaving || !projectCreateForm.project_name}
              onClick={async () => {
                setProjectSaveError("");
                setProjectSaving(true);
                try {
                  const res = await fetch(`${API_BASE}/api/v1/lookups/projects/insert`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(projectCreateForm),
                  });
                  if (!res.ok) {
                    const detail = await res.json().catch(() => ({}));
                    throw new Error(detail.detail || `Create failed (${res.status})`);
                  }
                  const created = await res.json();
                  setProjects((prev) => [...prev, created]);
                  setProjectCreateForm({ project_name: "" });
                } catch (err) {
                  setProjectSaveError(err instanceof Error ? err.message : "Create failed");
                } finally {
                  setProjectSaving(false);
                }
              }}
            >
              {projectSaving ? "Saving…" : "Add"}
            </button>
          </div>
        </div>

        <div className="table">
          <div className="table-head">
            <span>ID</span>
            <span>Name</span>
            <span className="hide-on-small" />
            <span>Actions</span>
          </div>
          <div className="table-body">
            {projects.map((project) => (
              <div className="table-row" key={project.project_id}>
                <span>{project.project_id}</span>
                {projectEditingId === project.project_id ? (
                  <>
                    <input
                      className="input"
                      value={projectForm.project_name}
                      onChange={(e) =>
                        setProjectForm((f) => ({ ...f, project_name: e.target.value }))
                      }
                    />
                    <div />
                  </>
                ) : (
                  <>
                    <span>{project.project_name}</span>
                    <span className="hide-on-small" />
                  </>
                )}
                <span className="actions">
                  {projectEditingId === project.project_id ? (
                    <>
                      <button
                        className="btn"
                        disabled={projectSaving}
                        onClick={async () => {
                          setProjectSaveError("");
                          setProjectSaving(true);
                          try {
                            const res = await fetch(
                              `${API_BASE}/api/v1/lookups/projects/update`,
                              {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                  project_id: project.project_id,
                                  project_name: projectForm.project_name,
                                }),
                              },
                            );
                            if (!res.ok) {
                              const detail = await res.json().catch(() => ({}));
                              throw new Error(detail.detail || `Save failed (${res.status})`);
                            }
                            const updated = await res.json();
                            setProjects((prev) =>
                              prev.map((it) =>
                                it.project_id === project.project_id ? updated : it,
                              ),
                            );
                            setProjectEditingId(null);
                          } catch (err) {
                            setProjectSaveError(err instanceof Error ? err.message : "Save failed");
                          } finally {
                            setProjectSaving(false);
                          }
                        }}
                      >
                        {projectSaving ? "Saving…" : "Save"}
                      </button>
                      <button
                        className="btn btn-ghost"
                        disabled={projectSaving}
                        onClick={() => {
                          setProjectEditingId(null);
                          setProjectSaveError("");
                        }}
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        className="btn"
                        onClick={() => {
                          setProjectEditingId(project.project_id);
                          setProjectForm({ project_name: project.project_name });
                        }}
                      >
                        Edit
                      </button>
                      <button
                        className="btn btn-ghost"
                        disabled={projectSaving}
                        onClick={async () => {
                          setProjectSaveError("");
                          setProjectSaving(true);
                          try {
                            const res = await fetch(
                              `${API_BASE}/api/v1/lookups/projects/delete`,
                              {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ project_id: project.project_id }),
                              },
                            );
                            if (!res.ok) {
                              const detail = await res.json().catch(() => ({}));
                              throw new Error(detail.detail || `Delete failed (${res.status})`);
                            }
                            setProjects((prev) =>
                              prev.filter((it) => it.project_id !== project.project_id),
                            );
                          } catch (err) {
                            setProjectSaveError(err instanceof Error ? err.message : "Delete failed");
                          } finally {
                            setProjectSaving(false);
                          }
                        }}
                      >
                        Delete
                      </button>
                    </>
                  )}
                </span>
              </div>
            ))}
            {projectsLoading && (
              <div className="table-row muted">
                <span colSpan={4}>Fetching…</span>
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Units</h2>
          <span className="status">
            {unitsLoading ? "Loading…" : unitsError ? "Error" : "Ready"}
          </span>
        </div>

        {unitsError && <div className="alert alert-error">{unitsError}</div>}
        {unitSaveError && <div className="alert alert-error">{unitSaveError}</div>}
        {!unitsError && units.length === 0 && !unitsLoading && (
          <div className="alert">No units available</div>
        )}

        <div className="panel subpanel">
          <h3>Add unit</h3>
          <div className="create-row">
            <input
              className="input"
              placeholder="Unit name"
              value={unitCreateForm.unit_name}
              onChange={(e) => setUnitCreateForm((f) => ({ ...f, unit_name: e.target.value }))}
            />
            <div />
            <button
              className="btn"
              disabled={unitSaving || !unitCreateForm.unit_name}
              onClick={async () => {
                setUnitSaveError("");
                setUnitSaving(true);
                try {
                  const res = await fetch(`${API_BASE}/api/v1/lookups/units/insert`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(unitCreateForm),
                  });
                  if (!res.ok) {
                    const detail = await res.json().catch(() => ({}));
                    throw new Error(detail.detail || `Create failed (${res.status})`);
                  }
                  const created = await res.json();
                  setUnits((prev) => [...prev, created]);
                  setUnitCreateForm({ unit_name: "" });
                } catch (err) {
                  setUnitSaveError(err instanceof Error ? err.message : "Create failed");
                } finally {
                  setUnitSaving(false);
                }
              }}
            >
              {unitSaving ? "Saving…" : "Add"}
            </button>
          </div>
        </div>

        <div className="table">
          <div className="table-head">
            <span>ID</span>
            <span>Name</span>
            <span className="hide-on-small" />
            <span>Actions</span>
          </div>
          <div className="table-body">
            {units.map((unit) => (
              <div className="table-row" key={unit.unit_id}>
                <span>{unit.unit_id}</span>
                {unitEditingId === unit.unit_id ? (
                  <>
                    <input
                      className="input"
                      value={unitForm.unit_name}
                      onChange={(e) => setUnitForm((f) => ({ ...f, unit_name: e.target.value }))}
                    />
                    <div />
                  </>
                ) : (
                  <>
                    <span>{unit.unit_name}</span>
                    <span className="hide-on-small" />
                  </>
                )}
                <span className="actions">
                  {unitEditingId === unit.unit_id ? (
                    <>
                      <button
                        className="btn"
                        disabled={unitSaving}
                        onClick={async () => {
                          setUnitSaveError("");
                          setUnitSaving(true);
                          try {
                            const res = await fetch(`${API_BASE}/api/v1/lookups/units/update`, {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({
                                unit_id: unit.unit_id,
                                unit_name: unitForm.unit_name,
                              }),
                            });
                            if (!res.ok) {
                              const detail = await res.json().catch(() => ({}));
                              throw new Error(detail.detail || `Save failed (${res.status})`);
                            }
                            const updated = await res.json();
                            setUnits((prev) =>
                              prev.map((it) => (it.unit_id === unit.unit_id ? updated : it)),
                            );
                            setUnitEditingId(null);
                          } catch (err) {
                            setUnitSaveError(err instanceof Error ? err.message : "Save failed");
                          } finally {
                            setUnitSaving(false);
                          }
                        }}
                      >
                        {unitSaving ? "Saving…" : "Save"}
                      </button>
                      <button
                        className="btn btn-ghost"
                        disabled={unitSaving}
                        onClick={() => {
                          setUnitEditingId(null);
                          setUnitSaveError("");
                        }}
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        className="btn"
                        onClick={() => {
                          setUnitEditingId(unit.unit_id);
                          setUnitForm({ unit_name: unit.unit_name });
                        }}
                      >
                        Edit
                      </button>
                      <button
                        className="btn btn-ghost"
                        disabled={unitSaving}
                        onClick={async () => {
                          setUnitSaveError("");
                          setUnitSaving(true);
                          try {
                            const res = await fetch(`${API_BASE}/api/v1/lookups/units/delete`, {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({ unit_id: unit.unit_id }),
                            });
                            if (!res.ok) {
                              const detail = await res.json().catch(() => ({}));
                              throw new Error(detail.detail || `Delete failed (${res.status})`);
                            }
                            setUnits((prev) => prev.filter((it) => it.unit_id !== unit.unit_id));
                          } catch (err) {
                            setUnitSaveError(err instanceof Error ? err.message : "Delete failed");
                          } finally {
                            setUnitSaving(false);
                          }
                        }}
                      >
                        Delete
                      </button>
                    </>
                  )}
                </span>
              </div>
            ))}
            {unitsLoading && (
              <div className="table-row muted">
                <span colSpan={4}>Fetching…</span>
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Disciplines</h2>
          <span className="status">
            {disciplinesLoading ? "Loading…" : disciplinesError ? "Error" : "Ready"}
          </span>
        </div>

        {disciplinesError && <div className="alert alert-error">{disciplinesError}</div>}
        {discSaveError && <div className="alert alert-error">{discSaveError}</div>}
        {!disciplinesError && disciplines.length === 0 && !disciplinesLoading && (
          <div className="alert">No disciplines available</div>
        )}

        <div className="panel subpanel">
          <h3>Add discipline</h3>
          <div className="create-row">
            <input
              className="input"
              placeholder="Discipline name"
              value={discCreateForm.discipline_name}
              onChange={(e) =>
                setDiscCreateForm((f) => ({ ...f, discipline_name: e.target.value }))
              }
            />
            <input
              className="input"
              placeholder="Acronym"
              value={discCreateForm.discipline_acronym}
              onChange={(e) =>
                setDiscCreateForm((f) => ({ ...f, discipline_acronym: e.target.value }))
              }
            />
            <button
              className="btn"
              disabled={
                discSaving || !discCreateForm.discipline_name || !discCreateForm.discipline_acronym
              }
              onClick={async () => {
                setDiscSaveError("");
                setDiscSaving(true);
                try {
                  const res = await fetch(`${API_BASE}/api/v1/lookups/disciplines/insert`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(discCreateForm),
                  });
                  if (!res.ok) {
                    const detail = await res.json().catch(() => ({}));
                    throw new Error(detail.detail || `Create failed (${res.status})`);
                  }
                  const created = await res.json();
                  setDisciplines((prev) => [...prev, created]);
                  setDiscCreateForm({ discipline_name: "", discipline_acronym: "" });
                } catch (err) {
                  setDiscSaveError(err instanceof Error ? err.message : "Create failed");
                } finally {
                  setDiscSaving(false);
                }
              }}
            >
              {discSaving ? "Saving…" : "Add"}
            </button>
          </div>
        </div>

        <div className="table">
          <div className="table-head">
            <span>ID</span>
            <span>Name</span>
            <span>Acronym</span>
            <span>Actions</span>
          </div>
          <div className="table-body">
            {disciplines.map((discipline) => (
              <div className="table-row" key={discipline.discipline_id}>
                <span>{discipline.discipline_id}</span>
                {discEditingId === discipline.discipline_id ? (
                  <>
                    <input
                      className="input"
                      value={discForm.discipline_name}
                      onChange={(e) =>
                        setDiscForm((f) => ({ ...f, discipline_name: e.target.value }))
                      }
                    />
                    <input
                      className="input"
                      value={discForm.discipline_acronym}
                      onChange={(e) =>
                        setDiscForm((f) => ({ ...f, discipline_acronym: e.target.value }))
                      }
                    />
                  </>
                ) : (
                  <>
                    <span>{discipline.discipline_name}</span>
                    <span className="tag">{discipline.discipline_acronym}</span>
                  </>
                )}
                <span className="actions">
                  {discEditingId === discipline.discipline_id ? (
                    <>
                      <button
                        className="btn"
                        disabled={discSaving}
                        onClick={async () => {
                          setDiscSaveError("");
                          setDiscSaving(true);
                          try {
                            const res = await fetch(
                              `${API_BASE}/api/v1/lookups/disciplines/update`,
                              {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                  discipline_id: discipline.discipline_id,
                                  discipline_name: discForm.discipline_name,
                                  discipline_acronym: discForm.discipline_acronym,
                                }),
                              },
                            );
                            if (!res.ok) {
                              const detail = await res.json().catch(() => ({}));
                              throw new Error(detail.detail || `Save failed (${res.status})`);
                            }
                            const updated = await res.json();
                            setDisciplines((prev) =>
                              prev.map((it) =>
                                it.discipline_id === discipline.discipline_id ? updated : it,
                              ),
                            );
                            setDiscEditingId(null);
                          } catch (err) {
                            setDiscSaveError(err instanceof Error ? err.message : "Save failed");
                          } finally {
                            setDiscSaving(false);
                          }
                        }}
                      >
                        {discSaving ? "Saving…" : "Save"}
                      </button>
                      <button
                        className="btn btn-ghost"
                        disabled={discSaving}
                        onClick={() => {
                          setDiscEditingId(null);
                          setDiscSaveError("");
                        }}
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        className="btn"
                        onClick={() => {
                          setDiscEditingId(discipline.discipline_id);
                          setDiscForm({
                            discipline_name: discipline.discipline_name,
                            discipline_acronym: discipline.discipline_acronym,
                          });
                        }}
                      >
                        Edit
                      </button>
                      <button
                        className="btn btn-ghost"
                        disabled={discSaving}
                        onClick={async () => {
                          setDiscSaveError("");
                          setDiscSaving(true);
                          try {
                            const res = await fetch(
                              `${API_BASE}/api/v1/lookups/disciplines/delete`,
                              {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ discipline_id: discipline.discipline_id }),
                              },
                            );
                            if (!res.ok) {
                              const detail = await res.json().catch(() => ({}));
                              throw new Error(detail.detail || `Delete failed (${res.status})`);
                            }
                            setDisciplines((prev) =>
                              prev.filter((it) => it.discipline_id !== discipline.discipline_id),
                            );
                          } catch (err) {
                            setDiscSaveError(err instanceof Error ? err.message : "Delete failed");
                          } finally {
                            setDiscSaving(false);
                          }
                        }}
                      >
                        Delete
                      </button>
                    </>
                  )}
                </span>
              </div>
            ))}
            {disciplinesLoading && (
              <div className="table-row muted">
                <span colSpan={4}>Fetching…</span>
              </div>
            )}
          </div>
        </div>
          </section>
        </>
      ) : activeTab === "documents" ? (
        <section className="panel" id="docs-pane" role="tabpanel" aria-labelledby="docs-tab">
          <div className="panel-header">
            <h2>Documents / Revisions</h2>
            <span className="status">
              {docsLoading ? "Loading…" : docsError ? "Error" : `${docs.length} docs`}
            </span>
          </div>

          {docsError && <div className="alert alert-error">{docsError}</div>}
          {docTypesError && <div className="alert alert-error">{docTypesError}</div>}
          {jobpacksError && <div className="alert alert-error">{jobpacksError}</div>}
          {unitsError && <div className="alert alert-error">{unitsError}</div>}
          {error && <div className="alert alert-error">{error}</div>}
          {!docProjectId && (
            <div className="alert">Select a project to load documents.</div>
          )}
          {!docsError && docProjectId && docs.length === 0 && !docsLoading && (
            <div className="alert">No documents found for this project.</div>
          )}

          <div className="panel subpanel">
            <h3>Filter</h3>
            <div className="create-row doc-filter">
              <select
                className="input"
                value={docProjectId}
                onChange={(e) => {
                  const newVal = e.target.value;
                  setDocProjectId(newVal);
                  if (newVal) {
                    fetchDocs(Number(newVal));
                  } else {
                    setDocs([]);
                  }
                }}
              >
                <option value="">Select project</option>
                {projects.map((project) => (
                  <option key={project.project_id} value={project.project_id}>
                    {project.project_name}
                  </option>
                ))}
              </select>
              <button
                className="btn"
                disabled={!docProjectId || docsLoading}
                onClick={() => fetchDocs(Number(docProjectId))}
              >
                {docsLoading ? "Loading…" : "Refresh"}
              </button>
            </div>
          </div>

          <div className="table docs-table">
            <div className="table-head">
              <span>ID</span>
              <span>Name</span>
              <span>Title</span>
              <span>Type</span>
              <span>Discipline</span>
              <span>Jobpack</span>
              <span>Area</span>
              <span>Unit</span>
              <span>Current rev</span>
            </div>
            <div className="table-body">
              {docs.map((doc) => (
                <div className="table-row" key={doc.doc_id}>
                  <span>{doc.doc_id}</span>
                  <span className="tag">{doc.doc_name_uq || doc.doc_name_unique}</span>
                  <span>{doc.title}</span>
                  <span>
                    {doc.doc_type_name
                      ? `${doc.doc_type_name}${
                          doc.discipline_acronym ? ` (${doc.discipline_acronym})` : ""
                        }`
                      : docTypeById[doc.type_id]
                        ? `${docTypeById[doc.type_id].doc_type_name}${
                            docTypeById[doc.type_id].discipline_acronym
                              ? ` (${docTypeById[doc.type_id].discipline_acronym})`
                              : ""
                          }`
                        : `Type ${doc.type_id}`}
                  </span>
                  <span>
                    {doc.discipline_name
                      ? `${doc.discipline_name}${
                          doc.discipline_acronym ? ` (${doc.discipline_acronym})` : ""
                        }`
                      : docTypeById[doc.type_id]
                        ? `${docTypeById[doc.type_id].discipline_name || "Discipline"}${
                            docTypeById[doc.type_id].discipline_acronym
                              ? ` (${docTypeById[doc.type_id].discipline_acronym})`
                              : ""
                            }`
                        : "—"}
                  </span>
                  <span>
                    {doc.jobpack_name
                      ? doc.jobpack_name
                      : doc.jobpack_id
                        ? jobpackById[doc.jobpack_id] || `Jobpack ${doc.jobpack_id}`
                        : "—"}
                  </span>
                  <span>
                    {doc.area_name
                      ? `${doc.area_name}${doc.area_acronym ? ` (${doc.area_acronym})` : ""}`
                      : areaById[doc.area_id] || `Area ${doc.area_id}`}
                  </span>
                  <span>
                    {doc.unit_name ? doc.unit_name : unitById[doc.unit_id] || `Unit ${doc.unit_id}`}
                  </span>
                  <span>{doc.rev_current_id ?? "—"}</span>
                </div>
              ))}
          {docsLoading && (
            <div className="table-row muted">
                  <span colSpan={7}>Fetching…</span>
                </div>
              )}
            </div>
          </div>
        </section>
      ) : (
        <section className="panel" id="people-pane" role="tabpanel" aria-labelledby="people-tab">
          <div className="panel-header">
            <h2>Persons / Users</h2>
            <span className="status">
              {personsLoading ? "Loading…" : personsError ? "Error" : "Ready"}
            </span>
          </div>

          {personsError && <div className="alert alert-error">{personsError}</div>}
          {personSaveError && <div className="alert alert-error">{personSaveError}</div>}
          {!personsError && persons.length === 0 && !personsLoading && (
            <div className="alert">No persons available</div>
          )}

          <div className="panel subpanel">
            <h3>Add person</h3>
            <div className="create-row">
              <input
                className="input"
                placeholder="Person name"
                value={personCreateForm.person_name}
                onChange={(e) =>
                  setPersonCreateForm((f) => ({ ...f, person_name: e.target.value }))
                }
              />
              <input
                className="input"
                placeholder="Photo S3 UID (optional)"
                value={personCreateForm.photo_s3_uid}
                onChange={(e) =>
                  setPersonCreateForm((f) => ({ ...f, photo_s3_uid: e.target.value }))
                }
              />
              <button
                className="btn"
                disabled={personSaving || !personCreateForm.person_name}
                onClick={async () => {
                  setPersonSaveError("");
                  setPersonSaving(true);
                  try {
                    const res = await fetch(`${API_BASE}/api/v1/people/persons/insert`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({
                        person_name: personCreateForm.person_name,
                        photo_s3_uid:
                          personCreateForm.photo_s3_uid === ""
                            ? null
                            : personCreateForm.photo_s3_uid,
                      }),
                    });
                    if (!res.ok) {
                      const detail = await res.json().catch(() => ({}));
                      throw new Error(detail.detail || `Create failed (${res.status})`);
                    }
                    const created = await res.json();
                    setPersons((prev) => [...prev, created]);
                    setPersonCreateForm({ person_name: "", photo_s3_uid: "" });
                  } catch (err) {
                    setPersonSaveError(err instanceof Error ? err.message : "Create failed");
                  } finally {
                    setPersonSaving(false);
                  }
                }}
              >
                {personSaving ? "Saving…" : "Add"}
              </button>
            </div>
          </div>

          <div className="table">
            <div className="table-head">
              <span>ID</span>
              <span>Name</span>
              <span>Photo UID</span>
              <span>Actions</span>
            </div>
            <div className="table-body">
              {persons.map((person) => (
                <div className="table-row" key={person.person_id}>
                  <span>{person.person_id}</span>
                  {personEditingId === person.person_id ? (
                    <>
                      <input
                        className="input"
                        value={personForm.person_name}
                        onChange={(e) =>
                          setPersonForm((f) => ({ ...f, person_name: e.target.value }))
                        }
                      />
                      <input
                        className="input"
                        value={personForm.photo_s3_uid ?? ""}
                        onChange={(e) =>
                          setPersonForm((f) => ({ ...f, photo_s3_uid: e.target.value }))
                        }
                      />
                    </>
                  ) : (
                    <>
                      <span>{person.person_name}</span>
                      <span className="tag">
                        {person.photo_s3_uid === null || person.photo_s3_uid === undefined
                          ? "—"
                          : person.photo_s3_uid}
                      </span>
                    </>
                  )}
                  <span className="actions">
                    {personEditingId === person.person_id ? (
                      <>
                        <button
                          className="btn"
                          disabled={personSaving}
                          onClick={async () => {
                            setPersonSaveError("");
                            setPersonSaving(true);
                            try {
                              const res = await fetch(
                                `${API_BASE}/api/v1/people/persons/update`,
                                {
                                  method: "POST",
                                  headers: { "Content-Type": "application/json" },
                                  body: JSON.stringify({
                                    person_id: person.person_id,
                                    person_name: personForm.person_name,
                                    photo_s3_uid:
                                      personForm.photo_s3_uid === ""
                                        ? null
                                        : personForm.photo_s3_uid,
                                  }),
                                },
                              );
                              if (!res.ok) {
                                const detail = await res.json().catch(() => ({}));
                                throw new Error(detail.detail || `Save failed (${res.status})`);
                              }
                              const updated = await res.json();
                              setPersons((prev) =>
                                prev.map((it) =>
                                  it.person_id === person.person_id ? updated : it,
                                ),
                              );
                              setPersonEditingId(null);
                            } catch (err) {
                              setPersonSaveError(err instanceof Error ? err.message : "Save failed");
                            } finally {
                              setPersonSaving(false);
                            }
                          }}
                        >
                          {personSaving ? "Saving…" : "Save"}
                        </button>
                        <button
                          className="btn btn-ghost"
                          disabled={personSaving}
                          onClick={() => {
                            setPersonEditingId(null);
                            setPersonSaveError("");
                          }}
                        >
                          Cancel
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          className="btn"
                          onClick={() => {
                            setPersonEditingId(person.person_id);
                            setPersonForm({
                              person_name: person.person_name,
                              photo_s3_uid:
                                person.photo_s3_uid === null || person.photo_s3_uid === undefined
                                  ? ""
                                  : person.photo_s3_uid,
                            });
                          }}
                        >
                          Edit
                        </button>
                        <button
                          className="btn btn-ghost"
                          disabled={personSaving}
                          onClick={async () => {
                            setPersonSaveError("");
                            setPersonSaving(true);
                            try {
                              const res = await fetch(
                                `${API_BASE}/api/v1/people/persons/delete`,
                                {
                                  method: "POST",
                                  headers: { "Content-Type": "application/json" },
                                  body: JSON.stringify({ person_id: person.person_id }),
                                },
                              );
                              if (!res.ok) {
                                const detail = await res.json().catch(() => ({}));
                                throw new Error(detail.detail || `Delete failed (${res.status})`);
                              }
                              setPersons((prev) =>
                                prev.filter((it) => it.person_id !== person.person_id),
                              );
                            } catch (err) {
                              setPersonSaveError(
                                err instanceof Error ? err.message : "Delete failed",
                              );
                            } finally {
                              setPersonSaving(false);
                            }
                          }}
                        >
                          Delete
                        </button>
                      </>
                    )}
                  </span>
                </div>
              ))}
              {personsLoading && (
                <div className="table-row muted">
                  <span colSpan={4}>Fetching…</span>
                </div>
              )}
            </div>
          </div>

          <div className="panel subpanel">
            <h3>Users</h3>
            {usersError && <div className="alert alert-error">{usersError}</div>}
            {userSaveError && <div className="alert alert-error">{userSaveError}</div>}
            {!usersError && users.length === 0 && !usersLoading && (
              <div className="alert">No users available</div>
            )}

            <div className="create-row user-create">
              <select
                className="input"
                value={userCreateForm.person_id}
                onChange={(e) =>
                  setUserCreateForm((f) => ({ ...f, person_id: e.target.value }))
                }
              >
                <option value="">Select person</option>
                {availablePersons.map((person) => (
                  <option key={person.person_id} value={person.person_id}>
                    {person.person_name} (ID {person.person_id})
                  </option>
                ))}
              </select>
              <input
                className="input"
                placeholder="User acronym"
                value={userCreateForm.user_acronym}
                onChange={(e) =>
                  setUserCreateForm((f) => ({ ...f, user_acronym: e.target.value }))
                }
              />
              <select
                className="input"
                value={userCreateForm.role_id}
                onChange={(e) => setUserCreateForm((f) => ({ ...f, role_id: e.target.value }))}
              >
                <option value="">Select role</option>
                {roles.map((role) => (
                  <option key={role.role_id} value={role.role_id}>
                    {role.role_name}
                  </option>
                ))}
              </select>
              <button
                className="btn"
                disabled={
                  userSaving || !userCreateForm.person_id || !userCreateForm.user_acronym || !userCreateForm.role_id
                }
                onClick={async () => {
                  setUserSaveError("");
                  setUserSaving(true);
                  try {
                    const res = await fetch(`${API_BASE}/api/v1/people/users/insert`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({
                        person_id: Number(userCreateForm.person_id),
                        user_acronym: userCreateForm.user_acronym,
                        role_id: Number(userCreateForm.role_id),
                      }),
                    });
                    if (!res.ok) {
                      const detail = await res.json().catch(() => ({}));
                      throw new Error(detail.detail || `Create failed (${res.status})`);
                    }
                    const created = await res.json();
                    setUsers((prev) => [...prev, created]);
                    setUserCreateForm({ person_id: "", user_acronym: "", role_id: "" });
                  } catch (err) {
                    setUserSaveError(err instanceof Error ? err.message : "Create failed");
                  } finally {
                    setUserSaving(false);
                  }
                }}
              >
                {userSaving ? "Saving…" : "Add"}
              </button>
            </div>


            <div className="table users-table">
              <div className="table-head">
                <span>ID</span>
                <span>Person</span>
                <span>Acronym</span>
                <span>Role</span>
                <span>Actions</span>
              </div>
              <div className="table-body">
                {users.map((user) => {
                  const person = persons.find((p) => p.person_id === user.person_id);
                  const role = roles.find((r) => r.role_id === user.role_id);
                  return (
                    <div className="table-row" key={user.user_id}>
                      <span>{user.user_id}</span>
                      {userEditingId === user.user_id ? (
                        <>
                          <select
                            className="input"
                            value={userForm.person_id}
                            onChange={(e) =>
                              setUserForm((f) => ({ ...f, person_id: e.target.value }))
                            }
                          >
                            <option value="">Select person</option>
                            {[...availablePersons, person].filter(Boolean).map((p) => (
                              <option key={p.person_id} value={p.person_id}>
                                {p.person_name} (ID {p.person_id})
                              </option>
                            ))}
                          </select>
                          <input
                            className="input"
                            value={userForm.user_acronym}
                            onChange={(e) =>
                              setUserForm((f) => ({ ...f, user_acronym: e.target.value }))
                            }
                          />
                          <select
                            className="input"
                            value={userForm.role_id}
                            onChange={(e) => setUserForm((f) => ({ ...f, role_id: e.target.value }))}
                          >
                            <option value="">Select role</option>
                            {roles.map((r) => (
                              <option key={r.role_id} value={r.role_id}>
                                {r.role_name}
                              </option>
                            ))}
                          </select>
                        </>
                      ) : (
                        <>
                          <span>{person ? person.person_name : `Person ${user.person_id}`}</span>
                          <span className="tag">{user.user_acronym}</span>
                          <span className="tag">{role ? role.role_name : `Role ${user.role_id}`}</span>
                        </>
                      )}
                      <span className="actions">
                        {userEditingId === user.user_id ? (
                          <>
                            <button
                              className="btn"
                              disabled={userSaving}
                              onClick={async () => {
                                setUserSaveError("");
                                setUserSaving(true);
                                try {
                                  const res = await fetch(`${API_BASE}/api/v1/people/users/update`, {
                                    method: "POST",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({
                                      user_id: user.user_id,
                                      person_id:
                                        userForm.person_id === "" ? null : Number(userForm.person_id),
                                      user_acronym: userForm.user_acronym,
                                      role_id: userForm.role_id === "" ? null : Number(userForm.role_id),
                                    }),
                                  });
                                  if (!res.ok) {
                                    const detail = await res.json().catch(() => ({}));
                                    throw new Error(detail.detail || `Save failed (${res.status})`);
                                  }
                                  const updated = await res.json();
                                  setUsers((prev) =>
                                    prev.map((it) => (it.user_id === user.user_id ? updated : it)),
                                  );
                                  setUserEditingId(null);
                                } catch (err) {
                                  setUserSaveError(err instanceof Error ? err.message : "Save failed");
                                } finally {
                                  setUserSaving(false);
                                }
                              }}
                            >
                              {userSaving ? "Saving…" : "Save"}
                            </button>
                            <button
                              className="btn btn-ghost"
                              disabled={userSaving}
                              onClick={() => {
                                setUserEditingId(null);
                                setUserSaveError("");
                              }}
                            >
                              Cancel
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              className="btn"
                              onClick={() => {
                                setUserEditingId(user.user_id);
                                setUserForm({
                                  person_id: String(user.person_id),
                                  user_acronym: user.user_acronym,
                                  role_id: String(user.role_id),
                                });
                              }}
                            >
                              Edit
                            </button>
                            <button
                              className="btn btn-ghost"
                              disabled={userSaving}
                              onClick={async () => {
                                setUserSaveError("");
                                setUserSaving(true);
                                try {
                                  const res = await fetch(`${API_BASE}/api/v1/people/users/delete`, {
                                    method: "POST",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({ user_id: user.user_id }),
                                  });
                                  if (!res.ok) {
                                    const detail = await res.json().catch(() => ({}));
                                    throw new Error(detail.detail || `Delete failed (${res.status})`);
                                  }
                                  setUsers((prev) => prev.filter((it) => it.user_id !== user.user_id));
                                  fetchPermissions();
                                } catch (err) {
                                  setUserSaveError(err instanceof Error ? err.message : "Delete failed");
                                } finally {
                                  setUserSaving(false);
                                }
                              }}
                            >
                              Delete
                            </button>
                          </>
                        )}
                      </span>
                    </div>
                  );
                })}
                {usersLoading && (
                  <div className="table-row muted">
                    <span colSpan={5}>Fetching…</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="panel subpanel">
            <h3>Permissions</h3>
            {permissionsError && <div className="alert alert-error">{permissionsError}</div>}
            {permissionSaveError && <div className="alert alert-error">{permissionSaveError}</div>}
            {!permissionsError && permissions.length === 0 && !permissionsLoading && (
              <div className="alert">No permissions defined</div>
            )}

            <div className="create-row permission-create">
              <select
                className="input"
                value={permissionCreateForm.user_id}
                onChange={(e) =>
                  setPermissionCreateForm((f) => ({ ...f, user_id: e.target.value }))
                }
              >
                <option value="">Select user</option>
                {users.map((user) => {
                  const person = persons.find((p) => p.person_id === user.person_id);
                  return (
                    <option key={user.user_id} value={user.user_id}>
                      {user.user_acronym} — {person ? person.person_name : `Person ${user.person_id}`}
                    </option>
                  );
                })}
              </select>
              <select
                className="input"
                value={permissionCreateForm.project_id}
                onChange={(e) =>
                  setPermissionCreateForm((f) => ({ ...f, project_id: e.target.value }))
                }
              >
                <option value="">Any project</option>
                {projects.map((project) => (
                  <option key={project.project_id} value={project.project_id}>
                    {project.project_name}
                  </option>
                ))}
              </select>
              <select
                className="input"
                value={permissionCreateForm.discipline_id}
                onChange={(e) =>
                  setPermissionCreateForm((f) => ({ ...f, discipline_id: e.target.value }))
                }
              >
                <option value="">Any discipline</option>
                {disciplines.map((discipline) => (
                  <option key={discipline.discipline_id} value={discipline.discipline_id}>
                    {discipline.discipline_name}
                  </option>
                ))}
              </select>
              <button
                className="btn"
                disabled={
                  permissionSaving ||
                  !permissionCreateForm.user_id ||
                  (!permissionCreateForm.project_id && !permissionCreateForm.discipline_id)
                }
                onClick={async () => {
                  setPermissionSaveError("");
                  setPermissionSaving(true);
                  try {
                    const res = await fetch(`${API_BASE}/api/v1/people/permissions/insert`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({
                        user_id: Number(permissionCreateForm.user_id),
                        project_id:
                          permissionCreateForm.project_id === ""
                            ? null
                            : Number(permissionCreateForm.project_id),
                        discipline_id:
                          permissionCreateForm.discipline_id === ""
                            ? null
                            : Number(permissionCreateForm.discipline_id),
                      }),
                    });
                    if (!res.ok) {
                      const detail = await res.json().catch(() => ({}));
                      throw new Error(detail.detail || `Create failed (${res.status})`);
                    }
                    const created = await res.json();
                    setPermissions((prev) => [...prev, created]);
                    setPermissionCreateForm({ user_id: "", project_id: "", discipline_id: "" });
                  } catch (err) {
                    setPermissionSaveError(err instanceof Error ? err.message : "Create failed");
                  } finally {
                    setPermissionSaving(false);
                  }
                }}
              >
                {permissionSaving ? "Saving…" : "Add"}
              </button>
            </div>

            <div className="table permissions-table">
              <div className="table-head">
                <span>User</span>
                <span>Project</span>
                <span>Discipline</span>
                <span>Actions</span>
              </div>
              <div className="table-body">
                {permissions.map((perm) => {
                  const user = users.find((u) => u.user_id === perm.user_id);
                  const person = user ? persons.find((p) => p.person_id === user.person_id) : null;
                  const project = perm.project_id
                    ? projects.find((p) => p.project_id === perm.project_id)
                    : null;
                  const discipline = perm.discipline_id
                    ? disciplines.find((d) => d.discipline_id === perm.discipline_id)
                    : null;
                  const editingKey = `${perm.permission_id}`;
                  return (
                    <div className="table-row" key={perm.permission_id}>
                      <span>
                        {user ? user.user_acronym : `User ${perm.user_id}`}
                        {person ? ` (${person.person_name})` : ""}
                      </span>
                      <span>
                        {permissionEditingKey === editingKey ? (
                          <select
                            className="input"
                            value={permissionForm.project_id}
                            onChange={(e) =>
                              setPermissionForm((f) => ({ ...f, project_id: e.target.value }))
                            }
                          >
                            <option value="">Any project</option>
                            {projects.map((project) => (
                              <option key={project.project_id} value={project.project_id}>
                                {project.project_name}
                              </option>
                            ))}
                          </select>
                        ) : (
                          project ? project.project_name : "Any project"
                        )}
                      </span>
                      <span>
                        {permissionEditingKey === editingKey ? (
                          <select
                            className="input"
                            value={permissionForm.discipline_id}
                            onChange={(e) =>
                              setPermissionForm((f) => ({ ...f, discipline_id: e.target.value }))
                            }
                          >
                            <option value="">Any discipline</option>
                            {disciplines.map((discipline) => (
                              <option key={discipline.discipline_id} value={discipline.discipline_id}>
                                {discipline.discipline_name}
                              </option>
                            ))}
                          </select>
                        ) : (
                          discipline ? discipline.discipline_name : "Any discipline"
                        )}
                      </span>
                      <span className="actions">
                        {permissionEditingKey === editingKey ? (
                          <>
                            <button
                              className="btn"
                              disabled={permissionSaving}
                              onClick={async () => {
                                setPermissionSaveError("");
                                setPermissionSaving(true);
                                try {
                                  const res = await fetch(`${API_BASE}/api/v1/people/permissions/update`, {
                                    method: "POST",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({
                                      permission_id: perm.permission_id,
                                      user_id: perm.user_id,
                                      project_id: perm.project_id,
                                      discipline_id: perm.discipline_id,
                                      new_project_id:
                                        permissionForm.project_id === ""
                                          ? null
                                          : Number(permissionForm.project_id),
                                      new_discipline_id:
                                        permissionForm.discipline_id === ""
                                          ? null
                                          : Number(permissionForm.discipline_id),
                                    }),
                                  });
                                  if (!res.ok) {
                                    const detail = await res.json().catch(() => ({}));
                                    throw new Error(detail.detail || `Save failed (${res.status})`);
                                  }
                                  const updated = await res.json();
                                  setPermissions((prev) =>
                                    prev.map((p) =>
                                      p.user_id === perm.user_id &&
                                      p.project_id === perm.project_id &&
                                      p.discipline_id === perm.discipline_id
                                        ? updated
                                        : p,
                                    ),
                                  );
                                  setPermissionEditingKey(null);
                                } catch (err) {
                                  setPermissionSaveError(err instanceof Error ? err.message : "Save failed");
                                } finally {
                                  setPermissionSaving(false);
                                }
                              }}
                            >
                              {permissionSaving ? "Saving…" : "Save"}
                            </button>
                            <button
                              className="btn btn-ghost"
                              disabled={permissionSaving}
                              onClick={() => {
                                setPermissionEditingKey(null);
                                setPermissionSaveError("");
                              }}
                            >
                              Cancel
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              className="btn"
                              onClick={() => {
                                setPermissionEditingKey(editingKey);
                                setPermissionForm({
                                  project_id: perm.project_id === null ? "" : String(perm.project_id),
                                  discipline_id:
                                    perm.discipline_id === null ? "" : String(perm.discipline_id),
                                });
                              }}
                            >
                              Edit
                            </button>
                            <button
                        className="btn btn-ghost"
                        disabled={permissionSaving}
                        onClick={async () => {
                          setPermissionSaveError("");
                          setPermissionSaving(true);
                          try {
                            const res = await fetch(`${API_BASE}/api/v1/people/permissions/delete`, {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({
                                permission_id: perm.permission_id,
                                user_id: perm.user_id,
                                project_id: perm.project_id,
                                discipline_id: perm.discipline_id,
                              }),
                            });
                                  if (!res.ok) {
                                    const detail = await res.json().catch(() => ({}));
                                    throw new Error(detail.detail || `Delete failed (${res.status})`);
                                  }
                                  setPermissions((prev) =>
                                    prev.filter(
                                      (p) =>
                                        !(
                                          p.user_id === perm.user_id &&
                                          p.project_id === perm.project_id &&
                                          p.discipline_id === perm.discipline_id
                                        ),
                                    ),
                                  );
                                } catch (err) {
                                  setPermissionSaveError(err instanceof Error ? err.message : "Delete failed");
                                } finally {
                                  setPermissionSaving(false);
                                }
                              }}
                            >
                              Delete
                            </button>
                          </>
                        )}
                      </span>
                    </div>
                  );
                })}
                {permissionsLoading && (
                  <div className="table-row muted">
                    <span colSpan={4}>Fetching…</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
