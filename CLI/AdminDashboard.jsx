// /**
//  * PHANTOM — Admin Dashboard
//  */

// import { useState, useEffect } from "react";
// import { useWebSocket } from "../hooks/useWebSocket";
// import { api } from "../utils/api";
// import MetricCard from "../components/MetricCard";
// import LiveChart from "../components/LiveChart";
// import StatusBadge from "../components/StatusBadge";
// import DataTable from "../components/DataTable";
// import {
//   Activity,
//   Shield,
//   Ban,
//   Users,
//   Bug,
//   Brain,
//   AlertTriangle,
//   Plus,
//   Trash2,
//   Search,
//   Eye,
// } from "lucide-react";

// export default function AdminDashboard() {
//   const { events, stats, connected } = useWebSocket();
//   const [tab, setTab] = useState("overview");
//   const [dashData, setDashData] = useState(null);
//   const [blockedIps, setBlockedIps] = useState([]);
//   const [honeypotEvents, setHoneypotEvents] = useState([]);
//   const [predictions, setPredictions] = useState({});
//   const [logs, setLogs] = useState([]);
//   const [blockIp, setBlockIp] = useState("");
//   const [blockReason, setBlockReason] = useState("");

//   const fetchData = async () => {
//     const safe = async (fn) => {
//       try {
//         return await fn();
//       } catch {
//         return null;
//       }
//     };

//     const [dash, blocked, honeypot, preds, logData] = await Promise.all([
//       safe(() => api("/api/admin/dashboard", {}, true)),
//       safe(() => api("/api/admin/blocked-ips", {}, true)),
//       safe(() => api("/api/admin/honeypot", {}, true)),
//       safe(() => api("/api/admin/predictions", {}, true)),
//       safe(() => api("/api/logs?limit=50", {}, true)),
//     ]);

//     if (dash) setDashData(dash);
//     if (blocked) setBlockedIps(blocked.blocked_ips || []);
//     if (honeypot) setHoneypotEvents(honeypot.events || []);
//     if (preds) setPredictions(preds.predictions || {});
//     if (logData) setLogs(logData.logs || []);
//   };

//   useEffect(() => {
//     fetchData();
//     const interval = setInterval(fetchData, 8000);
//     return () => clearInterval(interval);
//   }, []);

//   const handleBlock = async () => {
//     if (!blockIp.trim()) return;
//     try {
//       await api("/api/admin/block-ip", {
//         method: "POST",
//         body: JSON.stringify({
//           ip_address: blockIp,
//           reason: blockReason || "Manual block",
//         }),
//       });
//       setBlockIp("");
//       setBlockReason("");
//       fetchData();
//     } catch (e) {
//       /* ignore */
//     }
//   };

//   const handleUnblock = async (ip) => {
//     try {
//       await api(`/api/admin/unblock-ip/${ip}`, { method: "DELETE" });
//       fetchData();
//     } catch (e) {
//       /* ignore */
//     }
//   };

//   const attackDist = dashData?.attack_distribution || {};

//   return (
//     <div>
//       <div className="page-header">
//         <div
//           style={{
//             display: "flex",
//             alignItems: "center",
//             justifyContent: "space-between",
//           }}
//         >
//           <div>
//             <h1>PHANTOM Admin</h1>
//             <p>Global security operations center</p>
//           </div>
//           <div className="status-indicator">
//             <div
//               className={`status-dot ${connected ? "operational" : ""}`}
//               style={!connected ? { background: "var(--status-attack)" } : {}}
//             />
//             <span>{connected ? "Live" : "Offline"}</span>
//           </div>
//         </div>
//       </div>

//       {/* Metrics */}
//       <div className="metrics-grid">
//         <MetricCard
//           icon={<Activity size={20} />}
//           value={stats.total_requests}
//           label="Total Requests"
//           color="var(--accent-blue)"
//         />
//         <MetricCard
//           icon={<Shield size={20} />}
//           value={stats.total_attacks}
//           label="Attacks Detected"
//           color="var(--status-attack)"
//         />
//         <MetricCard
//           icon={<Ban size={20} />}
//           value={stats.total_blocked}
//           label="IPs Blocked"
//           color="var(--accent-purple)"
//         />
//         <MetricCard
//           icon={<Users size={20} />}
//           value={dashData?.total_users || 0}
//           label="Total Users"
//           color="var(--accent-teal)"
//         />
//         <MetricCard
//           icon={<Bug size={20} />}
//           value={dashData?.honeypot_events || 0}
//           label="Honeypot Events"
//           color="var(--status-suspicious)"
//         />
//         <MetricCard
//           icon={<AlertTriangle size={20} />}
//           value={dashData?.total_alerts || 0}
//           label="Alerts"
//           color="#f97316"
//         />
//       </div>

