// src/hooks/useSession.js
import { createContext, useContext, useState, useEffect } from "react";
import { getToken, setToken, clearToken } from "../lib/api";

const SessionContext = createContext(null);

function decodeJwt(token) {
  try {
    const [, payloadB64] = token.split(".");
    const padded = payloadB64 + "=".repeat((4 - (payloadB64.length % 4)) % 4);
    const json = atob(padded.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(json);
  } catch {
    return null;
  }
}

function isExpired(payload) {
  if (!payload?.exp) return true;
  return Date.now() >= payload.exp * 1000;
}

export function SessionProvider({ children }) {
  const [session, setSession] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setReady(true);
      return;
    }
    const payload = decodeJwt(token);
    if (!payload || isExpired(payload)) {
      clearToken();
      setReady(true);
      return;
    }
    setSession({
      token,
      user: {
        id: payload.sub,
        email: payload.email,
        agency: payload.agency,
        role: payload.role,
      },
    });
    setReady(true);
  }, []);

  function login(token) {
    setToken(token);
    const payload = decodeJwt(token);
    setSession({
      token,
      user: {
        id: payload.sub,
        email: payload.email,
        agency: payload.agency,
        role: payload.role,
      },
    });
  }

  function logout() {
    clearToken();
    setSession(null);
  }

  return (
    <SessionContext.Provider value={{ session, ready, login, logout }}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used inside <SessionProvider>");
  return ctx;
}