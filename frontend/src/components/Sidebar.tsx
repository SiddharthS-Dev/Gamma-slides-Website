import { Sparkles, BarChart3, BookOpen, Smartphone, Tag, Settings, ShieldAlert, ChevronLeft, ChevronRight } from 'lucide-react';
import type { Category } from '../types';

interface SidebarProps {
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (val: boolean) => void;
  activeTab: 'dashboard' | 'portal' | 'offline' | 'queue' | 'system';
  setActiveTab: (tab: 'dashboard' | 'portal' | 'offline' | 'queue' | 'system') => void;
  categories: Category[];
  activeCategory: string;
  setActiveCategory: (cat: string) => void;
  downloadedCount: number;
  setSelectedPresId: (id: string | null) => void;
  setShowFileViewer: (val: boolean) => void;
  setCurrentPage: (page: number) => void;
}

export default function Sidebar({
  sidebarCollapsed,
  setSidebarCollapsed,
  activeTab,
  setActiveTab,
  categories,
  activeCategory,
  setActiveCategory,
  downloadedCount,
  setSelectedPresId,
  setShowFileViewer,
  setCurrentPage
}: SidebarProps) {
  
  const getCategoryColorClass = (name: string): string => {
    name = name.toLowerCase();
    if (name.includes('tech') || name.includes('dev') || name.includes('engine')) return 'category-blue';
    if (name.includes('sale') || name.includes('market') || name.includes('growth')) return 'category-indigo';
    if (name.includes('business') || name.includes('exec') || name.includes('strat')) return 'category-emerald';
    if (name.includes('finance') || name.includes('oper') || name.includes('legal')) return 'category-amber';
    if (name.includes('hr') || name.includes('talent') || name.includes('cultur')) return 'category-rose';
    return 'category-blue';
  };

  const handleTabChange = (tab: 'dashboard' | 'portal' | 'offline' | 'queue' | 'system') => {
    setSelectedPresId(null);
    setShowFileViewer(false);
    setActiveTab(tab);
    if (tab === 'portal') {
      setCurrentPage(1);
    }
  };

  const handleCategoryChange = (catId: string) => {
    setSelectedPresId(null);
    setShowFileViewer(false);
    setActiveCategory(catId);
    setActiveTab('portal');
    setCurrentPage(1);
  };

  return (
    <aside className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <Sparkles className="animate-pulse" size={20} color="#fff" />
        </div>
        {!sidebarCollapsed && <span className="sidebar-logo-text text-gradient">SlideVault</span>}
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section">
          {!sidebarCollapsed && <div className="nav-section-title">Navigation</div>}
          <button
            onClick={() => handleTabChange('dashboard')}
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
          >
            <BarChart3 className="nav-item-icon" />
            {!sidebarCollapsed && <span>Dashboard</span>}
          </button>
          <button
            onClick={() => handleTabChange('portal')}
            className={`nav-item ${activeTab === 'portal' ? 'active' : ''}`}
          >
            <BookOpen className="nav-item-icon" />
            {!sidebarCollapsed && <span>Browse Portal</span>}
          </button>
          <button
            onClick={() => handleTabChange('offline')}
            className={`nav-item ${activeTab === 'offline' ? 'active' : ''}`}
          >
            <Smartphone className="nav-item-icon" />
            {!sidebarCollapsed && <span>Offline Downloads</span>}
            {!sidebarCollapsed && downloadedCount > 0 && (
              <span className="nav-item-badge">{downloadedCount}</span>
            )}
          </button>
        </div>

        {/* Quick Categories list */}
        {!sidebarCollapsed && categories.length > 0 && (
          <div className="nav-section">
            <div className="nav-section-title" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Tag size={12} /> Category Index
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', padding: '0 8px' }}>
              <button
                onClick={() => handleCategoryChange('')}
                className={`sidebar-category-link ${activeCategory === '' ? 'active' : ''}`}
              >
                <span className="category-color-dot" style={{ background: 'var(--color-text-tertiary)' }}></span>
                <span className="category-link-name">All Categories</span>
              </button>
              <button
                onClick={() => handleCategoryChange('unclassified')}
                className={`sidebar-category-link unclassified ${activeCategory === 'unclassified' ? 'active' : ''}`}
              >
                <span className="category-color-dot" style={{ background: '#ef4444' }}></span>
                <span className="category-link-name">Unclassified</span>
              </button>
              {categories.filter(cat => !cat.parent_id).map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => handleCategoryChange(cat.id)}
                  className={`sidebar-category-link ${activeCategory === cat.id ? 'active' : ''}`}
                >
                  <span className={`category-color-dot ${getCategoryColorClass(cat.name)}`}></span>
                  <span className="category-link-name">{cat.name}</span>
                  {cat.presentation_count !== undefined && (
                    <span className="category-link-count">{cat.presentation_count}</span>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="nav-section">
          {!sidebarCollapsed && <div className="nav-section-title">Administration</div>}
          <button
            onClick={() => handleTabChange('queue')}
            className={`nav-item ${activeTab === 'queue' ? 'active' : ''}`}
          >
            <ShieldAlert className="nav-item-icon" />
            {!sidebarCollapsed && <span>Review Queue</span>}
          </button>
          <button
            onClick={() => handleTabChange('system')}
            className={`nav-item ${activeTab === 'system' ? 'active' : ''}`}
          >
            <Settings className="nav-item-icon" />
            {!sidebarCollapsed && <span>System Settings</span>}
          </button>
        </div>
      </nav>

      <button
        onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
        className="sidebar-toggle"
      >
        {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>
    </aside>
  );
}
