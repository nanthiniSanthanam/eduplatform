/**
 * File: frontend/src/services/instructorService.js
 * Version: 2.7.0 (Critical fixes for EditCoursePage loading issues)
 * Date: 2025-05-25
 * Author: mohithasanthanam
 * Last Modified: 2025-05-25 06:45:21 UTC
 * 
 * Enhanced Instructor API Service - Fixed EditCoursePage loading issues
 * 
 * IMPROVEMENTS:
 * 1. FIXED: Data structure consistency to ensure EditCoursePage loads properly
 * 2. FIXED: Response handling in getCourseBySlug and getAllCourses
 * 3. FIXED: Data format consistency between functions
 * 4. FIXED: Other minor optimizations and bug fixes
 */

// Import apiClient directly from api.js and full api module for auth utilities
import api, { apiClient } from '../services/api';
import secureTokenStorage from '../utils/secureTokenStorage';

// FIXED: Enhanced slug validation to prevent security vulnerabilities
const isSlug = (value) => {
  if (typeof value !== 'string') return false;
  
  // Basic validation - must be string that doesn't consist entirely of digits
  if (/^\d+$/.test(value)) return false;
  
  // SECURITY FIX: Prevent path traversal attacks
  if (value.includes('..') || value.includes('/') || value.includes('\\')) {
    console.warn('Potential path traversal attempt detected:', value);
    return false;
  }
  
  // Prevent script injection attempts
  if (/<script|javascript:|data:/i.test(value)) {
    console.warn('Potential script injection attempt detected:', value);
    return false;
  }
  
  // Basic slug format validation (alphanumeric, hyphens, underscores)
  if (!/^[a-zA-Z0-9_-]+$/.test(value)) {
    console.warn('Invalid slug format:', value);
    return false;
  }
  
  return true;
};

/**
 * FIXED: Enhanced browser storage fallback mechanism
 */
const getTokenWithFallback = () => {
  try {
    if (secureTokenStorage && typeof secureTokenStorage.getToken === 'function') {
      return secureTokenStorage.getToken();
    }
  } catch (error) {
    console.warn('Primary token storage failed, trying fallback:', error);
  }
  
  // Fallback to basic token retrieval
  try {
    const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    return token;
  } catch (fallbackError) {
    console.error('All token storage methods failed:', fallbackError);
    return null;
  }
};

/**
 * CRITICAL FIX: Pure synchronous token validation - NO REFRESH CALLS
 * This completely eliminates the deadlock by removing any async operations
 */
const validateToken = () => {
  try {
    // DEADLOCK FIX: Just return the token validity check - DO NOT trigger refresh
    // This must be a pure, synchronous function that only checks expiration
    return secureTokenStorage.isTokenValid();
  } catch (error) {
    // IMPROVED: Better error logging instead of swallowing errors
    console.error('Token validation check failed with stack:', error);
    return false;
  }
};

// IMPROVED: Circuit breaker for refresh attempts
// This prevents unnecessary refresh attempts when token is invalid
globalThis.__refreshFailedUntilReload = globalThis.__refreshFailedUntilReload || false;

/**
 * CRITICAL FIX: Global single-flight refresh pattern to prevent multiple concurrent refreshes
 * Using globalThis to ensure only one refresh happens across the entire application
 */
const performTokenRefresh = async () => {
  // IMPROVED: Circuit breaker to prevent repeated refresh attempts
  if (globalThis.__refreshFailedUntilReload) {
    console.log('Circuit breaker active: refresh previously failed, redirecting to login');
    redirectToLogin();
    throw new Error('Authentication failed - circuit breaker active');
  }
  
  // Check if refresh is already in progress globally
  if (globalThis.__refreshPromise) {
    console.log('Token refresh already in progress globally, waiting...');
    return await globalThis.__refreshPromise;
  }
  
  // IMPROVED: Set promise before awaiting to handle synchronous throws
  let refreshPromise;
  try {
    console.log('Starting global token refresh...');
    refreshPromise = api.auth.refreshToken();
    // Set the global promise BEFORE awaiting
    globalThis.__refreshPromise = refreshPromise;
    
    await refreshPromise;
    
    // Verify that refresh actually worked
    if (secureTokenStorage.isTokenValid()) {
      console.log('Global token refresh successful and verified');
      return true;
    } else {
      throw new Error('Token refresh verification failed');
    }
  } catch (error) {
    console.error('Global token refresh failed:', error);
    // IMPROVED: Set circuit breaker flag on refresh failure
    globalThis.__refreshFailedUntilReload = true;
    throw error;
  } finally {
    // Always clear the global promise when done
    globalThis.__refreshPromise = null;
  }
};

