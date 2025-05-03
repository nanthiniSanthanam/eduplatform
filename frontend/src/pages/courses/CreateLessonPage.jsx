import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import instructorService from "../../services/instructorService";
import { Editor } from '@tinymce/tinymce-react';
import {
  FormInput,
  Button,
  Card,
  Alert,
  Container,
  Tabs
} from '../../components/common';

const CreateLessonPage = () => {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const { courseSlug, moduleId } = useParams();
  
  // Form state
  const [title, setTitle] = useState('');
  const [type, setType] = useState('video');
  const [content, setContent] = useState('');
  const [basicContent, setBasicContent] = useState('');
  const [intermediateContent, setIntermediateContent] = useState('');
  const [accessLevel, setAccessLevel] = useState('intermediate');
  const [duration, setDuration] = useState('');
  const [order, setOrder] = useState(1);
  const [hasAssessment, setHasAssessment] = useState(false);
  const [hasLab, setHasLab] = useState(false);
  const [isFreePreview, setIsFreePreview] = useState(false);
  
  // Resources state
  const [resources, setResources] = useState([]);
  const [newResource, setNewResource] = useState({
    title: '',
    type: 'Document',
    description: '',
    file: null,
    url: '',
    premium: false
  });
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [currentTab, setCurrentTab] = useState('basic');
  const [moduleDetails, setModuleDetails] = useState(null);
  const [courseDetails, setCourseDetails] = useState(null);
  
  // Fetch module details
  useEffect(() => {
    const fetchModuleDetails = async () => {
      try {
        setLoading(true);
        const response = await instructorService.getModule(moduleId);
        setModuleDetails(response.data);
        
        // Get existing lessons to determine order
        const lessonsResponse = await instructorService.getLessons(moduleId);
        setOrder(lessonsResponse.data.length + 1);
        
        setLoading(false);
      } catch (error) {
        setError("Failed to load module details");
        setLoading(false);
      }
    };
    
    fetchModuleDetails();
  }, [moduleId]);
  
  // Check if the user is an instructor
  useEffect(() => {
    if (currentUser && currentUser.role !== 'instructor' && currentUser.role !== 'administrator') {
      navigate('/forbidden');
    }
  }, [currentUser, navigate]);
  
  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!title || !content) {
      setError("Title and content are required.");
      return;
    }
    
    try {
      setLoading(true);
      
      // Prepare lesson data
      const lessonData = {
        module: moduleId,
        title,
        content,
        basic_content: basicContent || undefined,
        intermediate_content: intermediateContent || undefined,
        access_level: accessLevel,
        duration,
        type,
        order,
        has_assessment: hasAssessment,
        has_lab: hasLab,
        is_free_preview: isFreePreview,
      };
      
      // Create the lesson
      const response = await instructorService.createLesson(lessonData);
      const newLessonId = response.data.id;
      
      // Upload resources if any
      if (resources.length > 0 && newLessonId) {
        await Promise.all(resources.map(async (resource) => {
          const formData = new FormData();
          formData.append('lesson', newLessonId);
          formData.append('title', resource.title);
          formData.append('type', resource.type);
          formData.append('description', resource.description);
          formData.append('premium', resource.premium);
          
          if (resource.file) {
            formData.append('file', resource.file);
          }
          
          if (resource.url) {
            formData.append('url', resource.url);
          }
          
          return instructorService.createResource(formData);
        }));
      }
      
      // Create assessment if needed
      if (hasAssessment) {
        await instructorService.createAssessment({
          lesson: newLessonId,
          title: `${title} Assessment`,
          description: `Assessment for ${title}`,
          time_limit: 0, // No time limit by default
          passing_score: 70 // Default passing score
        });
      }
      
      setSuccess(true);
      // Redirect after successful creation
      setTimeout(() => {
        navigate(`/instructor/modules/${moduleId}/lessons`);
      }, 2000);
      
    } catch (error) {
      console.error("Error creating lesson:", error);
      setError(error.message || "Failed to create lesson");
    } finally {
      setLoading(false);
    }
  };
  
  // Handle adding a new resource
  const handleAddResource = () => {
    if (!newResource.title || (!newResource.file && !newResource.url)) {
      setError("Resource title and either file or URL are required.");
      return;
    }
    
    setResources([...resources, { ...newResource, id: Date.now() }]);
    setNewResource({
      title: '',
      type: 'Document',
      description: '',
      file: null,
      url: '',
      premium: false
    });
  };
  
  // Handle removing a resource
  const handleRemoveResource = (resourceId) => {
    setResources(resources.filter(resource => resource.id !== resourceId));
  };
  
  // Handle file selection
  const handleFileChange = (e) => {
    setNewResource({ ...newResource, file: e.target.files[0] });
  };

  return (
    <div className="py-8">
      <Container>
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Create New Lesson</h1>
          {moduleDetails && (
            <p className="text-gray-600">
              Adding lesson to module: <strong>{moduleDetails.title}</strong>
            </p>
          )}
        </div>
        
        {error && (
          <Alert type="error" className="mb-6">
            {error}
          </Alert>
        )}
        
        {success && (
          <Alert type="success" className="mb-6">
            Lesson created successfully! Redirecting...
          </Alert>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Main lesson details column */}
            <div className="md:col-span-2 space-y-6">
              <Card className="overflow-visible">
                <h2 className="text-xl font-semibold mb-4">Basic Information</h2>
                
                <FormInput
                  label="Lesson Title"
                  id="lesson-title"
                  name="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                />
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <FormInput
                    label="Estimated Duration"
                    id="duration"
                    name="duration"
                    value={duration}
                    onChange={(e) => setDuration(e.target.value)}
                    placeholder="e.g., 15 minutes"
                  />
                  
                  <FormInput
                    label="Order in Module"
                    id="order"
                    name="order"
                    type="number"
                    min="1"
                    value={order}
                    onChange={(e) => setOrder(parseInt(e.target.value))}
                  />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="form-group">
                    <label className="block text-gray-700 font-medium mb-1">
                      Lesson Type
                    </label>
                    <select
                      className="w-full p-2 border border-gray-300 rounded-md"
                      value={type}
                      onChange={(e) => setType(e.target.value)}
                    >
                      <option value="video">Video</option>
                      <option value="reading">Reading</option>
                      <option value="interactive">Interactive</option>
                      <option value="quiz">Quiz</option>
                      <option value="lab">Lab Exercise</option>
                    </select>
                  </div>
                  
                  <div className="form-group">
                    <label className="block text-gray-700 font-medium mb-1">
                      Access Level
                    </label>
                    <select
                      className="w-full p-2 border border-gray-300 rounded-md"
                      value={accessLevel}
                      onChange={(e) => setAccessLevel(e.target.value)}
                    >
                      <option value="basic">Basic (Unregistered Users)</option>
                      <option value="intermediate">Intermediate (Registered Users)</option>
                      <option value="advanced">Advanced (Paid Users)</option>
                    </select>
                  </div>
                </div>
                
                <div className="mt-4 space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={isFreePreview}
                      onChange={(e) => setIsFreePreview(e.target.checked)}
                      className="mr-2"
                    />
                    <span>Free Preview (Available to all visitors)</span>
                  </label>
                  
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={hasAssessment}
                      onChange={(e) => setHasAssessment(e.target.checked)}
                      className="mr-2"
                    />
                    <span>Include Assessment</span>
                  </label>
                  
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={hasLab}
                      onChange={(e) => setHasLab(e.target.checked)}
                      className="mr-2"
                    />
                    <span>Include Lab Exercise</span>
                  </label>
                </div>
              </Card>
              
              <Card className="overflow-visible">
                <h2 className="text-xl font-semibold mb-4">Lesson Content</h2>
                
                <Tabs
                  tabs={[
                    { id: 'basic', label: 'Basic Content' },
                    { id: 'intermediate', label: 'Intermediate Content' },
                    { id: 'advanced', label: 'Full Content' }
                  ]}
                  activeTab={currentTab}
                  onChange={setCurrentTab}
                />
                
                <div className="mt-4">
                  {currentTab === 'basic' && (
                    <div>
                      <p className="text-sm text-gray-500 mb-2">
                        Basic content is visible to all visitors, including those who are not logged in.
                      </p>
                      <Editor
                        apiKey="your-tinymce-api-key"
                        value={basicContent}
                        onEditorChange={(content) => setBasicContent(content)}
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
                      />
                    </div>
                  )}
                  
                  {currentTab === 'intermediate' && (
                    <div>
                      <p className="text-sm text-gray-500 mb-2">
                        Intermediate content is visible to registered users (free tier).
                      </p>
                      <Editor
                        apiKey="your-tinymce-api-key"
                        value={intermediateContent}
                        onEditorChange={(content) => setIntermediateContent(content)}
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
                      />
                    </div>
                  )}
                  
                  {currentTab === 'advanced' && (
                    <div>
                      <p className="text-sm text-gray-500 mb-2">
                        Full content is visible to paid subscribers.
                      </p>
                      <Editor
                        apiKey="your-tinymce-api-key"
                        value={content}
                        onEditorChange={(content) => setContent(content)}
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
                      />
                    </div>
                  )}
                </div>
              </Card>
            </div>
            
            {/* Sidebar column */}
            <div className="space-y-6">
              <Card>
                <h2 className="text-xl font-semibold mb-4">Resources</h2>
                
                {/* Resource list */}
                {resources.length > 0 ? (
                  <ul className="mb-4 space-y-2">
                    {resources.map((resource) => (
                      <li key={resource.id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <div>
                          <p className="font-medium">{resource.title}</p>
                          <p className="text-sm text-gray-600">{resource.type}</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleRemoveResource(resource.id)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                          </svg>
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-500 italic mb-4">No resources added yet.</p>
                )}
                
                {/* Add resource form */}
                <div className="border-t pt-4">
                  <h3 className="font-medium mb-2">Add Resource</h3>
                  
                  <FormInput
                    label="Resource Title"
                    id="resource-title"
                    value={newResource.title}
                    onChange={(e) => setNewResource({ ...newResource, title: e.target.value })}
                  />
                  
                  <div className="mb-4">
                    <label className="block text-gray-700 font-medium mb-1">
                      Resource Type
                    </label>
                    <select
                      className="w-full p-2 border border-gray-300 rounded-md"
                      value={newResource.type}
                      onChange={(e) => setNewResource({ ...newResource, type: e.target.value })}
                    >
                      <option value="Document">Document</option>
                      <option value="Video">Video</option>
                      <option value="External Link">External Link</option>
                      <option value="Code Sample">Code Sample</option>
                      <option value="Tool/Software">Tool/Software</option>
                    </select>
                  </div>
                  
                  {newResource.type === 'External Link' ? (
                    <FormInput
                      label="URL"
                      id="resource-url"
                      value={newResource.url}
                      onChange={(e) => setNewResource({ ...newResource, url: e.target.value })}
                      placeholder="https://"
                    />
                  ) : (
                    <div className="mb-4">
                      <label className="block text-gray-700 font-medium mb-1">
                        File
                      </label>
                      <input
                        type="file"
                        onChange={handleFileChange}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      />
                    </div>
                  )}
                  
                  <FormInput
                    label="Description (optional)"
                    id="resource-description"
                    value={newResource.description}
                    onChange={(e) => setNewResource({ ...newResource, description: e.target.value })}
                  />
                  
                  <label className="flex items-center mb-4">
                    <input
                      type="checkbox"
                      checked={newResource.premium}
                      onChange={(e) => setNewResource({ ...newResource, premium: e.target.checked })}
                      className="mr-2"
                    />
                    <span>Premium Resource (Paid subscribers only)</span>
                  </label>
                  
                  <Button
                    type="button"
                    variant="outlined"
                    color="primary"
                    onClick={handleAddResource}
                    className="w-full"
                  >
                    Add Resource
                  </Button>
                </div>
              </Card>
              
              <Card>
                <h2 className="text-xl font-semibold mb-4">Actions</h2>
                
                <div className="space-y-4">
                  <Button
                    type="submit"
                    variant="contained"
                    color="primary"
                    className="w-full"
                    disabled={loading}
                  >
                    {loading ? 'Creating Lesson...' : 'Create Lesson'}
                  </Button>
                  
                  <Button
                    type="button"
                    variant="outlined"
                    color="secondary"
                    className="w-full"
                    onClick={() => navigate(-1)}
                  >
                    Cancel
                  </Button>
                </div>
              </Card>
            </div>
          </div>
        </form>
      </Container>
    </div>
  );
};

export default CreateLessonPage;