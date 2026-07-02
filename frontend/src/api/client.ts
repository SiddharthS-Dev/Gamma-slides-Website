// Centralized API client layer for SlideVault

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
} from '../types';

export const API_BASE = (import.meta.env.VITE_API_BASE || 'http://localhost:8000') + '/api/v1';

/**
 * Perform healthcheck call.
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE.replace('/api/v1', '')}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(3000)
    });
    return res.ok;
  } catch (err) {
    return false;
  }
}

/**
 * Fetch categories from the backend.
 */
export async function fetchCategories(): Promise<Category[]> {
  const res = await fetch(`${API_BASE}/categories`);
  if (!res.ok) throw new Error('Failed to fetch categories');
  return res.json();
}

/**
 * Fetch departments from the backend.
 */
export async function fetchDepartments(): Promise<Department[]> {
  const res = await fetch(`${API_BASE}/departments`);
  if (!res.ok) throw new Error('Failed to fetch departments');
  return res.json();
}

/**
 * Fetch autocomplete suggestions for search.
 */
export async function fetchSearchSuggestions(query: string): Promise<SearchSuggestion[]> {
  if (!query.trim()) return [];
  const res = await fetch(`${API_BASE}/search/suggestions?q=${encodeURIComponent(query)}&limit=6`);
  if (!res.ok) throw new Error('Failed to fetch search suggestions');
  return res.json();
}

/**
 * Fetch dashboard analytics summary.
 */
export async function fetchAnalyticsSummary(): Promise<AnalyticsSummary> {
  const res = await fetch(`${API_BASE}/analytics/summary`);
  if (!res.ok) throw new Error('Failed to fetch analytics summary');
  const data = await res.json();
  return {
    total_presentations: data.total_presentations || 0,
    total_views: data.total_views || 0,
    total_downloads: data.total_downloads || 0,
    total_categories: data.total_categories || 0,
    total_departments: data.total_departments || 0,
    active_users_count: data.active_users_count || 0,
    trending_presentations: (data.trending || []).map((p: any) => ({
      ...p,
      popularity_score: p.trend_score || 0
    })),
    most_viewed_presentations: (data.most_viewed || []).map((p: any) => ({
      ...p,
      popularity_score: p.trend_score || 0
    })),
    recently_added: (data.recently_added || []).map((p: any) => ({
      ...p,
      popularity_score: p.trend_score || 0
    }))
  };
}

/**
 * Fetch storage statistics.
 */
export async function fetchStorageStats(): Promise<StorageStats> {
  const res = await fetch(`${API_BASE}/admin/storage-stats`);
  if (!res.ok) throw new Error('Failed to fetch storage stats');
  return res.json();
}

/**
 * Fetch ingestion sync engine status.
 */
export async function fetchIngestionStatus(): Promise<IngestionStatus> {
  const res = await fetch(`${API_BASE}/admin/ingestion-status`);
  if (!res.ok) throw new Error('Failed to fetch ingestion status');
  return res.json();
}

/**
 * Fetch pending classifications for review queue.
 */
