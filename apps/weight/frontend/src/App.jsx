import Navbar from './components/Navbar';
import WeightView from './WeightView';

export default function App() {
  return (
    <div className="app">
      <Navbar />
      <main className="main-content">
        <WeightView />
      </main>
    </div>
  );
}
