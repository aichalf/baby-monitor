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

function getStatusClass(state) {
  if (state === "EMERGENCY") return "status emergency";
  return "status normal";
}

function App() {
  const [data, setData] = useState(fallbackData);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/data");
        if (!res.ok) throw new Error("Erreur API");
        const json = await res.json();
        setData(json);
        setError("");
      } catch (err) {
        setError("Backend non connecté");
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="page">
      <div className="container">
        <header className="header">
          <div>
            <h1>Baby Monitor</h1>
            <p>Interface utilisateur du système de surveillance</p>
          </div>
          <div className="badge-box">
            <span className="badge">
              {data.connected ? "STM32 connecté" : "Mode simulation"}
            </span>
          </div>
        </header>

        {error && <div className="error-box">{error}</div>}

        <section className={getStatusClass(data.state)}>
          <div className="section-label">État système</div>
          <div className="status-text">
            {data.state === "EMERGENCY" ? "🚨 EMERGENCY" : "✅ NORMAL"}
          </div>
          <div className="status-message">{data.message}</div>
        </section>

        <div className="grid">
          <div className="card">
            <div className="label">Température bébé</div>
            <div className="value">{data.babyTemp} °C</div>
          </div>

          <div className="card">
            <div className="label">Fréquence cardiaque</div>
            <div className="value">
              {data.heartRate === 0 ? "No contact" : `${data.heartRate} bpm`}
            </div>
          </div>

          <div className="card">
            <div className="label">Mouvement</div>
            <div className="value">{data.movement}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;