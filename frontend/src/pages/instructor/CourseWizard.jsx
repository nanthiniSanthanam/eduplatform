/**
 * File: frontend/src/pages/instructor/CourseWizard.jsx
 * Version: 2.1.1
 * Date: 2025-05-25 15:47:10
 * Author: mohithasanthanam
 * Last Modified: 2025-05-25 15:47:10 UTC
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
 * 7. CRITICAL FIX: Changed access_level default from 'all' to 'intermediate'
 * 8. Added session recovery mechanism
 * 9. Improved module and lesson saving with better error handling
 * 10. Added editor mode switching capability
 * 11. Added localStorage persistence for better user experience
 * 
 * This component provides a multi-step wizard for course creation with:
 * - 5-step process: Basics → Details → Modules → Content → Review & Publish
 * - Persistent state across steps
 * - Auto-save functionality
 * - Pre-publishing validation
 * 
 * Variables to modify:
 * - AUTO_SAVE_DELAY: Time in ms to wait before auto-saving (default: 3000)
 * 
 * Connected files that need to be consistent:
 * - frontend/src/pages/instructor/CourseWizardContext.jsx - State management
 * - frontend/src/services/instructorService.js - API calls
 * - backend/instructor_portal/views.py - API endpoints
 * - backend/instructor_portal/serializers.py - Data validation
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
    saveFailed,
    prepareModulesForSaving
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
  
  // ADDED: Session recovery mechanism
  useEffect(() => {
    // Check if we have a course slug/id from URL
    if (!courseData.id && !courseData.slug) {
      // If not, check localStorage for last edited course
      const lastEditedId = localStorage.getItem('lastEditedCourseId');
      const lastEditedSlug = localStorage.getItem('lastEditedCourseSlug');
      
      if (lastEditedSlug) {
        // Ask user if they want to resume editing
        const shouldRestore = window.confirm(
          "It looks like you were editing a course. Would you like to resume where you left off?"
        );
        
        if (shouldRestore) {
          navigate(`/instructor/courses/wizard/${lastEditedSlug}`);
        } else {
          // Clear the stored data if user doesn't want to resume
          localStorage.removeItem('lastEditedCourseId');
          localStorage.removeItem('lastEditedCourseSlug');
        }
      }
    }
  }, [courseData.id, courseData.slug, navigate]);
  
  // MODIFIED: Save the course data with improved module and lesson handling
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
      
      try {
        console.log("Attempting to save course with data:", {
          title: courseData.title,
          category_id: courseData.category_id,
          modules_count: modules?.length
        });
        
        // ADDED: Store current editing mode in localStorage
        localStorage.setItem('editorMode', 'wizard');
        
        // For new courses, create without modules first
        if (!courseData.id && !courseData.slug) {
          // New course - create without modules first
          const courseDataWithoutModules = { ...courseData };
          savedCourse = await instructorService.createCourse(courseDataWithoutModules);
          console.log("New course created successfully", savedCourse);
          
          // ADDED: Save course ID and slug to localStorage for recovery
          localStorage.setItem('lastEditedCourseId', savedCourse.id);
          localStorage.setItem('lastEditedCourseSlug', savedCourse.slug);
          
          // Then create modules if any exist
          if (modules && modules.length > 0) {
            const preparedModules = prepareModulesForSaving(modules);
            console.log("Creating modules after course creation:", preparedModules);
            
            // MODIFIED: Use Promise.all to wait for all module creations
            const modulePromises = preparedModules.map(module => 
              instructorService.createModule({
                ...module,
                course: savedCourse.id
              }).then(createdModule => {
                console.log(`Module created: ${module.title}`, createdModule);
                
                // ADDED: If module has lessons, create them too
                if (module.lessons && module.lessons.length > 0) {
                  const lessonPromises = module.lessons.map(lesson => 
                    instructorService.createLesson({
                      ...lesson,
                      module: createdModule.id
                    }).catch(lessonError => {
                      console.error(`Failed to create lesson ${lesson.title}:`, lessonError);
                      return null;
                    })
                  );
                  
                  return Promise.all(lessonPromises);
                }
                return createdModule;
              }).catch(moduleError => {
                console.error(`Failed to create module ${module.title}:`, moduleError);
                return null;
              })
            );
            
            await Promise.all(modulePromises);
          }
        } else {
          // Update existing course
          const identifier = courseData.slug || courseData.id;
          const fullCourseData = {
            ...courseData,
            // Don't include modules in update - they're managed separately
          };
          savedCourse = await instructorService.updateCourse(identifier, fullCourseData);
          console.log(`Course updated successfully with ${courseData.slug ? 'slug' : 'ID'}: ${identifier}`);
          
          // ADDED: Save course ID and slug to localStorage for recovery
          localStorage.setItem('lastEditedCourseId', savedCourse.id);
          localStorage.setItem('lastEditedCourseSlug', savedCourse.slug);
          
          // MODIFIED: Update existing modules and create new ones
          if (modules && modules.length > 0) {
            for (const module of modules) {
              try {
                let savedModule;
                
                // If module has a non-temporary ID, update it
                if (module.id && !String(module.id).startsWith('temp_')) {
                  savedModule = await instructorService.updateModule(module.id, {
                    ...module,
                    course: savedCourse.id
                  });
                  console.log(`Module updated: ${module.title}`);
                } else {
                  // Otherwise create a new module
                  savedModule = await instructorService.createModule({
                    ...module,
                    id: undefined, // Remove temporary ID
                    course: savedCourse.id
                  });
                  console.log(`Module created: ${module.title}`);
                }
                
                // Process lessons for this module
                if (module.lessons && module.lessons.length > 0) {
                  for (const lesson of module.lessons) {
                    try {
                      // If lesson has a non-temporary ID, update it
                      if (lesson.id && !String(lesson.id).startsWith('temp_')) {
                        await instructorService.updateLesson(lesson.id, {
                          ...lesson,
                          module: savedModule.id
                        });
                        console.log(`Lesson updated: ${lesson.title}`);
                      } else {
                        // Otherwise create a new lesson
                        await instructorService.createLesson({
                          ...lesson,
                          id: undefined, // Remove temporary ID
                          module: savedModule.id
                        });
                        console.log(`Lesson created: ${lesson.title}`);
                      }
                    } catch (lessonError) {
                      console.error(`Failed to save lesson ${lesson.title}:`, lessonError);
                      // Continue with next lesson instead of failing the whole save
                    }
                  }
                }
              } catch (moduleError) {
                console.error(`Failed to save module ${module.title}:`, moduleError);
                // Continue with next module instead of failing the whole save
              }
            }
          }
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
        
        // ADDED: Implement retry mechanism for save failures
        if (!error.status || error.status < 400 || error.status >= 500) {
          // Only retry for server errors or network issues
          console.log("Will retry save in 5 seconds...");
          setTimeout(() => {
            console.log("Retrying save operation...");
            handleSave();
          }, 5000);
        }
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
      
      {/* ADDED: Editor mode switching button */}
      <div className="flex justify-end mb-4">
        <Button 
          color="primary"
          variant="outlined"
          onClick={() => {
            if (window.confirm("Switch to traditional editor? Your progress will be saved.")) {
              // Save current progress first
              handleSave();
              
              localStorage.setItem('editorMode', 'traditional');
              
              // Navigate to traditional editor
              if (courseData.slug) {
                navigate(`/instructor/courses/${courseData.slug}/edit`);
              } else if (courseData.id) {
                navigate(`/instructor/courses/${courseData.id}/edit`);
              } else {
                navigate('/instructor/courses/traditional/new');
              }
            }
          }}
        >
          Switch to Traditional Editor
        </Button>
      </div>
      
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