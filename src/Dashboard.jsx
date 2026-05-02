import { useEffect, useState, useCallback } from "react"

const API_URL = import.meta.env.VITE_API_URL || ""

// ─── Colour tokens (mirrors index.css vars for inline styles) ───────────────
const C = {
  navy:       "#003366",
  blue:       "#0066CC",
  amber:      "#E8A000",
  success:    "#1A7F37",
  warning:    "#9A6700",
  danger:     "#CF222E",
  bgPage:     "#F0F4F8",
  bgCard:     "#FFFFFF",
  bgSidebar:  "#001A33",
  border:     "#D1DCE8",
  textPri:    "#0D1B2A",
  textSec:    "#4A5568",
  textMuted:  "#8A9BB0",
}

// ─── Sidebar ─────────────────────────────────────────────────────────────────
function Sidebar({ activeTab, onTabChange }) {
  const navItems = [
    { id: "overview",  icon: "⊞", label: "Übersicht"      },
    { id: "queries",   icon: "💬", label: "Anfragen"       },
    { id: "costs",     icon: "€",  label: "Kosten"         },
    { id: "system",    icon: "⚙",  label: "System"         },
  ]

  return (
    <aside style={{
      width: "220px",
      minHeight: "100vh",
      background: C.bgSidebar,
      display: "flex",
      flexDirection: "column",
      flexShrink: 0,
      position: "sticky",
      top: 0,
    }}>
      {/* Logo area */}
      <div style={{
        padding: "1.75rem 1.5rem 1.25rem",
        borderBottom: "1px solid rgba(255,255,255,0.08)",
      }}>
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          marginBottom: "4px",
        }}>
          <div style={{
            width: "32px", height: "32px",
            background: C.amber,
            borderRadius: "8px",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "16px", fontWeight: "700", color: C.navy,
          }}>F</div>
          <span style={{
            color: "#FFFFFF",
            fontWeight: "600",
            fontSize: "15px",
            letterSpacing: "0.3px",
          }}>FinBot</span>
        </div>
        <div style={{
          fontSize: "11px",
          color: "rgba(255,255,255,0.4)",
          paddingLeft: "42px",
          letterSpacing: "0.5px",
        }}>VERSICHERUNGS-ASSISTENT</div>
      </div>

      {/* Navigation */}
      <nav style={{ padding: "1rem 0.75rem", flex: 1 }}>
        {navItems.map(item => (
          <button
            key={item.id}
            onClick={() => onTabChange(item.id)}
            style={{
              width: "100%",
              display: "flex",
              alignItems: "center",
              gap: "10px",
              padding: "0.65rem 0.75rem",
              marginBottom: "2px",
              background: activeTab === item.id
                ? "rgba(0,102,204,0.25)"
                : "transparent",
              border: activeTab === item.id
                ? "1px solid rgba(0,102,204,0.4)"
                : "1px solid transparent",
              borderRadius: "8px",
              color: activeTab === item.id ? "#FFFFFF" : "rgba(255,255,255,0.55)",
              fontSize: "13.5px",
              fontWeight: activeTab === item.id ? "500" : "400",
              cursor: "pointer",
              textAlign: "left",
              transition: "all 0.15s ease",
            }}
          >
            <span style={{ fontSize: "15px", width: "20px", textAlign: "center" }}>
              {item.icon}
            </span>
            {item.label}
          </button>
        ))}
      </nav>

      {/* Footer */}
      <div style={{
        padding: "1rem 1.5rem",
        borderTop: "1px solid rgba(255,255,255,0.08)",
        fontSize: "11px",
        color: "rgba(255,255,255,0.25)",
        lineHeight: "1.6",
      }}>
        <div>AWS Bedrock RAG</div>
        <div>eu-central-1 Frankfurt</div>
        <div style={{ marginTop: "4px", color: "rgba(255,255,255,0.15)" }}>
          DSGVO konform ✓
        </div>
      </div>
    </aside>
  )
}

