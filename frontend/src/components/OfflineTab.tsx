import { Smartphone } from 'lucide-react';
import type { Presentation } from '../types';

interface OfflineTabProps {
  offlinePresentations: Presentation[];
  isLoadingOfflineTab: boolean;
  handleOpenDetail: (id: string) => void;
}

export default function OfflineTab({
  offlinePresentations,
  isLoadingOfflineTab,
  handleOpenDetail
}: OfflineTabProps) {
  
  const getCategoryColorClass = (name: string | undefined): string => {
    name = name?.toLowerCase() || '';
    if (name.includes('tech') || name.includes('dev') || name.includes('engine')) return 'category-blue';
    if (name.includes('sale') || name.includes('market') || name.includes('growth')) return 'category-indigo';
    if (name.includes('business') || name.includes('exec') || name.includes('strat')) return 'category-emerald';
    if (name.includes('finance') || name.includes('oper') || name.includes('legal')) return 'category-amber';
    if (name.includes('hr') || name.includes('talent') || name.includes('cultur')) return 'category-rose';
    return 'category-blue';
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      <div style={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)', padding: '20px', borderRadius: 'var(--radius-lg)' }}>
        <h2 style={{ fontSize: 'var(--text-xl)', fontWeight: '600', marginBottom: '8px' }}>
          Offline Saved Collection ({offlinePresentations.length})
        </h2>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-xs)' }}>
          These presentations have been downloaded and cached in your browser. They are fully interactive, searchable, and readable even when you are disconnected from the network.
        </p>
      </div>

      {isLoadingOfflineTab ? (
        <div className="presentation-grid">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="skeleton skeleton-card" style={{ height: '220px' }}></div>
          ))}
        </div>
      ) : offlinePresentations.length === 0 ? (
        <div className="empty-state" style={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)' }}>
          <Smartphone className="empty-state-icon" style={{ opacity: 0.3 }} />
          <h3 className="empty-state-title">No Offline Files Found</h3>
          <p className="empty-state-description">
            Browse the portal while connected and view any presentation to automatically download it to your local offline vault.
          </p>
        </div>
      ) : (
        <div className="presentation-grid stagger-children">
          {offlinePresentations.map((p) => (
            <div key={p.id} className="presentation-card hover-lift" onClick={() => handleOpenDetail(p.id)}>
              <div className="card-thumbnail">
                <div className="card-thumbnail-placeholder">
                  {p.title.charAt(0).toUpperCase()}
                </div>
                <span className={`badge badge-${p.file_type.toLowerCase()} card-type-badge`}>
                  {p.file_type.toUpperCase()}
                </span>
                <span className="badge badge-success offline-ready-badge" style={{ position: 'absolute', bottom: '8px', left: '8px', zIndex: 2, fontSize: '9px' }}>
                  Offline Cache
                </span>
              </div>
              <div className="card-body">
                <h3 className="card-title" title={p.title}>{p.title}</h3>
                <p className="card-description">{p.description || 'No description extracted.'}</p>
                
                <div className="card-meta">
                  <span>{p.slide_count || 12} slides</span>
                  <span>•</span>
                  <span className={`badge category-badge ${getCategoryColorClass(p.category?.name)}`}>
                    {p.category?.name || 'Unclassified'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
