// App.jsx
import { BrowserRouter, Routes, Route, Link, Navigate } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";

import Memorize from "./pages/Memorize";
import Mypage from "./pages/Mypage";
import Translator from "./pages/Translator";
import Login from "./pages/Login";
import Landing from "./pages/Landing";
import RequireAuth from "./components/main/AuthGate";
import { isLoggedIn, logout } from "./services/auth";

export default function App() {
  return (
    <BrowserRouter>
      <nav className="navbar navbar-expand-lg bg-body-tertiary">
        <ul className="navbar-nav">
          {isLoggedIn() ? (
            <>
              <li className="nav-item">
                <Link className="nav-link" to="/translator">Translator</Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="/memorize">Memorize</Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="/mypage">Mypage</Link>
              </li>
              <li className="nav-item">
                <button
                  className="btn btn-sm btn-outline-danger"
                  onClick={() => {
                    logout();
                    window.location.href = "/login";
                  }}
                >
                  Logout
                </button>
              </li>
            </>
          ) : (
            <li className="nav-item">
              <Link className="nav-link" to="/login">Login</Link>
            </li>
          )}
        </ul>
      </nav>

      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />

        <Route element={<RequireAuth />}>
          <Route path="/translator" element={<Translator />} />
          <Route path="/memorize" element={<Memorize />} />
          <Route path="/mypage" element={<Mypage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
