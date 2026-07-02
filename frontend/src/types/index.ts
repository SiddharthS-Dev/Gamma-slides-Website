// TypeScript Interfaces for SlideVault Frontend

export interface Category {
  id: string;
  name: string;
  slug?: string;
  color?: string;
  presentation_count?: number;
  parent_id?: string | null;
}

export interface Department {
  id: string;
  name: string;
  presentation_count?: number;
}

export interface TagType {
  id: string;
  name: string;
  color?: string;
}

export interface Presentation {
  id: string;
  title: string;
  description?: string;
  file_name: string;
  file_type: string;
  file_size: number;
  slide_count?: number;
  reading_time_minutes?: number;
  thumbnail_url?: string;
  category?: Category;
  department?: Department;
  tags: TagType[];
  author?: string;
  version?: string;
  view_count: number;
  download_count: number;
  popularity_score: number;
  created_at: string;
  updated_at: string;
  is_offline_available?: boolean;
}

export interface PresentationDetail extends Presentation {
  file_path: string;
  file_hash: string;
  file_modified_at?: string;
  last_viewed_at?: string;
  is_active: boolean;
}

export interface AISummary {
  presentation_id: string;
  short_summary: string;
  medium_summary: string;
  executive_summary: string;
  learning_objectives: string[];
  key_topics: string[];
  generated_by: string;
}

export interface AIKeyword {
  id: string;
  presentation_id: string;
  keyword: string;
  relevance: number;
}

export interface SimilarPresentation {
  id: string;
  title: string;
  file_type: string;
  similarity_score: number;
}

export interface RecommendationSet {
  presentation_id: string;
  similar: SimilarPresentation[];
}

export interface QualityScores {
  presentation_id: string;
  completeness_score: number;
  freshness_score: number;
  knowledge_score: number;
  popularity_score: number;
  overall_score: number;
}

export interface Bookmark {
  id: string;
  presentation_id: string;
  slide_number?: number;
  note?: string;
  created_at: string;
}

export interface SearchSuggestion {
  text: string;
  type: 'title' | 'tag' | 'category' | 'author';
  id?: string;
}

export interface AnalyticsSummary {
  total_presentations: number;
  total_views: number;
  total_downloads: number;
  total_categories: number;
  total_departments: number;
  active_users_count: number;
  trending_presentations: Presentation[];
  most_viewed_presentations: Presentation[];
  recently_added: Presentation[];
}

export interface StorageStats {
  total_files: number;
  total_size_bytes: number;
  by_type: Record<string, { count: number; size: number }>;
  thumbnail_count: number;
  thumbnail_size_bytes: number;
}

export interface IngestionStatus {
  is_running: boolean;
  last_scan_at?: string;
  files_processed: number;
  files_failed: number;
  files_skipped: number;
  watch_paths: string[];
}

export interface SlideContent {
  slide_number: number;
  heading: string;
  body: string;
  speaker_notes: string;
  has_image: boolean;
}

export interface SlideContentResponse {
  presentation_id: string;
  title: string;
  total_slides: number;
  slides: SlideContent[];
}
