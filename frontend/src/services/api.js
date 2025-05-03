/**
 * File: frontend/src/services/api.js
 * Purpose: API Service for Educational Platform with JWT Authentication and Tiered Access
 * 
 * This revised module provides the API services for the Educational Platform,
 * with corrected endpoints that exactly match the backend URL structure.
 * 
 * Key Changes:
 * 1. Fixed all endpoint paths to match the backend structure
 * 2. Changed '/users/' to '/user/' to match backend convention
 * 3. Removed duplicate '/api' prefixes from endpoint paths
 * 4. Updated authentication endpoints to match JWT endpoints
 * 5. Ensured consistent use of 'accessToken' instead of 'token'
 * 6. Added notes for endpoints that may need backend implementation
 * 
 * Backend Connection Points (Verified):
 * - POST /api/token/ - Get JWT tokens with email/password
 * - POST /api/token/refresh/ - Refresh JWT token
 * - POST /api/user/register/ - Register new user
 * - GET /api/user/me/ - Get current user profile
 * - GET /api/courses/ - Get all courses
 * - GET /api/categories/ - Get all categories
 * 
 * @author nanthiniSanthanam (original)
 * @author cadsanthanam (revised 2025-04-29)
 * @version 3.1
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
 * Response interceptor for token refresh or logout
 * Handles 401 Unauthorized errors by attempting to refresh the token
 * If refresh fails, logs the user out and redirects to login page
 */
apiClient.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    
    // If error is 401 and not already trying to refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Try to refresh the token
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }
        
        // Use the correct endpoint for token refresh
        const response = await axios.post(
          `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'}/token/refresh/`,
          { refresh: refreshToken }
        );
        
        // Store the new access token
        localStorage.setItem('accessToken', response.data.access);
        
        // Update the original request and retry
        originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // If refresh fails, logout user
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
        
        // Redirect to login page
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    // Handle specific error status codes
    if (error.response?.status === 403) {
      console.error('Permission denied:', originalRequest.url);
      // If it's a permission issue, might be due to role restrictions
    } else if (error.response?.status === 404) {
      console.error('Resource not found:', originalRequest.url);
    } else if (error.response?.status === 500) {
      console.error('Server error:', error.response?.data);
    }
    
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
 * Authentication and user management services
 * Handles login, registration, token management, and user profile operations
 */
