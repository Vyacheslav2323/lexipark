// src/components/RequireAuth.jsx
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { isLoggedIn } from "../../services/auth";

export default function RequireAuth() {
  const location = useLocation();
  if (!isLoggedIn()) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}
