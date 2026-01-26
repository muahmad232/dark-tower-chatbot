import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import icon from '../../assests/icon/dark-tower-icon.png';
import './Header.css';

function Header({ onSettingsClick, showSettings = false }) {
  const location = useLocation();
  
  return (
    <header className="header">
      <Link to="/" className="header-content">
        <img src={icon} alt="Dark Tower" className="header-icon" />
        <div>
          <h1 className="header-title">KaGuide</h1>
          <span className="header-subtitle">Your Dark Tower Companion</span>
        </div>
      </Link>
      
      <nav className="header-nav">
        <Link 
          to="/" 
          className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
        >
          Home
        </Link>
        <Link 
          to="/chat" 
          className={`nav-link ${location.pathname === '/chat' ? 'active' : ''}`}
        >
          Chat
        </Link>
        <Link 
          to="/about" 
          className={`nav-link ${location.pathname === '/about' ? 'active' : ''}`}
        >
          About
        </Link>
        
        {showSettings && (
          <button className="settings-btn" onClick={onSettingsClick}>
            ⚙️
          </button>
        )}
      </nav>
    </header>
  );
}

export default Header;
