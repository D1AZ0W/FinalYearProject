import { useEffect, useMemo, useState } from 'react';
import { toast } from 'react-toastify';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { getNotificationStream, getStreamUrl } from '@/lib/api';

const videoSources = [{ label: 'Live Camera', value: '0' }];

export default function MonitorPage() {
  const [source, setSource] = useState('0');
  const [sourceInput, setSourceInput] = useState('0');
  const [feedUrl, setFeedUrl] = useState(getStreamUrl('0'));

  useEffect(() => {
    setFeedUrl(getStreamUrl(source));
  }, [source]);

  const sourceLabel = useMemo(() => videoSources.find(item => item.value === source)?.label ?? source, [source]);

  useEffect(() => {
    const evtSource = new EventSource(getNotificationStream());
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
      <aside className="space-y-4">
        <Card>
          <CardHeader><CardTitle>Camera Controls</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            <div className="space-y-2">
              {videoSources.map(item => (
              <Button
                key={item.value}
                type="button"
                onClick={() => {
                  setSource(item.value);
                  setSourceInput(item.value);
                }}
                variant={item.value === source ? 'default' : 'outline'}
                className="w-full"
              >
                {item.label}
              </Button>
            ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Custom source</CardTitle></CardHeader>
          <CardContent className="space-y-3">
          <label htmlFor="customSource" className="mb-2 block text-sm font-medium text-slate-700">Custom source</label>
          <Input
            id="customSource"
            value={sourceInput}
            onChange={e => setSourceInput(e.target.value)}
          />
          <Button type="button" onClick={() => setSource(sourceInput.trim())} disabled={!sourceInput.trim()} className="w-full">Load Source</Button>
          </CardContent>
        </Card>
      </aside>

      <section className="space-y-4">
        <Card>
          <CardContent className="flex flex-wrap items-center justify-between gap-3 pt-6">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-sky-600">HelmDetect Monitor</p>
            <h2 className="text-xl font-semibold text-slate-900">Live Violation Stream</h2>
          </div>
          <Badge className="bg-emerald-600 text-white hover:bg-emerald-600">Live</Badge>
          </CardContent>
        </Card>

        <div className="overflow-hidden rounded-[28px] border border-slate-200 bg-slate-50 p-2 shadow-[0_12px_35px_rgba(15,23,42,0.06)]">
          <div className="aspect-video w-full overflow-hidden rounded-[22px] bg-black">
            <img src={feedUrl} alt="Live stream" className="h-full w-full object-contain" />
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
