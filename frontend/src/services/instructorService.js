/**
 * File: frontend/src/services/instructorService.js
 * Purpose: Instructor API Services for Educational Platform
 * 
 * This module provides specialized API services for instructor operations,
 * including course, module, lesson and assessment management.
 * 
 * Features:
 * - Complete lesson CRUD operations
 * - Module management
 * - Course management for instructors
 * - Resource and assessment creation
 * 
 * Backend Connection Points:
 * - POST /api/instructor/lessons/ - Create new lessons
 * - PUT /api/instructor/lessons/{id}/ - Update lessons
 * - GET /api/instructor/lessons/ - Get instructor lessons
 * - POST /api/instructor/resources/ - Add resources to lessons
 * - POST /api/instructor/assessments/ - Create assessments
 * 
 * @author nanthiniSanthanam
 * @version 1.0
 * @date 2025-05-03
 */

import axios from 'axios';

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
 * Automatically adds the authentication token to all outgoing requests if available
 */
apiClient.interceptors.request.use(
  config => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
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
    return response;
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
 * Comprehensive instructor service API
 * Combines both implementations from api.js into a single consistent API
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
    return handleRequest(
      async () => await apiClient.get(`/instructor/courses/${courseId}/`),
      `Failed to fetch course ${courseId}`
    );
  },
  
  createCourse: async (courseData) => {
    return handleRequest(
      async () => await apiClient.post('/instructor/courses/', courseData),
      'Failed to create course'
    );
  },
  
  updateCourse: async (courseId, courseData) => {
    return handleRequest(
      async () => await apiClient.put(`/instructor/courses/${courseId}/`, courseData),
      `Failed to update course ${courseId}`
    );
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
  
  // Lesson management (combining both implementations)
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
    // Support both implementation styles
    if (moduleId && typeof moduleId === 'object') {
      // Called with just lessonData object
      lessonData = moduleId;
      return handleRequest(
        async () => await apiClient.post('/instructor/lessons/', lessonData),
        'Failed to create lesson'
      );
    } else {
      // Called with moduleId and lessonData
      return handleRequest(
        async () => await apiClient.post(`/modules/${moduleId}/lessons/`, lessonData),
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
  
  addLessonResource: async (lessonId, formData) => {
    return handleRequest(
      async () => await apiClient.post(`/lessons/${lessonId}/resources/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }),
      'Failed to add resource'
    );
  },
  
  createResource: async (resourceData) => {
    // Handle FormData for file uploads
    const headers = resourceData instanceof FormData ? 
      { 'Content-Type': 'multipart/form-data' } : {};
    
    return handleRequest(
      async () => await apiClient.post('/instructor/resources/', resourceData, { headers }),
      'Failed to create resource'
    );
  },
  
  // Assessment management (combining both implementations)
  getAssessment: async (lessonId) => {
    return handleRequest(
      async () => await apiClient.get('/instructor/assessments/', { params: { lesson: lessonId } }),
      `Failed to fetch assessment for lesson ${lessonId}`
    );
  },
  
  createAssessment: async (lessonId, assessmentData) => {
    // Support both implementation styles
    if (lessonId && typeof lessonId === 'object') {
      // Called with just assessmentData object
      assessmentData = lessonId;
      return handleRequest(
        async () => await apiClient.post('/instructor/assessments/', assessmentData),
        'Failed to create assessment'
      );
    } else {
      // Called with lessonId and assessmentData
      return handleRequest(
        async () => await apiClient.post(`/lessons/${lessonId}/assessment/`, assessmentData),
        'Failed to create assessment'
      );
    }
  },
  
  addAssessmentQuestion: async (assessmentId, questionData) => {
    return handleRequest(
      async () => await apiClient.post(`/instructor/assessments/${assessmentId}/add_question/`, questionData),
      'Failed to add question to assessment'
    );
  },
  
  // Instructor dashboard analytics
  getInstructorStatistics: async () => {
    return handleRequest(
      async () => await apiClient.get('/instructor/statistics/'),
      'Failed to fetch instructor statistics'
    );
  },
  
  getInstructorLessons: async () => {
    return handleRequest(
      async () => await apiClient.get('/instructor/lessons/'),
      'Failed to fetch instructor lessons'
    );
  }
};

export default instructorService;