//       {/* Tabs */}
//       <div className="tabs">
//         {["overview", "logs", "honeypot", "ips"].map((t) => (
//           <button
//             key={t}
//             className={`tab ${tab === t ? "active" : ""}`}
//             onClick={() => setTab(t)}
//           >
//             {t === "overview"
//               ? "Overview"
//               : t === "logs"
//                 ? "Logs"
//                 : t === "honeypot"
//                   ? "Honeypot"
//                   : "IP Management"}
//           </button>
//         ))}
//       </div>

//       {/* Overview Tab */}
//       {tab === "overview" && (
//         <>
//           <div className="two-col" style={{ marginBottom: "var(--space-lg)" }}>
//             <div className="card">
//               <div className="card-header">
//                 <h3>Live Traffic</h3>
//               </div>
//               <LiveChart events={events} />
//             </div>

//             <div className="card">
//               <div className="card-header">
//                 <h3>ML Predictions</h3>
//               </div>
//               <div style={{ padding: "var(--space-md) 0" }}>
//                 {Object.entries(predictions).map(([key, val]) => (
//                   <div
//                     key={key}
//                     style={{
//                       display: "flex",
//                       alignItems: "center",
//                       justifyContent: "space-between",
//                       padding: "10px var(--space-md)",
//                       borderBottom: "1px solid var(--border-primary)",
//                     }}
//                   >
//                     <div
//                       style={{
//                         display: "flex",
//                         alignItems: "center",
//                         gap: "8px",
//                       }}
//                     >
//                       <StatusBadge status={key} />
//                     </div>
//                     <div style={{ display: "flex", gap: "24px" }}>
//                       <span
//                         className="mono"
//                         style={{ color: "var(--text-primary)" }}
//                       >
//                         {val.count?.toLocaleString()}
//                       </span>
//                       <span
//                         className="mono"
//                         style={{
//                           color: "var(--text-muted)",
//                           fontSize: "0.8rem",
//                         }}
//                       >
//                         avg: {(val.avg_confidence * 100).toFixed(1)}%
//                       </span>
//                     </div>
//                   </div>
//                 ))}
//                 {Object.keys(predictions).length === 0 && (
//                   <div className="empty-state" style={{ padding: "24px" }}>
//                     <p>No predictions yet</p>
//                   </div>
//                 )}
//               </div>
//             </div>
//           </div>

//           {/* Attack Distribution */}
//           {Object.keys(attackDist).length > 0 && (
//             <div className="card" style={{ marginBottom: "var(--space-lg)" }}>
//               <div className="card-header">
//                 <h3>Attack Distribution</h3>
//               </div>
//               <div
//                 style={{
//                   display: "flex",
//                   flexWrap: "wrap",
//                   gap: "var(--space-md)",
//                   padding: "var(--space-sm) 0",
//                 }}
//               >
//                 {Object.entries(attackDist)
//                   .sort((a, b) => b[1] - a[1])
//                   .map(([type, count]) => (
//                     <div
//                       key={type}
//                       style={{
//                         background: "var(--bg-input)",
//                         borderRadius: "var(--radius-md)",
//                         padding: "12px 16px",
//                         minWidth: "140px",
//                       }}
//                     >
//                       <div
//                         style={{
//                           fontSize: "0.75rem",
//                           color: "var(--text-muted)",
//                           marginBottom: "4px",
//                         }}
//                       >
//                         {type}
//                       </div>
//                       <div
//                         style={{
//                           fontFamily: "var(--font-mono)",
//                           fontSize: "1.25rem",
//                           fontWeight: "600",
//                           color: "var(--status-attack)",
//                         }}
//                       >
//                         {count}
//                       </div>
//                     </div>
//                   ))}
//               </div>
//             </div>
//           )}

