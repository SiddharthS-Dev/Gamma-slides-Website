import {
  Play, Download, Maximize2, Minimize2, ChevronLeft, ChevronRight,
  WifiOff, Eye, Bookmark, Trash2, Tag, FileText
} from 'lucide-react';
import type {
  PresentationDetail, AISummary, AIKeyword,
  RecommendationSet, QualityScores, Bookmark as BookmarkType, SlideContentResponse
} from '../types';

interface DetailModalProps {
  selectedPresId: string;
  setSelectedPresId: (id: string | null) => void;
  selectedPres: PresentationDetail | null;
  downloadedIds: string[];
  isOnline: boolean;
  showFileViewer: boolean;
  handleToggleViewer: (val: boolean) => void;
  API_BASE: string;
  viewerMode: 'slides' | 'document';
  setViewerMode: (mode: 'slides' | 'document') => void;
  fullViewMode: boolean;
  setFullViewMode: (val: boolean) => void;
  isLoadingSlides: boolean;
  slidesResponse: SlideContentResponse | null;
  currentViewerSlide: number;
  setCurrentViewerSlide: (num: number) => void;
  setNewBookmarkSlide: (num: number) => void;
  localIframeUrls: Record<string, string>;
  activeDetailTab: 'summary' | 'ai' | 'recs' | 'quality' | 'bookmarks';
  setActiveDetailTab: (tab: 'summary' | 'ai' | 'recs' | 'quality' | 'bookmarks') => void;
  selectedPresSummary: AISummary | null;
  selectedPresKeywords: AIKeyword[];
  selectedPresRecs: RecommendationSet | null;
  selectedPresQuality: QualityScores | null;
  selectedPresBookmarks: BookmarkType[];
  newBookmarkSlide: number;
  newBookmarkNote: string;
  setNewBookmarkNote: (note: string) => void;
  handleAddBookmark: () => void;
  handleDeleteBookmark: (id: string) => void;
  handleOpenDetail: (id: string) => void;
  setActiveCategory: (cat: string) => void;
  setActiveDepartment: (dept: string) => void;
  setActiveTab: (tab: 'dashboard' | 'portal' | 'offline' | 'queue' | 'system') => void;
  setCurrentPage: (page: number) => void;
}