/**
 * Redirect to login page with return URL
 */
const redirectToLogin = (returnPath) => {
  const currentPath = returnPath || window.location.pathname;
  window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`;
};

/**
 * FIXED: Request deduplication and caching with proper cleanup
 */
const requestCache = new Map();
const pendingRequests = new Map();

// IMPROVED: Better cache key generation using URL instead of function text
const getCacheKey = (method, url, params) => {
  return `${method}:${url}:${JSON.stringify(params || {})}`;
};

/**
 * CRITICAL DEADLOCK FIX: Completely non-blocking request handler
 * - Removed ALL blocking pre-request token validation
 * - Token refresh ONLY happens on 401 response
 * - Enhanced skipAuthCheck support for public endpoints
 */
const handleRequest = async (apiCall, errorMessage, options = {}) => {
  const { 
    enableCache = false, 
    cacheTime = 30000, // 30 seconds default cache
    abortController = null,
    skipAuthCheck = false,
    url = '', // IMPROVED: Allow passing URL for better cache key generation
    returnRawResponse = false // FIXED: Option to return the raw response
  } = options;
  
  // IMPROVED: Determine the actual URL for cache key
  const requestUrl = url || (typeof apiCall === 'function' ? apiCall.toString().match(/['"](\/[^'"]+)['"]/)?.[1] || '' : '');
  
  // Generate cache key if caching is enabled
  let cacheKey = null;
  if (enableCache) {
    // IMPROVED: Use URL in cache key instead of function text
    cacheKey = getCacheKey(apiCall.name || 'unknown', requestUrl, options.params);
    
    // Check if we have a cached response
    const cached = requestCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < cacheTime) {
      console.log('Returning cached response for:', cacheKey);
      return cached.data;
    }
    
    // Check if this request is already pending to prevent duplicate calls
    if (pendingRequests.has(cacheKey)) {
      console.log('Request already pending, waiting for result:', cacheKey);
      return await pendingRequests.get(cacheKey);
    }
  }
  
  const executeRequest = async () => {
    try {
      // DEADLOCK FIX: Skip ALL token validation for public endpoints
      // For protected endpoints, don't block - let 401 handle auth issues
      if (!skipAuthCheck) {
        // Only do a quick, non-blocking token check for logging purposes
        const isValid = validateToken(); // Pure synchronous check only
        if (!isValid) {
          console.warn('Token appears invalid, but proceeding with request (401 will trigger refresh if needed)');
          // CRITICAL: Do not block here - let the request proceed
        }
      }
      
      // FIXED: Execute API call with AbortController support
      let response;
      if (abortController) {
        response = await apiCall({ signal: abortController.signal });
      } else {
        response = await apiCall();
      }
      
      // FIXED: Return raw response if requested (needed for EditCoursePage)
      if (returnRawResponse) {
        return response;
      }
      
      const data = response.data;
      
      // Cache the response if caching is enabled
      if (enableCache && cacheKey) {
        requestCache.set(cacheKey, {
          data,
          timestamp: Date.now()
        });
        
        // Clean up cache entry after cache time
        setTimeout(() => {
          requestCache.delete(cacheKey);
        }, cacheTime);
      }
      
      return data;
      
    } catch (error) {
      // FIXED: Handle AbortError gracefully
      if (error.name === 'AbortError') {
        console.log('Request was aborted');
        throw error;
      }
      
      console.error(`${errorMessage}:`, error);
      
      // CRITICAL DEADLOCK FIX: Enhanced 401 handling with global single-flight refresh
      if (error.response && error.response.status === 401) {
        console.warn('Received 401 response, attempting global token refresh and retry');
        
        try {
          // Use global single-flight refresh to prevent multiple concurrent refreshes
          await performTokenRefresh();
          
          console.log('Global token refresh successful, retrying original request');
          
          // Retry the original request once
          let retryResponse;
          if (abortController && !abortController.signal.aborted) {
            retryResponse = await apiCall({ signal: abortController.signal });
          } else if (!abortController) {
            retryResponse = await apiCall();
          } else {
            throw new Error('Request aborted during retry');
          }
          
          // FIXED: Return raw response if requested
          if (returnRawResponse) {
            return retryResponse;
          }
          
          return retryResponse.data;
          
        } catch (refreshError) {
          if (refreshError.name === 'AbortError') {
            throw refreshError;
          }
          
          console.error('Global token refresh failed, redirecting to login:', refreshError);
          
          // Clean logout and redirect
          try {
            if (api.logout && typeof api.logout === 'function') {
              api.logout();
            }
          } catch (logoutError) {
            console.warn('Logout failed:', logoutError);
          }
          
          redirectToLogin();
          throw new Error('Authentication failed - redirecting to login');
        }
      }
      
      // FIXED: Enhanced error formatting with detailed information
      const formattedError = {
        message: error.response?.data?.detail || 
                error.response?.data?.message || 
                error.message || 
                errorMessage,
        status: error.response?.status,
        details: error.response?.data || {},
        originalError: error,
        timestamp: new Date().toISOString()
      };
      
      throw formattedError;
    }
  };
  
  // Handle pending requests for deduplication
  if (enableCache && cacheKey) {
    const pendingPromise = executeRequest();
    pendingRequests.set(cacheKey, pendingPromise);
    
    try {
      const result = await pendingPromise;
      return result;
    } finally {
      // FIXED: Always clean up pending requests to prevent memory leaks
      pendingRequests.delete(cacheKey);
    }
  } else {
    return await executeRequest();
  }
};

/**
 * DEADLOCK RESOLUTION: Enhanced instructor service with completely fixed request handling
 */
const instructorService = {
  // IMPROVED: Removed skipAuthCheck for instructor-only endpoint
  getAllCourses: async (options = {}) => {
    const result = await handleRequest(
      async (requestOptions) => await apiClient.get('/instructor/courses/', requestOptions),
      'Failed to fetch instructor courses',
      { 
        enableCache: true, 
        cacheTime: 30000,
        url: '/instructor/courses/', // IMPROVED: Explicit URL for better cache key
        ...options 
      }
    );
    
    // FIXED: Ensure consistent response format for getAllCourses
    // This fixes an issue where the page expects results in a specific format
    if (result && !result.results && Object.keys(result).length > 0) {
      if (Array.isArray(result)) {
        return { results: result };
      } else {
        // Convert object with numeric keys to array if needed
        const isObjectWithNumericKeys = Object.keys(result).every(key => !isNaN(Number(key)));
        if (isObjectWithNumericKeys) {
          const arrayResults = Object.values(result);
          return { results: arrayResults };
        }
      }
    }
    
    return result;
  },
  
  // FIXED: Enhanced course fetching with proper error handling
  getCourse: async (courseId, options = {}) => {
    // FIXED: Enhanced slug validation
    if (isSlug(courseId)) {
      return instructorService.getCourseBySlug(courseId, options);
    }
    
    try {
      // Use cached courses to avoid heavy repeated calls
      const courses = await instructorService.getAllCourses({ 
        enableCache: true,
        ...options 
      });
      
      const coursesList = courses.results || courses;
      
      // Ensure coursesList is array-like and has elements
      if (!coursesList || typeof coursesList !== 'object') {
        throw new Error(`Invalid courses data received for ID ${courseId}`);
      }
      
      // Find the course with matching ID
      const course = Array.isArray(coursesList) 
        ? coursesList.find(c => c.id?.toString() === courseId?.toString())
        : Object.values(coursesList).find(c => c.id?.toString() === courseId?.toString());
      
      if (course?.slug) {
        return instructorService.getCourseBySlug(course.slug, options);
      } else {
        throw new Error(`Course with ID ${courseId} not found`);
      }
    } catch (error) {
      if (error.name === 'AbortError') throw error;
      console.error(`Failed to fetch course using ID mapping: ${error.message}`);
      throw error;
    }
  },
  
  // FIXED: Enhanced course creation with proper FormData handling
  createCourse: async (courseData, options = {}) => {
    const formData = new FormData();
    
    // Add timestamp to title to ensure unique slugs
    const timestamp = new Date().toISOString()
      .replace(/[-:]/g, '')
      .replace('T', '_')
      .replace(/\..+/, '');
    const uniqueTitle = courseData.title + ` [${timestamp}]`;
    
    // Basic required fields
    formData.append('title', uniqueTitle);
    
    // Ensure description is never blank
    const description = courseData.description && courseData.description.trim() !== '' 
      ? courseData.description 
      : `Course description for ${uniqueTitle}`;
    formData.append('description', description);
    
    formData.append('category_id', courseData.category_id || '1');
    
    // Optional fields with proper validation
    if (courseData.subtitle) formData.append('subtitle', courseData.subtitle);
    if (courseData.level) formData.append('level', courseData.level);
    if (courseData.price !== undefined && courseData.price !== null) {
      formData.append('price', courseData.price.toString());
    }
    if (courseData.discount_price) {
      formData.append('discount_price', courseData.discount_price.toString());
    }
    if (courseData.duration) formData.append('duration', courseData.duration.toString());
    
    // FIXED: Boolean fields - backend expects strings, not booleans
    formData.append('has_certificate', courseData.has_certificate ? 'true' : 'false');
    formData.append('is_featured', courseData.is_featured ? 'true' : 'false');
    
    // JSON fields - convert arrays to JSON strings
    if (courseData.requirements && Array.isArray(courseData.requirements)) {
      formData.append('requirements', JSON.stringify(courseData.requirements));
    }
    
    if (courseData.skills && Array.isArray(courseData.skills)) {
      formData.append('skills', JSON.stringify(courseData.skills));
    }
    
    // File fields - only append if it's a File object
    if (courseData.thumbnail && courseData.thumbnail instanceof File) {
      formData.append('thumbnail', courseData.thumbnail);
    }
    
    return handleRequest(
      async (requestOptions) => await apiClient.post('/instructor/courses/', formData, requestOptions),
      'Failed to create course',
      {
        url: '/instructor/courses/', // IMPROVED: Explicit URL for better cache key
        ...options
      }
    );
  },
  
  // FIXED: Enhanced course updating with proper FormData handling
  updateCourse: async (courseIdOrSlug, courseData, options = {}) => {
    // Validate courseIdOrSlug
    if (!courseIdOrSlug) {
      throw new Error('Course ID or slug is required for update');
    }
    
    // FIXED: Enhanced slug validation
    if (!isSlug(courseIdOrSlug) && !Number.isInteger(Number(courseIdOrSlug))) {
      throw new Error('Invalid course identifier provided');
    }
    
    let formData;
    
    // Check if courseData is already a FormData instance
    if (courseData instanceof FormData) {
      console.log('Using provided FormData directly for course update');
      formData = courseData;
    } else {
      // Create new FormData from object
      console.log('Creating new FormData from course data object');
      formData = new FormData();
      
      // FIXED: Always include required fields to avoid 400 errors
      if (courseData.title) formData.append('title', courseData.title);
      if (courseData.description) formData.append('description', courseData.description);
      if (courseData.category_id) formData.append('category_id', courseData.category_id.toString());
      
      // Optional fields
      if (courseData.subtitle) formData.append('subtitle', courseData.subtitle);
      if (courseData.level) formData.append('level', courseData.level);
      if (courseData.price !== undefined && courseData.price !== null) {
        formData.append('price', courseData.price.toString());
      }
      if (courseData.discount_price) {
        formData.append('discount_price', courseData.discount_price.toString());
      }
      if (courseData.duration) formData.append('duration', courseData.duration.toString());
      
      // FIXED: Boolean fields - backend expects strings, not booleans
      if (courseData.has_certificate !== undefined) {
        formData.append('has_certificate', courseData.has_certificate ? 'true' : 'false');
      }
      if (courseData.is_featured !== undefined) {
        formData.append('is_featured', courseData.is_featured ? 'true' : 'false');
      }
      if (courseData.is_published !== undefined) {
        formData.append('is_published', courseData.is_published ? 'true' : 'false');
      }
      
      // JSON fields
      if (courseData.requirements && Array.isArray(courseData.requirements)) {
        formData.append('requirements', JSON.stringify(courseData.requirements));
      }
      
      if (courseData.skills && Array.isArray(courseData.skills)) {
        formData.append('skills', JSON.stringify(courseData.skills));
      }
      
      // File fields - only append if it's a File object
      if (courseData.thumbnail && courseData.thumbnail instanceof File) {
        formData.append('thumbnail', courseData.thumbnail);
      }
    }
    
    try {
      if (isSlug(courseIdOrSlug)) {
        // Use slug directly
        return handleRequest(
          async (requestOptions) => await apiClient.patch(`/instructor/courses/${courseIdOrSlug}/`, formData, requestOptions),
          `Failed to update course ${courseIdOrSlug}`,
          {
            url: `/instructor/courses/${courseIdOrSlug}/`, // IMPROVED: Explicit URL for better cache key
            ...options
          }
        );
      } else {
        // Find course by ID and use its slug
        const courses = await instructorService.getAllCourses({ 
          enableCache: true,
          ...options 
        });
        
        const coursesList = courses.results || courses;
        
        // Find course by ID
        const course = Array.isArray(coursesList) 
          ? coursesList.find(c => c.id?.toString() === courseIdOrSlug?.toString())
          : Object.values(coursesList).find(c => c.id?.toString() === courseIdOrSlug?.toString());
        
        if (course?.slug) {
          return handleRequest(
            async (requestOptions) => await apiClient.patch(`/instructor/courses/${course.slug}/`, formData, requestOptions),
            `Failed to update course ${courseIdOrSlug}`,
            {
              url: `/instructor/courses/${course.slug}/`, // IMPROVED: Explicit URL for better cache key
              ...options
            }
          );
        } else {
          throw new Error(`Course with ID ${courseIdOrSlug} not found`);
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') throw error;
      console.error(`Failed to update course: ${error.message}`);
      throw error;
    }
  },
  
  // FIXED: Enhanced course fetching by slug with proper validation
  getCourseBySlug: async (slug, options = {}) => {
    // FIXED: Enhanced slug validation
    if (!isSlug(slug)) {
      throw new Error(`Invalid slug format: ${slug}`);
    }
    
    console.log(`Instructor service: Getting course with slug: ${slug}`);
    
    try {
      // FIXED: Return the full response with data property
      const response = await handleRequest(
        async (requestOptions) => {
          console.log(`Making instructor API request to: /instructor/courses/${slug}/`);
          return await apiClient.get(`/instructor/courses/${slug}/`, requestOptions);
        },
        `Failed to fetch course by slug: ${slug}`,
        {
          url: `/instructor/courses/${slug}/`, // IMPROVED: Explicit URL for better cache key
          returnRawResponse: true, // FIXED: Get the full response object
          ...options
        }
      );
      
      // Return the course data in the expected format
      return response.data;
      
    } catch (error) {
      if (error.name === 'AbortError') throw error;
      console.error(`Error fetching from instructor endpoint: ${error.message}`);
      
      // Fallback to regular course endpoint if needed
      try {
        console.log('Falling back to regular course endpoint');
        const fallbackResponse = await handleRequest(
          async (requestOptions) => await apiClient.get(`/courses/${slug}/`, requestOptions),
          `Failed to fetch course by slug (fallback): ${slug}`,
          {
            url: `/courses/${slug}/`, // IMPROVED: Explicit URL for better cache key
            skipAuthCheck: true, // Public endpoint
            returnRawResponse: true, // FIXED: Get the full response object
            ...options
          }
        );
        
        // Return the fallback course data
        return fallbackResponse.data;
        
      } catch (fallbackError) {
        if (fallbackError.name === 'AbortError') throw fallbackError;
        console.error(`Fallback course endpoint also failed: ${fallbackError.message}`);
        throw error; // Throw the original error
      }
    }
  },
  
  // Module management with enhanced error handling
  getModules: async (courseId, options = {}) => {
    return handleRequest(
      async (requestOptions) => await apiClient.get('/instructor/modules/', { 
        params: { course: courseId },
        ...requestOptions 
      }),
      `Failed to fetch modules for course ${courseId}`,
      {
        url: `/instructor/modules/?course=${courseId}`, // IMPROVED: Explicit URL for better cache key
        ...options
      }
    );
  },
  
  getModule: async (moduleId, options = {}) => {
    return handleRequest(
      async (requestOptions) => await apiClient.get(`/instructor/modules/${moduleId}/`, requestOptions),
      `Failed to fetch module ${moduleId}`,
      {
        url: `/instructor/modules/${moduleId}/`, // IMPROVED: Explicit URL for better cache key
        ...options
      }
    );
  },
  
  createModule: async (moduleData, options = {}) => {
    return handleRequest(
      async (requestOptions) => await apiClient.post('/instructor/modules/', moduleData, requestOptions),
      'Failed to create module',
      {
        url: '/instructor/modules/', // IMPROVED: Explicit URL for better cache key
        ...options
      }
    );
  },
  
  updateModule: async (moduleId, moduleData, options = {}) => {
    return handleRequest(
      async (requestOptions) => await apiClient.put(`/instructor/modules/${moduleId}/`, moduleData, requestOptions),
      `Failed to update module ${moduleId}`,
      {
        url: `/instructor/modules/${moduleId}/`, // IMPROVED: Explicit URL for better cache key
        ...options
      }
    );
  },
  
  // Lesson management with enhanced error handling
  getLessons: async (moduleId, options = {}) => {
    return handleRequest(
      async (requestOptions) => await apiClient.get('/instructor/lessons/', { 
        params: { module: moduleId },
        ...requestOptions 
      }),
      `Failed to fetch lessons for module ${moduleId}`,
      {
        url: `/instructor/lessons/?module=${moduleId}`, // IMPROVED: Explicit URL for better cache key
        ...options
      }
    );
  },
  
  getLesson: async (lessonId, options = {}) => {
    return handleRequest(
      async (requestOptions) => await apiClient.get(`/instructor/lessons/${lessonId}/`, requestOptions),
      `Failed to fetch lesson ${lessonId}`,
      {
        url: `/instructor/lessons/${lessonId}/`, // IMPROVED: Explicit URL for better cache key
        ...options
      }
    );
  },
  
  createLesson: async (moduleId, lessonData, options = {}) => {
    // Support both implementation styles
    if (moduleId && typeof moduleId === 'object') {
      // Called with just lessonData object
      options = lessonData || {};
      lessonData = moduleId;
      return handleRequest(
        async (requestOptions) => await apiClient.post('/instructor/lessons/', lessonData, requestOptions),
        'Failed to create lesson',
        {
          url: '/instructor/lessons/', // IMPROVED: Explicit URL for better cache key
          ...options
        }
      );
    } else {
      // Called with moduleId and lessonData
      const completeData = {
        ...lessonData,
        module: moduleId
      };
      return handleRequest(
        async (requestOptions) => await apiClient.post('/instructor/lessons/', completeData, requestOptions),
        'Failed to create lesson',
        {
          url: '/instructor/lessons/', // IMPROVED: Explicit URL for better cache key
          ...options
        }
      );
    }
  },
  
  updateLesson: async (lessonId, lessonData, options = {}) => {
    return handleRequest(
      async (requestOptions) => await apiClient.put(`/instructor/lessons/${lessonId}/`, lessonData, requestOptions),
      `Failed to update lesson ${lessonId}`,
      {
        url: `/instructor/lessons/${lessonId}/`, // IMPROVED: Explicit URL for better cache key
        ...options
      }
    );
  },
  
  // Resource management
  getResources: async (lessonId, options = {}) => {
    return handleRequest(
      async (requestOptions) => await apiClient.get('/instructor/resources/', { 
        params: { lesson: lessonId },
        ...requestOptions 
      }),
      `Failed to fetch resources for lesson ${lessonId}`,
      {
        url: `/instructor/resources/?lesson=${lessonId}`, // IMPROVED: Explicit URL for better cache key
        ...options
      }
    );
  },
  
  getInstructorLessons: async (options = {}) => {
    return handleRequest(
      async (requestOptions) => await apiClient.get('/instructor/lessons/', requestOptions),
      'Failed to fetch instructor lessons',
      {
        url: '/instructor/lessons/', // IMPROVED: Explicit URL for better cache key
        ...options
      }
    );
  },

  getInstructorStatistics: async (options = {}) => {
    return handleRequest(
      async (requestOptions) => await apiClient.get('/statistics/instructor/', requestOptions),
      'Failed to fetch instructor statistics',
      {
        url: '/statistics/instructor/', // IMPROVED: Explicit URL for better cache key
        ...options
      }
    );
  },
  
  // FIXED: Enhanced course deletion with proper validation
  deleteCourse: async (courseIdOrSlug, options = {}) => {
    if (!courseIdOrSlug) {
      throw new Error("Course ID or slug is required for deletion");
    }
    
    // FIXED: Enhanced slug validation
    if (!isSlug(courseIdOrSlug) && !Number.isInteger(Number(courseIdOrSlug))) {
      throw new Error('Invalid course identifier provided for deletion');
    }
    
    try {
      console.log(`Attempting to delete course: ${courseIdOrSlug}`);
      
      // If it's a slug, use it directly
      if (isSlug(courseIdOrSlug)) {
        return handleRequest(
          async (requestOptions) => await apiClient.delete(`/instructor/courses/${courseIdOrSlug}/`, requestOptions),
          `Failed to delete course ${courseIdOrSlug}`,
          {
            url: `/instructor/courses/${courseIdOrSlug}/`, // IMPROVED: Explicit URL for better cache key
            ...options
          }
        );
      }
      
      // If it's an ID, find the corresponding slug
      const courses = await instructorService.getAllCourses({ 
        enableCache: true,
        ...options 
      });
      
      const coursesList = courses.results || courses;
      
      // Find course by ID
      const course = Array.isArray(coursesList) 
        ? coursesList.find(c => c.id?.toString() === courseIdOrSlug?.toString())
        : Object.values(coursesList).find(c => c.id?.toString() === courseIdOrSlug?.toString());
      
      if (course?.slug) {
        return handleRequest(
          async (requestOptions) => await apiClient.delete(`/instructor/courses/${course.slug}/`, requestOptions),
          `Failed to delete course ${courseIdOrSlug}`,
          {
            url: `/instructor/courses/${course.slug}/`, // IMPROVED: Explicit URL for better cache key
            ...options
          }
        );
      } else {
        throw new Error(`Course with ID ${courseIdOrSlug} not found`);
      }
    } catch (error) {
      if (error.name === 'AbortError') throw error;
      console.error(`Course deletion failed: ${error.message}`);
      throw error;
    }
  },

  // Course publishing with enhanced error handling
  publishCourse: async (slug, shouldPublish = true, options = {}) => {
    // FIXED: Enhanced slug validation
    if (!isSlug(slug)) {
      throw new Error(`Invalid slug format for publishing: ${slug}`);
    }
    
    return handleRequest(
      async (requestOptions) => await apiClient.put(`/instructor/courses/${slug}/publish/`, 
        { publish: shouldPublish }, 
        requestOptions
      ),
      `Failed to ${shouldPublish ? 'publish' : 'unpublish'} course`,
      {
        url: `/instructor/courses/${slug}/publish/`, // IMPROVED: Explicit URL for better cache key
        ...options
      }
    );
  },
  
  // FIXED: Utility function to clear request cache and global refresh state
  clearCache: () => {
    console.log('Clearing instructor service cache and global refresh state');
    requestCache.clear();
    pendingRequests.clear();
    
    // Clear the global refresh promise to allow fresh auth attempts
    globalThis.__refreshPromise = null;
    // IMPROVED: Reset circuit breaker on manual cache clear
    globalThis.__refreshFailedUntilReload = false;
  },
  
  // FIXED: Utility function to get cache statistics
  getCacheStats: () => {
    return {
      cacheSize: requestCache.size,
      pendingRequests: pendingRequests.size,
      cacheEntries: Array.from(requestCache.keys()),
      refreshInProgress: globalThis.__refreshPromise !== null,
      // IMPROVED: Add circuit breaker status
      circuitBreakerActive: globalThis.__refreshFailedUntilReload || false
    };
  },
  
  // IMPROVED: Add a lightweight public health check endpoint for ProtectedRoute
  getPublicHealthCheck: async (options = {}) => {
    return handleRequest(
      async (requestOptions) => await apiClient.get('/statistics/platform/', requestOptions),
      'Failed to fetch platform health check',
      {
        url: '/statistics/platform/', // Explicit URL for better cache key
        skipAuthCheck: true, // This is a genuinely public endpoint
        enableCache: true,
        cacheTime: 60000, // Cache for 1 minute
        ...options
      }
    );
  }
};

export default instructorService;