import { useEffect, useMemo, useState } from 'react';
import { toast } from 'react-toastify';

const videoSources = [{ label: 'Live Camera', value: '0' }];

export default function MonitorPage() {
  const [source, setSource] = useState('0');
  const [feedUrl, setFeedUrl] = useState('/video_feed?source=0');

  useEffect(() => {
    setFeedUrl(`/video_feed?source=${encodeURIComponent(source)}`);
  }, [source]);

  const sourceLabel = useMemo(() => videoSources.find(item => item.value === source)?.label ?? source, [source]);

  useEffect(() => {
    const evtSource = new EventSource('/stream_notifications');
    evtSource.onmessage = event => {
      const data = JSON.parse(event.data);
      toast.success(`Case #${data.case_id} added to the fine list.`);
    };
    evtSource.onerror = () => {
      evtSource.close();
    };
    return () => {
      evtSource.close();
    };
  }, []);

  return (
    <div className="grid gap-6 xl:grid-cols-[320px_minmax(0,1fr)]">
      <aside className="space-y-4 rounded-3xl border border-slate-200 bg-white p-4 shadow-[0_12px_35px_rgba(15,23,42,0.06)]">
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <h2 className="mb-3 text-base font-semibold text-slate-900">Camera Controls</h2>
          <div className="space-y-2">
            {videoSources.map(item => (
              <button
                key={item.value}
                type="button"
                onClick={() => setSource(item.value)}
                className={`w-full rounded-xl px-3 py-2.5 text-sm font-medium transition ${item.value === source ? 'bg-sky-600 text-white' : 'bg-white text-slate-700 hover:bg-slate-100'}`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <label htmlFor="customSource" className="mb-2 block text-sm font-medium text-slate-700">Custom source</label>
          <input
            id="customSource"
            value={source}
            onChange={e => setSource(e.target.value)}
            className="mb-3 w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 outline-none focus:border-sky-500"
          />
          <button type="button" onClick={() => setSource(source)} className="w-full rounded-xl bg-sky-600 px-3 py-2.5 text-sm font-semibold text-white transition hover:bg-sky-500">
            Load Source
          </button>
        </div>
      </aside>

      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-3xl border border-slate-200 bg-white px-4 py-4 shadow-[0_12px_35px_rgba(15,23,42,0.06)]">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-sky-600">HelmDetect Monitor</p>
            <h2 className="text-xl font-semibold text-slate-900">Live Violation Stream</h2>
          </div>
          <span className="rounded-full bg-emerald-50 px-3 py-1 text-sm font-semibold text-emerald-600">Live</span>
        </div>

        <div className="overflow-hidden rounded-[28px] border border-slate-200 bg-slate-50 p-2 shadow-[0_12px_35px_rgba(15,23,42,0.06)]">
          <div className="aspect-video w-full overflow-hidden rounded-[22px] bg-slate-100">
            <img src={feedUrl} alt="Live stream" className="h-full w-full object-cover" />
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          <p>Current source: <span className="font-semibold text-slate-900">{sourceLabel}</span></p>
          <p className="mt-1">Video feed updates in real time as detections run.</p>
        </div>
      </section>
    </div>
  );
}
