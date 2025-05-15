/**
 * File: frontend/src/pages/instructor/CourseWizardContext.jsx
 * Version: 2.1.0
 * Date: 2025-08-01
 * 
 * Enhanced Course Wizard Context with Authentication Persistence Integration
 * 
 * Key Improvements:
 * 1. Added support for both slug and ID-based operations
 * 2. Enhanced error handling with detailed feedback
 * 3. Improved save state management with status tracking
 * 4. Fixed mutation issues with module and lesson arrays
 * 5. Enhanced ID generation to avoid collisions
 * 6. Improved validation for all wizard steps
 * 
 * This context manages state for the course wizard across steps:
 * - Course metadata (title, description, etc.)
 * - Module and lesson structure
 * - Current step tracking
 * - Validation state
 * - Auto-save functionality
 * 
 * Variables to modify:
 * - initialState: Default starting state for new courses
 * - ACTIONS: Reducer action types for state modifications
 */

import React, { createContext, useContext, useState, useReducer } from 'react';
import authPersist from '../../utils/authPersist';

// Initial state for the course wizard
const initialState = {
  // Course details
  courseData: {
    title: '',
    subtitle: '',
    description: '',
    category_id: '',
    level: 'beginner',
    price: 0,
    thumbnail: null,
    is_featured: false,
    requirements: [],
    skills: [],
    has_certificate: false,
    duration: '',
    slug: null,  // Added to track course slug
    id: null     // Added to track course ID
  },
  
  // Modules array
  modules: [],
  
  // Current editing state
  currentStep: 1,
  totalSteps: 5,
  isCompleted: false,
  
  // Save status
  isSaving: false,
  lastSavedAt: null,
  
  // Validation and errors
  errors: {},
  isDirty: false
};

// Actions for the reducer
const ACTIONS = {
  UPDATE_COURSE: 'UPDATE_COURSE',
  ADD_MODULE: 'ADD_MODULE',
  UPDATE_MODULE: 'UPDATE_MODULE',
  REMOVE_MODULE: 'REMOVE_MODULE',
  ADD_LESSON: 'ADD_LESSON',
  UPDATE_LESSON: 'UPDATE_LESSON',
  REMOVE_LESSON: 'REMOVE_LESSON',
  SET_STEP: 'SET_STEP',
  SAVE_STARTED: 'SAVE_STARTED',
  SAVE_COMPLETED: 'SAVE_COMPLETED',
  SAVE_FAILED: 'SAVE_FAILED',
  PUBLISH_COURSE: 'PUBLISH_COURSE',
  RESET_WIZARD: 'RESET_WIZARD',
  SET_ERRORS: 'SET_ERRORS',
  CLEAR_ERRORS: 'CLEAR_ERRORS',
  MARK_DIRTY: 'MARK_DIRTY',
  MARK_CLEAN: 'MARK_CLEAN'
};

