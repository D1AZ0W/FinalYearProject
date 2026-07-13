import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import StatisticCard from '../components/StatisticCard';
import { closeCase, getPendingFines } from '../lib/api';

type FineRow = {
  id: number;
  ts: string;
  plate_image_url: string;
  person_image_url: string;
  overall_conf: number;
  plate_number: string;
  status: string;
};

export default function DashboardPage() {
  const navigate = useNavigate();
  const [fineRows, setFineRows] = useState<FineRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState({ pending_count: 0, latest_case_id: null as number | null });
  const [closingId, setClosingId] = useState<number | null>(null);
  const [imageModal, setImageModal] = useState<{ open: boolean; src: string | null }>({ open: false, src: null });

  const refreshFines = async () => {
    setLoading(true);
    try {
      const response = await getPendingFines();
      setFineRows(response.fines.map((row: any) => ({
        id: row.id,
        ts: row.ts,
        plate_image_url: row.plate_image_url || '/placeholder_plate.jpg',
        person_image_url: row.person_image_url || '/placeholder_person.jpg',
        overall_conf: Number(row.overall_conf || 0),
        plate_number: row.plate_number || 'Unknown',
        status: row.status || 'Pending',
      })));
      setSummary(response.summary);
    } catch (error) {
      setFineRows([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshFines();
  }, []);

  const handleLookup = (query: string, plateImageUrl?: string, caseId?: number) => {
    const trimmed = query.trim();
    if (!trimmed) {
      toast.info('Select a fine to search the government records.');
      return;
    }

    const nextSearch = encodeURIComponent(trimmed);
    navigate(`/records?search=${nextSearch}`, {
      state: { lookupQuery: trimmed, plateImageUrl, caseId },
    });
  };

  const handleCloseCase = async (caseId: number) => {
    setClosingId(caseId);
    try {
      await closeCase(caseId);
      toast.success(`Case #${caseId} has been closed.`);
      await refreshFines();
    } catch (error) {
      toast.error('Unable to close this case right now.');
    } finally {
      setClosingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <StatisticCard label="Pending Fines" value={summary.pending_count} hint="Active cases in queue" />
        <StatisticCard label="Working Camera" value="Live" hint="Real-time violation stream" />
        <StatisticCard label="Latest Case" value={summary.latest_case_id ? `#${summary.latest_case_id}` : 'N/A'} hint="Most recent record" />
      </div>

      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-[0_12px_35px_rgba(15,23,42,0.06)]">
        <div className="border-b border-slate-200 px-5 py-4">
          <h2 className="text-lg font-semibold text-slate-900">Fine Queue</h2>
          <p className="text-sm text-slate-500">Official enforcement records in review</p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm text-slate-700">
            <thead className="bg-slate-50 text-left text-slate-500">
              <tr>
                <th className="px-4 py-3">Case</th>
                <th className="px-4 py-3">Time</th>
                <th className="px-4 py-3">Plate</th>
                <th className="px-4 py-3">Rider</th>
                <th className="px-4 py-3">Confidence</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-4 py-6 text-center text-slate-500">Loading cases…</td>
                </tr>
              ) : fineRows.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-6 text-center text-slate-500">No pending fines found.</td>
                </tr>
              ) : (
                fineRows.map(row => (
                  <tr key={row.id} className="border-t border-slate-200 bg-white">
                    <td className="px-4 py-3 font-semibold text-slate-900">#{row.id}</td>
                    <td className="px-4 py-3">{row.ts}</td>
                    <td className="px-4 py-3">
                      <button type="button" onClick={() => setImageModal({ open: true, src: row.plate_image_url })} className="rounded-lg border border-slate-200 p-0.5 transition hover:border-sky-400">
                        <img className="h-10 w-16 rounded-md object-cover" src={row.plate_image_url} alt={row.plate_number} />
                      </button>
                    </td>
                    <td className="px-4 py-3">
                      <button type="button" onClick={() => setImageModal({ open: true, src: row.person_image_url })} className="rounded-lg border border-slate-200 p-0.5 transition hover:border-sky-400">
                        <img className="h-10 w-16 rounded-md object-cover" src={row.person_image_url} alt="Rider" />
                      </button>
                    </td>
                    <td className="px-4 py-3">{Number(row.overall_conf).toFixed(2)}</td>
                    <td className="px-4 py-3"><span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700">{row.status}</span></td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => handleLookup(row.plate_number, row.plate_image_url, row.id)}
                          className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                        >
                          Lookup
                        </button>
                        <button
                          type="button"
                          onClick={() => handleCloseCase(row.id)}
                          disabled={closingId === row.id}
                          className="rounded-lg bg-rose-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-rose-500 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          {closingId === row.id ? 'Closing…' : 'Close'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {imageModal.open && imageModal.src ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 px-4 py-6" onClick={() => setImageModal({ open: false, src: null })}>
          <div className="relative w-full max-w-4xl rounded-3xl border border-slate-200 bg-white p-3 shadow-2xl" onClick={event => event.stopPropagation()}>
            <button type="button" onClick={() => setImageModal({ open: false, src: null })} className="absolute right-3 top-3 rounded-full bg-white/90 px-3 py-1.5 text-sm font-semibold text-slate-700 shadow">Close</button>
            <img src={imageModal.src} alt="Full rider crop" className="max-h-[80vh] w-full rounded-2xl object-contain" />
          </div>
        </div>
      ) : null}
    </div>
  );
}