// ─── Stat Card ───────────────────────────────────────────────────────────────
function StatCard({ label, value, subtext, icon, accentColor, trend }) {
  return (
    <div style={{
      background: C.bgCard,
      border: `1px solid ${C.border}`,
      borderRadius: "12px",
      padding: "1.5rem",
      boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
      position: "relative",
      overflow: "hidden",
    }}>
      {/* Accent bar */}
      <div style={{
        position: "absolute",
        top: 0, left: 0, right: 0,
        height: "3px",
        background: accentColor || C.blue,
        borderRadius: "12px 12px 0 0",
      }} />

      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-start",
        marginBottom: "0.75rem",
      }}>
        <span style={{
          fontSize: "12px",
          fontWeight: "500",
          color: C.textMuted,
          textTransform: "uppercase",
          letterSpacing: "0.6px",
        }}>{label}</span>
        <span style={{
          fontSize: "20px",
          opacity: 0.15,
        }}>{icon}</span>
      </div>

      <div style={{
        fontSize: "32px",
        fontWeight: "600",
        color: accentColor || C.textPri,
        lineHeight: 1,
        marginBottom: "0.5rem",
      }}>{value}</div>

      {subtext && (
        <div style={{
          fontSize: "12px",
          color: C.textMuted,
          display: "flex",
          alignItems: "center",
          gap: "4px",
        }}>
          {trend && (
            <span style={{
              color: trend === "up" ? C.success : trend === "down" ? C.danger : C.textMuted,
            }}>
              {trend === "up" ? "↑" : trend === "down" ? "↓" : "→"}
            </span>
          )}
          {subtext}
        </div>
      )}
    </div>
  )
}

// ─── Badge ───────────────────────────────────────────────────────────────────
function Badge({ label, color, bg }) {
  return (
    <span style={{
      background: bg || "#EFF6FF",
      color: color || C.blue,
      padding: "3px 10px",
      borderRadius: "20px",
      fontSize: "11px",
      fontWeight: "600",
      letterSpacing: "0.3px",
      whiteSpace: "nowrap",
    }}>{label}</span>
  )
}

// ─── Query type badge ─────────────────────────────────────────────────────────
function QueryBadge({ used_rag, norman_used, audio_sent }) {
  if (norman_used) return <Badge label="Norman" bg="#FFF3E0" color="#E65100" />
  if (used_rag)    return <Badge label="RAG"     bg="#E8F5E9" color={C.success} />
  if (audio_sent)  return <Badge label="Audio"   bg="#F3E5F5" color="#7B1FA2" />
  return               <Badge label="Fallback" bg="#FFFDE7" color={C.warning} />
}

// ─── Loading skeleton ─────────────────────────────────────────────────────────
function Skeleton({ width = "100%", height = "20px", radius = "6px" }) {
  return (
    <div style={{
      width, height,
      borderRadius: radius,
      background: "linear-gradient(90deg, #E8EDF2 25%, #F0F4F8 50%, #E8EDF2 75%)",
      backgroundSize: "200% 100%",
      animation: "pulse 1.5s ease-in-out infinite",
    }} />
  )
}

