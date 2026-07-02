import { openDB } from 'idb';
import type { IDBPDatabase } from 'idb';

const DB_NAME = 'slidevault-offline-db';
const DB_VERSION = 2;

export interface CachedPresentation {
  id: string;
  title: string;
  description?: string;
  file_name: string;
  file_type: string;
  file_size: number;
  slide_count?: number;
  reading_time_minutes?: number;
  thumbnail_url?: string;
  category?: { id: string; name: string };
  department?: { id: string; name: string };
  tags: Array<{ id: string; name: string; color?: string }>;
  author?: string;
  version?: string;
  view_count: number;
  download_count: number;
  popularity_score: number;
  created_at: string;
  updated_at: string;
}

export interface CachedSlide {
  slide_number: number;
  heading: string;
  body: string;
  speaker_notes: string;
  has_image: boolean;
}

export interface CachedSlidesResponse {
  presentation_id: string;
  title: string;
  total_slides: number;
  slides: CachedSlide[];
}

export class OfflineCache {
  private static dbPromise: Promise<IDBPDatabase> | null = null;

  private static getDB(): Promise<IDBPDatabase> {
    if (!this.dbPromise) {
      this.dbPromise = openDB(DB_NAME, DB_VERSION, {
        upgrade(db) {
          // Store presentation metadata list
          if (!db.objectStoreNames.contains('presentations')) {
            db.createObjectStore('presentations', { keyPath: 'id' });
          }
          // Store details, summaries, keywords, quality, bookmarks, and slides per presentation
          if (!db.objectStoreNames.contains('details')) {
            db.createObjectStore('details', { keyPath: 'id' });
          }
          if (!db.objectStoreNames.contains('summaries')) {
            db.createObjectStore('summaries', { keyPath: 'presentation_id' });
          }
          if (!db.objectStoreNames.contains('keywords')) {
            db.createObjectStore('keywords', { keyPath: 'presentation_id' });
          }
          if (!db.objectStoreNames.contains('recs')) {
            db.createObjectStore('recs', { keyPath: 'presentation_id' });
          }
          if (!db.objectStoreNames.contains('quality')) {
            db.createObjectStore('quality', { keyPath: 'presentation_id' });
          }
          if (!db.objectStoreNames.contains('bookmarks')) {
            db.createObjectStore('bookmarks', { keyPath: 'presentation_id' });
          }
          if (!db.objectStoreNames.contains('slides')) {
            db.createObjectStore('slides', { keyPath: 'presentation_id' });
          }
          if (!db.objectStoreNames.contains('files')) {
            db.createObjectStore('files');
          }
          // Store category lists, department lists, and tag lists
          if (!db.objectStoreNames.contains('meta')) {
            db.createObjectStore('meta');
          }
        },
      });
    }
    return this.dbPromise;
  }

  // Presentations List Caching
  static async getPresentations(): Promise<CachedPresentation[] | null> {
    try {
      const db = await this.getDB();
      return await db.getAll('presentations');
    } catch (err) {
      console.error('Error reading presentations from IndexedDB Cache', err);
      return null;
    }
  }

  static async setPresentations(presentations: CachedPresentation[]): Promise<void> {
    try {
      const db = await this.getDB();
      const tx = db.transaction('presentations', 'readwrite');
      for (const pres of presentations) {
        await tx.store.put(pres);
      }
      await tx.done;
    } catch (err) {
      console.error('Error writing presentations to IndexedDB Cache', err);
    }
  }

  // Metadata (categories, departments, tags) Caching
  static async getMeta(key: string): Promise<any | null> {
    try {
      const db = await this.getDB();
      return await db.get('meta', key);
    } catch (err) {
      console.error(`Error reading metadata ${key} from IndexedDB Cache`, err);
      return null;
    }
  }

  static async setMeta(key: string, value: any): Promise<void> {
    try {
      const db = await this.getDB();
      await db.put('meta', value, key);
    } catch (err) {
      console.error(`Error writing metadata ${key} to IndexedDB Cache`, err);
    }
  }

  // Presentation Detail Caching
  static async getDetail(id: string): Promise<any | null> {
    try {
      const db = await this.getDB();
      return await db.get('details', id);
    } catch (err) {
      console.error(`Error reading details for ${id} from cache`, err);
      return null;
    }
  }

  static async setDetail(id: string, value: any): Promise<void> {
    try {
      const db = await this.getDB();
      await db.put('details', value);
      
      // Also ensure this presentation is added to the 'presentations' catalog store so it can be listed offline!
      const presObj = {
        id: value.id,
        title: value.title,
        description: value.description,
        file_name: value.file_name,
        file_type: value.file_type,
        file_size: value.file_size,
        slide_count: value.slide_count,
        reading_time_minutes: value.reading_time_minutes,
        thumbnail_url: value.thumbnail_url,
        category: value.category,
        department: value.department,
        tags: value.tags,
        author: value.author,
        version: value.version,
        view_count: value.view_count,
        download_count: value.download_count,
        popularity_score: value.popularity_score,
        created_at: value.created_at,
        updated_at: value.updated_at
      };
      await db.put('presentations', presObj);
    } catch (err) {
      console.error(`Error writing details for ${id} to cache`, err);
    }
  }

