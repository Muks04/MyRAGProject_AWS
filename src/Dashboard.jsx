import { useEffect, useState } from "react";

function Dashboard() {
  const [stats, setStats] = useState({
    daily_queries: 124,
    avg_latency: 1.23,
    daily_cost: "3.45",
    cache_hit_rate: 87,
  });

  return (
    <div style={{ padding: "2rem", maxWidth: "1200px", margin: "0 auto" }}>
      <h1 style={{ fontSize: "28px", marginBottom: "0.25rem" }}>
        Versicherungs‑Assistent Dashboard
      </h1>
      <p style={{ color: "#6E7681", marginBottom: "2rem" }}>
        Echtzeit‑Übersicht — Bayerische Versicherungsgesellschaft
      </p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: "1rem",
          marginBottom: "2rem",
        }}
      >
        {[
          { label: "Anfragen heute", value: stats.daily_queries },
          { label: "Ø Antwortzeit", value: `${stats.avg_latency}s` },
          { label: "Kosten heute", value: `$${stats.daily_cost}` },
          { label: "Cache‑Trefferrate", value: `${stats.cache_hit_rate}%` },
        ].map((item) => (
          <div
            key={item.label}
            style={{
              background: "#F6F8FA",
              border: "1px solid #D1D9E0",
              borderRadius: "10px",
              padding: "1.25rem",
            }}
          >
            <div style={{ fontSize: "13px", color: "#6E7681" }}>
              {item.label}
            </div>
            <div style={{ fontSize: "26px", marginTop: "4px" }}>
              {item.value}
            </div>
          </div>
        ))}
      </div>

      <div
        style={{
          background: "#F6F8FA",
          border: "1px solid #D1D9E0",
          borderRadius: "10px",
          padding: "1.25rem",
        }}
      >
        <h2 style={{ fontSize: "16px", marginBottom: "1rem" }}>
          Letzte Anfragen
        </h2>

        <p style={{ color: "#6E7681" }}>
          (API‑Integration kommt im nächsten Schritt)
        </p>
      </div>
    </div>
  );
}

export default Dashboard;
