from django.core.management.base import BaseCommand
from courses.models import Course, Category
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Adds a software testing course to the database'

    def handle(self, *args, **kwargs):
        # Get or create a category
        category, created = Category.objects.get_or_create(
            name='Software Development',
            defaults={
                'slug': 'software-development',
                'description': 'Courses related to software development.',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Created category: {category.name}'))

        # Create the software testing course
        course, created = Course.objects.get_or_create(
            slug='software-testing',
            defaults={
                'title': 'Software Testing',
                'description': 'Learn software testing methodologies and best practices.',
                'category': category,
                'is_published': True,  # Set this to True!
                'level': 'beginner',  # Add some additional fields
                'duration': '20 hours'  # Add some additional fields
            }
        )

        # If course already exists, ensure it's published
        if not created:
            if not course.is_published:
                course.is_published = True
                course.save()
                self.stdout.write(self.style.SUCCESS(
                    f'Updated course: {course.title} (marked as published)'))
            else:
                self.stdout.write(self.style.WARNING(
                    f'Course already exists: {course.title}'))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Created course: {course.title}'))

        self.stdout.write(self.style.SUCCESS('Command completed successfully'))
