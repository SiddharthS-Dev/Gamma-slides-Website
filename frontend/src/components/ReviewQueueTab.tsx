import { X, Check, CheckCircle } from 'lucide-react';
import type { Category } from '../types';

interface ReviewQueueTabProps {
  reviewQueue: any[];
  isLoadingQueue: boolean;
  selectedReviewItem: any | null;
  handleSelectReviewItem: (item: any) => void;
  setSelectedReviewItem: (item: any | null) => void;
  categories: Category[];
  reviewCategory: string;
  setReviewCategory: (val: string) => void;
  reviewTags: string[];
  reviewNotes: string;
  setReviewNotes: (val: string) => void;
  handleReviewAction: (action: 'accept' | 'modify') => void;
}

export default function ReviewQueueTab({
  reviewQueue,
  isLoadingQueue,
  selectedReviewItem,
  handleSelectReviewItem,
  setSelectedReviewItem,
  categories,
  reviewCategory,
  setReviewCategory,
  reviewTags,
  reviewNotes,
  setReviewNotes,
  handleReviewAction
}: ReviewQueueTabProps) {
  return (
    <div className="animate-fade-in" style={{ display: 'grid', gridTemplateColumns: selectedReviewItem ? '1fr 1fr' : '1fr', gap: '24px' }}>
      
      {/* Queue List */}
      <div
        style={{
          background: 'var(--color-bg-secondary)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          padding: '20px',
          alignSelf: 'start'
        }}
      >
        <h3 style={{ fontSize: 'var(--text-base)', marginBottom: '16px' }}>
          Assets Awaiting Classification Review
        </h3>

        {isLoadingQueue ? (
          <div className="spinner"></div>
        ) : reviewQueue.length === 0 ? (
          <div className="empty-state">
            <CheckCircle size={32} style={{ color: 'var(--color-success)', marginBottom: '12px' }} />
            <h4 className="empty-state-title">Queue is Empty</h4>
            <p className="empty-state-description">
              All ingested presentations have been reviewed and classified.
            </p>
          </div>
        ) : (
          <div className="presentation-list">
            {reviewQueue.map((item) => (
              <div
                key={item.id}
                className={`presentation-list-item ${selectedReviewItem?.id === item.id ? 'active' : ''}`}
                onClick={() => handleSelectReviewItem(item)}
              >
                <div className="list-item-content">
                  <div className="list-item-title">{item.title}</div>
                  <div className="list-item-meta">
                    <span className="badge badge-secondary" style={{ fontSize: '10px' }}>
                      AI Category: {item.ai_category || 'None'}
                    </span>
                    <span>Confidence: {Math.round(item.ai_confidence * 100)}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Selected Review Panel */}
      {selectedReviewItem && (
        <div
          className="animate-scale-in"
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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: 'var(--text-base)' }}>Review Classification</h3>
            <button className="btn btn-ghost btn-icon" onClick={() => setSelectedReviewItem(null)}>
              <X size={16} />
            </button>
          </div>

          <div>
            <span style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', textTransform: 'uppercase' }}>Asset Title</span>
            <h4 style={{ fontSize: 'var(--text-sm)', marginTop: '4px', fontWeight: '600' }}>
              {selectedReviewItem.title}
            </h4>
          </div>

          {/* Override Category */}
          <div>
            <span style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', textTransform: 'uppercase' }}>Verify Category</span>
            <select
              className="sort-select"
              value={reviewCategory}
              onChange={(e) => setReviewCategory(e.target.value)}
              style={{ width: '100%', padding: '8px 12px', marginTop: '6px' }}
            >
              <option value="">Choose Category...</option>
              {categories.filter(c => !c.parent_id).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Tag preview */}
          <div>
            <span style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', textTransform: 'uppercase' }}>Associated Tags</span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '6px' }}>
              {reviewTags.map((tagText, idx) => (
                <span key={idx} className="badge badge-secondary">
                  #{tagText}
                </span>
              ))}
            </div>
          </div>

          {/* Notes textbox */}
          <div>
            <span style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', textTransform: 'uppercase' }}>Reviewer Notes</span>
            <textarea
              placeholder="Add any validation comments or overrides rationale..."
              style={{
                width: '100%',
                height: '70px',
                background: 'var(--color-bg-tertiary)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                padding: '10px',
                marginTop: '6px',
                fontSize: 'var(--text-sm)',
                resize: 'none'
              }}
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
            />
          </div>

          {/* Actions buttons */}
          <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
            <button
              className="btn btn-primary"
              style={{ flex: 1 }}
              onClick={() => handleReviewAction('accept')}
            >
              <Check size={16} /> Approve AI
            </button>
            <button
              className="btn btn-secondary"
              style={{ flex: 1 }}
              onClick={() => handleReviewAction('modify')}
            >
              Modify & Save
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
