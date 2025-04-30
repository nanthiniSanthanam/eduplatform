#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# fmt: off
# isort: skip_file

r"""
File: django_api_generator.py

Purpose:
    This script generates serializers.py, views.py, and urls.py files for a Django project
    by analyzing existing models.py files. It ensures perfect consistency between models and 
    their API representations, solving the cyclic modification problem in REST API development.

Features:
    1. Automatically reads Django models.py files to extract model information
    2. Generates serializers.py with proper handling of all field types, including:
       - Basic fields (matching the model exactly)
       - Foreign key relationships (with proper ID field handling)
       - Many-to-many relationships
       - Computed properties
    3. Generates views.py with ViewSets, permissions, and filtering
    4. Creates urls.py with appropriate routing for API endpoints
    5. Includes detailed comments and formatting protection headers
    6. Handles the three-tier access system for educational content
    7. Ensures consistent API design and field naming
    8. Creates backup files before overwriting existing files
    9. Logs all operations and warns about potential issues
    10. Rich exception handling for better debugging

Variables to modify:
    PROJECT_DIR: Base directory of your Django project (where manage.py is located)
        (default: C:\Users\Santhanam\OneDrive\Personal\Full stack web development\eduplatform)
        IMPORTANT: This should be the directory containing manage.py, not the backend package!
        
    APPS_TO_PROCESS: List of app names to process or empty for all apps
        (default: [] which means all apps)
        
    BACKUP_EXISTING: Whether to create backups of existing files before overwriting them
        (default: True)
        
    API_PREFIX: Prefix for API URLs 
        (default: 'api/v1/')
        
    INDENT: String used for code indentation
        (default: '    ' - four spaces)
        
    MAX_BACKUPS: Maximum number of backup files to keep per file
        (default: 5)
        
    URL_SLUG_STYLE: Style for URL slugs ('hyphens' or 'underscores')
        (default: 'hyphens')
    
Requirements:
    - Python 3.6+
    - Django 3.2+
    - django-filter (pip install django-filter)
    - Access to your Django project's code
    - inflect package for proper pluralization (pip install inflect)

How to use:
    1. Make sure your Django project is properly configured (settings.py is accessible)
    2. Place this script in your project directory (same level as manage.py)
    3. Activate your virtual environment: source venv/bin/activate (Linux/Mac) or venv\Scripts\activate (Windows)
    4. Run the script: python django_api_generator.py [options]
       Available options:
       --apps app1 app2 ... : Specific apps to process
       --settings module.path : Django settings module to use (e.g., core.settings)
       --all-apps : Process all discovered apps without asking
       --no-backup : Skip creating backup files
       --max-backups N : Maximum number of backup files to keep (default: 5)
       --project-dir PATH : Specify project directory (overrides default)
    5. Review the generated code in your app directories

Output:
    For each Django app with models, the script will generate:
    - serializers.py: Converts model instances to/from JSON
    - views.py: Provides API endpoints and implements business logic
    - urls.py: Defines URL routing for the API endpoints

Note:
    This script won't overwrite your models.py files - it only reads from them
    to create consistent serializers, views, and URLs.

Created by: Professor Santhanam
Last updated: 2025-04-28 15:43:21
"""

import os
import sys
import re
import inspect
import importlib
import datetime
import shutil
import ast
import traceback
import logging
import argparse
import glob
from collections import defaultdict, OrderedDict
from pathlib import Path

try:
    import inflect
    INFLECT_ENGINE = inflect.engine()
except ImportError:
    INFLECT_ENGINE = None
    print("Warning: inflect package not installed. Using simple pluralization rules.")
    print("To install: pip install inflect")

# --- CONFIGURATION SECTION ---
# You can modify these variables to customize the behavior of the script

# Base directory of your Django project (where manage.py is located)
PROJECT_DIR = r"C:\Users\Santhanam\OneDrive\Personal\Full stack web development\eduplatform"

# List of app names to process (leave empty to process all apps with models)
APPS_TO_PROCESS = []

# Whether to create backups of existing files before overwriting them
BACKUP_EXISTING = True

# Prefix for API URLs - IMPORTANT: Used consistently throughout the code
# Change this to match your API routing scheme
API_PREFIX = 'api/v1/'

# String used for code indentation
INDENT = '    '  # four spaces

# Format protection header for all generated files
FORMAT_PROTECTION = '# fmt: off\n# isort: skip_file\n\n'

# Maximum number of backup files to keep per file
MAX_BACKUPS = 5

# Style for URL slugs ('hyphens' or 'underscores')
URL_SLUG_STYLE = 'hyphens'  # Alternative: 'underscores'

# Set up logging
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_generator.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- END OF CONFIGURATION SECTION ---

# Global tracking variables
generated_files = []
warnings = []
errors = []
processed_models = []

def normalize_path(path):
    """
    Normalize path separators to forward slashes for consistency.

    Args:
        path (str): The file path to normalize

    Returns:
        str: The normalized path with forward slashes
    """
    return path.replace(os.sep, '/')

def format_url_slug(text):
    """
    Format text as a URL slug according to URL_SLUG_STYLE.

    Args:
        text (str): The text to format

    Returns:
        str: Formatted URL slug
    """
    # Replace spaces with hyphens or underscores based on style
    if URL_SLUG_STYLE == 'hyphens':
        return text.replace(' ', '-')
    else:  # underscores
        return text.replace(' ', '_')

def parse_args():
    """Parse command line arguments for automation support."""
    parser = argparse.ArgumentParser(description='Django API Generator')
    parser.add_argument('--apps', nargs='+', help='App names to process')
    parser.add_argument('--settings', help='Django settings module (e.g., core.settings)')
    parser.add_argument('--all-apps', action='store_true', help='Process all discovered apps')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backup files')
    parser.add_argument('--max-backups', type=int, help=f'Maximum number of backup files to keep (default: {MAX_BACKUPS})')
    parser.add_argument('--project-dir', help=f'Project directory (default: {PROJECT_DIR})')
    return parser.parse_args()

def pluralize(name):
    """
    Convert singular name to plural form using proper English rules.

    Args:
        name (str): Singular name

    Returns:
        str: Pluralized name
    """
    if INFLECT_ENGINE:
        # Use inflect package for proper pluralization
        return INFLECT_ENGINE.plural(name)
    else:
        # Fallback to simple rules if inflect isn't available
        if name.endswith('y') and name[-2] not in 'aeiou':
            return name[:-1] + 'ies'
        elif name.endswith('s') or name.endswith('x') or name.endswith('z') or name.endswith('ch') or name.endswith('sh'):
            return name + 'es'
        else:
            return name + 's'

def get_model_plural_name(model_info):
    """
    Get the plural name for a model, checking for custom plural_name in Meta.

    Args:
        model_info (dict): Information about the model

    Returns:
        str: Pluralized name for the model suitable for URLs
    """
    # Check if model has Meta class with custom plural_name
    meta = model_info.get('meta', {})
    if meta and 'plural_name' in meta:
        return format_url_slug(meta['plural_name'])

    # Try to get verbose_name_plural from Django model
    django_model = model_info.get('django_model')
    if django_model and hasattr(django_model._meta, 'verbose_name_plural'):
        # Format slug according to style but preserve case
        return format_url_slug(django_model._meta.verbose_name_plural)

    # Fall back to our pluralize function with snake_case name
    model_name = model_info['name']
    snake_name = camel_to_snake(model_name)
    return pluralize(snake_name)

