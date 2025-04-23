from django.contrib import admin
from .models import (
    Category, Course, CourseInstructor, Module, Lesson,
    Resource, Assessment, Question, Answer, Enrollment,
    Progress, AssessmentAttempt, AttemptAnswer, Review,
    Note, Certificate
)


class CourseInstructorInline(admin.TabularInline):
    model = CourseInstructor
    extra = 1


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'level',
                    'is_published', 'enrolled_students')
    list_filter = ('category', 'level', 'is_published')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [CourseInstructorInline, ModuleInline]


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    search_fields = ('title', 'description')
    inlines = [LessonInline]


class ResourceInline(admin.TabularInline):
    model = Resource
    extra = 1


class AssessmentInline(admin.StackedInline):
    model = Assessment
    extra = 0


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'type', 'order',
                    'has_assessment', 'has_lab')
    list_filter = ('module__course', 'type', 'has_assessment', 'has_lab')
    search_fields = ('title', 'content')
    inlines = [ResourceInline, AssessmentInline]


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'assessment',
                    'question_type', 'order', 'points')
    list_filter = ('question_type', 'assessment__lesson__module__course')
    search_fields = ('question_text',)
    inlines = [AnswerInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'status',
                    'enrolled_date', 'completion_date')
    list_filter = ('status', 'course')
    search_fields = ('user__username', 'user__email', 'course__title')


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'lesson', 'is_completed',
                    'completed_date', 'time_spent')
    list_filter = ('is_completed', 'enrollment__course')
    search_fields = ('enrollment__user__username', 'lesson__title')


@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'assessment', 'start_time',
                    'end_time', 'score', 'passed')
    list_filter = ('passed', 'assessment__lesson__module__course')
    search_fields = ('user__username', 'assessment__title')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'rating',
                    'date_created', 'helpful_count')
    list_filter = ('rating', 'course')
    search_fields = ('user__username', 'course__title', 'content')


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'issue_date', 'certificate_number')
    search_fields = ('enrollment__user__username',
                     'enrollment__course__title', 'certificate_number')


# Register remaining models
admin.site.register(Category)
admin.site.register(Resource)
admin.site.register(Answer)
admin.site.register(AttemptAnswer)
admin.site.register(Note)
admin.site.register(Assessment)
admin.site.register(CourseInstructor)