// Reducer function
function courseWizardReducer(state, action) {
  switch (action.type) {
    case ACTIONS.UPDATE_COURSE:
      return {
        ...state,
        courseData: {
          ...state.courseData,
          ...action.payload
        },
        isDirty: true
      };
      
    case ACTIONS.ADD_MODULE:
      return {
        ...state,
        modules: [...state.modules, action.payload],
        isDirty: true
      };
      
    case ACTIONS.UPDATE_MODULE:
      return {
        ...state,
        modules: state.modules.map(module => 
          module.id === action.payload.id ? { ...module, ...action.payload } : module
        ),
        isDirty: true
      };
      
    case ACTIONS.REMOVE_MODULE:
      return {
        ...state,
        modules: state.modules.filter(module => module.id !== action.payload),
        isDirty: true
      };
      
    case ACTIONS.ADD_LESSON:
      return {
        ...state,
        modules: state.modules.map(module => 
          module.id === action.payload.moduleId 
            ? { 
                ...module, 
                lessons: Array.isArray(module.lessons) 
                  ? [...module.lessons, action.payload.lesson] 
                  : [action.payload.lesson] 
              } 
            : module
        ),
        isDirty: true
      };
      
    case ACTIONS.UPDATE_LESSON:
      return {
        ...state,
        modules: state.modules.map(module => 
          module.id === action.payload.moduleId 
            ? { 
                ...module, 
                lessons: Array.isArray(module.lessons) 
                  ? module.lessons.map(lesson => 
                      lesson.id === action.payload.lesson.id 
                        ? { ...lesson, ...action.payload.lesson } 
                        : lesson
                    )
                  : [action.payload.lesson] // If module has no lessons array, create one with this lesson
              } 
            : module
        ),
        isDirty: true
      };
      
    case ACTIONS.REMOVE_LESSON:
      return {
        ...state,
        modules: state.modules.map(module => 
          module.id === action.payload.moduleId 
            ? { 
                ...module, 
                lessons: Array.isArray(module.lessons)
                  ? module.lessons.filter(lesson => lesson.id !== action.payload.lessonId)
                  : []
              } 
            : module
        ),
        isDirty: true
      };
      
    case ACTIONS.SET_STEP:
      return {
        ...state,
        currentStep: action.payload
      };
      
    case ACTIONS.SAVE_STARTED:
      return {
        ...state,
        isSaving: true
      };
      
    case ACTIONS.SAVE_COMPLETED:
      return {
        ...state,
        isSaving: false,
        lastSavedAt: new Date(),
        isDirty: false,
        courseData: action.payload ? {
          ...state.courseData,
          ...action.payload,
          // Ensure we keep track of ID and slug
          id: action.payload.id || state.courseData.id,
          slug: action.payload.slug || state.courseData.slug
        } : state.courseData
      };
      
    case ACTIONS.SAVE_FAILED:
      return {
        ...state,
        isSaving: false,
        errors: { ...state.errors, save: action.payload }
      };
      
    case ACTIONS.PUBLISH_COURSE:
      return {
        ...state,
        courseData: {
          ...state.courseData,
          is_published: action.payload
        },
        isDirty: true
      };
      
    case ACTIONS.RESET_WIZARD:
      return {
        ...initialState,
        currentStep: 1
      };
      
    case ACTIONS.SET_ERRORS:
      return {
        ...state,
        errors: { ...state.errors, ...action.payload }
      };
      
    case ACTIONS.CLEAR_ERRORS:
      return {
        ...state,
        errors: {}
      };
      
    case ACTIONS.MARK_DIRTY:
      return {
        ...state,
        isDirty: true
      };
      
    case ACTIONS.MARK_CLEAN:
      return {
        ...state,
        isDirty: false
      };
      
    default:
      return state;
  }
}

// Create context
const CourseWizardContext = createContext();

// Counter for ID generation to ensure uniqueness
let idCounter = 1;

