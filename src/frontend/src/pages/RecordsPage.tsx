import { useCallback, useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { assignFine, getRecords, type RecordsResponse } from '../lib/api';
import { useFetch } from '../hooks/useFetch';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

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

  const locationState = location.state as { lookupQuery?: string; plateImageUrl?: string; caseId?: number } | null;
  const urlSearch = new URLSearchParams(location.search).get('search') ?? '';
  const initialQuery = urlSearch || locationState?.lookupQuery || '';
  // Don't pre-fill the search with the placeholder text from the backend
  const [searchTerm, setSearchTerm] = useState(initialQuery === 'ID REQUIRED' ? '' : initialQuery);
  const [activeQuery, setActiveQuery] = useState(initialQuery === 'ID REQUIRED' ? '' : initialQuery);
  const [plateImageUrl, setPlateImageUrl] = useState<string | null>(locationState?.plateImageUrl ?? null);
  const [caseId, setCaseId] = useState<number | null>(locationState?.caseId ?? null);
  const [assigningId, setAssigningId] = useState<number | null>(null);

  // Sync state when navigating to this page from Dashboard
  useEffect(() => {
    const state = location.state as { lookupQuery?: string; plateImageUrl?: string; caseId?: number } | null;
    const query = new URLSearchParams(location.search).get('search') ?? state?.lookupQuery ?? '';
    const clean = query === 'ID REQUIRED' ? '' : query;
    setSearchTerm(clean);
    setActiveQuery(clean);
    setPlateImageUrl(state?.plateImageUrl ?? null);
    setCaseId(state?.caseId ?? null);
  }, [location.search, location.state]);

  const fetcher = useCallback(() => getRecords(activeQuery), [activeQuery]);
  const { data, loading } = useFetch<RecordsResponse>(fetcher);

  const records: RecordRow[] = data?.records ?? [];

  const handleSearch = () => {
    const trimmed = searchTerm.trim();
    setActiveQuery(trimmed);
    navigate(`/records?search=${encodeURIComponent(trimmed)}`, {
      state: { lookupQuery: trimmed, plateImageUrl, caseId },
    });
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
    } catch {
      toast.error('Unable to assign the fine right now.');
    } finally {
      setAssigningId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-4 lg:grid-cols-[320px_minmax(0,1fr)]">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Manual Record Lookup</CardTitle>
              <CardDescription>Search by plate number or citizen name and confirm the match directly in the registry.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="mt-3 space-y-2">
                <Input
                  value={searchTerm}
                  onChange={e => setSearchTerm(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSearch()}
                  placeholder="Plate or owner name"
                />
                <Button type="button" onClick={handleSearch} disabled={loading} className="w-full">
                  {loading ? 'Searching…' : 'Lookup'}
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="border-sky-200 bg-gradient-to-br from-sky-50 to-amber-50">
            <CardHeader>
              <CardTitle>Plate Evidence</CardTitle>
              <CardDescription>A large plate preview appears here for the selected case lookup.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mt-3 overflow-hidden rounded-2xl border border-slate-200 bg-white p-3">
                {plateImageUrl ? (
                  <img src={plateImageUrl} alt="Number plate evidence" className="h-44 w-full rounded-xl object-contain" />
                ) : (
                  <div className="flex h-44 items-center justify-center rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 text-center text-sm text-slate-500">
                    {activeQuery
                      ? `No plate image available for "${activeQuery}".`
                      : 'Select a fine to open the matching plate evidence here.'}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="overflow-hidden">
          <CardHeader>
            <CardTitle>Registered Citizens & Assigned Fines</CardTitle>
            <CardDescription>Official data for enforcement review</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader className="bg-slate-50 text-slate-500">
                <tr>
                  <TableHead>Plate</TableHead><TableHead>Name</TableHead><TableHead>Violations</TableHead><TableHead>Total Due</TableHead><TableHead>Action</TableHead>
                </tr>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow><TableCell colSpan={5} className="py-6 text-center text-muted-foreground">Loading records…</TableCell></TableRow>
                ) : records.length === 0 ? (
                  <TableRow><TableCell colSpan={5} className="py-6 text-center text-muted-foreground">No matching records found.</TableCell></TableRow>
                ) : (
                  records.map(record => (
                    <TableRow key={record.id}>
                      <TableCell className="font-semibold">{record.plate_number}</TableCell>
                      <TableCell>{record.person_name}</TableCell>
                      <TableCell>{record.violation_count}</TableCell>
                      <TableCell>Rs. {record.total_fine_due}</TableCell>
                      <TableCell>
                        <Button type="button" onClick={() => handleAssignFine(record.id)} disabled={assigningId === record.id} size="sm">
                          {assigningId === record.id ? 'Assigning…' : 'Assign Fine'}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