export const authService = {
  /**
   * Authenticates a user and stores JWT tokens
   * @param {Object} credentials - User credentials (email, password, rememberMe)
   * @returns {Promise} - User authentication data including tokens
   */
  login: async (credentials) => {
    return handleRequest(
      async () => {
        const { email, password, rememberMe } = credentials;
        // Use correct endpoint: /api/token/ -> /token/
        const response = await apiClient.post('/token/', { email, password });
        
        // Store tokens
        localStorage.setItem('accessToken', response.data.access);
        localStorage.setItem('refreshToken', response.data.refresh);
        
        // If remember me is false, set tokens to expire when browser closes
        if (!rememberMe) {
          // Using sessionStorage would be more ideal, but we need to maintain API compatibility
          // Instead, we set a flag to check on app initialization
          localStorage.setItem('tokenPersistence', 'session');
        } else {
          localStorage.setItem('tokenPersistence', 'permanent');
        }
        
        return response.data;
      },
      'Login failed'
    );
  },
  
  /**   * Registers a new user
   * @param {Object} userData - User registration data
   * @returns {Promise} - New user data
   */
  register: async (userData) => {
    // Transform camelCase field names to snake_case if needed
    const transformedData = {
      ...(userData.firstName && { first_name: userData.firstName }),
      ...(userData.lastName && { last_name: userData.lastName }),
      ...(userData.email && { email: userData.email }),
      ...(userData.username && { username: userData.username }),
      ...(userData.password && { password: userData.password }),
      ...(userData.role && { role: userData.role }),
      ...userData, // Include other fields that might not need transformation
    };
    
    // Updated to use correct path: /api/user/register/ -> /user/register/
    return handleRequest(
      async () => await apiClient.post('/user/register/', transformedData),
      'Registration failed'
    );
  },
  
/**
 * Resends verification email to user added on 29.04.2025
 * @param {String|Object} emailData - Email address or object with email property
 * @returns {Promise} - Resend result
 */
resendVerification: async (emailData) => {
  const payload = typeof emailData === 'string' 
    ? { email: emailData }
    : emailData;
    
  // Use correct path: /api/user/email/verify/resend/ -> /user/email/verify/resend/
  return handleRequest(
    async () => await apiClient.post('/user/email/verify/resend/', payload),
    'Failed to resend verification email'
  );
},


  /**
   * Verifies a user's email address
   * @param {String} token - Email verification token
   * @returns {Promise} - Verification result
   */
  verifyEmail: async (token) => {
    // Updated to use correct path: /api/user/email/verify/ -> /user/email/verify/
    return handleRequest(
      async () => await apiClient.post('/user/email/verify/', { token }),
      'Email verification failed'
    );
  },
  
  /**
   * Logs out the current user by removing stored tokens
   */
  logout: () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    localStorage.removeItem('tokenPersistence');
  },
  
  /**
   * Retrieves the current user's profile information
   * @returns {Promise} - Current user data
   */
  getCurrentUser: async () => {
    // Updated to use correct path: /api/user/me/ -> /user/me/
    return handleRequest(
      async () => await apiClient.get('/user/me/'),
      'Failed to retrieve user data'
    );
  },
  
  /**
   * Updates the current user's profile information
   * @param {Object} userData - User data to update
   * @returns {Promise} - Updated user data
   */
  updateProfile: async (userData) => {
    // Transform camelCase field names to snake_case if needed
    const transformedData = {
      ...(userData.firstName && { first_name: userData.firstName }),
      ...(userData.lastName && { last_name: userData.lastName }),
      ...userData, // Include other fields that might not need transformation
    };
    
    // Updated to use correct path: /api/user/me/ -> /user/me/
    return handleRequest(
      async () => await apiClient.put('/user/me/', transformedData),
      'Failed to update profile'
    );
  },
  
  /**
   * Changes the user's password
   * @param {Object} passwordData - Old and new password
   * @returns {Promise} - Change password result
   */
  changePassword: async (passwordData) => {
    const transformedData = {
      old_password: passwordData.oldPassword,
      new_password: passwordData.newPassword
    };
    
    // Updated to use correct path: /api/user/password/change/ -> /user/password/change/
    return handleRequest(
      async () => await apiClient.post('/user/password/change/', transformedData),
      'Failed to change password'
    );
  },
  
  /**
   * Requests a password reset email
   * @param {String|Object} emailData - Email address or object with email property
   * @returns {Promise} - Request result
   */
  requestPasswordReset: async (emailData) => {
    const payload = typeof emailData === 'string' 
      ? { email: emailData }
      : emailData;
      
    // Updated to use correct path: /api/user/password/reset/ -> /user/password/reset/
    return handleRequest(
      async () => await apiClient.post('/user/password/reset/', payload),
      'Failed to request password reset'
    );
  },
  
  /**
   * Resets password with token
   * @param {String} token - Password reset token
   * @param {String|Object} password - New password or object with password property
   * @returns {Promise} - Reset result
   */
  resetPassword: async (token, password) => {
    const payload = {
      token,
      password: typeof password === 'string' ? password : password.password
    };
    
    // Updated to use correct path: /api/user/password/reset/confirm/ -> /user/password/reset/confirm/
    return handleRequest(
      async () => await apiClient.post('/user/password/reset/confirm/', payload),
      'Failed to reset password'
    );
  },
  
  /**
   * Refreshes the access token using the refresh token
   * @returns {Promise} - New access token
   */
  refreshToken: async () => {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    
    // Updated to use correct path: /api/token/refresh/ -> /token/refresh/
    return handleRequest(
      async () => {
        const response = await apiClient.post('/token/refresh/', { refresh: refreshToken });
        localStorage.setItem('accessToken', response.data.access);
        return response;
      },
      'Failed to refresh token'
    );
  },
  
  /**
   * Checks if the user is authenticated based on stored token
   * @returns {Boolean} - Authentication status
   */
  isAuthenticated: () => {
    return !!localStorage.getItem('accessToken');
  }
};

/**
 * Subscription-related services
 * Handles operations for user subscription management and tiered access
 * NOTE: Some endpoints may need to be implemented on the backend
 */