//           {/* Recent Alerts */}
//           {/* Recent Alerts (Under Overview Tab) */}
//           <div className="card">
//             <div className="card-header">
//               <h3>Recent Alerts</h3>
//             </div>
//             <DataTable
//               columns={[
//                 {
//                   key: "severity",
//                   label: "Severity",
//                   render: (val) => <StatusBadge status={val} />,
//                 },
//                 { key: "title", label: "Alert" },
//                 { key: "ip_address", label: "IP", mono: true },
//                 // --- NEW CDL COLUMNS ---
//                 {
//                   key: "cdl",
//                   label: "CDL Risk",
//                   render: (val) => (
//                     <div
//                       style={{
//                         display: "flex",
//                         alignItems: "center",
//                         gap: "8px",
//                       }}
//                     >
//                       <div
//                         style={{
//                           width: "40px",
//                           height: "6px",
//                           background: "var(--bg-input)",
//                           borderRadius: "3px",
//                           overflow: "hidden",
//                         }}
//                       >
//                         <div
//                           style={{
//                             width: `${(val?.risk_score || 0) * 100}%`,
//                             height: "100%",
//                             background:
//                               val?.risk_score > 0.7
//                                 ? "var(--status-attack)"
//                                 : "var(--accent-teal)",
//                           }}
//                         />
//                       </div>
//                       <span className="mono" style={{ fontSize: "0.75rem" }}>
//                         {val ? `${(val.risk_score * 100).toFixed(0)}%` : "0%"}
//                       </span>
//                     </div>
//                   ),
//                 },
//                 {
//                   key: "cdl",
//                   label: "Next Prediction",
//                   render: (val) => (
//                     <span
//                       style={{
//                         fontSize: "0.75rem",
//                         color: "var(--accent-purple)",
//                         fontWeight: "600",
//                       }}
//                     >
//                       {val?.prediction?.next_attack || "RECON"}
//                     </span>
//                   ),
//                 },
//                 // -----------------------
//                 { key: "action_taken", label: "Action" },
//                 {
//                   key: "timestamp",
//                   label: "Time",
//                   mono: true,
//                   render: (val) =>
//                     val ? new Date(val).toLocaleTimeString() : "—",
//                 },
//               ]}
//               data={dashData?.recent_alerts || []}
//               emptyMessage="No alerts yet"
//             />
//           </div>
//         </>
//       )}

//       {/* Logs Tab */}
//       {tab === "logs" && (
//         <div className="card">
//           <div className="card-header">
//             <h3>Request Logs</h3>
//             <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
//               Last 50
//             </span>
//           </div>
//           <DataTable
//             columns={[
//               { key: "ip_address", label: "IP", mono: true },
//               { key: "endpoint", label: "Endpoint" },
//               { key: "method", label: "Method" },
//               { key: "status_code", label: "Status", mono: true },
//               {
//                 key: "prediction",
//                 label: "Prediction",
//                 render: (val) => <StatusBadge status={val} />,
//               },
//               {
//                 key: "confidence",
//                 label: "Confidence",
//                 mono: true,
//                 render: (val) => (val ? `${(val * 100).toFixed(1)}%` : "—"),
//               },
//               {
//                 key: "attack_type",
//                 label: "Type",
//                 render: (val) => val || "—",
//               },
//               {
//                 key: "timestamp",
//                 label: "Time",
//                 mono: true,
//                 render: (val) =>
//                   val ? new Date(val).toLocaleTimeString() : "—",
//               },
//             ]}
//             data={logs}
//             emptyMessage="No logs yet"
//           />
//         </div>
//       )}

