import { useEffect, useState } from "react"

const API_URL = import.meta.env.VITE_API_URL || ""

function StatCard({ label, value, color }) {
    return (
        <div style={{
            background: "#F6F8FA",
            border: "1px solid #D1D9E0",
            borderRadius: "12px",
            padding: "1.5rem"
        }}>
            <div style={{ fontSize: "13px", color: "#6E7681",
                          marginBottom: "0.5rem" }}>
                {label}
            </div>
            <div style={{ fontSize: "28px", fontWeight: "500",
                          color: color || "#232F3E" }}>
                {value}
            </div>
        </div>
    )
}

function StatusBadge({ used_rag }) {
    return (
        <span style={{
            background: used_rag ? "#DCFCE7" : "#FFF8C5",
            color:      used_rag ? "#1A7F37" : "#9A6700",
            padding: "2px 10px",
            borderRadius: "12px",
            fontSize: "12px",
            fontWeight: "500"
        }}>
            {used_rag ? "RAG" : "Fallback"}
        </span>
    )
}

function Dashboard() {
    const [stats,    setStats]    = useState(null)
    const [queries,  setQueries]  = useState([])
    const [loading,  setLoading]  = useState(true)
    const [lastSync, setLastSync] = useState(null)
    const [error,    setError]    = useState(null)

    async function fetchData() {
        try {
            setError(null)
            const res  = await fetch(`${API_URL}/dashboard`)
            
            if (!res.ok) throw new Error(`HTTP ${res.status}`)
            
            const data = await res.json()
            setStats(data.stats)
            setQueries(data.recent_queries || [])
            setLastSync(new Date())
        } catch (e) {
            console.error("Fetch failed:", e)
            setError("Verbindung zum Server unterbrochen")
            // Keep showing last known data — do not blank the screen
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchData()
        // Auto-refresh every 60 seconds
        const interval = setInterval(fetchData, 60000)
        return () => clearInterval(interval)
    }, [])

    if (loading) return (
        <div style={{ padding: "3rem", textAlign: "center", color: "#6E7681" }}>
            Lade Dashboard...
        </div>
    )

    return (
        <div style={{ padding: "2rem", maxWidth: "1200px",
                      margin: "0 auto", fontFamily: "system-ui, sans-serif" }}>

            {/* Header */}
            <div style={{ display: "flex", justifyContent: "space-between",
                          alignItems: "flex-start", marginBottom: "2rem" }}>
                <div>
                    <h1 style={{ fontSize: "26px", fontWeight: "500",
                                 marginBottom: "0.25rem", color: "#232F3E" }}>
                        Versicherungs-Assistent Dashboard
                    </h1>
                    <p style={{ color: "#6E7681", fontSize: "14px" }}>
                        Echtzeit-Übersicht — Bayerische Versicherungsgesellschaft
                    </p>
                </div>
                <div style={{ textAlign: "right" }}>
                    {error && (
                        <div style={{ fontSize: "12px", color: "#CF222E",
                                      marginBottom: "4px" }}>
                            ⚠ {error}
                        </div>
                    )}
                    {lastSync && (
                        <div style={{ fontSize: "12px", color: "#6E7681" }}>
                            Aktualisiert: {lastSync.toLocaleTimeString("de-DE")}
                        </div>
                    )}
                    <button onClick={fetchData} style={{
                        marginTop: "6px",
                        background: "#FF9900", color: "white",
                        border: "none", borderRadius: "6px",
                        padding: "6px 14px", fontSize: "12px",
                        cursor: "pointer"
                    }}>
                        Aktualisieren
                    </button>
                </div>
            </div>

            {/* Stats grid */}
            <div style={{ display: "grid",
                          gridTemplateColumns: "repeat(4, 1fr)",
                          gap: "1rem", marginBottom: "2rem" }}>
                <StatCard
                    label="Anfragen heute"
                    value={stats?.daily_queries ?? 0}
                    color="#232F3E"
                />
                <StatCard
                    label="Ø Antwortzeit"
                    value={`${stats?.avg_latency ?? 0}s`}
                    color={stats?.avg_latency > 3 ? "#CF222E" : "#1A7F37"}
                />
                <StatCard
                    label="Kosten heute"
                    value={`$${stats?.daily_cost ?? "0.00"}`}
                    color="#232F3E"
                />
                <StatCard
                    label="Cache-Trefferrate"
                    value={`${stats?.cache_hit_rate ?? 0}%`}
                    color={stats?.cache_hit_rate > 70 ? "#1A7F37" : "#9A6700"}
                />
            </div>

            {/* Recent queries table */}
            <div style={{
                background: "#F6F8FA",
                border: "1px solid #D1D9E0",
                borderRadius: "12px",
                padding: "1.5rem"
            }}>
                <h2 style={{ fontSize: "16px", fontWeight: "500",
                             marginBottom: "1rem", color: "#232F3E" }}>
                    Letzte Anfragen
                </h2>

                {queries.length === 0 ? (
                    <p style={{ color: "#6E7681", fontSize: "14px" }}>
                        Noch keine Anfragen heute.
                    </p>
                ) : (
                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                        <thead>
                            <tr style={{ borderBottom: "1px solid #D1D9E0" }}>
                                {["Zeit", "Anfrage", "Typ",
                                  "Latenz", "Kosten"].map(h => (
                                    <th key={h} style={{
                                        textAlign: "left",
                                        padding: "0.5rem",
                                        fontSize: "12px",
                                        color: "#6E7681",
                                        fontWeight: "500"
                                    }}>{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {queries.map((q, i) => (
                                <tr key={i} style={{
                                    borderBottom: "1px solid #EEF0F2"
                                }}>
                                    <td style={{ padding: "0.75rem 0.5rem",
                                                 fontSize: "13px",
                                                 color: "#6E7681",
                                                 whiteSpace: "nowrap" }}>
                                        {new Date(q.timestamp * 1000)
                                            .toLocaleTimeString("de-DE")}
                                    </td>
                                    <td style={{ padding: "0.75rem 0.5rem",
                                                 fontSize: "14px",
                                                 maxWidth: "320px" }}>
                                        {q.message}
                                        {q.message?.length >= 80 ? "..." : ""}
                                    </td>
                                    <td style={{ padding: "0.75rem 0.5rem" }}>
                                        <StatusBadge used_rag={q.used_rag} />
                                    </td>
                                    <td style={{ padding: "0.75rem 0.5rem",
                                                 fontSize: "13px" }}>
                                        {parseFloat(q.processing_time)
                                            .toFixed(2)}s
                                    </td>
                                    <td style={{ padding: "0.75rem 0.5rem",
                                                 fontSize: "13px",
                                                 color: "#6E7681" }}>
                                        ${parseFloat(q.cost_estimate)
                                            .toFixed(4)}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Footer */}
            <div style={{ marginTop: "1.5rem", textAlign: "center",
                          fontSize: "12px", color: "#6E7681" }}>
                AWS Bedrock RAG · eu-central-1 Frankfurt · GDPR konform
            </div>
        </div>
    )
}

export default Dashboard
