export default function HomePage() {
  return (
    <main style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <header style={{ marginBottom: '2rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 600 }}>Equipment Operations Workspace</h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
          Decision Support & Fault Triage Engine — Baseline Foundation Active
        </p>
      </header>
      <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
        <p style={{ color: 'var(--color-success)', fontWeight: 500 }}>● Foundation Verified (Epic E-01)</p>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginTop: '0.5rem' }}>
          Synthetic demo data baseline locked. Proceeding with domain contracts and deterministic fixtures (Epic E-02).
        </p>
      </div>
    </main>
  );
}