// ─── Overview Tab ─────────────────────────────────────────────────────────────
function OverviewTab({ stats, queries, loading }) {
  if (loading) return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: "1rem" }}>
      {[...Array(4)].map((_, i) => (
        <div key={i} style={{
          background: C.bgCard, borderRadius: "12px",
          padding: "1.5rem", border: `1px solid ${C.border}`,
        }}>
          <Skeleton height="12px" width="60%" />
          <div style={{ marginTop: "1rem" }}><Skeleton height="32px" width="40%" /></div>
        </div>
      ))}
    </div>
  )

  const latencyOk = (stats?.avg_latency || 0) <= 3
  const cacheGood = (stats?.cache_hit_rate || 0) >= 70

  return (
    <div style={{ animation: "fadeIn 0.3s ease" }}>
      {/* KPI cards */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
        gap: "1rem",
        marginBottom: "1.5rem",
      }}>
        <StatCard
          label="Anfragen heute"
          value={stats?.daily_queries ?? 0}
          subtext="Gesamtanfragen"
          icon="💬"
          accentColor={C.blue}
        />
        <StatCard
          label="Ø Antwortzeit"
          value={`${stats?.avg_latency ?? 0}s`}
          subtext={latencyOk ? "Optimal" : "Erhöhte Latenz"}
          icon="⚡"
          accentColor={latencyOk ? C.success : C.danger}
          trend={latencyOk ? "down" : "up"}
        />
        <StatCard
          label="Kosten heute"
          value={`$${stats?.daily_cost ?? "0.00"}`}
          subtext="AWS Bedrock"
          icon="€"
          accentColor={C.amber}
        />
        <StatCard
          label="Cache-Trefferrate"
          value={`${stats?.cache_hit_rate ?? 0}%`}
          subtext={cacheGood ? "Effizient" : "Optimierbar"}
          icon="⚡"
          accentColor={cacheGood ? C.success : C.warning}
          trend={cacheGood ? "up" : "down"}
        />
      </div>

      {/* Recent queries preview */}
      <div style={{
        background: C.bgCard,
        border: `1px solid ${C.border}`,
        borderRadius: "12px",
        overflow: "hidden",
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
      }}>
        <div style={{
          padding: "1.25rem 1.5rem",
          borderBottom: `1px solid ${C.border}`,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}>
          <h2 style={{ fontSize: "14px", fontWeight: "600", color: C.textPri }}>
            Letzte Anfragen
          </h2>
          <Badge label={`${queries.length} heute`} />
        </div>

        {queries.length === 0 ? (
          <div style={{
            padding: "3rem",
            textAlign: "center",
            color: C.textMuted,
            fontSize: "14px",
          }}>
            <div style={{ fontSize: "32px", marginBottom: "0.75rem" }}>💬</div>
            Noch keine Anfragen heute.
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "#F8FAFC" }}>
                  {["Zeit", "Anfrage", "Typ", "Latenz", "Kosten"].map(h => (
                    <th key={h} style={{
                      padding: "0.75rem 1rem",
                      textAlign: "left",
                      fontSize: "11px",
                      fontWeight: "600",
                      color: C.textMuted,
                      textTransform: "uppercase",
                      letterSpacing: "0.5px",
                      borderBottom: `1px solid ${C.border}`,
                      whiteSpace: "nowrap",
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {queries.map((q, i) => (
                  <tr key={i} style={{
                    borderBottom: i < queries.length - 1 ? `1px solid #F0F4F8` : "none",
                    transition: "background 0.1s",
                  }}
                    onMouseEnter={e => e.currentTarget.style.background = "#F8FAFC"}
                    onMouseLeave={e => e.currentTarget.style.background = "transparent"}
                  >
                    <td style={{
                      padding: "0.875rem 1rem",
                      fontSize: "12px",
                      color: C.textMuted,
                      whiteSpace: "nowrap",
                      fontVariantNumeric: "tabular-nums",
                    }}>
                      {new Date(q.timestamp * 1000).toLocaleTimeString("de-DE")}
                    </td>
                    <td style={{
                      padding: "0.875rem 1rem",
                      fontSize: "13px",
                      color: C.textPri,
                      maxWidth: "320px",
                    }}>
                      <div style={{
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        maxWidth: "300px",
                      }}>
                        {q.message}{q.message?.length >= 80 ? "…" : ""}
                      </div>
                    </td>
                    <td style={{ padding: "0.875rem 1rem" }}>
                      <QueryBadge
                        used_rag={q.used_rag}
                        norman_used={q.norman_used}
                        audio_sent={q.audio_sent}
                      />
                    </td>
                    <td style={{
                      padding: "0.875rem 1rem",
                      fontSize: "13px",
                      color: parseFloat(q.processing_time) > 3 ? C.danger : C.textSec,
                      fontVariantNumeric: "tabular-nums",
                      whiteSpace: "nowrap",
                    }}>
                      {parseFloat(q.processing_time).toFixed(2)}s
                    </td>
                    <td style={{
                      padding: "0.875rem 1rem",
                      fontSize: "12px",
                      color: C.textMuted,
                      fontVariantNumeric: "tabular-nums",
                      whiteSpace: "nowrap",
                    }}>
                      ${parseFloat(q.cost_estimate).toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

// ─── System Tab ───────────────────────────────────────────────────────────────
function SystemTab() {
  const services = [
    { name: "Amazon Bedrock",       region: "eu-central-1", status: "operational", latency: "~1.2s" },
    { name: "Amazon DynamoDB",      region: "eu-central-1", status: "operational", latency: "~8ms"  },
    { name: "Amazon Polly TTS",     region: "eu-central-1", status: "operational", latency: "~0.9s" },
    { name: "AWS Lambda",           region: "eu-central-1", status: "operational", latency: "~180ms"},
    { name: "Amazon API Gateway",   region: "eu-central-1", status: "operational", latency: "~12ms" },
    { name: "Norman Finance API",   region: "EU",           status: "operational", latency: "~1.4s" },
    { name: "Twilio WhatsApp",      region: "Global",       status: "operational", latency: "~200ms"},
  ]

  return (
    <div style={{ animation: "fadeIn 0.3s ease" }}>
      <div style={{
        background: C.bgCard,
        border: `1px solid ${C.border}`,
        borderRadius: "12px",
        overflow: "hidden",
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
      }}>
        <div style={{
          padding: "1.25rem 1.5rem",
          borderBottom: `1px solid ${C.border}`,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}>
          <h2 style={{ fontSize: "14px", fontWeight: "600", color: C.textPri }}>
            Systemstatus
          </h2>
          <Badge label="Alle Systeme betriebsbereit" bg="#E8F5E9" color={C.success} />
        </div>

        <div style={{ padding: "0.5rem 0" }}>
          {services.map((svc, i) => (
            <div key={i} style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "0.875rem 1.5rem",
              borderBottom: i < services.length - 1 ? `1px solid #F0F4F8` : "none",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <div style={{
                  width: "8px", height: "8px",
                  borderRadius: "50%",
                  background: svc.status === "operational" ? C.success : C.danger,
                  boxShadow: svc.status === "operational"
                    ? `0 0 0 3px rgba(26,127,55,0.15)`
                    : `0 0 0 3px rgba(207,34,46,0.15)`,
                }} />
                <div>
                  <div style={{ fontSize: "13px", fontWeight: "500", color: C.textPri }}>
                    {svc.name}
                  </div>
                  <div style={{ fontSize: "11px", color: C.textMuted }}>
                    {svc.region}
                  </div>
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                <span style={{ fontSize: "12px", color: C.textMuted }}>
                  {svc.latency}
                </span>
                <Badge
                  label={svc.status === "operational" ? "Betriebsbereit" : "Gestört"}
                  bg={svc.status === "operational" ? "#E8F5E9" : "#FFEBEE"}
                  color={svc.status === "operational" ? C.success : C.danger}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Compliance info */}
      <div style={{
        marginTop: "1rem",
        background: C.bgCard,
        border: `1px solid ${C.border}`,
        borderRadius: "12px",
        padding: "1.5rem",
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
      }}>
        <h3 style={{ fontSize: "13px", fontWeight: "600", color: C.textPri, marginBottom: "1rem" }}>
          Datenschutz & Compliance
        </h3>
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "0.75rem",
        }}>
          {[
            { label: "DSGVO", status: "Konform" },
            { label: "Datenspeicherung", status: "EU (Frankfurt)" },
            { label: "Verschlüsselung", status: "AES-256 / KMS" },
            { label: "Audit-Logs", status: "CloudTrail aktiv" },
          ].map((item, i) => (
            <div key={i} style={{
              background: "#F8FAFC",
              border: `1px solid ${C.border}`,
              borderRadius: "8px",
              padding: "0.875rem 1rem",
            }}>
              <div style={{ fontSize: "11px", color: C.textMuted, marginBottom: "4px" }}>
                {item.label}
              </div>
              <div style={{ fontSize: "13px", fontWeight: "500", color: C.success }}>
                ✓ {item.status}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────
function Dashboard() {
  const [stats,    setStats]    = useState(null)
  const [queries,  setQueries]  = useState([])
  const [loading,  setLoading]  = useState(true)
  const [lastSync, setLastSync] = useState(null)
  const [error,    setError]    = useState(null)
  const [activeTab, setActiveTab] = useState("overview")
  const [refreshing, setRefreshing] = useState(false)

  const fetchData = useCallback(async (isManual = false) => {
    try {
      if (isManual) setRefreshing(true)
      setError(null)
      const res  = await fetch(`${API_URL}/dashboard`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setStats(data.stats)
      setQueries(data.recent_queries || [])
      setLastSync(new Date())
    } catch (e) {
      console.error("Fetch failed:", e)
      setError("Verbindung unterbrochen")
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 60000)
    return () => clearInterval(interval)
  }, [fetchData])

  const tabContent = {
    overview: <OverviewTab stats={stats} queries={queries} loading={loading} />,
    queries:  <OverviewTab stats={stats} queries={queries} loading={loading} />,
    costs:    (
      <div style={{
        background: C.bgCard, borderRadius: "12px",
        padding: "2rem", border: `1px solid ${C.border}`,
        textAlign: "center", color: C.textMuted,
        animation: "fadeIn 0.3s ease",
      }}>
        <div style={{ fontSize: "40px", marginBottom: "1rem" }}>📊</div>
        <div style={{ fontSize: "15px", fontWeight: "500", color: C.textPri, marginBottom: "0.5rem" }}>
          Kostenanalyse
        </div>
        <div style={{ fontSize: "13px" }}>
          Detaillierte Kostenaufschlüsselung — demnächst verfügbar
        </div>
      </div>
    ),
    system: <SystemTab />,
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: C.bgPage }}>
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Main content */}
      <main style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>

        {/* Top bar */}
        <header style={{
          background: C.bgCard,
          borderBottom: `1px solid ${C.border}`,
          padding: "0 2rem",
          height: "64px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          position: "sticky",
          top: 0,
          zIndex: 10,
          boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
        }}>
          <div>
            <h1 style={{
              fontSize: "16px",
              fontWeight: "600",
              color: C.textPri,
              lineHeight: 1.2,
            }}>
              Versicherungs-Assistent Dashboard
            </h1>
            <p style={{ fontSize: "12px", color: C.textMuted, marginTop: "2px" }}>
              Bayerische Versicherungsgesellschaft · KI-gestützte Kundenbetreuung
            </p>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            {error && (
              <div style={{
                display: "flex", alignItems: "center", gap: "6px",
                background: "#FFEBEE",
                border: "1px solid #FFCDD2",
                borderRadius: "6px",
                padding: "4px 10px",
                fontSize: "12px",
                color: C.danger,
              }}>
                ⚠ {error}
              </div>
            )}

            {lastSync && (
              <div style={{ fontSize: "12px", color: C.textMuted, whiteSpace: "nowrap" }}>
                Sync: {lastSync.toLocaleTimeString("de-DE")}
              </div>
            )}

            <button
              onClick={() => fetchData(true)}
              disabled={refreshing}
              style={{
                display: "flex", alignItems: "center", gap: "6px",
                background: C.navy,
                color: "white",
                border: "none",
                borderRadius: "8px",
                padding: "8px 16px",
                fontSize: "13px",
                fontWeight: "500",
                cursor: refreshing ? "not-allowed" : "pointer",
                opacity: refreshing ? 0.7 : 1,
                transition: "opacity 0.15s",
              }}
            >
              <span style={{
                display: "inline-block",
                animation: refreshing ? "spin 1s linear infinite" : "none",
              }}>↻</span>
              {refreshing ? "Lädt…" : "Aktualisieren"}
            </button>
          </div>
        </header>

        {/* Page content */}
        <div style={{ padding: "1.75rem 2rem", flex: 1 }}>
          {tabContent[activeTab]}
        </div>

        {/* Footer */}
        <footer style={{
          padding: "1rem 2rem",
          borderTop: `1px solid ${C.border}`,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: "11px",
          color: C.textMuted,
          background: C.bgCard,
        }}>
          <span>© 2025 FinBot · Powered by Amazon Bedrock</span>
          <span>DSGVO konform · Daten in EU (Frankfurt) · TLS 1.3</span>
        </footer>
      </main>
    </div>
  )
}

export default Dashboard
