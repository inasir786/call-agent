import { useState } from "react"
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import Login from "./pages/Login"
import Dashboard from "./pages/Dashboard"
import Leads from "./pages/Leads"
import LeadDetail from "./pages/LeadDetail"
import Campaign from "./pages/Campaign"
import Layout from "./components/Layout"
import { getToken, setToken, clearToken } from "./api/client"

export default function App() {
  const [authed, setAuthed] = useState(Boolean(getToken()))

  const handleLogin = (token) => {
    setToken(token)
    setAuthed(true)
  }

  const handleLogout = () => {
    clearToken()
    setAuthed(false)
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={authed ? <Navigate to="/" /> : <Login onLogin={handleLogin} />} />
        <Route element={authed ? <Layout onLogout={handleLogout} /> : <Navigate to="/login" />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/leads" element={<Leads />} />
          <Route path="/leads/:id" element={<LeadDetail />} />
          <Route path="/campaign" element={<Campaign />} />
        </Route>
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  )
}
