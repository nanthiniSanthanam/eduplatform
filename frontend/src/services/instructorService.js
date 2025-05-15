/**
 * File: frontend/src/services/instructorService.js
 * Version: 2.1.0
 * Date: 2025-07-24 17:08:29
 * Author: nanthiniSanthanam
 * 
 * Enhanced Instructor API Service with Improved Course Management
 * 
 * Key Improvements:
 * 1. Support for both ID and slug-based operations
 * 2. Intelligent course lookup strategy that handles both endpoints
 * 3. Enhanced error handling with detailed feedback
 * 4. Better token management using authPersist
 * 5. Streamlined file upload handling
 * 6. Consistent use of apiClient across all methods
 * 
 * This service handles all instructor-specific API operations including:
 * - Course creation, editing, and deletion
 * - Module and lesson management
 * - Resource and assessment creation
 * - Publishing and unpublishing courses
 */

import axios from 'axios';
import authPersist from '../utils/authPersist';

/**
 * Create axios instance with base URL
 * This initializes a consistent client for all API requests with common configuration
 */
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000, // 15 seconds timeout
});

/**
 * Request interceptor for authentication
 * Uses authPersist to ensure valid tokens are sent with all requests
 */
apiClient.interceptors.request.use(
  config => {
    const token = authPersist.getValidToken() || localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      
      // Refresh token expiry on API operations
      if (authPersist.refreshTokenExpiry) {
        authPersist.refreshTokenExpiry();
      }
    }
    return config;
  },
  error => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

/**
 * Generic request handler with error formatting
 * @param {Function} apiCall - The API call function to execute
 * @param {String} errorMessage - Custom error message to display
 * @returns {Promise} - The API response or formatted error
 */
const handleRequest = async (apiCall, errorMessage) => {
  try {
    const response = await apiCall();
    return response.data;
  } catch (error) {
    console.error(`${errorMessage}:`, error);
    
    // Format error for consistent handling
    const formattedError = {
      message: error.response?.data?.detail || error.response?.data?.message || errorMessage,
      status: error.response?.status,
      details: error.response?.data || {},
      originalError: error
    };
    
    throw formattedError;
  }
};

/**
 * Check if a value is likely a slug rather than an ID
 * @param {string|number} value - The value to check
 * @returns {boolean} - True if the value is likely a slug
 */
const isSlug = (value) => {
  return typeof value === 'string' && isNaN(parseInt(value));
};

/**
 * Comprehensive instructor service API
 * Supports both ID and slug-based operations
 */
