import { Grid, List, AlertCircle, ArrowUpDown } from 'lucide-react';
import type { Category, Department, Presentation } from '../types';

interface PortalTabProps {
  categories: Category[];
  departments: Department[];
  presentations: Presentation[];
  isLoadingPortal: boolean;
  activeCategory: string;
  setActiveCategory: (val: string) => void;
  activeDepartment: string;
  setActiveDepartment: (val: string) => void;
  activeFileType: string;
  setActiveFileType: (val: string) => void;
  sortBy: string;
  setSortBy: (val: string) => void;
  sortOrder: 'asc' | 'desc';
  setSortOrder: (val: 'asc' | 'desc') => void;
  viewMode: 'grid' | 'list';
  setViewMode: (val: 'grid' | 'list') => void;
  currentPage: number;
  setCurrentPage: (page: number) => void;
  totalPages: number;
  totalPresentations: number;
  handleOpenDetail: (id: string) => void;
  downloadedIds: string[];
  isOnline: boolean;
  searchQuery: string;
  handleClearFilters: () => void;
}

export default function PortalTab({
  categories,
  departments,
  presentations,
  isLoadingPortal,
  activeCategory,
  setActiveCategory,
  activeDepartment,
  setActiveDepartment,
  activeFileType,
  setActiveFileType,
  sortBy,
  setSortBy,
  sortOrder,
  setSortOrder,
  viewMode,
  setViewMode,
  currentPage,
  setCurrentPage,
  totalPages,
  totalPresentations,
  handleOpenDetail,
  downloadedIds,
  isOnline,
  searchQuery,
  handleClearFilters
}: PortalTabProps) {
  
  const getCategoryColorClass = (name: string | undefined): string => {
    name = name?.toLowerCase() || '';
    if (name.includes('tech') || name.includes('dev') || name.includes('engine')) return 'category-blue';
    if (name.includes('sale') || name.includes('market') || name.includes('growth')) return 'category-indigo';
    if (name.includes('business') || name.includes('exec') || name.includes('strat')) return 'category-emerald';
    if (name.includes('finance') || name.includes('oper') || name.includes('legal')) return 'category-amber';
    if (name.includes('hr') || name.includes('talent') || name.includes('cultur')) return 'category-rose';
    return 'category-blue';
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const handleToggleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Category chip pills toolbar */}
      {categories.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <span style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Filter by Topic Category</span>
          <div className="category-chips-cloud">
            <button
              onClick={() => {
                setActiveCategory('');
                setCurrentPage(1);
              }}
              className={`category-chip-pill ${activeCategory === '' ? 'active' : ''}`}
            >
              All Topics
            </button>
            <button
              onClick={() => {
                setActiveCategory('unclassified');
                setCurrentPage(1);
              }}
              className={`category-chip-pill ${activeCategory === 'unclassified' ? 'active' : ''}`}
              style={{ borderColor: activeCategory === 'unclassified' ? 'transparent' : 'rgba(239, 68, 68, 0.3)', color: activeCategory === 'unclassified' ? 'white' : '#f87171' }}
            >
              Unclassified
            </button>
            {categories.filter(c => !c.parent_id).map((c) => (
              <button
                key={c.id}
                onClick={() => {
                  setActiveCategory(c.id);
                  setCurrentPage(1);
                }}
                className={`category-chip-pill ${getCategoryColorClass(c.name)} ${activeCategory === c.id ? 'active' : ''}`}
              >
                {c.name}
                {c.presentation_count !== undefined && (
                  <span className="pill-count-badge">{c.presentation_count}</span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Filters Toolbar */}
      <div
        style={{
          background: 'var(--color-bg-secondary)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px'
        }}
      >
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'center' }}>
          
          {/* Category Filter selector */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '10px', color: 'var(--color-text-tertiary)' }}>Category Selector</span>
            <select
              className="sort-select"
              value={activeCategory}
              onChange={(e) => {
                setActiveCategory(e.target.value);
                setCurrentPage(1);
              }}
              style={{ padding: '6px 32px 6px 12px', height: '36px' }}
            >
              <option value="">All Categories</option>
              <option value="unclassified">Unclassified</option>
              {categories.filter(c => !c.parent_id).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Department Filter selector */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '10px', color: 'var(--color-text-tertiary)' }}>Department</span>
            <select
              className="sort-select"
              value={activeDepartment}
              onChange={(e) => {
                setActiveDepartment(e.target.value);
                setCurrentPage(1);
              }}
              style={{ padding: '6px 32px 6px 12px', height: '36px' }}
            >
              <option value="">All Departments</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>

          {/* File Type Filter pills */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '10px', color: 'var(--color-text-tertiary)' }}>File Extension</span>
            <div style={{ display: 'flex', gap: '6px' }}>
              {['pptx', 'pdf', 'html'].map((ext) => (
                <button
                  key={ext}
                  className={`filter-chip ${activeFileType === ext ? 'active' : ''}`}
                  onClick={() => {
                    setActiveFileType(activeFileType === ext ? '' : ext);
                    setCurrentPage(1);
                  }}
                  style={{ padding: '6px 12px', height: '36px' }}
                >
                  {ext.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginLeft: 'auto' }}>
            <span style={{ fontSize: '10px', color: 'var(--color-text-tertiary)' }}>Layout Mode</span>
            <div className="view-toggle">
              <button
                className={`view-toggle-btn ${viewMode === 'grid' ? 'active' : ''}`}
                onClick={() => setViewMode('grid')}
              >
                <Grid size={16} />
              </button>
              <button
                className={`view-toggle-btn ${viewMode === 'list' ? 'active' : ''}`}
                onClick={() => setViewMode('list')}
              >
                <List size={16} />
              </button>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--color-border)', paddingTop: '12px', flexWrap: 'wrap', gap: '12px' }}>
          <div className="result-count">
            Found <strong>{totalPresentations}</strong> assets matching criteria
          </div>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            {/* Sort buttons */}
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => handleToggleSort('updated_at')}
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <ArrowUpDown size={12} /> Date {sortBy === 'updated_at' && (sortOrder === 'asc' ? '↑' : '↓')}
            </button>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => handleToggleSort('title')}
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <ArrowUpDown size={12} /> Name {sortBy === 'title' && (sortOrder === 'asc' ? '↑' : '↓')}
            </button>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => handleToggleSort('popularity_score')}
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <ArrowUpDown size={12} /> Hits {sortBy === 'popularity_score' && (sortOrder === 'asc' ? '↑' : '↓')}
            </button>

            {(activeCategory || activeDepartment || activeFileType || searchQuery) && (
              <button className="btn btn-ghost btn-sm" onClick={handleClearFilters}>
                Clear Filters
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Presentation Grid or List Result views */}
      {isLoadingPortal ? (
        // Skeleton loading state
        <div className="presentation-grid">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="skeleton skeleton-card" style={{ height: '220px' }}></div>
          ))}
        </div>
      ) : presentations.length === 0 ? (
        // Empty search result layout
        <div className="empty-state" style={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)' }}>
          <AlertCircle className="empty-state-icon" />
          <h3 className="empty-state-title">No Matches Found</h3>
          <p className="empty-state-description">
            Try checking spelling or simplifying tags, or click clear filters.
          </p>
        </div>
      ) : viewMode === 'grid' ? (
        // Grid render
        <div className="presentation-grid stagger-children">
          {presentations.map((p) => (
            <div key={p.id} className="presentation-card hover-lift" onClick={() => handleOpenDetail(p.id)}>
              <div className="card-thumbnail">
                <div className="card-thumbnail-placeholder">
                  {p.title.charAt(0).toUpperCase()}
                </div>
                {p.thumbnail_url && isOnline && (
                  <img src={`http://localhost:8000${p.thumbnail_url}`} alt={p.title} />
                )}
                <span className={`badge badge-${p.file_type.toLowerCase()} card-type-badge`}>
                  {p.file_type.toUpperCase()}
                </span>
                {downloadedIds.includes(p.id) && (
                  <span className="badge badge-success offline-ready-badge" style={{ position: 'absolute', bottom: '8px', left: '8px', zIndex: 2, fontSize: '9px' }}>
                    Offline Cache
                  </span>
                )}
              </div>
              <div className="card-body">
                <h3 className="card-title" title={p.title}>{p.title}</h3>
                <p className="card-description">{p.description || 'No description extracted.'}</p>
                
                <div className="card-meta">
                  <span>{p.slide_count || 12} slides</span>
                  <span>•</span>
                  <span
                    onClick={(e) => {
                      e.stopPropagation();
                      if (p.category) {
                        setActiveCategory(p.category.id);
                        setCurrentPage(1);
                      }
                    }}
                    className={`badge category-badge ${getCategoryColorClass(p.category?.name)}`}
                    style={{ cursor: 'pointer' }}
                  >
                    {p.category?.name || 'Unclassified'}
                  </span>
                </div>

                {p.tags.length > 0 && (
                  <div className="card-tags">
                    {p.tags.slice(0, 3).map((t, idx) => (
                      <span key={idx} className="badge badge-secondary" style={{ fontSize: '10px' }}>
                        #{t.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        // List render
        <div className="presentation-list stagger-children">
          {presentations.map((p) => (
            <div key={p.id} className="presentation-list-item" onClick={() => handleOpenDetail(p.id)}>
              <div className="list-item-thumbnail">
                <div className="card-thumbnail-placeholder" style={{ fontSize: '16px' }}>
                  {p.title.charAt(0).toUpperCase()}
                </div>
              </div>
              <div className="list-item-content">
                <div className="list-item-title">{p.title}</div>
                <div className="list-item-meta">
                  <span>Type: {p.file_type.toUpperCase()}</span>
                  <span>•</span>
                  <span
                    onClick={(e) => {
                      e.stopPropagation();
                      if (p.category) {
                        setActiveCategory(p.category.id);
                        setCurrentPage(1);
                      }
                    }}
                    className={`badge category-badge ${getCategoryColorClass(p.category?.name)}`}
                    style={{ cursor: 'pointer' }}
                  >
                    Category: {p.category?.name || 'Unclassified'}
                  </span>
                  <span>•</span>
                  <span>Views: {p.view_count}</span>
                  {downloadedIds.includes(p.id) && (
                    <>
                      <span>•</span>
                      <span className="badge badge-success" style={{ fontSize: '9px' }}>Offline Cache</span>
                    </>
                  )}
                </div>
              </div>
              <div className="list-item-actions">
                <span className="badge badge-secondary">{formatBytes(p.file_size)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination elements */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '16px', marginTop: '12px' }}>
          <button
            className="btn btn-secondary btn-sm"
            disabled={currentPage <= 1}
            onClick={() => setCurrentPage(currentPage - 1)}
          >
            Previous
          </button>
          <span style={{ fontSize: 'var(--text-sm)' }}>
            Page <strong>{currentPage}</strong> of <strong>{totalPages}</strong>
          </span>
          <button
            className="btn btn-secondary btn-sm"
            disabled={currentPage >= totalPages}
            onClick={() => setCurrentPage(currentPage + 1)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
