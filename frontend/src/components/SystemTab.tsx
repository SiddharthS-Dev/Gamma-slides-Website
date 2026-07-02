import { HardDrive, Cpu, Bookmark } from 'lucide-react';
import type { StorageStats, IngestionStatus } from '../types';

interface SystemTabProps {
  storageStats: StorageStats | null;
  ingestionStatus: IngestionStatus | null;
  systemActionLoading: string | null;
  runAdminAction: (action: 'reindex' | 'scan' | 'regenerate-thumbnails', label: string) => void;
}

export default function SystemTab({
  storageStats,
  ingestionStatus,
  systemActionLoading,
  runAdminAction
}: SystemTabProps) {
  
  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };
 
  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Storage and monitoring statistics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px' }}>
        <div style={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)', padding: '20px', borderRadius: 'var(--radius-lg)', display: 'flex', gap: '16px', alignItems: 'center' }}>
          <HardDrive size={32} style={{ color: 'var(--color-brand-start)' }} />
          <div>
            <span style={{ fontSize: '10px', color: 'var(--color-text-tertiary)' }}>TOTAL STORAGE SPACE</span>
            <div style={{ fontSize: 'var(--text-lg)', fontWeight: '700' }}>
              {storageStats ? formatBytes(storageStats.total_size_bytes) : '...'}
            </div>
          </div>
        </div>

        <div style={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)', padding: '20px', borderRadius: 'var(--radius-lg)', display: 'flex', gap: '16px', alignItems: 'center' }}>
          <Cpu size={32} style={{ color: 'var(--color-accent-blue)' }} />
          <div>
            <span style={{ fontSize: '10px', color: 'var(--color-text-tertiary)' }}>INGESTION ENGINE</span>
            <div style={{ fontSize: 'var(--text-lg)', fontWeight: '700', color: ingestionStatus?.is_running ? 'var(--color-success)' : 'var(--color-text-secondary)' }}>
              {ingestionStatus?.is_running ? 'Active Watch' : 'Inactive'}
            </div>
          </div>
        </div>

        <div style={{ background: 'var(--color-bg-secondary)', border: '1px solid var(--color-border)', padding: '20px', borderRadius: 'var(--radius-lg)', display: 'flex', gap: '16px', alignItems: 'center' }}>
          <Bookmark size={32} style={{ color: 'var(--color-accent-amber)' }} />
          <div>
            <span style={{ fontSize: '10px', color: 'var(--color-text-tertiary)' }}>CACHE & THUMBNAILS</span>
            <div style={{ fontSize: 'var(--text-lg)', fontWeight: '700' }}>
              {storageStats ? `${storageStats.thumbnail_count} images (${formatBytes(storageStats.thumbnail_size_bytes)})` : '...'}
            </div>
          </div>
        </div>
      </div>

      {/* Action operations controls */}
      <div
        style={{
          background: 'var(--color-bg-secondary)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px'
        }}
      >
        <h3 style={{ fontSize: 'var(--text-base)' }}>Operational Controls</h3>

        {/* Scan presentations folder */}
        <div style={{ display: 'flex', justifyItems: 'center', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--color-border)', paddingBottom: '16px' }}>
          <div>
            <h4 style={{ fontSize: 'var(--text-sm)', fontWeight: '600' }}>Scan Directory</h4>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)', marginTop: '2px' }}>
              Trigger folder watcher lookup to sync newly added files immediately.
            </p>
          </div>
          <button
            className="btn btn-primary btn-sm"
            disabled={systemActionLoading !== null}
            onClick={() => runAdminAction('scan', 'Directory Scan')}
          >
            {systemActionLoading === 'Directory Scan' ? 'Scanning...' : 'Run Scan'}
          </button>
        </div>

        {/* DB Full Reindexing */}
        <div style={{ display: 'flex', justifyItems: 'center', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--color-border)', paddingBottom: '16px' }}>
          <div>
            <h4 style={{ fontSize: 'var(--text-sm)', fontWeight: '600' }}>Force Database Reindexing</h4>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)', marginTop: '2px' }}>
              Clears current classification models and re-analyzes every presentation in the folder.
            </p>
          </div>
          <button
            className="btn btn-secondary btn-sm"
            disabled={systemActionLoading !== null}
            onClick={() => runAdminAction('reindex', 'Database Reindexing')}
          >
            {systemActionLoading === 'Database Reindexing' ? 'Reindexing...' : 'Force Reindex'}
          </button>
        </div>

        {/* Thumbnails regeneration */}
        <div style={{ display: 'flex', justifyItems: 'center', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h4 style={{ fontSize: 'var(--text-sm)', fontWeight: '600' }}>Regenerate Assets Thumbnails</h4>
            <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)', marginTop: '2px' }}>
              Wipes current preview cached items and re-extracts cover slides.
            </p>
          </div>
          <button
            className="btn btn-secondary btn-sm"
            disabled={systemActionLoading !== null}
            onClick={() => runAdminAction('regenerate-thumbnails', 'Thumbnail Generation')}
          >
            {systemActionLoading === 'Thumbnail Generation' ? 'Regenerating...' : 'Regenerate Cover'}
          </button>
        </div>
      </div>
    </div>
  );
}
