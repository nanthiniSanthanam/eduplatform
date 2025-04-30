# fmt: off
# isort: skip_file

r"""
File: C:\Users\Santhanam\OneDrive\Personal\Full stack web development\eduplatform\backend\comprehensive_create_courses.py

Purpose: Creates sample courses with tiered content for the educational platform.

This script creates:
1. Course categories (Web Development, Data Science)
2. Courses with detailed descriptions
3. Modules within each course
4. Lessons with three levels of content:
   - Basic content: For unregistered users (previews only)
   - Intermediate content: For registered users (full lessons)
   - Advanced content: For premium/paid users (advanced content + resources)
5. Resources attached to lessons (basic and premium)
6. Instructor assignments to courses

Variables you can modify:
1. SAMPLE_COURSES: List of courses with their details
   - 'title': Course title (e.g., 'Introduction to Web Development')
   - 'description': Course description (e.g., 'Learn the fundamentals of web development...')
   - 'category_name': Category for the course (e.g., 'Web Development')
   - 'modules': List of modules in the course, each containing:
     - 'title': Module title (e.g., 'HTML Fundamentals')
     - 'description': Module description (e.g., 'Master the building blocks of the web')
     - 'lessons': List of lessons in the module, each containing:
       - 'title': Lesson title (e.g., 'Introduction to HTML')
       - 'duration': Lesson duration (e.g., '30 minutes')
       - 'access_level': Access level required ('basic', 'intermediate', or 'advanced')
       - 'content_data': Dictionary with lesson content (varies by lesson)

2. Basic Content Template: Controls what unregistered users see (preview content)

3. Intermediate Content Template: Controls what registered users see (full content)

4. Advanced Content Template: Controls what premium users see (advanced content)

Requirements:
- Python 3.8 or higher
- Django 3.2 or higher
- PostgreSQL database configured in settings.py
- User accounts created with fixed_create_users.py

How to run:
1. Make sure your virtual environment is activated:
   venv\Scripts\activate
2. Run the script:
   python comprehensive_create_courses.py
3. Check for success messages in the console

Created by: Professor Santhanam
Last updated: 2025-04-27 17:35:45
"""

#####################################################
# PART 1: DJANGO SETUP
# This section sets up Django properly
# Do not modify this section unless you know what you're doing
#####################################################

# Standard library imports - these come with Python
import os
import sys
import traceback
import random
from datetime import timedelta

# Get the absolute path to your project directory
# This helps Python find your project files
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
print(f"Project directory: {SCRIPT_DIR}")

# Add your project directory to the Python path
# This is required for Python to find your Django modules
sys.path.insert(0, SCRIPT_DIR)
print("Added project directory to Python path")

# Set the Django settings module environment variable
# This tells Django where to find your settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'educore.settings'
print("Set Django settings module to 'educore.settings'")

# Before importing any Django models, initialize Django
print("Initializing Django...")
import django
django.setup()
print("Django initialized successfully!")

# Now it's safe to import Django models
print("Importing Django models...")
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from courses.models import Course, Module, Lesson, Resource, Category, CourseInstructor
print("Models imported successfully!")

#####################################################
# PART 2: CONTENT TEMPLATES
# These templates define what each user tier will see
# You can modify these to change how the content looks
#####################################################

# Basic content - visible to all users without login (preview content)
BASIC_CONTENT = """
<div class="preview-content">
    <h2>{title} - Preview</h2>
    
    <p>This is a preview of the lesson content. {preview_text}</p>
    
    <div class="premium-features bg-gray-100 p-4 rounded my-4">
        <h3>What you'll learn in the full lesson:</h3>
        <ul>
            <li>{learning_point_1}</li>
            <li>{learning_point_2}</li>
            <li>{learning_point_3}</li>
        </ul>
    </div>
    
    <div class="cta-box bg-blue-50 p-4 border-l-4 border-blue-500 my-6">
        <p>Register for free to access the complete lesson content!</p>
    </div>
</div>
"""

