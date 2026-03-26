export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <a href="/">← All Apps</a>
      </div>
      <div className="navbar-apps">
        <span className="navbar-app">
          <span className="app-icon">⚖️</span>
          <span className="app-name">Weight Tracker</span>
        </span>
      </div>
    </nav>
  );
}
