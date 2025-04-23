from rest_framework import permissions


class IsEnrolledOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow enrolled users to access course content beyond basic details.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check if user is enrolled in the course
        course = obj
        if hasattr(obj, 'module'):
            course = obj.module.course
        elif hasattr(obj, 'course'):
            course = obj.course

        return request.user.is_authenticated and course.enrollments.filter(user=request.user).exists()


class IsEnrolled(permissions.BasePermission):
    """
    Custom permission to only allow enrolled users to access course content.
    """

    def has_object_permission(self, request, view, obj):
        # Get the course from the object
        course = None
        if hasattr(obj, 'course'):
            course = obj.course
        elif hasattr(obj, 'module'):
            course = obj.module.course
        elif hasattr(obj, 'module') and hasattr(obj.module, 'course'):
            course = obj.module.course
        elif hasattr(obj, 'lesson') and hasattr(obj.lesson, 'module'):
            course = obj.lesson.module.course
        elif hasattr(obj, 'assessment') and hasattr(obj.assessment, 'lesson'):
            course = obj.assessment.lesson.module.course

        if not course:
            return False

        return request.user.is_authenticated and course.enrollments.filter(user=request.user).exists()
