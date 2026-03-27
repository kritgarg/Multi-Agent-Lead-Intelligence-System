import { useState } from 'react';
import { SearchBar } from './components/SearchBar';
import { Table } from './components/Table';
import { Sparkles } from 'lucide-react';
import axios from 'axios';
import './index.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

function App() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (company, location) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_BASE_URL}/process-company`, {
        company,
        location,
      });
      setResults((prev) => [response.data, ...prev]);
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail || "Failed to process. Is the backend running?"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleExcelUpload = async (file) => {
    if (!file) return;
    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE_URL}/process-excel`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResults(response.data.results || []);
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail || "Failed to process Excel. Is the backend running?"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>Lead Intelligence 🚀</h1>
        <p>Multi-Agent AI System for Smart Prospecting</p>
      </header>

      <main style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        <div className="glass-panel">
          <SearchBar onSearch={handleSearch} onExcelUpload={handleExcelUpload} loading={loading} />
          {error && <div className="error-message">{error}</div>}
        </div>

        <div className="glass-panel">
          {loading && results.length === 0 ? (
            <div className="empty-state">
              <div className="loader" style={{ margin: '0 auto 1.5rem', width: '44px', height: '44px' }}></div>
              <h3>Agents at Work</h3>
              <p>Our AI agents are analyzing your leads...</p>
            </div>
          ) : results.length > 0 ? (
            <Table data={results} loading={loading} />
          ) : (
            <div className="empty-state">
              <Sparkles size={48} color="var(--secondary-container)" style={{ margin: '0 auto 1rem' }} />
              <h3>Ready to Discover</h3>
              <p>Search for a company or upload an Excel file to get started.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
