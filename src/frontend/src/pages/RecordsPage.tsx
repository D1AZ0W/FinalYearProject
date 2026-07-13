import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { assignFine, getRecords } from '../lib/api';

type RecordRow = {
  id: number;
  plate_number: string;
  person_name: string;
  violation_count: number;
  total_fine_due: number;
};

export default function RecordsPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [records, setRecords] = useState<RecordRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeSearch, setActiveSearch] = useState('');
  const [plateImageUrl, setPlateImageUrl] = useState<string | null>(null);
  const [caseId, setCaseId] = useState<number | null>(null);
  const [assigningId, setAssigningId] = useState<number | null>(null);

  const loadRecords = async (query = '') => {
    setLoading(true);
    try {
      const response = await getRecords(query);
      setRecords(response.records || []);
      setActiveSearch(query);
    } catch (error) {
      setRecords([]);
      setActiveSearch(query);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const state = location.state as { lookupQuery?: string; plateImageUrl?: string; caseId?: number } | null;
    const initialQuery = new URLSearchParams(location.search).get('search') || state?.lookupQuery || '';
    const query= initialQuery=== "ID REQUIRED"? "" : initialQuery; 
    setSearchTerm(initialQuery);
    setPlateImageUrl(state?.plateImageUrl || null);
    setCaseId(state?.caseId ?? null);
    loadRecords(query);
  }, [location.search, location.state]);

  const handleSearch = () => {
    const trimmed = searchTerm.trim();
    const nextSearch = encodeURIComponent(trimmed);
    navigate(`/records?search=${nextSearch}`, { state: { lookupQuery: trimmed, plateImageUrl, caseId } });
    loadRecords(trimmed);
  };

  const handleAssignFine = async (personId: number) => {
    if (!caseId) {
      toast.error('No fine case is linked to this lookup.');
      return;
    }

    setAssigningId(personId);
    try {
      await assignFine(personId, caseId);
      toast.success('Fine assigned and case closed.');
      navigate('/dashboard');
    } catch (error) {
      toast.error('Unable to assign the fine right now.');
    } finally {
      setAssigningId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-4 lg:grid-cols-[320px_minmax(0,1fr)]">
        <div className="space-y-4 rounded-3xl border border-slate-200 bg-white p-4 shadow-[0_12px_35px_rgba(15,23,42,0.06)] ">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <h3 className="text-lg font-semibold text-slate-900">Manual Record Lookup</h3>
            <p className="mt-2 text-sm text-slate-600">Search by plate number or citizen name and confirm the match directly in the registry.</p>
            <div className="mt-3 space-y-2">
              <input
                value={searchTerm}
                onChange={event => setSearchTerm(event.target.value)}
                placeholder="Plate or owner name"
                className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 outline-none focus:border-sky-500"
              />
              <button
                type="button"
                onClick={handleSearch}
                disabled={loading}
                className="w-full rounded-xl bg-sky-600 px-3 py-2.5 text-sm font-semibold text-white transition hover:bg-sky-500 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? 'Searching…' : 'Lookup'}
              </button>
            </div>
          </div>

          <div className="rounded-2xl border border-sky-200 bg-gradient-to-br from-sky-50 to-amber-50 p-4">
            <h3 className="text-lg font-semibold text-slate-900">Plate Evidence</h3>
            <p className="mt-2 text-sm text-slate-700">A large plate preview appears here for the selected case lookup.</p>
            <div className="mt-3 overflow-hidden rounded-2xl border border-slate-200 bg-white p-3">
              {plateImageUrl ? (
                <img src={plateImageUrl} alt="Number plate evidence" className="h-44 w-full rounded-xl object-cover" />
              ) : (
                <div className="flex h-44 items-center justify-center rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 text-center text-sm text-slate-500">
                  {activeSearch ? `No plate image available for “${activeSearch}”.` : 'Select a fine to open the matching plate evidence here.'}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-[0_12px_35px_rgba(15,23,42,0.06)]">
          <div className="border-b border-slate-200 px-5 py-4">
            <h2 className="text-lg font-semibold text-slate-900">Registered Citizens & Assigned Fines</h2>
            <p className="text-sm text-slate-500">Official data for enforcement review</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm text-slate-700">
              <thead className="bg-slate-50 text-left text-slate-500">
                <tr>
                  <th className="px-4 py-3">Plate</th>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Violations</th>
                  <th className="px-4 py-3">Total Due</th>
                  <th className="px-4 py-3">Action</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-6 text-center text-slate-500">Loading records…</td>
                  </tr>
                ) : records.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-6 text-center text-slate-500">No matching records found.</td>
                  </tr>
                ) : (
                  records.map(record => (
                    <tr key={record.id} className="border-t border-slate-200 bg-white">
                      <td className="px-4 py-3 font-semibold text-slate-900">{record.plate_number}</td>
                      <td className="px-4 py-3">{record.person_name}</td>
                      <td className="px-4 py-3">{record.violation_count}</td>
                      <td className="px-4 py-3">Rs. {record.total_fine_due}</td>
                      <td className="px-4 py-3">
                        <button
                          type="button"
                          onClick={() => handleAssignFine(record.id)}
                          disabled={assigningId === record.id}
                          className="rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-sky-500 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          {assigningId === record.id ? 'Assigning…' : 'Assign Fine'}
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
