import { useRef, useEffect } from 'react';
import { Menu, Search, Wifi, WifiOff, FileText, Tag, BookOpen } from 'lucide-react';
import type { SearchSuggestion } from '../types';

interface HeaderProps {
  searchQuery: string;
  setSearchQuery: (val: string) => void;
  suggestions: SearchSuggestion[];
  showSuggestions: boolean;
  setShowSuggestions: (val: boolean) => void;
  isOnline: boolean;
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (val: boolean) => void;
  onSuggestionClick: (sug: SearchSuggestion) => void;
  onSearchSubmit: (query: string) => void;
}

export default function Header({
  searchQuery,
  setSearchQuery,
  suggestions,
  showSuggestions,
  setShowSuggestions,
  isOnline,
  sidebarCollapsed,
  setSidebarCollapsed,
  onSuggestionClick,
  onSearchSubmit
}: HeaderProps) {
  const searchRef = useRef<HTMLDivElement>(null);

  // Click outside search suggestions container to close it
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [setShowSuggestions]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      onSearchSubmit(searchQuery);
      setShowSuggestions(false);
    }
  };

  return (
    <header className="header">
      <button
        onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
        className="hamburger-btn"
      >
        <Menu size={20} />
      </button>

      <div className="search-container" ref={searchRef}>
        <div className="search-input-wrapper">
          <Search className="search-icon" size={18} />
          <input
            type="text"
            placeholder="Search presentations, slides, topics, authors..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setShowSuggestions(true);
            }}
            onFocus={() => setShowSuggestions(true)}
            onKeyDown={handleKeyDown}
            className="search-input"
          />
        </div>

        {showSuggestions && suggestions.length > 0 && (
          <div className="search-suggestions-dropdown">
            {suggestions.map((sug, index) => (
              <button
                key={index}
                onClick={() => {
                  onSuggestionClick(sug);
                  setShowSuggestions(false);
                }}
                className="suggestion-item"
              >
                {sug.type === 'title' && <BookOpen size={14} className="suggestion-icon text-indigo" />}
                {sug.type === 'tag' && <Tag size={14} className="suggestion-icon text-emerald" />}
                {sug.type === 'category' && <Tag size={14} className="suggestion-icon text-amber" />}
                {sug.type === 'author' && <FileText size={14} className="suggestion-icon text-rose" />}
                <div className="suggestion-content">
                  <span className="suggestion-text">{sug.text}</span>
                  <span className="suggestion-meta">{sug.type}</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div className={`connection-badge ${isOnline ? 'online' : 'offline'}`}>
          {isOnline ? <Wifi size={14} /> : <WifiOff size={14} />}
          <span>{isOnline ? 'Online' : 'Offline Mode'}</span>
        </div>
      </div>
    </header>
  );
}
