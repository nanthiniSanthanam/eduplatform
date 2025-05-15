/**
 * File: frontend/src/pages/instructor/CourseWizard.jsx
 * Version: 2.1.0
 * Date: 2025-08-01
 * Author: nanthiniSanthanam
 * 
 * Enhanced Course Wizard with Authentication Persistence and Improved Course Management
 * 
 * Key Improvements:
 * 1. Integration with authPersist for reliable authentication
 * 2. Support for both ID and slug-based course fetching
 * 3. Enhanced error handling with detailed user feedback
 * 4. Improved auto-save functionality with useRef for timer management
 * 5. Better temporary ID handling before saving
 * 6. Fixed memory leaks in auto-save timer
 * 
 * This component provides a multi-step wizard for course creation with:
 * - 5-step process: Basics → Details → Modules → Content → Review & Publish
 * - Persistent state across steps
 * - Auto-save functionality
 * - Pre-publishing validation
 * 
 * Variables to modify:
 * - AUTO_SAVE_DELAY: Time in ms to wait before auto-saving (default: 3000)
 */

import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CourseWizardProvider, useCourseWizard } from './CourseWizardContext';
import MainLayout from '../../components/layouts/MainLayout';
import { 
  Card, 
  Button, 
  StepIndicator,
  Alert,
  LoadingScreen
} from '../../components/common';
import instructorService from '../../services/instructorService';
import authPersist from '../../utils/authPersist';

// Wizard Steps
import { 
  CourseBasicsStep,
  CourseDetailsStep, 
  ModuleStructureStep,
  ContentCreationStep,
  ReviewPublishStep
} from './wizardSteps';

// Configuration
const AUTO_SAVE_DELAY = 3000; // 3 seconds delay for auto-save

/**
 * CourseWizardContent Component
 * 
 * Inner content for the wizard that has access to the CourseWizard context
 */
