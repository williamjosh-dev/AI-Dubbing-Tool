const historyItems = [
	{ name: 'episode-11.mp4', status: 'Completed', date: 'Today' },
	{ name: 'client-review.mov', status: 'Archived', date: 'Yesterday' },
	{ name: 'training-clip.wav', status: 'Completed', date: '2 days ago' },
];

export default function HistoryPage() {
	return (
		<section className="dashboard-grid dashboard-page">
			<div className="panel-card hero-panel">
				<p className="section-label">History</p>
				<h2 className="panel-title">Completed dubbing jobs land here.</h2>
				<p className="panel-copy">
					This route is ready for job archives, playback links, and export metadata once your backend starts saving results.
				</p>
			</div>

			<div className="panel-card">
				<p className="section-label">Recent Jobs</p>
				<div className="table-list">
					{historyItems.map((item) => (
						<div key={item.name} className="table-row">
							<div>
								<strong>{item.name}</strong>
								<span>{item.date}</span>
							</div>
							<span className="status-pill status-pill-muted">{item.status}</span>
						</div>
					))}
				</div>
			</div>
		</section>
	);
}