//       {/* Honeypot Tab */}
//       {tab === "honeypot" && (
//         <div className="card">
//           <div className="card-header">
//             <h3>
//               <Bug
//                 size={14}
//                 style={{ marginRight: "6px", display: "inline" }}
//               />
//               Honeypot Captured Events
//             </h3>
//             <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
//               {honeypotEvents.length} events
//             </span>
//           </div>
//           <DataTable
//             columns={[
//               { key: "ip_address", label: "IP", mono: true },
//               {
//                 key: "event_type",
//                 label: "Type",
//                 render: (val) => (
//                   <StatusBadge
//                     status={
//                       val === "login_attempt"
//                         ? "attack"
//                         : val === "sql_injection"
//                           ? "critical"
//                           : "suspicious"
//                     }
//                   />
//                 ),
//               },
//               { key: "endpoint", label: "Endpoint" },
//               { key: "method", label: "Method" },
//               {
//                 key: "payload",
//                 label: "Payload",
//                 render: (val) => (
//                   <code
//                     style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}
//                   >
//                     {val
//                       ? val.length > 50
//                         ? val.slice(0, 50) + "..."
//                         : val
//                       : "—"}
//                   </code>
//                 ),
//               },
//               {
//                 key: "captured_data",
//                 label: "Captured Info",
//                 render: (val) => (val ? val.slice(0, 60) : "—"),
//               },
//               {
//                 key: "timestamp",
//                 label: "Time",
//                 mono: true,
//                 render: (val) =>
//                   val ? new Date(val).toLocaleTimeString() : "—",
//               },
//             ]}
//             data={honeypotEvents}
//             emptyMessage="No honeypot events captured yet"
//           />
//         </div>
//       )}

//       {/* IP Management Tab */}
//       {tab === "ips" && (
//         <>
//           {/* Block IP form */}
//           <div className="card" style={{ marginBottom: "var(--space-lg)" }}>
//             <div className="card-header">
//               <h3>Block IP Address</h3>
//             </div>
//             <div
//               style={{
//                 display: "flex",
//                 gap: "var(--space-md)",
//                 alignItems: "flex-end",
//               }}
//             >
//               <div className="input-group" style={{ flex: 1, marginBottom: 0 }}>
//                 <label>IP Address</label>
//                 <input
//                   className="input"
//                   placeholder="192.168.1.100"
//                   value={blockIp}
//                   onChange={(e) => setBlockIp(e.target.value)}
//                 />
//               </div>
//               <div className="input-group" style={{ flex: 2, marginBottom: 0 }}>
//                 <label>Reason</label>
//                 <input
//                   className="input"
//                   placeholder="Reason for blocking"
//                   value={blockReason}
//                   onChange={(e) => setBlockReason(e.target.value)}
//                 />
//               </div>
//               <button
//                 className="btn btn-danger"
//                 onClick={handleBlock}
//                 style={{ height: "40px" }}
//               >
//                 <Ban size={14} /> Block
//               </button>
//             </div>
//           </div>

//           {/* Blocked IPs list */}
//           <div className="card">
//             <div className="card-header">
//               <h3>Active Blocked IPs</h3>
//               <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
//                 {blockedIps.length} active
//               </span>
//             </div>
//             <DataTable
//               columns={[
//                 { key: "ip_address", label: "IP Address", mono: true },
//                 { key: "reason", label: "Reason" },
//                 { key: "attack_type", label: "Attack Type" },
//                 {
//                   key: "confidence",
//                   label: "Confidence",
//                   mono: true,
//                   render: (val) => (val ? `${(val * 100).toFixed(0)}%` : "—"),
//                 },
//                 { key: "blocked_by", label: "Blocked By" },
//                 {
//                   key: "blocked_at",
//                   label: "Time",
//                   mono: true,
//                   render: (val) => (val ? new Date(val).toLocaleString() : "—"),
//                 },
//                 {
//                   key: "ip_address",
//                   label: "Action",
//                   render: (val) => (
//                     <button
//                       className="btn btn-secondary btn-sm"
//                       onClick={() => handleUnblock(val)}
//                     >
//                       Unblock
//                     </button>
//                   ),
//                 },
//               ]}
//               data={blockedIps}
//               emptyMessage="No blocked IPs"
//             />
//           </div>
//         </>
//       )}
//     </div>
//   );
// }

/**
 * PHANTOM — Admin Dashboard
 */

import { useState, useEffect } from "react";
import { useWebSocket } from "../hooks/useWebSocket";
import { api } from "../utils/api";
import MetricCard from "../components/MetricCard";
import LiveChart from "../components/LiveChart";
import StatusBadge from "../components/StatusBadge";
import DataTable from "../components/DataTable";
import {
  Activity,
  Shield,
  Ban,
  Users,
  Bug,
  Brain,
  AlertTriangle,
  Plus,
  Trash2,
  Search,
  Eye,
} from "lucide-react";