export const subscriptionService = {
  /**
   * Retrieves the current user's subscription
   * @returns {Promise} - Current subscription details
   */
  getCurrentSubscription: async () => {
    // This endpoint may need to be verified or implemented on the backend
    return handleRequest(
      async () => await apiClient.get('/user/sessions/'), // This is a placeholder, update with actual endpoint
      'Failed to retrieve subscription information'
    );
  },
  
  /**
   * Upgrades user to a paid subscription tier
   * @param {String} tier - Subscription tier (basic, premium)
   * @param {Object} paymentData - Payment details
   * @returns {Promise} - Updated subscription details
   */
  upgradeSubscription: async (tier, paymentData = {}) => {
    // This endpoint may need to be verified or implemented on the backend
    return handleRequest(
      async () => await apiClient.post('/user/subscription/upgrade/', {
        tier,
        payment_method: paymentData.paymentMethod || 'credit_card',
        auto_renew: paymentData.autoRenew !== false
      }),
      'Failed to upgrade subscription'
    );
  },
  
  /**
   * Cancels the current paid subscription
   * @returns {Promise} - Updated subscription details
   */
  cancelSubscription: async () => {
    // This endpoint may need to be verified or implemented on the backend
    return handleRequest(
      async () => await apiClient.post('/user/subscription/cancel/'),
      'Failed to cancel subscription'
    );
  },
  
  /**
   * Downgrades to a lower subscription tier at the end of the current billing period
   * @param {String} tier - Target tier to downgrade to
   * @returns {Promise} - Updated subscription details
   */
  downgradeSubscription: async (tier = 'free') => {
    // This endpoint may need to be verified or implemented on the backend
    return handleRequest(
      async () => await apiClient.post('/user/subscription/downgrade/', { tier }),
      'Failed to downgrade subscription'
    );
  }
};

/**
 * Course-related services
 * Handles operations for courses, modules, lessons, enrollments, and reviews
 */
