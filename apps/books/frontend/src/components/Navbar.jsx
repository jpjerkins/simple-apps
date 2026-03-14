export default function Navbar({ schema }) {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <a href="/">← All Apps</a>
      </div>
      <div className="navbar-apps">
        <span className="navbar-app">
          <span className="app-icon">{schema.icon}</span>
          <span className="app-name">{schema.name}</span>
        </span>
      </div>
    </nav>
  );
}
