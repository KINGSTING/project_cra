// src/components/ProtectedRoute.jsx
import { Navigate } from "react-router-dom";
import { useSession } from "../../hooks/useSession"; 

export default function ProtectedRoute({ children }) {
  const { session, ready } = useSession();

  if (!ready) {
    return <div style={{ padding: 48, textAlign: "center" }}>Loading…</div>;
  }
  if (!session) {
    return <Navigate to="/login" replace />;
  }
  return children;
}