export const courseService = {
  /**
   * Retrieves all courses with optional filtering
   * @param {Object} params - Query parameters for filtering and pagination
   * @returns {Promise} - List of courses
   */
  getAllCourses: async (params = {}) => {
    // Correct path: /api/courses/ -> /courses/
    return handleRequest(
      async () => await apiClient.get('/courses/', { params }),
      'Failed to fetch courses'
    );
  },
  
  /**
   * Retrieves a course by its slug
   * @param {String} slug - Course slug
   * @returns {Promise} - Course details
   */
  getCourseBySlug: async (slug) => {
    // Correct path: /api/courses/<slug>/ -> /courses/<slug>/
    return handleRequest(
      async () => await apiClient.get(`/courses/${slug}/`),
      `Failed to fetch course ${slug}`
    );
  },
  
  /**
   * Enrolls the current user in a course
   * @param {String} slug - Course slug
   * @returns {Promise} - Enrollment details
   */
  enrollInCourse: async (slug) => {
    // Correct path: /api/courses/<slug>/enroll/ -> /courses/<slug>/enroll/
    return handleRequest(
      async () => await apiClient.post(`/courses/${slug}/enroll/`),
      `Failed to enroll in course ${slug}`
    );
  },
  
  /**
   * Retrieves all modules for a specific course
   * @param {String} slug - Course slug
   * @returns {Promise} - List of modules
   */
  getCourseModules: async (slug) => {
    // Correct path: /api/courses/<slug>/modules/ -> /courses/<slug>/modules/
    return handleRequest(
      async () => await apiClient.get(`/courses/${slug}/modules/`),
      `Failed to fetch modules for course ${slug}`
    );
  },
  
  /**
   * Retrieves details for a specific module
   * @param {Number|String} moduleId - Module ID
   * @returns {Promise} - Module details including lessons
   */
  getModuleDetails: async (moduleId) => {
    // Correct path: /api/modules/<pk>/ -> /modules/<moduleId>/
    return handleRequest(
      async () => await apiClient.get(`/modules/${moduleId}/`),
      `Failed to fetch module details for module ${moduleId}`
    );
  },
  
  /**
   * Retrieves all lessons for a specific module
   * @param {Number|String} moduleId - Module ID
   * @returns {Promise} - List of lessons
   */
  getModuleLessons: async (moduleId) => {
    // Correct path: /api/modules/<pk>/lessons/ -> /modules/<moduleId>/lessons/
    return handleRequest(
      async () => await apiClient.get(`/modules/${moduleId}/lessons/`),
      `Failed to fetch lessons for module ${moduleId}`
    );
  },
  
  /**
   * Retrieves details for a specific lesson
   * @param {Number|String} lessonId - Lesson ID
   * @returns {Promise} - Lesson details including content and resources
   */
  getLessonDetails: async (lessonId) => {
    // Correct path: /api/lessons/<pk>/ -> /lessons/<lessonId>/
    return handleRequest(
      async () => await apiClient.get(`/lessons/${lessonId}/`),
      `Failed to fetch lesson details for lesson ${lessonId}`
    );
  },
  
  /**
   * Marks a lesson as completed
   * @param {Number|String} lessonId - Lesson ID
   * @param {Number} timeSpent - Time spent on lesson in seconds
   * @returns {Promise} - Updated lesson progress
   */
  completeLesson: async (lessonId, timeSpent = 0) => {
    // This endpoint may need verification - not directly visible in URL list
    return handleRequest(
      async () => await apiClient.put(`/lessons/${lessonId}/complete/`, { time_spent: timeSpent }),
      `Failed to mark lesson ${lessonId} as complete`
    );
  },
  
  /**
   * Retrieves all reviews for a specific course
   * @param {String} slug - Course slug
   * @returns {Promise} - List of reviews
   */
  getCourseReviews: async (slug) => {
    // Correct path: /api/courses/<slug>/reviews/ -> /courses/<slug>/reviews/
    return handleRequest(
      async () => await apiClient.get(`/courses/${slug}/reviews/`),
      `Failed to fetch reviews for course ${slug}`
    );
  },
  
  /**
   * Adds a review for a specific course
   * @param {String} slug - Course slug
   * @param {Object} reviewData - Review data including rating and content
   * @returns {Promise} - Created review
   */
  addCourseReview: async (slug, reviewData) => {
    // Correct path: /api/courses/<slug>/review/ -> /courses/<slug>/review/
    return handleRequest(
      async () => await apiClient.post(`/courses/${slug}/review/`, reviewData),
      `Failed to add review for course ${slug}`
    );
  },
  
  /**
   * Updates a course review
   * @param {String} slug - Course slug
   * @param {Number|String} reviewId - Review ID
   * @param {Object} reviewData - Updated review data
   * @returns {Promise} - Updated review
   */
  updateCourseReview: async (slug, reviewId, reviewData) => {
    // This endpoint may need verification - not directly visible in URL list
    return handleRequest(
      async () => await apiClient.put(`/courses/${slug}/review/${reviewId}/`, reviewData),
      `Failed to update review ${reviewId}`
    );
  },
  
  /**
   * Deletes a course review
   * @param {String} slug - Course slug
   * @param {Number|String} reviewId - Review ID
   * @returns {Promise} - Deletion result
   */
  deleteCourseReview: async (slug, reviewId) => {
    // This endpoint may need verification - not directly visible in URL list
    return handleRequest(
      async () => await apiClient.delete(`/courses/${slug}/review/${reviewId}/`),
      `Failed to delete review ${reviewId}`
    );
  },
  
  /**
   * Searches courses by keyword
   * @param {String} query - Search query
   * @returns {Promise} - Search results
   */
  searchCourses: async (query) => {
    // This endpoint may need verification - not directly visible in URL list
    return handleRequest(
      async () => await apiClient.get('/courses/', { params: { q: query } }),
      'Course search failed'
    );
  },
  
  /**
   * Retrieves featured courses
   * @param {Number} limit - Number of courses to retrieve
   * @returns {Promise} - List of featured courses
   */
  getFeaturedCourses: async (limit = 3) => {
    // Uses course list endpoint with filter parameter
    return handleRequest(
      async () => await apiClient.get('/courses/', { params: { is_featured: true, limit } }),
      'Failed to fetch featured courses'
    );
  }
};

/**
 * Assessment-related services
 * Handles operations for assessments, attempts, and submissions
 * NOTE: Some endpoints may need to be implemented or verified on the backend
 */
