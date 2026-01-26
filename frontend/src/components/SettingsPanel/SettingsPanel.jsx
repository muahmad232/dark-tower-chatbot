import React from 'react';
import './SettingsPanel.css';

const BOOKS = [
  { id: 1, title: "The Gunslinger" },
  { id: 2, title: "The Drawing of the Three" },
  { id: 3, title: "The Waste Lands" },
  { id: 4, title: "Wizard and Glass" },
  { id: 5, title: "Wolves of the Calla" },
  { id: 6, title: "Song of Susannah" },
  { id: 7, title: "The Dark Tower" },
  { id: 8, title: "The Wind Through the Keyhole" }
];

function SettingsPanel({ settings, setSettings, onClose }) {
  return (
    <div className="settings-panel">
      <h3>⚙️ Settings</h3>
      
      <div className="setting-item">
        <label>
          <input
            type="checkbox"
            checked={settings.spoilerMode}
            onChange={(e) => setSettings(prev => ({ ...prev, spoilerMode: e.target.checked }))}
          />
          <span>Spoiler Mode</span>
        </label>
        <small>Enable to allow spoilers from any book</small>
      </div>

      {!settings.spoilerMode && (
        <div className="setting-item">
          <label>
            <span>Book Progress</span>
          </label>
          <small>I've read up to:</small>
          <select
            value={settings.bookLimit}
            onChange={(e) => setSettings(prev => ({ ...prev, bookLimit: parseInt(e.target.value) }))}
          >
            {BOOKS.map(book => (
              <option key={book.id} value={book.id}>
                {book.id}. {book.title}
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="setting-item">
        <label>
          <input
            type="checkbox"
            checked={settings.showSources}
            onChange={(e) => setSettings(prev => ({ ...prev, showSources: e.target.checked }))}
          />
          <span>Show Sources</span>
        </label>
        <small>Display wiki source links with answers</small>
      </div>

      <button className="close-settings-btn" onClick={onClose}>
        Save Settings
      </button>
    </div>
  );
}

export default SettingsPanel;