  // AI Summary Caching
  static async getSummary(id: string): Promise<any | null> {
    try {
      const db = await this.getDB();
      return await db.get('summaries', id);
    } catch (err) {
      console.error(`Error reading summary for ${id} from cache`, err);
      return null;
    }
  }

  static async setSummary(id: string, value: any): Promise<void> {
    try {
      const db = await this.getDB();
      await db.put('summaries', { presentation_id: id, ...value });
    } catch (err) {
      console.error(`Error writing summary for ${id} to cache`, err);
    }
  }

  // AI Keywords Caching
  static async getKeywords(id: string): Promise<any | null> {
    try {
      const db = await this.getDB();
      return await db.get('keywords', id);
    } catch (err) {
      console.error(`Error reading keywords for ${id} from cache`, err);
      return null;
    }
  }

  static async setKeywords(id: string, value: any): Promise<void> {
    try {
      const db = await this.getDB();
      await db.put('keywords', { presentation_id: id, keywords: value });
    } catch (err) {
      console.error(`Error writing keywords for ${id} to cache`, err);
    }
  }

  // AI Recommendations Caching
  static async getRecommendations(id: string): Promise<any | null> {
    try {
      const db = await this.getDB();
      return await db.get('recs', id);
    } catch (err) {
      console.error(`Error reading recommendations for ${id} from cache`, err);
      return null;
    }
  }

  static async setRecommendations(id: string, value: any): Promise<void> {
    try {
      const db = await this.getDB();
      await db.put('recs', { presentation_id: id, ...value });
    } catch (err) {
      console.error(`Error writing recommendations for ${id} to cache`, err);
    }
  }

  // Quality Scores Caching
  static async getQuality(id: string): Promise<any | null> {
    try {
      const db = await this.getDB();
      return await db.get('quality', id);
    } catch (err) {
      console.error(`Error reading quality for ${id} from cache`, err);
      return null;
    }
  }

  static async setQuality(id: string, value: any): Promise<void> {
    try {
      const db = await this.getDB();
      await db.put('quality', { presentation_id: id, ...value });
    } catch (err) {
      console.error(`Error writing quality for ${id} to cache`, err);
    }
  }

  // Bookmarks Caching
  static async getBookmarks(id: string): Promise<any | null> {
    try {
      const db = await this.getDB();
      return await db.get('bookmarks', id);
    } catch (err) {
      console.error(`Error reading bookmarks for ${id} from cache`, err);
      return null;
    }
  }

  static async setBookmarks(id: string, value: any): Promise<void> {
    try {
      const db = await this.getDB();
      await db.put('bookmarks', { presentation_id: id, bookmarks: value });
    } catch (err) {
      console.error(`Error writing bookmarks for ${id} to cache`, err);
    }
  }

  // Slides Content Caching
  static async getSlides(id: string): Promise<CachedSlidesResponse | null> {
    try {
      const db = await this.getDB();
      return await db.get('slides', id);
    } catch (err) {
      console.error(`Error reading slides content for ${id} from cache`, err);
      return null;
    }
  }

  static async setSlides(id: string, value: CachedSlidesResponse): Promise<void> {
    try {
      const db = await this.getDB();
      // Ensure presentation_id matches the id parameter
      const data = { ...value, presentation_id: id };
      await db.put('slides', data);
    } catch (err) {
      console.error(`Error writing slides content for ${id} to cache`, err);
    }
  }

  // Get list of presentation IDs cached offline for visual indicator badges
  static async getCachedIds(): Promise<string[]> {
    try {
      const db = await this.getDB();
      const slidesKeys = await db.getAllKeys('slides');
      return slidesKeys.map(k => String(k));
    } catch (err) {
      console.error('Error fetching cached slides keys', err);
      return [];
    }
  }

  // File blob Caching
  static async getFile(id: string): Promise<Blob | null> {
    try {
      const db = await this.getDB();
      return await db.get('files', id);
    } catch (err) {
      console.error(`Error reading file blob for ${id} from cache`, err);
      return null;
    }
  }

  static async setFile(id: string, value: Blob): Promise<void> {
    try {
      const db = await this.getDB();
      await db.put('files', value, id);
    } catch (err) {
      console.error(`Error writing file blob for ${id} to cache`, err);
    }
  }

  static async getDownloadedIds(): Promise<string[]> {
    try {
      const db = await this.getDB();
      const fileKeys = await db.getAllKeys('files');
      return fileKeys.map(k => String(k));
    } catch (err) {
      console.error('Error fetching cached files keys', err);
      return [];
    }
  }
}