export const assessmentService = {
  /**
   * Retrieves details for a specific assessment
   * @param {Number|String} assessmentId - Assessment ID
   * @returns {Promise} - Assessment details including questions
   */
  getAssessmentDetails: async (assessmentId) => {
    // Endpoint path may need verification
    return handleRequest(
      async () => await apiClient.get(`/assessments/${assessmentId}/`),
      `Failed to fetch assessment ${assessmentId}`
    );
  },
  
  /**
   * Starts a new assessment attempt
   * @param {Number|String} assessmentId - Assessment ID
   * @returns {Promise} - New assessment attempt details
   */
  startAssessment: async (assessmentId) => {
    // Endpoint path may need verification
    return handleRequest(
      async () => await apiClient.post(`/assessments/${assessmentId}/start/`),
      `Failed to start assessment ${assessmentId}`
    );
  },
  
  /**
   * Submits answers for an assessment attempt
   * @param {Number|String} attemptId - Assessment attempt ID
   * @param {Array} answers - List of answers
   * @returns {Promise} - Assessment results
   */
  submitAssessment: async (attemptId, answers) => {
    // Endpoint path may need verification
    return handleRequest(
      async () => await apiClient.put(`/assessment-attempts/${attemptId}/submit/`, { answers }),
      `Failed to submit assessment attempt ${attemptId}`
    );
  },
  
  /**
   * Retrieves all assessment attempts for the current user
   * @returns {Promise} - List of assessment attempts
   */
  getUserAssessmentAttempts: async () => {
    // Endpoint path may need verification
    return handleRequest(
      async () => await apiClient.get('/user/assessment-attempts/'),
      'Failed to fetch assessment attempts'
    );
  },
  
  /**
   * Retrieves details for a specific assessment attempt
   * @param {Number|String} attemptId - Assessment attempt ID
   * @returns {Promise} - Assessment attempt details
   */
  getAssessmentAttempt: async (attemptId) => {
    // Endpoint path may need verification
    return handleRequest(
      async () => await apiClient.get(`/assessment-attempts/${attemptId}/`),
      `Failed to fetch assessment attempt ${attemptId}`
    );
  },
  
  /**
   * Gets assessment questions for practice
   * @param {Number|String} lessonId - Lesson ID
   * @returns {Promise} - Practice questions
   */
  getPracticeQuestions: async (lessonId) => {
    // Endpoint path may need verification
    return handleRequest(
      async () => await apiClient.get(`/lessons/${lessonId}/practice/`),
      `Failed to fetch practice questions for lesson ${lessonId}`
    );
  }
};

/**
 * User progress-related services
 * Handles operations for tracking user progress through courses
 * NOTE: Some endpoints may need to be implemented or verified on the backend
 */
export const progressService = {
  /**
   * Retrieves all enrollments for the current user
   * @returns {Promise} - List of enrollments
   */
  getUserEnrollments: async () => {
    // This endpoint exists in URL listings: /api/enrollments/ -> /enrollments/
    return handleRequest(
      async () => await apiClient.get('/enrollments/'),
      'Failed to fetch enrollments'
    );
  },
  
  /**
   * Retrieves progress for a specific course
   * @param {Number|String} courseId - Course ID or slug
   * @returns {Promise} - Course progress details
   */
  getUserProgress: async (courseId) => {
    // Endpoint path may need verification
    return handleRequest(
      async () => await apiClient.get(`/user/progress/${courseId}/`),
      `Failed to fetch progress for course ${courseId}`
    );
  },
  
  /**
   * Retrieves overall user progress statistics
   * @returns {Promise} - Progress statistics
   */
  getUserProgressStats: async () => {
    // Endpoint path may need verification
    return handleRequest(
      async () => await apiClient.get('/user/progress/stats/'),
      'Failed to fetch progress statistics'
    );
  },
  
  /**
   * Updates user's last activity timestamp
   * @param {Number|String} courseId - Course ID
   * @returns {Promise} - Updated activity record
   */
  updateLastActivity: async (courseId) => {
    // Endpoint path may need verification
    return handleRequest(
      async () => await apiClient.post(`/user/activity/${courseId}/`),
      `Failed to update activity for course ${courseId}`
    );
  },
  
  /**
   * Retrieves learning recommendations for the user
   * @returns {Promise} - Personalized recommendations
   */
  getLearningRecommendations: async () => {
    // Endpoint path may need verification
    return handleRequest(
      async () => await apiClient.get('/user/recommendations/'),
      'Failed to fetch learning recommendations'
    );
  }
};