const instructorService = {
  // Course management
  getAllCourses: async () => {
    return handleRequest(
      async () => await apiClient.get('/instructor/courses/'),
      'Failed to fetch instructor courses'
    );
  },
  
  getCourse: async (courseId) => {
    // Determine if the ID is actually a slug
    if (isSlug(courseId)) {
      return instructorService.getCourseBySlug(courseId);
    }
    
    // Try to fetch by ID first
    try {
      const coursesResponse = await instructorService.getAllCourses();
      const course = coursesResponse.find(c => c.id?.toString() === courseId?.toString());
      
      if (course?.slug) {
        // If we found the course, get its full details using the slug
        return instructorService.getCourseBySlug(course.slug);
      } else {
        throw new Error(`Course with ID ${courseId} not found`);
      }
    } catch (error) {
      console.error(`Failed to fetch course using ID mapping: ${error.message}`);
      throw error;
    }
  },
  
  createCourse: async (courseData) => {
    // Use FormData for file upload
    const formData = new FormData();
    
    // Add timestamp to title to ensure unique slugs
    const timestamp = new Date().toISOString()
      .replace(/[-:]/g, '')
      .replace('T', '_')
      .replace(/\..+/, '');
    const uniqueTitle = courseData.title + ` [${timestamp}]`;
    
    // Basic fields
    formData.append('title', uniqueTitle);
    
    // Ensure description is never blank
    const description = courseData.description && courseData.description.trim() !== '' 
      ? courseData.description 
      : `Course description for ${uniqueTitle}`;
    formData.append('description', description);
    
    formData.append('category_id', courseData.category_id || '1');
    
    // Optional fields with null checks
    if (courseData.subtitle) formData.append('subtitle', courseData.subtitle);
    if (courseData.level) formData.append('level', courseData.level);
    if (courseData.price) formData.append('price', courseData.price);
    if (courseData.discount_price) formData.append('discount_price', courseData.discount_price);
    if (courseData.duration) formData.append('duration', courseData.duration);
    
    // Boolean fields
    formData.append('has_certificate', courseData.has_certificate || false);
    formData.append('is_featured', courseData.is_featured || false);
    
    // JSON fields - convert arrays to JSON strings
    if (courseData.requirements && Array.isArray(courseData.requirements)) {
      formData.append('requirements', JSON.stringify(courseData.requirements));
    }
    
    if (courseData.skills && Array.isArray(courseData.skills)) {
      formData.append('skills', JSON.stringify(courseData.skills));
    }
    
    // File fields
    if (courseData.thumbnail) {
      formData.append('thumbnail', courseData.thumbnail);
    }
    
    // Handle modules if included
    if (courseData.modules && Array.isArray(courseData.modules)) {
      // For initial creation we don't send modules directly
      // They'll be created separately after course creation
      console.log('Modules will be created after course creation:', courseData.modules);
    }
    
    return handleRequest(
      async () => await apiClient.post('/instructor/courses/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      }),
      'Failed to create course'
    );
  },
  
  updateCourse: async (courseIdOrSlug, courseData) => {
    // Use FormData for file upload
    const formData = new FormData();
    
    // Basic fields
    if (courseData.title) formData.append('title', courseData.title);
    if (courseData.description) formData.append('description', courseData.description);
    if (courseData.category_id) formData.append('category_id', courseData.category_id);
    
    // Optional fields with null checks
    if (courseData.subtitle) formData.append('subtitle', courseData.subtitle);
    if (courseData.level) formData.append('level', courseData.level);
    if (courseData.price) formData.append('price', courseData.price);
    if (courseData.discount_price) formData.append('discount_price', courseData.discount_price);
    if (courseData.duration) formData.append('duration', courseData.duration);
    
    // Boolean fields
    if (courseData.has_certificate !== undefined) 
      formData.append('has_certificate', courseData.has_certificate);
    if (courseData.is_featured !== undefined) 
      formData.append('is_featured', courseData.is_featured);
    if (courseData.is_published !== undefined) 
      formData.append('is_published', courseData.is_published);
    
    // JSON fields - convert arrays to JSON strings
    if (courseData.requirements && Array.isArray(courseData.requirements)) {
      formData.append('requirements', JSON.stringify(courseData.requirements));
    }
    
    if (courseData.skills && Array.isArray(courseData.skills)) {
      formData.append('skills', JSON.stringify(courseData.skills));
    }
    
    // File fields - only append if it's a File object, not a string URL
    if (courseData.thumbnail && courseData.thumbnail instanceof File) {
      formData.append('thumbnail', courseData.thumbnail);
    }
    
    try {
      if (isSlug(courseIdOrSlug)) {
        // Use slug directly
        return handleRequest(
          async () => await apiClient.put(`/instructor/courses/${courseIdOrSlug}/`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          }),
          `Failed to update course ${courseIdOrSlug}`
        );
      } else {
        // First try to find the course by ID to get its slug
        const coursesResponse = await instructorService.getAllCourses();
        const course = coursesResponse.find(c => c.id?.toString() === courseIdOrSlug?.toString());
        
        if (course?.slug) {
          return handleRequest(
            async () => await apiClient.put(`/instructor/courses/${course.slug}/`, formData, {
              headers: { 'Content-Type': 'multipart/form-data' }
            }),
            `Failed to update course ${courseIdOrSlug}`
          );
        } else {
          throw new Error(`Course with ID ${courseIdOrSlug} not found`);
        }
      }
    } catch (error) {
      console.error(`Failed to update course: ${error.message}`);
      throw error;
    }
  },
  
  getCourseBySlug: async (slug) => {
    console.log(`Instructor service: Getting course with slug: ${slug}`);
    try {
      // First try instructor-specific endpoint
      return handleRequest(
        async () => {
          console.log(`Making instructor API request to: /instructor/courses/${slug}/`);
          return await apiClient.get(`/instructor/courses/${slug}/`);
        },
        `Failed to fetch course by slug: ${slug}`
      );
    } catch (error) {
      console.error(`Error fetching from instructor endpoint: ${error.message}`);
      
      // Fallback to regular course endpoint (this shouldn't normally be needed)
      try {
        console.log('Falling back to regular course endpoint');
        return handleRequest(
          async () => await apiClient.get(`/courses/${slug}/`),
          `Failed to fetch course by slug (fallback): ${slug}`
        );
      } catch (fallbackError) {
        console.error(`Fallback course endpoint also failed: ${fallbackError.message}`);
        throw error; // Throw the original error
      }
    }
  },
  
  // Module management
  getModules: async (courseId) => {
    return handleRequest(
      async () => await apiClient.get('/instructor/modules/', { params: { course: courseId } }),
      `Failed to fetch modules for course ${courseId}`
    );
  },
  
  getModule: async (moduleId) => {
    return handleRequest(
      async () => await apiClient.get(`/instructor/modules/${moduleId}/`),
      `Failed to fetch module ${moduleId}`
    );
  },
  
  createModule: async (moduleData) => {
    return handleRequest(
      async () => await apiClient.post('/instructor/modules/', moduleData),
      'Failed to create module'
    );
  },
  
  updateModule: async (moduleId, moduleData) => {
    return handleRequest(
      async () => await apiClient.put(`/instructor/modules/${moduleId}/`, moduleData),
      `Failed to update module ${moduleId}`
    );
  },
  
  // Lesson management (consistently using instructor endpoints)
  getLessons: async (moduleId) => {
    return handleRequest(
      async () => await apiClient.get('/instructor/lessons/', { params: { module: moduleId } }),
      `Failed to fetch lessons for module ${moduleId}`
    );
  },
  
  getLesson: async (lessonId) => {
    return handleRequest(
      async () => await apiClient.get(`/instructor/lessons/${lessonId}/`),
      `Failed to fetch lesson ${lessonId}`
    );
  },
  
  createLesson: async (moduleId, lessonData) => {
    // Support both implementation styles but always use the instructor endpoint
    if (moduleId && typeof moduleId === 'object') {
      // Called with just lessonData object
      lessonData = moduleId;
      return handleRequest(
        async () => await apiClient.post('/instructor/lessons/', lessonData),
        'Failed to create lesson'
      );
    } else {
      // Called with moduleId and lessonData
      // Ensure module_id is included in the data
      const completeData = {
        ...lessonData,
        module: moduleId
      };
      return handleRequest(
        async () => await apiClient.post('/instructor/lessons/', completeData),
        'Failed to create lesson'
      );
    }
  },
  
  updateLesson: async (lessonId, lessonData) => {
    return handleRequest(
      async () => await apiClient.put(`/instructor/lessons/${lessonId}/`, lessonData),
      `Failed to update lesson ${lessonId}`
    );
  },
  
  // Resource management
  getResources: async (lessonId) => {
    return handleRequest(
      async () => await apiClient.get('/instructor/resources/', { params: { lesson: lessonId } }),
      `Failed to fetch resources for lesson ${lessonId}`
    );
  },
  
  getInstructorLessons: async () => {
    return handleRequest(
      async () => await apiClient.get('/instructor/lessons/'),
      'Failed to fetch instructor lessons'
    );
  },

  getInstructorStatistics: async () => {
    return handleRequest(
      async () => await apiClient.get('/statistics/instructor/'),
      'Failed to fetch instructor statistics'
    );
  },
  
  // Course deletion
  deleteCourse: async (courseIdOrSlug) => {
    if (!courseIdOrSlug) {
      console.error("Course ID or slug is required for deletion");
      return Promise.reject({
        message: "Course ID or slug is required for deletion"
      });
    }
    
    try {
      console.log(`Attempting to delete course: ${courseIdOrSlug}`);
      
      // If it's a slug, use it directly
      if (isSlug(courseIdOrSlug)) {
        return handleRequest(
          async () => await apiClient.delete(`/instructor/courses/${courseIdOrSlug}/`),
          `Failed to delete course ${courseIdOrSlug}`
        );
      }
      
      // If it's an ID, try to find the corresponding slug
      const coursesResponse = await instructorService.getAllCourses();
      const course = coursesResponse.find(c => c.id?.toString() === courseIdOrSlug?.toString());
      
      if (course?.slug) {
        return handleRequest(
          async () => await apiClient.delete(`/instructor/courses/${course.slug}/`),
          `Failed to delete course ${courseIdOrSlug}`
        );
      } else {
        throw new Error(`Course with ID ${courseIdOrSlug} not found`);
      }
    } catch (error) {
      console.error(`Course deletion failed: ${error.message}`);
      throw error;
    }
  },

  // Course publishing
  publishCourse: async (slug, shouldPublish = true) => {
    return handleRequest(
      async () => await apiClient.put(`/instructor/courses/${slug}/publish/`, { publish: shouldPublish }),
      `Failed to ${shouldPublish ? 'publish' : 'unpublish'} course`
    );
  }
};

export default instructorService;
// END OF CODE