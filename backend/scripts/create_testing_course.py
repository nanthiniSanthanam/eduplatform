#!/usr/bin/env python
# isort: skip_file
# fmt: off
# flake8: noqa: E402
"""
Create or update a comprehensive software testing course in the database.
Author: nanthiniSanthanam
Date: 2025-04-23
Last updated: 2025-04-23 11:55:25 UTC
"""

import os
import sys
import django
import datetime
import logging
from django.utils.text import slugify

# Add the project path to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educore.settings')
django.setup()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("course_creation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Now import Django models AFTER setting up Django

from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from courses.models import (
    Category, Course, CourseInstructor, Module, Lesson,
    Resource, Assessment, Question, Answer
)


User = get_user_model()


def create_or_update_software_testing_course():
    """Create or update a comprehensive software testing course with modules, lessons, and assessments."""
    logger.info("Starting software testing course creation/update...")

    # Get or create admin user
    try:
        admin = User.objects.get(username='admin')
        logger.info("Found admin user")
    except User.DoesNotExist:
        logger.info("Admin user not found. Creating a new admin user...")
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            first_name='Admin',
            last_name='User'
        )

    # Create or update the Software Testing category
    category, created = Category.objects.update_or_create(
        slug='software-testing-category',
        defaults={
            'name': 'Software Testing',
            'description': 'Courses related to software testing methodologies, tools, and best practices for ensuring software quality.',
            'icon': 'bug_report'
        }
    )
    logger.info(
        f"Category {'created' if created else 'updated'}: {category.name}")

    # Create or update the course
    course, created = Course.objects.update_or_create(
        slug='software-testing',
        defaults={
            'title': 'Comprehensive Software Testing Masterclass',
            'subtitle': 'Master the art and science of software quality assurance from fundamentals to advanced techniques',
            'description': '''
            <div class="course-banner">
                <h1>Complete Software Testing Masterclass</h1>
                <p class="course-tagline">From Manual Testing to Automation: Become a Testing Professional</p>
            </div>

            <h2>Course Overview</h2>
            <p>This comprehensive course covers everything you need to know about software testing,
            from basic principles to advanced techniques used in the industry today. Whether you're
            a beginner looking to start a career in software testing or an experienced professional
            seeking to expand your skills, this course provides all the knowledge and practical
            experience you need.</p>

            <p>You'll learn how to design effective test cases, execute tests methodically, report bugs
            professionally, and implement automated testing in your development process. By the end of
            this course, you'll have the skills to ensure software quality and reliability in any project.</p>

            <div class="course-highlights">
                <h3>What you'll learn</h3>
                <ul>
                    <li><strong>Testing Fundamentals</strong>: Principles, methodologies, and best practices</li>
                    <li><strong>Test Planning</strong>: Creating comprehensive test plans and strategies</li>
                    <li><strong>Test Case Design</strong>: Effective techniques like boundary analysis and equivalence partitioning</li>
                    <li><strong>Manual Testing</strong>: Systematic approaches to manual testing</li>
                    <li><strong>Automated Testing</strong>: Introduction to popular automation frameworks</li>
                    <li><strong>API Testing</strong>: Validating APIs using various tools</li>
                    <li><strong>Performance Testing</strong>: Load, stress, and scalability testing</li>
                    <li><strong>Security Testing</strong>: Basics of testing for security vulnerabilities</li>
                    <li><strong>Mobile Testing</strong>: Special considerations for mobile applications</li>
                    <li><strong>DevOps & CI/CD</strong>: Integration of testing in modern development pipelines</li>
                </ul>
            </div>

            <h3>Who is this course for?</h3>
            <ul>
                <li>Beginners looking to start a career in software testing</li>
                <li>Developers who want to improve their testing skills</li>
                <li>QA professionals seeking to update their knowledge</li>
                <li>Project managers who want to understand the testing process</li>
            </ul>

            <div class="instructor-note">
                <h4>A Note from the Instructor</h4>
                <p>Testing is not just a phase in software development—it's a mindset that ensures quality at every step.
                In this course, I'll share my 15+ years of industry experience to help you develop that mindset and
                become a confident testing professional capable of improving any software product.</p>
            </div>
            ''',
            'category': category,
            'price': 119.99,
            'discount_price': 89.99,
            'discount_ends': timezone.now() + datetime.timedelta(days=30),
            'level': 'all_levels',
            'duration': '60 hours',
            'has_certificate': True,
            'is_featured': True,
            'is_published': True,
            'requirements': [
                'Basic understanding of software development concepts',
                'Familiarity with at least one programming language (Python, Java, or JavaScript recommended)',
                'A computer with internet access for practical exercises',
                'No prior testing experience required'
            ],
            'skills': [
                'Software Testing Fundamentals',
                'Test Case Design',
                'Test Planning and Strategy',
                'Manual Testing Techniques',
                'Defect Management',
                'Test Automation',
                'Performance Testing',
                'Mobile Application Testing',
                'API Testing',
                'Security Testing Basics',
                'Test-Driven Development',
                'Continuous Integration/Testing'
            ]
        }
    )
    logger.info(
        f"Course {'created' if created else 'updated'}: {course.title}")

    # Create or update course instructor
    instructor, created = CourseInstructor.objects.update_or_create(
        course=course,
        instructor=admin,
        defaults={
            'title': 'Director of Quality Engineering',
            'bio': '''
            With over 15 years of experience in software quality assurance and testing,
            I've helped companies of all sizes implement effective testing strategies across
            various domains including finance, healthcare, e-commerce, and enterprise software.

            My expertise spans the full testing spectrum from manual testing to test automation,
            performance testing, and integrating testing into CI/CD pipelines. I'm passionate about
            sharing my knowledge to help create the next generation of skilled testing professionals.

            Prior to my teaching career, I served as the QA Director at several Fortune 500 companies,
            leading teams of 50+ QA engineers and establishing quality processes that reduced
            production defects by over 80%.
            ''',
            'is_lead': True
        }
    )
    logger.info(
        f"Instructor {'created' if created else 'updated'}: {instructor.instructor.username}")

    # Create modules
    modules = create_course_modules(course)

    # Create lessons for each module
    for module_index, module_data in enumerate(modules, 1):
        create_module_content(module_data, module_index)

    logger.info(
        "\nSoftware Testing course has been successfully created or updated.")
    logger.info(
        f"Course URL: http://localhost:8000/admin/courses/course/{course.id}/change/")

    return course