/**
 * Notes-related services
 * Handles operations for user notes associated with lessons
 * NOTE: Endpoint may need to be implemented or verified on the backend
 */
export const noteService = {
  /**
   * Retrieves all notes for the current user
   * @returns {Promise} - List of notes
   */
  getUserNotes: async () => {
    // Endpoint path may need verification
    return handleRequest(
      async () => await apiClient.get('/notes/'),
      'Failed to fetch notes'
    );
  },
  
  /**
   * Retrieves notes for a specific lesson
   * @param {Number|String} lessonId - Lesson ID
   * @returns {Promise} - List of notes for the lesson
   */
  getNotesForLesson: async (lessonId) => {
    // Endpoint path may need verification
    return handleRequest(
      async () => await apiClient.get('/notes/', { params: { lesson: lessonId } }),
      `Failed to fetch notes for lesson ${lessonId}`
    );
  },
  
  /**
   * Creates a new note
   * @param {Object} noteData - Note data including lesson ID and content
   * @returns {Promise} - Created note
   */
  createNote: async (noteData) => {
    // Endpoint path may need verification
    return handleRequest(
      async () => await apiClient.post('/notes/', noteData),
      'Failed to create note'
    );
  },
  
  /**
   * Updates an existing note
   * @param {Number|String} noteId - Note ID
   * @param {Object} noteData - Updated note data
   * @returns {Promise} - Updated note
   */
  updateNote: async (noteId, noteData) => {
    // Endpoint path may need verification
    return handleRequest(
      async () => await apiClient.put(`/notes/${noteId}/`, noteData),
      `Failed to update note ${noteId}`
    );
  },
  
  /**
   * Deletes a note
   * @param {Number|String} noteId - Note ID
   * @returns {Promise} - Deletion result
   */
  deleteNote: async (noteId) => {
    // Endpoint path may need verification
    return handleRequest(
      async () => await apiClient.delete(`/notes/${noteId}/`),
      `Failed to delete note ${noteId}`
    );
  }
};

/**
 * Forum and discussion-related services
 * Handles operations for course discussions, questions, and answers
 * NOTE: These endpoints may need to be implemented on the backend
 */
export const forumService = {
  /**
   * Retrieves all discussions for a course
   * @param {String} courseSlug - Course slug
   * @returns {Promise} - List of discussions
   */
  getCourseDiscussions: async (courseSlug) => {
    // Endpoint path may need verification or implementation
    return handleRequest(
      async () => await apiClient.get(`/courses/${courseSlug}/discussions/`),
      `Failed to fetch discussions for course ${courseSlug}`
    );
  },
  
  /**
   * Retrieves a specific discussion
   * @param {String} courseSlug - Course slug
   * @param {Number|String} discussionId - Discussion ID
   * @returns {Promise} - Discussion details
   */
  getDiscussion: async (courseSlug, discussionId) => {
    // Endpoint path may need verification or implementation
    return handleRequest(
      async () => await apiClient.get(`/courses/${courseSlug}/discussions/${discussionId}/`),
      `Failed to fetch discussion ${discussionId}`
    );
  },
  
  /**
   * Creates a new discussion
   * @param {String} courseSlug - Course slug
   * @param {Object} discussionData - Discussion data
   * @returns {Promise} - Created discussion
   */
  createDiscussion: async (courseSlug, discussionData) => {
    // Endpoint path may need verification or implementation
    return handleRequest(
      async () => await apiClient.post(`/courses/${courseSlug}/discussions/`, discussionData),
      'Failed to create discussion'
    );
  },
  
  /**
   * Adds a reply to a discussion
   * @param {String} courseSlug - Course slug
   * @param {Number|String} discussionId - Discussion ID
   * @param {Object} replyData - Reply data
   * @returns {Promise} - Created reply
   */
  addDiscussionReply: async (courseSlug, discussionId, replyData) => {
    // Endpoint path may need verification or implementation
    return handleRequest(
      async () => await apiClient.post(`/courses/${courseSlug}/discussions/${discussionId}/replies/`, replyData),
      `Failed to add reply to discussion ${discussionId}`
    );
  }
};

