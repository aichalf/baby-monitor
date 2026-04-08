import { useEffect, useState } from "react";
import "./index.css";

const fallbackData = {
  babyTemp: 0,
  heartRate: 0,
  movement: "En attente",
  movementLevel: 0,
  state: "NORMAL",
  message: "En attente de données STM32.",
  connected: false,
  source: "default"
};

const TempIcon = () => (
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/>
  </svg>
);

const HeartIcon = () => (
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
  </svg>
);

const MoveIcon = () => (
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="2"/>
    <path d="M12 2v3m0 14v3M4.22 4.22l2.12 2.12m11.32 11.32 2.12 2.12M2 12h3m14 0h3M4.22 19.78l2.12-2.12m11.32-11.32 2.12-2.12"/>
  </svg>
);

const AlertIcon = () => (
  <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
    <line x1="12" y1="9" x2="12" y2="13"/>
    <line x1="12" y1="17" x2="12.01" y2="17"/>
  </svg>
);

const CheckIcon = () => (
  <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
    <polyline points="22 4 12 14.01 9 11.01"/>
  </svg>
);

function getTempStatus(temp) {
  if (temp === 0) return "no-data";
  if (temp < 36.0 || temp > 37.5) return "warning";
  return "normal";
}

function getHRStatus(hr) {
  if (hr === 0) return "no-data";
  if (hr < 100 || hr > 160) return "warning";
  return "normal";
}