def create_course_modules(course):
    """Create or update all modules for the software testing course"""
    modules_data = [
        {
            'title': 'Introduction to Software Testing',
            'description': 'Learn the fundamental concepts, principles, and importance of software testing.',
            'order': 1,
            'duration': '5 hours',
            'lessons': [
                {
                    'title': 'What is Software Testing?',
                    'content': '''
                    <h2>What is Software Testing?</h2>
                    <p>Software testing is the process of evaluating and verifying that a software product or application does what it is supposed to do. The benefits of testing include preventing bugs, reducing development costs, and improving performance.</p>

                    <h3>Key Objectives of Software Testing</h3>
                    <ul>
                        <li><strong>Defect Detection</strong>: Finding bugs or defects in the software</li>
                        <li><strong>Quality Assurance</strong>: Ensuring the software meets quality standards</li>
                        <li><strong>Validation</strong>: Confirming the software meets user requirements</li>
                        <li><strong>Verification</strong>: Checking if the software adheres to specifications</li>
                        <li><strong>Reliability</strong>: Making sure the software performs consistently under various conditions</li>
                    </ul>

                    <h3>Why Software Testing is Important</h3>
                    <p>Software testing is crucial because:</p>
                    <ul>
                        <li>It ensures customer satisfaction by delivering a quality product</li>
                        <li>It improves security and minimizes risks</li>
                        <li>It saves time and cost in the long run by identifying issues early</li>
                        <li>It improves performance and user experience</li>
                    </ul>

                    <div class="note-block">
                        <h4>Remember</h4>
                        <p>Software testing is not just about finding bugs—it's about ensuring quality at every stage of development.</p>
                    </div>

                    <h3>Types of Software Testing at a Glance</h3>
                    <div class="table-container">
                        <table>
                            <tr>
                                <th>Type</th>
                                <th>Description</th>
                                <th>When Performed</th>
                            </tr>
                            <tr>
                                <td>Functional Testing</td>
                                <td>Tests if the application functions as expected</td>
                                <td>After development of a feature</td>
                            </tr>
                            <tr>
                                <td>Non-functional Testing</td>
                                <td>Tests non-functional aspects like performance, usability</td>
                                <td>After functional testing</td>
                            </tr>
                            <tr>
                                <td>Unit Testing</td>
                                <td>Tests individual components or functions</td>
                                <td>During development</td>
                            </tr>
                            <tr>
                                <td>Integration Testing</td>
                                <td>Tests interactions between components</td>
                                <td>After unit testing</td>
                            </tr>
                            <tr>
                                <td>System Testing</td>
                                <td>Tests the complete system</td>
                                <td>After integration testing</td>
                            </tr>
                            <tr>
                                <td>Acceptance Testing</td>
                                <td>Validates if the system meets business requirements</td>
                                <td>Final stage before release</td>
                            </tr>
                        </table>
                    </div>
                    ''',
                    'duration': '45 minutes',
                    'type': 'video',
                    'order': 1,
                    'has_assessment': True,
                    'is_free_preview': True,
                    'assessment': {
                        'title': 'Software Testing Fundamentals Quiz',
                        'description': 'Test your understanding of basic software testing concepts.',
                        'time_limit': 10,  # minutes
                        'passing_score': 70,
                        'questions': [
                            {
                                'text': 'What is the primary goal of software testing?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'To make the software look attractive',
                                        'correct': False},
                                    {'text': 'To find and fix defects in the software',
                                        'correct': True},
                                    {'text': 'To develop the software faster',
                                        'correct': False},
                                    {'text': 'To reduce development costs',
                                        'correct': False}
                                ]
                            },
                            {
                                'text': 'Which of the following is NOT one of the key objectives of software testing?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'Defect detection', 'correct': False},
                                    {'text': 'Quality assurance', 'correct': False},
                                    {'text': 'Code development', 'correct': True},
                                    {'text': 'Reliability assessment',
                                        'correct': False}
                                ]
                            },
                            {
                                'text': 'When should testing ideally begin in the software development lifecycle?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'After the development is complete',
                                        'correct': False},
                                    {'text': 'As early as possible in the development lifecycle',
                                        'correct': True},
                                    {'text': 'Just before releasing the software',
                                        'correct': False},
                                    {'text': 'Only when bugs are reported',
                                        'correct': False}
                                ]
                            }
                        ]
                    }
                },
                {
                    'title': 'Software Testing Principles',
                    'content': '''
                    <h2>Seven Fundamental Principles of Software Testing</h2>
                    <p>There are seven fundamental principles that guide effective software testing:</p>

                    <h3>1. Testing shows the presence of defects, not their absence</h3>
                    <p>Testing can show that defects are present, but cannot prove that there are no defects. Even after thorough testing, we can't guarantee a completely defect-free application.</p>

                    <h3>2. Exhaustive testing is impossible</h3>
                    <p>Testing everything, including all combinations of inputs and preconditions, is not feasible except for trivial cases. Instead of exhaustive testing, we use risk analysis, test techniques, and priorities to focus testing efforts.</p>

                    <h3>3. Early testing</h3>
                    <p>Testing activities should start as early as possible in the software development lifecycle and focus on defined objectives.</p>

                    <h3>4. Defect clustering</h3>
                    <p>Testing efforts should be focused proportionally to the expected and observed defect density of modules. A small number of modules usually contains most of the defects discovered.</p>

                    <h3>5. Pesticide paradox</h3>
                    <p>If the same tests are repeated over and over again, eventually they will no longer find new defects. To overcome this, tests need to be regularly reviewed and revised.</p>

                    <h3>6. Testing is context dependent</h3>
                    <p>Testing is done differently in different contexts. For example, safety-critical software is tested differently from an e-commerce site.</p>

                    <h3>7. Absence-of-errors fallacy</h3>
                    <p>Finding and fixing defects does not help if the system built does not fulfill user needs and expectations.</p>

                    <h3>Applying These Principles in Real Projects</h3>
                    <p>Understanding and applying these principles helps create more effective testing strategies:</p>
                    <ul>
                        <li>Acknowledge that testing will find defects but never prove perfection</li>
                        <li>Be strategic about what to test since you can't test everything</li>
                        <li>Get involved in testing from the beginning of the project</li>
                        <li>Focus testing efforts on areas most likely to contain defects</li>
                        <li>Regularly update your test cases and approaches</li>
                        <li>Adapt your testing approach to the specific project context</li>
                        <li>Remember that zero defects doesn't mean the product meets user needs</li>
                    </ul>

                    <div class="practice-section">
                        <h4>Apply These Principles</h4>
                        <p>Think about a software application you use regularly. How would you apply these principles when testing it?</p>
                    </div>
                    ''',
                    'duration': '60 minutes',
                    'type': 'reading',
                    'order': 2,
                    'has_assessment': True,
                    'assessment': {
                        'title': 'Testing Principles Assessment',
                        'description': 'Test your understanding of the seven principles of software testing.',
                        'time_limit': 15,
                        'passing_score': 70,
                        'questions': [
                            {
                                'text': 'Which principle states that "If the same tests are repeated over and over again, eventually they will no longer find new defects"?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'Pesticide paradox', 'correct': True},
                                    {'text': 'Defect clustering', 'correct': False},
                                    {'text': 'Early testing', 'correct': False},
                                    {'text': 'Absence-of-errors fallacy',
                                        'correct': False}
                                ]
                            },
                            {
                                'text': 'What does the principle "Testing shows the presence of defects, not their absence" mean?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'Testing can only find bugs, not prove they don\'t exist',
                                        'correct': True},
                                    {'text': 'Testing is only useful for finding defects',
                                        'correct': False},
                                    {'text': 'Testing always finds all defects',
                                        'correct': False},
                                    {'text': 'Absence of defects is impossible',
                                        'correct': False}
                                ]
                            },
                            {
                                'text': 'Why is "Exhaustive testing is impossible"?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'Because developers make too many errors',
                                        'correct': False},
                                    {'text': 'Because there are too many possible input combinations to test them all', 'correct': True},
                                    {'text': 'Because testers get tired of testing',
                                        'correct': False},
                                    {'text': 'Because testing tools have limitations',
                                        'correct': False}
                                ]
                            }
                        ]
                    }
                },
                {
                    'title': 'Software Development Lifecycle and Testing',
                    'content': '''
                    <h2>Software Development Lifecycle and Testing</h2>
                    <p>The Software Development Life Cycle (SDLC) is a process used by the software industry to design, develop, and test high-quality software. Testing plays a crucial role at each stage of the SDLC.</p>

                    <div class="video-container">
                        [Video Player: SDLC and Testing]
                    </div>

                    <h3>Testing in Different SDLC Models</h3>

                    <h4>1. Waterfall Model</h4>
                    <p>In the traditional Waterfall model, testing is a distinct phase that comes after the development phase is complete:</p>
                    <ul>
                        <li><strong>Requirements</strong> → <strong>Design</strong> → <strong>Development</strong> → <strong>Testing</strong> → <strong>Deployment</strong> → <strong>Maintenance</strong></li>
                        <li>Testing is comprehensive but occurs late in the cycle</li>
                        <li>Issues found late can be expensive to fix</li>
                    </ul>

                    <h4>2. Agile Model</h4>
                    <p>In Agile development, testing is integrated throughout the development process:</p>
                    <ul>
                        <li>Testing occurs in each sprint or iteration</li>
                        <li>Continuous testing and feedback</li>
                        <li>Test-Driven Development (TDD) may be used</li>
                        <li>Close collaboration between developers and testers</li>
                    </ul>

                    <h4>3. DevOps Model</h4>
                    <p>In DevOps, testing is highly automated and continuous:</p>
                    <ul>
                        <li>Continuous Integration (CI) and Continuous Deployment (CD)</li>
                        <li>Automated testing at multiple levels</li>
                        <li>Quick feedback loops</li>
                        <li>Shift-left approach (testing earlier in the cycle)</li>
                    </ul>

                    <h3>Types of Testing Throughout the SDLC</h3>
                    <div class="table-container">
                        <table>
                            <tr>
                                <th>SDLC Phase</th>
                                <th>Testing Activities</th>
                            </tr>
                            <tr>
                                <td>Requirements</td>
                                <td>
                                    <ul>
                                        <li>Requirements review</li>
                                        <li>Testability analysis</li>
                                        <li>Test planning begins</li>
                                    </ul>
                                </td>
                            </tr>
                            <tr>
                                <td>Design</td>
                                <td>
                                    <ul>
                                        <li>Test strategy development</li>
                                        <li>Test case design</li>
                                        <li>Design reviews</li>
                                    </ul>
                                </td>
                            </tr>
                            <tr>
                                <td>Development</td>
                                <td>
                                    <ul>
                                        <li>Unit testing</li>
                                        <li>Code reviews</li>
                                        <li>Static code analysis</li>
                                    </ul>
                                </td>
                            </tr>
                            <tr>
                                <td>Testing</td>
                                <td>
                                    <ul>
                                        <li>Integration testing</li>
                                        <li>System testing</li>
                                        <li>Performance testing</li>
                                        <li>Security testing</li>
                                    </ul>
                                </td>
                            </tr>
                            <tr>
                                <td>Deployment</td>
                                <td>
                                    <ul>
                                        <li>User acceptance testing</li>
                                        <li>Beta testing</li>
                                        <li>Production verification testing</li>
                                    </ul>
                                </td>
                            </tr>
                            <tr>
                                <td>Maintenance</td>
                                <td>
                                    <ul>
                                        <li>Regression testing</li>
                                        <li>Maintenance testing</li>
                                        <li>Monitoring</li>
                                    </ul>
                                </td>
                            </tr>
                        </table>
                    </div>

                    <h3>Shift-Left Testing</h3>
                    <p>"Shift-Left" is a practice intended to find and fix defects as early as possible in the software development process:</p>
                    <ul>
                        <li>Testing begins at the requirements and design phases</li>
                        <li>Developers perform unit tests as they write code</li>
                        <li>Automated tests are integrated into the development pipeline</li>
                        <li>Benefits include reduced costs, faster delivery, and higher quality</li>
                    </ul>

                    <div class="practice-section">
                        <h4>Discussion Question</h4>
                        <p>How would you integrate testing effectively in an Agile development environment? What specific testing activities would you perform in each sprint?</p>
                    </div>
                    ''',
                    'duration': '75 minutes',
                    'type': 'video',
                    'order': 3,
                    'has_assessment': True,
                    'assessment': {
                        'title': 'SDLC and Testing Quiz',
                        'description': 'Test your understanding of how testing integrates with different SDLC models.',
                        'time_limit': 15,
                        'passing_score': 70,
                        'questions': [
                            {
                                'text': 'In which SDLC model is testing performed as a distinct phase after development is complete?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'Agile', 'correct': False},
                                    {'text': 'DevOps', 'correct': False},
                                    {'text': 'Waterfall', 'correct': True},
                                    {'text': 'Spiral', 'correct': False}
                                ]
                            },
                            {
                                'text': 'What is "Shift-Left" testing?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'Testing only the leftmost modules in the architecture',
                                        'correct': False},
                                    {'text': 'Moving testing activities to earlier stages in the development lifecycle', 'correct': True},
                                    {'text': 'Testing on left-handed devices only',
                                        'correct': False},
                                    {'text': 'A left-to-right testing approach for user interfaces',
                                        'correct': False}
                                ]
                            }
                        ]
                    }
                }
            ]
        },
        {
            'title': 'Testing Types and Methodologies',
            'description': 'Explore different types of software testing and when to use each methodology.',
            'order': 2,
            'duration': '8 hours',
            'lessons': [
                {
                    'title': 'Functional vs. Non-functional Testing',
                    'content': '''
                    <h2>Functional vs. Non-functional Testing</h2>
                    <p>Software testing can be broadly classified into two categories: functional testing and non-functional testing. Each serves different purposes and focuses on different aspects of the software.</p>

                    <div class="video-container">
                        [Video Player: Functional vs. Non-functional Testing]
                    </div>

                    <h3>Functional Testing</h3>
                    <p>Functional testing verifies that each function of the software application works in conformance with the requirement specification. It mainly focuses on:</p>
                    <ul>
                        <li>Main functions of the application</li>
                        <li>Basic usability</li>
                        <li>Error conditions handling</li>
                        <li>Specific user requirements</li>
                    </ul>

                    <h4>Examples of Functional Testing</h4>
                    <ul>
                        <li><strong>Unit Testing</strong>: Testing individual components</li>
                        <li><strong>Integration Testing</strong>: Testing component interactions</li>
                        <li><strong>System Testing</strong>: Testing the entire system</li>
                        <li><strong>Acceptance Testing</strong>: Final testing before delivery</li>
                    </ul>

                    <h3>Non-functional Testing</h3>
                    <p>Non-functional testing verifies aspects of the software that are not related to specific functions or user actions, such as performance, scalability, and usability. It focuses on:</p>
                    <ul>
                        <li>How the system operates, rather than specific behaviors</li>
                        <li>Quality attributes of the system</li>
                        <li>The system under expected and unexpected conditions</li>
                    </ul>

                    <h4>Examples of Non-functional Testing</h4>
                    <ul>
                        <li><strong>Performance Testing</strong>: How the system performs under load</li>
                        <li><strong>Security Testing</strong>: System protection against threats</li>
                        <li><strong>Usability Testing</strong>: How user-friendly the system is</li>
                        <li><strong>Compatibility Testing</strong>: How well the system works in different environments</li>
                        <li><strong>Reliability Testing</strong>: System consistency under expected conditions</li>
                        <li><strong>Scalability Testing</strong>: System's ability to handle growth</li>
                    </ul>

                    <div class="comparison-table">
                        <h4>Comparison: Functional vs. Non-functional Testing</h4>
                        <table>
                            <tr>
                                <th>Aspect</th>
                                <th>Functional Testing</th>
                                <th>Non-functional Testing</th>
                            </tr>
                            <tr>
                                <td>Focus</td>
                                <td>What the system does</td>
                                <td>How well the system does it</td>
                            </tr>
                            <tr>
                                <td>Requirements</td>
                                <td>Functional requirements</td>
                                <td>Non-functional requirements</td>
                            </tr>
                            <tr>
                                <td>Testing Method</td>
                                <td>Black-box testing</td>
                                <td>Both black-box and white-box testing</td>
                            </tr>
                            <tr>
                                <td>Complexity</td>
                                <td>Usually simpler to define and execute</td>
                                <td>Often more complex, requiring special tools</td>
                            </tr>
                            <tr>
                                <td>When Performed</td>
                                <td>Earlier in the testing cycle</td>
                                <td>Usually after functional testing</td>
                            </tr>
                        </table>
                    </div>

                    <h3>When to Use Each Type of Testing</h3>
                    <p>The decision about which type of testing to focus on depends on various factors:</p>
                    <ul>
                        <li><strong>Project Requirements</strong>: What is most critical for your application?</li>
                        <li><strong>User Expectations</strong>: What will users value most?</li>
                        <li><strong>Risk Assessment</strong>: Where are the highest risks?</li>
                        <li><strong>Time and Resources</strong>: What can you realistically test given constraints?</li>
                    </ul>

                    <p>A balanced approach usually involves both functional and non-functional testing, with priorities determined by the specific context of the project.</p>
                    ''',
                    'duration': '75 minutes',
                    'type': 'video',
                    'order': 1,
                    'has_assessment': True,
                    'resources': [
                        {
                            'title': 'Functional Testing Cheat Sheet',
                            'type': 'document',
                            'url': 'https://example.com/resources/functional-testing-cheatsheet.pdf',
                            'description': 'A quick reference guide for functional testing techniques and best practices.'
                        },
                        {
                            'title': 'Non-Functional Testing Tools Overview',
                            'type': 'link',
                            'url': 'https://example.com/resources/non-functional-testing-tools',
                            'description': 'An overview of popular tools used for different types of non-functional testing.'
                        }
                    ],
                    'assessment': {
                        'title': 'Functional vs. Non-functional Testing Quiz',
                        'description': 'Test your understanding of functional and non-functional testing concepts.',
                        'time_limit': 15,
                        'passing_score': 70,
                        'questions': [
                            {
                                'text': 'Which of the following is a non-functional testing type?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'Unit testing', 'correct': False},
                                    {'text': 'Integration testing',
                                        'correct': False},
                                    {'text': 'Performance testing', 'correct': True},
                                    {'text': 'System testing', 'correct': False}
                                ]
                            },
                            {
                                'text': 'What is the main focus of functional testing?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'How well the system performs',
                                        'correct': False},
                                    {'text': 'What the system does',
                                        'correct': True},
                                    {'text': 'How secure the system is',
                                        'correct': False},
                                    {'text': 'How easy the system is to use',
                                        'correct': False}
                                ]
                            }
                        ]
                    }
                },
                {
                    'title': 'Black Box vs. White Box Testing',
                    'content': '''
                    <h2>Black Box vs. White Box Testing</h2>
                    <p>Software testing techniques can be classified based on the knowledge and perspective of the tester regarding the internal workings of the system. The two main approaches are Black Box and White Box testing.</p>

                    <h3>Black Box Testing</h3>
                    <p>Black Box Testing is a testing technique where the tester doesn't know the internal structure, design, or implementation of the item being tested. The tester is only aware of what the software is supposed to do, not how it does it.</p>

                    <h4>Characteristics of Black Box Testing:</h4>
                    <ul>
                        <li>Tester has no knowledge of the internal code</li>
                        <li>Tests are based on requirements and specifications</li>
                        <li>Testing is done from a user's perspective</li>
                        <li>Can be performed by non-technical testers</li>
                    </ul>

                    <h4>When to Use Black Box Testing:</h4>
                    <ul>
                        <li>When testing user interfaces</li>
                        <li>For acceptance testing</li>
                        <li>When testing large systems where knowing the code is impractical</li>
                        <li>When an independent testing perspective is needed</li>
                    </ul>

                    <h4>Black Box Testing Techniques:</h4>
                    <ul>
                        <li><strong>Equivalence Partitioning</strong>: Dividing input data into partitions</li>
                        <li><strong>Boundary Value Analysis</strong>: Testing at the boundaries of input domains</li>
                        <li><strong>Decision Table Testing</strong>: Testing different combinations of inputs and conditions</li>
                        <li><strong>Use Case Testing</strong>: Testing based on user scenarios</li>
                    </ul>

                    <h3>White Box Testing</h3>
                    <p>White Box Testing (also known as Clear Box or Glass Box Testing) is a testing technique where the tester has knowledge of the internal structure, design, and implementation of the item being tested.</p>

                    <h4>Characteristics of White Box Testing:</h4>
                    <ul>
                        <li>Tester has knowledge of the code and internal structure</li>
                        <li>Tests are based on code paths, conditions, and branches</li>
                        <li>Testing focuses on how the software works</li>
                        <li>Typically requires programming knowledge</li>
                    </ul>

                    <h4>When to Use White Box Testing:</h4>
                    <ul>
                        <li>During unit testing by developers</li>
                        <li>When testing complex algorithms</li>
                        <li>To ensure all code paths are executed</li>
                        <li>For security testing to find vulnerabilities</li>
                    </ul>

                    <h4>White Box Testing Techniques:</h4>
                    <ul>
                        <li><strong>Statement Coverage</strong>: Ensuring each statement is executed</li>
                        <li><strong>Branch Coverage</strong>: Ensuring each branch is executed</li>
                        <li><strong>Path Coverage</strong>: Ensuring all paths through the code are executed</li>
                        <li><strong>Condition Coverage</strong>: Testing each boolean expression</li>
                    </ul>

                    <h3>Gray Box Testing</h3>
                    <p>Gray Box Testing is a hybrid of both Black Box and White Box testing, where the tester has partial knowledge of the internal workings of the application.</p>

                    <h4>Characteristics of Gray Box Testing:</h4>
                    <ul>
                        <li>Tester has limited knowledge of internals</li>
                        <li>Tests are based on high-level design documents and database diagrams</li>
                        <li>Combines both Black Box and White Box approaches</li>
                    </ul>

                    <div class="comparison-table">
                        <h4>Comparison: Black Box vs. White Box vs. Gray Box Testing</h4>
                        <table>
                            <tr>
                                <th>Aspect</th>
                                <th>Black Box Testing</th>
                                <th>White Box Testing</th>
                                <th>Gray Box Testing</th>
                            </tr>
                            <tr>
                                <td>Knowledge of Internal Code</td>
                                <td>None</td>
                                <td>Complete</td>
                                <td>Partial</td>
                            </tr>
                            <tr>
                                <td>Testing Perspective</td>
                                <td>User perspective</td>
                                <td>Developer perspective</td>
                                <td>Mixed perspective</td>
                            </tr>
                            <tr>
                                <td>Technical Knowledge Required</td>
                                <td>Low</td>
                                <td>High</td>
                                <td>Medium</td>
                            </tr>
                            <tr>
                                <td>Typical Testing Level</td>
                                <td>System, acceptance</td>
                                <td>Unit, integration</td>
                                <td>Integration</td>
                            </tr>
                        </table>
                    </div>

                    <div class="practice-section">
                        <h4>Practical Exercise</h4>
                        <p>Consider a web-based email application. Describe:</p>
                        <ol>
                            <li>Three test cases you would design using the black box approach</li>
                            <li>Three test cases you would design using the white box approach</li>
                            <li>Two test cases that would benefit from a gray box approach</li>
                        </ol>
                    </div>
                    ''',
                    'duration': '60 minutes',
                    'type': 'reading',
                    'order': 2,
                    'has_assessment': True,
                    'assessment': {
                        'title': 'Testing Approaches Quiz',
                        'description': 'Test your understanding of Black Box, White Box, and Gray Box testing approaches.',
                        'time_limit': 15,
                        'passing_score': 70,
                        'questions': [
                            {
                                'text': 'Which testing technique requires knowledge of the internal code structure?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'Black Box Testing', 'correct': False},
                                    {'text': 'White Box Testing', 'correct': True},
                                    {'text': 'Beta Testing', 'correct': False},
                                    {'text': 'Exploratory Testing', 'correct': False}
                                ]
                            },
                            {
                                'text': 'Statement coverage is a technique used in which testing approach?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'Black Box Testing', 'correct': False},
                                    {'text': 'White Box Testing', 'correct': True},
                                    {'text': 'Usability Testing', 'correct': False},
                                    {'text': 'Acceptance Testing', 'correct': False}
                                ]
                            },
                            {
                                'text': 'Gray Box Testing is characterized by:',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'No knowledge of internal code',
                                        'correct': False},
                                    {'text': 'Complete knowledge of internal code',
                                        'correct': False},
                                    {'text': 'Partial knowledge of internal code',
                                        'correct': True},
                                    {'text': 'Testing only by developers',
                                        'correct': False}
                                ]
                            }
                        ]
                    }
                }
            ]
        },
        {
            'title': 'Test Design Techniques',
            'description': 'Learn how to design effective tests using proven techniques.',
            'order': 3,
            'duration': '10 hours',
            'lessons': [
                {
                    'title': 'Equivalence Partitioning',
                    'content': '''
                    <h2>Equivalence Partitioning</h2>
                    <p>Equivalence partitioning is a test design technique that divides input data into partitions (or equivalence classes) such that testing one value from each partition is equivalent to testing all values in that partition.</p>

                    <h3>Why Use Equivalence Partitioning?</h3>
                    <p>This technique helps reduce the number of test cases while maintaining good test coverage. Instead of testing every possible input, you test one representative value from each group of inputs that should be processed similarly.</p>

                    <h3>How to Apply Equivalence Partitioning</h3>
                    <ol>
                        <li>Identify the input domains for the system under test</li>
                        <li>Divide each input domain into equivalence classes (valid and invalid)</li>
                        <li>Select test cases from each equivalence class</li>
                    </ol>

                    <h3>Example: Testing an Age Input Field</h3>
                    <p>For an age field that accepts values from 18 to 65, we can define these equivalence classes:</p>
                    <ul>
                        <li><strong>Valid class</strong>: 18-65 (test value: 30)</li>
                        <li><strong>Invalid class 1</strong>: Less than 18 (test value: 15)</li>
                        <li><strong>Invalid class 2</strong>: Greater than 65 (test value: 70)</li>
                        <li><strong>Invalid class 3</strong>: Non-numeric values (test value: "ABC")</li>
                    </ul>

                    <p>By testing these four values, we effectively test the entire range of possible inputs without needing to test every single age value.</p>

                    <h3>More Complex Example: Email Validation</h3>
                    <p>For an email address field, we might define these equivalence classes:</p>

                    <h4>Valid Classes:</h4>
                    <ul>
                        <li>Standard format (test value: "user@example.com")</li>
                        <li>With subdomain (test value: "user@subdomain.example.com")</li>
                        <li>With numbers (test value: "user123@example.com")</li>
                        <li>With special characters (test value: "user.name+tag@example.com")</li>
                    </ul>

                    <h4>Invalid Classes:</h4>
                    <ul>
                        <li>Missing @ symbol (test value: "userexample.com")</li>
                        <li>Missing domain (test value: "user@")</li>
                        <li>Multiple @ symbols (test value: "user@domain@example.com")</li>
                        <li>Invalid characters (test value: "user!@example.com")</li>
                        <li>Missing username (test value: "@example.com")</li>
                    </ul>

                    <h3>Benefits of Equivalence Partitioning</h3>
                    <ul>
                        <li>Reduces the number of test cases needed</li>
                        <li>Provides systematic coverage of inputs</li>
                        <li>Helps identify classes of inputs that might be forgotten</li>
                        <li>Can be applied to many types of inputs (not just numeric)</li>
                    </ul>

                    <h3>Limitations</h3>
                    <ul>
                        <li>May not catch errors at boundaries of equivalence classes</li>
                        <li>Complex relationships between inputs may be missed</li>
                        <li>Not sufficient for testing combined conditions or multi-variable dependencies</li>
                    </ul>

                    <div class="practice-section">
                        <h4>Practice Exercise</h4>
                        <p>Consider a system that accepts credit card payments. The valid card number length is 16 digits. Identify the equivalence classes for testing the card number field and specify a representative value for each class.</p>
                    </div>
                    ''',
                    'duration': '60 minutes',
                    'type': 'video',
                    'order': 1,
                    'has_assessment': True,
                    'assessment': {
                        'title': 'Equivalence Partitioning Quiz',
                        'description': 'Test your understanding of equivalence partitioning concepts and application.',
                        'time_limit': 15,
                        'passing_score': 70,
                        'questions': [
                            {
                                'text': 'What is the main purpose of equivalence partitioning?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'To test every possible input value',
                                        'correct': False},
                                    {'text': 'To test boundary values only',
                                        'correct': False},
                                    {'text': 'To reduce the number of test cases while maintaining good coverage', 'correct': True},
                                    {'text': 'To focus on complex error conditions',
                                        'correct': False}
                                ]
                            },
                            {
                                'text': 'For a field that accepts values between 0 and 100, how many equivalence classes would you typically identify?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': '1 (all values between 0 and 100)',
                                                 'correct': False},
                                    {'text': '2 (valid: 0-100, invalid: all other values)',
                                                 'correct': False},
                                    {'text': '3 (invalid: < 0, valid: 0-100, invalid: > 100)',
                                                 'correct': True},
                                    {'text': '101 (one for each possible value)',
                                                   'correct': False}
                                ]
                            },
                            {
                                'text': 'When applying equivalence partitioning to test a login form, which of the following is NOT a valid equivalence class?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'Valid usernames', 'correct': False},
                                    {'text': 'Empty usernames', 'correct': False},
                                    {'text': 'Usernames with special characters',
                                        'correct': False},
                                    {'text': 'The specific username "admin"',
                                        'correct': True}
                                ]
                            }
                        ]
                    }
                },
                {
                    'title': 'Boundary Value Analysis',
                    'content': '''
                    <h2>Boundary Value Analysis</h2>
                    <p>Boundary Value Analysis is a test design technique that focuses on testing at the boundaries of equivalence partitions. It's based on the observation that errors tend to occur at the boundaries of input domains rather than in the center.</p>

                    <h3>Why Boundary Value Analysis?</h3>
                    <p>Many defects occur at the boundaries of valid ranges. For example, if a field accepts values from 1 to 100, the boundaries (1 and 100) and their adjacent values (0 and 101) are more likely to reveal defects.</p>

                    <h3>How to Apply Boundary Value Analysis</h3>
                    <ol>
                        <li>Identify the boundaries of each equivalence partition</li>
                        <li>Select test cases at the boundaries and just inside/outside the boundaries</li>
                        <li>For a range a to b, test: a-1, a, a+1, b-1, b, b+1</li>
                    </ol>

                    <h3>Example: Testing a Date Range</h3>
                    <p>For a hotel booking system that allows bookings from January 1 to December 31:</p>
                    <ul>
                        <li>Lower boundary tests: December 31 (previous year), January 1, January 2</li>
                        <li>Upper boundary tests: December 30, December 31, January 1 (next year)</li>
                    </ul>

                    <h3>Detailed Example: Age Verification System</h3>
                    <p>Consider a system that verifies age for different services:</p>
                    <ul>
                        <li>Under 13: Cannot create an account</li>
                        <li>13-17: Can create an account with parental consent</li>
                        <li>18+: Can create an account without restrictions</li>
                    </ul>

                    <p>Using Boundary Value Analysis, we would test:</p>
                    <ul>
                        <li>Ages 12, 13, 14 (boundary between "Cannot create" and "Parental consent")</li>
                        <li>Ages 17, 18, 19 (boundary between "Parental consent" and "No restrictions")</li>
                    </ul>

                    <h3>Two-Boundary Analysis</h3>
                    <p>For a single input with a range, test these 6 values:</p>
                    <ul>
                        <li>Minimum - 1 (just below lower boundary)</li>
                        <li>Minimum (lower boundary)</li>
                        <li>Minimum + 1 (just above lower boundary)</li>
                        <li>Maximum - 1 (just below upper boundary)</li>
                        <li>Maximum (upper boundary)</li>
                        <li>Maximum + 1 (just above upper boundary)</li>
                    </ul>

                    <h3>Three-Boundary Analysis</h3>
                    <p>When there are three boundaries (e.g., a range divided into sections), test values at and around each boundary.</p>

                    <h3>Benefits of Boundary Value Analysis</h3>
                    <ul>
                        <li>Finds defects that occur at the edges of ranges</li>
                        <li>Complements equivalence partitioning</li>
                        <li>Reveals off-by-one errors (very common in programming)</li>
                        <li>Effective for numerical inputs and ranges</li>
                    </ul>

                    <h3>When to Use with Other Techniques</h3>
                    <p>Boundary Value Analysis works best when combined with:</p>
                    <ul>
                        <li>Equivalence Partitioning (for defining the boundaries)</li>
                        <li>Decision Table Testing (for complex combinations)</li>
                        <li>Error Guessing (for identifying potential boundary issues)</li>
                    </ul>

                    <div class="lab-exercise">
                        <h4>Interactive Lab Exercise: Boundary Testing</h4>
                        <p>In this lab, you'll apply boundary value analysis to test a shopping cart system that:</p>
                        <ul>
                            <li>Allows 1-10 items per product</li>
                            <li>Offers a 10% discount for orders over $100</li>
                            <li>Charges shipping of $5 for orders under $50, free shipping otherwise</li>
                            <li>Requires a minimum order of $10</li>
                        </ul>
                        <p>Your task is to design test cases using boundary value analysis and execute them in the simulated system.</p>
                        <button class="lab-button">Open Virtual Lab</button>
                    </div>
                    ''',
                    'duration': '90 minutes',
                    'type': 'interactive',
                    'order': 2,
                    'has_lab': True,
                    'assessment': {
                        'title': 'Boundary Value Analysis Quiz',
                        'description': 'Test your understanding of boundary value analysis concepts.',
                        'time_limit': 15,
                        'passing_score': 70,
                        'questions': [
                            {
                                'text': 'For an input field that accepts values from 1 to 100, which values would you test using boundary value analysis?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': '1, 50, 100', 'correct': False},
                                    {'text': '0, 1, 2, 99, 100, 101',
                                        'correct': True},
                                    {'text': '1, 100', 'correct': False},
                                    {'text': '0, 50, 101', 'correct': False}
                                ]
                            },
                            {
                                'text': 'Why is boundary value analysis effective?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'Because it tests all possible values',
                                        'correct': False},
                                    {'text': 'Because errors often occur at boundary conditions',
                                        'correct': True},
                                    {'text': "Because it's faster than other techniques", 'correct': False},
                                    {'text': 'Because it only requires one test case', 'correct': False}
                                ]
                            },
                            {
                                'text': 'Which of these is NOT a value you would typically test when analyzing the boundary for an age field that accepts adults (18+)?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': '17', 'correct': False},
                                    {'text': '18', 'correct': False},
                                    {'text': '19', 'correct': False},
                                    {'text': '30', 'correct': True}
                                ]
                            }
                        ]
                    }
                },
                {
                    'title': 'Decision Tables and State Transition Testing',
                    'content': '''
                    <h2>Decision Tables and State Transition Testing</h2>
                    <p>This lesson covers two powerful test design techniques that are particularly useful for complex logic and systems with states.</p>
                    
                    <h3>Decision Table Testing</h3>
                    <p>Decision table testing is a systematic approach for testing systems where different combinations of inputs or conditions produce different actions or outputs.</p>
                    
                    <h4>When to Use Decision Table Testing</h4>
                    <ul>
                        <li>When requirements contain logical conditions (if-then-else)</li>
                        <li>When multiple conditions affect a single outcome</li>
                        <li>When business rules are complex</li>
                        <li>When testing combinations of inputs</li>
                    </ul>
                    
                    <h4>How to Create a Decision Table</h4>
                    <ol>
                        <li>Identify all conditions (inputs)</li>
                        <li>Determine all possible actions (outputs)</li>
                        <li>List all combinations of conditions</li>
                        <li>Determine the expected outcome for each combination</li>
                    </ol>
                    
                    <h4>Example: Insurance Premium Calculator</h4>
                    <p>Consider a system that calculates insurance premiums based on:</p>
                    <ul>
                        <li>Age: Under 25 or 25 and over</li>
                        <li>Driving Record: Clean or With Violations</li>
                        <li>Car Type: Economy or Luxury</li>
                    </ul>
                    
                    <div class="table-container">
                        <table>
                            <tr>
                                <th colspan="8">Decision Table</th>
                            </tr>
                            <tr>
                                <th colspan="3">Conditions</th>
                                <th colspan="5">Rules</th>
                            </tr>
                            <tr>
                                <td>Age under 25</td>
                                <td>Clean Record</td>
                                <td>Luxury Car</td>
                                <td>1</td>
                                <td>2</td>
                                <td>3</td>
                                <td>4</td>
                                <td>5</td>
                            </tr>
                            <tr>
                                <td>Yes</td>
                                <td>Yes</td>
                                <td>Yes</td>
                                <td>X</td>
                                <td></td>
                                <td></td>
                                <td></td>
                                <td></td>
                            </tr>
                            <tr>
                                <td>Yes</td>
                                <td>Yes</td>
                                <td>No</td>
                                <td></td>
                                <td>X</td>
                                <td></td>
                                <td></td>
                                <td></td>
                            </tr>
                            <tr>
                                <td>Yes</td>
                                <td>No</td>
                                <td>-</td>
                                <td></td>
                                <td></td>
                                <td>X</td>
                                <td></td>
                                <td></td>
                            </tr>
                            <tr>
                                <td>No</td>
                                <td>Yes</td>
                                <td>-</td>
                                <td></td>
                                <td></td>
                                <td></td>
                                <td>X</td>
                                <td></td>
                            </tr>
                            <tr>
                                <td>No</td>
                                <td>No</td>
                                <td>-</td>
                                <td></td>
                                <td></td>
                                <td></td>
                                <td></td>
                                <td>X</td>
                            </tr>
                            <tr>
                                <th colspan="3">Actions</th>
                                <th colspan="5"></th>
                            </tr>
                            <tr>
                                <td colspan="3">Premium Rate</td>
                                <td>High</td>
                                <td>Medium</td>
                                <td>Very High</td>
                                <td>Standard</td>
                                <td>High</td>
                            </tr>
                            <tr>
                                <td colspan="3">Discount Eligible</td>
                                <td>No</td>
                                <td>Yes</td>
                                <td>No</td>
                                <td>Yes</td>
                                <td>No</td>
                            </tr>
                        </table>
                    </div>
                    
                    <p>Each column represents a test case to execute.</p>
                    
                    <h3>State Transition Testing</h3>
                    <p>State transition testing is used when a system can exist in several different states and transitions between states are triggered by events or conditions.</p>
                    
                    <h4>When to Use State Transition Testing</h4>
                    <ul>
                        <li>For systems with clearly defined states</li>
                        <li>When testing workflow processes</li>
                        <li>For menu-driven applications</li>
                        <li>When testing transaction processing systems</li>
                        <li>For embedded systems with state machines</li>
                    </ul>
                    
                    <h4>How to Apply State Transition Testing</h4>
                    <ol>
                        <li>Identify all possible states of the system</li>
                        <li>Determine events or conditions that cause state transitions</li>
                        <li>Create a state transition diagram or table</li>
                        <li>Design test cases to cover states, events, and transitions</li>
                    </ol>
                    
                    <h4>Example: Online Order Processing</h4>
                    <p>Consider an online order with states:</p>
                    <ul>
                        <li>New</li>
                        <li>Payment Pending</li>
                        <li>Paid</li>
                        <li>Processing</li>
                        <li>Shipped</li>
                        <li>Delivered</li>
                        <li>Canceled</li>
                    </ul>
                    
                    <p>State transition diagram for this would show transitions like:</p>
                    <ul>
                        <li>New → Payment Pending: User submits order</li>
                        <li>Payment Pending → Paid: Payment received</li>
                        <li>Payment Pending → Canceled: Payment timeout</li>
                        <li>Paid → Processing: Order verified</li>
                        <li>Processing → Shipped: Packaging complete</li>
                        <li>Shipped → Delivered: Delivery confirmed</li>
                        <li>Any state except Delivered → Canceled: Cancellation request</li>
                    </ul>
                    
                    <h4>Test Coverage Levels for State Transition Testing</h4>
                    <ul>
                        <li><strong>0-switch coverage</strong>: Test all states</li>
                        <li><strong>1-switch coverage</strong>: Test all transitions</li>
                        <li><strong>2-switch coverage</strong>: Test all pairs of transitions</li>
                        <li><strong>N-switch coverage</strong>: Test all sequences of N transitions</li>
                    </ul>
                    
                    <h3>Combining These Techniques</h3>
                    <p>Decision tables and state transition testing can be combined for complex systems:</p>
                    <ul>
                        <li>Use decision tables to determine state transitions</li>
                        <li>Use state transition testing to follow the flow through the system</li>
                        <li>Create test scenarios that cover both logical conditions and state sequences</li>
                    </ul>
                    
                    <div class="practice-section">
                        <h4>Practice Exercise</h4>
                        <p>Consider a simple ATM machine with the following states: Idle, Card Inserted, PIN Entered, Transaction Selection, Processing Transaction, Dispensing Cash, Printing Receipt, and Ejecting Card.</p>
                        <ol>
                            <li>Draw a state transition diagram for this ATM</li>
                            <li>Design 5 test cases using state transition testing</li>
                        </ol>
                    </div>
                    ''',
                    'duration': '75 minutes',
                                        'type': 'video',
                    'order': 3,
                    'has_assessment': True,
                    'assessment': {
                        'title': 'Decision Tables and State Transition Testing Quiz',
                        'description': 'Test your understanding of decision tables and state transition testing concepts.',
                        'time_limit': 20,
                        'passing_score': 70,
                        'questions': [
                            {
                                'text': 'When would you use decision table testing?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'For systems with clearly defined states', 'correct': False},
                                    {'text': 'When requirements contain logical conditions (if-then-else)', 'correct': True},
                                    {'text': 'For performance testing', 'correct': False},
                                    {'text': 'When testing UI elements', 'correct': False}
                                ]
                            },
                            {
                                'text': 'What is a key component of state transition testing?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'Identifying all possible states of the system', 'correct': True},
                                    {'text': 'Creating truth tables', 'correct': False},
                                    {'text': 'Testing all possible input values', 'correct': False},
                                    {'text': 'Identifying all SQL queries', 'correct': False}
                                ]
                            },
                            {
                                'text': 'What does "1-switch coverage" mean in state transition testing?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'Testing all states', 'correct': False},
                                    {'text': 'Testing all transitions', 'correct': True},
                                    {'text': 'Testing the system once', 'correct': False},
                                    {'text': 'Testing with one user', 'correct': False}
                                ]
                            }
                        ]
                    }
                }
            ]
        },
        {
            'title': 'Test Planning and Management',
            'description': 'Learn how to plan, document, and manage the testing process.',
            'order': 4,
            'duration': '8 hours',
            'lessons': [
                {
                    'title': 'Test Planning and Strategy',
                    'content': '''
                    <h2>Test Planning and Strategy</h2>
                    <p>A well-defined test plan and strategy are essential for effective software testing. They provide structure, direction, and clarity about what needs to be tested, how it will be tested, and what resources are required.</p>
                    
                    <h3>Test Strategy vs. Test Plan</h3>
                    <div class="comparison-table">
                        <table>
                            <tr>
                                <th>Test Strategy</th>
                                <th>Test Plan</th>
                            </tr>
                            <tr>
                                <td>High-level document</td>
                                <td>Detailed document</td>
                            </tr>
                            <tr>
                                <td>Organization-wide approach</td>
                                <td>Project-specific approach</td>
                            </tr>
                            <tr>
                                <td>Created by senior QA management</td>
                                <td>Created by test lead/manager</td>
                            </tr>
                            <tr>
                                <td>Rarely changes</td>
                                <td>May be updated throughout the project</td>
                            </tr>
                            <tr>
                                <td>Defines testing standards</td>
                                <td>Implements standards for a specific project</td>
                            </tr>
                        </table>
                    </div>
                    
                    <h3>Components of a Test Strategy</h3>
                    <ol>
                        <li><strong>Testing Objectives</strong>: The overall goals of testing</li>
                        <li><strong>Testing Scope</strong>: What will and won't be tested</li>
                        <li><strong>Testing Types</strong>: Which testing approaches will be used</li>
                        <li><strong>Testing Levels</strong>: How testing will be conducted at different levels (unit, integration, etc.)</li>
                        <li><strong>Resource Planning</strong>: People, environments, and tools needed</li>
                        <li><strong>Risk and Contingency Plans</strong>: How to handle risks and issues</li>
                    </ol>
                    
                    <h3>Test Plan Structure (IEEE 829 Format)</h3>
                    <ol>
                        <li><strong>Test Plan Identifier</strong>: Unique identifier for the document</li>
                        <li><strong>Introduction</strong>: Purpose, scope, objectives, and background</li>
                        <li><strong>Test Items</strong>: Software components to be tested</li>
                        <li><strong>Features to be Tested</strong>: List of features and functionality to test</li>
                        <li><strong>Features Not to be Tested</strong>: Features explicitly excluded from testing</li>
                        <li><strong>Approach</strong>: Overall approach to testing</li>
                        <li><strong>Item Pass/Fail Criteria</strong>: How to determine if a test passes or fails</li>
                        <li><strong>Suspension Criteria and Resumption Requirements</strong>: When to pause and resume testing</li>
                        <li><strong>Test Deliverables</strong>: Documents and other artifacts to be delivered</li>
                        <li><strong>Testing Tasks</strong>: Specific activities and responsibilities</li>
                        <li><strong>Environmental Needs</strong>: Hardware, software, and network requirements</li>
                        <li><strong>Responsibilities</strong>: Who does what</li>
                        <li><strong>Staffing and Training Needs</strong>: Required skills and training</li>
                        <li><strong>Schedule</strong>: Timeline and milestones</li>
                        <li><strong>Risks and Contingencies</strong>: What could go wrong and how to handle it</li>
                        <li><strong>Approvals</strong>: Signatures of relevant stakeholders</li>
                    </ol>
                    
                    <h3>Risk-Based Testing</h3>
                    <p>Risk-based testing prioritizes testing effort based on the risk of failure and the impact of potential failures.</p>
                    
                    <h4>Steps in Risk-Based Testing:</h4>
                    <ol>
                        <li>Identify risks (technical, business, operational)</li>
                        <li>Analyze risks (probability and impact)</li>
                        <li>Prioritize risks</li>
                        <li>Develop test strategy based on risk analysis</li>
                        <li>Execute tests in order of risk priority</li>
                        <li>Reassess risks regularly</li>
                    </ol>
                    
                    <h4>Risk Assessment Matrix:</h4>
                    <div class="table-container">
                        <table>
                            <tr>
                                <th></th>
                                <th colspan="3">Probability</th>
                            </tr>
                            <tr>
                                <th>Impact</th>
                                <th>Low</th>
                                <th>Medium</th>
                                <th>High</th>
                            </tr>
                            <tr>
                                <th>High</th>
                                <td class="medium-risk">Medium Risk</td>
                                <td class="high-risk">High Risk</td>
                                <td class="critical-risk">Critical Risk</td>
                            </tr>
                            <tr>
                                <th>Medium</th>
                                <td class="low-risk">Low Risk</td>
                                <td class="medium-risk">Medium Risk</td>
                                <td class="high-risk">High Risk</td>
                            </tr>
                            <tr>
                                <th>Low</th>
                                <td class="very-low-risk">Very Low Risk</td>
                                <td class="low-risk">Low Risk</td>
                                <td class="medium-risk">Medium Risk</td>
                            </tr>
                        </table>
                    </div>
                    
                    <h3>Test Estimation Techniques</h3>
                    <ul>
                        <li><strong>Expert Judgment</strong>: Relies on experienced testers/managers</li>
                        <li><strong>Analogous Estimation</strong>: Based on similar past projects</li>
                        <li><strong>Three-Point Estimation</strong>: (Optimistic + 4x Most Likely + Pessimistic) ÷ 6</li>
                        <li><strong>Function Point Analysis</strong>: Based on functional complexity</li>
                        <li><strong>Test Point Analysis</strong>: Based on test case complexity</li>
                        <li><strong>Use Case Point Method</strong>: Based on use case complexity</li>
                    </ul>
                    
                    <h3>Test Metrics and KPIs</h3>
                    <p>Key metrics to track during testing:</p>
                    <ul>
                        <li><strong>Test Case Execution Rate</strong>: Tests executed vs. planned per day/week</li>
                        <li><strong>Defect Density</strong>: Number of defects per size unit (KLOC or Function Point)</li>
                        <li><strong>Defect Detection Percentage</strong>: Defects found during testing vs. total defects</li>
                        <li><strong>Test Coverage</strong>: Percentage of requirements/code covered by tests</li>
                        <li><strong>Test Effectiveness</strong>: Defects found by testing vs. total defects</li>
                        <li><strong>Average Time to Fix</strong>: Time from defect reporting to resolution</li>
                    </ul>
                    
                    <div class="practice-section">
                        <h4>Practice Exercise</h4>
                        <p>For a mobile banking application, create a high-level test plan covering:</p>
                        <ul>
                            <li>Test objectives</li>
                            <li>Features to be tested</li>
                            <li>Features not to be tested</li>
                            <li>Top three testing risks and mitigation strategies</li>
                            <li>Key test metrics to track</li>
                        </ul>
                    </div>
                    ''',
                    'duration': '90 minutes',
                    'type': 'reading',
                    'order': 1,
                    'has_assessment': True,
                    'resources': [
                        {
                            'title': 'Test Plan Template (IEEE 829)',
                            'type': 'document',
                            'url': 'https://example.com/resources/test-plan-template.docx',
                            'description': 'Standard test plan template following IEEE 829 format.'
                        },
                        {
                            'title': 'Risk Assessment Matrix Spreadsheet',
                            'type': 'document',
                            'url': 'https://example.com/resources/risk-assessment-tool.xlsx',
                            'description': 'Spreadsheet tool for risk-based test prioritization.'
                        }
                    ],
                    'assessment': {
                        'title': 'Test Planning and Strategy Quiz',
                        'description': 'Test your understanding of test planning concepts and techniques.',
                        'time_limit': 20,
                        'passing_score': 70,
                        'questions': [
                            {
                                'text': 'Which of the following is a difference between a test strategy and a test plan?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'Test strategy is project-specific while test plan is organization-wide', 'correct': False},
                                    {'text': 'Test strategy is high-level while test plan is detailed', 'correct': True},
                                    {'text': 'Test strategy is created by developers while test plan is created by testers', 'correct': False},
                                    {'text': 'Test strategy focuses on automation while test plan focuses on manual testing', 'correct': False}
                                ]
                            },
                            {
                                'text': 'What is the purpose of risk-based testing?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'To avoid testing risky features', 'correct': False},
                                    {'text': 'To prioritize testing effort based on risk levels', 'correct': True},
                                    {'text': 'To eliminate all project risks', 'correct': False},
                                    {'text': 'To test only high-risk features', 'correct': False}
                                ]
                            },
                            {
                                'text': 'Which test estimation technique uses the formula: (Optimistic + 4x Most Likely + Pessimistic) ÷ 6?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'Expert Judgment', 'correct': False},
                                    {'text': 'Function Point Analysis', 'correct': False},
                                    {'text': 'Three-Point Estimation', 'correct': True},
                                    {'text': 'Test Point Analysis', 'correct': False}
                                ]
                            },
                            {
                                'text': 'What does "defect density" measure?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'The total number of defects', 'correct': False},
                                    {'text': 'The number of defects per size unit (e.g., per KLOC)', 'correct': True},
                                    {'text': 'The complexity of defects', 'correct': False},
                                    {'text': 'The time taken to fix defects', 'correct': False}
                                ]
                            }
                        ]
                    }
                },
                {
                    'title': 'Test Documentation',
                    'content': '''
                    <h2>Test Documentation</h2>
                    <p>Comprehensive and well-structured test documentation is essential for effective testing. It provides clarity, consistency, and traceability throughout the testing process.</p>
                    
                    <h3>Types of Test Documentation</h3>
                    
                    <h4>1. Test Policy</h4>
                    <p>A high-level document that outlines the principles, approach, and major objectives of the testing organization.</p>
                    <ul>
                        <li>Purpose and goals of testing</li>
                        <li>Testing philosophy and principles</li>
                        <li>Roles and responsibilities</li>
                        <li>Quality standards and metrics</li>
                    </ul>
                    
                    <h4>2. Test Strategy</h4>
                    <p>Defines the general approach to testing across projects or the organization.</p>
                    <ul>
                        <li>Testing levels and types</li>
                        <li>Tools and environments</li>
                        <li>General test processes</li>
                        <li>Risk and mitigation approaches</li>
                    </ul>
                    
                    <h4>3. Test Plan</h4>
                    <p>A detailed document for a specific project that outlines the scope, approach, resources, and schedule for testing.</p>
                    <ul>
                        <li>Items to be tested</li>
                        <li>Testing scope and objectives</li>
                        <li>Testing approach and techniques</li>
                        <li>Entry and exit criteria</li>
                        <li>Resource and schedule planning</li>
                    </ul>
                    
                    <h4>4. Test Case Specification</h4>
                    <p>Detailed documentation of specific test cases, including inputs, expected results, and test procedures.</p>
                    <ul>
                        <li>Test case ID and title</li>
                        <li>Test objective</li>
                        <li>Preconditions</li>
                        <li>Test steps</li>
                        <li>Expected results</li>
                        <li>Postconditions</li>
                        <li>Dependencies</li>
                    </ul>
                    
                    <h4>5. Test Data Specification</h4>
                    <p>Describes the data needed to execute test cases.</p>
                    <ul>
                        <li>Data requirements</li>
                        <li>Data generation methods</li>
                        <li>Privacy and security considerations</li>
                        <li>Data relationships and dependencies</li>
                    </ul>
                    
                    <h4>6. Test Execution Report</h4>
                    <p>Documents the results of test execution.</p>
                    <ul>
                        <li>Test summary</li>
                        <li>Tests passed/failed/blocked</li>
                        <li>Defects found</li>
                        <li>Test environment details</li>
                        <li>Deviations from test plan</li>
                    </ul>
                    
                    <h4>7. Defect Report</h4>
                    <p>Documents defects found during testing.</p>
                    <ul>
                        <li>Defect ID and summary</li>
                        <li>Severity and priority</li>
                        <li>Steps to reproduce</li>
                        <li>Actual vs. expected results</li>
                        <li>Environment information</li>
                        <li>Status and assignee</li>
                    </ul>
                    
                    <h4>8. Test Summary Report</h4>
                    <p>Provides an overview of the testing activities and results for stakeholders.</p>
                    <ul>
                        <li>Testing scope and objectives</li>
                        <li>Testing activities summary</li>
                        <li>Metrics and statistics</li>
                        <li>Evaluation of exit criteria</li>
                        <li>Recommendations</li>
                    </ul>
                    
                    <h3>Test Case Writing Best Practices</h3>
                    
                    <h4>Structure of a Good Test Case</h4>
                    <ol>
                        <li><strong>Test Case ID</strong>: Unique identifier</li>
                        <li><strong>Test Case Description</strong>: What is being tested</li>
                        <li><strong>Preconditions</strong>: Required setup before execution</li>
                        <li><strong>Test Steps</strong>: Detailed, sequential steps to follow</li>
                        <li><strong>Expected Results</strong>: Clear description of what should happen</li>
                        <li><strong>Postconditions</strong>: System state after execution</li>
                        <li><strong>Test Data</strong>: Required data for execution</li>
                        <li><strong>Related Requirements</strong>: Requirements being verified</li>
                    </ol>
                    
                    <h4>Tips for Writing Effective Test Cases</h4>
                    <ul>
                        <li><strong>Be Clear and Concise</strong>: Use simple language</li>
                        <li><strong>Be Specific</strong>: Avoid ambiguity in steps and expected results</li>
                        <li><strong>One Test Case, One Purpose</strong>: Focus on testing one thing at a time</li>
                        <li><strong>Make Test Cases Independent</strong>: Minimize dependencies between test cases</li>
                        <li><strong>Include Both Positive and Negative Tests</strong>: Test both valid and invalid scenarios</li>
                        <li><strong>Make Test Cases Repeatable</strong>: Any tester should get the same results</li>
                        <li><strong>Make Test Cases Maintainable</strong>: Structure for easy updates</li>
                        <li><strong>Ensure Traceability</strong>: Link test cases to requirements</li>
                    </ul>
                    
                    <h3>Test Case Example</h3>
                    <div class="example-block">
                        <h4>Test Case ID: TC_LOGIN_001</h4>
                        <p><strong>Title:</strong> Verify Login with Valid Credentials</p>
                        <p><strong>Description:</strong> Test to verify that a user can successfully log in with valid username and password</p>
                        <p><strong>Preconditions:</strong></p>
                        <ul>
                            <li>User has a valid account</li>
                            <li>User is on the login page</li>
                        </ul>
                        <p><strong>Test Steps:</strong></p>
                        <ol>
                            <li>Enter valid username in the Username field</li>
                            <li>Enter valid password in the Password field</li>
                            <li>Click on the Login button</li>
                        </ol>
                        <p><strong>Expected Results:</strong></p>
                        <ul>
                            <li>User is successfully logged in</li>
                            <li>User is redirected to the dashboard</li>
                            <li>A welcome message is displayed with the user's name</li>
                        </ul>
                        <p><strong>Test Data:</strong></p>
                        <ul>
                            <li>Username: validuser@example.com</li>
                            <li>Password: Valid123!</li>
                        </ul>
                        <p><strong>Related Requirement:</strong> REQ-AUTH-001</p>
                    </div>
                    
                    <h3>Traceability Matrix</h3>
                    <p>A traceability matrix is a document that maps and traces test cases to requirements, ensuring that all requirements are covered by tests.</p>
                    
                    <div class="table-container">
                        <table>
                            <tr>
                                <th>Requirement ID</th>
                                <th>Requirement Description</th>
                                <th>Test Case IDs</th>
                                <th>Status</th>
                            </tr>
                            <tr>
                                <td>REQ-AUTH-001</td>
                                <td>Users should be able to log in with username and password</td>
                                <td>TC_LOGIN_001, TC_LOGIN_002, TC_LOGIN_003</td>
                                <td>Covered</td>
                            </tr>
                            <tr>
                                <td>REQ-AUTH-002</td>
                                <td>System should lock account after 5 failed login attempts</td>
                                <td>TC_LOGIN_004, TC_LOGIN_005</td>
                                <td>Covered</td>
                            </tr>
                            <tr>
                                <td>REQ-AUTH-003</td>
                                <td>Users should be able to reset password</td>
                                <td>TC_RESET_001, TC_RESET_002</td>
                                <td>Covered</td>
                            </tr>
                            <tr>
                                <td>REQ-AUTH-004</td>
                                <td>Passwords must meet security requirements</td>
                                <td>TC_REG_001, TC_REG_002, TC_REG_003</td>
                                <td>Covered</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div class="practice-section">
                        <h4>Practice Exercise</h4>
                        <p>Create test cases for a password reset functionality with the following requirements:</p>
                        <ul>
                            <li>Users can request a password reset by entering their email address</li>
                            <li>System sends a reset link to the provided email if it exists in the database</li>
                            <li>Reset link expires after 24 hours</li>
                            <li>New password must be at least 8 characters with at least one uppercase letter, one number, and one special character</li>
                            <li>User must enter the new password twice for confirmation</li>
                            <li>System displays success message after password is reset</li>
                        </ul>
                    </div>
                    ''',
                    'duration': '75 minutes',
                    'type': 'reading',
                    'order': 2,
                    'has_assessment': True,
                    'resources': [
                        {
                            'title': 'Test Case Template Package',
                            'type': 'document',
                            'url': 'https://example.com/resources/test-case-templates.zip',
                            'description': 'Collection of test case and test suite templates in various formats.'
                        }
                    ],
                    'assessment': {
                        'title': 'Test Documentation Quiz',
                        'description': 'Test your understanding of test documentation concepts and best practices.',
                        'time_limit': 15,
                        'passing_score': 70,
                        'questions': [
                            {
                                'text': 'What is the purpose of a traceability matrix?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'To track defects and their resolution', 'correct': False},
                                    {'text': 'To map test cases to requirements', 'correct': True},
                                    {'text': 'To document test execution results', 'correct': False},
                                    {'text': 'To estimate testing effort', 'correct': False}
                                ]
                            },
                            {
                                'text': 'Which of the following is NOT a best practice for writing test cases?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'Be clear and concise', 'correct': False},
                                    {'text': 'Make test cases independent', 'correct': False},
                                    {'text': 'Combine multiple test objectives in one test case for efficiency', 'correct': True},
                                    {'text': 'Include both positive and negative tests', 'correct': False}
                                ]
                            },
                            {
                                'text': 'What should be included in a test execution report?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'Tests passed/failed/blocked', 'correct': True},
                                    {'text': 'Detailed development specifications', 'correct': False},
                                    {'text': 'User story acceptance criteria', 'correct': False},
                                    {'text': 'Project budget information', 'correct': False}
                                ]
                            }
                        ]
                    }
                }
            ]
        },
        {
            'title': 'Automated Testing',
            'description': 'Learn fundamentals of automated testing and how to implement it effectively.',
            'order': 5,
            'duration': '15 hours',
            'lessons': [
                {
                    'title': 'Introduction to Test Automation',
                    'content': '''
                    <h2>Introduction to Test Automation</h2>
                    <p>Test automation involves using specialized tools and frameworks to execute tests automatically, compare actual results with expected results, and generate test reports without human intervention.</p>
                    
                    <h3>Benefits of Test Automation</h3>
                    <ul>
                        <li><strong>Time Savings</strong>: Automated tests run much faster than manual tests</li>
                        <li><strong>Improved Accuracy</strong>: Eliminates human errors in test execution</li>
                        <li><strong>Increased Test Coverage</strong>: Enables testing more features and scenarios</li>
                        <li><strong>Reusability</strong>: Test scripts can be reused across multiple test cycles</li>
                        <li><strong>Regression Testing</strong>: Makes continuous regression testing practical</li>
                        <li><strong>Consistency</strong>: Tests are executed the same way every time</li>
                        <li><strong>Early Defect Detection</strong>: Can be integrated with CI/CD for rapid feedback</li>
                    </ul>
                    
                    <h3>Limitations of Test Automation</h3>
                    <ul>
                        <li><strong>Initial Investment</strong>: Requires time and resources to set up</li>
                        <li><strong>Maintenance Overhead</strong>: Test scripts need maintenance as application changes</li>
                        <li><strong>Limited to Verifiable Results</strong>: Some aspects (like UI aesthetics) are hard to automate</li>
                        <li><strong>Learning Curve</strong>: Requires programming and tooling knowledge</li>
                        <li><strong>Cannot Replace Exploratory Testing</strong>: Human intuition still required for some testing</li>
                    </ul>
                    
                    <h3>What to Automate</h3>
                    <p>Not all tests should be automated. Consider automating tests that are:</p>
                    <ul>
                        <li><strong>Repetitive</strong>: Tests that need to be run frequently</li>
                        <li><strong>Time-consuming</strong>: Tests that take a long time to execute manually</li>
                        <li><strong>High-risk</strong>: Tests for critical functionality</li>
                        <li><strong>Data-intensive</strong>: Tests requiring multiple data combinations</li>
                        <li><strong>Stable</strong>: Tests for features that don't change frequently</li>
                        <li><strong>Cross-browser/platform</strong>: Tests that need to be run in multiple environments</li>
                    </ul>
                    
                    <h3>What Not to Automate</h3>
                    <p>Some tests are better performed manually:</p>
                    <ul>
                        <li><strong>Exploratory testing</strong>: Requires human creativity and intuition</li>
                        <li><strong>Usability testing</strong>: Evaluates user experience</li>
                        <li><strong>Ad-hoc testing</strong>: One-time or irregular tests</li>
                        <li><strong>Tests for rapidly changing features</strong>: Would require frequent script updates</li>
                        <li><strong>Visual validation</strong>: Unless using specialized visual testing tools</li>
                    </ul>
                    
                    <h3>Test Automation Pyramid</h3>
                    <p>The test automation pyramid is a framework that suggests what types of automated tests to create and in what proportions:</p>
                    
                    <div class="pyramid-container">
                        <div class="pyramid-tier tier-1">
                            <h4>UI Tests</h4>
                            <p>End-to-end tests that validate the entire application</p>
                            <ul>
                                <li>Slowest and most brittle</li>
                                <li>Should be fewer in number (10-20% of tests)</li>
                                <li>Examples: Selenium, Cypress</li>
                            </ul>
                        </div>
                        <div class="pyramid-tier tier-2">
                            <h4>Integration Tests</h4>
                            <p>Tests that validate how components work together</p>
                            <ul>
                                <li>Medium speed and stability</li>
                                <li>Should be a moderate number (20-30% of tests)</li>
                                <li>Examples: API tests, service tests</li>
                            </ul>
                        </div>
                        <div class="pyramid-tier tier-3">
                            <h4>Unit Tests</h4>
                            <p>Tests that validate individual functions or methods</p>
                            <ul>
                                <li>Fastest and most stable</li>
                                <li>Should be the majority (50-70% of tests)</li>
                                <li>Examples: JUnit, NUnit, Jest</li>
                            </ul>
                        </div>
                    </div>
                    
                    <h3>Types of Test Automation</h3>
                    
                    <h4>Unit Test Automation</h4>
                    <ul>
                        <li>Tests individual components in isolation</li>
                        <li>Usually written by developers</li>
                        <li>Fast execution and easy maintenance</li>
                        <li>Examples: JUnit, NUnit, pytest</li>
                    </ul>
                    
                    <h4>API Test Automation</h4>
                    <ul>
                        <li>Tests backend services and APIs</li>
                        <li>Validates data exchange between systems</li>
                        <li>More stable than UI tests, faster than UI tests</li>
                        <li>Examples: Postman, REST Assured, Karate</li>
                    </ul>
                    
                    <h4>UI Test Automation</h4>
                    <ul>
                        <li>Tests the application through its user interface</li>
                        <li>Validates end-to-end flows from a user perspective</li>
                        <li>More prone to breakage when UI changes</li>
                        <li>Examples: Selenium, Cypress, TestCafe</li>
                    </ul>
                    
                    <h4>Performance Test Automation</h4>
                    <ul>
                        <li>Tests system behavior under load</li>
                        <li>Measures response times and resource usage</li>
                        <li>Helps identify bottlenecks</li>
                        <li>Examples: JMeter, Gatling, LoadRunner</li>
                    </ul>
                    
                    <h3>Test Automation Framework Components</h3>
                    <ul>
                        <li><strong>Test Libraries</strong>: Reusable functions for common operations</li>
                        <li><strong>Test Data Management</strong>: Methods for handling test data</li>
                        <li><strong>Object Repository</strong>: Storage of UI element identifiers</li>
                        <li><strong>Configuration Management</strong>: Environment-specific settings</li>
                        <li><strong>Reporting Mechanism</strong>: Test results visualization</li>
                        <li><strong>Recovery Scenario Management</strong>: Handling of unexpected situations</li>
                    </ul>
                    
                    <h3>Test Automation Best Practices</h3>
                    <ul>
                        <li><strong>Start Small and Scale</strong>: Begin with simple, high-value tests</li>
                        <li><strong>Create Independent Tests</strong>: Tests should not depend on other tests</li>
                        <li><strong>Use Appropriate Wait Mechanisms</strong>: Avoid hard-coded waits</li>
                        <li><strong>Implement Proper Error Handling</strong>: Tests should fail with meaningful messages</li>
                        <li><strong>Use Version Control</strong>: Store test scripts in a repository</li>
                        <li><strong>Implement Continuous Integration</strong>: Run tests automatically on code changes</li>
                        <li><strong>Maintain Test Data</strong>: Ensure test data is appropriate and isolated</li>
                        <li><strong>Review Test Results Regularly</strong>: Don't just set and forget</li>
                        <li><strong>Follow Page Object Model</strong>: For UI test organization</li>
                    </ul>
                    
                    <div class="practice-section">
                        <h4>Discussion Question</h4>
                        <p>For an e-commerce application, identify five test scenarios that would be good candidates for automation and five scenarios that would be better tested manually. Explain your reasoning for each.</p>
                    </div>
                    ''',
                    'duration': '90 minutes',
                    'type': 'video',
                    'order': 1,
                    'has_assessment': True,
                    'assessment': {
                        'title': 'Test Automation Fundamentals Quiz',
                        'description': 'Test your understanding of test automation concepts and best practices.',
                        'time_limit': 15,
                        'passing_score': 70,
                        'questions': [
                            {
                                'text': 'According to the test automation pyramid, which type of tests should be the majority?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'UI Tests', 'correct': False},
                                    {'text': 'Integration Tests', 'correct': False},
                                    {'text': 'Unit Tests', 'correct': True},
                                    {'text': 'Manual Tests', 'correct': False}
                                ]
                            },
                            {
                                'text': 'Which of the following is NOT a typical benefit of test automation?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'Time savings', 'correct': False},
                                    {'text': 'Improved accuracy', 'correct': False},
                                    {'text': 'Better usability evaluation', 'correct': True},
                                    {'text': 'Increased test coverage', 'correct': False}
                                ]
                            },
                            {
                                'text': 'Which of the following would be the best candidate for test automation?',
                                'type': 'multiple_choice',
                                'points': 1,
                                'answers': [
                                    {'text': 'Exploratory testing of a new feature', 'correct': False},
                                    {'text': 'Usability evaluation of a redesigned interface', 'correct': False},
                                    {'text': 'Regression testing of core functionality', 'correct': True},
                                    {'text': 'One-time data migration validation', 'correct': False}
                                ]
                            }
                        ]
                    }
                }
            ]
        }
    ]

    logger.info(f"Created {len(modules_data)} module definitions for the course")
    return modules_data