/**
 * Virtual lab-related services
 * Handles operations for interactive lab exercises
 * NOTE: These endpoints may need to be implemented on the backend
 */
export const virtualLabService = {
  /**
   * Retrieves details for a specific lab
   * @param {Number|String} labId - Lab ID or lesson ID with lab
   * @returns {Promise} - Lab details
   */
  getLabDetails: async (labId) => {
    // Endpoint path may need verification or implementation
    return handleRequest(
      async () => await apiClient.get(`/labs/${labId}/`),
      `Failed to fetch lab ${labId}`
    );
  },
  
  /**
   * Starts a lab session
   * @param {Number|String} labId - Lab ID
   * @returns {Promise} - Lab session details
   */
  startLabSession: async (labId) => {
    // Endpoint path may need verification or implementation
    return handleRequest(
      async () => await apiClient.post(`/labs/${labId}/start/`),
      `Failed to start lab ${labId}`
    );
  },
  
  /**
   * Submits a lab solution
   * @param {Number|String} labId - Lab ID
   * @param {Object} solutionData - Solution data
   * @returns {Promise} - Evaluation result
   */
  submitLabSolution: async (labId, solutionData) => {
    // Endpoint path may need verification or implementation
    return handleRequest(
      async () => await apiClient.post(`/labs/${labId}/submit/`, solutionData),
      `Failed to submit solution for lab ${labId}`
    );
  },
  
  /**
   * Retrieves lab progress history
   * @param {Number|String} labId - Lab ID
   * @returns {Promise} - Lab progress history
   */
  getLabProgress: async (labId) => {
    // Endpoint path may need verification or implementation
    return handleRequest(
      async () => await apiClient.get(`/labs/${labId}/progress/`),
      `Failed to fetch progress for lab ${labId}`
    );
  }
};

/**
 * Category-related services
 * Handles operations for course categories
 */
export const categoryService = {
  /**
   * Retrieves all categories
   * @returns {Promise} - List of categories
   */
  getAllCategories: async () => {
    // Correct path: /api/categories/ -> /categories/
    return handleRequest(
      async () => await apiClient.get('/categories/'),
      'Failed to fetch categories'
    );
  },
  
  /**
   * Retrieves courses for a specific category
   * @param {String} categorySlug - Category slug
   * @returns {Promise} - List of courses in the category
   */
  getCoursesByCategory: async (categorySlug) => {
    // Endpoint path may need verification
    return handleRequest(
      async () => await apiClient.get(`/categories/${categorySlug}/courses/`),
      `Failed to fetch courses for category ${categorySlug}`
    );
  }
};

/**
 * System-related services
 * Handles operations for system status, database, and admin operations
 */
export const systemService = {
  /**
   * Checks database connection status
   * @returns {Promise} - Database status information
   */
  checkDbStatus: async () => {
    // Correct path: /api/system/db-status/ -> /system/db-status/
    return handleRequest(
      async () => await apiClient.get('/system/db-status/'),
      'Database status check failed'
    );
  },
  
  /**
   * Retrieves database statistics
   * @returns {Promise} - Database statistics
   */
  getDbStats: async () => {
    // Correct path: /api/system/db-stats/ -> /system/db-stats/
    return handleRequest(
      async () => await apiClient.get('/system/db-stats/'),
      'Failed to get database statistics'
    );
  },
  
  /**
   * Retrieves system health information
   * @returns {Promise} - System health data
   */
  getSystemHealth: async () => {
    // Endpoint path may need verification
    return handleRequest(
      async () => await apiClient.get('/system/health/'),
      'Failed to get system health information'
    );
  }
};

/**
 * Certificate-related services
 * Handles operations for course completion certificates
 * NOTE: Some endpoints may need to be implemented on the backend
 */
