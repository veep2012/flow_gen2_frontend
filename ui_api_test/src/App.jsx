import { useEffect, useMemo, useState } from "react";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:5556";

function useAreas() {
  const [areas, setAreas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        setLoading(true);
        const res = await fetch(`${API_BASE}/api/v1/lookups/areas`);
        if (!res.ok) {
          throw new Error(`API error ${res.status}`);
        }
        const data = await res.json();
        if (active) setAreas(data);
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, []);

  return { areas, loading, error };
}

export default function App() {
  const { areas, loading, error } = useAreas();
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
        {!error && areas.length === 0 && !loading && (
          <div className="alert">No areas available</div>
        )}

        <div className="table">
          <div className="table-head">
            <span>ID</span>
            <span>Name</span>
            <span>Acronym</span>
          </div>
          <div className="table-body">
            {areas.map((area) => (
              <div className="table-row" key={area.area_id}>
                <span>{area.area_id}</span>
                <span>{area.area_name}</span>
                <span className="tag">{area.area_acronym}</span>
              </div>
            ))}
            {loading && (
              <div className="table-row muted">
                <span colSpan={3}>Fetching…</span>
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
