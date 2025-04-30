"""
File: backend/courses/utils.py
Purpose: Utility functions for the courses app in the educational platform.

This file contains helper functions used across multiple views and serializers
in the courses module, particularly for access control and subscription checks.

Key functions:
- get_user_access_level: Determines access level based on user authentication and subscription
- get_restricted_content_message: Provides consistent messages for restricted content

Variables that might need modification:
- DEFAULT_PREMIUM_CONTENT_MESSAGE: Message shown when premium content is restricted
- DEFAULT_REGISTERED_CONTENT_MESSAGE: Message shown when registered content is restricted

Connected files:
1. backend/courses/views.py - Uses these utilities in view functions
2. backend/courses/serializers.py - Uses these utilities in serializers
"""

# Messages shown to users based on their access level
DEFAULT_PREMIUM_CONTENT_MESSAGE = """
<div class="premium-content-notice">
    <h2>{title} - Premium Content</h2>
    <p>This content requires a premium subscription.</p>
    <p>Please upgrade your account to access this lesson.</p>
</div>
"""

DEFAULT_REGISTERED_CONTENT_MESSAGE = """
<div class="preview-content">
    <h2>{title} - Preview</h2>
    <p>Register for free to access this content.</p>
</div>
"""


def get_user_access_level(request):
    """
    Determine a user's access level based on authentication and subscription.

    Parameters:
    - request: The HTTP request object containing the user

    Returns:
    - 'basic': For unauthenticated/anonymous users
    - 'intermediate': For registered users with free or basic subscription
    - 'advanced': For registered users with premium subscription
    """
    # Default access level for unauthenticated users
    user_access_level = 'basic'

    # If user is authenticated, they get at least intermediate access
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        user_access_level = 'intermediate'

        # Check if user has premium subscription
        try:
            subscription = request.user.subscription
            if subscription.tier == 'premium' and subscription.is_active():
                user_access_level = 'advanced'
        except AttributeError:
            # If user.subscription doesn't exist
            pass
        except Exception:
            # For any other errors, default to intermediate access
            pass

    return user_access_level


def get_restricted_content_message(title, access_level):
    """
    Get appropriate message for restricted content based on user's access level.

    Parameters:
    - title: The title of the content
    - access_level: The user's access level ('basic' or 'intermediate')

    Returns:
    - HTML formatted message appropriate for the access level
    """
    if access_level == 'basic':
        return DEFAULT_REGISTERED_CONTENT_MESSAGE.format(title=title)
    else:
        return DEFAULT_PREMIUM_CONTENT_MESSAGE.format(title=title)