# Intermediate content - visible to registered users (full content)
INTERMEDIATE_CONTENT = """
<div class="full-lesson">
    <h2>{title}</h2>

    <div class="lesson-overview">
        <p class="text-lg text-gray-700 mb-4">{overview}</p>
    </div>

    <div class="lesson-content">
        <h3>Key Concepts</h3>
        <p>{key_concepts}</p>
        
        <h3>Detailed Explanation</h3>
        <p>{detailed_explanation}</p>
        
        <div class="example bg-gray-50 p-4 rounded my-4">
            <h4>Example</h4>
            <p>{example}</p>
            <pre><code class="language-{language}">{code_example}</code></pre>
        </div>
        
        <h3>Practice Exercise</h3>
        <div class="exercise border-l-4 border-green-500 pl-4">
            <p>{practice_exercise}</p>
        </div>
        
        <div class="premium-teaser bg-purple-50 p-4 rounded my-6">
            <h4 class="text-purple-800">Premium Content Preview</h4>
            <p>As a registered user, you have access to all main course content. Upgrade to Premium to access:</p>
            <ul class="text-gray-700">
                <li>Advanced exercises and solutions</li>
                <li>Downloadable resources and templates</li>
                <li>Expert insights and case studies</li>
                <li>Course completion certificates</li>
            </ul>
            <p class="mt-4 font-medium">Upgrade now to unlock all premium features!</p>
        </div>
    </div>
</div>
"""

# Advanced content - visible to premium subscribers (advanced content)
ADVANCED_CONTENT = """
<div class="premium-lesson">
    <h2>{title}</h2>

    <div class="lesson-overview">
        <p class="text-lg text-gray-700 mb-4">{overview}</p>
    </div>

    <div class="lesson-content">
        <h3>Key Concepts</h3>
        <p>{key_concepts}</p>
        
        <h3>Detailed Explanation</h3>
        <p>{detailed_explanation}</p>
        
        <div class="example bg-gray-50 p-4 rounded my-4">
            <h4>Example</h4>
            <p>{example}</p>
            <pre><code class="language-{language}">{code_example}</code></pre>
        </div>
        
        <h3>Practice Exercise</h3>
        <div class="exercise border-l-4 border-green-500 pl-4">
            <p>{practice_exercise}</p>
        </div>
        
        <div class="premium-content mt-8 border-t-2 border-purple-200 pt-6">
            <div class="premium-badge bg-purple-600 text-white inline-block px-3 py-1 rounded-full text-sm">PREMIUM</div>
            <h3 class="text-xl font-semibold mt-2">Advanced Content</h3>
            
            <div class="advanced-theory mt-4">
                <h4>Advanced Theory</h4>
                <p>{advanced_theory}</p>
            </div>
            
            <div class="advanced-example bg-gray-50 p-4 rounded my-4">
                <h4>Advanced Example</h4>
                <p>{advanced_example}</p>
                <pre><code class="language-{language}">{advanced_code}</code></pre>
            </div>
            
            <div class="case-study bg-blue-50 p-4 rounded my-6">
                <h4 class="text-blue-800">Case Study: {case_study_title}</h4>
                <p>{case_study_content}</p>
                <p class="mt-4 font-medium">Result: {case_study_result}</p>
            </div>
            
            <h4>Downloadable Resources</h4>
            <div class="resources-list">
                <p>The following premium resources are available for download:</p>
                <ul class="list-disc pl-5 mt-2">
                    <li><a href="#" class="text-purple-600 hover:underline">Complete solution worksheet</a></li>
                    <li><a href="#" class="text-purple-600 hover:underline">Practice templates</a></li>
                    <li><a href="#" class="text-purple-600 hover:underline">Reference guide</a></li>
                </ul>
            </div>
        </div>
    </div>
</div>
"""

#####################################################
# PART 3: SAMPLE COURSE DATA
# This section defines the courses, modules, and lessons to create
# You can modify this to add your own courses
#####################################################