const CourseWizardContent = () => {
  const navigate = useNavigate();
  const { 
    courseData, 
    modules, 
    currentStep, 
    totalSteps,
    setStep, 
    nextStep, 
    prevStep, 
    errors,
    setErrors,
    validateCurrentStep,
    isDirty,
    isSaving,
    saveStarted,
    saveCompleted,
    saveFailed
  } = useCourseWizard();
  
  // Use useRef for timer to properly clean up on unmount and prevent stale closures
  const saveTimerRef = useRef(null);
  const [generalError, setGeneralError] = useState(null);
  const [savingStatus, setSavingStatus] = useState({
    saving: false,
    success: false,
    error: null
  });

  // Ref for token refresh interval to properly clean up
  const refreshIntervalRef = useRef(null);
  
  // Handle auto-save with proper cleanup
  useEffect(() => {
    // Skip if already saving or no title yet
    if (isSaving || !courseData.title) {
      return;
    }
    
    // Clear any existing timer
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current);
      saveTimerRef.current = null;
    }
    
    if (isDirty && courseData.title) {
      // Set a new timer to save after delay
      saveTimerRef.current = setTimeout(() => {
        handleSave();
      }, AUTO_SAVE_DELAY);
    }
    
    // Clean up timer on unmount or when dependencies change
    return () => {
      if (saveTimerRef.current) {
        clearTimeout(saveTimerRef.current);
        saveTimerRef.current = null;
      }
    };
  }, [courseData, modules, isDirty, isSaving]);
  
  // Ensure authentication persists during long editing sessions
  useEffect(() => {
    // Refresh token expiry periodically during active editing
    refreshIntervalRef.current = setInterval(() => {
      if (authPersist && typeof authPersist.isTokenValid === 'function') {
        const tokenExpiry = localStorage.getItem('tokenExpiry');
        if (tokenExpiry) {
          // Check if token will expire in less than 10 minutes
          const expiryDate = new Date(tokenExpiry);
          const now = new Date();
          const timeUntilExpiry = expiryDate.getTime() - now.getTime();
          const tenMinutes = 10 * 60 * 1000;
          
          if (timeUntilExpiry < tenMinutes) {
            // Token expiring soon, refresh it
            const refreshToken = authPersist.getRefreshToken();
            if (refreshToken) {
              import('../../services/api').then(api => {
                if (api.auth && typeof api.auth.refreshToken === 'function') {
                  api.auth.refreshToken(refreshToken)
                    .then(() => console.log("Token refreshed during course editing"))
                    .catch(err => console.error("Failed to refresh token:", err));
                }
              }).catch(err => console.error("Failed to import API module:", err));
            }
          } else if (typeof authPersist.refreshTokenExpiry === 'function') {
            // Just extend the local expiry
            authPersist.refreshTokenExpiry();
            console.log("Authentication session extended during course editing");
          }
        }
      }
    }, 10 * 60 * 1000); // Every 10 minutes
    
    // Clear interval on unmount
    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
        refreshIntervalRef.current = null;
      }
    };
  }, []);
  
  // Prepare modules and lessons by removing temporary IDs
  const prepareModulesForSaving = (modulesList) => {
    return modulesList.map(module => {
      // Create a new module object to avoid mutating state
      const preparedModule = { ...module };
      
      // Remove temporary IDs
      if (preparedModule.id && typeof preparedModule.id === 'string' && preparedModule.id.startsWith('temp_')) {
        preparedModule.id = null;
      }
      
      // Process lessons if they exist
      if (preparedModule.lessons && Array.isArray(preparedModule.lessons)) {
        preparedModule.lessons = preparedModule.lessons.map(lesson => {
          const preparedLesson = { ...lesson };
          
          // Remove temporary IDs from lessons
          if (preparedLesson.id && typeof preparedLesson.id === 'string' && preparedLesson.id.startsWith('temp_')) {
            preparedLesson.id = null;
          }
          
          // Ensure access_level is set
          if (!preparedLesson.access_level) {
            preparedLesson.access_level = 'all';
          }
          
          return preparedLesson;
        });
      }
      
      return preparedModule;
    });
  };
  
  // Save the course data
  const handleSave = async () => {
    // Prevent saving if already in progress
    if (isSaving) {
      console.log("Save already in progress, skipping");
      return;
    }
    
    if (!courseData.title) {
      setGeneralError("Course title is required");
      return;
    }
    
    try {
      setSavingStatus({
        saving: true,
        success: false,
        error: null
      });
      
      saveStarted();
      
      // Create or update course
      let savedCourse;
      
      // Prepare modules by removing temporary IDs
      const preparedModules = prepareModulesForSaving(modules);
      
      // Prepare course data with prepared modules
      const fullCourseData = {
        ...courseData,
        modules: preparedModules
      };
      
      try {
        console.log("Attempting to save course with data:", {
          title: fullCourseData.title,
          category_id: fullCourseData.category_id,
          modules_count: fullCourseData.modules?.length
        });
        
        // Use update if course has an ID or slug, otherwise create
        if (courseData.id || courseData.slug) {
          const identifier = courseData.slug || courseData.id;
          savedCourse = await instructorService.updateCourse(identifier, fullCourseData);
          console.log(`Course updated successfully with ${courseData.slug ? 'slug' : 'ID'}: ${identifier}`);
        } else {
          savedCourse = await instructorService.createCourse(fullCourseData);
          console.log("New course created successfully");
        }
        
        // Show success status briefly
        setSavingStatus({
          saving: false,
          success: true,
          error: null
        });
        
        // Reset success message after 2 seconds
        setTimeout(() => {
          setSavingStatus(prev => ({
            ...prev,
            success: false
          }));
        }, 2000);
        
        saveCompleted(savedCourse);
      } catch (error) {
        console.error("Error saving course:", error);
        
        // Extract detailed error if available
        let errorMessage = "Failed to save course";
        let errorDetails = [];
        
        // Handle different error formats
        if (error.details) {
          if (typeof error.details === 'string') {
            errorMessage = error.details;
          } else if (typeof error.details === 'object') {
            // Process Django REST Framework detailed error format
            Object.entries(error.details).forEach(([key, value]) => {
              const errorText = Array.isArray(value) ? value.join(', ') : value;
              errorDetails.push(`${key}: ${errorText}`);
            });
            
            if (errorDetails.length > 0) {
              errorMessage = errorDetails.join('\n');
            }
          }
        } else if (error.message) {
          errorMessage = error.message;
        }
        
        if (error.status) {
          errorMessage += ` (Status: ${error.status})`;
        }
        
        console.error("Formatted error message:", errorMessage);
        
        setSavingStatus({
          saving: false,
          success: false,
          error: errorMessage
        });
        
        saveFailed(errorMessage);
      }
    } catch (error) {
      console.error("Unexpected error during save:", error);
      setSavingStatus({
        saving: false,
        success: false,
        error: "Unknown error occurred while saving"
      });
      
      saveFailed("Unknown error occurred while saving");
    }
  };
  
  // Handle course publication
  const handlePublishCourse = async () => {
    if (!courseData.id && !courseData.slug) {
      setGeneralError("Course must be saved before publishing");
      return;
    }
    
    try {
      // Save the course first to ensure all changes are captured
      await handleSave();
      
      // Publish the course using the dedicated endpoint
      const identifier = courseData.slug || courseData.id;
      await instructorService.publishCourse(identifier, true);
      
      // Show success message
      setSavingStatus({
        saving: false,
        success: true,
        error: null
      });
      
      // Navigate after a short delay
      setTimeout(() => {
        navigate(`/instructor/courses/${identifier}`);
      }, 1500);
    } catch (error) {
      console.error("Error publishing course:", error);
      setSavingStatus({
        saving: false,
        success: false,
        error: "Failed to publish course: " + (error.message || "Unknown error")
      });
    }
  };
  
  // Navigate to previous step
  const handlePrevStep = () => {
    prevStep();
  };
  
  // Navigate to next step after validation
  const handleNextStep = () => {
    const isValid = validateCurrentStep();
    
    if (isValid) {
      handleSave(); // Save before advancing
      nextStep();
    }
  };
  
  // Render step content based on current step
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return <CourseBasicsStep />;
      case 2:
        return <CourseDetailsStep />;
      case 3:
        return <ModuleStructureStep />;
      case 4:
        return <ContentCreationStep />;
      case 5:
        return <ReviewPublishStep />;
      default:
        return <div>Unknown step</div>;
    }
  };
  
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">
          {courseData.title || "New Course"}
        </h1>
        <p className="text-gray-600">
          Complete all steps to create your course
        </p>
      </div>
      
      {generalError && (
        <Alert type="error" className="mb-4">
          {generalError}
          <button 
            className="ml-2 text-sm underline"
            onClick={() => setGeneralError(null)}
          >
            Dismiss
          </button>
        </Alert>
      )}
      
      {savingStatus.error && (
        <Alert type="error" className="mb-4">
          <div className="font-medium">Error saving course:</div>
          <div className="text-sm whitespace-pre-line">{savingStatus.error}</div>
          <button 
            className="ml-2 text-sm underline"
            onClick={() => setSavingStatus(prev => ({ ...prev, error: null }))}
          >
            Dismiss
          </button>
        </Alert>
      )}
      
      {/* Step indicator */}
      <div className="mb-6">
        <StepIndicator 
          steps={[
            { label: "Basics" },
            { label: "Details" },
            { label: "Modules" },
            { label: "Content" },
            { label: "Review" }
          ]}
          currentStep={currentStep}
          onChange={setStep}
        />
      </div>
      
      {/* Saving indicator */}
      {(savingStatus.saving || savingStatus.success) && (
        <div className={`mb-4 p-2 text-sm rounded-md ${
          savingStatus.saving ? 'bg-blue-50 text-blue-700' : 'bg-green-50 text-green-700'
        }`}>
          {savingStatus.saving ? (
            <div className="flex items-center">
              <svg className="animate-spin h-4 w-4 mr-2" viewBox="0 0 24 24">
                <circle 
                  className="opacity-25" 
                  cx="12" 
                  cy="12" 
                  r="10" 
                  stroke="currentColor" 
                  strokeWidth="4"
                  fill="none"
                />
                <path 
                  className="opacity-75" 
                  fill="currentColor" 
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Saving course...
            </div>
          ) : (
            <div className="flex items-center">
              <svg className="h-4 w-4 mr-2 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Course saved successfully
            </div>
          )}
        </div>
      )}
      
      {/* Main content */}
      <Card className="mb-6">
        {renderStepContent()}
      </Card>
      
      {/* Navigation buttons */}
      <div className="flex justify-between mt-6">
        <Button
          color="secondary"
          variant="outlined"
          onClick={handlePrevStep}
          disabled={currentStep === 1}
        >
          Previous
        </Button>
        
        <div className="flex space-x-2">
          <Button
            color="primary"
            onClick={handleSave}
            disabled={savingStatus.saving}
          >
            Save
          </Button>
          
          {currentStep < totalSteps ? (
            <Button
              color="primary"
              onClick={handleNextStep}
              disabled={savingStatus.saving}
            >
              Next
            </Button>
          ) : (
            <Button
              color="success"
              onClick={handlePublishCourse}
              disabled={savingStatus.saving}
            >
              Publish Course
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * CourseWizard Component
 * 
 * Main wrapper component that provides the CourseWizard context
 */
const CourseWizard = () => {
  const { courseSlug } = useParams();
  const [loading, setLoading] = useState(courseSlug ? true : false);
  const [course, setCourse] = useState(null);
  const [error, setError] = useState(null);
  
  // Fetch existing course data if editing
  useEffect(() => {
    const fetchCourse = async () => {
      if (courseSlug) {
        try {
          setLoading(true);
          
          // Refresh auth token to prevent session expiration during editing
          if (authPersist && typeof authPersist.isTokenValid === 'function' && 
              typeof authPersist.refreshTokenExpiry === 'function') {
            if (authPersist.isTokenValid()) {
              authPersist.refreshTokenExpiry();
            }
          }
          
          const response = await instructorService.getCourseBySlug(courseSlug);
          const courseData = response.data || response;
          
          if (!courseData) {
            throw new Error(`Course with slug "${courseSlug}" not found`);
          }
          
          setCourse(courseData);
          setLoading(false);
        } catch (error) {
          console.error("Error fetching course:", error);
          
          // Format error message
          let errorMessage = "Failed to fetch course. Please try again.";
          if (error.message) {
            errorMessage = error.message;
          } else if (error.status === 404) {
            errorMessage = `Course with slug "${courseSlug}" not found.`;
          } else if (error.status === 403) {
            errorMessage = "You don't have permission to edit this course.";
          }
          
          setError(errorMessage);
          setLoading(false);
        }
      }
    };
    
    fetchCourse();
  }, [courseSlug]);
  
  if (loading) {
    return <MainLayout><LoadingScreen message="Loading course data..." /></MainLayout>;
  }
  
  if (error) {
    return (
      <MainLayout>
        <div className="container mx-auto px-4 py-8">
          <Alert type="error">
            {error}
          </Alert>
          <div className="mt-4">
            <Button onClick={() => window.history.back()}>
              Go Back
            </Button>
          </div>
        </div>
      </MainLayout>
    );
  }
  
  return (
    <MainLayout>
      <CourseWizardProvider existingCourse={course}>
        <CourseWizardContent />
      </CourseWizardProvider>
    </MainLayout>
  );
};

export default CourseWizard;
// END OF CODE