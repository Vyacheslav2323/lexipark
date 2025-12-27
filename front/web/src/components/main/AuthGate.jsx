// src/components/RequireAuth.jsx
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import { getToken, logout } from "../../services/auth";
import { apiGet } from "../../services/api";

export default function RequireAuth() {
  const location = useLocation();
  const [isValid, setIsValid] = useState(null);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setIsValid(false);
      return;
    }

    apiGet("/chat", { auth: true })
      .then(() => setIsValid(true))
      .catch(() => {
        logout();
        setIsValid(false);
      });
  }, []);

  if (isValid === null) {
    return <div>Loading...</div>;
  }

  if (!isValid) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}
