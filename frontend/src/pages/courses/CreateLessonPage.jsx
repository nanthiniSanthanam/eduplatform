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
                  onChange={e => setTitle(e.target.value)}
                  required
                  placeholder="e.g., Introduction to Testing"
                />
                <FormInput
                  label="Order"
                  id="order"
                  name="order"
                  type="number"
                  value={order}
                  onChange={e => setOrder(Number(e.target.value))}
                  required
                  placeholder="1"
                />
                <FormInput
                  label="Duration"
                  id="duration"
                  name="duration"
                  value={duration}
                  onChange={e => setDuration(e.target.value)}
                  placeholder="e.g., 30 min"
                />
                <div className="form-group">
                  <label htmlFor="type" className="block text-gray-700 font-medium mb-1">Lesson Type</label>
                  <select
                    id="type"
                    value={type}
                    onChange={e => setType(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  >
                    <option value="video">Video</option>
                    <option value="reading">Reading</option>
                    <option value="interactive">Interactive</option>
                    <option value="quiz">Quiz</option>
                    <option value="lab">Lab Exercise</option>
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="access-level" className="block text-gray-700 font-medium mb-1">Access Level</label>
                  <select
                    id="access-level"
                    value={accessLevel}
                    onChange={e => setAccessLevel(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  >
                    <option value="basic">Basic (Unregistered Users)</option>
                    <option value="intermediate">Intermediate (Registered Users)</option>
                    <option value="advanced">Advanced (Paid Users)</option>
                  </select>
                </div>
              </Card>
              <Card className="overflow-visible">
                <h2 className="text-xl font-semibold mb-4">Tiered Content</h2>
                <div className="form-group mb-4">
                  <label htmlFor="basic-content" className="block text-gray-700 font-medium mb-1">Basic Content (Preview for Unregistered Users)</label>
                  <textarea
                    id="basic-content"
                    rows={3}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    value={basicContent}
                    onChange={e => setBasicContent(e.target.value)}
                    placeholder="Enter preview content for unregistered users"
                  ></textarea>
                </div>
                <div className="form-group mb-4">
                  <label htmlFor="intermediate-content" className="block text-gray-700 font-medium mb-1">Intermediate Content (Registered Users)</label>
                  <textarea
                    id="intermediate-content"
                    rows={3}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    value={intermediateContent}
                    onChange={e => setIntermediateContent(e.target.value)}
                    placeholder="Enter content for registered users"
                  ></textarea>
                </div>
                <div className="form-group mb-4">
                  <label htmlFor="content" className="block text-gray-700 font-medium mb-1">Advanced Content (Full for Paid Users)</label>
                  <textarea
                    id="content"
                    rows={5}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    value={content}
                    onChange={e => setContent(e.target.value)}
                    placeholder="Enter full content for paid users"
                  ></textarea>
                </div>
              </Card>
              <Card className="overflow-visible">
                <h2 className="text-xl font-semibold mb-4">Resources & Attachments</h2>
                {/* Resource upload UI here */}
                {/* ... existing resource upload code ... */}
              </Card>
              <Card className="overflow-visible">
                <h2 className="text-xl font-semibold mb-4">Assessment (Optional)</h2>
                <div className="flex items-center mb-2">
                  <input
                    id="has-assessment"
                    type="checkbox"
                    checked={hasAssessment}
                    onChange={e => setHasAssessment(e.target.checked)}
                    className="mr-2"
                  />
                  <label htmlFor="has-assessment" className="text-gray-700 font-medium">Include Assessment</label>
                </div>
                {/* Assessment creation UI if hasAssessment is true */}
                {/* ... code for assessment creation ... */}
              </Card>
            </div>
            {/* Sidebar for flags and actions */}
            <div className="space-y-6">
              <Card className="overflow-visible">
                <h2 className="text-xl font-semibold mb-4">Lesson Options</h2>
                <div className="flex items-center mb-2">
                  <input
                    id="has-lab"
                    type="checkbox"
                    checked={hasLab}
                    onChange={e => setHasLab(e.target.checked)}
                    className="mr-2"
                  />
                  <label htmlFor="has-lab" className="text-gray-700 font-medium">Has Lab</label>
                </div>
                <div className="flex items-center mb-2">
                  <input
                    id="is-free-preview"
                    type="checkbox"
                    checked={isFreePreview}
                    onChange={e => setIsFreePreview(e.target.checked)}
                    className="mr-2"
                  />
                  <label htmlFor="is-free-preview" className="text-gray-700 font-medium">Is Free Preview</label>
                </div>
              </Card>
              <Button type="submit" variant="contained" color="primary" disabled={loading}>
                {loading ? 'Creating Lesson...' : 'Create Lesson'}
              </Button>
            </div>
          </div>
        </form>
      </Container>
    </div>
  );
};

export default CreateLessonPage;