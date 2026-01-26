import React from 'react';
import './ChatMessage.css';
import userIcon from '../../assests/icon/user-icon.png';
import towerIcon from '../../assests/icon/dark-tower-icon.png';

function ChatMessage({ message }) {
  const isUser = message?.role === 'user';
  const content = message?.content || '';
  
  return (
    <div className={`message ${isUser ? 'user-message' : 'assistant-message'}`}>
      <div className="message-avatar">
        <img src={isUser ? userIcon : towerIcon} alt={isUser ? 'User' : 'KaGuide'} />
      </div>
      <div className="message-content">
        {content.split('\n').map((line, i) => (
          <p key={i}>{line || '\u00A0'}</p>
        ))}
      </div>
    </div>
  );
}

export default ChatMessage;
