import { useEffect, useMemo, useState } from "react";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:5556";

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

function useRoles() {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchRoles = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/api/v1/lookups/roles`);
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
  const { units, loading: unitsLoading, error: unitsError, fetchUnits, setUnits } = useUnits();
  const {
    jobpacks,
    loading: jobpacksLoading,
    error: jobpacksError,
    fetchJobpacks,
    setJobpacks,
  } = useJobpacks();
  const { roles, loading: rolesLoading, error: rolesError, fetchRoles, setRoles } = useRoles();
  const {
    milestones,
    loading: milestonesLoading,
    error: milestonesError,
    fetchMilestones,
    setMilestones,
  } = useMilestones();
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
  const [roleCreateForm, setRoleCreateForm] = useState({ role_id: "", role_name: "" });
  const [roleEditingId, setRoleEditingId] = useState(null);
  const [roleForm, setRoleForm] = useState({ role_id: "", role_name: "" });
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
    return `${areaLabel} • ${discLabel} • ${projectLabel} • ${unitLabel} • ${jobpackLabel} • ${roleLabel} • ${milestoneLabel}`;
  }, [
    areas.length,
    disciplines.length,
    projects.length,
    units.length,
    jobpacks.length,
    roles.length,
    milestones.length,
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
  ]);

  return (
    <div className="page">
      <div className="hero">
        <div>
          <p className="eyebrow">Flow Docs</p>
          <h1>Project lookups</h1>
          <p className="lede">
            Lightweight UI to inspect lookup tables served by the FastAPI backend.
          </p>
          <p className="hint">API base: {API_BASE}</p>
        </div>
        <div className="pill">{header}</div>
      </div>

      <section className="panel">
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
              placeholder="Role ID"
              type="number"
              value={roleCreateForm.role_id}
              onChange={(e) =>
                setRoleCreateForm((f) => ({ ...f, role_id: e.target.value ? Number(e.target.value) : "" }))
              }
            />
            <input
              className="input"
              placeholder="Role name"
              value={roleCreateForm.role_name}
              onChange={(e) => setRoleCreateForm((f) => ({ ...f, role_name: e.target.value }))}
            />
            <button
              className="btn"
              disabled={roleSaving || roleCreateForm.role_id === "" || !roleCreateForm.role_name}
              onClick={async () => {
                setRoleSaveError("");
                setRoleSaving(true);
                try {
                  const res = await fetch(`${API_BASE}/api/v1/lookups/roles/insert`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      role_id: Number(roleCreateForm.role_id),
                      role_name: roleCreateForm.role_name,
                    }),
                  });
                  if (!res.ok) {
                    const detail = await res.json().catch(() => ({}));
                    throw new Error(detail.detail || `Create failed (${res.status})`);
                  }
                  const created = await res.json();
                  setRoles((prev) => [...prev, created]);
                  setRoleCreateForm({ role_id: "", role_name: "" });
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
                            const res = await fetch(`${API_BASE}/api/v1/lookups/roles/update`, {
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
                          setRoleForm({ role_name: role.role_name, role_id: role.role_id });
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
                            const res = await fetch(`${API_BASE}/api/v1/lookups/roles/delete`, {
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
    </div>
  );
}