export default function AdminDashboard() {
  const { events, stats, connected } = useWebSocket();
  const [tab, setTab] = useState("overview");
  const [dashData, setDashData] = useState(null);
  const [blockedIps, setBlockedIps] = useState([]);
  const [honeypotEvents, setHoneypotEvents] = useState([]);
  const [predictions, setPredictions] = useState({});
  const [logs, setLogs] = useState([]);
  const [blockIp, setBlockIp] = useState("");
  const [blockReason, setBlockReason] = useState("");

  const fetchData = async () => {
    const safe = async (fn) => {
      try {
        return await fn();
      } catch {
        return null;
      }
    };

    const [dash, blocked, honeypot, preds, logData] = await Promise.all([
      safe(() => api("/api/admin/dashboard", {}, true)),
      safe(() => api("/api/admin/blocked-ips", {}, true)),
      safe(() => api("/api/admin/honeypot", {}, true)),
      safe(() => api("/api/admin/predictions", {}, true)),
      safe(() => api("/api/logs?limit=50", {}, true)),
    ]);

    if (dash) setDashData(dash);
    if (blocked) setBlockedIps(blocked.blocked_ips || []);
    if (honeypot) setHoneypotEvents(honeypot.events || []);
    if (preds) setPredictions(preds.predictions || {});
    if (logData) setLogs(logData.logs || []);
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleBlock = async () => {
    if (!blockIp.trim()) return;
    try {
      await api("/api/admin/block-ip", {
        method: "POST",
        body: JSON.stringify({
          ip_address: blockIp,
          reason: blockReason || "Manual block",
        }),
      });
      setBlockIp("");
      setBlockReason("");
      fetchData();
    } catch (e) {
      /* ignore */
    }
  };

  const handleUnblock = async (ip) => {
    try {
      await api(`/api/admin/unblock-ip/${ip}`, { method: "DELETE" });
      fetchData();
    } catch (e) {
      /* ignore */
    }
  };

  const attackDist = dashData?.attack_distribution || {};

  return (
    <div>
      <div className="page-header">
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div>
            <h1>PHANTOM Admin</h1>
            <p>Global security operations center</p>
          </div>
          <div className="status-indicator">
            <div
              className={`status-dot ${connected ? "operational" : ""}`}
              style={!connected ? { background: "var(--status-attack)" } : {}}
            />
            <span>{connected ? "Live" : "Offline"}</span>
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="metrics-grid">
        <MetricCard
          icon={<Activity size={20} />}
          value={stats.total_requests}
          label="Total Requests"
          color="var(--accent-blue)"
        />
        <MetricCard
          icon={<Shield size={20} />}
          value={stats.total_attacks}
          label="Attacks Detected"
          color="var(--status-attack)"
        />
        <MetricCard
          icon={<Ban size={20} />}
          value={stats.total_blocked}
          label="IPs Blocked"
          color="var(--accent-purple)"
        />
        <MetricCard
          icon={<Users size={20} />}
          value={dashData?.total_users || 0}
          label="Total Users"
          color="var(--accent-teal)"
        />
        <MetricCard
          icon={<Bug size={20} />}
          value={dashData?.honeypot_events || 0}
          label="Honeypot Events"
          color="var(--status-suspicious)"
        />
        <MetricCard
          icon={<AlertTriangle size={20} />}
          value={dashData?.total_alerts || 0}
          label="Alerts"
          color="#f97316"
        />
      </div>

      {/* Tabs */}
      <div className="tabs">
        {["overview", "logs", "honeypot", "ips"].map((t) => (
          <button
            key={t}
            className={`tab ${tab === t ? "active" : ""}`}
            onClick={() => setTab(t)}
          >
            {t === "overview"
              ? "Overview"
              : t === "logs"
                ? "Logs"
                : t === "honeypot"
                  ? "Honeypot"
                  : "IP Management"}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {tab === "overview" && (
        <>
          <div className="two-col" style={{ marginBottom: "var(--space-lg)" }}>
            <div className="card">
              <div className="card-header">
                <h3>Live Traffic</h3>
              </div>
              <LiveChart events={events} />
            </div>

            <div className="card">
              <div className="card-header">
                <h3>ML Predictions</h3>
              </div>
              <div style={{ padding: "var(--space-md) 0" }}>
                {Object.entries(predictions).map(([key, val]) => (
                  <div
                    key={key}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "10px var(--space-md)",
                      borderBottom: "1px solid var(--border-primary)",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                      }}
                    >
                      <StatusBadge status={key} />
                    </div>
                    <div style={{ display: "flex", gap: "24px" }}>
                      <span
                        className="mono"
                        style={{ color: "var(--text-primary)" }}
                      >
                        {val.count?.toLocaleString()}
                      </span>
                      <span
                        className="mono"
                        style={{
                          color: "var(--text-muted)",
                          fontSize: "0.8rem",
                        }}
                      >
                        avg: {(val.avg_confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
                {Object.keys(predictions).length === 0 && (
                  <div className="empty-state" style={{ padding: "24px" }}>
                    <p>No predictions yet</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Attack Distribution */}
          {Object.keys(attackDist).length > 0 && (
            <div className="card" style={{ marginBottom: "var(--space-lg)" }}>
              <div className="card-header">
                <h3>Attack Distribution</h3>
              </div>
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "var(--space-md)",
                  padding: "var(--space-sm) 0",
                }}
              >
                {Object.entries(attackDist)
                  .sort((a, b) => b[1] - a[1])
                  .map(([type, count]) => (
                    <div
                      key={type}
                      style={{
                        background: "var(--bg-input)",
                        borderRadius: "var(--radius-md)",
                        padding: "12px 16px",
                        minWidth: "140px",
                      }}
                    >
                      <div
                        style={{
                          fontSize: "0.75rem",
                          color: "var(--text-muted)",
                          marginBottom: "4px",
                        }}
                      >
                        {type}
                      </div>
                      <div
                        style={{
                          fontFamily: "var(--font-mono)",
                          fontSize: "1.25rem",
                          fontWeight: "600",
                          color: "var(--status-attack)",
                        }}
                      >
                        {count}
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Recent Alerts */}
          <div className="card">
            <div className="card-header">
              <h3>Recent Alerts</h3>
            </div>
            <DataTable
              columns={[
                {
                  key: "severity",
                  label: "Severity",
                  render: (val) => <StatusBadge status={val} />,
                },
                { key: "title", label: "Alert" },
                { key: "ip_address", label: "IP", mono: true },
                {
                  key: "cdl",
                  label: "CDL Risk",
                  render: (val) => (
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                      }}
                    >
                      <div
                        style={{
                          width: "40px",
                          height: "6px",
                          background: "var(--bg-input)",
                          borderRadius: "3px",
                          overflow: "hidden",
                        }}
                      >
                        <div
                          style={{
                            width: `${(val?.risk_score || 0) * 100}%`,
                            height: "100%",
                            background:
                              val?.risk_score > 0.7
                                ? "var(--status-attack)"
                                : "var(--accent-teal)",
                          }}
                        />
                      </div>
                      <span className="mono" style={{ fontSize: "0.75rem" }}>
                        {val ? `${(val.risk_score * 100).toFixed(0)}%` : "0%"}
                      </span>
                    </div>
                  ),
                },
                {
                  key: "cdl",
                  label: "Next Prediction",
                  render: (val) => (
                    <span
                      style={{
                        fontSize: "0.75rem",
                        color: "var(--accent-purple)",
                        fontWeight: "600",
                      }}
                    >
                      {val?.prediction?.next_attack || "RECON"}
                    </span>
                  ),
                },
                { key: "action_taken", label: "Action" },
                {
                  key: "timestamp",
                  label: "Time",
                  mono: true,
                  render: (val) =>
                    val ? new Date(val).toLocaleTimeString() : "—",
                },
              ]}
              data={dashData?.recent_alerts || []}
              emptyMessage="No alerts yet"
            />
          </div>
        </>
      )}

      {/* Logs Tab */}
      {tab === "logs" && (
        <div className="card">
          <div className="card-header">
            <h3>Request Logs</h3>
            <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
              Last 50
            </span>
          </div>
          <DataTable
            columns={[
              { key: "ip_address", label: "IP", mono: true },
              { key: "endpoint", label: "Endpoint" },
              {
                key: "cdl",
                label: "AI Context",
                render: (val) => (
                  <span
                    style={{
                      fontStyle: "italic",
                      fontSize: "0.75rem",
                      color: "var(--text-muted)",
                    }}
                  >
                    {val?.context || "Initial behavior analysis..."}
                  </span>
                ),
              },
              { key: "method", label: "Method" },
              { key: "status_code", label: "Status", mono: true },
              {
                key: "prediction",
                label: "Prediction",
                render: (val) => <StatusBadge status={val} />,
              },
              {
                key: "confidence",
                label: "Confidence",
                mono: true,
                render: (val) => (val ? `${(val * 100).toFixed(1)}%` : "—"),
              },
              {
                key: "attack_type",
                label: "Type",
                render: (val) => val || "—",
              },
              {
                key: "timestamp",
                label: "Time",
                mono: true,
                render: (val) =>
                  val ? new Date(val).toLocaleTimeString() : "—",
              },
            ]}
            data={logs}
            emptyMessage="No logs yet"
          />
        </div>
      )}

      {/* Honeypot Tab */}
      {tab === "honeypot" && (
        <div className="card">
          <div className="card-header">
            <h3>
              <Bug
                size={14}
                style={{ marginRight: "6px", display: "inline" }}
              />
              Honeypot Captured Events
            </h3>
            <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
              {honeypotEvents.length} events
            </span>
          </div>
          <DataTable
            columns={[
              { key: "ip_address", label: "IP", mono: true },
              {
                key: "event_type",
                label: "Type",
                render: (val) => (
                  <StatusBadge
                    status={
                      val === "login_attempt"
                        ? "attack"
                        : val === "sql_injection"
                          ? "critical"
                          : "suspicious"
                    }
                  />
                ),
              },
              { key: "endpoint", label: "Endpoint" },
              { key: "method", label: "Method" },
              {
                key: "payload",
                label: "Payload",
                render: (val) => (
                  <code
                    style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}
                  >
                    {val
                      ? val.length > 50
                        ? val.slice(0, 50) + "..."
                        : val
                      : "—"}
                  </code>
                ),
              },
              {
                key: "captured_data",
                label: "Captured Info",
                render: (val) => (val ? val.slice(0, 60) : "—"),
              },
              {
                key: "timestamp",
                label: "Time",
                mono: true,
                render: (val) =>
                  val ? new Date(val).toLocaleTimeString() : "—",
              },
            ]}
            data={honeypotEvents}
            emptyMessage="No honeypot events captured yet"
          />
        </div>
      )}

      {/* IP Management Tab */}
      {tab === "ips" && (
        <>
          {/* Block IP form */}
          <div className="card" style={{ marginBottom: "var(--space-lg)" }}>
            <div className="card-header">
              <h3>Block IP Address</h3>
            </div>
            <div
              style={{
                display: "flex",
                gap: "var(--space-md)",
                alignItems: "flex-end",
              }}
            >
              <div className="input-group" style={{ flex: 1, marginBottom: 0 }}>
                <label>IP Address</label>
                <input
                  className="input"
                  placeholder="192.168.1.100"
                  value={blockIp}
                  onChange={(e) => setBlockIp(e.target.value)}
                />
              </div>
              <div className="input-group" style={{ flex: 2, marginBottom: 0 }}>
                <label>Reason</label>
                <input
                  className="input"
                  placeholder="Reason for blocking"
                  value={blockReason}
                  onChange={(e) => setBlockReason(e.target.value)}
                />
              </div>
              <button
                className="btn btn-danger"
                onClick={handleBlock}
                style={{ height: "40px" }}
              >
                <Ban size={14} /> Block
              </button>
            </div>
          </div>

          {/* Blocked IPs list */}
          <div className="card">
            <div className="card-header">
              <h3>Active Blocked IPs</h3>
              <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                {blockedIps.length} active
              </span>
            </div>
            <DataTable
              columns={[
                { key: "ip_address", label: "IP Address", mono: true },
                { key: "reason", label: "Reason" },
                { key: "attack_type", label: "Attack Type" },
                {
                  key: "confidence",
                  label: "Confidence",
                  mono: true,
                  render: (val) => (val ? `${(val * 100).toFixed(0)}%` : "—"),
                },
                { key: "blocked_by", label: "Blocked By" },
                {
                  key: "blocked_at",
                  label: "Time",
                  mono: true,
                  render: (val) => (val ? new Date(val).toLocaleString() : "—"),
                },
                {
                  key: "ip_address",
                  label: "Action",
                  render: (val) => (
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleUnblock(val)}
                    >
                      Unblock
                    </button>
                  ),
                },
              ]}
              data={blockedIps}
              emptyMessage="No blocked IPs"
            />
          </div>
        </>
      )}
    </div>
  );
}
