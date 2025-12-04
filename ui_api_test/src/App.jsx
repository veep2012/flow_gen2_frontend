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

export default function App() {
  const { areas, loading, error, fetchAreas, setAreas } = useAreas();
  const [createForm, setCreateForm] = useState({ area_name: "", area_acronym: "" });
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({ area_name: "", area_acronym: "" });
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const header = useMemo(() => {
    if (loading) return "Loading areas…";
    if (error) return "Could not load areas";
    return `${areas.length} Areas`;
  }, [areas.length, loading, error]);

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
    </div>
  );
}
