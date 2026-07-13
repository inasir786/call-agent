import { NavLink, Outlet } from "react-router-dom"

export default function Layout({ onLogout }) {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark" />
          <div>
            <div className="brand-name">AI Calling Agent</div>
            <div className="brand-sub">Admissions Campaign</div>
          </div>
        </div>
        <nav>
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/leads">Leads</NavLink>
          <NavLink to="/campaign">Campaign</NavLink>
        </nav>
        <button className="btn ghost logout" onClick={onLogout}>Log out</button>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
