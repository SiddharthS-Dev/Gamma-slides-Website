import { Sparkles, Clock, Search } from 'lucide-react';
import type { AnalyticsSummary } from '../types';

interface DashboardTabProps {
  isLoadingDashboard: boolean;
  analyticsSummary: AnalyticsSummary | null;
  handleOpenDetail: (id: string) => void;
  setActiveTab: (tab: 'dashboard' | 'portal' | 'offline' | 'queue' | 'system') => void;
}

export default function DashboardTab({
  isLoadingDashboard,
  analyticsSummary,
  handleOpenDetail,
  setActiveTab
}: DashboardTabProps) {
  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      
      {/* Highlight metrics banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.05) 100%)',
          border: '1px solid rgba(99, 102, 241, 0.2)',
          borderRadius: 'var(--radius-lg)',
          padding: '32px',
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        <div style={{ position: 'relative', zIndex: 1, maxWidth: '600px' }}>
          <h2 style={{ fontSize: 'var(--text-2xl)', fontWeight: '700', marginBottom: '8px' }}>
            Welcome to <span className="text-gradient">SlideVault</span> Dashboard
          </h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)', lineHeight: '1.6' }}>
            Centralized discovery, semantic classification, and intelligence search platform. Automated AI indexing processes have cataloged enterprise slides across folders.
          </p>
          
          <button
            onClick={() => setActiveTab('portal')}
            className="btn btn-primary"
            style={{ marginTop: '20px' }}
          >
            <Search size={16} /> Explore Repository
          </button>
        </div>

        <div
          style={{
            position: 'absolute',
            right: '-40px',
            bottom: '-40px',
            width: '240px',
            height: '240px',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%)',
            filter: 'blur(30px)'
          }}
        />
      </div>

      {/* Counter Statistics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
        <div style={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)', padding: '20px', borderRadius: 'var(--radius-lg)' }}>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)', textTransform: 'uppercase' }}>Total Presentations</span>
          <div style={{ fontSize: 'var(--text-3xl)', fontWeight: '700', marginTop: '8px', color: 'var(--color-brand-start)' }}>
            {isLoadingDashboard ? '...' : analyticsSummary?.total_presentations}
          </div>
        </div>

        <div style={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)', padding: '20px', borderRadius: 'var(--radius-lg)' }}>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)', textTransform: 'uppercase' }}>Indexed Categories</span>
          <div style={{ fontSize: 'var(--text-3xl)', fontWeight: '700', marginTop: '8px', color: 'var(--color-brand-mid)' }}>
            {isLoadingDashboard ? '...' : analyticsSummary?.total_categories}
          </div>
        </div>

        <div style={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)', padding: '20px', borderRadius: 'var(--radius-lg)' }}>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)', textTransform: 'uppercase' }}>Total Views</span>
          <div style={{ fontSize: 'var(--text-3xl)', fontWeight: '700', marginTop: '8px', color: 'var(--color-accent-blue)' }}>
            {isLoadingDashboard ? '...' : analyticsSummary?.total_views}
          </div>
        </div>

        <div style={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)', padding: '20px', borderRadius: 'var(--radius-lg)' }}>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)', textTransform: 'uppercase' }}>Total Downloads</span>
          <div style={{ fontSize: 'var(--text-3xl)', fontWeight: '700', marginTop: '8px', color: 'var(--color-accent-emerald)' }}>
            {isLoadingDashboard ? '...' : analyticsSummary?.total_downloads}
          </div>
        </div>
      </div>

      {/* Lists of Trending / Recently Added Presentations */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
        
        {/* Trending list */}
        <div
          style={{
            background: 'var(--color-bg-secondary)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-lg)',
            padding: '20px'
          }}
        >
          <h3 style={{ fontSize: 'var(--text-base)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={16} style={{ color: 'var(--color-brand-start)' }} /> Trending Materials
          </h3>
          
          {isLoadingDashboard ? (
            <div className="spinner"></div>
          ) : (
            <div className="presentation-list">
              {analyticsSummary?.trending_presentations?.slice(0, 5).map((p) => (
                <div key={p.id} className="presentation-list-item" onClick={() => handleOpenDetail(p.id)}>
                  <div className="list-item-content">
                    <div className="list-item-title">{p.title}</div>
                    <div className="list-item-meta">
                      <span>Views: {p.view_count}</span>
                      <span>•</span>
                      <span>Popularity Score: {Math.round(p.popularity_score * 100) / 100}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recently added */}
        <div
          style={{
            background: 'var(--color-bg-secondary)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-lg)',
            padding: '20px'
          }}
        >
          <h3 style={{ fontSize: 'var(--text-base)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock size={16} style={{ color: 'var(--color-accent-cyan)' }} /> Recently Added Index
          </h3>
          
          {isLoadingDashboard ? (
            <div className="spinner"></div>
          ) : (
            <div className="presentation-list">
              {analyticsSummary?.recently_added?.slice(0, 5).map((p) => (
                <div key={p.id} className="presentation-list-item" onClick={() => handleOpenDetail(p.id)}>
                  <div className="list-item-content">
                    <div className="list-item-title">{p.title}</div>
                    <div className="list-item-meta">
                      <span>Added: {new Date(p.created_at).toLocaleDateString()}</span>
                      <span>•</span>
                      <span>{p.file_type.toUpperCase()}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
