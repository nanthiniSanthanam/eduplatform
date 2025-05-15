"""
File: backend/courses/models.py
Purpose: Defines all database models for the courses app in the educational platform.

Key models:
- Category: Course categories
- Course: Main course information
- Module: Course modules/sections
- Lesson: Individual lessons with tiered content access
- Resource: Additional learning materials
- Assessment: Quizzes and tests
- Enrollment: Student course registrations
- Certificate: Course completion certificates

Modified for tiered access:
- Added ACCESS_LEVEL_CHOICES to Lesson model
- Added access_level field to control content visibility
- Added basic_content and intermediate_content fields for different subscription tiers
- Added premium field to Resource model

Variables to modify:
- ACCESS_LEVEL_CHOICES: If you want to change the tier names
- Default values for the access_level field

Connected files to update:
1. Create a migration to apply these changes: python manage.py makemigrations
2. Update the LessonSerializer in backend/courses/serializers.py
3. Modify LessonDetailView in backend/courses/views.py to respect access levels
4. Update the frontend ContentAccessController.jsx to match these access levels
"""

from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


def get_default_category():
    # This will return the ID of the "general" category, creating it if it doesn't exist
    return Category.objects.get_or_create(name="General")[0].id


class Course(models.Model):
    LEVEL_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('all_levels', 'All Levels'),
    )

    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='courses', default=get_default_category)
    thumbnail = models.ImageField(
        upload_to='course_thumbnails/', blank=True, null=True)
    price = models.DecimalField(max_digits=7, decimal_places=2, default=490)
    discount_price = models.DecimalField(
        max_digits=7, decimal_places=2, blank=True, null=True)
    discount_ends = models.DateTimeField(blank=True, null=True)
    level = models.CharField(
        max_length=20, choices=LEVEL_CHOICES, default='all_levels')
    duration = models.CharField(
        max_length=50, blank=True, null=True)  # e.g., "60 hours"
    has_certificate = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    published_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    # Course requirements and what will be learned
    requirements = models.JSONField(default=dict, blank=True, null=True)
    skills = models.JSONField(default=dict, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return 0
        return sum([review.rating for review in reviews]) / len(reviews)

    @property
    def enrolled_students(self):
        return self.enrollments.count()


class CourseInstructor(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='instructors')
    instructor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='courses_teaching')
    title = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    is_lead = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.instructor.get_full_name()} - {self.course.title}"


class Module(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=1)
    duration = models.CharField(
        max_length=50, blank=True, null=True)  # e.g., "8 hours"

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    """
    Lesson model representing individual units of learning within a module.

    Lessons can include different types of content (video, text, etc.) and may have 
    associated assessments, labs, and resources.

    Content Formatting:
    - Lessons support rich HTML content including headings and subheadings
    - Use <h2>, <h3>, <h4> tags to create a hierarchical structure in the content
    - Example: 
        <h2>Main Topic</h2>
        <p>Introduction paragraph...</p>
        <h3>Subtopic</h3>
        <p>Detailed content...</p>
        <h4>Specific Concept</h4>
        <p>Details about the specific concept...</p>

    - The frontend will render these headings properly with appropriate styling
    - This allows instructors to organize their content in a structured way
    - Properly formatted headings also improve accessibility and readability
    """
    LESSON_TYPE_CHOICES = (
        ('video', 'Video'),
        ('reading', 'Reading'),
        ('interactive', 'Interactive'),
        ('quiz', 'Quiz'),
        ('lab', 'Lab Exercise'),
    )

    # Define access levels for different user types
    ACCESS_LEVEL_CHOICES = (
        ('basic', 'Basic - Unregistered Users'),
        ('intermediate', 'Intermediate - Registered Users'),
        ('advanced', 'Advanced - Paid Users'),
    )

    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)

    # Content fields for different user types
    content = models.TextField(
        help_text="Full content visible to all users (or premium content if access_level is set)")
    basic_content = models.TextField(
        blank=True, null=True, help_text="Preview content for unregistered users")
    intermediate_content = models.TextField(
        blank=True, null=True, help_text="Limited content for registered users")

    # Access control field
    access_level = models.CharField(
        max_length=20,
        choices=ACCESS_LEVEL_CHOICES,
        default='intermediate',
        help_text="Minimum access level required to view this lesson"
    )

    duration = models.CharField(
        max_length=50, blank=True, null=True)  # e.g. "15min"
    type = models.CharField(
        max_length=20, choices=LESSON_TYPE_CHOICES, default='video')
    order = models.PositiveIntegerField(default=1)
    has_assessment = models.BooleanField(default=False)
    has_lab = models.BooleanField(default=False)
    is_free_preview = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.module.title} - {self.title}"

    def save(self, *args, **kwargs):
        # If this is a new lesson, set order to be last in module
        if not self.id:
            try:
                last_order = Lesson.objects.filter(
                    module=self.module).aggregate(models.Max('order'))['order__max']
                if last_order is not None:
                    self.order = last_order + 1
            except (KeyError, Lesson.DoesNotExist):
                self.order = 1

        super().save(*args, **kwargs)