def create_module_content(module_data, module_index):
    """Create or update a module and its lessons, assessments, etc."""
    course = Course.objects.get(slug='software-testing')

    # Create or update the module
    module, created = Module.objects.update_or_create(
        course=course,
        title=module_data['title'],
        defaults={
            'description': module_data['description'],
            'order': module_data['order'],
            'duration': module_data['duration']
        }
    )
    logger.info(f"Module {module_index} {'created' if created else 'updated'}: {module.title}")

    # Create lessons for this module
    for lesson_index, lesson_data in enumerate(module_data['lessons'], 1):
        lesson, created = Lesson.objects.update_or_create(
            module=module,
            title=lesson_data['title'],
            defaults={
                'content': lesson_data['content'],
                'duration': lesson_data['duration'],
                'type': lesson_data['type'],
                'order': lesson_data['order'],
                'has_assessment': lesson_data.get('has_assessment', False),
                'has_lab': lesson_data.get('has_lab', False),
                'is_free_preview': lesson_data.get('is_free_preview', False)
            }
        )
        logger.info(f"Lesson {module_index}.{lesson_index} {'created' if created else 'updated'}: {lesson.title}")

        # Create resources for this lesson if they exist
        if 'resources' in lesson_data:
            for resource_data in lesson_data['resources']:
                resource, created = Resource.objects.update_or_create(
                    lesson=lesson,
                    title=resource_data['title'],
                    defaults={
                        'type': resource_data['type'],
                        'url': resource_data.get('url', ''),
                        'description': resource_data.get('description', '')
                    }
                )
                logger.info(f"Resource {'created' if created else 'updated'} for lesson {module_index}.{lesson_index}: {resource.title}")

        # Create assessment for this lesson if it exists
        if 'assessment' in lesson_data and lesson.has_assessment:
            assessment_data = lesson_data['assessment']
            assessment, created = Assessment.objects.update_or_create(
                lesson=lesson,
                defaults={
                    'title': assessment_data['title'],
                    'description': assessment_data.get('description', ''),
                    'time_limit': assessment_data.get('time_limit', 0),
                    'passing_score': assessment_data.get('passing_score', 70)
                }
            )
            logger.info(f"Assessment {'created' if created else 'updated'} for lesson {module_index}.{lesson_index}: {assessment.title}")

            # Delete existing questions for this assessment
            Question.objects.filter(assessment=assessment).delete()
            logger.info(f"Deleted existing questions for assessment: {assessment.title}")

            # Create questions for this assessment
            if 'questions' in assessment_data:
                for question_index, question_data in enumerate(assessment_data['questions'], 1):
                    question = Question.objects.create(
                        assessment=assessment,
                        question_text=question_data['text'],
                        question_type=question_data['type'],
                        order=question_index,
                        points=question_data.get('points', 1)
                    )
                    logger.info(f"Question {question_index} created for assessment: {question.question_text}")

                    # Create answers for this question
                    if 'answers' in question_data:
                        for answer_data in question_data['answers']:
                            answer = Answer.objects.create(
                                question=question,
                                answer_text=answer_data['text'],
                                is_correct=answer_data['correct'],
                                explanation=answer_data.get('explanation', '')
                            )
                            logger.info(f"Answer created for question {question_index}: {answer.answer_text}")


if __name__ == "__main__":
    try:
        with transaction.atomic():  # Wrap everything in a transaction for safety
            create_or_update_software_testing_course()
            logger.info("Script completed successfully!")
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())