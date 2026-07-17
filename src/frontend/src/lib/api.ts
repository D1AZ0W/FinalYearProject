import axios, { AxiosError } from 'axios';

type ApiEnvelope<T> = { success: boolean; data: T; message?: string };

export type DashboardResponse = {
  fines: unknown[];
  summary: { pending_count: number; latest_case_id: number | null };
};

export type RecordsResponse = {
  records: Array<{
    id: number;
    plate_number: string;
    person_name: string;
    violation_count: number;
    total_fine_due: number;
  }>;
};

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: { Accept: 'application/json' },
});

function toMessage(error: unknown) {
  if (error instanceof AxiosError) {
    const payload = error.response?.data as { message?: string; error?: string } | undefined;
    return payload?.message || payload?.error || error.message;
  }
  return 'Unable to complete the request.';
}

async function request<T>(call: Promise<{ data: ApiEnvelope<T> }>) {
  try {
    const { data } = await call;
    if (!data.success) throw new Error(data.message || 'Request was not successful.');
    return data.data;
  } catch (error) {
    throw new Error(toMessage(error));
  }
}

export const getStatus = () => request(api.get<ApiEnvelope<{ authenticated: boolean }>>('/auth/status'));
export const login = (username: string, password: string) => request(api.post<ApiEnvelope<{ success: boolean }>>('/auth/login', { username, password }));
export const logout = () => request(api.post<ApiEnvelope<unknown>>('/auth/logout'));
export const getPendingFines = (search = '', date = '') => request(api.get<ApiEnvelope<DashboardResponse>>('/dashboard', { params: { search, date } }));
export const getRecords = (search = '') => request(api.get<ApiEnvelope<RecordsResponse>>('/records', { params: { search } }));
export const closeCase = (caseId: number) => request(api.post<ApiEnvelope<{ closed: boolean }>>(`/dashboard/close/${caseId}`));
export const assignFine = (personId: number, caseId: number) => request(api.post<ApiEnvelope<{ assigned: boolean }>>(`/assign_fine/${personId}/${caseId}`));
export const getStreamUrl = (source: string) => `/video_feed?source=${encodeURIComponent(source)}`;
export const getNotificationStream = () => '/stream_notifications';

export default api;
