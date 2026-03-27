import { useState } from 'react';
import { Mail, Phone, MessageSquare, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';

function SummaryCell({ profile }) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const text = (!profile || profile === "Not Available" || profile.includes("error"))
    ? "Profile data could not be fully extracted."
    : profile;

  const MAX_LENGTH = 150;
  const isLong = text.length > MAX_LENGTH;

  return (
    <div className="summary-cell-container">
      <div className={isExpanded ? "text-full" : "text-truncate-multi"}>
        {text}
      </div>
      {isLong && (
        <button 
          onClick={() => setIsExpanded(!isExpanded)}
          className="read-more-btn"
        >
          {isExpanded ? (
            <>Read Less <ChevronUp size={14} /></>
          ) : (
            <>Read More <ChevronDown size={14} /></>
          )}
        </button>
      )}
    </div>
  );
}

export function Table({ data, loading }) {
  return (
    <div className="table-container">
      {loading && (
        <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--on-surface-variant)' }}>
          <div className="loader" style={{ display: 'inline-block', verticalAlign: 'middle', marginRight: '0.5rem' }}></div>
          Processing more results...
        </div>
      )}
      <table className="custom-table" style={{ opacity: loading ? 0.5 : 1, transition: 'opacity 0.3s' }}>
        <thead>
          <tr>
            <th>Company</th>
            <th>Summary</th>
            <th>Contact</th>
            <th>Outreach Message</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, idx) => (
            <tr key={`${row.company}-${idx}`}>
              <td>
                <div className="company-name">
                  <span className="pulse-dot"></span>
                  {row.company}
                </div>
                {row.sources && row.sources.length > 0 && (
                  <a
                    href={row.sources[0]}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="badge"
                  >
                    Website <ExternalLink size={12} />
                  </a>
                )}
              </td>
              <td>
                <SummaryCell profile={row.profile} />
              </td>
              <td>
                <div className="contact-item">
                  <Mail size={16} className="contact-icon" />
                  <span>{row.contact?.email || 'Not Available'}</span>
                </div>
                <div className="contact-item">
                  <Phone size={16} className="contact-icon" />
                  <span>{row.contact?.phone || 'Not Available'}</span>
                </div>
                <div className="contact-item">
                  <MessageSquare size={16} className="contact-icon" />
                  <span>{row.contact?.whatsapp || 'Not Available'}</span>
                </div>
              </td>
              <td>
                <div className="message-box">
                  {row.message}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
