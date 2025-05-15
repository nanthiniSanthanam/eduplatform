// fmt: off
// isort: skip_file
// Timestamp: 2024-06-15 - Course Details Step (Step 2) of Course Creation Wizard

import React, { useState } from 'react';
import { useCourseWizard } from '../CourseWizardContext';
// Remove ReactQuill imports
// Direct imports to avoid casing issues
import FormInput from '../../../components/common/FormInput';
import Card from '../../../components/common/Card';
import Button from '../../../components/common/Button';
import TagInput from '../../../components/common/TagInput';
import Alert from '../../../components/common/Alert';

/**
 * Step 2: Course Details
 * 
 * Captures the detailed information about the course:
 * - Comprehensive description (rich text)
 * - Skills students will learn (tags)
 * - Requirements/prerequisites (tags)
 * - Pricing information
 * - Duration and certificate options
 */
const CourseDetailsStep = () => {
  const { courseData, updateCourse, errors } = useCourseWizard();
  const [newSkill, setNewSkill] = useState('');
  const [newRequirement, setNewRequirement] = useState('');
  const [description, setDescription] = useState(courseData.description || '');
  
  // Handle rich text editor change
  const handleDescriptionChange = (e) => {
    const value = e.target.value;
    setDescription(value);
    updateCourse({ description: value });
  };
  
  // Handle tag additions and removals
  const addSkill = () => {
    if (!newSkill.trim()) return;
    
    const updatedSkills = [...(courseData.skills || []), newSkill.trim()];
    updateCourse({ skills: updatedSkills });
    setNewSkill('');
  };
  
  const removeSkill = (index) => {
    const updatedSkills = [...(courseData.skills || [])];
    updatedSkills.splice(index, 1);
    updateCourse({ skills: updatedSkills });
  };
  
  const addRequirement = () => {
    if (!newRequirement.trim()) return;
    
    const updatedRequirements = [...(courseData.requirements || []), newRequirement.trim()];
    updateCourse({ requirements: updatedRequirements });
    setNewRequirement('');
  };
  
  const removeRequirement = (index) => {
    const updatedRequirements = [...(courseData.requirements || [])];
    updatedRequirements.splice(index, 1);
    updateCourse({ requirements: updatedRequirements });
  };
  
  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-gray-200">
        <h2 className="text-2xl font-bold">Course Details</h2>
        <p className="text-gray-600 mt-1">
          Provide comprehensive information to showcase your course
        </p>
      </div>
      
      {errors.description && (
        <Alert type="error">
          {errors.description}
        </Alert>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Main details column */}
        <div className="md:col-span-2 space-y-4">
          <Card className="overflow-visible">
            <h3 className="font-medium mb-3">Course Description</h3>
            <div className="mb-4">
              <textarea
                value={description}
                onChange={handleDescriptionChange}
                placeholder="Enter course description"
                rows={10}
                className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-200 focus:border-primary-500"
              />
              <p className="mt-2 text-sm text-gray-500">
                Provide a detailed description of your course. Include what students will learn,
                your teaching approach, and why they should take your course.
              </p>
            </div>
          </Card>
          
          <Card className="overflow-visible">
            <h3 className="font-medium mb-3">What Students Will Learn</h3>
            <div className="space-y-3">
              <div className="flex space-x-2">
                <FormInput
                  id="new-skill"
                  placeholder="Add a learning outcome..."
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addSkill()}
                />
                <Button onClick={addSkill} variant="outlined" color="secondary">
                  Add
                </Button>
              </div>
              
              <div className="mt-3">
                {courseData.skills && courseData.skills.length > 0 ? (
                  <ul className="space-y-2">
                    {courseData.skills.map((skill, index) => (
                      <li key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                        <span>{skill}</span>
                        <button
                          type="button"
                          onClick={() => removeSkill(index)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-500 text-sm italic">
                    No learning outcomes added yet. Add at least 4-6 specific outcomes.
                  </p>
                )}
              </div>
            </div>
          </Card>
          
          <Card className="overflow-visible">
            <h3 className="font-medium mb-3">Prerequisites & Requirements</h3>
            <div className="space-y-3">
              <div className="flex space-x-2">
                <FormInput
                  id="new-requirement"
                  placeholder="Add a course requirement..."
                  value={newRequirement}
                  onChange={(e) => setNewRequirement(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addRequirement()}
                />
                <Button onClick={addRequirement} variant="outlined" color="secondary">
                  Add
                </Button>
              </div>
              
              <div className="mt-3">
                {courseData.requirements && courseData.requirements.length > 0 ? (
                  <ul className="space-y-2">
                    {courseData.requirements.map((requirement, index) => (
                      <li key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                        <span>{requirement}</span>
                        <button
                          type="button"
                          onClick={() => removeRequirement(index)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-500 text-sm italic">
                    No requirements added yet. Specify what students need to know before starting.
                  </p>
                )}
              </div>
            </div>
          </Card>
        </div>
        
        {/* Sidebar column */}
        <div className="space-y-4">
          <Card className="overflow-visible">
            <h3 className="font-medium mb-3">Pricing & Certificates</h3>
            
            <div className="mb-4">
              <FormInput
                label="Price (USD)"
                id="price"
                type="number"
                min="0"
                step="0.01"
                value={courseData.price || 0}
                onChange={(e) => updateCourse({ price: parseFloat(e.target.value) })}
                placeholder="e.g., 49.99"
              />
              <p className="mt-1 text-xs text-gray-500">
                Set your course's base price. You can add discounts later.
              </p>
            </div>
            
            <div className="mb-4">
              <FormInput
                label="Discount Price (Optional)"
                id="discount-price"
                type="number"
                min="0"
                step="0.01"
                value={courseData.discount_price || ''}
                onChange={(e) => {
                  const value = e.target.value ? parseFloat(e.target.value) : null;
                  updateCourse({ discount_price: value });
                }}
                placeholder="e.g., 39.99"
              />
              <p className="mt-1 text-xs text-gray-500">
                If you want to offer a discount, set the promotional price here.
              </p>
            </div>
            
            <div className="flex items-center mt-4">
              <input
                type="checkbox"
                id="has-certificate"
                checked={courseData.has_certificate || false}
                onChange={(e) => updateCourse({ has_certificate: e.target.checked })}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="has-certificate" className="ml-2 text-gray-700">
                Offer completion certificate
              </label>
            </div>
          </Card>
          
          <Card className="overflow-visible">
            <h3 className="font-medium mb-3">Course Timeline</h3>
            
            <div className="mb-4">
              <FormInput
                label="Estimated Duration"
                id="duration"
                value={courseData.duration || ''}
                onChange={(e) => updateCourse({ duration: e.target.value })}
                placeholder="e.g., 6 weeks, 10 hours"
                helperText="How long will it take to complete this course?"
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-gray-700 font-medium mb-1">Difficulty Level</label>
              <div className="flex flex-wrap gap-2">
                {['beginner', 'intermediate', 'advanced', 'all-levels'].map((level) => (
                  <button
                    key={level}
                    type="button"
                    className={`px-3 py-1.5 rounded-full text-sm ${
                      courseData.level === level
                        ? 'bg-primary-100 text-primary-800 border border-primary-300'
                        : 'bg-gray-100 text-gray-800 border border-gray-300'
                    }`}
                    onClick={() => updateCourse({ level })}
                  >
                    {level.charAt(0).toUpperCase() + level.slice(1).replace(/-/g, ' ')}
                  </button>
                ))}
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default CourseDetailsStep; 