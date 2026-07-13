import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import Layout from './components/Layout';
import DashboardPage from './pages/DashboardPage';
import LoginPage from './pages/LoginPage';
import MonitorPage from './pages/MonitorPage';
import RecordsPage from './pages/RecordsPage';
import { useAuth } from './context/AuthContext';

function RequireAuth({ children }: { children: JSX.Element }) {
  const { authenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div className="page-loading">Loading…</div>;
  }

  return authenticated ? children : <Navigate to="/login" state={{ from: location }} replace />;
}

function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route index element={<MonitorPage />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="records" element={<RecordsPage />} />
      </Route>
      <Route path="/login" element={<LoginPage />} />
    </Routes>
  );
}

export default App;
