import { useState, useEffect } from "react"
import { Amplify } from "aws-amplify"
import { withAuthenticator } from "@aws-amplify/ui-react"
import "@aws-amplify/ui-react/styles.css"

// Dashboard for Bavarian insurance firm admins
// Shows: daily queries, cost, top questions, user activity

function Dashboard() {
    const [stats,    setStats]    = useState(null)
    const [queries,  setQueries]  = useState([])
    const [loading,  setLoading]  = useState(true)

    useEffect(() => {
        fetchDashboardData()
        // Refresh every 5 minutes
        const interval = setInterval(fetchDashboardData, 300000)
        return () => clearInterval(interval)
    }, [])

    async function fetchDashboardData() {
        try {
            // Call your Lambda via API Gateway
            const res  = await fetch(
                `${process.env.REACT_APP_API_URL}/dashboard`,
                { headers: { Authorization: `Bearer ${await getToken()}` } }
            )
            const data = await res.json()
            setStats(data.stats)
            setQueries(data.recent_queries)
        } catch (e) {
            console.error("Dashboard fetch failed:", e)
        } finally {
            setLoading(false)
        }
    }

    if (loading) return (
        <div style={{ padding: "2rem", color: "var(--amplify-colors-font-primary)" }}>
            Lade Dashboard...
        </div>
    )

    return (
        <div style={{ padding: "2rem", maxWidth: "1200px", margin: "0 auto" }}>

            {/* Header */}
            <h1 style={{ fontSize: "24px", fontWeight: "500", marginBottom: "0.5rem" }}>
                Versicherungs-Assistent Dashboard
            </h1>
            <p style={{ color: "#6E7681", marginBottom: "2rem" }}>
                Echtzeit-Übersicht — Bayerische Versicherungsgesellschaft
            </p>

            {/* Stats cards */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)",
                          gap: "1rem", marginBottom: "2rem" }}>
                {[
                    { label: "Anfragen heute",    value: stats?.daily_queries  ?? 0,    unit: ""     },
                    { label: "Ø Antwortzeit",     value: stats?.avg_latency    ?? 0,    unit: "s"    },
                    { label: "Kosten heute",      value: `$${stats?.daily_cost ?? "0.00"}`, unit: "" },
                    { label: "Cache-Trefferrate", value: stats?.cache_hit_rate ?? "0",  unit: "%"    },
                ].map(({ label, value, unit }) => (
                    <div key={label} style={{
                        background: "#F6F8FA", border: "1px solid #D1D9E0",
                        borderRadius: "12px", padding: "1.25rem"
                    }}>
                        <div style={{ fontSize: "13px", color: "#6E7681", marginBottom: "0.5rem" }}>
                            {label}
                        </div>
                        <div style={{ fontSize: "28px", fontWeight: "500", color: "#232F3E" }}>
                            {value}{unit}
                        </div>
                    </div>
                ))}
            </div>

            {/* Recent queries table */}
            <div style={{
                background: "#F6F8FA", border: "1px solid #D1D9E0",
                borderRadius: "12px", padding: "1.25rem"
            }}>
                <h2 style={{ fontSize: "16px", fontWeight: "500", marginBottom: "1rem" }}>
                    Letzte Anfragen
                </h2>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead>
                        <tr style={{ borderBottom: "1px solid #D1D9E0" }}>
                            {["Zeit", "Anfrage", "Antworttyp", "Latenz", "Kosten"].map(h => (
                                <th key={h} style={{
                                    textAlign: "left", padding: "0.75rem 0.5rem",
                                    fontSize: "13px", color: "#6E7681", fontWeight: "500"
                                }}>{h}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {queries.map((q, i) => (
                            <tr key={i} style={{ borderBottom: "1px solid #EEF0F2" }}>
                                <td style={{ padding: "0.75rem 0.5rem", fontSize: "13px", color: "#6E7681" }}>
                                    {new Date(q.timestamp * 1000).toLocaleTimeString("de-DE")}
                                </td>
                                <td style={{ padding: "0.75rem 0.5rem", fontSize: "14px", maxWidth: "280px" }}>
                                    {q.message.substring(0, 60)}{q.message.length > 60 ? "..." : ""}
                                </td>
                                <td style={{ padding: "0.75rem 0.5rem" }}>
                                    <span style={{
                                        background: q.used_rag ? "#DCFCE7" : "#FFF8C5",
                                        color:      q.used_rag ? "#1A7F37" : "#9A6700",
                                        padding: "2px 8px", borderRadius: "12px",
                                        fontSize: "12px", fontWeight: "500"
                                    }}>
                                        {q.used_rag ? "RAG" : "Fallback"}
                                    </span>
                                </td>
                                <td style={{ padding: "0.75rem 0.5rem", fontSize: "13px" }}>
                                    {parseFloat(q.processing_time).toFixed(2)}s
                                </td>
                                <td style={{ padding: "0.75rem 0.5rem", fontSize: "13px", color: "#6E7681" }}>
                                    ${parseFloat(q.cost_estimate).toFixed(4)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}

export default withAuthenticator(Dashboard)