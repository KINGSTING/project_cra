// src/App.jsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { SessionProvider } from "./hooks/useSession";
import ProtectedRoute from "./components/client/ProtectedRoute";

import Landing from "./pages/LandingPage";
import Register from "./pages/Register";
import Login from "./pages/Login";
import Verify from "./pages/Verify";

import Dashboard from "./components/client/Dashboard";
import CreateAssessment from "./components/client/CreateAssessment";
import AssessmentDetail from "./components/client/AssessmentDetail";

export default function App() {
  return (
    <SessionProvider>
      <BrowserRouter>
       <Routes>
        <Route path="/"          element={<Landing />} />
        <Route path="/register"  element={<Register />} />
        <Route path="/login"     element={<Login />} />
        <Route path="/verify"    element={<Verify />} />

        <Route path="/dashboard"
          element={<ProtectedRoute><Dashboard /></ProtectedRoute>}
        />
        <Route path="/assessments/new"
          element={<ProtectedRoute><CreateAssessment /></ProtectedRoute>}
        />
        <Route path="/assessments/:id"
          element={<ProtectedRoute><AssessmentDetail /></ProtectedRoute>}
        />

        <Route path="*" element={<div style={{ padding: 48 }}>Page not found.</div>} />
      </Routes>
      </BrowserRouter>
    </SessionProvider>
  );
}