def camel_to_snake(name):
    """
    Convert CamelCase to snake_case.

    Args:
        name (str): CamelCase string

    Returns:
        str: snake_case string
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def extract_timestamp_from_backup(filename):
    """
    Extract timestamp from backup filename.

    Args:
        filename (str): Backup filename with timestamp (file.py.20250428_154321.bak)

    Returns:
        datetime or None: Extracted timestamp or None if not found
    """
    match = re.search(r'\.(\d{8}_\d{6})\.bak$', filename)
    if match:
        try:
            timestamp_str = match.group(1)
            return datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        except (ValueError, IndexError):
            pass
    return None

def backup_file(file_path, max_backups=MAX_BACKUPS):
    """
    Create a backup of an existing file, rotating old backups if needed.

    Args:
        file_path (str): Path to the file to back up
        max_backups (int): Maximum number of backups to keep

    Returns:
        str: Path to the backup file, or None on failure
    """
    if os.path.exists(file_path):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.{timestamp}.bak"

        try:
            # Create new backup
            shutil.copy2(file_path, backup_path)

            # Check for old backups to rotate
            if max_backups > 0:
                # Use glob to find all backup files (more robust across platforms)
                backup_pattern = f"{file_path}.*.bak"
                backups = glob.glob(backup_pattern)

                # If we have too many backups
                if len(backups) > max_backups:
                    # Sort by timestamp in filename (not by modification time)
                    backups_with_time = []
                    for backup in backups:
                        timestamp = extract_timestamp_from_backup(backup)
                        if timestamp:
                            backups_with_time.append((backup, timestamp))

                    # Sort by timestamp (oldest first)
                    backups_with_time.sort(key=lambda x: x[1])

                    # Remove oldest backups, keeping the most recent max_backups
                    for old_backup, _ in backups_with_time[:-max_backups]:
                        try:
                            os.remove(old_backup)
                            logger.debug(f"Removed old backup: {old_backup}")
                        except Exception as e:
                            logger.warning(f"Failed to remove old backup {old_backup}: {str(e)}")

            return backup_path
        except Exception as e:
            logger.error(f"Failed to back up file {file_path}: {str(e)}")

    return None

class ModelInspector:
    """
    Class to inspect Django models and extract their metadata.
    """

    def __init__(self, django_apps):
        """
        Initialize the ModelInspector with Django app registry.

        Args:
            django_apps: Django app registry from django.apps.apps
        """
        self.django_apps = django_apps
        self.app_models = {}

    def find_apps_with_models(self):
        """
        Find all Django apps that contain models.

        Returns:
            dict: Dictionary mapping app names to info about each app
        """
        logger.info("Finding apps with models...")

        try:
            # Iterate through all installed apps
            for app_config in self.django_apps.get_app_configs():
                app_name = app_config.name

                # Skip Django's built-in apps unless specifically requested
                if app_name.startswith('django.') and app_name not in APPS_TO_PROCESS:
                    continue

                # Skip apps not in our list if APPS_TO_PROCESS is specified
                if APPS_TO_PROCESS and app_name not in APPS_TO_PROCESS:
                    continue

                # Check if the app has models
                models = list(app_config.get_models())
                if models:
                    # Find the models.py file
                    models_file = None
                    module = app_config.module
                    module_path = module.__file__
                    if module_path:
                        module_dir = os.path.dirname(module_path)
                        possible_models_file = os.path.join(module_dir, 'models.py')
                        if os.path.exists(possible_models_file):
                            models_file = possible_models_file

                    self.app_models[app_name] = {
                        'app_config': app_config,
                        'models': models,
                        'models_file': models_file,
                        'app_dir': os.path.dirname(module_path) if module_path else None,
                        'app_label': app_name.split('.')[-1]
                    }

            logger.info(f"Found {len(self.app_models)} apps with models")
            return self.app_models

        except Exception as e:
            logger.error(f"Error finding apps with models: {str(e)}")
            traceback.print_exc()
            return {}

    def get_ast_value(self, node):
        """
        Extract value from AST node, compatible with Python 3.7+ and 3.8+.

        Args:
            node: The AST node

        Returns:
            The extracted value or None if not extractable
        """
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Str):     # Python 3.7-
            return node.s
        elif isinstance(node, ast.Num):     # Python 3.7-
            return node.n
        elif isinstance(node, ast.NameConstant):  # Python 3.7- for True, False, None
            return node.value
        elif isinstance(node, ast.List):
            return [self.get_ast_value(item) for item in node.elts]
        elif isinstance(node, ast.Tuple):
            return tuple(self.get_ast_value(item) for item in node.elts)
        return None

    def analyze_models_file(self, file_path):
        """
        Parse and analyze a models.py file using AST to extract detailed information.

        Args:
            file_path (str): Path to models.py file

        Returns:
            dict: Information about imports and models defined in the file
        """
        logger.info(f"Analyzing models file: {normalize_path(file_path)}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            # Parse the file
            tree = ast.parse(file_content)

            # Extract imports
            imports = []
            from_imports = {}

            for node in tree.body:
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module
                    names = [name.name for name in node.names]
                    from_imports[module] = names

            # Extract model classes
            models = []

            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    # Check if this is a model class by looking at the base classes
                    is_model = False
                    base_models = []

                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            base_name = base.id
                            if base_name in ['Model', 'models.Model']:
                                is_model = True
                            base_models.append(base_name)
                        elif isinstance(base, ast.Attribute):
                            base_name = f"{base.value.id}.{base.attr}" if hasattr(base.value, 'id') else str(base.value)
                            if base_name in ['models.Model', 'django.db.models.Model']:
                                is_model = True
                            base_models.append(base_name)

                    if is_model or any(base.endswith('Model') for base in base_models):
                        # This appears to be a model class
                        model_info = {
                            'name': node.name,
                            'bases': base_models,
                            'docstring': self._parse_docstring(node),
                            'fields': [],
                            'methods': [],
                            'properties': [],
                            'meta': None,
                        }

                        # Extract fields, methods, properties, and Meta class
                        for item in node.body:
                            if isinstance(item, ast.Assign):
                                # This might be a field
                                for target in item.targets:
                                    if isinstance(target, ast.Name):
                                        field_name = target.id
                                        field_value = None

                                        if isinstance(item.value, ast.Call):
                                            field_type = None
                                            if isinstance(item.value.func, ast.Attribute):
                                                # models.CharField, etc.
                                                if hasattr(item.value.func.value, 'id'):
                                                    module = item.value.func.value.id
                                                    if module == 'models':
                                                        field_type = item.value.func.attr
                                            elif isinstance(item.value.func, ast.Name):
                                                # Direct field type
                                                field_type = item.value.func.id

                                            if field_type:
                                                # Extract field arguments
                                                args = []
                                                kwargs = {}

                                                # Extract positional arguments
                                                for arg in item.value.args:
                                                    value = self.get_ast_value(arg)
                                                    if value is not None:
                                                        args.append(value)
                                                    else:
                                                        args.append(str(arg))

                                                # Extract keyword arguments
                                                for kwarg in item.value.keywords:
                                                    key = kwarg.arg
                                                    value = self.get_ast_value(kwarg.value)

                                                    if value is None:
                                                        # Handle function calls like models.Q()
                                                        if isinstance(kwarg.value, ast.Call):
                                                            func_name = None
                                                            if hasattr(kwarg.value.func, 'id'):
                                                                func_name = kwarg.value.func.id
                                                            elif hasattr(kwarg.value.func, 'attr'):
                                                                func_name = kwarg.value.func.attr
                                                            value = f"{func_name}(...)"
                                                        else:
                                                            value = str(kwarg.value)

                                                    kwargs[key] = value

                                                model_info['fields'].append({
                                                    'name': field_name,
                                                    'type': field_type,
                                                    'args': args,
                                                    'kwargs': kwargs,
                                                })

                            elif isinstance(item, ast.FunctionDef):
                                # This is a method
                                method_name = item.name

                                # Check if it's a property
                                is_property = False
                                for decorator in item.decorator_list:
                                    if isinstance(decorator, ast.Name) and decorator.id == 'property':
                                        is_property = True
                                        break

                                if is_property:
                                    model_info['properties'].append({
                                        'name': method_name,
                                        'docstring': self._parse_docstring(item),
                                    })
                                else:
                                    # Regular method
                                    method_args = [arg.arg for arg in item.args.args if arg.arg != 'self']

                                    model_info['methods'].append({
                                        'name': method_name,
                                        'args': method_args,
                                        'docstring': self._parse_docstring(item),
                                    })

                            elif isinstance(item, ast.ClassDef) and item.name == 'Meta':
                                # This is the Meta class
                                meta_attrs = {}

                                for meta_node in item.body:
                                    if isinstance(meta_node, ast.Assign):
                                        for target in meta_node.targets:
                                            if isinstance(target, ast.Name):
                                                attr_name = target.id
                                                attr_value = self.get_ast_value(meta_node.value)

                                                if attr_value is not None:
                                                    meta_attrs[attr_name] = attr_value
                                                else:
                                                    meta_attrs[attr_name] = str(meta_node.value)

                                model_info['meta'] = meta_attrs

                        # Add this model to the list
                        models.append(model_info)

            return {
                'imports': imports,
                'from_imports': from_imports,
                'models': models,
            }

        except Exception as e:
            logger.error(f"Failed to analyze models.py file {normalize_path(file_path)}: {str(e)}")
            traceback.print_exc()
            return None

    def analyze_app_models(self, app_info):
        """
        Combine static analysis with Django's model introspection for complete model info.

        Args:
            app_info (dict): Information about the app

        Returns:
            list: List of model information dictionaries
        """
        app_name = app_info['app_config'].name
        app_label = app_name.split('.')[-1]
        django_models = app_info['models']

        logger.info(f"Analyzing models for app: {app_name}")

        # Get models info from the models.py file
        models_file = app_info['models_file']
        if not models_file:
            logger.error(f"Could not find models.py file for app {app_name}")
            return []

        # Parse the models.py file
        parsed_info = self.analyze_models_file(models_file)
        if not parsed_info:
            logger.error(f"Failed to parse models.py file for app {app_name}")
            return []

        # Combine parsed info with Django's model introspection
        model_infos = []

        # Create a mapping from model name to Django model object
        django_models_map = {model.__name__: model for model in django_models}

        for parsed_model in parsed_info['models']:
            model_name = parsed_model['name']

            # Skip abstract models
            meta = parsed_model.get('meta', {})
            if meta and meta.get('abstract') is True:
                logger.info(f"  Skipping abstract model: {model_name}")
                continue

            # Get the corresponding Django model
            django_model = django_models_map.get(model_name)
            if not django_model:
                logger.warning(f"Model {model_name} found in models.py but not in Django's registry")
                continue

            # Combine information
            model_info = {
                'name': model_name,
                'django_model': django_model,
                'docstring': parsed_model['docstring'],
                'fields': [],
                'foreign_keys': [],
                'many_to_many': [],
                'properties': parsed_model['properties'],
                'methods': parsed_model['methods'],
                'meta': parsed_model['meta'],
                'has_access_level': False,  # Will be set later
                'app_label': app_label,
            }

            # Process fields using Django's introspection
            fields_map = {field['name']: field for field in parsed_model['fields']}

            for field in django_model._meta.get_fields():
                field_name = field.name
                field_type = type(field).__name__

                # Get the parsed field info if available
                parsed_field = fields_map.get(field_name, {})

                field_info = {
                    'name': field_name,
                    'type': field_type,
                    'attname': hasattr(field, 'attname') and field.attname or field_name,
                    'null': getattr(field, 'null', False),
                }

                # Add common attributes
                for attr in ['verbose_name', 'blank', 'default', 'help_text', 'choices', 'max_length']:
                    if hasattr(field, attr):
                        value = getattr(field, attr)
                        if value is not None and not (attr == 'default' and value == field.default):
                            field_info[attr] = value

                # Handle relationships
                if hasattr(field, 'related_model') and field.related_model:
                    related_model_name = field.related_model.__name__
                    related_app_label = field.related_model._meta.app_label

                    field_info['related_model'] = {
                        'name': related_model_name,
                        'app_label': related_app_label,
                    }

                    if field_type in ['ManyToManyField', 'ManyToManyRel']:
                        model_info['many_to_many'].append(field_info)
                    elif field_type in ['ForeignKey', 'OneToOneField', 'OneToOneRel']:
                        model_info['foreign_keys'].append(field_info)
                    else:
                        model_info['fields'].append(field_info)
                else:
                    model_info['fields'].append(field_info)

                # Check if this is an access_level field
                if field_name == 'access_level':
                    model_info['has_access_level'] = True

            # Add model to the list
            model_infos.append(model_info)
            processed_models.append(f"{app_name}.{model_name}")
            logger.info(f"  Processed model: {model_name}")

        return model_infos

    def _parse_docstring(self, node):
        """
        Extract docstring from a class or function node in the AST.

        Args:
            node: AST node (class or function)

        Returns:
            str: The docstring or empty string if not found
        """
        if node.body and isinstance(node.body[0], ast.Expr):
            value = self.get_ast_value(node.body[0].value)
            if isinstance(value, str):
                return value.strip()
        return ""

class SerializerGenerator:
    """
    Class to generate serializer code from model definitions.
    """

    def __init__(self):
        """Initialize the SerializerGenerator."""
        # Registry of computed fields for specific models
        # Note: Keep this registry in sync with model changes
        self.computed_fields = {
            'Subscription': {
                'days_remaining': {
                    'method': 'get_days_remaining',
                    'source': None,
                    'code': [
                        "def get_days_remaining(self, obj):",
                        "    \"\"\"Calculate days remaining in subscription.\"\"\"",
                        "    if not obj.end_date:",
                        "        return None",
                        "    today = timezone.now().date()",
                        "    if obj.end_date.date() < today:",
                        "        return 0",
                        "    return (obj.end_date.date() - today).days"
                    ]
                },
                'is_active': {
                    'method': 'get_is_active',
                    'source': 'status',
                    'code': [
                        "def get_is_active(self, obj):",
                        "    \"\"\"Check if the subscription is active.\"\"\"",
                        "    return obj.status == 'active'"
                    ]
                }
            },
            'AssessmentAttempt': {
                'score_percentage': {
                    'method': 'get_score_percentage',
                    'source': None,
                    'code': [
                        "def get_score_percentage(self, obj):",
                        "    \"\"\"Calculate the score as a percentage.\"\"\"",
                        "    if not obj.assessment or not obj.assessment.passing_score:",
                        "        return 0",
                        "    return int((obj.score / obj.assessment.passing_score) * 100)"
                    ]
                }
            },
            'Certificate': {
                'course': {
                    'method': 'get_course',
                    'source': 'enrollment.course',
                    'code': [
                        "def get_course(self, obj):",
                        "    \"\"\"Get the course from the enrollment.\"\"\"",
                        "    if obj.enrollment and obj.enrollment.course:",
                        "        return obj.enrollment.course.id",
                        "    return None"
                    ]
                },
                'user': {
                    'method': 'get_user',
                    'source': 'enrollment.user',
                    'code': [
                        "def get_user(self, obj):",
                        "    \"\"\"Get the user from the enrollment.\"\"\"",
                        "    if obj.enrollment and obj.enrollment.user:",
                        "        return obj.enrollment.user.id",
                        "    return None"
                    ]
                }
            },
            'Course': {
                'category_id': {
                    'method': None,  # Will be handled as a regular field, not SerializerMethodField
                    'source': 'category',
                    'code': []
                },
                'rating': {
                    'method': 'get_rating',
                    'source': None,
                    'code': [
                        "def get_rating(self, obj):",
                        "    \"\"\"Calculate the average rating for the course.\"\"\"",
                        "    reviews = obj.reviews.all()",
                        "    if not reviews:",
                        "        return None",
                        "    return sum(review.rating for review in reviews) / reviews.count()"
                    ]
                },
                'enrolled_students': {
                    'method': 'get_enrolled_students',
                    'source': None,
                    'code': [
                        "def get_enrolled_students(self, obj):",
                        "    \"\"\"Get the count of enrolled students.\"\"\"",
                        "    return obj.enrollments.count()"
                    ]
                },
                'is_enrolled': {
                    'method': 'get_is_enrolled',
                    'source': None,
                    'code': [
                        "def get_is_enrolled(self, obj):",
                        "    \"\"\"Check if the current user is enrolled in this course.\"\"\"",
                        "    request = self.context.get('request')",
                        "    if not request or not request.user.is_authenticated:",
                        "        return False",
                        "    return obj.enrollments.filter(user=request.user).exists()"
                    ]
                }
            },
            'Enrollment': {
                'course_id': {
                    'method': None,  # Will be handled as a regular field, not SerializerMethodField
                    'source': 'course',
                    'code': []
                }
            },
            'Lesson': {
                'premium_resources': {
                    'method': 'get_premium_resources',
                    'source': None,
                    'code': [
                        "def get_premium_resources(self, obj):",
                        "    \"\"\"Get premium resources for this lesson.\"\"\"",
                        "    return obj.resource_set.filter(premium=True).values('id', 'title', 'type')"
                    ]
                },
                'is_completed': {
                    'method': 'get_is_completed',
                    'source': None,
                    'code': [
                        "def get_is_completed(self, obj):",
                        "    \"\"\"Check if the current user has completed this lesson.\"\"\"",
                        "    request = self.context.get('request')",
                        "    if not request or not request.user.is_authenticated:",
                        "        return False",
                        "    return obj.progress.filter(enrollment__user=request.user, is_completed=True).exists()"
                    ]
                }
            }
        }

    def generate_serializer_code(self, model_info):
        """
        Generate code for a serializer for a specific model.

        Args:
            model_info (dict): Information about the model

        Returns:
            str: The generated serializer code
        """
        model_name = model_info['name']
        serializer_name = f"{model_name}Serializer"

        code = []

        # Generate class header
        code.append(f"class {serializer_name}(serializers.ModelSerializer):")

        # Add docstring
        docstring = model_info.get('docstring', '') or f"Serializer for the {model_name} model."
        code.append(f'{INDENT}"""')
        code.append(f'{INDENT}{docstring}')
        code.append(f'{INDENT}')
        code.append(f'{INDENT}This serializer handles conversion between {model_name} instances and JSON representations.')
        code.append(f'{INDENT}"""')

        # Add SerializerMethodField declarations for computed fields
        added_fields = set()  # Track fields we've already added
        method_fields = []
        direct_fields = []

        # Add computed field declarations - only if they have a method
        if model_name in self.computed_fields:
            for field_name, field_info in self.computed_fields[model_name].items():
                if field_name not in added_fields:
                    if field_info['method']:  # Only add SerializerMethodField if there's a method
                        method_fields.append(f"{INDENT}# Computed field {field_name}")
                        method_fields.append(f"{INDENT}{field_name} = serializers.SerializerMethodField()")
                    else:  # For fields without methods, use appropriate serializer field with source
                        direct_fields.append(f"{INDENT}# Field from {field_info['source']}")
                        direct_fields.append(f"{INDENT}{field_name} = serializers.IntegerField(source='{field_info['source']}', read_only=True)")
                    added_fields.add(field_name)

        # Add property fields
        for prop in model_info['properties']:
            prop_name = prop['name']
            if prop_name not in added_fields:
                method_fields.append(f"{INDENT}# Property field {prop_name}")
                method_fields.append(f"{INDENT}{prop_name} = serializers.SerializerMethodField()")
                added_fields.add(prop_name)

        # Add access_level_display if needed
        if model_info['has_access_level'] and 'access_level_display' not in added_fields:
            method_fields.append(f"{INDENT}# Access level display field")
            method_fields.append(f"{INDENT}access_level_display = serializers.SerializerMethodField()")
            added_fields.add('access_level_display')

        # Add custom field definitions for relationships if needed
        relationship_fields = []

        # Foreign keys - only add *_display fields, not duplicate _id fields
        for field in model_info['foreign_keys']:
            field_name = field['name']

            # Add string representation field
            relationship_fields.append(f"{INDENT}# String representation of {field_name}")
            relationship_fields.append(f"{INDENT}{field_name}_display = serializers.StringRelatedField(")
            relationship_fields.append(f"{INDENT}{INDENT}source='{field_name}',")
            relationship_fields.append(f"{INDENT}{INDENT}read_only=True")
            relationship_fields.append(f"{INDENT})")
            added_fields.add(f"{field_name}_display")

        # Add all fields
        all_field_sections = []
        if method_fields:
            all_field_sections.append(method_fields)
        if direct_fields:
            all_field_sections.append(direct_fields)
        if relationship_fields:
            all_field_sections.append(relationship_fields)

        # Add each section with a separator
        for i, section in enumerate(all_field_sections):
            if section:
                code.extend(section)
                if i < len(all_field_sections) - 1:
                    code.append("")  # Add separator between sections

        # Add computed field methods from our registry
        added_methods = []

        if model_name in self.computed_fields:
            field_methods = self.computed_fields[model_name]

            for field_name, field_info in field_methods.items():
                method_name = field_info['method']

                if method_name and field_info['code']:
                    code.append("")
                    for line in field_info['code']:
                        code.append(f"{INDENT}{line}")
                    added_methods.append(method_name)

        # Add property field methods
        for prop in model_info['properties']:
            prop_name = prop['name']
            method_name = f"get_{prop_name}"

            if method_name not in added_methods:
                code.append("")
                code.append(f"{INDENT}def {method_name}(self, obj):")
                code.append(f"{INDENT}{INDENT}\"\"\"Get the {prop_name} property.\"\"\"")
                code.append(f"{INDENT}{INDENT}return obj.{prop_name}")
                added_methods.append(method_name)

        # Add custom methods for special fields
        if model_info['has_access_level'] and 'get_access_level_display' not in added_methods:
            code.append("")
            code.append(f"{INDENT}def get_access_level_display(self, obj):")
            code.append(f"{INDENT}{INDENT}\"\"\"Return the display name for the access level.\"\"\"")
            code.append(f"{INDENT}{INDENT}return obj.get_access_level_display()")

        # Generate Meta class
        code.append("")
        code.append(f"{INDENT}class Meta:")
        code.append(f"{INDENT}{INDENT}\"\"\"Meta options for the {model_name} serializer.\"\"\"")
        code.append(f"{INDENT}{INDENT}model = {model_name}")

        # Add fields list
        code.append(f"{INDENT}{INDENT}fields = [")

        # Collect all fields to include
        all_fields = set()

        # Basic fields
        for field in model_info['fields']:
            all_fields.add(field['name'])

        # Foreign keys (just add the base field name, not the _id version)
        for field in model_info['foreign_keys']:
            all_fields.add(field['name'])
            all_fields.add(f"{field['name']}_display")

        # Many-to-many fields
        for field in model_info['many_to_many']:
            all_fields.add(field['name'])

        # Properties
        for prop in model_info['properties']:
            all_fields.add(prop['name'])

        # Add computed fields
        if model_name in self.computed_fields:
            for field_name in self.computed_fields[model_name].keys():
                all_fields.add(field_name)

        # If it has access_level, add the display field
        if model_info['has_access_level']:
            all_fields.add('access_level_display')

        # Sort and add fields
        for field in sorted(all_fields):
            code.append(f"{INDENT}{INDENT}{INDENT}'{field}',")

        code.append(f"{INDENT}{INDENT}]")

        # Add read_only_fields for properties and computed fields
        read_only_fields = set()

        # Properties are read-only
        for prop in model_info['properties']:
            read_only_fields.add(prop['name'])

        # Add computed fields to read_only_fields
        if model_name in self.computed_fields:
            for field_name in self.computed_fields[model_name].keys():
                read_only_fields.add(field_name)

        # Access level display is read-only
        if model_info['has_access_level']:
            read_only_fields.add('access_level_display')

        # Add display fields for foreign keys
        for field in model_info['foreign_keys']:
            read_only_fields.add(f"{field['name']}_display")

        # Make sure all read_only_fields are in fields list
        for field in list(read_only_fields):
            if field not in all_fields:
                warnings.append(f"Field {field} in read_only_fields but not in fields for {model_name}Serializer")
                read_only_fields.remove(field)

        if read_only_fields:
            code.append("")
            code.append(f"{INDENT}{INDENT}read_only_fields = [")
            for field in sorted(read_only_fields):
                code.append(f"{INDENT}{INDENT}{INDENT}'{field}',")
            code.append(f"{INDENT}{INDENT}]")

        # Add extra_kwargs if needed for foreign keys with null constraints
        extra_kwargs = {}
        for field in model_info['foreign_keys']:
            field_name = field['name']
            # Set required based on null constraint
            if not field['null']:
                extra_kwargs[field_name] = {'required': True}
            else:
                extra_kwargs[field_name] = {'required': False}

        if extra_kwargs:
            code.append("")
            code.append(f"{INDENT}{INDENT}extra_kwargs = {{")
            for field_name, kwargs in sorted(extra_kwargs.items()):
                kwargs_str = ', '.join([f"'{k}': {v}" for k, v in kwargs.items()])
                code.append(f"{INDENT}{INDENT}{INDENT}'{field_name}': {{{kwargs_str}}},")
            code.append(f"{INDENT}{INDENT}}}")

        return "\n".join(code)

    def generate_serializers_file(self, app_info, model_infos, file_path=None):
        """
        Generate a serializers.py file for an app.

        Args:
            app_info (dict): Information about the app
            model_infos (list): List of model information dictionaries
            file_path (str, optional): Custom path to save the file

        Returns:
            str: The path to the generated file
        """
        app_name = app_info['app_config'].name
        app_label = app_name.split('.')[-1]
        app_dir = app_info['app_dir']

        # Determine the file path
        if not file_path:
            file_path = os.path.join(app_dir, 'serializers.py')

        logger.info(f"Generating serializers.py for {app_name}...")

        # Back up existing file if needed
        if os.path.exists(file_path) and BACKUP_EXISTING:
            backup_path = backup_file(file_path)
            logger.info(f"Backed up existing serializers.py to {backup_path}")

        # Start with the file header
        content = []

        # Add formatting protection
        content.append(FORMAT_PROTECTION)

        # Add file header docstring
        content.append(f'r"""')
        content.append(f'File: {normalize_path(file_path)}')
        content.append(f'')
        content.append(f'This file contains serializers for the {app_label} app models.')
        content.append(f'These serializers convert model instances to JSON for the API and validate incoming data.')
        content.append(f'')
        content.append(f'These serializers support the educational platform\'s three-tier access system:')
        content.append(f'1. Unregistered users: Can view basic content')
        content.append(f'2. Registered users: Can view intermediate content')
        content.append(f'3. Paid users: Can view advanced content with certificates')
        content.append(f'')
        content.append(f'Generated by: django_api_generator.py')
        content.append(f'Date: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        content.append(f'Author: nanthiniSanthanam')
        content.append(f'"""')
        content.append('')

        # Check if we need to import timezone
        need_timezone = False
        for model_info in model_infos:
            model_name = model_info['name']
            if model_name in self.computed_fields:
                for field_name, field_info in self.computed_fields[model_name].items():
                    if 'timezone' in '\n'.join(field_info.get('code', [])):
                        need_timezone = True
                        break

        # Add imports
        if need_timezone:
            content.append('from django.utils import timezone')
        content.append('from rest_framework import serializers')

        # Import all models from this app
        model_names = [model['name'] for model in model_infos]
        content.append(f'from .models import {", ".join(model_names)}')

        # Import related models from other apps
        related_imports = {}

        for model_info in model_infos:
            for field in model_info['foreign_keys'] + model_info['many_to_many']:
                if 'related_model' in field:
                    related_app = field['related_model']['app_label']
                    related_model = field['related_model']['name']

                    if related_app != app_label:
                        if related_app not in related_imports:
                            related_imports[related_app] = set()
                        related_imports[related_app].add(related_model)

        # Convert the sets to lists to avoid modification during iteration
        for app in related_imports:
            related_imports[app] = sorted(list(related_imports[app]))

        for app, models in sorted(related_imports.items()):
            content.append(f'from {app}.models import {", ".join(models)}')

        content.append('')

        # Add serializer classes
        for model_info in model_infos:
            # Generate serializer code for this model
            serializer_code = self.generate_serializer_code(model_info)
            content.append(serializer_code)
            content.append('')

        # Write the file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))

            logger.info(f"Successfully wrote serializers.py for {app_name}")
            generated_files.append(file_path)
            return file_path
        except Exception as e:
            logger.error(f"Failed to write serializers.py for {app_name}: {str(e)}")
            return None

class ViewGenerator:
    """
    Class to generate view code from model definitions.
    """

    def __init__(self):
        """Initialize the ViewGenerator."""
        # Custom actions for specific models
        self.custom_actions = {
            'Course': [
                {
                    'name': 'modules',
                    'detail': True,
                    'methods': ['get'],
                    'code': [
                        "def modules(self, request, pk=None):",
                        "    \"\"\"List all modules for this course.\"\"\"",
                        "    course = self.get_object()",
                        "    modules = course.module_set.all().order_by('order')",
                        "    from .serializers import ModuleSerializer",
                        "    serializer = ModuleSerializer(modules, many=True)",
                        "    return Response(serializer.data)"
                    ]
                },
                {
                    'name': 'enroll',
                    'detail': True,
                    'methods': ['post'],
                    'code': [
                        "def enroll(self, request, pk=None):",
                        "    \"\"\"Enroll the current user in this course.\"\"\"",
                        "    course = self.get_object()",
                        "    user = request.user",
                        "",
                        "    if not user.is_authenticated:",
                        "        return Response({'error': 'You must be logged in to enroll'}, status=status.HTTP_401_UNAUTHORIZED)",
                        "",
                        "    # Check if user is already enrolled",
                        "    if course.enrollments.filter(user=user).exists():",
                        "        return Response({'message': 'Already enrolled'}, status=status.HTTP_200_OK)",
                        "",
                        "    # Create enrollment",
                        "    from .models import Enrollment",
                        "    enrollment = Enrollment.objects.create(",
                        "        user=user,",
                        "        course=course,",
                        "        status='active'",
                        "    )",
                        "",
                        "    from .serializers import EnrollmentSerializer",
                        "    serializer = EnrollmentSerializer(enrollment)",
                        "    return Response(serializer.data, status=status.HTTP_201_CREATED)"
                    ]
                },
                {
                    'name': 'reviews',
                    'detail': True,
                    'methods': ['get', 'post'],
                    'code': [
                        "def reviews(self, request, pk=None):",
                        "    \"\"\"Get or create reviews for this course.\"\"\"",
                        "    course = self.get_object()",
                        "",
                        "    if request.method == 'POST':",
                        "        # Check if user is authenticated",
                        "        if not request.user.is_authenticated:",
                        "            return Response({'error': 'You must be logged in to submit a review'}, ",
                        "                            status=status.HTTP_401_UNAUTHORIZED)",
                        "",
                        "        # Check if user is enrolled in the course",
                        "        if not course.enrollments.filter(user=request.user).exists():",
                        "            return Response({'error': 'You must be enrolled in the course to submit a review'}, ",
                        "                            status=status.HTTP_403_FORBIDDEN)",
                        "",
                        "        # Check if user has already reviewed this course",
                        "        if course.reviews.filter(user=request.user).exists():",
                        "            return Response({'error': 'You have already reviewed this course'}, ",
                        "                            status=status.HTTP_400_BAD_REQUEST)",
                        "",
                        "        # Create the review",
                        "        from .models import Review",
                        "        from .serializers import ReviewSerializer",
                        "",
                        "        data = request.data.copy()",
                        "        data['user'] = request.user.id",
                        "        data['course'] = course.id",
                        "",
                        "        serializer = ReviewSerializer(data=data)",
                        "        if serializer.is_valid():",
                        "            serializer.save()",
                        "            return Response(serializer.data, status=status.HTTP_201_CREATED)",
                        "        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)",
                        "    else:",
                        "        # Get all reviews for this course",
                        "        from .serializers import ReviewSerializer",
                        "        reviews = course.reviews.all()",
                        "        serializer = ReviewSerializer(reviews, many=True)",
                        "        return Response(serializer.data)"
                    ]
                }
            ],
            'Module': [
                {
                    'name': 'lessons',
                    'detail': True,
                    'methods': ['get'],
                    'code': [
                        "def lessons(self, request, pk=None):",
                        "    \"\"\"List all lessons for this module.\"\"\"",
                        "    module = self.get_object()",
                        "    lessons = module.lesson_set.all().order_by('order')",
                        "    from .serializers import LessonSerializer",
                        "    serializer = LessonSerializer(lessons, many=True, context={'request': request})",
                        "    return Response(serializer.data)"
                    ]
                }
            ],
            'Lesson': [
                {
                    'name': 'complete',
                    'detail': True,
                    'methods': ['post'],
                    'code': [
                        "def complete(self, request, pk=None):",
                        "    \"\"\"Mark this lesson as completed for the current user.\"\"\"",
                        "    lesson = self.get_object()",
                        "    user = request.user",
                        "",
                        "    if not user.is_authenticated:",
                        "        return Response({'error': 'You must be logged in to mark lessons as complete'}, ",
                        "                       status=status.HTTP_401_UNAUTHORIZED)",
                        "",
                        "    # Get the enrollment for this course",
                        "    course = lesson.module.course",
                        "    try:",
                        "        enrollment = course.enrollments.get(user=user)",
                        "    except Enrollment.DoesNotExist:",
                        "        return Response({'error': 'You must be enrolled in this course'}, ",
                        "                       status=status.HTTP_403_FORBIDDEN)",
                        "",
                        "    # Create or update progress record",
                        "    from .models import Progress",
                        "    progress, created = Progress.objects.update_or_create(",
                        "        enrollment=enrollment,",
                        "        lesson=lesson,",
                        "        defaults={",
                        "            'is_completed': True,",
                        "            'completed_date': timezone.now(),",
                        "        }",
                        "    )",
                        "",
                        "    from .serializers import ProgressSerializer",
                        "    serializer = ProgressSerializer(progress)",
                        "    return Response(serializer.data)"
                    ]
                },
                {
                    'name': 'resources',
                    'detail': True,
                    'methods': ['get'],
                    'code': [
                        "def resources(self, request, pk=None):",
                        "    \"\"\"List resources for this lesson based on user's access level.\"\"\"",
                        "    lesson = self.get_object()",
                        "    user = request.user",
                        "",
                        "    # Filter resources based on user's subscription",
                        "    resources = lesson.resource_set.all()",
                        "    if not user.is_authenticated:",
                        "        # No resources for unregistered users",
                        "        resources = resources.filter(premium=False).filter(type='document')",
                        "    elif not (hasattr(user, 'subscription') and user.subscription and ",
                        "             user.subscription.tier == 'premium' and user.subscription.status == 'active'):",
                        "        # Non-premium users only get non-premium resources",
                        "        resources = resources.filter(premium=False)",
                        "",
                        "    from .serializers import ResourceSerializer",
                        "    serializer = ResourceSerializer(resources, many=True)",
                        "    return Response(serializer.data)"
                    ]
                }
            ],
            'Assessment': [
                {
                    'name': 'start',
                    'detail': True,
                    'methods': ['post'],
                    'code': [
                        "def start(self, request, pk=None):",
                        "    \"\"\"Start an assessment attempt.\"\"\"",
                        "    assessment = self.get_object()",
                        "    user = request.user",
                        "",
                        "    if not user.is_authenticated:",
                        "        return Response({'error': 'You must be logged in to take assessments'}, ",
                        "                       status=status.HTTP_401_UNAUTHORIZED)",
                        "",
                        "    # Create a new attempt",
                        "    from .models import AssessmentAttempt",
                        "    attempt = AssessmentAttempt.objects.create(",
                        "        user=user,",
                        "        assessment=assessment,",
                        "        start_time=timezone.now(),",
                        "        score=0,",
                        "        passed=False",
                        "    )",
                        "",
                        "    from .serializers import AssessmentAttemptSerializer",
                        "    serializer = AssessmentAttemptSerializer(attempt)",
                        "    return Response(serializer.data, status=status.HTTP_201_CREATED)"
                    ]
                },
                {
                    'name': 'submit',
                    'detail': True,
                    'methods': ['post'],
                    'code': [
                        "def submit(self, request, pk=None):",
                        "    \"\"\"Submit answers for an assessment attempt.\"\"\"",
                        "    assessment = self.get_object()",
                        "    user = request.user",
                        "",
                        "    if not user.is_authenticated:",
                        "        return Response({'error': 'You must be logged in to submit assessments'}, ",
                        "                       status=status.HTTP_401_UNAUTHORIZED)",
                        "",
                        "    # Get the attempt ID from request data",
                        "    attempt_id = request.data.get('attempt_id')",
                        "    if not attempt_id:",
                        "        return Response({'error': 'attempt_id is required'}, status=status.HTTP_400_BAD_REQUEST)",
                        "",
                        "    try:",
                        "        from .models import AssessmentAttempt, AttemptAnswer",
                        "        attempt = AssessmentAttempt.objects.get(id=attempt_id, user=user, assessment=assessment)",
                        "    except AssessmentAttempt.DoesNotExist:",
                        "        return Response({'error': 'Attempt not found'}, status=status.HTTP_404_NOT_FOUND)",
                        "",
                        "    # Check if attempt is already completed",
                        "    if attempt.end_time is not None:",
                        "        return Response({'error': 'This attempt has already been submitted'}, ",
                        "                       status=status.HTTP_400_BAD_REQUEST)",
                        "",
                        "    # Get answers from request data",
                        "    answers = request.data.get('answers', [])",
                        "    if not answers:",
                        "        return Response({'error': 'No answers provided'}, status=status.HTTP_400_BAD_REQUEST)",
                        "",
                        "    # Process each answer",
                        "    total_points = 0",
                        "    for answer_data in answers:",
                        "        question_id = answer_data.get('question_id')",
                        "        selected_answer_id = answer_data.get('selected_answer_id')",
                        "        text_answer = answer_data.get('text_answer')",
                        "",
                        "        try:",
                        "            from .models import Question, Answer",
                        "            question = Question.objects.get(id=question_id, assessment=assessment)",
                        "        except Question.DoesNotExist:",
                        "            continue",
                        "",
                        "        # Handle different question types",
                        "        is_correct = False",
                        "        points_earned = 0",
                        "",
                        "        if question.question_type in ['multiple_choice', 'true_false']:",
                        "            if selected_answer_id:",
                        "                try:",
                        "                    selected_answer = Answer.objects.get(id=selected_answer_id, question=question)",
                        "                    is_correct = selected_answer.is_correct",
                        "                    points_earned = question.points if is_correct else 0",
                        "                except Answer.DoesNotExist:",
                        "                    pass",
                        "        elif question.question_type == 'short_answer':",
                        "            # For short answers, set is_correct=False initially",
                        "            # An admin will need to review and grade this manually",
                        "            is_correct = False",

                            "            points_earned = 0",
                            "",
                            "        # Create attempt answer",
                            "        attempt_answer = AttemptAnswer.objects.create(",
                            "            attempt=attempt,",
                            "            question=question,",
                            "            selected_answer_id=selected_answer_id,",
                            "            text_answer=text_answer,",
                            "            is_correct=is_correct,",
                            "            points_earned=points_earned",
                            "        )",
                            "",
                            "        total_points += points_earned",
                            "",
                            "    # Update attempt with score and completion time",
                            "    attempt.end_time = timezone.now()",
                            "    attempt.score = total_points",
                            "    attempt.passed = total_points >= assessment.passing_score",
                            "    attempt.save()",
                            "",
                            "    # Return updated attempt",
                            "    from .serializers import AssessmentAttemptSerializer",
                            "    serializer = AssessmentAttemptSerializer(attempt)",
                            "    return Response(serializer.data)"
                        ]
                    }
                ]
            }
        }

    def generate_view_code(self, app_info, model_info):
        """
        Generate code for a view for a specific model.

        Args:
            app_info (dict): Information about the app
            model_info (dict): Information about the model

        Returns:
            str: The generated view code
        """
        model_name = model_info['name']
        view_name = f"{model_name}ViewSet"
        serializer_name = f"{model_name}Serializer"
        app_label = app_info['app_config'].name.split('.')[-1]

        # Get proper plural name for URL patterns
        url_name_plural = get_model_plural_name(model_info)

        code = []

        # Generate class header
        code.append(f"class {view_name}(viewsets.ModelViewSet):")

        # Add docstring
        code.append(f'{INDENT}"""')
        code.append(f'{INDENT}API endpoint for {model_name} objects.')
        code.append(f'{INDENT}')
        code.append(f'{INDENT}This viewset automatically provides:')
        code.append(f'{INDENT}- List view: GET /{API_PREFIX}{app_label}/{url_name_plural}/')
        code.append(f'{INDENT}- Detail view: GET /{API_PREFIX}{app_label}/{url_name_plural}/{{id}}/')
        code.append(f'{INDENT}- Create view: POST /{API_PREFIX}{app_label}/{url_name_plural}/')
        code.append(f'{INDENT}- Update view: PUT /{API_PREFIX}{app_label}/{url_name_plural}/{{id}}/')
        code.append(f'{INDENT}- Partial update: PATCH /{API_PREFIX}{app_label}/{url_name_plural}/{{id}}/')
        code.append(f'{INDENT}- Delete view: DELETE /{API_PREFIX}{app_label}/{url_name_plural}/{{id}}/')

        # Add custom actions to docstring if present
        if model_name in self.custom_actions:
            for action in self.custom_actions[model_name]:
                action_name = action['name']
                methods_str = ', '.join(action['methods']).upper()
                code.append(f'{INDENT}- {action_name}: {methods_str} /{API_PREFIX}{app_label}/{url_name_plural}/{{id}}/{action_name}/')

        code.append(f'{INDENT}"""')

        # Basic view configuration
        code.append(f'{INDENT}queryset = {model_name}.objects.all()')
        code.append(f'{INDENT}serializer_class = {serializer_name}')
        code.append(f'{INDENT}pagination_class = StandardResultsSetPagination')

        # Add permission classes
        if model_info['has_access_level']:
            code.append(f'{INDENT}permission_classes = [AccessLevelPermission]')
        else:
            code.append(f'{INDENT}permission_classes = [permissions.IsAuthenticatedOrReadOnly]')

        # Add filter backends
        code.append(f'{INDENT}filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]')

        # Add filterset_fields
        code.append(f'{INDENT}filterset_fields = [')

        # Add basic fields suitable for filtering
        for field in model_info['fields']:
            # Skip text fields and file fields
            if field['type'] not in ['TextField', 'FileField', 'ImageField', 'JSONField']:
                code.append(f"{INDENT}{INDENT}'{field['name']}',")

        # Add foreign key fields with _id for proper filtering
        for field in model_info['foreign_keys']:
            # Use _id instead of __id for standard Django filtering
            code.append(f"{INDENT}{INDENT}'{field['name']}_id',")
            code.append(f"{INDENT}{INDENT}'{field['name']}',")

        code.append(f'{INDENT}]')

        # Add search_fields
        code.append(f'{INDENT}search_fields = [')

        # Add text fields suitable for searching
        for field in model_info['fields']:
            if field['type'] in ['CharField', 'TextField', 'SlugField', 'EmailField']:
                code.append(f"{INDENT}{INDENT}'{field['name']}',")

        code.append(f'{INDENT}]')

        # Add ordering_fields
        code.append(f'{INDENT}ordering_fields = [')

        # Add fields suitable for ordering
        for field in model_info['fields']:
            if field['type'] not in ['FileField', 'ImageField', 'JSONField']:
                code.append(f"{INDENT}{INDENT}'{field['name']}',")

        code.append(f'{INDENT}]')

        # Default ordering based on common field names
        default_ordering = '-id'
        for field in model_info['fields']:
            if field['name'] in ['created_at', 'date_created', 'created', 'order']:
                if field['name'] == 'order':
                    default_ordering = 'order'
                else:
                    default_ordering = f'-{field["name"]}'

        code.append(f'{INDENT}ordering = ["{default_ordering}"]  # Default ordering')

        # Add custom queryset handling for models with access_level
        if model_info['has_access_level']:
            code.append("")
            code.append(f"{INDENT}def get_queryset(self):")
            code.append(f"{INDENT}{INDENT}\"\"\"Filter queryset based on user's access level.\"\"\"")
            code.append(f"{INDENT}{INDENT}queryset = super().get_queryset()")
            code.append(f"{INDENT}{INDENT}user = self.request.user")
            code.append(f"")
            code.append(f"{INDENT}{INDENT}# Staff can see everything")
            code.append(f"{INDENT}{INDENT}if user.is_staff or user.is_superuser:")
            code.append(f"{INDENT}{INDENT}{INDENT}return queryset")
            code.append(f"")
            code.append(f"{INDENT}{INDENT}# Anonymous users can only see basic content")
            code.append(f"{INDENT}{INDENT}if not user.is_authenticated:")
            code.append(f"{INDENT}{INDENT}{INDENT}return queryset.filter(access_level='basic')")
            code.append(f"")
            code.append(f"{INDENT}{INDENT}# Check subscription for authenticated users")
            code.append(f"{INDENT}{INDENT}has_premium = (")
            code.append(f"{INDENT}{INDENT}{INDENT}hasattr(user, 'subscription') and")
            code.append(f"{INDENT}{INDENT}{INDENT}user.subscription and")
            code.append(f"{INDENT}{INDENT}{INDENT}user.subscription.tier == 'premium' and")
            code.append(f"{INDENT}{INDENT}{INDENT}user.subscription.status == 'active'")
            code.append(f"{INDENT}{INDENT})")
            code.append(f"{INDENT}{INDENT}if has_premium:")
            code.append(f"{INDENT}{INDENT}{INDENT}# Premium users can see everything")
            code.append(f"{INDENT}{INDENT}{INDENT}return queryset")
            code.append(f"{INDENT}{INDENT}else:")
            code.append(f"{INDENT}{INDENT}{INDENT}# Regular users can see basic and intermediate content")
            code.append(f"{INDENT}{INDENT}{INDENT}return queryset.filter(access_level__in=['basic', 'intermediate'])")

        # Add custom retrieve method for Lesson to serve different content
        if model_name == 'Lesson':
            code.append("")
            code.append(f"{INDENT}def retrieve(self, request, *args, **kwargs):")
            code.append(f"{INDENT}{INDENT}\"\"\"Serve different content based on user's access level.\"\"\"")
            code.append(f"{INDENT}{INDENT}instance = self.get_object()")
            code.append(f"{INDENT}{INDENT}serializer = self.get_serializer(instance)")
            code.append(f"{INDENT}{INDENT}data = serializer.data")
            code.append(f"{INDENT}{INDENT}")
            code.append(f"{INDENT}{INDENT}user = request.user")
            code.append(f"{INDENT}{INDENT}# Modify content based on access level")
            code.append(f"{INDENT}{INDENT}if not user.is_authenticated:")
            code.append(f"{INDENT}{INDENT}{INDENT}# Serve basic content for unregistered users")
            code.append(f"{INDENT}{INDENT}{INDENT}if hasattr(instance, 'basic_content') and instance.basic_content:")
            code.append(f"{INDENT}{INDENT}{INDENT}{INDENT}data['content'] = instance.basic_content")
            code.append(f"{INDENT}{INDENT}elif not (hasattr(user, 'subscription') and user.subscription and")
            code.append(f"{INDENT}{INDENT}{INDENT}   user.subscription.tier == 'premium' and user.subscription.status == 'active'):")
            code.append(f"{INDENT}{INDENT}{INDENT}# Serve intermediate content for non-premium users")
            code.append(f"{INDENT}{INDENT}{INDENT}if hasattr(instance, 'intermediate_content') and instance.intermediate_content:")
            code.append(f"{INDENT}{INDENT}{INDENT}{INDENT}data['content'] = instance.intermediate_content")
            code.append(f"{INDENT}{INDENT}")
            code.append(f"{INDENT}{INDENT}return Response(data)")

        # Add custom actions for special models
        if model_name in self.custom_actions:
            for action in self.custom_actions[model_name]:
                code.append("")

                # Add decorator and method signature
                detail = 'True' if action['detail'] else 'False'
                methods = [f"'{method}'" for method in action['methods']]
                methods_str = ', '.join(methods)

                code.append(f"{INDENT}@action(detail={detail}, methods=[{methods_str}])")

                # Add the method body
                for line in action['code']:
                    code.append(f"{INDENT}{line}")

        return "\n".join(code)

    def generate_views_file(self, app_info, model_infos, file_path=None):
        """
        Generate a views.py file for an app.

        Args:
            app_info (dict): Information about the app
            model_infos (list): List of model information dictionaries
            file_path (str, optional): Custom path to save the file

        Returns:
            str: The path to the generated file
        """
        app_name = app_info['app_config'].name
        app_label = app_name.split('.')[-1]
        app_dir = app_info['app_dir']

        # Determine the file path
        if not file_path:
            file_path = os.path.join(app_dir, 'views.py')

        logger.info(f"Generating views.py for {app_name}...")

        # Back up existing file if needed
        if os.path.exists(file_path) and BACKUP_EXISTING:
            backup_path = backup_file(file_path)
            logger.info(f"Backed up existing views.py to {backup_path}")

        # Start with the file header
        content = []

        # Add formatting protection
        content.append(FORMAT_PROTECTION)

        # Add file header docstring
        content.append(f'r"""')
        content.append(f'File: {normalize_path(file_path)}')
        content.append(f'')
        content.append(f'This file contains views and viewsets for the {app_label} app models.')
        content.append(f'These views handle API requests and return appropriate responses.')
        content.append(f'')
        content.append(f'These views support the educational platform\'s three-tier access system:')
        content.append(f'1. Unregistered users: Can view basic content')
        content.append(f'2. Registered users: Can view intermediate content')
        content.append(f'3. Paid users: Can view advanced content with certificates')
        content.append(f'')
        content.append(f'Generated by: django_api_generator.py')
        content.append(f'Date: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        content.append(f'Author: nanthiniSanthanam')
        content.append(f'"""')
        content.append('')

        # Add imports
        content.append('from django.utils import timezone')
        content.append('from django.db.models import Avg, Count')
        content.append('from rest_framework import viewsets, permissions, status')
        content.append('from rest_framework.decorators import action')
        content.append('from rest_framework.response import Response')
        content.append('from rest_framework.pagination import PageNumberPagination')
        content.append('from rest_framework import filters')
        content.append('from django_filters.rest_framework import DjangoFilterBackend')

        # Import all models from this app
        model_names = [model['name'] for model in model_infos]
        content.append(f'from .models import {", ".join(model_names)}')

        # Import all serializers
        serializer_names = [f"{model['name']}Serializer" for model in model_infos]
        content.append(f'from .serializers import {", ".join(serializer_names)}')
        content.append('')

        # Add standard pagination class
        content.append('class StandardResultsSetPagination(PageNumberPagination):')
        content.append(f'{INDENT}"""')
        content.append(f'{INDENT}Standard pagination class for all viewsets.')
        content.append(f'{INDENT}')
        content.append(f'{INDENT}This sets reasonable defaults for page size while allowing')
        content.append(f'{INDENT}clients to override via query parameters.')
        content.append(f'{INDENT}"""')
        content.append(f'{INDENT}page_size = 50')
        content.append(f'{INDENT}page_size_query_param = "page_size"')
        content.append(f'{INDENT}max_page_size = 1000')
        content.append('')

        # Check if we need to add a custom permission class for access levels
        has_access_level_models = any(model['has_access_level'] for model in model_infos)

        if has_access_level_models:
            # Add custom permission class for the three-tier access system
            content.append('class AccessLevelPermission(permissions.BasePermission):')
            content.append(f'{INDENT}"""')
            content.append(f'{INDENT}Custom permission to handle the three-tier access system.')
            content.append(f'{INDENT}')
            content.append(f'{INDENT}This permission class checks the user\'s subscription level against')
            content.append(f'{INDENT}the access_level of the requested object.')
            content.append(f'{INDENT}')
            content.append(f'{INDENT}Access levels:')
            content.append(f'{INDENT}- "basic": Available to all users (even unregistered)')
            content.append(f'{INDENT}- "intermediate": Available to registered users')
            content.append(f'{INDENT}- "advanced": Available only to paid/premium users')
            content.append(f'{INDENT}"""')
            content.append('')
            content.append(f'{INDENT}def has_permission(self, request, view):')
            content.append(f'{INDENT}{INDENT}"""Check if user has permission to access the view."""')
            content.append(f'{INDENT}{INDENT}# Allow all safe methods (GET, HEAD, OPTIONS)')
            content.append(f'{INDENT}{INDENT}if request.method in permissions.SAFE_METHODS:')
            content.append(f'{INDENT}{INDENT}{INDENT}return True')
            content.append(f'{INDENT}{INDENT}# For unsafe methods, require authentication')
            content.append(f'{INDENT}{INDENT}return request.user.is_authenticated')
            content.append('')
            content.append(f'{INDENT}def has_object_permission(self, request, view, obj):')
            content.append(f'{INDENT}{INDENT}"""Check if user has permission to access the object."""')
            content.append(f'{INDENT}{INDENT}# For methods that modify the object')
            content.append(f'{INDENT}{INDENT}if request.method not in permissions.SAFE_METHODS:')
            content.append(f'{INDENT}{INDENT}{INDENT}# Only allow staff to modify objects')
            content.append(f'{INDENT}{INDENT}{INDENT}return request.user.is_staff or request.user.is_superuser')
            content.append('')
            content.append(f'{INDENT}{INDENT}# For safe methods, check access level')
            content.append(f'{INDENT}{INDENT}if not hasattr(obj, "access_level"):')
            content.append(f'{INDENT}{INDENT}{INDENT}return True  # No access level, allow access')
            content.append('')
            content.append(f'{INDENT}{INDENT}# Handle different access levels')
            content.append(f'{INDENT}{INDENT}if obj.access_level == "basic":')
            content.append(f'{INDENT}{INDENT}{INDENT}# Basic content is available to everyone')
            content.append(f'{INDENT}{INDENT}{INDENT}return True')
            content.append(f'{INDENT}{INDENT}elif obj.access_level == "intermediate":')
            content.append(f'{INDENT}{INDENT}{INDENT}# Intermediate content requires authentication')
            content.append(f'{INDENT}{INDENT}{INDENT}return request.user.is_authenticated')
            content.append(f'{INDENT}{INDENT}elif obj.access_level == "advanced":')
            content.append(f'{INDENT}{INDENT}{INDENT}# Advanced content requires premium subscription')
            content.append(f'{INDENT}{INDENT}{INDENT}has_premium = (')
            content.append(f'{INDENT}{INDENT}{INDENT}{INDENT}request.user.is_authenticated and')
            content.append(f'{INDENT}{INDENT}{INDENT}{INDENT}hasattr(request.user, "subscription") and')
            content.append(f'{INDENT}{INDENT}{INDENT}{INDENT}request.user.subscription and')
            content.append(f'{INDENT}{INDENT}{INDENT}{INDENT}request.user.subscription.tier == "premium" and')
            content.append(f'{INDENT}{INDENT}{INDENT}{INDENT}request.user.subscription.status == "active"')
            content.append(f'{INDENT}{INDENT}{INDENT})')
            content.append(f'{INDENT}{INDENT}{INDENT}return has_premium')
            content.append(f'{INDENT}{INDENT}else:')
            content.append(f'{INDENT}{INDENT}{INDENT}# Unknown access level, default to requiring authentication')
            content.append(f'{INDENT}{INDENT}{INDENT}return request.user.is_authenticated')
            content.append('')

        # Add view classes for each model
        for model_info in model_infos:
            # Generate view code for this model
            view_code = self.generate_view_code(app_info, model_info)
            content.append(view_code)
            content.append('')

        # Write the file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))

            logger.info(f"Successfully wrote views.py for {app_name}")
            generated_files.append(file_path)
            return file_path
        except Exception as e:
            logger.error(f"Failed to write views.py for {app_name}: {str(e)}")
            return None

class UrlGenerator:
    """
    Class to generate URL routing code from model definitions.
    """

    def __init__(self):
        """Initialize the UrlGenerator."""
        pass

    def generate_urls_file(self, app_info, model_infos, file_path=None):
        """
        Generate a urls.py file for an app.

        Args:
            app_info (dict): Information about the app
            model_infos (list): List of model information dictionaries
            file_path (str, optional): Custom path to save the file

        Returns:
            str: The path to the generated file
        """
        app_name = app_info['app_config'].name
        app_label = app_name.split('.')[-1]
        app_dir = app_info['app_dir']

        # Determine the file path
        if not file_path:
            file_path = os.path.join(app_dir, 'urls.py')

        logger.info(f"Generating urls.py for {app_name}...")

        # Back up existing file if needed
        if os.path.exists(file_path) and BACKUP_EXISTING:
            backup_path = backup_file(file_path)
            logger.info(f"Backed up existing urls.py to {backup_path}")

        # Start with the file header
        content = []

        # Add formatting protection
        content.append(FORMAT_PROTECTION)

        # Add file header docstring
        content.append(f'r"""')
        content.append(f'File: {normalize_path(file_path)}')
        content.append(f'')
        content.append(f'This file contains URL patterns for the {app_label} app.')
        content.append(f'It defines the API endpoints for accessing the {app_label} models.')
        content.append(f'')
        content.append(f'Generated by: django_api_generator.py')
        content.append(f'Date: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        content.append(f'Author: nanthiniSanthanam')
        content.append(f'"""')
        content.append('')

        # Add imports
        content.append('from django.urls import path, include')
        content.append('from rest_framework.routers import DefaultRouter')
        content.append('from . import views')
        content.append('')

        # Create router
        content.append('# Create a router and register our viewsets with it')
        content.append('router = DefaultRouter()')

        # Register all viewsets
        url_patterns = []

        for model_info in model_infos:
            model_name = model_info['name']
            view_name = f"{model_name}ViewSet"

            # Get proper plural name for URL patterns
            url_name_plural = get_model_plural_name(model_info)

            content.append(f"router.register(r'{url_name_plural}', views.{view_name})")

            # Add to URL patterns list for documentation
            url_patterns.append(f"{API_PREFIX}{app_label}/{url_name_plural}/")

        content.append('')

        # Add app_name for namespacing
        content.append(f"app_name = '{app_label}'")
        content.append('')

        # Add urlpatterns
        content.append('# The API URLs are determined automatically by the router')
        content.append('urlpatterns = [')
        content.append(f"{INDENT}path('', include(router.urls)),")
        content.append(']')

        # Write the file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))

            logger.info(f"Successfully wrote urls.py for {app_name}")
            generated_files.append(file_path)
            return file_path
        except Exception as e:
            logger.error(f"Failed to write urls.py for {app_name}: {str(e)}")
            return None

class MainURLUpdater:
    """
    Class to update the project's main urls.py to include app URLs.
    """

    def __init__(self):
        """Initialize the MainURLUpdater."""
        pass

    def update_project_urls(self, app_infos):
        """
        Update the project's main urls.py file to include the app URLs.

        Args:
            app_infos (list): List of app information dictionaries

        Returns:
            bool: True on success, False on failure
        """
        logger.info("Checking project URLs configuration...")

        # Try to find the project's main urls.py file
        urls_file = None
        potential_locations = [
            os.path.join(PROJECT_DIR, 'urls.py'),
            os.path.join(PROJECT_DIR, 'educore', 'urls.py'),  # Your specific project
            os.path.join(PROJECT_DIR, 'config', 'urls.py'),
            os.path.join(PROJECT_DIR, 'core', 'urls.py'),     # Common Django structure
        ]

        # Check for urls.py in project directories
        for location in potential_locations:
            if os.path.exists(location):
                urls_file = location
                break

        # If not found, look in all directories
        if not urls_file:
            for item in os.listdir(PROJECT_DIR):
                item_path = os.path.join(PROJECT_DIR, item)
                if os.path.isdir(item_path):
                    potential_urls = os.path.join(item_path, 'urls.py')
                    if os.path.exists(potential_urls):
                        urls_file = potential_urls
                        break

        if not urls_file:
            logger.warning("Could not find the project's main urls.py file. You'll need to manually include your app URLs.")
            return False

        logger.info(f"Found project URLs file: {normalize_path(urls_file)}")

        # Back up the file
        if BACKUP_EXISTING:
            backup_path = backup_file(urls_file)
            logger.info(f"Backed up project urls.py to {backup_path}")

        try:
            # Read the current content
            with open(urls_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if we need to add any imports or URL patterns
            needs_update = False
            new_imports = []
            new_patterns = []

            for app_info in app_infos:
                app_name = app_info['app_config'].name
                app_label = app_name.split('.')[-1]

                # Check if this app is already included
                import_pattern = f"from {app_label} import urls as {app_label}_urls"
                url_pattern = f"path('{API_PREFIX}{app_label}/', include("

                if import_pattern not in content and f"import {app_label}.urls" not in content:
                    new_imports.append(import_pattern)
                    needs_update = True

                if url_pattern not in content and f"path('{API_PREFIX}{app_label}/" not in content:
                    # Use proper tuple structure for include with namespace 
                    new_patterns.append(
                        f"    path('{API_PREFIX}{app_label}/', "
                        f"include(('{app_label}.urls', '{app_label}'), namespace='{app_label}')),"
                    )
                    needs_update = True

            if not needs_update:
                logger.info("Project URLs file already includes all app URLs.")
                return True

            logger.info("Updating project URLs file...")

            # Extract the existing content structure
            import_section_end = 0
            urlpatterns_start = 0
            urlpatterns_end = 0

            # Find the end of the import section (usually ends with a blank line)
            import_lines = re.findall(r'^(?:import|from)\s+.*$', content, re.MULTILINE)
            if import_lines:
                last_import = import_lines[-1]
                import_section_end = content.find(last_import) + len(last_import)

            # Find the urlpatterns section
            urlpatterns_match = re.search(r'urlpatterns\s*=\s*\[(.*?)\]', content, re.DOTALL)
            if urlpatterns_match:
                urlpatterns_start = urlpatterns_match.start()
                urlpatterns_end = urlpatterns_match.end()

            if import_section_end > 0 and urlpatterns_start > 0:
                # Insert new imports after the last import
                if new_imports:
                    modified_content = content[:import_section_end] + '\n' + '\n'.join(new_imports) + content[import_section_end:]
                    # Update positions after insertion
                    urlpatterns_start += len('\n' + '\n'.join(new_imports))
                    urlpatterns_end += len('\n' + '\n'.join(new_imports))
                    content = modified_content

                # Insert new URL patterns before the closing bracket of urlpatterns
                if new_patterns:
                    closing_bracket_pos = content.rfind(']', urlpatterns_start, urlpatterns_end)
                    if closing_bracket_pos > 0:
                        pattern_text = '\n' + '\n'.join(new_patterns)
                        modified_content = content[:closing_bracket_pos] + pattern_text + content[closing_bracket_pos:]
                        content = modified_content

                # Write the updated file
                with open(urls_file, 'w', encoding='utf-8') as f:
                    f.write(content)

                logger.info(f"Successfully updated project URLs file with {len(new_patterns)} new URL patterns.")
                return True
            else:
                logger.warning("Could not properly identify import section or urlpatterns in the project's URLs file.")
                logger.warning("You'll need to manually add the following imports and URL patterns:")

                for imp in new_imports:
                    logger.warning(f"Import: {imp}")

                for pattern in new_patterns:
                    logger.warning(f"URL Pattern: {pattern}")

                return False

        except Exception as e:
            logger.error(f"Failed to update project URLs file: {str(e)}")
            traceback.print_exc()
            return False

class ReportGenerator:
    """
    Class to generate a report of all operations performed.
    """

    def __init__(self):
        """Initialize the ReportGenerator."""
        pass

    def generate_report(self, app_infos):
        """
        Generate a comprehensive report of all operations performed.

        Args:
            app_infos (dict): Dictionary mapping app names to app information

        Returns:
            str: Path to the report file
        """
        logger.info("Generating report...")

        report_file = os.path.join(PROJECT_DIR, "api_generator_report.txt")

        # Create the report content
        content = []

        # Add report header
        content.append("=" * 80)
        content.append("API GENERATOR REPORT")
        content.append("=" * 80)
        content.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append(f"Project Directory: {normalize_path(PROJECT_DIR)}")
        content.append(f"Generated by: nanthiniSanthanam")
        content.append("")

        # Add summary
        content.append("SUMMARY")
        content.append("-" * 80)
        content.append(f"Apps processed: {len(app_infos)}")
        content.append(f"Files generated: {len(generated_files)}")
        content.append(f"Models processed: {len(processed_models)}")
        content.append(f"Warnings: {len(warnings)}")
        content.append(f"Errors: {len(errors)}")
        content.append("")

        # Add details for each app
        content.append("APP DETAILS")
        content.append("-" * 80)

        for app_name, app_info in app_infos.items():
            app_label = app_name.split('.')[-1]
            models = app_info['models']

            content.append(f"App: {app_label}")
            content.append(f"  Directory: {normalize_path(app_info['app_dir'])}")
            content.append(f"  Models: {len(models)}")
            content.append(f"  Models file: {normalize_path(app_info['models_file'])}")
            content.append("")

        # Add generated files
        content.append("GENERATED FILES")
        content.append("-" * 80)

        for file_path in generated_files:
            content.append(f"- {normalize_path(file_path)}")

        content.append("")

        # Add warnings
        if warnings:
            content.append("WARNINGS")
            content.append("-" * 80)

            for warning in warnings:
                content.append(f"- {warning}")

            content.append("")

        # Add errors
        if errors:
            content.append("ERRORS")
            content.append("-" * 80)

            for error in errors:
                content.append(f"- {error}")

            content.append("")

        # Add next steps
        content.append("NEXT STEPS")
        content.append("-" * 80)
        content.append("1. Review the generated files to ensure they meet your requirements")
        content.append("2. Run migrations if you've made changes to your models")
        content.append("3. Test your API endpoints using a tool like Postman or the Django REST Framework browsable API")
        content.append("4. Update your frontend code to use the new API endpoints")
        content.append("5. Add additional custom logic to your views as needed")
        content.append("")

        # Add API endpoints
        content.append("API ENDPOINTS")
        content.append("-" * 80)

        for app_name, app_info in app_infos.items():
            app_label = app_name.split('.')[-1]
            model_infos = app_info.get('model_infos', [])

            content.append(f"App: {app_label}")

            for model_info in model_infos:
                model_name = model_info['name']
                url_name_plural = get_model_plural_name(model_info)

                content.append(f"  Model: {model_name}")
                content.append(f"    - List/Create: GET/POST /{API_PREFIX}{app_label}/{url_name_plural}/")
                content.append(f"    - Retrieve/Update/Delete: GET/PUT/PATCH/DELETE /{API_PREFIX}{app_label}/{url_name_plural}/{{id}}/")

                # Add custom actions
                if model_name == 'Course':
                    content.append(f"    - List modules: GET /{API_PREFIX}{app_label}/{url_name_plural}/{{id}}/modules/")
                    content.append(f"    - Enroll: POST /{API_PREFIX}{app_label}/{url_name_plural}/{{id}}/enroll/")
                    content.append(f"    - List/Create reviews: GET/POST /{API_PREFIX}{app_label}/{url_name_plural}/{{id}}/reviews/")
                elif model_name == 'Module':
                    content.append(f"    - List lessons: GET /{API_PREFIX}{app_label}/{url_name_plural}/{{id}}/lessons/")
                elif model_name == 'Lesson':
                    content.append(f"    - Complete lesson: POST /{API_PREFIX}{app_label}/{url_name_plural}/{{id}}/complete/")
                    content.append(f"    - List resources: GET /{API_PREFIX}{app_label}/{url_name_plural}/{{id}}/resources/")
                elif model_name == 'Assessment':
                    content.append(f"    - Start assessment: POST /{API_PREFIX}{app_label}/{url_name_plural}/{{id}}/start/")
                    content.append(f"    - Submit assessment: POST /{API_PREFIX}{app_label}/{url_name_plural}/{{id}}/submit/")

            content.append("")

        # Write the report
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))

            logger.info(f"Report generated successfully: {report_file}")
            return report_file
        except Exception as e:
            logger.error(f"Failed to write report: {str(e)}")
            return None

def setup_django_environment():
    """
    Set up the Django environment.

    Returns:
        tuple: (success, apps) where success is a boolean indicating success and apps is the Django apps registry
    """
    logger.info("Setting up Django environment...")

    args = parse_args()

    # Update global config based on args
    global APPS_TO_PROCESS, BACKUP_EXISTING, MAX_BACKUPS, PROJECT_DIR
    if args.apps:
        APPS_TO_PROCESS = args.apps
    if args.no_backup:
        BACKUP_EXISTING = False
    if args.max_backups is not None:
        MAX_BACKUPS = args.max_backups
    if args.project_dir:
        PROJECT_DIR = args.project_dir

    sys.path.insert(0, PROJECT_DIR)

    # Try to find the settings module
    settings_module = args.settings

    if not settings_module:
        # First look for settings.py in common locations
        settings_locations = [
            os.path.join(PROJECT_DIR, 'settings.py'),
            os.path.join(PROJECT_DIR, 'educore', 'settings.py'),
            os.path.join(PROJECT_DIR, 'config', 'settings.py'),
            os.path.join(PROJECT_DIR, 'core', 'settings.py'),
            # Add more common locations here
        ]

        # Then try to find a settings module in named apps
        for directory in [d for d in os.listdir(PROJECT_DIR) if os.path.isdir(os.path.join(PROJECT_DIR, d))]:
            settings_locations.append(os.path.join(PROJECT_DIR, directory, 'settings.py'))

        # Find first valid settings file
        for location in settings_locations:
            if os.path.exists(location):
                # Extract the module name from path
                rel_path = os.path.relpath(location, PROJECT_DIR)
                module_path = rel_path.replace(os.path.sep, '.').replace('.py', '')
                settings_module = module_path
                break

    # If still not found and we have a TTY, ask the user
    if not settings_module and sys.stdout.isatty():
        logger.info("\nCould not automatically find your Django settings module.")
        settings_input = input("Please enter the name of your settings module (e.g., 'core.settings'): ")
        settings_module = settings_input.strip()
    elif not settings_module:
        logger.error("Could not find Django settings module and running in non-interactive mode. Please specify with --settings.")
        return False, None

    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
    logger.info(f"Using settings module: {settings_module}")

    try:
        import django
        django.setup()
        from django.apps import apps
        logger.info(f"Django {django.get_version()} initialized successfully.")
        return True, apps
    except ImportError as e:
        logger.error(f"Django is not installed or not found: {str(e)}")
        return False, None
    except Exception as e:
        logger.error(f"Failed to initialize Django: {str(e)}")
        traceback.print_exc()
        return False, None

def main():
    """
    Main function to run the API generator.

    This function:
    1. Initializes the environment
    2. Finds apps with models
    3. Analyzes each model
    4. Generates serializers.py, views.py and urls.py files
    5. Updates main project URLs
    6. Generates a detailed report

    Returns:
        int: 0 on success, 1 on error
    """
    logger.info("=" * 80)
    logger.info("DJANGO API GENERATOR FOR EDUCATIONAL PLATFORM")
    logger.info("=" * 80)
    logger.info("This script generates serializers.py, views.py, and urls.py files")
    logger.info("from your Django models.py files.")
    logger.info("")

    # Display the current date/time in the format requested
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Execution time: {current_time}")

    # Parse command-line arguments
    args = parse_args()

    # Set up Django environment
    success, django_apps = setup_django_environment()
    if not success:
        logger.error("Failed to set up Django environment. Exiting.")
        return 1

    # Initialize the model inspector
    model_inspector = ModelInspector(django_apps)

    # Find apps with models
    app_infos = model_inspector.find_apps_with_models()
    if not app_infos:
        logger.error("No Django apps with models found. Exiting.")
        return 1

    # If APPS_TO_PROCESS is not specified, and not using --all-apps, ask the user which apps to process
    if not APPS_TO_PROCESS and not args.all_apps and sys.stdout.isatty():
        logger.info("\nFound the following apps with models:")

        for i, (app_name, app_info) in enumerate(app_infos.items(), 1):
            model_count = len(app_info['models'])
            logger.info(f"  {i}. {app_name} ({model_count} model{'s' if model_count != 1 else ''})")

        process_all = input("\nProcess all apps? (y/n): ").lower() in ('y', 'yes')

        if not process_all:
            app_indices = input("Enter the numbers of the apps to process (comma-separated): ")
            try:
                selected_indices = [int(idx.strip()) for idx in app_indices.split(',')]
                app_keys = list(app_infos.keys())
                selected_apps = {app_keys[i-1]: app_infos[app_keys[i-1]] for i in selected_indices if 1 <= i <= len(app_keys)}
                app_infos = selected_apps
            except ValueError:
                logger.warning("Invalid input. Processing all apps.")
    elif APPS_TO_PROCESS:
        # Filter app_infos to only include the specified apps
        app_infos = {name: info for name, info in app_infos.items() if name.split('.')[-1] in APPS_TO_PROCESS or name in APPS_TO_PROCESS}

    # Process each app
    for app_name, app_info in app_infos.items():
        logger.info(f"\nProcessing app: {app_name}")

        # Analyze models
        model_infos = model_inspector.analyze_app_models(app_info)
        if not model_infos:
            logger.warning(f"No models found for app {app_name}. Skipping.")
            continue

        app_info['model_infos'] = model_infos

        # Generate serializers
        serializer_generator = SerializerGenerator()
        serializer_file = serializer_generator.generate_serializers_file(app_info, model_infos)
        if serializer_file:
            logger.info(f"Generated serializers for {app_name}: {normalize_path(serializer_file)}")
        else:
            logger.error(f"Failed to generate serializers for {app_name}")

        # Generate views
        view_generator = ViewGenerator()
        view_file = view_generator.generate_views_file(app_info, model_infos)
        if view_file:
            logger.info(f"Generated views for {app_name}: {normalize_path(view_file)}")
        else:
            logger.error(f"Failed to generate views for {app_name}")

        # Generate URLs
        url_generator = UrlGenerator()
        url_file = url_generator.generate_urls_file(app_info, model_infos)
        if url_file:
            logger.info(f"Generated URLs for {app_name}: {normalize_path(url_file)}")
        else:
            logger.error(f"Failed to generate URLs for {app_name}")

    # Update project URLs
    url_updater = MainURLUpdater()
    url_updater.update_project_urls(app_infos.values())

    # Generate report
    report_generator = ReportGenerator()
    report_file = report_generator.generate_report(app_infos)

    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Apps processed: {len(app_infos)}")
    logger.info(f"Files generated: {len(generated_files)}")
    logger.info(f"Models processed: {len(processed_models)}")
    logger.info(f"Warnings: {len(warnings)}")
    logger.info(f"Errors: {len(errors)}")

    if report_file:
        logger.info(f"\nDetailed report: {normalize_path(report_file)}")

    if errors:
        logger.info("\nERRORS ENCOUNTERED:")
        for error in errors:
            logger.info(f"- {error}")
        logger.info("\nPlease review the errors and fix any issues before using the generated code.")

    logger.info("\nAPI generation complete!")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)        








