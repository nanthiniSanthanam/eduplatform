// fmt: off
// isort: skip_file
// Timestamp: 2025-08-01 - Review and Publish Step (Step 5) of Course Creation Wizard

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCourseWizard } from '../CourseWizardContext';
import { Card, Button, Alert } from '../../../components/common';
import instructorService from '../../../services/instructorService';

/**
 * Step 5: Review & Publish
 * 
 * Allows instructors to:
 * - Review their entire course structure
 * - See a completeness score/checklist
 * - Handle publishing options
 * - Get final validation before publishing
 */
const ReviewPublishStep = () => {
  const navigate = useNavigate();
  const { 
    courseData, modules, updateCourse, publishCourse,
    validateCurrentStep, isStepCompleted 
  } = useCourseWizard();
  
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Calculate course completeness score
  const calculateCompletenessScore = () => {
    let score = 0;
    let total = 0;
    
    // Basic course info (30%)
    total += 30;
    if (courseData.title) score += 10;
    if (courseData.description && courseData.description.length > 50) score += 10;
    if (courseData.thumbnail) score += 5;
    if (courseData.category_id) score += 5;
    
    // Additional details (20%)
    total += 20;
    if (courseData.subtitle) score += 5;
    if (courseData.requirements && courseData.requirements.length > 0) score += 5;
    if (courseData.skills && courseData.skills.length > 0) score += 5;
    if (courseData.price >= 0) score += 5;
    
    // Modules (20%)
    total += 20;
    if (modules.length > 0) score += 10;
    if (modules.length >= 3) score += 10; // Good course structure
    
    // Content (30%)
    total += 30;
    const hasLessons = modules.every(module => module.lessons && module.lessons.length > 0);
    if (hasLessons) score += 15;
    
    // Count total lessons
    const lessonsCount = modules.reduce((total, module) => {
      return total + (module.lessons ? module.lessons.length : 0);
    }, 0);
    
    if (lessonsCount >= 5) score += 5;
    if (lessonsCount >= 10) score += 5;
    if (lessonsCount >= 15) score += 5;
    
    // Calculate percentage
    return Math.round((score / total) * 100);
  };
  
  const completenessScore = calculateCompletenessScore();
  
  // Check if course is publishable
  const canPublish = completenessScore >= 70 && 
    isStepCompleted(1) && isStepCompleted(3) && isStepCompleted(4);
  
  // Handle publish action
  const handlePublish = async () => {
    if (!canPublish) return;
    
    setPublishing(true);
    setError(null);
    setSuccess(null);
    
    try {
      // Check if we have a valid course identifier (slug or ID)
      if (!courseData.slug && !courseData.id) {
        throw new Error("Course must be saved before publishing");
      }
      
      // Use the dedicated publish endpoint instead of generic update
      const identifier = courseData.slug || courseData.id;
      await instructorService.publishCourse(identifier, true);
      
      // Update state
      publishCourse(true);
      setSuccess('Your course has been published successfully!');
      
      // Redirect after short delay
      setTimeout(() => {
        navigate(`/instructor/dashboard`);
      }, 3000);
      
    } catch (err) {
      console.error('Error publishing course:', err);
      setError(err.message || 'Failed to publish course. Please try again.');
    } finally {
      setPublishing(false);
    }
  };
  
  // Check requirements for missing content
  const getMissingRequirements = () => {
    const missing = [];
    
    if (!courseData.title) missing.push('Course title is required');
    if (!courseData.category_id) missing.push('Course category is required');
    if (!courseData.description) missing.push('Course description is missing');
    if (modules.length === 0) missing.push('At least one module is required');
    
    const modulesWithoutLessons = modules.filter(
      module => !module.lessons || module.lessons.length === 0
    );
    
    if (modulesWithoutLessons.length > 0) {
      missing.push(`${modulesWithoutLessons.length} module(s) have no lessons`);
    }
    
    return missing;
  };
  
  const missingRequirements = getMissingRequirements();
  
  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-gray-200">
        <h2 className="text-2xl font-bold">Review & Publish</h2>
        <p className="text-gray-600 mt-1">
          Review your course and make it available to students
        </p>
      </div>
      
      {/* Completeness score */}
      <Card className="bg-white overflow-visible">
        <h3 className="font-medium mb-4">Course Completeness</h3>
        
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-700">Overall Score</span>
            <span className="font-medium">{completenessScore}%</span>
          </div>
          <div className="h-2.5 w-full bg-gray-200 rounded-full">
            <div 
              className={`h-2.5 rounded-full ${
                completenessScore >= 70
                  ? 'bg-green-500'
                  : completenessScore >= 40
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
              }`}
              style={{ width: `${completenessScore}%` }}
            ></div>
          </div>
        </div>
        
        {missingRequirements.length > 0 && (
          <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
            <h4 className="font-medium text-yellow-700 mb-2">Missing Items</h4>
            <ul className="list-disc list-inside text-sm text-yellow-600 space-y-1">
              {missingRequirements.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </div>
        )}
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Course Structure</h4>
            <ul className="space-y-2">
              <li className="flex items-start">
                <div className={`flex-shrink-0 h-5 w-5 ${courseData.title ? 'text-green-500' : 'text-gray-300'}`}>
                  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="ml-2 text-sm text-gray-600">Course Title</span>
              </li>
              <li className="flex items-start">
                <div className={`flex-shrink-0 h-5 w-5 ${courseData.description ? 'text-green-500' : 'text-gray-300'}`}>
                  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="ml-2 text-sm text-gray-600">Course Description</span>
              </li>
              <li className="flex items-start">
                <div className={`flex-shrink-0 h-5 w-5 ${courseData.thumbnail ? 'text-green-500' : 'text-gray-300'}`}>
                  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="ml-2 text-sm text-gray-600">Course Thumbnail</span>
              </li>
              <li className="flex items-start">
                <div className={`flex-shrink-0 h-5 w-5 ${modules.length > 0 ? 'text-green-500' : 'text-gray-300'}`}>
                  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="ml-2 text-sm text-gray-600">Modules ({modules.length})</span>
              </li>
              <li className="flex items-start">
                <div className={`flex-shrink-0 h-5 w-5 ${isStepCompleted(4) ? 'text-green-500' : 'text-gray-300'}`}>
                  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="ml-2 text-sm text-gray-600">Lessons with Content</span>
              </li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Optional Items</h4>
            <ul className="space-y-2">
              <li className="flex items-start">
                <div className={`flex-shrink-0 h-5 w-5 ${courseData.subtitle ? 'text-green-500' : 'text-gray-300'}`}>
                  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="ml-2 text-sm text-gray-600">Course Subtitle</span>
              </li>
              <li className="flex items-start">
                <div className={`flex-shrink-0 h-5 w-5 ${courseData.requirements?.length > 0 ? 'text-green-500' : 'text-gray-300'}`}>
                  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="ml-2 text-sm text-gray-600">Course Requirements</span>
              </li>
              <li className="flex items-start">
                <div className={`flex-shrink-0 h-5 w-5 ${courseData.skills?.length > 0 ? 'text-green-500' : 'text-gray-300'}`}>
                  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="ml-2 text-sm text-gray-600">Skills Students Will Learn</span>
              </li>
              <li className="flex items-start">
                <div className={`flex-shrink-0 h-5 w-5 ${courseData.has_certificate ? 'text-green-500' : 'text-gray-300'}`}>
                  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="ml-2 text-sm text-gray-600">Course Certificate</span>
              </li>
              <li className="flex items-start">
                <div className={`flex-shrink-0 h-5 w-5 ${modules.length >= 3 ? 'text-green-500' : 'text-gray-300'}`}>
                  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="ml-2 text-sm text-gray-600">Multiple Modules (3+)</span>
              </li>
            </ul>
          </div>
        </div>
      </Card>
      
      {/* Course summary */}
      <Card className="overflow-visible">
        <h3 className="font-medium mb-4">Course Summary</h3>
        
        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-medium text-gray-700">Title</h4>
            <p className="mt-1">{courseData.title || 'No title set'}</p>
          </div>
          
          <div>
            <h4 className="text-sm font-medium text-gray-700">Description</h4>
            <p className="mt-1 text-sm">{courseData.description || 'No description set'}</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <h4 className="text-sm font-medium text-gray-700">Level</h4>
              <p className="mt-1 capitalize">{courseData.level || 'Not set'}</p>
            </div>
            
            <div>
              <h4 className="text-sm font-medium text-gray-700">Price</h4>
              <p className="mt-1">{courseData.price ? `$${courseData.price}` : 'Free'}</p>
            </div>
            
            <div>
              <h4 className="text-sm font-medium text-gray-700">Certificate</h4>
              <p className="mt-1">{courseData.has_certificate ? 'Yes' : 'No'}</p>
            </div>
          </div>
        </div>
        
        <h4 className="text-sm font-medium text-gray-700 mt-6 mb-2">Module Structure</h4>
        <div className="space-y-2 mb-6">
          {modules.length > 0 ? (
            modules
              .sort((a, b) => a.order - b.order)
              .map((module, index) => (
                <div key={module.id} className="bg-gray-50 p-3 rounded-md">
                  <div className="font-medium">
                    {index + 1}. {module.title}
                  </div>
                  <div className="text-sm text-gray-500 mt-1">
                    {module.lessons?.length || 0} lesson{module.lessons?.length !== 1 ? 's' : ''}
                  </div>
                </div>
              ))
          ) : (
            <p className="text-gray-500 italic">No modules created yet</p>
          )}
        </div>
      </Card>
      
      {/* Publishing options */}
      <Card className="overflow-visible">
        <h3 className="font-medium mb-4">Publishing Options</h3>
        
        {error && (
          <Alert type="error" className="mb-4">
            {error}
          </Alert>
        )}
        
        {success && (
          <Alert type="success" className="mb-4">
            {success}
          </Alert>
        )}
        
        <div className="flex items-center mb-4">
          <input
            type="checkbox"
            id="draft-mode"
            checked={!courseData.is_published}
            onChange={(e) => updateCourse({ is_published: !e.target.checked })}
            className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
          />
          <label htmlFor="draft-mode" className="ml-2 text-gray-700">
            Save as draft (not visible to students)
          </label>
        </div>
        
        <div className="flex space-x-4">
          <Button
            variant="contained"
            color="success"
            onClick={handlePublish}
            disabled={publishing || !canPublish}
            className="min-w-32"
          >
            {publishing ? 'Publishing...' : 'Publish Course'}
          </Button>
          
          {!canPublish && (
            <p className="text-yellow-600 text-sm flex items-center">
              <svg className="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Complete all required items before publishing
            </p>
          )}
        </div>
      </Card>
    </div>
  );
};

export default ReviewPublishStep; 