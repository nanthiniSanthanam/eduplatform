// fmt: off
// isort: skip_file
// Timestamp: 2024-06-15 - Course Basics Step (Step 1) of Course Creation Wizard

import React, { useState, useEffect } from 'react';
import { useCourseWizard } from '../CourseWizardContext';
// Direct imports to avoid casing issues
import FormInput from '../../../components/common/FormInput';
import Card from '../../../components/common/Card';
import Tooltip from '../../../components/common/Tooltip';
import { categoryService } from '../../../services/api';

/**
 * Step 1: Course Basics
 * 
 * Captures the essential information needed to create a course:
 * - Course title (required)
 * - Course subtitle
 * - Category (required)
 * - Level (beginner, intermediate, advanced)
 * - Thumbnail image
 */
const CourseBasicsStep = () => {
  const { courseData, updateCourse, errors } = useCourseWizard();
  const [categories, setCategories] = useState([]);
  const [imagePreview, setImagePreview] = useState(null);
  
  // Fetch categories
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const data = await categoryService.getAllCategories();
        setCategories(data || []);
      } catch (error) {
        console.error('Failed to fetch categories:', error);
      }
    };
    
    fetchCategories();
  }, []);
  
  // Handle image upload
  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    updateCourse({ thumbnail: file });
    
    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result);
    };
    reader.readAsDataURL(file);
  };
  
  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-gray-200">
        <h2 className="text-2xl font-bold">Course Basics</h2>
        <p className="text-gray-600 mt-1">
          Start with the fundamental information about your course
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Main course information column */}
        <div className="md:col-span-2 space-y-4">
          <FormInput
            label="Course Title"
            id="course-title"
            value={courseData.title || ''}
            onChange={e => updateCourse({ title: e.target.value })}
            error={errors.title}
            required
            placeholder="e.g., Complete Web Development Bootcamp"
            maxLength={100}
            helpText="Clear, specific titles perform better. (max 100 characters)"
          />
          
          <FormInput
            label="Course Subtitle"
            id="course-subtitle"
            value={courseData.subtitle || ''}
            onChange={e => updateCourse({ subtitle: e.target.value })}
            error={errors.subtitle}
            placeholder="e.g., Learn HTML, CSS, JavaScript, React, Node.js and more!"
            maxLength={150}
            helpText="A brief, compelling description of what students will learn. (max 150 characters)"
          />
          
          <div className="form-group">
            <label htmlFor="category" className="block text-gray-700 font-medium mb-1">
              Category <span className="text-red-500">*</span>
            </label>
            <select
              id="category"
              value={courseData.category_id || ''}
              onChange={e => updateCourse({ category_id: e.target.value })}
              className={`w-full p-3 rounded-md border ${errors.category ? 'border-red-500' : 'border-gray-300'}`}
              aria-invalid={!!errors.category}
            >
              <option value="">Select a category</option>
              {categories.map(category => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
            {errors.category && (
              <p className="mt-1 text-sm text-red-500">{errors.category}</p>
            )}
            <p className="mt-1 text-sm text-gray-500">Choose the most specific category that fits your course</p>
          </div>
          
          <div className="form-group">
            <label htmlFor="level" className="block text-gray-700 font-medium mb-1">
              Course Level
            </label>
            <select
              id="level"
              value={courseData.level || 'beginner'}
              onChange={e => updateCourse({ level: e.target.value })}
              className="w-full p-3 rounded-md border border-gray-300"
            >
              <option value="beginner">Beginner - No experience required</option>
              <option value="intermediate">Intermediate - Some knowledge expected</option>
              <option value="advanced">Advanced - Experienced learners</option>
              <option value="all-levels">All Levels - Suitable for everyone</option>
            </select>
            <p className="mt-1 text-sm text-gray-500">Setting the right level helps students find your course</p>
          </div>
        </div>
        
        {/* Thumbnail column */}
        <div className="space-y-4">
          <Card className="p-4 overflow-visible">
            <h3 className="font-medium mb-2">Course Thumbnail</h3>
            <p className="text-sm text-gray-600 mb-4">
              Upload an eye-catching image that represents your course (16:9 ratio recommended)
            </p>
            
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center mb-4">
              {imagePreview || courseData.thumbnail ? (
                <div className="relative">
                  <img 
                    src={imagePreview || (typeof courseData.thumbnail === 'string' ? courseData.thumbnail : null)} 
                    alt="Thumbnail preview" 
                    className="mx-auto max-h-40 object-contain"
                  />
                  <button 
                    type="button"
                    onClick={() => {
                      updateCourse({ thumbnail: null });
                      setImagePreview(null);
                    }}
                    className="absolute top-0 right-0 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center"
                  >
                    ×
                  </button>
                </div>
              ) : (
                <div className="py-8">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <p className="mt-2 text-sm text-gray-500">PNG, JPG, or GIF</p>
                </div>
              )}
              
              <input
                type="file"
                id="thumbnail"
                accept="image/*"
                onChange={handleImageChange}
                className="hidden"
              />
              <label
                htmlFor="thumbnail"
                className="mt-2 inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 cursor-pointer"
              >
                {imagePreview || courseData.thumbnail ? 'Change Image' : 'Upload Image'}
              </label>
            </div>
            
            <div className="bg-blue-50 p-3 rounded-lg">
              <h4 className="text-blue-700 font-medium text-sm mb-1">Thumbnail Tips</h4>
              <ul className="text-xs text-blue-700 list-disc list-inside">
                <li>Use high-quality, vibrant images</li>
                <li>Avoid too much text in the image</li>
                <li>Keep it simple and clear</li>
                <li>Recommended size: 1280×720 pixels</li>
              </ul>
            </div>
          </Card>
          
          <Tooltip content="Featured courses appear on the homepage and get more visibility">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="is-featured"
                checked={courseData.is_featured || false}
                onChange={e => updateCourse({ is_featured: e.target.checked })}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="is-featured" className="ml-2 text-gray-700">
                Request featured placement
              </label>
            </div>
          </Tooltip>
        </div>
      </div>
    </div>
  );
};

export default CourseBasicsStep; 