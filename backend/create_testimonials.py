"""
Script to create initial testimonials and platform statistics
Run with: python create_testimonials.py
"""

import os
import django
import sys

# Setup Django environment
print("Setting up Django environment...")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educore.settings')
try:
    django.setup()
    print("Django setup successful!")
except Exception as e:
    print(f"Django setup failed: {e}")
    sys.exit(1)

# Now we can import models
try:
    from content.models import Testimonial, PlatformStatistics
    print("Models imported successfully!")
except Exception as e:
    print(f"Error importing models: {e}")
    sys.exit(1)

# Create some testimonials
testimonials = [
    {
        'name': 'Jane Smith',
        'role': 'Software Engineer',
        'content': 'This platform helped me transition from a junior to senior developer in just 6 months.',
        'rating': 5,
        'is_featured': True
    },
    {
        'name': 'Michael Johnson',
        'role': 'Data Scientist',
        'content': 'The data science courses here are comprehensive and practical. I use what I learned daily.',
        'rating': 5,
        'is_featured': True
    },
    {
        'name': 'Sarah Williams',
        'role': 'UX Designer',
        'content': 'The design courses completely changed how I approach user experience. Highly recommended!',
        'rating': 4,
        'is_featured': True
    },
    {
        'name': 'David Lee',
        'role': 'Product Manager',
        'content': 'As a product manager, the business courses gave me valuable insights into tech strategy.',
        'rating': 5,
        'is_featured': True
    },
    {
        'name': 'Emma Garcia',
        'role': 'Full Stack Developer',
        'content': 'The React and Node.js courses were exactly what I needed to build my first full-stack app.',
        'rating': 4,
        'is_featured': False
    }
]

print("Creating testimonials...")
for t_data in testimonials:
    try:
        obj, created = Testimonial.objects.get_or_create(
            name=t_data['name'],
            defaults=t_data
        )
        if created:
            print(f"Created testimonial: {obj.name}")
        else:
            print(f"Testimonial already exists: {obj.name}")
    except Exception as e:
        print(f"Error creating testimonial {t_data['name']}: {e}")

# Initialize platform statistics
print("Initializing platform statistics...")
try:
    stats = PlatformStatistics.get_stats()
    stats.update_stats()
    print(
        f"Platform stats: {stats.total_courses} courses, {stats.total_students} students, {stats.total_instructors} instructors")
except Exception as e:
    print(f"Error updating platform statistics: {e}")

print("Done!")
