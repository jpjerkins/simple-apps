import { Link } from 'react-router-dom';

export default function Navbar({ schemas }) {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">Simple Apps</Link>
      </div>
      <div className="navbar-apps">
        {schemas.map(schema => (
          <Link
            key={schema.id}
            to={`/${schema.id}`}
            className="navbar-app"
          >
            <span className="app-icon">{schema.icon}</span>
            <span className="app-name">{schema.name}</span>
          </Link>
        ))}
      </div>
    </nav>
  );
}