// Context provider component
export function CourseWizardProvider({ children, existingCourse = null }) {
  // Initialize state with existing course data if available
  const [state, dispatch] = useReducer(
    courseWizardReducer, 
    existingCourse 
      ? {
          ...initialState,
          courseData: { 
            ...initialState.courseData, 
            ...existingCourse,
            // Ensure we capture ID and slug
            id: existingCourse.id || null,
            slug: existingCourse.slug || null
          },
          modules: existingCourse.modules || []
        }
      : initialState
  );
  
  // Generate a temporary ID for new modules/lessons
  const generateTempId = () => {
    // Use a combination of timestamp, random number, and counter to avoid collisions
    const timestamp = Date.now();
    const random = Math.floor(Math.random() * 100000);
    
    // Increment the counter with each call to ensure uniqueness even for quick successive calls
    idCounter += 1;
    
    return `temp_${timestamp}_${random}_${idCounter}`;
  };
  
  // Methods for updating state
  const updateCourse = (data) => {
    dispatch({ type: ACTIONS.UPDATE_COURSE, payload: data });
  };
  
  const addModule = (moduleData) => {
    const newModule = {
      id: generateTempId(),
      title: '',
      description: '',
      order: state.modules.length + 1,
      lessons: [],
      ...moduleData
    };
    dispatch({ type: ACTIONS.ADD_MODULE, payload: newModule });
    return newModule.id;
  };
  
  const updateModule = (moduleId, data) => {
    dispatch({ 
      type: ACTIONS.UPDATE_MODULE, 
      payload: { id: moduleId, ...data } 
    });
  };
  
  const removeModule = (moduleId) => {
    dispatch({ type: ACTIONS.REMOVE_MODULE, payload: moduleId });
  };
  
  const addLesson = (moduleId, lessonData) => {
    // Find the module to calculate proper lesson order
    const module = state.modules.find(m => m.id === moduleId);
    const lessonCount = module?.lessons?.length || 0;
    
    const newLesson = {
      id: generateTempId(),
      title: '',
      content: '',
      order: lessonCount + 1,
      access_level: 'all', // Default access level
      ...lessonData
    };
    
    dispatch({ 
      type: ACTIONS.ADD_LESSON, 
      payload: { moduleId, lesson: newLesson } 
    });
    
    return newLesson.id;
  };
  
  const updateLesson = (moduleId, lessonId, data) => {
    dispatch({ 
      type: ACTIONS.UPDATE_LESSON, 
      payload: { 
        moduleId, 
        lesson: { id: lessonId, ...data } 
      } 
    });
  };
  
  const removeLesson = (moduleId, lessonId) => {
    dispatch({ 
      type: ACTIONS.REMOVE_LESSON, 
      payload: { moduleId, lessonId } 
    });
  };
  
  const setStep = (step) => {
    // Refresh auth token when changing steps to prevent session timeout
    if (authPersist && typeof authPersist.isTokenValid === 'function' && 
        typeof authPersist.refreshTokenExpiry === 'function') {
      if (authPersist.isTokenValid()) {
        authPersist.refreshTokenExpiry();
      }
    }
    
    dispatch({ type: ACTIONS.SET_STEP, payload: step });
  };
  
  const nextStep = () => {
    if (state.currentStep < state.totalSteps) {
      dispatch({ type: ACTIONS.SET_STEP, payload: state.currentStep + 1 });
    }
  };
  
  const prevStep = () => {
    if (state.currentStep > 1) {
      dispatch({ type: ACTIONS.SET_STEP, payload: state.currentStep - 1 });
    }
  };
  
  const goToStep = (step) => {
    if (step >= 1 && step <= state.totalSteps) {
      dispatch({ type: ACTIONS.SET_STEP, payload: step });
    }
  };
  
  const saveStarted = () => {
    dispatch({ type: ACTIONS.SAVE_STARTED });
  };
  
  const saveCompleted = (courseData = null) => {
    dispatch({ 
      type: ACTIONS.SAVE_COMPLETED,
      payload: courseData 
    });
  };
  
  const saveFailed = (error) => {
    dispatch({ 
      type: ACTIONS.SAVE_FAILED,
      payload: error 
    });
  };
  
  const publishCourse = (isPublished = true) => {
    dispatch({ 
      type: ACTIONS.PUBLISH_COURSE,
      payload: isPublished 
    });
  };
  
  const resetWizard = () => {
    dispatch({ type: ACTIONS.RESET_WIZARD });
  };
  
  const setErrors = (errors) => {
    dispatch({ 
      type: ACTIONS.SET_ERRORS,
      payload: errors 
    });
  };
  
  const clearErrors = () => {
    dispatch({ type: ACTIONS.CLEAR_ERRORS });
  };
  
  // Function to validate the current step
  const validateCurrentStep = () => {
    let isValid = true;
    const errors = {};
    
    switch (state.currentStep) {
      case 1: // Course basics
        if (!state.courseData.title) {
          errors.title = 'Course title is required';
          isValid = false;
        }
        if (!state.courseData.category_id) {
          errors.category = 'Category is required';
          isValid = false;
        }
        break;
        
      case 2: // Course details
        if (!state.courseData.description || state.courseData.description.trim() === '') {
          errors.description = 'Course description is required';
          isValid = false;
        }
        // Price validation - must be a number or empty string (which will be converted to 0)
        if (state.courseData.price === '' || state.courseData.price === null) {
          // Empty price is valid (will be converted to 0)
        } else if (isNaN(parseFloat(state.courseData.price))) {
          errors.price = 'Price must be a valid number';
          isValid = false;
        }
        break;
        
      case 3: // Modules
        if (state.modules.length === 0) {
          errors.modules = 'At least one module is required';
          isValid = false;
        } else {
          // Check if all modules have titles
          const modulesWithoutTitles = state.modules.filter(
            module => !module.title || module.title.trim() === ''
          );
          if (modulesWithoutTitles.length > 0) {
            errors.moduleTitles = 'All modules must have titles';
            isValid = false;
          }
        }
        break;
        
      case 4: // Content
        // Check if any modules have no lessons
        const modulesWithoutLessons = state.modules.filter(
          module => !module.lessons || module.lessons.length === 0
        );
        if (modulesWithoutLessons.length > 0) {
          errors.lessons = 'All modules must have at least one lesson';
          isValid = false;
        }
        
        // Check if all lessons have titles
        let hasUntitledLessons = false;
        state.modules.forEach(module => {
          if (module.lessons && Array.isArray(module.lessons)) {
            const untitledLessons = module.lessons.filter(
              lesson => !lesson.title || lesson.title.trim() === ''
            );
            if (untitledLessons.length > 0) {
              hasUntitledLessons = true;
            }
          }
        });
        
        if (hasUntitledLessons) {
          errors.lessonTitles = 'All lessons must have titles';
          isValid = false;
        }
        break;
        
      case 5: // Review
        // Final validation before publishing
        if (!state.courseData.title || state.courseData.title.trim() === '') {
          errors.title = 'Course title is required';
          isValid = false;
        }
        
        if (!state.courseData.description || state.courseData.description.trim() === '') {
          errors.description = 'Course description is required';
          isValid = false;
        }
        
        if (!state.courseData.category_id) {
          errors.category = 'Category is required';
          isValid = false;
        }
        
        if (state.modules.length === 0) {
          errors.modules = 'At least one module is required';
          isValid = false;
        }
        
        // Check if there's at least one lesson across all modules
        let hasLessons = false;
        state.modules.forEach(module => {
          if (module.lessons && Array.isArray(module.lessons) && module.lessons.length > 0) {
            hasLessons = true;
          }
        });
        
        if (!hasLessons) {
          errors.lessons = 'Course must have at least one lesson';
          isValid = false;
        }
        break;
    }
    
    if (!isValid) {
      setErrors(errors);
    } else {
      clearErrors();
    }
    
    return isValid;
  };
  
  // Check if a step is completed based on state
  const isStepCompleted = (step) => {
    switch (step) {
      case 1: // Course basics
        return !!state.courseData.title && !!state.courseData.category_id;
        
      case 2: // Course details
        return !!state.courseData.description && state.courseData.description.trim() !== ''; 
        
      case 3: // Modules
        return state.modules.length > 0 && 
          state.modules.every(module => module.title && module.title.trim() !== '');
        
      case 4: // Content
        return state.modules.every(module => 
          Array.isArray(module.lessons) && 
          module.lessons.length > 0 &&
          module.lessons.every(lesson => lesson.title && lesson.title.trim() !== '')
        );
        
      case 5: // Review
        return true; // Always considered complete
        
      default:
        return false;
    }
  };
  
  // Value object
  const value = {
    ...state,
    updateCourse,
    addModule,
    updateModule,
    removeModule,
    addLesson,
    updateLesson,
    removeLesson,
    setStep,
    nextStep,
    prevStep,
    goToStep,
    saveStarted,
    saveCompleted,
    saveFailed,
    publishCourse,
    resetWizard,
    setErrors,
    clearErrors,
    validateCurrentStep,
    isStepCompleted,
    ACTIONS
  };

  return (
    <CourseWizardContext.Provider value={value}>
      {children}
    </CourseWizardContext.Provider>
  );
}

// Custom hook to use the context
export function useCourseWizard() {
  const context = useContext(CourseWizardContext);
  if (!context) {
    throw new Error('useCourseWizard must be used within a CourseWizardProvider');
  }
  return context;
}

export default CourseWizardContext;
// END OF CODE