# Sample course data - you can add your own courses by copying this structure
SAMPLE_COURSES = [
    {
        'title': 'Introduction to Web Development',
        'description': 'Learn the fundamentals of web development including HTML, CSS, and JavaScript.',
        'category_name': 'Web Development',
        'modules': [
            {
                'title': 'HTML Fundamentals',
                'description': 'Master the building blocks of the web',
                'lessons': [
                    {
                        'title': 'Introduction to HTML',
                        'duration': '30 minutes',
                        'access_level': 'basic',
                        'content_data': {
                            'title': 'Introduction to HTML',
                            'preview_text': 'Learn the basics of HTML, the backbone of all web pages.',
                            'learning_point_1': 'Understand HTML document structure',
                            'learning_point_2': 'Learn about essential HTML tags',
                            'learning_point_3': 'Create your first web page',
                            'overview': 'HTML (HyperText Markup Language) is the standard markup language for documents designed to be displayed in a web browser. It defines the structure of web content.',
                            'key_concepts': 'HTML uses elements to label pieces of content such as "heading", "paragraph", "image", and so on. These elements are represented by tags like <h1>, <p>, and <img>.',
                            'detailed_explanation': 'HTML documents are made up of a tree of HTML elements. Elements are represented by tags. Tags come in pairs - opening and closing tags, like <p> and </p>. The content goes between these tags. Some elements are self-closing and don\'t need a closing tag, like <img>.',
                            'example': 'Here\'s a simple HTML document structure:',
                            'language': 'html',
                            'code_example': '<!DOCTYPE html>\n<html>\n<head>\n  <title>My First Web Page</title>\n</head>\n<body>\n  <h1>Hello, World!</h1>\n  <p>This is my first web page.</p>\n</body>\n</html>',
                            'practice_exercise': 'Create a simple HTML document that includes a heading, a paragraph, and a list of your favorite foods.',
                            'advanced_theory': 'Beyond the basics, modern HTML5 introduces semantic elements that clearly describe their meaning to both the browser and the developer. Elements like <nav>, <header>, <article>, and <footer> provide more context than generic containers like <div>.',
                            'advanced_example': 'Here\'s how to structure a page with semantic HTML:',
                            'advanced_code': '<!DOCTYPE html>\n<html>\n<head>\n  <title>Semantic HTML Example</title>\n</head>\n<body>\n  <header>\n    <h1>My Website</h1>\n    <nav>\n      <ul>\n        <li><a href="#">Home</a></li>\n        <li><a href="#">About</a></li>\n        <li><a href="#">Contact</a></li>\n      </ul>\n    </nav>\n  </header>\n  <main>\n    <article>\n      <h2>Article Title</h2>\n      <p>Article content goes here...</p>\n    </article>\n    <aside>\n      <h3>Related Links</h3>\n      <ul>\n        <li><a href="#">Link 1</a></li>\n        <li><a href="#">Link 2</a></li>\n      </ul>\n    </aside>\n  </main>\n  <footer>\n    <p>Copyright © 2025</p>\n  </footer>\n</body>\n</html>',
                            'case_study_title': 'Improving Website Accessibility',
                            'case_study_content': 'A major e-commerce website improved their HTML structure by replacing generic <div> elements with semantic HTML5 elements. They also added proper ARIA roles and attributes to components.',
                            'case_study_result': 'The site saw a 30% increase in engagement from users with disabilities, and their search engine ranking improved significantly.'
                        }
                    },
                    {
                        'title': 'HTML Elements and Attributes',
                        'duration': '45 minutes',
                        'access_level': 'intermediate',
                        'content_data': {
                            'title': 'HTML Elements and Attributes',
                            'preview_text': 'Explore the different types of HTML elements and how to use attributes.',
                            'learning_point_1': 'Understand block and inline elements',
                            'learning_point_2': 'Use HTML attributes effectively',
                            'learning_point_3': 'Structure your content correctly',
                            'overview': 'HTML elements are the building blocks of HTML pages, and attributes provide additional information about those elements.',
                            'key_concepts': 'HTML elements are categorized as block-level or inline elements. Block-level elements start on a new line and take up the full width available, while inline elements only take up as much width as necessary and don\'t force new lines.',
                            'detailed_explanation': 'Attributes provide additional information about HTML elements. They are always specified in the start tag and usually come in name/value pairs like: name="value". Attributes can modify the behavior or appearance of elements, provide metadata, or help with accessibility.',
                            'example': 'Here\'s an example showing different elements and their attributes:',
                            'language': 'html',
                            'code_example': '<div class="container" id="main-content">\n  <h1 style="color: blue;">This is a heading</h1>\n  <p>This is a <a href="https://example.com" target="_blank">link</a> within a paragraph.</p>\n  <img src="image.jpg" alt="A description of the image" width="300" height="200">\n</div>',
                            'practice_exercise': 'Create an HTML page with a form that includes different input types (text, email, password), labels, and a submit button. Use appropriate attributes for each element.',
                            'advanced_theory': 'Custom data attributes (data-*) allow you to store extra information on HTML elements that isn\'t directly visible to users but can be accessed via JavaScript or CSS. These are extremely useful for modern web applications.',
                            'advanced_example': 'Here\'s how to use data attributes and access them with JavaScript:',
                            'advanced_code': '<!-- HTML with data attributes -->\n<div id="user-profile" data-user-id="123" data-role="admin">\n  <h2>User Profile</h2>\n</div>\n\n<!-- JavaScript to access data attributes -->\n<script>\n  const profile = document.getElementById(\'user-profile\');\n  \n  // Get data attributes\n  const userId = profile.dataset.userId;\n  const role = profile.dataset.role;\n  \n  console.log(`User ID: ${userId}, Role: ${role}`);\n  \n  // Conditionally show admin features\n  if (role === \'admin\') {\n    // Show admin interface elements\n  }\n</script>',
                            'case_study_title': 'Single-Page Application Enhancement',
                            'case_study_content': 'A tech company was building a complex single-page application with React. They implemented data attributes to store component state information directly in the DOM.',
                            'case_study_result': 'This approach improved debugging capabilities and allowed easier integration with external analytics tools, resulting in 40% faster development cycles.'
                        }
                    },
                    {
                        'title': 'Advanced HTML5 Features',
                        'duration': '60 minutes',
                        'access_level': 'advanced',
                        'content_data': {
                            'title': 'Advanced HTML5 Features',
                            'preview_text': 'Discover the powerful features introduced in HTML5 that transform web capabilities.',
                            'learning_point_1': 'Use HTML5 semantic elements',
                            'learning_point_2': 'Implement advanced forms',
                            'learning_point_3': 'Utilize HTML5 APIs',
                            'overview': 'HTML5 introduced many new features including semantic elements, advanced form controls, and powerful APIs that enable rich web applications.',
                            'key_concepts': 'HTML5 semantic elements provide meaning to the structure of web pages, making them more accessible and SEO-friendly. HTML5 also includes powerful APIs like Canvas, Geolocation, Web Storage, and more.',
                            'detailed_explanation': 'HTML5 was designed to replace not only HTML 4, but also XHTML and the HTML DOM Level 2. It provides clearer code, eliminates the need for some external plugins, and includes built-in features for modern web requirements like graphics, multimedia, and application functionality.',
                            'example': 'Here\'s a basic example of HTML5 form controls:',
                            'language': 'html',
                            'code_example': '<form>\n  <label for="email">Email:</label>\n  <input type="email" id="email" required>\n  \n  <label for="url">Website:</label>\n  <input type="url" id="url">\n  \n  <label for="date">Date:</label>\n  <input type="date" id="date">\n  \n  <label for="range">Range (1-10):</label>\n  <input type="range" id="range" min="1" max="10">\n  \n  <label for="color">Pick a color:</label>\n  <input type="color" id="color">\n  \n  <button type="submit">Submit</button>\n</form>',
                            'practice_exercise': 'Create an HTML5 page that uses at least three semantic elements, includes a form with HTML5 validation, and demonstrates one HTML5 API like localStorage.',
                            'advanced_theory': 'HTML5 Web Components allow developers to create reusable custom elements with encapsulated functionality. This includes Custom Elements, Shadow DOM, HTML Templates, and ES Modules, which together provide a standard component model for the web.',
                            'advanced_example': 'Here\'s how to create a custom element with HTML5 Web Components:',
                            'advanced_code': '<!-- Define a template -->\n<template id="user-card-template">\n  <style>\n    .user-card {\n      border: 1px solid #ccc;\n      padding: 16px;\n      border-radius: 4px;\n    }\n    .user-name {\n      font-weight: bold;\n      color: #333;\n    }\n  </style>\n  \n  <div class="user-card">\n    <img class="user-avatar">\n    <div class="user-name"></div>\n    <div class="user-email"></div>\n    <slot name="extra-info"></slot>\n  </div>\n</template>\n\n<script>\n  class UserCard extends HTMLElement {\n    constructor() {\n      super();\n      \n      // Create a shadow root\n      const shadow = this.attachShadow({mode: \'open\'});\n      \n      // Get the template content\n      const template = document.getElementById(\'user-card-template\');\n      const templateContent = template.content;\n      \n      // Clone the template\n      const clone = templateContent.cloneNode(true);\n      \n      // Set properties based on attributes\n      const img = clone.querySelector(\'.user-avatar\');\n      const name = clone.querySelector(\'.user-name\');\n      const email = clone.querySelector(\'.user-email\');\n      \n      img.src = this.getAttribute(\'avatar\') || \'default-avatar.png\';\n      name.textContent = this.getAttribute(\'name\') || \'Unknown\';\n      email.textContent = this.getAttribute(\'email\') || \'\';\n      \n      // Attach to shadow DOM\n      shadow.appendChild(clone);\n    }\n  }\n  \n  // Define the custom element\n  customElements.define(\'user-card\', UserCard);\n</script>\n\n<!-- Usage -->\n<user-card \n  name="John Doe" \n  email="john@example.com" \n  avatar="john.jpg">\n  <div slot="extra-info">Senior Developer</div>\n</user-card>',
                            'case_study_title': 'Major News Website Redesign',
                            'case_study_content': 'A leading news organization completely rebuilt their website using HTML5 semantic elements, native video, offline capabilities via Service Workers, and Web Components for consistent UI elements across their platform.',
                            'case_study_result': 'The new site loaded 65% faster, increased audience engagement by 42%, and supported offline reading. It also dramatically reduced maintenance costs by using standardized components.'
                        }
                    }
                ]
            },
            {
                'title': 'CSS Styling',
                'description': 'Learn how to style your web pages with CSS',
                'lessons': [
                    {
                        'title': 'CSS Fundamentals',
                        'duration': '40 minutes',
                        'access_level': 'basic',
                        'content_data': {
                            'title': 'CSS Fundamentals',
                            'preview_text': 'Learn how to style HTML elements with Cascading Style Sheets.',
                            'learning_point_1': 'Understand CSS selectors',
                            'learning_point_2': 'Apply styles to HTML elements',
                            'learning_point_3': 'Use the CSS box model',
                            'overview': 'Cascading Style Sheets (CSS) is the language used to style web pages. CSS describes how HTML elements should be displayed.',
                            'key_concepts': 'CSS works by selecting HTML elements and applying styles to them. The "cascade" refers to how styles can be inherited and overridden, with more specific selectors taking precedence over general ones.',
                            'detailed_explanation': 'CSS can be added to HTML in three ways: inline (using the style attribute), internal (using a <style> element in the head section), or external (linking to an external CSS file). External CSS is the most efficient method for larger websites as it separates the content from the presentation.',
                            'example': 'Here\'s a simple example of CSS styling:',
                            'language': 'css',
                            'code_example': '/* External CSS file style.css */\n\n/* Element selector */\nbody {\n  font-family: Arial, sans-serif;\n  line-height: 1.6;\n  color: #333;\n  background-color: #f4f4f4;\n}\n\n/* Class selector */\n.container {\n  max-width: 1100px;\n  margin: 0 auto;\n  padding: 0 20px;\n}\n\n/* ID selector */\n#header {\n  background-color: #333;\n  color: #fff;\n  padding: 10px;\n}\n\n/* Descendant selector */\n#header h1 {\n  margin: 0;\n}',
                            'practice_exercise': 'Create a CSS file to style an HTML page with a header, navigation menu, main content area, and footer. Use a combination of element, class, and ID selectors.',
                            'advanced_theory': 'CSS Specificity is a weight that determines which style declarations apply to an element when multiple rules could apply. Specificity is based on the matching rules which are composed of different sorts of CSS selectors.',
                            'advanced_example': 'Here\'s an example demonstrating CSS specificity:',
                            'advanced_code': '/* Specificity Examples */\n\n/* Specificity: 0,0,0,1 */\nli {\n  color: black;\n}\n\n/* Specificity: 0,0,1,1 */\nul li {\n  color: blue;\n}\n\n/* Specificity: 0,1,0,1 */\n.nav li {\n  color: green;\n}\n\n/* Specificity: 0,1,1,1 */\n.nav li.active {\n  color: red;\n}\n\n/* Specificity: 1,0,0,0 - highest */\n#main-nav li {\n  color: purple;\n}\n\n/* Inline style has highest specificity outside of !important */\n<li style="color: orange;">This will be orange</li>\n\n/* !important overrides all other styles */\nli {\n  color: yellow !important; /* Will override even inline styles */\n}',
                            'case_study_title': 'E-commerce Site Style Standardization',
                            'case_study_content': 'A large e-commerce platform was struggling with inconsistent styling across their site due to multiple teams working on different sections. They implemented a comprehensive CSS architecture using BEM methodology and created a design system.',
                            'case_study_result': 'Development speed increased by 35% as developers spent less time writing custom CSS. User experience improved due to consistent styling, and the site\'s visual coherence led to a 12% increase in conversion rates.'
                        }
                    }
                ]
            }
        ]
    },
    {
        'title': 'Data Science Fundamentals',
        'description': 'An introduction to data science concepts, tools, and methodologies.',
        'category_name': 'Data Science',
        'modules': [
            {
                'title': 'Introduction to Python for Data Science',
                'description': 'Learn the basics of Python programming for data analysis',
                'lessons': [
                    {
                        'title': 'Getting Started with Python',
                        'duration': '45 minutes',
                        'access_level': 'basic',
                        'content_data': {
                            'title': 'Getting Started with Python',
                            'preview_text': 'Learn why Python is the preferred language for data science and how to get started.',
                            'learning_point_1': 'Install Python and essential libraries',
                            'learning_point_2': 'Understand basic Python syntax',
                            'learning_point_3': 'Write your first data analysis script',
                            'overview': 'Python has become the leading language for data science due to its readability, versatility, and powerful libraries. This lesson introduces you to Python basics with a focus on data analysis applications.',
                            'key_concepts': 'Python is an interpreted, high-level, general-purpose programming language with simple syntax that makes it accessible to beginners. For data science, key libraries include NumPy, Pandas, Matplotlib, and scikit-learn.',
                            'detailed_explanation': 'Python\'s simplicity and readability make it ideal for data analysis. Its extensive ecosystem of data-oriented libraries allows you to perform complex data operations with minimal code. Unlike specialized statistical software, Python is a full programming language, giving you the flexibility to build complete data pipelines and applications.',
                            'example': 'Here\'s a simple example of using Python for data analysis:',
                            'language': 'python',
                            'code_example': '# Import libraries\nimport pandas as pd\nimport matplotlib.pyplot as plt\n\n# Load a sample dataset\ndata = pd.read_csv(\'sample_data.csv\')\n\n# View the first few rows\nprint(data.head())\n\n# Get basic statistics\nprint(data.describe())\n\n# Create a simple visualization\ndata.plot(kind=\'bar\', x=\'Category\', y=\'Value\')\nplt.title(\'Values by Category\')\nplt.show()',
                            'practice_exercise': 'Install Python and the Pandas library on your computer. Then write a script to load a CSV file of your choice and print out basic information about the data (number of rows, columns, and basic statistics).',
                            'advanced_theory': 'Python\'s dynamic typing and memory management can impact performance for large-scale data operations. Understanding Python\'s Global Interpreter Lock (GIL), vectorization, and parallel processing options is essential for optimizing data science workflows.',
                            'advanced_example': 'Here\'s how to optimize a data processing task using vectorized operations:',
                            'advanced_code': 'import numpy as np\nimport pandas as pd\nimport time\n\n# Generate sample data\nsize = 1000000\ndf = pd.DataFrame({\n    \'A\': np.random.randn(size),\n    \'B\': np.random.randn(size)\n})\n\n# Method 1: Loop (slow)\nstart = time.time()\nresult1 = []\nfor i in range(len(df)):\n    result1.append(df.iloc[i][\'A\'] * df.iloc[i][\'B\'])\nprint(f"Loop time: {time.time() - start:.2f} seconds")\n\n# Method 2: Vectorized operation (fast)\nstart = time.time()\nresult2 = df[\'A\'] * df[\'B\']\nprint(f"Vectorized time: {time.time() - start:.2f} seconds")\n\n# Verify results are the same\nprint(f"Results match: {np.allclose(result1, result2)}")',
                            'case_study_title': 'Retail Inventory Optimization',
                            'case_study_content': 'A retail chain was struggling with inventory management, often having overstock of some items while running out of others. They implemented a Python-based forecasting system that analyzed historical sales data, seasonal trends, and external factors.',
                            'case_study_result': 'The system reduced stockouts by 37% while decreasing overall inventory costs by 23%. The entire solution was built with Python and open-source libraries, saving hundreds of thousands of dollars compared to commercial solutions.'
                        }
                    }
                ]
            }
        ]
    }
]

