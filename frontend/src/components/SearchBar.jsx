import { useState } from 'react';
import { Search, Upload, FileSpreadsheet } from 'lucide-react';

export function SearchBar({ onSearch, onExcelUpload, loading }) {
  const [company, setCompany] = useState('');
  const [location, setLocation] = useState('');
  const [file, setFile] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!company.trim()) return;
    onSearch(company, location);
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleProcessExcel = () => {
    if (file) {
      onExcelUpload(file);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit} className="search-controls">
        <div className="input-group">
          <label htmlFor="company" className="input-label">Company Name</label>
          <input
            id="company"
            type="text"
            className="input-field"
            placeholder="e.g. Freshworks"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            disabled={loading}
            required
          />
        </div>

        <div className="input-group">
          <label htmlFor="location" className="input-label">Location</label>
          <input
            id="location"
            type="text"
            className="input-field"
            placeholder="e.g. Chennai (Optional)"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            disabled={loading}
          />
        </div>

        <button type="submit" className="btn" disabled={loading || !company.trim()}>
          {loading ? <div className="loader"></div> : <Search size={20} />}
          Search Lead
        </button>
      </form>

      <div className="excel-upload-group">
        <div className="file-input-wrapper">
          <FileSpreadsheet size={22} color="var(--primary)" />
          <input
            type="file"
            accept=".xlsx, .xls"
            onChange={handleFileChange}
            disabled={loading}
          />
        </div>
        <button
          onClick={handleProcessExcel}
          className="btn btn-secondary"
          disabled={loading || !file}
        >
          {loading ? <div className="loader"></div> : <Upload size={20} />}
          Process Batch
        </button>
      </div>
    </div>
  );
}
