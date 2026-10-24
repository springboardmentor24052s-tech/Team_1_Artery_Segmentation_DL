import { NAV_ITEMS } from "../data/navigation.js";
import "./AppLayout.css";

export default function AppLayout({ page, navigate, mobileNavOpen, setMobileNavOpen, children }) {
  return <div className="app-layout">
    {mobileNavOpen && <button aria-label="Close navigation" className="nav-backdrop" onClick={() => setMobileNavOpen(false)} />}
    <aside className={`sidebar${mobileNavOpen ? " sidebar--open" : ""}`}>
      <button className="sidebar__brand" onClick={() => navigate("dashboard")}><span className="brand-mark">S</span><span><span className="brand-name">StenoVision</span><span className="brand-caption">Medical Imaging Workspace</span></span></button>
      <p className="sidebar__section-label">Workspace</p>
      <nav aria-label="Main navigation" className="sidebar__nav">{NAV_ITEMS.map(([id, label, icon]) => <button key={id} onClick={() => navigate(id)} aria-current={page === id ? "page" : undefined} className={`nav-link${page === id ? " nav-link--active" : ""}`}><span className="nav-link__icon">{icon}</span>{label}{page === id && <span className="nav-link__indicator" />}</button>)}</nav>
      <div className="sidebar__notice"><div className="sidebar__notice-title"><span className="online-dot" />Local prototype mode</div></div>
    </aside>
    <div className="app-content">
      <header className="topbar">
        <div className="topbar__left"><button aria-label="Open navigation" className="menu-button" onClick={() => setMobileNavOpen(true)}>☰</button><span className="topbar__desktop-label">Student research prototype</span><span className="topbar__mobile-label">StenoVision</span></div>
        <button className="profile-button" onClick={() => window.alert("Profile is a placeholder; authentication is not connected.")}><span className="profile-avatar">SV</span><span className="profile-copy"><span>Workspace user</span><small>Research account</small></span><span className="profile-chevron">⌄</span></button>
      </header>
      <main className="main-content">{children}</main>
      <footer className="app-footer"><span>StenoVision · Student research prototype</span></footer>
    </div>
  </div>;
}
