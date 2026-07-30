const pipelineCards = [
	{ title: 'Upload Queue', value: '3 active files', detail: 'Waiting to enter the dubbing pipeline' },
	{ title: 'Current Model', value: 'Whisper + TTS', detail: 'Transcribe, translate, and synthesize' },
	{ title: 'Export Mode', value: 'MP4 + WAV', detail: 'Default output targets for beta testing' },
];

const jobRows = [
	{ name: 'episode-12.mp4', status: 'Transcribing', lang: 'es → en' },
	{ name: 'tutorial-audio.wav', status: 'Translating', lang: 'fr → en' },
	{ name: 'product-demo.mov', status: 'Rendering', lang: 'de → en' },
];

export default function HomePage() {
	return (
		<section className="dashboard-grid dashboard-page">
			<div className="panel-card hero-panel">
				<p className="section-label">Dashboard</p>
				<h2 className="panel-title">Operational control for dubbing jobs.</h2>
				<p className="panel-copy">
					Use this view to track pipeline progress, review job state, and keep the beta workflow organized.
				</p>
			</div>

			<div className="stats-grid">
				{pipelineCards.map((card) => (
					<article key={card.title} className="stat-card">
						<p className="stat-label">{card.title}</p>
						<strong className="stat-value stat-value-sm">{card.value}</strong>
						<span className="stat-hint">{card.detail}</span>
					</article>
				))}
			</div>

			<div className="panel-card">
				<p className="section-label">Live Jobs</p>
				<div className="table-list">
					{jobRows.map((job) => (
						<div key={job.name} className="table-row">
							<div>
								<strong>{job.name}</strong>
								<span>{job.lang}</span>
							</div>
							<span className="status-pill">{job.status}</span>
						</div>
					))}
				</div>
			</div>
		</section>
	);
}
