// fmt: off
// isort: skip_file
// Timestamp: 2024-06-15 - Content Creation Step (Step 4) of Course Creation Wizard

import React, { useState } from 'react';
import { useCourseWizard } from '../CourseWizardContext';
// Direct imports to avoid casing issues
import Card from '../../../components/common/Card';
import Button from '../../../components/common/Button';
import Alert from '../../../components/common/Alert';
import FormInput from '../../../components/common/FormInput';
import Tabs from '../../../components/common/Tabs';
import { Editor } from '@tinymce/tinymce-react';

/**
 * Step 4: Content Creation
 * 
 * Allows instructors to add lessons to each module:
 * - Create lessons with tiered content (basic/intermediate/advanced)
 * - Set access levels for different tiers
 * - Add lesson details like duration and type
 */
const ContentCreationStep = () => {
  const { modules, errors, addLesson, updateLesson, removeLesson } = useCourseWizard();
  const [selectedModule, setSelectedModule] = useState(modules.length > 0 ? modules[0].id : null);
  const [editingLesson, setEditingLesson] = useState(null);
  const [lessonForm, setLessonForm] = useState({
    title: '',
    duration: '',
    type: 'video',
    content: '', // Advanced (paid) content
    basic_content: '', // Basic preview content
    intermediate_content: '', // Registered user content
    access_level: 'intermediate',
    is_free_preview: false
  });
  
  // Access level options based on backend model
  const accessLevelOptions = [
    { value: 'basic', label: 'Basic - Preview for Unregistered Users' },
    { value: 'intermediate', label: 'Intermediate - Registered Users' },
    { value: 'advanced', label: 'Advanced - Paid Users Only' }
  ];

  const lessonTypeOptions = [
    { value: 'video', label: 'Video' },
    { value: 'reading', label: 'Reading Material' },
    { value: 'interactive', label: 'Interactive Content' },
    { value: 'quiz', label: 'Quiz' },
    { value: 'lab', label: 'Lab Exercise' }
  ];
  
  // Handle form changes
  const handleFormChange = (field, value) => {
    setLessonForm({
      ...lessonForm,
      [field]: value
    });
  };
  
  // Handle editor content changes
  const handleEditorChange = (field, content) => {
    setLessonForm({
      ...lessonForm,
      [field]: content
    });
  };
  
  // Reset the form
  const resetForm = () => {
    setLessonForm({
      title: '',
      duration: '',
      type: 'video',
      content: '',
      basic_content: '',
      intermediate_content: '',
      access_level: 'intermediate',
      is_free_preview: false
    });
    setEditingLesson(null);
  };
  
  // Save lesson
  const handleSaveLesson = () => {
    if (!lessonForm.title) return;
    
    const module = modules.find(m => m.id === selectedModule);
    if (!module) return;
    
    const lessonData = {
      ...lessonForm,
      order: module.lessons ? module.lessons.length + 1 : 1
    };
    
    if (editingLesson) {
      // Update existing lesson
      updateLesson(selectedModule, editingLesson, lessonData);
    } else {
      // Create new lesson
      addLesson(selectedModule, lessonData);
    }
    
    resetForm();
  };
  
  // Edit a lesson
  const handleEditLesson = (lesson) => {
    setEditingLesson(lesson.id);
    setLessonForm({
      title: lesson.title || '',
      duration: lesson.duration || '',
      type: lesson.type || 'video',
      content: lesson.content || '',
      basic_content: lesson.basic_content || '',
      intermediate_content: lesson.intermediate_content || '',
      access_level: lesson.access_level || 'intermediate',
      is_free_preview: lesson.is_free_preview || false
    });
  };
  
  // Delete a lesson
  const handleDeleteLesson = (lessonId) => {
    if (window.confirm('Are you sure you want to delete this lesson?')) {
      removeLesson(selectedModule, lessonId);
      if (editingLesson === lessonId) {
        resetForm();
      }
    }
  };
  
  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-gray-200">
        <h2 className="text-2xl font-bold">Content Creation</h2>
        <p className="text-gray-600 mt-1">
          Add lessons, content tiers, and resources to your modules
        </p>
      </div>
      
      {errors.lessons && (
        <Alert type="error">
          {errors.lessons}
        </Alert>
      )}
      
      {modules.length === 0 ? (
        <Alert type="warning">
          You need to create modules first before adding content. Please go back to the previous step.
        </Alert>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Left panel - Module selector and lessons list */}
          <div className="md:col-span-1 space-y-4">
            <Card>
              <h3 className="font-medium mb-3">Modules</h3>
              <div className="space-y-2">
                {modules.map(module => (
                  <button
                    key={module.id}
                    onClick={() => setSelectedModule(module.id)}
                    className={`w-full text-left p-3 rounded-md ${
                      selectedModule === module.id 
                        ? 'bg-primary-50 border border-primary-200' 
                        : 'bg-gray-50 hover:bg-gray-100'
                    }`}
                  >
                    <div className="font-medium">{module.title}</div>
                    <div className="text-sm text-gray-500">
                      {module.lessons && module.lessons.length > 0 
                        ? `${module.lessons.length} lessons` 
                        : 'No lessons yet'}
                    </div>
                  </button>
                ))}
              </div>
            </Card>
            
            {selectedModule && (
              <Card>
                <div className="flex justify-between items-center mb-3">
                  <h3 className="font-medium">Lessons</h3>
                  <Button 
                    color="primary" 
                    size="small"
                    onClick={() => {
                      resetForm();
                      setEditingLesson(null);
                    }}
                  >
                    + Add Lesson
                  </Button>
                </div>
                
                {modules.find(m => m.id === selectedModule)?.lessons?.length > 0 ? (
                  <div className="space-y-2">
                    {modules
                      .find(m => m.id === selectedModule)
                      .lessons
                      .sort((a, b) => a.order - b.order)
                      .map(lesson => (
                        <div 
                          key={lesson.id}
                          className={`p-3 rounded-md border ${
                            editingLesson === lesson.id 
                              ? 'border-primary-300 bg-primary-50' 
                              : 'border-gray-200'
                          }`}
                        >
                          <div className="flex justify-between">
                            <div>
                              <div className="font-medium">{lesson.title}</div>
                              <div className="text-sm text-gray-500">
                                {lesson.type} {lesson.duration && `• ${lesson.duration}`}
                              </div>
                              {lesson.is_free_preview && (
                                <span className="text-xs bg-green-100 text-green-800 rounded-full px-2 py-0.5 mt-1 inline-block">
                                  Free Preview
                                </span>
                              )}
                            </div>
                            <div className="flex space-x-1">
                              <button
                                onClick={() => handleEditLesson(lesson)}
                                className="p-1 text-gray-500 hover:text-primary-500"
                              >
                                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                              </button>
                              <button
                                onClick={() => handleDeleteLesson(lesson.id)}
                                className="p-1 text-gray-500 hover:text-red-500"
                              >
                                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                  </div>
                ) : (
                  <div className="text-center py-6 text-gray-500">
                    No lessons created yet
                  </div>
                )}
              </Card>
            )}
          </div>
          
          {/* Right panel - Lesson editor */}
          <div className="md:col-span-2">
            {selectedModule ? (
              <Card>
                <h3 className="font-medium mb-4">
                  {editingLesson ? 'Edit Lesson' : 'Create New Lesson'}
                </h3>
                
                <div className="space-y-4">
                  <FormInput
                    label="Lesson Title"
                    id="lesson-title"
                    value={lessonForm.title}
                    onChange={(e) => handleFormChange('title', e.target.value)}
                    placeholder="Enter lesson title"
                    required
                  />
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-gray-700 font-medium mb-1">Lesson Type</label>
                      <select
                        value={lessonForm.type}
                        onChange={(e) => handleFormChange('type', e.target.value)}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      >
                        {lessonTypeOptions.map(option => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    
                    <FormInput
                      label="Duration"
                      id="lesson-duration"
                      value={lessonForm.duration}
                      onChange={(e) => handleFormChange('duration', e.target.value)}
                      placeholder="e.g., 15 minutes"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-gray-700 font-medium mb-1">Access Level</label>
                    <select
                      value={lessonForm.access_level}
                      onChange={(e) => handleFormChange('access_level', e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    >
                      {accessLevelOptions.map(option => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                    <p className="mt-1 text-sm text-gray-500">
                      Determines which users can access this lesson
                    </p>
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="is_free_preview"
                      checked={lessonForm.is_free_preview}
                      onChange={(e) => handleFormChange('is_free_preview', e.target.checked)}
                      className="h-4 w-4 text-primary-600 border-gray-300 rounded"
                    />
                    <label htmlFor="is_free_preview" className="ml-2 text-gray-700">
                      Make this a free preview lesson (available to all users)
                    </label>
                  </div>
                  
                  {/* Tiered content editors */}
                  <div className="mt-4">
                    <Tabs
                      tabs={[
                        { id: 'advanced', label: 'Advanced Content' },
                        { id: 'intermediate', label: 'Intermediate Content' },
                        { id: 'basic', label: 'Basic Content' }
                      ]}
                    >
                      <Tabs.Panel id="advanced">
                        <div className="mb-2">
                          <div className="flex justify-between mb-1">
                            <label className="block text-gray-700 font-medium">
                              Advanced Content (Premium Users)
                            </label>
                          </div>
                          <Editor
                            apiKey="your-tinymce-api-key" // Replace with your TinyMCE API key
                            value={lessonForm.content}
                            init={{
                              height: 300,
                              menubar: false,
                              plugins: [
                                'advlist autolink lists link image charmap print preview anchor',
                                'searchreplace visualblocks code fullscreen',
                                'insertdatetime media table paste code help wordcount'
                              ],
                              toolbar:
                                'undo redo | formatselect | bold italic backcolor | \
                                alignleft aligncenter alignright alignjustify | \
                                bullist numlist outdent indent | removeformat | help'
                            }}
                            onEditorChange={(content) => handleEditorChange('content', content)}
                          />
                        </div>
                      </Tabs.Panel>
                      
                      <Tabs.Panel id="intermediate">
                        <div className="mb-2">
                          <div className="flex justify-between mb-1">
                            <label className="block text-gray-700 font-medium">
                              Intermediate Content (Registered Users)
                            </label>
                          </div>
                          <Editor
                            apiKey="your-tinymce-api-key"
                            value={lessonForm.intermediate_content}
                            init={{
                              height: 300,
                              menubar: false,
                              plugins: [
                                'advlist autolink lists link image charmap print preview anchor',
                                'searchreplace visualblocks code fullscreen',
                                'insertdatetime media table paste code help wordcount'
                              ],
                              toolbar:
                                'undo redo | formatselect | bold italic backcolor | \
                                alignleft aligncenter alignright alignjustify | \
                                bullist numlist outdent indent | removeformat | help'
                            }}
                            onEditorChange={(content) => handleEditorChange('intermediate_content', content)}
                          />
                        </div>
                      </Tabs.Panel>
                      
                      <Tabs.Panel id="basic">
                        <div className="mb-2">
                          <div className="flex justify-between mb-1">
                            <label className="block text-gray-700 font-medium">
                              Basic Content (Preview for All Users)
                            </label>
                          </div>
                          <Editor
                            apiKey="your-tinymce-api-key"
                            value={lessonForm.basic_content}
                            init={{
                              height: 300,
                              menubar: false,
                              plugins: [
                                'advlist autolink lists link image charmap print preview anchor',
                                'searchreplace visualblocks code fullscreen',
                                'insertdatetime media table paste code help wordcount'
                              ],
                              toolbar:
                                'undo redo | formatselect | bold italic backcolor | \
                                alignleft aligncenter alignright alignjustify | \
                                bullist numlist outdent indent | removeformat | help'
                            }}
                            onEditorChange={(content) => handleEditorChange('basic_content', content)}
                          />
                        </div>
                      </Tabs.Panel>
                    </Tabs>
                  </div>
                  
                  <div className="flex justify-end space-x-3 mt-6">
                    <Button
                      variant="outlined"
                      color="secondary"
                      onClick={resetForm}
                    >
                      Cancel
                    </Button>
                    
                    <Button
                      variant="contained"
                      color="primary"
                      disabled={!lessonForm.title}
                      onClick={handleSaveLesson}
                    >
                      {editingLesson ? 'Update Lesson' : 'Add Lesson'}
                    </Button>
                  </div>
                </div>
              </Card>
            ) : (
              <Card>
                <div className="text-center py-10">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">Select a module</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Choose a module from the list to add or edit lessons
                  </p>
                </div>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ContentCreationStep; 