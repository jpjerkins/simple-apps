import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom';
import Navbar from './components/Navbar';
import ListView from './ListView';
import FormView from './FormView';

export default function App() {
  const [schemas, setSchemas] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/schemas')
      .then(res => res.json())
      .then(data => {
        setSchemas(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load schemas:', err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (schemas.length === 0) {
    return (
      <div className="empty-state">
        <h1>No Apps Found</h1>
        <p>Add a schema file to the /apps directory to get started.</p>
      </div>
    );
  }

  const getSchema = (appId) => schemas.find(s => s.id === appId);

  return (
    <BrowserRouter>
      <div className="app">
        <Navbar schemas={schemas} />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home schemas={schemas} />} />
            {schemas.map(schema => (
              <Route key={schema.id} path={`/${schema.id}`}>
                <Route
                  index
                  element={<ListView schema={schema} />}
                />
                <Route
                  path="new"
                  element={<FormView schema={schema} />}
                />
                <Route
                  path="edit/:id"
                  element={<FormView schema={schema} isEdit />}
                />
              </Route>
            ))}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

function Home({ schemas }) {
  return (
    <div className="home">
      <h1>Simple Apps</h1>
      <p>Select an app from the navigation to get started.</p>
      <div className="app-list">
        {schemas.map(schema => (
          <Link key={schema.id} to={`/${schema.id}`} className="app-card">
            <span className="app-icon">{schema.icon}</span>
            <h2>{schema.name}</h2>
            <p>{schema.description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
