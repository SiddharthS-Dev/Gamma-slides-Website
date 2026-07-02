import { useState, useEffect } from 'react';
import { ArrowLeft, CheckCircle, AlertCircle } from 'lucide-react';
import './index.css';
import './animations.css';
import './components.css';

import { OfflineCache } from './offlineCache';
import * as client from './api/client';
import type {
  Category,
  Department,
  Presentation,
  PresentationDetail,
  AISummary,
  AIKeyword,
  RecommendationSet,
  QualityScores,
  Bookmark,
  SearchSuggestion,
  AnalyticsSummary,
  StorageStats,
  IngestionStatus,
  SlideContentResponse
} from './types';

// Import subcomponents
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import DashboardTab from './components/DashboardTab';
import PortalTab from './components/PortalTab';
import OfflineTab from './components/OfflineTab';
import ReviewQueueTab from './components/ReviewQueueTab';
import SystemTab from './components/SystemTab';
import DetailModal from './components/DetailModal';

export default function App() {
  // Navigation & Shell State
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'portal' | 'offline' | 'queue' | 'system'>('dashboard');
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  // Cached state IDs
  const [downloadedIds, setDownloadedIds] = useState<string[]>([]);
  const [localIframeUrls, setLocalIframeUrls] = useState<Record<string, string>>({});

  // Global Metadata
  const [categories, setCategories] = useState<Category[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);

  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeCategory, setActiveCategory] = useState<string>('');
  const [activeDepartment, setActiveDepartment] = useState<string>('');
  const [activeFileType, setActiveFileType] = useState<string>('');
  const [sortBy, setSortBy] = useState('updated_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Presentation Lists (Portal & Offline)
  const [presentations, setPresentations] = useState<Presentation[]>([]);
  const [totalPresentations, setTotalPresentations] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoadingPortal, setIsLoadingPortal] = useState(false);

  const [offlinePresentations, setOfflinePresentations] = useState<Presentation[]>([]);
  const [isLoadingOfflineTab, setIsLoadingOfflineTab] = useState(false);

  // Selected Presentation Modal Detail State
  const [selectedPresId, setSelectedPresId] = useState<string | null>(null);
  const [selectedPres, setSelectedPres] = useState<PresentationDetail | null>(null);
  const [selectedPresSummary, setSelectedPresSummary] = useState<AISummary | null>(null);
  const [selectedPresKeywords, setSelectedPresKeywords] = useState<AIKeyword[]>([]);
  const [selectedPresRecs, setSelectedPresRecs] = useState<RecommendationSet | null>(null);
  const [selectedPresQuality, setSelectedPresQuality] = useState<QualityScores | null>(null);
  const [selectedPresBookmarks, setSelectedPresBookmarks] = useState<Bookmark[]>([]);
  const [activeDetailTab, setActiveDetailTab] = useState<'summary' | 'ai' | 'recs' | 'quality' | 'bookmarks'>('summary');
  const [showFileViewer, setShowFileViewer] = useState(false);
  const [currentViewerSlide, setCurrentViewerSlide] = useState(1);
  const [newBookmarkSlide, setNewBookmarkSlide] = useState<number>(1);
  const [newBookmarkNote, setNewBookmarkNote] = useState('');

  // Viewer modes
  const [viewerMode, setViewerMode] = useState<'slides' | 'document'>('document');
  const [fullViewMode, setFullViewMode] = useState(false);
  const [slidesResponse, setSlidesResponse] = useState<SlideContentResponse | null>(null);
  const [isLoadingSlides, setIsLoadingSlides] = useState(false);

  // Dashboard & System Admin metrics state
  const [analyticsSummary, setAnalyticsSummary] = useState<AnalyticsSummary | null>(null);
  const [isLoadingDashboard, setIsLoadingDashboard] = useState(true);
  const [storageStats, setStorageStats] = useState<StorageStats | null>(null);
  const [ingestionStatus, setIngestionStatus] = useState<IngestionStatus | null>(null);
  const [systemActionLoading, setSystemActionLoading] = useState<string | null>(null);
  const [systemMessage, setSystemMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Review Queue State
  const [reviewQueue, setReviewQueue] = useState<any[]>([]);
  const [isLoadingQueue, setIsLoadingQueue] = useState(false);
  const [selectedReviewItem, setSelectedReviewItem] = useState<any | null>(null);
  const [reviewCategory, setReviewCategory] = useState('');
  const [reviewTags, setReviewTags] = useState<string[]>([]);
  const [reviewNotes, setReviewNotes] = useState('');

  // Refresh list of cached IDs on cache changes
  const refreshCacheStatus = async () => {
    try {
      const fileIds = await OfflineCache.getDownloadedIds();
      setDownloadedIds(fileIds);
    } catch (err) {
      console.error('Failed to get downloaded offline cache IDs:', err);
    }
  };

  useEffect(() => {
    refreshCacheStatus();
  }, [selectedPresId, showFileViewer]);

  // Load offline catalog
  useEffect(() => {
    if (activeTab === 'offline') {
      loadOfflinePresentations();
    }
  }, [activeTab]);

  const loadOfflinePresentations = async () => {
    setIsLoadingOfflineTab(true);
    try {
      const fileIds = await OfflineCache.getDownloadedIds();
      const list = await OfflineCache.getPresentations();
      if (list) {
        const filtered = list.filter(p => fileIds.includes(p.id));
        setOfflinePresentations(filtered);
      }
    } catch (err) {
      console.error('Failed to load offline presentations list:', err);
    } finally {
      setIsLoadingOfflineTab(false);
    }
  };

  // Connection checking & handlers
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    const checkConn = async () => {
      const ok = await client.checkHealth();
      setIsOnline(ok);
    };
    checkConn();

    const interval = setInterval(checkConn, 10000);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(interval);
    };
  }, []);

  // Poll cache status if viewing pptx converted file on cache miss
  useEffect(() => {
    if (!selectedPresId || !showFileViewer || viewerMode !== 'document') return;
    if (!selectedPres || selectedPres.is_offline_available) return;
    if (!isOnline) return;

    let active = true;
    const interval = setInterval(async () => {
      try {
        const detail = await client.fetchPresentationDetail(selectedPresId);
        if (detail.is_offline_available && active) {
          setSelectedPres(detail);
          downloadAndCacheFile(selectedPresId);
          clearInterval(interval);
        }
      } catch (err) {
        console.error("Error polling presentation cache status:", err);
      }
    }, 3000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [selectedPresId, showFileViewer, viewerMode, selectedPres, isOnline]);

  // Fetch initial category & department lists
  useEffect(() => {
    async function loadMeta() {
      try {
        if (isOnline) {
          const [catData, deptData] = await Promise.all([
            client.fetchCategories(),
            client.fetchDepartments()
          ]);
          setCategories(catData);
          setDepartments(deptData);
          await OfflineCache.setMeta('categories', catData);
          await OfflineCache.setMeta('departments', deptData);
        } else {
          const catCached = await OfflineCache.getMeta('categories');
          const deptCached = await OfflineCache.getMeta('departments');
          if (catCached) setCategories(catCached);
          if (deptCached) setDepartments(deptCached);
        }
      } catch (err) {
        console.error('Failed to load metadata', err);
        const catCached = await OfflineCache.getMeta('categories');
        const deptCached = await OfflineCache.getMeta('departments');
        if (catCached) setCategories(catCached);
        if (deptCached) setDepartments(deptCached);
      }
    }
    loadMeta();
  }, [isOnline]);

  // Trigger metrics reload on active tab changes
  useEffect(() => {
    if (activeTab === 'dashboard') {
      fetchDashboardStats();
    } else if (activeTab === 'system') {
      fetchSystemStats();
    } else if (activeTab === 'queue') {
      fetchReviewQueue();
    }
  }, [activeTab, isOnline]);

  // Trigger list query reloads on filter changes
  useEffect(() => {
    if (activeTab === 'portal') {
      fetchPortalPresentations();
    }
  }, [activeTab, searchQuery, activeCategory, activeDepartment, activeFileType, sortBy, sortOrder, currentPage, isOnline]);

  // Fetch dashboard metrics
  const fetchDashboardStats = async () => {
    setIsLoadingDashboard(true);
    try {
      if (isOnline) {
        const data = await client.fetchAnalyticsSummary();
        setAnalyticsSummary(data);
      } else {
        const offlineList = await OfflineCache.getPresentations();
        if (offlineList) {
          setAnalyticsSummary({
            total_presentations: offlineList.length,
            total_categories: new Set(offlineList.map(p => p.category?.id).filter(Boolean)).size,
            total_views: offlineList.reduce((acc, p) => acc + (p.view_count || 0), 0),
            total_downloads: offlineList.reduce((acc, p) => acc + (p.download_count || 0), 0),
            total_departments: new Set(offlineList.map(p => p.department?.id).filter(Boolean)).size,
            active_users_count: 0,
            trending_presentations: [...offlineList].sort((a, b) => b.popularity_score - a.popularity_score).slice(0, 5),
            most_viewed_presentations: [...offlineList].sort((a, b) => b.view_count - a.view_count).slice(0, 5),
            recently_added: [...offlineList].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).slice(0, 5)
          });
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingDashboard(false);
    }
  };

  // Fetch admin storage statistics
  const fetchSystemStats = async () => {
    try {
      if (isOnline) {
        const [storage, ingest] = await Promise.all([
          client.fetchStorageStats(),
          client.fetchIngestionStatus()
        ]);
        setStorageStats(storage);
        setIngestionStatus(ingest);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Fetch classification review queue
  const fetchReviewQueue = async () => {
    setIsLoadingQueue(true);
    try {
      if (isOnline) {
        const queue = await client.fetchClassificationQueue();
        setReviewQueue(queue);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingQueue(false);
    }
  };

  // Fetch portal list presentations
  const fetchPortalPresentations = async () => {
    setIsLoadingPortal(true);
    try {
      if (isOnline) {
        const data = await client.fetchPresentations({
          page: currentPage,
          pageSize: 12,
          sortBy,
          sortOrder,
          categoryId: activeCategory,
          departmentId: activeDepartment,
          fileType: activeFileType,
          q: searchQuery
        });
        setPresentations(data.items);
        setTotalPresentations(data.total);
        setTotalPages(data.total_pages);
        
        await OfflineCache.setPresentations(data.items);
      } else {
        let cached = await OfflineCache.getPresentations();
        if (cached) {
          if (searchQuery.trim().length > 0) {
            const query = searchQuery.toLowerCase();
            cached = cached.filter(p => 
              p.title.toLowerCase().includes(query) || 
              p.description?.toLowerCase().includes(query) ||
              p.file_name.toLowerCase().includes(query) ||
              p.tags.some(t => t.name.toLowerCase().includes(query))
            );
          }
          if (activeCategory) {
            if (activeCategory === 'unclassified') {
              cached = cached.filter(p => !p.category);
            } else {
              cached = cached.filter(p => p.category?.id === activeCategory);
            }
          }
          if (activeDepartment) {
            cached = cached.filter(p => p.department?.id === activeDepartment);
          }
          if (activeFileType) {
            cached = cached.filter(p => p.file_type.toLowerCase() === activeFileType.toLowerCase());
          }

          cached.sort((a, b) => {
            let valA: any = (a as any)[sortBy];
            let valB: any = (b as any)[sortBy];

            if (sortBy === 'title') {
              valA = a.title.toLowerCase();
              valB = b.title.toLowerCase();
            } else if (sortBy === 'updated_at') {
              valA = new Date(a.updated_at).getTime();
              valB = new Date(b.updated_at).getTime();
            }

            if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
            if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
            return 0;
          });

          const itemsPerPage = 12;
          const totalItems = cached.length;
          const pagesTotal = Math.ceil(totalItems / itemsPerPage);
          const startIndex = (currentPage - 1) * itemsPerPage;
          const paginated = cached.slice(startIndex, startIndex + itemsPerPage);

          setPresentations(paginated);
          setTotalPresentations(totalItems);
          setTotalPages(pagesTotal || 1);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingPortal(false);
    }
  };

  // Autocomplete suggestion fetch logic
  useEffect(() => {
    if (!searchQuery || searchQuery.trim().length < 2 || !isOnline) {
      setSuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const listData = await client.fetchSearchSuggestions(searchQuery);
        setSuggestions(listData);
      } catch (err) {
        console.error(err);
      }
    }, 200);
    return () => clearTimeout(timer);
  }, [searchQuery, isOnline]);

  // Keyboard navigation event triggers
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (!showFileViewer || !selectedPres || !slidesResponse || viewerMode !== 'slides') return;
      if (event.key === 'ArrowRight' || event.key === 'Right') {
        if (currentViewerSlide < (slidesResponse.total_slides || selectedPres.slide_count || 12)) {
          setCurrentViewerSlide(prev => prev + 1);
          setNewBookmarkSlide(prev => prev + 1);
        }
      } else if (event.key === 'ArrowLeft' || event.key === 'Left') {
        if (currentViewerSlide > 1) {
          setCurrentViewerSlide(prev => prev - 1);
          setNewBookmarkSlide(prev => prev - 1);
        }
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showFileViewer, selectedPres, slidesResponse, currentViewerSlide, viewerMode]);

  // Binary caching downloader logic
  const downloadAndCacheFile = async (id: string) => {
    try {
      const isAlreadyCached = downloadedIds.includes(id);
      if (isAlreadyCached) {
        await loadCachedFileUrl(id);
        return;
      }
      const fileRes = await fetch(`${client.API_BASE}/presentations/${id}/file`);
      if (fileRes.ok) {
        const fileBlob = await fileRes.blob();
        await OfflineCache.setFile(id, fileBlob);
        await loadCachedFileUrl(id);
        refreshCacheStatus();
      }
    } catch (err) {
      console.error(`Failed to cache binary file for ${id}`, err);
    }
  };

  // Convert blob to local Object URL
  const loadCachedFileUrl = async (id: string) => {
    try {
      if (localIframeUrls[id]) return;
      const fileBlob = await OfflineCache.getFile(id);
      if (fileBlob) {
        const localUrl = URL.createObjectURL(fileBlob);
        setLocalIframeUrls(prev => ({ ...prev, [id]: localUrl }));
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Handle visual presenter frame viewer open/close
  const handleToggleViewer = (open: boolean) => {
    setShowFileViewer(open);
    if (!open) {
      setFullViewMode(false);
    }
    if (open && selectedPresId) {
      fetchSlideContent(selectedPresId);
      if (!isOnline) {
        loadCachedFileUrl(selectedPresId);
      }
    }
  };

  const fetchSlideContent = async (id: string) => {
    setIsLoadingSlides(true);
    setSlidesResponse(null);
    try {
      if (isOnline) {
        const data = await client.fetchSlideContent(id);
        setSlidesResponse(data);
        await OfflineCache.setSlides(id, data);
      } else {
        const cached = await OfflineCache.getSlides(id);
        if (cached) setSlidesResponse(cached);
      }
    } catch (err) {
      console.error(err);
      const cached = await OfflineCache.getSlides(id);
      if (cached) setSlidesResponse(cached);
    } finally {
      setIsLoadingSlides(false);
    }
  };

  // Selected Presentation details viewer loader
  const handleOpenDetail = async (id: string) => {
    setSelectedPresId(id);
    setSelectedPres(null);
    setSelectedPresSummary(null);
    setSelectedPresKeywords([]);
    setSelectedPresRecs(null);
    setSelectedPresQuality(null);
    setSelectedPresBookmarks([]);
    setActiveDetailTab('summary');
    setShowFileViewer(false);
    setFullViewMode(false);
    setCurrentViewerSlide(1);
    setNewBookmarkSlide(1);
    setNewBookmarkNote('');

    try {
      if (isOnline) {
        const detail = await client.fetchPresentationDetail(id);
        setSelectedPres(detail);
        await OfflineCache.setDetail(id, detail);

        downloadAndCacheFile(id);

        client.recordView(id);

        const [sum, keywords, recs, quality, bookmarks] = await Promise.all([
          client.fetchAISummary(id),
          client.fetchAIKeywords(id),
          client.fetchRecommendations(id),
          client.fetchQualityScores(id),
          client.fetchBookmarks(id)
        ]);

        setSelectedPresSummary(sum);
        setSelectedPresKeywords(keywords);
        setSelectedPresRecs(recs);
        setSelectedPresQuality(quality);
        setSelectedPresBookmarks(bookmarks);

        await OfflineCache.setSummary(id, sum);
        await OfflineCache.setKeywords(id, keywords);
        await OfflineCache.setRecommendations(id, recs);
        await OfflineCache.setQuality(id, quality);
        await OfflineCache.setBookmarks(id, bookmarks);
      } else {
        const detail = await OfflineCache.getDetail(id);
        if (detail) setSelectedPres(detail);

        const summary = await OfflineCache.getSummary(id);
        if (summary) setSelectedPresSummary(summary);

        const keywords = await OfflineCache.getKeywords(id);
        if (keywords) setSelectedPresKeywords(keywords.keywords || []);

        const recs = await OfflineCache.getRecommendations(id);
        if (recs) setSelectedPresRecs(recs);

        const quality = await OfflineCache.getQuality(id);
        if (quality) setSelectedPresQuality(quality);

        const bookmarks = await OfflineCache.getBookmarks(id);
        if (bookmarks) setSelectedPresBookmarks(bookmarks.bookmarks || []);

        loadCachedFileUrl(id);
      }
    } catch (err) {
      console.error(err);
      // Fallback offline loader
      const detail = await OfflineCache.getDetail(id);
      if (detail) setSelectedPres(detail);
      const summary = await OfflineCache.getSummary(id);
      if (summary) setSelectedPresSummary(summary);
      const keywords = await OfflineCache.getKeywords(id);
      if (keywords) setSelectedPresKeywords(keywords.keywords || []);
      const recs = await OfflineCache.getRecommendations(id);
      if (recs) setSelectedPresRecs(recs);
      const quality = await OfflineCache.getQuality(id);
      if (quality) setSelectedPresQuality(quality);
      const bookmarks = await OfflineCache.getBookmarks(id);
      if (bookmarks) setSelectedPresBookmarks(bookmarks.bookmarks || []);
      loadCachedFileUrl(id);
    }
  };

  // Add bookmark study note
  const handleAddBookmark = async () => {
    if (!selectedPresId) return;
    try {
      if (isOnline) {
        const added = await client.createBookmark(selectedPresId, newBookmarkSlide, newBookmarkNote || 'Bookmarked slide');
        const updated = [added, ...selectedPresBookmarks];
        setSelectedPresBookmarks(updated);
        await OfflineCache.setBookmarks(selectedPresId, updated);
        setNewBookmarkNote('');
      } else {
        const added: Bookmark = {
          id: `offline-bookmark-${Date.now()}`,
          presentation_id: selectedPresId,
          slide_number: newBookmarkSlide,
          note: newBookmarkNote || 'Bookmarked slide',
          created_at: new Date().toISOString()
        };
        const updated = [added, ...selectedPresBookmarks];
        setSelectedPresBookmarks(updated);
        await OfflineCache.setBookmarks(selectedPresId, updated);
        setNewBookmarkNote('');
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Delete bookmark study note
  const handleDeleteBookmark = async (bookmarkId: string) => {
    try {
      if (isOnline) {
        await client.deleteBookmark(bookmarkId);
      }
      const updated = selectedPresBookmarks.filter(b => b.id !== bookmarkId);
      setSelectedPresBookmarks(updated);
      if (selectedPresId) await OfflineCache.setBookmarks(selectedPresId, updated);
    } catch (err) {
      console.error(err);
    }
  };

  // Review tags queue selection
  const handleSelectReviewItem = async (item: any) => {
    setSelectedReviewItem(item);
    setReviewNotes('');
    setReviewCategory(item.ai_category ? categories.find(c => c.name === item.ai_category)?.id || '' : '');
    setReviewTags(item.tags || []);
  };

  // Admin submit classification override review
  const handleReviewAction = async (action: 'accept' | 'modify') => {
    if (!selectedReviewItem) return;
    try {
      const finalCategory = action === 'accept' 
        ? categories.find(c => c.name === selectedReviewItem.ai_category)?.id || ''
        : reviewCategory;

      const apiAction = action === 'accept' ? 'accepted' : 'modified';
      await client.submitReview(
        selectedReviewItem.id,
        apiAction,
        finalCategory || null,
        null,
        reviewNotes
      );
      setReviewQueue(reviewQueue.filter(q => q.id !== selectedReviewItem.id));
      setSelectedReviewItem(null);
      setSystemMessage({ text: `Review submitted: Classification ${action}ed successfully.`, type: 'success' });
    } catch (err: any) {
      console.error(err);
      setSystemMessage({ text: `Review failed: ${err.message || 'API call error'}`, type: 'error' });
    }
  };

  // System admin manual sync / thumbnail action triggers
  const runAdminAction = async (action: 'reindex' | 'scan' | 'regenerate-thumbnails', label: string) => {
    setSystemActionLoading(label);
    setSystemMessage(null);
    try {
      const data = await client.triggerAdminAction(action);
      setSystemMessage({
        text: `Success: ${label} completed. ${data.result?.processed !== undefined ? `Processed: ${data.result.processed}` : ''}`,
        type: 'success'
      });
      fetchSystemStats();
    } catch (err: any) {
      console.error(err);
      setSystemMessage({ text: `Error running ${label}: ${err.message || 'API error'}`, type: 'error' });
    } finally {
      setSystemActionLoading(null);
    }
  };

  // Search input selection
  const handleSuggestionClick = (sug: SearchSuggestion) => {
    setSelectedPresId(null);
    setShowFileViewer(false);
    setSearchQuery(sug.text);
    setShowSuggestions(false);
    setActiveTab('portal');
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setActiveCategory('');
    setActiveDepartment('');
    setActiveFileType('');
    setCurrentPage(1);
  };

  return (
    <div className="app-shell">
      {/* Sidebar Navigation */}
      <Sidebar
        sidebarCollapsed={sidebarCollapsed}
        setSidebarCollapsed={setSidebarCollapsed}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        categories={categories}
        activeCategory={activeCategory}
        setActiveCategory={setActiveCategory}
        downloadedCount={downloadedIds.length}
        setSelectedPresId={setSelectedPresId}
        setShowFileViewer={setShowFileViewer}
        setCurrentPage={setCurrentPage}
      />

      <div className={`app-content ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
        {/* Header toolbar */}
        <Header
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          suggestions={suggestions}
          showSuggestions={showSuggestions}
          setShowSuggestions={setShowSuggestions}
          isOnline={isOnline}
          sidebarCollapsed={sidebarCollapsed}
          setSidebarCollapsed={setSidebarCollapsed}
          onSuggestionClick={handleSuggestionClick}
          onSearchSubmit={(query) => {
            setSelectedPresId(null);
            setShowFileViewer(false);
            setSearchQuery(query);
            setActiveTab('portal');
            setCurrentPage(1);
          }}
        />

        {/* Global Toast Alert banner */}
        {systemMessage && (
          <div
            className={`alert ${systemMessage.type === 'success' ? 'alert-success' : 'alert-error'} animate-scale-in`}
            style={{ margin: '16px 32px 0 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {systemMessage.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
              <span>{systemMessage.text}</span>
            </div>
            <button className="btn btn-ghost btn-xs" onClick={() => setSystemMessage(null)}>Dismiss</button>
          </div>
        )}

        {/* Root page router viewport */}
        <main className="main-content">
          {/* Back Navigation Bar (Shown when selectedPresId is set) */}
          {selectedPresId && (
            <div className="animate-fade-in" style={{ marginBottom: '16px' }}>
              <button
                onClick={() => {
                  setSelectedPresId(null);
                  setShowFileViewer(false);
                  setNewBookmarkNote('');
                }}
                className="btn btn-secondary btn-sm"
                style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
              >
                <ArrowLeft size={16} /> Back to Listings
              </button>
            </div>
          )}

          {/* Render Detail Modal overlay */}
          {selectedPresId && (
            <DetailModal
              selectedPresId={selectedPresId}
              setSelectedPresId={setSelectedPresId}
              selectedPres={selectedPres}
              downloadedIds={downloadedIds}
              isOnline={isOnline}
              showFileViewer={showFileViewer}
              handleToggleViewer={handleToggleViewer}
              API_BASE={client.API_BASE}
              viewerMode={viewerMode}
              setViewerMode={setViewerMode}
              fullViewMode={fullViewMode}
              setFullViewMode={setFullViewMode}
              isLoadingSlides={isLoadingSlides}
              slidesResponse={slidesResponse}
              currentViewerSlide={currentViewerSlide}
              setCurrentViewerSlide={setCurrentViewerSlide}
              setNewBookmarkSlide={setNewBookmarkSlide}
              localIframeUrls={localIframeUrls}
              activeDetailTab={activeDetailTab}
              setActiveDetailTab={setActiveDetailTab}
              selectedPresSummary={selectedPresSummary}
              selectedPresKeywords={selectedPresKeywords}
              selectedPresRecs={selectedPresRecs}
              selectedPresQuality={selectedPresQuality}
              selectedPresBookmarks={selectedPresBookmarks}
              newBookmarkSlide={newBookmarkSlide}
              newBookmarkNote={newBookmarkNote}
              setNewBookmarkNote={setNewBookmarkNote}
              handleAddBookmark={handleAddBookmark}
              handleDeleteBookmark={handleDeleteBookmark}
              handleOpenDetail={handleOpenDetail}
              setActiveCategory={setActiveCategory}
              setActiveDepartment={setActiveDepartment}
              setActiveTab={setActiveTab}
              setCurrentPage={setCurrentPage}
            />
          )}

          {/* Render Tab views conditionally */}
          {activeTab === 'dashboard' && !selectedPresId && (
            <DashboardTab
              isLoadingDashboard={isLoadingDashboard}
              analyticsSummary={analyticsSummary}
              handleOpenDetail={handleOpenDetail}
              setActiveTab={setActiveTab}
            />
          )}

          {activeTab === 'portal' && !selectedPresId && (
            <PortalTab
              categories={categories}
              departments={departments}
              presentations={presentations}
              isLoadingPortal={isLoadingPortal}
              activeCategory={activeCategory}
              setActiveCategory={setActiveCategory}
              activeDepartment={activeDepartment}
              setActiveDepartment={setActiveDepartment}
              activeFileType={activeFileType}
              setActiveFileType={setActiveFileType}
              sortBy={sortBy}
              setSortBy={setSortBy}
              sortOrder={sortOrder}
              setSortOrder={setSortOrder}
              viewMode={viewMode}
              setViewMode={setViewMode}
              currentPage={currentPage}
              setCurrentPage={setCurrentPage}
              totalPages={totalPages}
              totalPresentations={totalPresentations}
              handleOpenDetail={handleOpenDetail}
              downloadedIds={downloadedIds}
              isOnline={isOnline}
              searchQuery={searchQuery}
              handleClearFilters={handleClearFilters}
            />
          )}

          {activeTab === 'offline' && !selectedPresId && (
            <OfflineTab
              offlinePresentations={offlinePresentations}
              isLoadingOfflineTab={isLoadingOfflineTab}
              handleOpenDetail={handleOpenDetail}
            />
          )}

          {activeTab === 'queue' && !selectedPresId && (
            <ReviewQueueTab
              reviewQueue={reviewQueue}
              isLoadingQueue={isLoadingQueue}
              selectedReviewItem={selectedReviewItem}
              handleSelectReviewItem={handleSelectReviewItem}
              setSelectedReviewItem={setSelectedReviewItem}
              categories={categories}
              reviewCategory={reviewCategory}
              setReviewCategory={setReviewCategory}
              reviewTags={reviewTags}
              reviewNotes={reviewNotes}
              setReviewNotes={setReviewNotes}
              handleReviewAction={handleReviewAction}
            />
          )}

          {activeTab === 'system' && !selectedPresId && (
            <SystemTab
              storageStats={storageStats}
              ingestionStatus={ingestionStatus}
              systemActionLoading={systemActionLoading}
              runAdminAction={runAdminAction}
            />
          )}
        </main>
      </div>
    </div>
  );
}
