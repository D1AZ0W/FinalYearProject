import { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import StatisticCard from '../components/StatisticCard';
import { closeCase, getPendingFines, type DashboardResponse } from '../lib/api';
import { useFetch } from '../hooks/useFetch';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

type FineRow = {
  id: number;
  ts: string;
  plate_image_url: string;
  person_image_url: string;
  overall_conf: number;
  plate_number: string;
  status: string;
};

function normaliseFines(response: DashboardResponse): FineRow[] {
  return response.fines.map((row: any) => ({
    id: row.id,
    ts: row.ts,
    plate_image_url: row.plate_image_url || '/placeholder_plate.jpg',
    person_image_url: row.person_image_url || '/placeholder_person.jpg',
    overall_conf: Number(row.overall_conf || 0),
    plate_number: row.plate_number || 'Unknown',
    status: row.status || 'Pending',
  }));
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [closingId, setClosingId] = useState<number | null>(null);
  const [imageModal, setImageModal] = useState<{ open: boolean; src: string | null }>({ open: false, src: null });

  // Stable fetcher — useCallback ensures useFetch doesn't re-run on every render
  const fetcher = useCallback(() => getPendingFines(), []);
  const { data, loading, error, refresh } = useFetch<DashboardResponse>(fetcher);

  const fineRows: FineRow[] = data ? normaliseFines(data) : [];
  const summary = data?.summary ?? { pending_count: 0, latest_case_id: null };

  const handleLookup = (query: string, plateImageUrl?: string, caseId?: number) => {
    const trimmed = query.trim();
    if (!trimmed) {
      toast.info('Select a fine to search the government records.');
      return;
    }
    navigate(`/records?search=${encodeURIComponent(trimmed)}`, {
      state: { lookupQuery: trimmed, plateImageUrl, caseId },
    });
  };

  const handleCloseCase = async (caseId: number) => {
    setClosingId(caseId);
    try {
      await closeCase(caseId);
      toast.success(`Case #${caseId} has been closed.`);
      refresh();
    } catch {
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

      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle>Fine Queue</CardTitle>
          <CardDescription>Official enforcement records in review</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader className="bg-slate-50 text-slate-500">
              <tr>
                <TableHead>Case</TableHead><TableHead>Time</TableHead><TableHead>Plate</TableHead><TableHead>Rider</TableHead><TableHead>Confidence</TableHead><TableHead>Status</TableHead><TableHead>Actions</TableHead>
              </tr>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow><TableCell colSpan={7} className="py-6 text-center text-muted-foreground">Loading cases…</TableCell></TableRow>
              ) : error ? (
                <TableRow><TableCell colSpan={7} className="py-6 text-center text-red-500">Failed to load cases: {error}</TableCell></TableRow>
              ) : fineRows.length === 0 ? (
                <TableRow><TableCell colSpan={7} className="py-6 text-center text-muted-foreground">No pending fines found.</TableCell></TableRow>
              ) : (
                fineRows.map(row => (
                  <TableRow key={row.id}>
                    <TableCell className="font-semibold">#{row.id}</TableCell>
                    <TableCell>{row.ts}</TableCell>
                    <TableCell>
                      <Button type="button" variant="outline" size="icon-sm" onClick={() => setImageModal({ open: true, src: row.plate_image_url })} className="h-auto w-auto p-0.5">
                        <img className="h-10 w-16 rounded-md object-cover" src={row.plate_image_url} alt={row.plate_number} />
                      </Button>
                    </TableCell>
                    <TableCell>
                      <Button type="button" variant="outline" size="icon-sm" onClick={() => setImageModal({ open: true, src: row.person_image_url })} className="h-auto w-auto p-0.5">
                        <img className="h-10 w-16 rounded-md object-cover" src={row.person_image_url} alt="Rider" />
                      </Button>
                    </TableCell>
                    <TableCell>{row.overall_conf.toFixed(2)}</TableCell>
                    <TableCell><Badge variant="secondary" className="bg-amber-50 text-amber-700">{row.status}</Badge></TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-2">
                        <Button type="button" onClick={() => handleLookup(row.plate_number, row.plate_image_url, row.id)} variant="outline" size="sm">
                          Lookup
                        </Button>
                        <Button type="button" onClick={() => handleCloseCase(row.id)} disabled={closingId === row.id} variant="destructive" size="sm">
                          {closingId === row.id ? 'Closing…' : 'Close'}
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={imageModal.open} onOpenChange={open => !open && setImageModal({ open: false, src: null })}>
        <DialogContent className="max-w-4xl p-3">
          <DialogHeader className="sr-only"><DialogTitle>Case image</DialogTitle><DialogDescription>Full-size case evidence</DialogDescription></DialogHeader>
          {imageModal.src && <img src={imageModal.src} alt="Full case evidence" className="max-h-[80vh] w-full rounded-lg object-contain" />}
        </DialogContent>
      </Dialog>
    </div>
  );
}
