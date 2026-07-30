import './global.css';
import Link from 'next/link';

export const metadata = {
	title: 'AI Dubbing Studio',
	description: 'Route-based dubbing dashboard for uploads, jobs, and history.',
};

export default function RootLayout({ children }) {
	return (
		<html lang="en" suppressHydrationWarning>
			<body>
				<div className="app-shell">
					<header className="topbar">
						<div>
							<p className="eyebrow">AI Dubbing Tool</p>
							<h1 className="brand-title">Studio Dashboard</h1>
						</div>

						<nav className="topnav" aria-label="Primary navigation">
							<Link href="/" className="topnav-link">
								Home
							</Link>
							<Link href="/dashboard" className="topnav-link">
								Dashboard
							</Link>
							<Link href="/history" className="topnav-link">
								History
							</Link>
						</nav>
					</header>

					<main className="app-main">{children}</main>
				</div>
			</body>
		</html>
	);
}