export const certificateService = {
  /**
   * Retrieves all certificates for the current user
   * @returns {Promise} - List of certificates
   */
  getUserCertificates: async () => {
    // Endpoint path may need verification
    return handleRequest(
      async () => await apiClient.get('/certificates/'),
      'Failed to fetch certificates'
    );
  },
  
  /**
   * Generates a certificate for a completed course
   * @param {String} courseSlug - Course slug
   * @returns {Promise} - Certificate details
   */
  generateCertificate: async (courseSlug) => {
    // Endpoint path may need verification
    return handleRequest(
      async () => await apiClient.post(`/courses/${courseSlug}/certificate/`),
      `Failed to generate certificate for course ${courseSlug}`
    );
  },
  
  /**
   * Retrieves a specific certificate
   * @param {Number|String} certificateId - Certificate ID
   * @returns {Promise} - Certificate details
   */
  getCertificate: async (certificateId) => {
    // Endpoint path may need verification
    return handleRequest(
      async () => await apiClient.get(`/certificates/${certificateId}/`),
      `Failed to fetch certificate ${certificateId}`
    );
  },
  
  /**
   * Verifies a certificate by its verification code
   * @param {String} verificationCode - Certificate verification code
   * @returns {Promise} - Verification result
   */
  verifyCertificate: async (verificationCode) => {
    // Endpoint path may need verification
    return handleRequest(
      async () => await apiClient.get(`/certificates/verify/${verificationCode}/`),
      'Certificate verification failed'
    );
  }
};

// Blog services
export const blogService = {
  /**
   * Get latest blog posts
   * @param {Number} limit - Number of posts to retrieve
   * @returns {Promise} - List of blog posts
   */
  getLatestPosts: async (limit = 3) => {
    // Endpoint path may need verification or implementation
    return handleRequest(
      async () => await apiClient.get('/blog/posts/', { params: { limit } }),
      'Failed to fetch latest blog posts'
    );
  },
  
  /**
   * Get blog post by slug
   * @param {String} slug - Blog post slug
   * @returns {Promise} - Blog post details
   */
  getPostBySlug: async (slug) => {
    // Endpoint path may need verification or implementation
    return handleRequest(
      async () => await apiClient.get(`/blog/posts/${slug}/`),
      `Failed to fetch blog post ${slug}`
    );
  },
  
  /**
   * Get blog posts by category
   * @param {String} category - Category slug
   * @param {Object} params - Query parameters
   * @returns {Promise} - List of blog posts in category
   */
  getPostsByCategory: async (category, params = {}) => {
    // Endpoint path may need verification or implementation
    return handleRequest(
      async () => await apiClient.get(`/blog/categories/${category}/posts/`, { params }),
      `Failed to fetch posts in category ${category}`
    );
  }
};

// Testimonial services
export const testimonialService = {
  /**
   * Get featured testimonials
   * @param {Number} limit - Number of testimonials to retrieve
   * @returns {Promise} - List of testimonials
   */
  getFeaturedTestimonials: async (limit = 3) => {
    // Endpoint path may need verification or implementation
    return handleRequest(
      async () => await apiClient.get('/testimonials/featured/', { params: { limit } }),
      'Failed to fetch featured testimonials'
    );
  },
  
  /**
   * Get testimonials for a specific course
   * @param {String} courseSlug - Course slug
   * @returns {Promise} - List of course testimonials
   */
  getCourseTestimonials: async (courseSlug) => {
    // Endpoint path may need verification or implementation
    return handleRequest(
      async () => await apiClient.get(`/courses/${courseSlug}/testimonials/`),
      `Failed to fetch testimonials for course ${courseSlug}`
    );
  }
};

// Statistics services
export const statisticsService = {
  /**
   * Get platform-wide statistics
   * @returns {Promise} - Platform statistics
   */
  getPlatformStats: async () => {
    // Endpoint path may need verification or implementation
    return handleRequest(
      async () => await apiClient.get('/statistics/platform/'),
      'Failed to fetch platform statistics'
    );
  },
  
  /**
   * Get course category statistics
   * @returns {Promise} - Category statistics
   */
  getCategoryStats: async () => {
    // Endpoint path may need verification or implementation
    return handleRequest(
      async () => await apiClient.get('/statistics/categories/'),
      'Failed to fetch category statistics'
    );
  }
};


/**
 * Exports all services as a default object
 * This allows importing the entire API or individual services as needed
 */
export default {
  authService,
  subscriptionService,
  courseService,
  assessmentService,
  progressService,
  noteService,
  forumService,
  virtualLabService,
  categoryService,
  systemService,
  certificateService,
  blogService,
  testimonialService,
  statisticsService,
  
};