import React, { useState } from 'react';
import Header from '../../components/Header';
import Footer from '../../components/Footer';
import SettingsPanel from '../../components/SettingsPanel';
import ChatMessage from '../../components/ChatMessage';
import towerIcon from '../../assests/icon/dark-tower-icon.png';
import './Chat.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const BOOKS = [
  "The Gunslinger",
  "The Drawing of the Three",
  "The Waste Lands",
  "Wizard and Glass",
  "Wolves of the Calla",
  "Song of Susannah",
  "The Dark Tower",
  "The Wind Through the Keyhole"
];

function Chat() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hile, traveler! I am KaGuide, keeper of the Dark Tower's lore. Long days and pleasant nights to you.\n\nI walk beside those who follow the Path of the Beam, offering knowledge without spoiling the journey ahead. Tell me, how far have you traveled in your reading? Set your book progress in the settings, and ask what you will about Mid-World, the ka-tet, or any mystery that plagues your mind.\n\nWhat would you know, sai?"
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState({
    spoilerMode: false,
    bookLimit: 1,
    showSources: true
  });

  // Convert book number to book name for API
  const getBookName = (bookNum) => {
    if (settings.spoilerMode) return null;
    return BOOKS[bookNum - 1] || null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // --------------- Session memory ---------------
      // sessionStorage is tab-scoped: it survives page refreshes within the
      // same tab but is automatically cleared the moment the tab is closed.
      // This gives us zero-persistence-after-close without any database.
      const currentSessionId = sessionStorage.getItem('ka_session_id') || null;
      // -----------------------------------------------

      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: input,
          spoiler_mode: settings.spoilerMode,
          book_limit: getBookName(settings.bookLimit),
          show_sources: settings.showSources,
          // null on the first message → server mints a fresh UUID and returns it
          session_id: currentSessionId,
        })
      });

      const data = await response.json();

      // Save the server-assigned session_id so subsequent messages are
      // linked to the same conversation history on the backend.
      if (data.session_id) {
        sessionStorage.setItem('ka_session_id', data.session_id);
      }
      
      // Build response with optional sources
      let responseText = data.answer || "I could not find an answer, sai.";
      if (settings.showSources && data.sources && data.sources.length > 0) {
        responseText += `\n\n📚 Sources: ${data.sources.join(', ')}`;
      }
      
      setMessages(prev => [...prev, { role: 'assistant', content: responseText }]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: "The Crimson King's interference has disrupted our connection. The path forward is temporarily blocked. Try again, sai."
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="page chat-page">
      <div className="background-overlay"></div>
      <Header 
        onSettingsClick={() => setShowSettings(!showSettings)} 
        showSettings={true}
      />
      
      {showSettings && (
        <SettingsPanel 
          settings={settings}
          setSettings={setSettings}
          onClose={() => setShowSettings(false)}
        />
      )}

      <main className="chat-container">
        <div className="messages">
          {messages.map((msg, idx) => (
            <ChatMessage key={idx} message={msg} />
          ))}
          
          {isLoading && (
            <div className="message assistant-message">
              <div className="message-avatar"><img src={towerIcon} alt="KaGuide" /></div>
              <div className="message-content">
                <div className="loading">
                  <span className="loading-dot">•</span>
                  <span className="loading-dot">•</span>
                  <span className="loading-dot">•</span>
                </div>
              </div>
            </div>
          )}
        </div>

        <form className="input-form" onSubmit={handleSubmit}>
          <input
            type="text"
            className="message-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about the Dark Tower..."
            disabled={isLoading}
          />
          <button type="submit" className="send-btn" disabled={isLoading}>
            ➤
          </button>
        </form>
      </main>

      <Footer />
    </div>
  );
}

export default Chat;
