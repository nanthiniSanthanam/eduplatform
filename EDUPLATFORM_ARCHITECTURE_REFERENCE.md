# EduPlatform - Comprehensive Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [Backend Architecture](#backend-architecture)
   - [Technology Stack](#backend-technology-stack)
   - [Data Models](#data-models)
   - [APIs](#apis)
   - [Serializers](#serializers)
   - [Authentication System](#backend-authentication)
3. [Frontend Architecture](#frontend-architecture)
   - [Technology Stack](#frontend-technology-stack)
   - [Component Structure](#component-structure)
   - [Routing](#routing)
   - [State Management](#state-management)
   - [Authentication Implementation](#frontend-authentication)
4. [UI/UX Design](#uiux-design)
   - [Theme and Styling](#theme-and-styling)
   - [Layout Components](#layout-components)
   - [Responsive Design](#responsive-design)
5. [Integration Points](#integration-points)
6. [Deployment](#deployment)

## Project Overview

EduPlatform is a comprehensive educational platform that connects students, teachers, and educational content in an interactive learning environment. The application follows a modern client-server architecture with a React.js frontend and Django/Python backend. The system provides features for course management, student progress tracking, content delivery, and interactive learning experiences.

The application is structured with clear separation between frontend and backend components, communicating through RESTful APIs. Authentication is handled through JWT tokens, ensuring secure access to platform resources.

## Backend Architecture

### Backend Technology Stack

- **Framework**: Django with Django REST Framework
- **Database**: SQLite (development), PostgreSQL (production-ready)
- **Authentication**: JWT (JSON Web Tokens)
- **API Style**: RESTful

### Data Models

The database structure is defined through the following key models:

#### User Model

Extended from Django's built-in User model with additional fields for user profiles:

```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### Course Model

Defines educational courses with metadata and relationship to instructors:

```python
class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)
```

#### Module Model

Represents sections within courses:

```python
class Module(models.Model):
    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
```

#### Content Model

Stores different types of learning materials:

```python
class Content(models.Model):
    module = models.ForeignKey(Module, related_name='contents', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    text_content = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='content_files/', blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
```

#### Enrollment Model

Tracks student course registrations:

```python
class Enrollment(models.Model):
    student = models.ForeignKey(User, related_name='enrollments', on_delete=models.CASCADE)
    course = models.ForeignKey(Course, related_name='enrollments', on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
```

#### Progress Model

Tracks student progress through course materials:

```python
class Progress(models.Model):
    student = models.ForeignKey(User, related_name='progress', on_delete=models.CASCADE)
    content = models.ForeignKey(Content, related_name='progress', on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    last_accessed = models.DateTimeField(auto_now=True)
```

### APIs

The backend exposes the following RESTful API endpoints:

#### Authentication Endpoints

- `POST /api/auth/register/`: User registration
- `POST /api/auth/login/`: User login (returns JWT token)
- `POST /api/auth/refresh/`: Refresh JWT token
- `GET /api/auth/user/`: Get current user information

#### User Endpoints

- `GET /api/users/`: List all users (admin only)
- `GET /api/users/{id}/`: Retrieve specific user details
- `PUT /api/users/{id}/`: Update user details
- `PATCH /api/users/{id}/`: Partially update user details
- `DELETE /api/users/{id}/`: Delete a user (admin only)

#### Course Endpoints

- `GET /api/courses/`: List all available courses
- `POST /api/courses/`: Create a new course (instructor only)
- `GET /api/courses/{id}/`: Retrieve course details
- `PUT /api/courses/{id}/`: Update course details (instructor only)
- `DELETE /api/courses/{id}/`: Delete a course (instructor only)
- `GET /api/courses/{id}/modules/`: Get all modules for a course

#### Module Endpoints

- `GET /api/modules/`: List all modules
- `POST /api/modules/`: Create a new module (instructor only)
- `GET /api/modules/{id}/`: Get module details
- `PUT /api/modules/{id}/`: Update module (instructor only)
- `DELETE /api/modules/{id}/`: Delete module (instructor only)
- `GET /api/modules/{id}/contents/`: List contents in a module

#### Content Endpoints

- `GET /api/contents/`: List all content
- `POST /api/contents/`: Create new content (instructor only)
- `GET /api/contents/{id}/`: Get content details
- `PUT /api/contents/{id}/`: Update content (instructor only)
- `DELETE /api/contents/{id}/`: Delete content (instructor only)

#### Enrollment Endpoints

- `GET /api/enrollments/`: List all enrollments
- `POST /api/enrollments/`: Enroll in a course
- `GET /api/enrollments/{id}/`: Get enrollment details
- `DELETE /api/enrollments/{id}/`: Unenroll from a course

#### Progress Endpoints

- `GET /api/progress/`: Get progress records
- `POST /api/progress/`: Create progress record
- `PUT /api/progress/{id}/`: Update progress
- `GET /api/progress/by-course/{course_id}/`: Get progress for a specific course

### Serializers

Serializers handle the conversion between complex data types and Python data types, enabling proper API responses:

#### User Serializers

```python
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'role', 'bio', 'profile_picture', 'created_at', 'updated_at']
```

#### Course Serializers

```python
class CourseSerializer(serializers.ModelSerializer):
    instructor_name = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'instructor', 'instructor_name',
                  'thumbnail', 'created_at', 'updated_at', 'is_published']

    def get_instructor_name(self, obj):
        return f"{obj.instructor.first_name} {obj.instructor.last_name}"
```

#### Module Serializers

```python
class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ['id', 'course', 'title', 'description', 'order']
```

#### Content Serializers

```python
class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = ['id', 'module', 'title', 'content_type', 'text_content',
                  'file', 'url', 'order']
```

#### Enrollment Serializers

```python
class EnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)

    class Meta:
        model = Enrollment
        fields = ['id', 'student', 'student_name', 'course', 'course_title',
                  'enrolled_at', 'is_completed']
```

### Backend Authentication

The authentication system uses Django's built-in authentication along with JWT (JSON Web Tokens) for API authorization:

1. **User Registration**: New users register by providing username, email, password, and role information.
2. **Token Generation**: Upon successful login, the system generates a JWT access token and refresh token.
3. **Token Refresh**: When the access token expires, the client can use the refresh token to obtain a new access token.
4. **Permission Levels**:
   - Anonymous users: Can view public courses and register
   - Students: Can enroll in courses and track progress
   - Instructors: Can create and manage courses, modules, and content
   - Administrators: Have full access to platform management

Authentication middleware validates JWT tokens on protected endpoints and attaches the authenticated user to the request object.

## Frontend Architecture

### Frontend Technology Stack

- **Framework**: React.js
- **State Management**: Context API with hooks
- **Routing**: React Router
- **Styling**: CSS with some Material-UI components
- **HTTP Client**: Axios for API communication

### Component Structure

The frontend follows a modular component structure organized by feature:

#### Core Components

- **App**: Main application container and routing setup
- **Layout**: Page layout components (Header, Footer, Sidebar)
- **ProtectedRoute**: Higher-order component for route protection

#### Authentication Components

- **Login**: User login form and logic
- **Register**: User registration form and logic
- **ForgotPassword**: Password reset request form
- **ResetPassword**: Password reset confirmation form
- **Profile**: User profile display and edit interface

#### Course Components

- **CourseList**: Displays available courses with filtering options
- **CourseDetail**: Shows detailed information about a specific course
- **CourseCreator**: Interface for instructors to create/edit courses
- **ModuleList**: Displays modules within a course
- **ContentViewer**: Displays various types of learning content

#### Student Components

- **Dashboard**: Student dashboard showing enrolled courses and progress
- **Progress**: Shows detailed progress through course materials
- **Enrollment**: Handles course enrollment and unenrollment

#### Instructor Components

- **InstructorDashboard**: Shows instructor courses and analytics
- **CourseManager**: Interface for managing existing courses
- **ContentCreator**: Tools for creating and organizing course content

### Routing

The application uses React Router for navigation with the following route structure:

```jsx
// Main routes configuration
<Routes>
  <Route path="/" element={<Home />} />
  <Route path="/login" element={<Login />} />
  <Route path="/register" element={<Register />} />
  <Route path="/forgot-password" element={<ForgotPassword />} />
  <Route path="/reset-password/:token" element={<ResetPassword />} />

  {/* Protected routes requiring authentication */}
  <Route element={<ProtectedRoute />}>
    <Route path="/dashboard" element={<Dashboard />} />
    <Route path="/profile" element={<Profile />} />

    {/* Course routes */}
    <Route path="/courses" element={<CourseList />} />
    <Route path="/courses/:courseId" element={<CourseDetail />} />

    {/* Student specific routes */}
    <Route path="/my-courses" element={<StudentCourses />} />
    <Route path="/progress/:courseId" element={<CourseProgress />} />

    {/* Instructor specific routes */}
    <Route path="/instructor/dashboard" element={<InstructorDashboard />} />
    <Route path="/instructor/courses" element={<InstructorCourses />} />
    <Route path="/instructor/courses/create" element={<CreateCourse />} />
    <Route path="/instructor/courses/:courseId/edit" element={<EditCourse />} />
    <Route
      path="/instructor/courses/:courseId/modules"
      element={<ManageModules />}
    />
    <Route
      path="/instructor/courses/:courseId/modules/:moduleId/content"
      element={<ManageContent />}
    />
  </Route>

  <Route path="*" element={<NotFound />} />
</Routes>
```

### State Management

State management is implemented using React's Context API with custom hooks:

#### Authentication Context

Manages user authentication state across the application:

```jsx
export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Login function
  const login = async (credentials) => {
    try {
      const response = await axios.post("/api/auth/login/", credentials);
      localStorage.setItem("accessToken", response.data.access);
      localStorage.setItem("refreshToken", response.data.refresh);
      await getCurrentUser();
      return true;
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed");
      return false;
    }
  };

  // Logout function
  const logout = () => {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    setUser(null);
  };

  // Get current user
  const getCurrentUser = async () => {
    try {
      const response = await axios.get("/api/auth/user/");
      setUser(response.data);
      return response.data;
    } catch (err) {
      setUser(null);
      throw err;
    }
  };

  // Auth context values
  const value = {
    user,
    loading,
    error,
    login,
    logout,
    getCurrentUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Custom hook for using auth context
export const useAuth = () => useContext(AuthContext);
```

#### Course Context

Manages course-related state and operations:

```jsx
export const CourseContext = createContext();

export const CourseProvider = ({ children }) => {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch all courses
  const fetchCourses = async (filters = {}) => {
    setLoading(true);
    try {
      const params = new URLSearchParams(filters);
      const response = await axios.get(`/api/courses/?${params}`);
      setCourses(response.data);
      setLoading(false);
      return response.data;
    } catch (err) {
      setError("Failed to fetch courses");
      setLoading(false);
      throw err;
    }
  };

  // Get course details
  const getCourse = async (courseId) => {
    try {
      const response = await axios.get(`/api/courses/${courseId}/`);
      return response.data;
    } catch (err) {
      setError("Failed to fetch course details");
      throw err;
    }
  };

  // Course context values
  const value = {
    courses,
    loading,
    error,
    fetchCourses,
    getCourse,
    // Additional functions for course management
  };

  return (
    <CourseContext.Provider value={value}>{children}</CourseContext.Provider>
  );
};

// Custom hook for using course context
export const useCourses = () => useContext(CourseContext);
```

### Frontend Authentication

The frontend implements authentication using JWT tokens with the following flow:

1. **Login Process**:

   - User submits credentials (username/email and password)
   - Backend validates credentials and returns JWT access and refresh tokens
   - Tokens are stored in localStorage or secure cookies
   - User details are fetched and stored in AuthContext state

2. **Token Management**:
   - Access tokens expire after a short period (typically 15-60 minutes)
   - Refresh tokens have a longer lifespan (days or weeks)
   - Axios interceptor refreshes tokens automatically when needed:

```jsx
// Axios interceptor for token refresh
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem("refreshToken");
        const response = await axios.post("/api/auth/refresh/", {
          refresh: refreshToken,
        });

        localStorage.setItem("accessToken", response.data.access);
        axios.defaults.headers.common[
          "Authorization"
        ] = `Bearer ${response.data.access}`;
        originalRequest.headers[
          "Authorization"
        ] = `Bearer ${response.data.access}`;

        return axios(originalRequest);
      } catch (refreshError) {
        // Refresh token expired or invalid, logout user
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        window.location.href = "/login";
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
```

3. **Route Protection**:
   - ProtectedRoute component ensures authenticated access to restricted areas
   - Role-based protection for instructor and admin areas

```jsx
const ProtectedRoute = ({ allowedRoles = [], ...rest }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
};
```

## UI/UX Design

### Theme and Styling

The application uses a clean, modern design with an education-focused color scheme:

#### Color Palette

- **Primary Color**: #4a6da7 (Educational blue)
- **Secondary Color**: #ff6b6b (Accent red)
- **Background Colors**: #f8f9fa (Light gray) and white
- **Text Colors**: #333333 (Dark gray) for main text, #6c757d (Medium gray) for secondary text

#### Typography

- **Primary Font**: 'Roboto', sans-serif
- **Secondary Font**: 'Poppins', sans-serif for headings
- **Body Text**: 16px with 1.5 line height
- **Headings**: Bold weight with scaled sizes (h1: 2.5rem, h2: 2rem, h3: 1.75rem, etc.)

#### Design Elements

- **Cards**: Soft shadows with rounded corners (8px radius)
- **Buttons**: Rounded buttons with hover effects
- **Icons**: Material Design icons for consistent visual language
- **Spacing**: 8px base unit with multiples for consistent spacing

### Layout Components

The application uses several reusable layout components:

#### MainLayout

Primary layout used for authenticated pages:

```jsx
const MainLayout = ({ children }) => {
  return (
    <div className="main-layout">
      <Header />
      <div className="main-content">
        <Sidebar />
        <div className="content-area">{children}</div>
      </div>
      <Footer />
    </div>
  );
};
```

#### AuthLayout

Simplified layout for authentication pages:

```jsx
const AuthLayout = ({ children }) => {
  return (
    <div className="auth-layout">
      <div className="auth-logo">
        <img src="/logo.png" alt="EduPlatform" />
      </div>
      <div className="auth-container">{children}</div>
      <div className="auth-footer">
        <p>© 2025 EduPlatform. All rights reserved.</p>
      </div>
    </div>
  );
};
```

#### CourseLayout

Special layout for course viewing:

```jsx
const CourseLayout = ({ course, children }) => {
  return (
    <MainLayout>
      <div className="course-header">
        <h1>{course.title}</h1>
        <div className="course-meta">
          <span>Instructor: {course.instructor_name}</span>
          <span>
            Created: {new Date(course.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>
      <div className="course-content">
        <CourseSidebar modules={course.modules} />
        <div className="course-main">{children}</div>
      </div>
    </MainLayout>
  );
};
```

### Responsive Design

The application is fully responsive with breakpoints at:

- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

Responsive techniques include:

- Fluid grid layouts using CSS Flexbox and Grid
- Media queries for component adaptations
- Dynamic sidebar that collapses to top navigation on mobile
- Touch-friendly controls with appropriate sizing for mobile interaction

## Integration Points

### Frontend-Backend Communication

The frontend communicates with the backend using RESTful API calls:

1. **API Base URL**: All API requests are prefixed with `/api/`
2. **Authentication Headers**: JWT tokens are included in Authorization headers
3. **API Client**: Axios is configured with base settings and interceptors:

```jsx
// API client setup
const apiClient = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

// Add token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("accessToken");
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);
```

### External Integrations

The platform supports integration with external services:

1. **File Storage**: Integration with AWS S3 for course materials and user uploads
2. **Video Playback**: Support for embedded YouTube and Vimeo videos in course content
3. **OAuth Authentication**: Support for Google and Facebook login

## Deployment

The application is designed for deployment in the following environments:

### Development Environment

- Local development server for Django (runserver)
- React development server (npm start)
- SQLite database for simplicity

### Production Environment

- **Backend**: Django served via Gunicorn behind Nginx
- **Frontend**: Static React build served through Nginx
- **Database**: PostgreSQL for production data
- **Media Storage**: AWS S3 for user uploads and course materials
- **Caching**: Redis for session and query caching
- **Deployment**: Docker containers orchestrated with Docker Compose

### Deployment Process

1. Build React frontend into static assets
2. Collect Django static files
3. Build Docker images for frontend and backend
4. Deploy containers with proper environment variables
5. Configure Nginx for routing and serving static files
6. Set up SSL certificates for HTTPS

This deployment setup ensures scalability and maintainability of the platform.