class Resource(models.Model):
    RESOURCE_TYPE_CHOICES = (
        ('document', 'Document'),
        ('video', 'Video'),
        ('link', 'External Link'),
        ('code', 'Code Sample'),
        ('tool', 'Tool/Software'),
    )

    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=RESOURCE_TYPE_CHOICES)
    file = models.FileField(
        upload_to='lesson_resources/', blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    premium = models.BooleanField(
        default=False, help_text="Whether this resource requires a premium subscription")

    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


class Assessment(models.Model):
    lesson = models.OneToOneField(
        Lesson, on_delete=models.CASCADE, related_name='assessment')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    time_limit = models.PositiveIntegerField(
        default=0)  # in minutes, 0 means no limit
    passing_score = models.PositiveIntegerField(default=70)  # percentage

    def __str__(self):
        return f"Assessment for {self.lesson.title}"


class Question(models.Model):
    QUESTION_TYPE_CHOICES = (
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('matching', 'Matching'),
    )

    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=20, choices=QUESTION_TYPE_CHOICES)
    order = models.PositiveIntegerField(default=1)
    points = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Question {self.order} for {self.assessment.title}"


class Answer(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    explanation = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Answer for {self.question}"


class Enrollment(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_date = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='active')
    completion_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ['user', 'course']

    def __str__(self):
        return f"{self.user.username} enrolled in {self.course.title}"


class Progress(models.Model):
    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE, related_name='progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_date = models.DateTimeField(blank=True, null=True)
    time_spent = models.PositiveIntegerField(default=0)  # in seconds

    class Meta:
        unique_together = ['enrollment', 'lesson']

    def __str__(self):
        return f"{self.enrollment.user.username} - {self.lesson.title} progress"


class AssessmentAttempt(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='assessment_attempts')
    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name='attempts')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    score = models.PositiveIntegerField(default=0)
    passed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} attempt at {self.assessment.title}"

    @property
    def score_percentage(self):
        max_score = sum([q.points for q in self.assessment.questions.all()])
        if max_score == 0:
            return 0
        return (self.score / max_score) * 100


class AttemptAnswer(models.Model):
    attempt = models.ForeignKey(
        AssessmentAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(
        Answer, on_delete=models.CASCADE, blank=True, null=True)
    text_answer = models.TextField(blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    points_earned = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Answer for {self.question} in {self.attempt}"


class Review(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reviews')
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    helpful_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['user', 'course']

    def __str__(self):
        return f"{self.user.username}'s review on {self.course.title}"


class Note(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notes')
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name='notes')
    content = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s note on {self.lesson.title}"


class Certificate(models.Model):
    enrollment = models.OneToOneField(
        Enrollment, on_delete=models.CASCADE, related_name='certificate')
    issue_date = models.DateTimeField(auto_now_add=True)
    certificate_number = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"Certificate for {self.enrollment.user.username} - {self.enrollment.course.title}"
