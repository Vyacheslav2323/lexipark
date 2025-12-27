// src/pages/Login.jsx
import { useEffect } from "react";
import { isLoggedIn } from "../services/auth";

function loadGoogleScript() {
  return new Promise((resolve) => {
    if (window.google) return resolve();
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = resolve;
    document.body.appendChild(script);
  });
}

async function handleGoogleResponse(response) {
  if (isLoggedIn()) return;
  if (!response?.credential) return;

  const googleIdToken = response.credential;

  const res = await fetch("http://127.0.0.1:8000/auth/google", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${googleIdToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ googleIdToken }),
  });

  if (!res.ok) return;

  const data = await res.json();
  localStorage.setItem("access_token", data.access_token);

  // simplest for now
  window.location.href = "/";
}

export default function Login() {
  useEffect(() => {
    if (isLoggedIn()) {
      window.location.href = "/";
      return;
    }

    loadGoogleScript().then(() => {
      window.google.accounts.id.initialize({
        client_id:
          "614213081580-9heabahooqahutmdlc1t5ol26a64ngev.apps.googleusercontent.com",
        callback: handleGoogleResponse,
      });

      window.google.accounts.id.renderButton(
        document.getElementById("google-login"),
        { theme: "outline", size: "large" }
      );
    });
  }, []);

  return (
    <div className="container py-5">
      <h1 className="mb-3">Login</h1>
      <div id="google-login" />
    </div>
  );
}
