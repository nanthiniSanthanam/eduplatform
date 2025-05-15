// fmt: off
// isort: skip_file
// Timestamp: 2024-06-15 - Fixed drag handle issues in Module Structure Step

import React, { useState } from 'react';
import { useCourseWizard } from '../CourseWizardContext';
// Direct imports to avoid casing issues
import Card from '../../../components/common/Card';
import Button from '../../../components/common/Button';
import FormInput from '../../../components/common/FormInput';
import Alert from '../../../components/common/Alert';
import Tooltip from '../../../components/common/Tooltip';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';

/**
 * Step 3: Module Structure
 * 
 * Allows instructors to build the structure of their course by:
 * - Adding modules 
 * - Organizing modules in a logical sequence
 * - Setting module titles, descriptions, and durations
 * - Reordering modules via drag and drop
 */
const ModuleStructureStep = () => {
  const { 
    modules, addModule, updateModule, removeModule, errors 
  } = useCourseWizard();
  
  const [isEditing, setIsEditing] = useState(null);
  const [editData, setEditData] = useState({
    title: '',
    description: '',
    duration: ''
  });
  
  // Handle drag and drop reordering
  const handleDragEnd = (result) => {
    if (!result.destination) return;
    
    const items = Array.from(modules);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);
    
    // Update the order of all modules
    items.forEach((module, index) => {
      updateModule(module.id, { order: index + 1 });
    });
  };
  
  // Start editing a module
  const handleEditModule = (module) => {
    setIsEditing(module.id);
    setEditData({
      title: module.title || '',
      description: module.description || '',
      duration: module.duration || ''
    });
  };
  
  // Save module edits
  const handleSaveModule = () => {
    if (!editData.title) return;
    
    updateModule(isEditing, editData);
    setIsEditing(null);
    setEditData({ title: '', description: '', duration: '' });
  };
  
  // Create a new module
  const handleCreateModule = () => {
    const newModuleId = addModule({
      title: 'New Module',
      description: '',
      duration: '',
      order: modules.length + 1
    });
    
    handleEditModule({ id: newModuleId, title: 'New Module', description: '', duration: '' });
  };
  
  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-gray-200">
        <h2 className="text-2xl font-bold">Course Structure</h2>
        <p className="text-gray-600 mt-1">
          Organize your course by creating modules to group related content
        </p>
      </div>
      
      {errors.modules && (
        <Alert type="error">
          {errors.modules}
        </Alert>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Module list */}
        <div className="md:col-span-2">
          {modules.length > 0 ? (
            <DragDropContext onDragEnd={handleDragEnd}>
              <Droppable droppableId="modules">
                {(provided) => (
                  <div
                    {...provided.droppableProps}
                    ref={provided.innerRef}
                    className="space-y-4"
                  >
                    {modules
                      .sort((a, b) => a.order - b.order)
                      .map((module, index) => (
                        <Draggable
                          key={module.id}
                          draggableId={String(module.id)}
                          index={index}
                        >
                          {(provided) => (
                            <div
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              className="border rounded-lg overflow-hidden bg-white shadow-sm"
                            >
                              {isEditing === module.id ? (
                                // Edit mode
                                <div className="p-4">
                                  <FormInput
                                    label="Module Title"
                                    value={editData.title}
                                    onChange={(e) => setEditData({ ...editData, title: e.target.value })}
                                    placeholder="Enter module title"
                                    required
                                  />
                                  
                                  <div className="form-group mt-3">
                                    <label className="block text-gray-700 font-medium mb-1">
                                      Description
                                    </label>
                                    <textarea
                                      rows={3}
                                      className="w-full p-2 border border-gray-300 rounded-md"
                                      value={editData.description}
                                      onChange={(e) => setEditData({ ...editData, description: e.target.value })}
                                      placeholder="Enter module description"
                                    />
                                  </div>
                                  
                                  <FormInput
                                    label="Estimated Duration"
                                    value={editData.duration}
                                    onChange={(e) => setEditData({ ...editData, duration: e.target.value })}
                                    placeholder="e.g., 2 hours"
                                    className="mt-3"
                                  />
                                  
                                  <div className="flex justify-end mt-3 space-x-2">
                                    <Button
                                      color="secondary"
                                      onClick={() => setIsEditing(null)}
                                      variant="outlined"
                                    >
                                      Cancel
                                    </Button>
                                    <Button
                                      color="primary"
                                      onClick={handleSaveModule}
                                      disabled={!editData.title}
                                    >
                                      Save Module
                                    </Button>
                                  </div>
                                </div>
                              ) : (
                                // View mode
                                <div>
                                  {/* Header with drag handle */}
                                  <div 
                                    className="bg-gray-50 p-4 flex items-center justify-between"
                                    {...provided.dragHandleProps} 
                                  >
                                    <div className="flex items-center">
                                      <div className="flex-shrink-0 mr-3 text-gray-400">
                                        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8h16M4 16h16" />
                                        </svg>
                                      </div>
                                      <h3 className="font-medium">
                                        {index + 1}. {module.title || 'Untitled Module'}
                                      </h3>
                                    </div>
                                    <div className="flex space-x-1">
                                      <button
                                        onClick={() => handleEditModule(module)}
                                        className="p-1 text-gray-500 hover:text-gray-700"
                                        aria-label="Edit module"
                                      >
                                        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                        </svg>
                                      </button>
                                      <button
                                        onClick={() => removeModule(module.id)}
                                        className="p-1 text-gray-500 hover:text-red-500"
                                        aria-label="Remove module"
                                      >
                                        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                        </svg>
                                      </button>
                                    </div>
                                  </div>
                                  
                                  {/* Module content */}
                                  <div className="p-4">
                                    {module.description ? (
                                      <p className="text-gray-600 text-sm mb-2">{module.description}</p>
                                    ) : (
                                      <p className="text-gray-400 text-sm italic mb-2">No description provided</p>
                                    )}
                                    
                                    {module.duration && (
                                      <div className="flex items-center text-sm text-gray-500">
                                        <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        {module.duration}
                                      </div>
                                    )}
                                    
                                    {module.lessons && module.lessons.length > 0 && (
                                      <div className="mt-3 text-sm">
                                        <p className="text-gray-500">
                                          {module.lessons.length} lesson{module.lessons.length !== 1 ? 's' : ''} in this module
                                        </p>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </Draggable>
                      ))}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            </DragDropContext>
          ) : (
            <div className="text-center py-12 bg-gray-50 rounded-lg border border-dashed border-gray-300">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No modules yet</h3>
              <p className="mt-1 text-sm text-gray-500">Get started by creating your first module.</p>
              <div className="mt-6">
                <Button color="primary" onClick={handleCreateModule}>
                  <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Create Module
                </Button>
              </div>
            </div>
          )}
        </div>
        
        {/* Tips and actions column */}
        <div className="space-y-4">
          <Card>
            <h3 className="font-medium mb-3">Module Structure Tips</h3>
            <ul className="space-y-3 text-sm text-gray-600">
              <li className="flex items-start">
                <svg className="h-5 w-5 text-green-500 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Group related content into modules (chapters)</span>
              </li>
              <li className="flex items-start">
                <svg className="h-5 w-5 text-green-500 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Aim for 3-7 modules in a typical course</span>
              </li>
              <li className="flex items-start">
                <svg className="h-5 w-5 text-green-500 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Use clear, descriptive module titles</span>
              </li>
              <li className="flex items-start">
                <svg className="h-5 w-5 text-green-500 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Arrange modules in a logical sequence</span>
              </li>
              <li className="flex items-start">
                <svg className="h-5 w-5 text-green-500 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Drag and drop to reorder modules</span>
              </li>
            </ul>
          </Card>
          
          <div className="sticky top-4">
            <Button
              color="primary"
              className="w-full mb-3"
              onClick={handleCreateModule}
            >
              <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add New Module
            </Button>
            
            {modules.length > 0 && (
              <Tooltip content="You'll add lessons to your modules in the next step">
                <p className="text-sm text-center text-gray-500">
                  {modules.length} module{modules.length !== 1 ? 's' : ''} added
                </p>
              </Tooltip>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModuleStructureStep; 