export default function DetailModal({
  selectedPresId,
  setSelectedPresId,
  selectedPres,
  downloadedIds,
  isOnline,
  showFileViewer,
  handleToggleViewer,
  API_BASE,
  viewerMode,
  setViewerMode,
  fullViewMode,
  setFullViewMode,
  isLoadingSlides,
  slidesResponse,
  currentViewerSlide,
  setCurrentViewerSlide,
  setNewBookmarkSlide,
  localIframeUrls,
  activeDetailTab,
  setActiveDetailTab,
  selectedPresSummary,
  selectedPresKeywords,
  selectedPresRecs,
  selectedPresQuality,
  selectedPresBookmarks,
  newBookmarkSlide,
  newBookmarkNote,
  setNewBookmarkNote,
  handleAddBookmark,
  handleDeleteBookmark,
  handleOpenDetail,
  setActiveCategory,
  setActiveDepartment,
  setActiveTab,
  setCurrentPage
}: DetailModalProps) {
  
  const getCategoryColorClass = (name: string): string => {
    name = name?.toLowerCase() || '';
    if (name.includes('tech') || name.includes('dev') || name.includes('engine')) return 'category-blue';
    if (name.includes('sale') || name.includes('market') || name.includes('growth')) return 'category-indigo';
    if (name.includes('business') || name.includes('exec') || name.includes('strat')) return 'category-emerald';
    if (name.includes('finance') || name.includes('oper') || name.includes('legal')) return 'category-amber';
    if (name.includes('hr') || name.includes('talent') || name.includes('cultur')) return 'category-rose';
    return 'category-blue';
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Header Title Information card */}
      <div
        style={{
          background: 'var(--color-bg-secondary)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          padding: '24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: '16px'
        }}
      >
        <div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center', marginBottom: '8px' }}>
            {selectedPres?.file_type && (
              <span className={`badge badge-${selectedPres.file_type.toLowerCase()}`}>
                {selectedPres.file_type.toUpperCase()}
              </span>
            )}
            {selectedPres && selectedPres.category && (
              <span
                onClick={() => {
                  setActiveCategory(selectedPres.category!.id);
                  setActiveTab('portal');
                  setCurrentPage(1);
                }}
                className={`badge category-badge ${getCategoryColorClass(selectedPres.category.name)}`}
                style={{ cursor: 'pointer' }}
                title="View other presentations in this category"
              >
                {selectedPres.category.name}
              </span>
            )}
            {selectedPres && selectedPres.department && (
              <span
                onClick={() => {
                  setActiveDepartment(selectedPres.department!.id);
                  setActiveTab('portal');
                  setCurrentPage(1);
                }}
                className="badge badge-secondary"
                style={{ cursor: 'pointer' }}
                title="View other presentations in this department"
              >
                {selectedPres.department.name}
              </span>
            )}
            {downloadedIds.includes(selectedPresId) && (
              <span className="badge badge-success offline-ready-badge" style={{ fontSize: '10px' }}>
                Offline Cache Enabled
              </span>
            )}
          </div>
          <h1 style={{ fontSize: 'var(--text-2xl)', marginBottom: '8px' }}>
            {selectedPres ? selectedPres.title : 'Loading metadata...'}
          </h1>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)' }}>
            {selectedPres?.description || 'No description provided.'}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => handleToggleViewer(!showFileViewer)}
            className="btn btn-primary"
            disabled={!selectedPres}
          >
            <Play size={16} /> {showFileViewer ? 'Close Viewer' : 'View Presentation'}
          </button>
          {isOnline && (
            <a
              href={`${API_BASE}/presentations/${selectedPresId}/download`}
              target="_blank"
              rel="noreferrer"
              className="btn btn-secondary"
            >
              <Download size={16} /> Download
            </a>
          )}
        </div>
      </div>

      {/* Two Panel Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: showFileViewer ? (fullViewMode ? '1fr' : '1.2fr 1fr') : '1fr', gap: '24px' }}>
        
        {/* Visual Presenter Layer (Shown when user clicks "View Presentation") */}
        {showFileViewer && selectedPres && (
          <div
            className="animate-scale-in"
            style={{
              background: 'var(--color-bg-secondary)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-lg)',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
              alignSelf: 'start'
            }}
          >
            {/* View mode toggle: Exact Document vs Struct Slide text */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
              <div style={{ display: 'flex', background: 'var(--color-bg-tertiary)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '2px' }}>
                <button
                  onClick={() => setViewerMode('document')}
                  className={`btn btn-sm ${viewerMode === 'document' ? 'btn-primary' : 'btn-ghost'}`}
                  style={{ borderRadius: 'var(--radius-sm)' }}
                >
                  Exact Presentation File
                </button>
                <button
                  onClick={() => setViewerMode('slides')}
                  className={`btn btn-sm ${viewerMode === 'slides' ? 'btn-primary' : 'btn-ghost'}`}
                  style={{ borderRadius: 'var(--radius-sm)' }}
                >
                  Intelligent Slide Viewer
                </button>
              </div>
              <button
                onClick={() => setFullViewMode(!fullViewMode)}
                className={`btn btn-sm ${fullViewMode ? 'btn-primary' : 'btn-ghost'}`}
                style={{ display: 'flex', alignItems: 'center', gap: '6px', border: '1px solid var(--color-border)' }}
                title={fullViewMode ? 'Exit full view' : 'Expand to full view'}
              >
                {fullViewMode ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
                {fullViewMode ? 'Split View' : 'Full View'}
              </button>
            </div>

            {/* Render Interactive Presentation Frame */}
            {viewerMode === 'slides' ? (
              isLoadingSlides ? (
                <div className="slide-loader-container">
                  <div className="spinner"></div>
                  <span>Extracting slide structure...</span>
                </div>
              ) : slidesResponse && slidesResponse.slides.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {/* Interactive Slide Viewer Canvas */}
                  <div className="slide-canvas" style={fullViewMode ? { aspectRatio: 'unset', minHeight: '60vh' } : undefined}>
                    {/* Slide Content Layout */}
                    <div className="slide-inner-content">
                      <span className="slide-number-indicator">
                        Slide {currentViewerSlide} of {slidesResponse.total_slides}
                      </span>
                      
                      {/* Slide Title */}
                      <h2 className="slide-heading text-gradient">
                        {slidesResponse.slides[currentViewerSlide - 1]?.heading || 'Untitled Slide'}
                      </h2>
                      
                      {/* Slide Body */}
                      <div className="slide-body-content" style={fullViewMode ? { maxHeight: 'none' } : undefined}>
                        {slidesResponse.slides[currentViewerSlide - 1]?.body ? (
                          slidesResponse.slides[currentViewerSlide - 1].body.split('\n').map((line, idx) => (
                            <p key={idx}>{line}</p>
                          ))
                        ) : (
                          <p style={{ opacity: 0.4, fontStyle: 'italic' }}>No slide text content extracted.</p>
                        )}
                      </div>
                    </div>

                    {/* Speaker Notes Drawer */}
                    {slidesResponse.slides[currentViewerSlide - 1]?.speaker_notes && (
                      <div className="speaker-notes-container">
                        <div className="speaker-notes-title">
                          <FileText size={12} /> Speaker Notes
                        </div>
                        <p className="speaker-notes-text">
                          {slidesResponse.slides[currentViewerSlide - 1].speaker_notes}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Navigation controls */}
                  <div style={{ display: 'flex', justifyItems: 'center', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
                    <button
                      className="btn btn-secondary btn-sm"
                      disabled={currentViewerSlide <= 1}
                      onClick={() => {
                        setCurrentViewerSlide(currentViewerSlide - 1);
                        setNewBookmarkSlide(currentViewerSlide - 1);
                      }}
                    >
                      <ChevronLeft size={16} /> Prev Slide
                    </button>
                    
                    <span style={{ fontSize: 'var(--text-sm)' }}>
                      Slide <strong>{currentViewerSlide}</strong> of <strong>{slidesResponse.total_slides}</strong>
                    </span>

                    <button
                      className="btn btn-secondary btn-sm"
                      disabled={currentViewerSlide >= slidesResponse.total_slides}
                      onClick={() => {
                        setCurrentViewerSlide(currentViewerSlide + 1);
                        setNewBookmarkSlide(currentViewerSlide + 1);
                      }}
                    >
                      Next Slide <ChevronRight size={16} />
                    </button>
                  </div>
                </div>
              ) : (
                <div className="slide-canvas" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '260px', flexDirection: 'column', gap: '12px' }}>
                  <span>No slide structure extracted for this presentation.</span>
                </div>
              )
            ) : (
              // exact document iframe viewer
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {localIframeUrls[selectedPresId] ? (
                  <iframe
                    src={`${localIframeUrls[selectedPresId]}#toolbar=0`}
                    title="SlideVault Document Viewer (Offline Cache)"
                    style={{
                      width: '100%',
                      height: fullViewMode ? '75vh' : undefined,
                      aspectRatio: fullViewMode ? undefined : '16 / 9',
                      border: 'none',
                      borderRadius: 'var(--radius-md)',
                      background: '#fff'
                    }}
                  />
                ) : (isOnline && selectedPres.is_offline_available) ? (
                  <iframe
                    src={`${API_BASE}/presentations/${selectedPresId}/file#toolbar=0`}
                    title="SlideVault Document Viewer"
                    style={{
                      width: '100%',
                      height: fullViewMode ? '75vh' : undefined,
                      aspectRatio: fullViewMode ? undefined : '16 / 9',
                      border: 'none',
                      borderRadius: 'var(--radius-md)',
                      background: '#fff'
                    }}
                  />
                ) : isOnline ? (
                  <div className="slide-canvas" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '260px', flexDirection: 'column', gap: '12px' }}>
                    <div className="spinner"></div>
                    <span>Generating secure PDF copy of PowerPoint file for inline viewing...</span>
                    <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)' }}>This will take a few seconds and prevents downloading the file locally.</span>
                  </div>
                ) : (
                  <div className="slide-canvas" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '260px', flexDirection: 'column', gap: '12px' }}>
                    <WifiOff size={48} style={{ color: 'var(--color-text-tertiary)' }} />
                    <span>No exact presentation file cached offline.</span>
                    <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)' }}>View this presentation online once to download the exact document locally.</span>
                  </div>
                )}
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)' }}>
                  <span>Viewer Source: {isOnline ? 'static file stream' : 'IndexedDB Local Blob URL'}</span>
                  <span>Browser Canvas</span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Right Panel Tabs detailing AI insights */}
        <div
          style={{
            background: 'var(--color-bg-secondary)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-lg)',
            padding: '24px',
            display: (showFileViewer && fullViewMode) ? 'none' : 'flex',
            flexDirection: 'column',
            gap: '20px'
          }}
        >
          {/* Tab Navigation header */}
          <div
            style={{
              display: 'flex',
              borderBottom: '1px solid var(--color-border)',
              gap: '16px',
              overflowX: 'auto',
              paddingBottom: '2px'
            }}
          >
            <button
              onClick={() => setActiveDetailTab('summary')}
              style={{
                paddingBottom: '12px',
                borderBottom: `2px solid ${activeDetailTab === 'summary' ? 'var(--color-brand-start)' : 'transparent'}`,
                color: activeDetailTab === 'summary' ? 'var(--color-text-primary)' : 'var(--color-text-tertiary)',
                fontWeight: activeDetailTab === 'summary' ? '600' : '500'
              }}
            >
              AI Summary
            </button>
            <button
              onClick={() => setActiveDetailTab('ai')}
              style={{
                paddingBottom: '12px',
                borderBottom: `2px solid ${activeDetailTab === 'ai' ? 'var(--color-brand-start)' : 'transparent'}`,
                color: activeDetailTab === 'ai' ? 'var(--color-text-primary)' : 'var(--color-text-tertiary)',
                fontWeight: activeDetailTab === 'ai' ? '600' : '500'
              }}
            >
              AI Metadata
            </button>
            <button
              onClick={() => setActiveDetailTab('recs')}
              style={{
                paddingBottom: '12px',
                borderBottom: `2px solid ${activeDetailTab === 'recs' ? 'var(--color-brand-start)' : 'transparent'}`,
                color: activeDetailTab === 'recs' ? 'var(--color-text-primary)' : 'var(--color-text-tertiary)',
                fontWeight: activeDetailTab === 'recs' ? '600' : '500'
              }}
            >
              Recommendations
            </button>
            <button
              onClick={() => setActiveDetailTab('quality')}
              style={{
                paddingBottom: '12px',
                borderBottom: `2px solid ${activeDetailTab === 'quality' ? 'var(--color-brand-start)' : 'transparent'}`,
                color: activeDetailTab === 'quality' ? 'var(--color-text-primary)' : 'var(--color-text-tertiary)',
                fontWeight: activeDetailTab === 'quality' ? '600' : '500'
              }}
            >
              Quality & Usage
            </button>
            <button
              onClick={() => setActiveDetailTab('bookmarks')}
              style={{
                paddingBottom: '12px',
                borderBottom: `2px solid ${activeDetailTab === 'bookmarks' ? 'var(--color-brand-start)' : 'transparent'}`,
                color: activeDetailTab === 'bookmarks' ? 'var(--color-text-primary)' : 'var(--color-text-tertiary)',
                fontWeight: activeDetailTab === 'bookmarks' ? '600' : '500'
              }}
            >
              Bookmarks ({selectedPresBookmarks.length})
            </button>
          </div>

          {/* Summary Tab Content */}
          {activeDetailTab === 'summary' && (
            <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {!selectedPresSummary ? (
                <div className="empty-state">
                  <div className="spinner"></div>
                  <span style={{ marginTop: '12px' }}>Analyzing slides and extracting summaries...</span>
                </div>
              ) : (
                <>
                  <div>
                    <h4 style={{ fontSize: 'var(--text-sm)', color: 'var(--color-brand-start)', marginBottom: '4px' }}>Short Summary</h4>
                    <p style={{ fontSize: 'var(--text-sm)', lineHeight: '1.6' }}>{selectedPresSummary.short_summary}</p>
                  </div>
                  {selectedPresSummary.key_topics && selectedPresSummary.key_topics.length > 0 && (
                    <div>
                      <h4 style={{ fontSize: 'var(--text-sm)', color: 'var(--color-brand-start)', marginBottom: '4px' }}>Key Topics</h4>
                      <ul style={{ listStyleType: 'disc', paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {selectedPresSummary.key_topics.map((obj, i) => (
                          <li key={i} style={{ fontSize: 'var(--text-sm)' }}>{obj}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {selectedPresSummary.learning_objectives && selectedPresSummary.learning_objectives.length > 0 && (
                    <div>
                      <h4 style={{ fontSize: 'var(--text-sm)', color: 'var(--color-brand-start)', marginBottom: '4px' }}>Learning Objectives</h4>
                      <ul style={{ listStyleType: 'disc', paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {selectedPresSummary.learning_objectives.map((obj, i) => (
                          <li key={i} style={{ fontSize: 'var(--text-sm)' }}>{obj}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* AI Metadata Details Tab */}
          {activeDetailTab === 'ai' && (
            <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <span style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', textTransform: 'uppercase' }}>Author / Presenter</span>
                  <div style={{ fontWeight: '600', fontSize: 'var(--text-sm)', marginTop: '4px' }}>
                    {selectedPres?.author || 'Unknown'}
                  </div>
                </div>
                <div>
                  <span style={{ fontSize: '10px', color: 'var(--color-text-tertiary)', textTransform: 'uppercase' }}>Version / Iteration</span>
                  <div style={{ fontWeight: '600', fontSize: 'var(--text-sm)', marginTop: '4px' }}>
                    v{selectedPres?.version || '1.0.0'}
                  </div>
                </div>
              </div>

              {/* Display Keywords */}
              <div>
                <h4 style={{ fontSize: 'var(--text-sm)', marginBottom: '8px', color: 'var(--color-text-secondary)' }}>Extracted Focus Areas</h4>
                {selectedPresKeywords.length === 0 ? (
                  <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)' }}>No keywords extracted.</span>
                ) : (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {selectedPresKeywords.map((kw, i) => (
                      <span
                        key={i}
                        className="badge badge-secondary"
                        style={{
                          fontSize: '11px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          border: '1px solid var(--color-border)'
                        }}
                        title={`Relevance score: ${Math.round(kw.relevance * 100)}%`}
                      >
                        <Tag size={10} />
                        {kw.keyword}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Display Tags */}
              <div>
                <h4 style={{ fontSize: 'var(--text-sm)', marginBottom: '8px', color: 'var(--color-text-secondary)' }}>Faceted Tag Cloud</h4>
                {selectedPres?.tags.length === 0 ? (
                  <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)' }}>No tags mapped.</span>
                ) : (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {selectedPres?.tags.map((t, i) => (
                      <span
                        key={i}
                        onClick={() => {
                          setSelectedPresId(null);
                          handleToggleViewer(false);
                          setNewBookmarkNote('');
                          // Set search query and go to portal
                          const urlParams = new URLSearchParams(window.location.search);
                          urlParams.set('q', t.name);
                          window.history.pushState({}, '', '?' + urlParams.toString());
                          
                          // Parent triggers
                          setActiveCategory('');
                          setActiveTab('portal');
                          setCurrentPage(1);
                        }}
                        className="badge badge-primary"
                        style={{ fontSize: '11px', cursor: 'pointer' }}
                        title={`Search for tag #${t.name}`}
                      >
                        #{t.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Recommendations Tab */}
          {activeDetailTab === 'recs' && (
            <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <h4 style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)' }}>Similar Knowledge Tracks</h4>
              {!selectedPresRecs ? (
                <div className="spinner"></div>
              ) : selectedPresRecs.similar.length === 0 ? (
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)' }}>No similar presentations found.</span>
              ) : (
                <div className="presentation-list">
                  {selectedPresRecs.similar.map((s, i) => (
                    <div
                      key={i}
                      className="presentation-list-item"
                      style={{ padding: '8px 12px' }}
                      onClick={() => handleOpenDetail(s.id)}
                    >
                      <div className="list-item-content">
                        <div className="list-item-title">{s.title}</div>
                        <div className="list-item-meta" style={{ marginTop: '2px' }}>
                          <span>Match: {Math.round(s.similarity_score * 100)}%</span>
                          <span>•</span>
                          <span>{s.file_type.toUpperCase()}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Quality metrics tab */}
          {activeDetailTab === 'quality' && (
            <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div style={{ background: 'var(--color-bg-tertiary)', padding: '16px', borderRadius: 'var(--radius-md)' }}>
                  <span style={{ fontSize: '11px', color: 'var(--color-text-tertiary)' }}>Total Visual Views</span>
                  <div style={{ fontSize: 'var(--text-2xl)', fontWeight: '700', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Eye size={20} style={{ color: 'var(--color-brand-start)' }} />
                    {selectedPres?.view_count}
                  </div>
                </div>
                <div style={{ background: 'var(--color-bg-tertiary)', padding: '16px', borderRadius: 'var(--radius-md)' }}>
                  <span style={{ fontSize: '11px', color: 'var(--color-text-tertiary)' }}>Total Downloads</span>
                  <div style={{ fontSize: 'var(--text-2xl)', fontWeight: '700', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Download size={20} style={{ color: 'var(--color-accent-emerald)' }} />
                    {selectedPres?.download_count}
                  </div>
                </div>
              </div>

              {/* Display quality indicators */}
              {selectedPresQuality && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '8px' }}>
                  <h4 style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)' }}>AI Asset Quality Scores</h4>
                  
                  <div>
                    <div style={{ display: 'flex', justifyItems: 'center', justifyContent: 'space-between', fontSize: 'var(--text-xs)', marginBottom: '4px' }}>
                      <span>Completeness (Structural details)</span>
                      <span>{Math.round(selectedPresQuality.completeness_score * 100)}/100</span>
                    </div>
                    <div className="progress-bar">
                      <div className="progress-bar-fill" style={{ width: `${selectedPresQuality.completeness_score * 100}%` }}></div>
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyItems: 'center', justifyContent: 'space-between', fontSize: 'var(--text-xs)', marginBottom: '4px' }}>
                      <span>Freshness (Temporal accuracy)</span>
                      <span>{Math.round(selectedPresQuality.freshness_score * 100)}/100</span>
                    </div>
                    <div className="progress-bar">
                      <div className="progress-bar-fill" style={{ width: `${selectedPresQuality.freshness_score * 100}%` }}></div>
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyItems: 'center', justifyContent: 'space-between', fontSize: 'var(--text-xs)', marginBottom: '4px' }}>
                      <span>Knowledge Index (Rich data density)</span>
                      <span>{Math.round(selectedPresQuality.knowledge_score * 100)}/100</span>
                    </div>
                    <div className="progress-bar">
                      <div className="progress-bar-fill" style={{ width: `${selectedPresQuality.knowledge_score * 100}%` }}></div>
                    </div>
                  </div>

                  <div
                    style={{
                      marginTop: '8px',
                      padding: '12px',
                      background: 'rgba(99, 102, 241, 0.06)',
                      borderRadius: 'var(--radius-md)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <span style={{ fontSize: 'var(--text-sm)', fontWeight: '600' }}>Overall Asset Score</span>
                    <span className="badge badge-primary" style={{ fontSize: 'var(--text-sm)', fontWeight: '700' }}>
                      {Math.round(selectedPresQuality.overall_score * 100)}%
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Slide Bookmarks Manager tab */}
          {activeDetailTab === 'bookmarks' && (
            <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input
                  type="number"
                  placeholder="Slide"
                  style={{
                    width: '70px',
                    background: 'var(--color-bg-tertiary)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: '8px',
                    textAlign: 'center'
                  }}
                  value={newBookmarkSlide}
                  onChange={(e) => setNewBookmarkSlide(parseInt(e.target.value) || 1)}
                />
                <input
                  type="text"
                  placeholder="Add custom study note for this slide..."
                  style={{
                    flex: 1,
                    background: 'var(--color-bg-tertiary)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: '8px'
                  }}
                  value={newBookmarkNote}
                  onChange={(e) => setNewBookmarkNote(e.target.value)}
                />
                <button className="btn btn-primary btn-sm" onClick={handleAddBookmark}>
                  <Bookmark size={14} /> Add
                </button>
              </div>

              {/* Display Bookmarks List */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '250px', overflowY: 'auto' }}>
                {selectedPresBookmarks.length === 0 ? (
                  <div className="empty-state" style={{ padding: '24px' }}>
                    <Bookmark size={24} style={{ opacity: 0.3, marginBottom: '8px' }} />
                    <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-tertiary)' }}>No slides bookmarked yet.</span>
                  </div>
                ) : (
                  selectedPresBookmarks.map((b) => (
                    <div
                      key={b.id}
                      style={{
                        display: 'flex',
                        justifyItems: 'center',
                        justifyContent: 'space-between',
                        background: 'var(--color-bg-tertiary)',
                        padding: '10px 12px',
                        borderRadius: 'var(--radius-md)',
                        fontSize: 'var(--text-xs)'
                      }}
                    >
                      <div>
                        <span className="badge badge-secondary" style={{ marginRight: '8px' }}>
                          Slide {b.slide_number}
                        </span>
                        <span style={{ color: 'var(--color-text-primary)' }}>{b.note}</span>
                      </div>
                      <button
                        style={{ color: 'var(--color-error)', opacity: 0.8 }}
                        onClick={() => handleDeleteBookmark(b.id)}
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
