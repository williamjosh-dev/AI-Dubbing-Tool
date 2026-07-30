import { CheckCircle2, Archive, Download } from 'lucide-react';

const historyItems = [
  { name: 'episode-11.mp4', status: 'Completed', date: 'Today', size: '842 MB' },
  { name: 'client-review.mov', status: 'Archived', date: 'Yesterday', size: '1.2 GB' },
  { name: 'training-clip.wav', status: 'Completed', date: '2 days ago', size: '64 MB' },
];

const statusMeta = {
  Completed: { style: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20', icon: CheckCircle2 },
  Archived: { style: 'bg-slate-100 text-slate-600 ring-slate-500/20', icon: Archive },
};

export default function HistoryPage() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-10 space-y-8">
      <div>
        <p className="text-sm font-medium text-indigo-600">History</p>
        <h1 className="mt-1 text-2xl font-semibold text-slate-900">
          Completed dubbing jobs land here
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Job archives, playback links, and export metadata once your backend starts saving results.
        </p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 p-5">
          <p className="text-sm font-medium text-indigo-600">Recent Jobs</p>
          <h2 className="text-base font-semibold text-slate-900">{historyItems.length} completed jobs</h2>
        </div>

        <div className="divide-y divide-slate-100">
          {historyItems.map((item) => {
            const meta = statusMeta[item.status];
            const StatusIcon = meta.icon;
            return (
              <div key={item.name} className="flex items-center justify-between gap-4 px-5 py-4">
                <div className="min-w-0 flex-1">
                  <strong className="block truncate text-sm font-medium text-slate-900">
                    {item.name}
                  </strong>
                  <span className="text-xs text-slate-400">
                    {item.date} · {item.size}
                  </span>
                </div>

                <span
                  className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${meta.style}`}
                >
                  <StatusIcon className="h-3 w-3" />
                  {item.status}
                </span>

                <button className="rounded-md p-1.5 text-slate-400 hover:bg-slate-50 hover:text-slate-600">
                  <Download className="h-4 w-4" />
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}