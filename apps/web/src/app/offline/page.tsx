"use client";

export default function OfflinePage() {
  return (
    <div style={{ margin: 0, fontFamily: "system-ui, sans-serif", background: "#0f172a", color: "white", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "100vh", textAlign: "center", padding: "2rem" }}>
      <div style={{ fontSize: "4rem", marginBottom: "1rem" }}>📡</div>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 800, marginBottom: "0.5rem" }}>আপনি অফলাইনে আছেন</h1>
      <p style={{ color: "#94a3b8", marginBottom: "2rem" }}>You are offline. Please check your internet connection.</p>
      <button
        onClick={() => window.location.reload()}
        style={{ background: "#6366f1", color: "white", border: "none", padding: "0.75rem 2rem", borderRadius: "0.75rem", cursor: "pointer", fontSize: "1rem", fontWeight: 600 }}
      >
        Try Again
      </button>
    </div>
  );
}