#####################################################
# PART 4: INSTRUCTOR CREATION
# This function creates an instructor for the courses
#####################################################

def get_instructor():
    """
    Get or create an instructor user for the courses.

    This function:
    1. Checks if an instructor user already exists
    2. If not, creates a new instructor user
    3. Returns the instructor user object

    Returns:
        User: The instructor user object
    """
    User = get_user_model()
    try:
        # Try to get an existing instructor
        instructor = User.objects.get(username='instructor')
        print(f"Using existing instructor: {instructor.username}")
        return instructor
    except User.DoesNotExist:
        # If instructor doesn't exist, create a new one
        print("Creating instructor user...")
        instructor = User.objects.create_user(
            username='instructor',
            email='instructor@example.com',
            password='instructorpass123',
            first_name='Teaching',
            last_name='Professor',
            role='instructor',
            is_email_verified=True
        )
        print(f"Created new instructor: {instructor.email}")
        return instructor

#####################################################
# PART 5: COURSE CREATION
# This function creates courses, modules, lessons, and resources
#####################################################

def create_test_courses():
    """
    Create or update test courses with tiered content.

    This function:
    1. Creates course categories (like Web Development, Data Science)
    2. Creates courses within those categories
    3. Adds an instructor to each course
    4. Creates modules within each course
    5. Creates lessons within each module
    6. Creates basic and premium resources for lessons

    Returns:
        None
    """
    print("\nCreating test courses with tiered content...")

    # Get an instructor user for the courses
    instructor = get_instructor()

    # Process each course in the sample data
    for course_data in SAMPLE_COURSES:
        try:
            # Step 1: Create or get category
            category, created = Category.objects.get_or_create(
                name=course_data['category_name'],
                defaults={'slug': slugify(course_data['category_name'])}
            )
            if created:
                print(f"Created new category: {category.name}")
            else:
                print(f"Using existing category: {category.name}")

            # Step 2: Create or update course
            slug = slugify(course_data['title'])
            try:
                # Try to get an existing course
                course = Course.objects.get(slug=slug)
                # Update the course if it exists
                course.title = course_data['title']
                course.description = course_data['description']
                course.category = category
                course.save()
                print(f"Updated course: {course.title}")
            except Course.DoesNotExist:
                # Create a new course if it doesn't exist
                course = Course.objects.create(
                    title=course_data['title'],
                    slug=slug,
                    description=course_data['description'],
                    category=category,
                    is_published=True
                )
                print(f"Created new course: {course.title}")

            # Step 3: Add instructor to course
            # First check if this instructor is already assigned to this course
            instructor_relation_exists = CourseInstructor.objects.filter(
                course=course, instructor=instructor
            ).exists()

            if not instructor_relation_exists:
                # Create a new relationship between instructor and course
                CourseInstructor.objects.create(
                    course=course,
                    instructor=instructor,
                    title="Lead Instructor",  # Instructor's title for this course
                    bio="Expert instructor with years of experience",  # Instructor's bio for this course
                    is_lead=True  # This is the lead instructor for this course
                )
                print(f"Added instructor {instructor.username} to course {course.title}")
            else:
                print(f"Instructor {instructor.username} already assigned to course {course.title}")

            # Step 4: Process modules
            for i, module_data in enumerate(course_data['modules']):
                try:
                    # Create or update module
                    module, created = Module.objects.get_or_create(
                        course=course,
                        title=module_data['title'],
                        defaults={
                            'description': module_data.get('description', ''),
                            'order': i + 1  # Set the order of the module
                        }
                    )
                    if not created:
                        # Update the module if it exists
                        module.description = module_data.get('description', '')
                        module.order = i + 1
                        module.save()
                        print(f"Updated module: {module.title}")
                    else:
                        print(f"Created new module: {module.title}")

                    # Step 5: Process lessons
                    for j, lesson_data in enumerate(module_data['lessons']):
                        try:
                            # Get the content data for this lesson
                            content_data = lesson_data['content_data']

                            # Create content for each access level using the templates
                            basic_content = BASIC_CONTENT.format(**content_data)
                            intermediate_content = INTERMEDIATE_CONTENT.format(**content_data)
                            advanced_content = ADVANCED_CONTENT.format(**content_data)

                            # Create or update lesson
                            lesson, created = Lesson.objects.get_or_create(
                                module=module,
                                title=lesson_data['title'],
                                defaults={
                                    'content': advanced_content,  # Full content for premium users
                                    'intermediate_content': intermediate_content,  # Content for registered users
                                    'basic_content': basic_content,  # Preview content for unregistered users
                                    'access_level': lesson_data['access_level'],  # Required access level
                                    'duration': lesson_data['duration'],  # Lesson duration
                                    'order': j + 1,  # Lesson order within module
                                    'has_assessment': random.choice([True, False])  # Randomly decide if it has an assessment
                                }
                            )

                            if not created:
                                # Update the lesson if it exists
                                lesson.content = advanced_content
                                lesson.intermediate_content = intermediate_content
                                lesson.basic_content = basic_content
                                lesson.access_level = lesson_data['access_level']
                                lesson.duration = lesson_data['duration']
                                lesson.order = j + 1
                                lesson.save()
                                print(f"Updated lesson: {lesson.title}")
                            else:
                                print(f"Created new lesson: {lesson.title}")

                            # Skip resource creation if lesson already exists
                            if not created:
                                continue

                            # Step 6: Create resources for the lesson
                            # Create a basic resource (for all registered users)
                            Resource.objects.create(
                                lesson=lesson,
                                title=f"Basic Guide - {lesson.title}",
                                description="Supplementary materials for registered users",
                                type="document",
                                premium=False
                            )
                            print(f"Created basic resource for lesson: {lesson.title}")

                            # Create a premium resource (only for paid users)
                            if lesson_data['access_level'] == 'advanced':
                                Resource.objects.create(
                                    lesson=lesson,
                                    title=f"Premium Resource - {lesson.title}",
                                    description="Advanced materials for premium subscribers only",
                                    type="document",
                                    premium=True
                                )
                                print(f"Created premium resource for lesson: {lesson.title}")

                        except Exception as e:
                            # Print an error message if something goes wrong with creating a lesson
                            print(f"Error creating lesson '{lesson_data['title']}': {str(e)}")
                except Exception as e:
                    # Print an error message if something goes wrong with creating a module
                    print(f"Error creating module '{module_data['title']}': {str(e)}")
        except Exception as e:
            # Print an error message if something goes wrong with creating a course
            print(f"Error creating course '{course_data['title']}': {str(e)}")

    print("\nCourse creation process completed!")