function formatTime(date) {
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function App() {
  const [data, setData] = useState(fallbackData);
  const [error, setError] = useState("");
  const [lastUpdate, setLastUpdate] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/data");
        if (!res.ok) throw new Error("Erreur API");
        const json = await res.json();
        setData(json);
        setLastUpdate(new Date());
        setError("");
      } catch {
        setError("Backend non connecté — mode simulation actif");
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const clock = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(clock);
  }, []);

  const isEmergency = data.state === "EMERGENCY";
  const tempStatus = getTempStatus(data.babyTemp);
  const hrStatus = getHRStatus(data.heartRate);

  return (
    <div className={`app-shell${isEmergency ? " emergency-mode" : ""}`}>
      <nav className="topnav">
        <div className="nav-brand">
          <div className="nav-logo">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
          </div>
          <div>
            <span className="nav-name">BabySafe</span>
            <span className="nav-tag">Infant Care Platform</span>
          </div>
        </div>

        <div className="nav-center">
          <div className={`nav-status-pill${isEmergency ? " danger" : " safe"}`}>
            <span className="pulse-dot"></span>
            <span>{isEmergency ? "ALERT ACTIVE" : "All Systems Normal"}</span>
          </div>
        </div>

        <div className="nav-right">
          {data.connected && (
            <span className="hw-badge">
              <span className="hw-dot"></span>
              STM32 Online
            </span>
          )}
          <div className="time-display">
            <div className="time-main">{formatTime(currentTime)}</div>
            {lastUpdate && (
              <div className="time-sub">Updated {formatTime(lastUpdate)}</div>
            )}
          </div>
        </div>
      </nav>

      <main className="main">
        {error && (
          <div className="error-banner">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            {error}
          </div>
        )}

        <div className="page-header">
          <div>
            <h1 className="page-title">BabySafe Dashboard</h1>
            <p className="page-sub">Real-time vitals and system assessment dashboard</p>
          </div>
          <div className="header-meta">
            <div className="meta-item">
              <span>Hardware</span>
              <strong className={data.connected ? "val-green" : ""}>{data.connected ? "STM32 Online" : "Simulation"}</strong>
            </div>
            <div className="meta-item">
              <span>Motion</span>
              <strong>{data.movementLevel ?? 0}%</strong>
            </div>
            <div className="meta-item">
              <span>Source</span>
              <strong>{data.source}</strong>
            </div>
          </div>
        </div>

        <div className={`alert-hero${isEmergency ? " emergency" : " normal"}`}>
          <div className="alert-hero-icon">
            {isEmergency ? <AlertIcon /> : <CheckIcon />}
          </div>
          <div className="alert-hero-body">
            <div className="alert-hero-eyebrow">Live Assessment</div>
            <h2 className="alert-hero-title">
              {isEmergency ? "Emergency Detected" : "Patient Status Normal"}
            </h2>
            <p className="alert-hero-msg">{data.message}</p>
          </div>
          <div className="alert-hero-badge">
            {isEmergency ? "Requires Attention" : "Monitoring Active"}
          </div>
        </div>

        <div className="metrics-row">
          <div className={`metric-card${tempStatus === "warning" ? " metric-warn" : ""}`}>
            <div className="metric-card-top">
              <div className={`metric-icon temp-icon ${tempStatus}`}>
                <TempIcon />
              </div>
              <div className="metric-chip-wrap">
                <span className="metric-label">Body Temperature</span>
                <span className={`metric-status-chip ${tempStatus}`}>
                  {tempStatus === "no-data" ? "No Data" : tempStatus === "warning" ? "Out of Range" : "Normal"}
                </span>
              </div>
            </div>
            <div className="metric-value">{data.babyTemp === 0 ? "—" : data.babyTemp}</div>
            <div className="metric-unit">°C</div>
            <div className="metric-range">Normal range: 36.0 – 37.5 °C</div>
          </div>

          <div className={`metric-card${hrStatus === "warning" ? " metric-warn" : ""}`}>
            <div className="metric-card-top">
              <div className={`metric-icon heart-icon ${hrStatus}`}>
                <HeartIcon />
              </div>
              <div className="metric-chip-wrap">
                <span className="metric-label">Heart Rate</span>
                <span className={`metric-status-chip ${hrStatus}`}>
                  {hrStatus === "no-data" ? "No Contact" : hrStatus === "warning" ? "Out of Range" : "Normal"}
                </span>
              </div>
            </div>
            <div className="metric-value">{data.heartRate === 0 ? "—" : data.heartRate}</div>
            <div className="metric-unit">bpm</div>
            <div className="metric-range">Normal infant: 100 – 160 bpm</div>
          </div>

          <div className="metric-card">
            <div className="metric-card-top">
              <div className="metric-icon move-icon">
                <MoveIcon />
              </div>
              <div className="metric-chip-wrap">
                <span className="metric-label">Movement</span>
                <span className="metric-status-chip normal">Sensor Active</span>
              </div>
            </div>
            <div className="metric-value movement-text">{data.movement}</div>
            <div className="metric-unit">&nbsp;</div>
            <div className="metric-range">Motion level: {data.movementLevel ?? 0}%</div>
          </div>
        </div>

        <div className="lower-row">
          <div className="detail-card">
            <div className="detail-card-header">
              <h3>Monitoring Summary</h3>
              <span className="live-tag"><span></span>Live</span>
            </div>
            <table className="detail-table">
              <tbody>
                <tr><td>Global state</td><td><strong className={isEmergency ? "val-red" : "val-green"}>{data.state}</strong></td></tr>
                <tr><td>System message</td><td><strong>{data.message}</strong></td></tr>
                <tr><td>Hardware link</td><td><strong>{data.connected ? "Connected" : "Offline / Simulation"}</strong></td></tr>
                <tr><td>Data source</td><td><strong>{data.source}</strong></td></tr>
                <tr><td>Last update</td><td><strong>{lastUpdate ? formatTime(lastUpdate) : "—"}</strong></td></tr>
              </tbody>
            </table>
          </div>

          <div className={`guidance-card${isEmergency ? " guidance-emergency" : ""}`}>
            <div className="detail-card-header">
              <h3>Response Guidance</h3>
              <span className="operator-tag">Operator</span>
            </div>
            <div className="guidance-content">
              {isEmergency ? (
                <>
                  <div className="guidance-head danger">Immediate Action Required</div>
                  <ul className="guidance-list">
                    <li>Check on infant immediately</li>
                    <li>Verify heart rate sensor contact</li>
                    <li>Confirm physical sensor conditions</li>
                    <li>Contact caregiver if unresponsive</li>
                  </ul>
                </>
              ) : (
                <>
                  <div className="guidance-head safe">System Stable</div>
                  <ul className="guidance-list">
                    <li>All parameters within normal range</li>
                    <li>Monitoring running continuously</li>
                    <li>No action required at this time</li>
                  </ul>
                </>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
