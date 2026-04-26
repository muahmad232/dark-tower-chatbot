import React from 'react';
import './ChatMessage.css';
import userIcon from '../../assests/icon/user-icon.png';
import towerIcon from '../../assests/icon/dark-tower-icon.png';

/**
 * Converts a single line of markdown-flavoured text into React inline elements.
 * Handles: **bold**, *italic*, and plain text — interleaved correctly.
 */
function renderInline(text, lineKey) {
  // Split on **...** and *...* markers, keeping the delimiters in the array
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={`${lineKey}-${i}`}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      return <em key={`${lineKey}-${i}`}>{part.slice(1, -1)}</em>;
    }
    return part; // plain text
  });
}

/**
 * Converts a multi-line markdown string into React nodes.
 * Supports:
 *   - **bold** and *italic* inline
 *   - Numbered lists  (lines starting with "1.", "2.", etc.)
 *   - Bullet lists    (lines starting with "- ", "• ", or "* ")
 *   - Blank lines     → paragraph break (a small gap)
 *   - Everything else → a <p> element
 */
function renderMarkdown(content) {
  const lines = content.split('\n');
  const nodes = [];
  let listItems = [];
  let listType = null; // 'ul' | 'ol'
  let key = 0;

  const flushList = () => {
    if (listItems.length === 0) return;
    if (listType === 'ol') {
      nodes.push(<ol key={key++} className="md-list">{listItems}</ol>);
    } else {
      nodes.push(<ul key={key++} className="md-list">{listItems}</ul>);
    }
    listItems = [];
    listType = null;
  };

  lines.forEach((line) => {
    const trimmed = line.trim();

    // Numbered list item: "1. text", "2. text", etc.
    const olMatch = trimmed.match(/^(\d+)\.\s+(.+)/);
    if (olMatch) {
      if (listType === 'ul') flushList();
      listType = 'ol';
      listItems.push(
        <li key={key++}>{renderInline(olMatch[2], key)}</li>
      );
      return;
    }

    // Bullet list item: "- text", "• text", "* text"
    const ulMatch = trimmed.match(/^[-•*]\s+(.+)/);
    if (ulMatch) {
      if (listType === 'ol') flushList();
      listType = 'ul';
      listItems.push(
        <li key={key++}>{renderInline(ulMatch[1], key)}</li>
      );
      return;
    }

    // Flush any pending list before a non-list line
    flushList();

    // Blank line → visual gap
    if (trimmed === '') {
      nodes.push(<div key={key++} className="md-spacer" />);
      return;
    }

    // Normal paragraph line
    nodes.push(
      <p key={key++} className="md-line">{renderInline(trimmed, key)}</p>
    );
  });

  flushList(); // flush any list still open at end of content
  return nodes;
}

function ChatMessage({ message }) {
  const isUser = message?.role === 'user';
  const content = message?.content || '';

  return (
    <div className={`message ${isUser ? 'user-message' : 'assistant-message'}`}>
      <div className="message-avatar">
        <img src={isUser ? userIcon : towerIcon} alt={isUser ? 'User' : 'KaGuide'} />
      </div>
      <div className="message-content">
        {isUser
          ? <p>{content}</p>           // user messages are plain text, no markdown needed
          : renderMarkdown(content)    // assistant responses get full markdown rendering
        }
      </div>
    </div>
  );
}

export default ChatMessage;