#####################################################
# PART 6: MAIN EXECUTION
# This section runs the script
#####################################################

if __name__ == "__main__":
    try:
        print("-" * 80)
        print("EDUCATIONAL PLATFORM - TEST COURSE CREATION TOOL")
        print("-" * 80)

        # Create the test courses
        create_test_courses()

        print("\nTest courses created successfully!")
        print("\nNext steps:")
        print("1. Start your Django server: python manage.py runserver")
        print("2. Log in to the admin panel: http://localhost:8000/admin/")
        print("3. Start your frontend: npm run dev (in the frontend directory)")
        print("4. Test with these users:")
        print("   - Unregistered: Use an incognito/private browser window")
        print("   - Registered: Log in with intermediate@example.com / testpassword123")
        print("   - Premium: Log in with premium@example.com / testpassword123")
        print("-" * 80)
    except Exception as e:
        # Print error details if something goes wrong
        print("\nAn error occurred:", e)
        traceback.print_exc()

        # Show troubleshooting tips
        print("\nTROUBLESHOOTING TIPS:")
        print("1. Check that your virtual environment is activated (venv\\Scripts\\activate)")
        print("2. Make sure all required packages are installed (pip install -r requirements.txt)")
        print("3. Verify that your database is properly configured")
        print("4. Make sure your PostgreSQL database is running and accessible")
        print("5. Check if your models are compatible with the field names used in this script")
        print("6. Try running Django migrations: python manage.py migrate")
        print("-" * 80)