export async function fetchClassificationQueue(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/admin/classification-queue?status=pending_review&limit=50`);
  if (!res.ok) throw new Error('Failed to fetch classification queue');
  return res.json();
}

/**
 * Query presentations list with filters.
 */
export interface FetchPresentationsParams {
  page: number;
  pageSize: number;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
  categoryId?: string;
  departmentId?: string;
  fileType?: string;
  q?: string;
}

export async function fetchPresentations(params: FetchPresentationsParams): Promise<{
  items: Presentation[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}> {
  let endpoint = `${API_BASE}/presentations?page=${params.page}&page_size=${params.pageSize}&sort_by=${params.sortBy}&sort_order=${params.sortOrder}`;
  
  if (params.categoryId) {
    if (params.categoryId === 'unclassified') {
      endpoint += '&unclassified=true';
    } else {
      endpoint += `&category_id=${params.categoryId}`;
    }
  }
  if (params.departmentId) {
    endpoint += `&department_id=${params.departmentId}`;
  }
  if (params.fileType) {
    endpoint += `&file_type=${params.fileType}`;
  }
  
  // If search query is present, use search router instead of direct listing
  if (params.q && params.q.trim()) {
    endpoint = `${API_BASE}/search?q=${encodeURIComponent(params.q)}&page=${params.page}&page_size=${params.pageSize}`;
    if (params.categoryId) {
      if (params.categoryId === 'unclassified') {
        endpoint += '&unclassified=true';
      } else {
        endpoint += `&category_id=${params.categoryId}`;
      }
    }
    if (params.departmentId) {
      endpoint += `&department_id=${params.departmentId}`;
    }
    if (params.fileType) {
      endpoint += `&file_type=${params.fileType}`;
    }
  }

  const res = await fetch(endpoint);
  if (!res.ok) throw new Error('Failed to fetch presentations');
  return res.json();
}

/**
 * Fetch slide texts/contents for slide mode search.
 */
export async function fetchSlideContent(id: string): Promise<SlideContentResponse> {
  const res = await fetch(`${API_BASE}/presentations/${id}/slides`);
  if (!res.ok) throw new Error('Failed to fetch slide contents');
  return res.json();
}

/**
 * Fetch a single presentation detail by ID.
 */
export async function fetchPresentationDetail(id: string): Promise<PresentationDetail> {
  const res = await fetch(`${API_BASE}/presentations/${id}`);
  if (!res.ok) throw new Error('Failed to fetch presentation details');
  return res.json();
}

/**
 * Record a presentation view event.
 */
export async function recordView(id: string, slideNumber?: number, duration?: number): Promise<void> {
  try {
    await fetch(`${API_BASE}/presentations/${id}/view`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: 'session_' + window.location.port,
        slide_number: slideNumber || 1,
        duration_seconds: duration || 0
      })
    });
  } catch (err) {
    console.error('Failed to log view analytic event:', err);
  }
}

/**
 * Fetch presentation sub-insights.
 */
export async function fetchAISummary(id: string): Promise<AISummary> {
  const res = await fetch(`${API_BASE}/presentations/${id}/summary`);
  if (!res.ok) throw new Error('Failed to fetch AI summary');
  return res.json();
}

export async function fetchAIKeywords(id: string): Promise<AIKeyword[]> {
  const res = await fetch(`${API_BASE}/presentations/${id}/keywords`);
  if (!res.ok) throw new Error('Failed to fetch AI keywords');
  const data = await res.json();
  if (data && Array.isArray(data.keywords)) {
    return data.keywords.map((kw: any, index: number) => ({
      id: kw.id || `kw-${index}`,
      presentation_id: id,
      keyword: kw.keyword,
      relevance: kw.relevance_score || 0
    }));
  }
  return [];
}

export async function fetchRecommendations(id: string): Promise<RecommendationSet> {
  const res = await fetch(`${API_BASE}/presentations/${id}/recommendations`);
  if (!res.ok) throw new Error('Failed to fetch recommendations');
  return res.json();
}

export async function fetchQualityScores(id: string): Promise<QualityScores> {
  const res = await fetch(`${API_BASE}/presentations/${id}/quality`);
  if (!res.ok) throw new Error('Failed to fetch quality scores');
  return res.json();
}

export async function fetchBookmarks(id: string): Promise<Bookmark[]> {
  const res = await fetch(`${API_BASE}/presentations/${id}/bookmarks`);
  if (!res.ok) throw new Error('Failed to fetch bookmarks');
  return res.json();
}

/**
 * Bookmarks actions.
 */
export async function createBookmark(id: string, slideNumber: number, note: string): Promise<Bookmark> {
  const res = await fetch(`${API_BASE}/presentations/${id}/bookmarks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      slide_number: slideNumber,
      note: note,
      session_id: 'session_' + window.location.port
    })
  });
  if (!res.ok) throw new Error('Failed to create bookmark');
  return res.json();
}

export async function deleteBookmark(bookmarkId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/presentations/bookmarks/${bookmarkId}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to delete bookmark');
}

/**
 * Review tag submit action.
 */
export async function submitReview(
  id: string,
  action: 'accepted' | 'modified' | 'rejected',
  categoryId: string | null,
  tagIds: string[] | null,
  notes: string
): Promise<any> {
  const res = await fetch(`${API_BASE}/admin/review/${id}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      action: action,
      reviewer: 'admin',
      final_category_id: categoryId || null,
      final_tag_ids: tagIds || null,
      notes: notes || null
    })
  });
  if (!res.ok) {
    let errMsg = 'Failed to submit classification review';
    try {
      const errData = await res.json();
      if (errData && errData.detail) {
        if (typeof errData.detail === 'string') {
          errMsg = errData.detail;
        } else if (Array.isArray(errData.detail)) {
          errMsg = errData.detail.map((d: any) => `${d.loc ? d.loc.join('.') + ': ' : ''}${d.msg}`).join(', ');
        } else if (typeof errData.detail === 'object') {
          errMsg = JSON.stringify(errData.detail);
        }
      }
    } catch (e) {
      // ignore parsing error
    }
    throw new Error(errMsg);
  }
  return res.json();
}

/**
 * Trigger administrative system tasks.
 */
export async function triggerAdminAction(action: 'reindex' | 'scan' | 'regenerate-thumbnails'): Promise<any> {
  const endpoint = action === 'regenerate-thumbnails' ? 'regenerate-thumbnails' : action;
  const res = await fetch(`${API_BASE}/admin/${endpoint}`, { method: 'POST' });
  if (!res.ok) throw new Error(`Failed to execute admin action ${action}`);
  return res.json();
}
