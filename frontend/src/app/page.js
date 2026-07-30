import Link from 'next/link';

const stats = [
  { label: 'Queued Jobs', value: '08', hint: '+2 in the last hour' },
  { label: 'Processed Minutes', value: '124', hint: 'Today across all jobs' },
  { label: 'Supported Formats', value: '6', hint: 'Video and audio inputs' },
];

const steps = [
  'Upload a media file',
  'Pick source and target languages',
  'Run transcription, translation, and TTS',
  'Review the output in history',
];

export default function HomePage() {
  return (
    <section className="dashboard-grid">
      <div className="hero-card">
        <p className="section-label">Main Root Dashboard</p>
        <h2 className="hero-title">Ship dubbing jobs from one place.</h2>
        <p className="hero-copy">
          This root page is now your app entry point for uploads, job status, and future beta workflows.
        </p>

        <div className="hero-actions">
          <Link href="/dashboard" className="primary-btn">
            Open Dashboard
          </Link>
          <Link href="/history" className="secondary-btn">
            View History
          </Link>
        </div>
      </div>

      <div className="stats-grid">
        {stats.map((stat) => (
          <article key={stat.label} className="stat-card">
            <p className="stat-label">{stat.label}</p>
            <strong className="stat-value">{stat.value}</strong>
            <span className="stat-hint">{stat.hint}</span>
          </article>
        ))}
      </div>

      <div className="panel-card">
        <p className="section-label">Workflow</p>
        <h3 className="panel-title">What the app will do on every job</h3>
        <ol className="step-list">
          {steps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </div>

      <div className="panel-card split-panel">
        <div>
          <p className="section-label">Quick Actions</p>
          <h3 className="panel-title">Routes are now ready for a dashboard-first flow.</h3>
          <p className="panel-copy">
            Keep uploads on the home route, use dashboard for operational status, and reserve history for completed jobs.
          </p>
        </div>

        <div className="action-stack">
          <Link href="/dashboard" className="ghost-btn">
            Go to dashboard
          </Link>
          <Link href="/history" className="ghost-btn">
            Open history
          </Link>
        </div>
      </div>
    </section>
  );
}
