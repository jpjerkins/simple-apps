import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import ListView from './ListView';
import FormView from './FormView';
import schema from './schema';

export default function App() {
  return (
    <BrowserRouter basename="/razorblades">
      <div className="app">
        <Navbar schema={schema} />
        <main className="main-content">
          <Routes>
            <Route index element={<ListView schema={schema} />} />
            <Route path="new" element={<FormView schema={schema} />} />
            <Route path="edit/:id" element={<FormView schema={schema} isEdit />} />
            <Route path="*" element={<Navigate to="" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
