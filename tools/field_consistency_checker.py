#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# fmt: off
# isort: skip_file

r"""
File: C:\Users\Santhanam\OneDrive\Personal\Full stack web development\eduplatform\tools\field_consistency_checker.py

Purpose:
    This script checks for consistency between Django backend models/serializers and React frontend form fields.
    It identifies mismatches, missing fields, and ensures your frontend forms properly align with your backend data models.
    
Features:
    1. Direct Django model introspection (no regex parsing of reports)
    2. JavaScript/React code parsing for accurate frontend field detection
    3. Intelligent name matching (handles camelCase vs snake_case conventions)
    4. Support for frontend-only fields through whitelisting
    5. Detects fields in various React component styles (functional, class, arrow functions)
    6. Analyzes API calls to match request bodies with form fields
    7. Performance optimization with caching and concurrency
    8. Flexible configuration through YAML settings file
    9. Comprehensive HTML report generation
    10. Non-interactive mode for CI/CD pipelines

Variables to modify:
    DJANGO_PROJECT_ROOT: Root directory of your Django project
        (default: C:\Users\Santhanam\OneDrive\Personal\Full stack web development\eduplatform\backend)
    FRONTEND_ROOT: Root directory of your React frontend
        (default: C:\Users\Santhanam\OneDrive\Personal\Full stack web development\eduplatform\frontend)
    CONFIG_FILE: Path to configuration file (created if it doesn't exist)
        (default: C:\Users\Santhanam\OneDrive\Personal\Full stack web development\eduplatform\tools\field_checker_config.yaml)
    REPORT_FILE: Path for HTML report output
        (default: C:\Users\Santhanam\OneDrive\Personal\Full stack web development\eduplatform\tools\field_consistency_report.html)
    
Requirements:
    - Python 3.6+
    - Django project with models
    - React/JavaScript frontend with forms
    - Required Python packages:
        - django
        - pyyaml
        - chardet (for better file encoding detection)
        - colorama (for terminal colors)
        - jinja2 (for report generation)

How to use:
    1. Place this script in your project's tools directory
    2. Install required packages: pip install django pyyaml colorama jinja2 chardet
    3. Run the script: python field_consistency_checker.py
    4. Review the generated HTML report for field mismatches
    5. Update your configuration file to whitelist intentional mismatches
    
    Advanced usage:
    - Run non-interactively: python field_consistency_checker.py --non-interactive
    - Specify config file: python field_consistency_checker.py --config custom_config.yaml
    - Output JSON: python field_consistency_checker.py --format json --output results.json
    - Check specific app: python field_consistency_checker.py --apps courses,users
    - Verbose logging: python field_consistency_checker.py --verbose

Changes from original version:
    - Fixed JavaScript parser dependency (removed babel dependency)
    - Implemented proper --apps flag functionality
    - Fixed backend-only field detection logic
    - Corrected field count statistics
    - Normalized path handling for cross-platform compatibility
    - Improved thread safety for logging
    - Enhanced serializer introspection
    - Added better file encoding detection with chardet
    - Improved error handling and reporting
    - Fixed duplicate field resolution with proper confidence comparison
    - Added expanded whitelist handling for both camelCase and snake_case variants
    - Improved settings module discovery for various Django project layouts
    - Added proper Jinja2 template filter handling for compatibility
    - Fixed serializer field template checks
    - Applied confidence level CSS classes in reports
    - Implemented better ID sanitization for HTML elements
    - Added smarter exit code threshold calculation

Created by: Professor Santhanam
Last updated: 2025-04-28 15:37:44
"""

# Import logging and set up queue before any other imports
import logging
import queue
from logging.handlers import QueueHandler, QueueListener
import sys

# Create a queue for log messages (thread-safe logging)
log_queue = queue.Queue(-1)  # No limit on size

# Setup logging with queue handler
queue_handler = QueueHandler(log_queue)
logging.basicConfig(
    level=logging.INFO,
    handlers=[queue_handler],
    force=True  # Force reconfiguration of existing loggers
)
logger = logging.getLogger(__name__)

# Standard library imports
import os
import re
import json
import yaml
import argparse
import datetime
import concurrent.futures
import traceback
import copy
import importlib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Union, Any

# Start queue listener with actual output handlers
try:
    # Try to use concurrent handler if available for better thread safety
    from concurrent_log_handler import ConcurrentRotatingFileHandler
    file_handler = ConcurrentRotatingFileHandler("field_checker.log", maxBytes=10*1024*1024, backupCount=5)
except ImportError:
    # Fall back to regular file handler with delay
    file_handler = logging.FileHandler("field_checker.log", delay=True)

console_handler = logging.StreamHandler()
listener = QueueListener(log_queue, file_handler, console_handler)
listener.start()

# ------------------------------------------------------------------------------
# CONFIGURATION SECTION - MODIFY THESE SETTINGS AS NEEDED
# ------------------------------------------------------------------------------

# Base directory of your Django project
DJANGO_PROJECT_ROOT = r"C:\Users\Santhanam\OneDrive\Personal\Full stack web development\eduplatform\backend"

# Base directory of your React frontend
FRONTEND_ROOT = r"C:\Users\Santhanam\OneDrive\Personal\Full stack web development\eduplatform\frontend"

# Path to configuration file
CONFIG_FILE = r"C:\Users\Santhanam\OneDrive\Personal\Full stack web development\eduplatform\tools\field_checker_config.yaml"

# Path for HTML report output
REPORT_FILE = r"C:\Users\Santhanam\OneDrive\Personal\Full stack web development\eduplatform\tools\field_consistency_report.html"

# Default configuration
DEFAULT_CONFIG = {
    'frontend': {
        'ignore_folders': ['node_modules', 'dist', 'build', '.git', '__tests__', '__mocks__'],
        'file_extensions': ['.js', '.jsx', '.ts', '.tsx'],
        'whitelist_fields': [
            'confirmPassword',
            'passwordConfirm',
            'rememberMe',
            'agreeToTerms',
            'isSubmitting',
            'currentPassword',
            'newPassword'
        ]
    },
    'backend': {
        'ignore_apps': ['auth', 'contenttypes', 'sessions', 'admin', 'messages'],
        'serializer_suffix': 'Serializer'
    },
    'field_mapping': {
        'rules': [
            {'frontend': 'camelCase', 'backend': 'snake_case', 'enabled': True}
        ],
        'custom_mappings': {}
    }
}

# ------------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ------------------------------------------------------------------------------

def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensure that a directory exists, creating it if necessary.

    Args:
        directory_path: The path to the directory
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create directory {directory_path}: {str(e)}")
        sys.exit(1)

def deep_update(source, updates):
    """
    Update a nested dictionary or similar mapping.
    Modifies source in place.

    Args:
        source: The dictionary to update
        updates: The dictionary with updates

    Returns:
        dict: The updated source dictionary
    """
    for key, value in updates.items():
        if isinstance(value, dict) and key in source and isinstance(source[key], dict):
            deep_update(source[key], value)
        else:
            source[key] = value
    return source

def load_or_create_config() -> dict:
    """
    Load configuration from file or create a default one if it doesn't exist.

    Returns:
        dict: The configuration dictionary
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {CONFIG_FILE}")

                # Create a deep copy of the default config
                result_config = copy.deepcopy(DEFAULT_CONFIG)
                # Merge with loaded config (preserving defaults for missing keys)
                deep_update(result_config, config)

                # Expand whitelist to include both camelCase and snake_case variants
                result_config['frontend']['whitelist_fields'] = list(
                    expand_whitelist(result_config['frontend']['whitelist_fields'])
                )

                return result_config
        except Exception as e:
            logger.error(f"Failed to load configuration file: {str(e)}")
            logger.info("Using default configuration")
            default_config = copy.deepcopy(DEFAULT_CONFIG)
            default_config['frontend']['whitelist_fields'] = list(
                expand_whitelist(default_config['frontend']['whitelist_fields'])
            )
            return default_config
    else:
        # Create a new configuration file with defaults
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False)
            logger.info(f"Created new configuration file at {CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Failed to create configuration file: {str(e)}")

        default_config = copy.deepcopy(DEFAULT_CONFIG)
        default_config['frontend']['whitelist_fields'] = list(
            expand_whitelist(default_config['frontend']['whitelist_fields'])
        )
        return default_config

def snake_to_camel(snake_str: str) -> str:
    """
    Convert a snake_case string to camelCase.

    Args:
        snake_str: The snake_case string

    Returns:
        str: The camelCase version of the input string
    """
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def camel_to_snake(camel_str: str) -> str:
    """
    Convert a camelCase string to snake_case.

    Args:
        camel_str: The camelCase string

    Returns:
        str: The snake_case version of the input string
    """
    snake_str = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', snake_str).lower()

def expand_whitelist(whitelist: List[str]) -> Set[str]:
    """
    Expand whitelist to include both camelCase and snake_case variants.

    Args:
        whitelist: List of field names to whitelist

    Returns:
        set: Expanded set of field names
    """
    expanded = set()
    for field in whitelist:
        expanded.add(field)  # Original
        if '_' in field:  # snake_case
            expanded.add(snake_to_camel(field))
        else:  # Assume camelCase
            expanded.add(camel_to_snake(field))
    return expanded

def detect_file_encoding(file_path: str) -> str:
    """
    Attempt to detect the encoding of a file using chardet if available,
    with fallback to manual detection.

    Args:
        file_path: Path to the file

    Returns:
        str: The detected encoding or 'utf-8' as fallback
    """
    try:
        # First try chardet for more efficient detection
        try:
            import chardet
            with open(file_path, 'rb') as f:
                sample = f.read(min(4096, os.path.getsize(file_path)))  # Read up to 4KB for efficiency
                if not sample:  # Empty file
                    return 'utf-8'
                result = chardet.detect(sample)
                encoding = result['encoding'] or 'utf-8'
                return encoding
        except ImportError:
            # If chardet not available, use fallback method
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        f.read(1024)  # Just read a bit to test encoding
                    return encoding
                except UnicodeDecodeError:
                    continue
    except Exception as e:
        logger.debug(f"Error detecting encoding for {file_path}: {e}")

    # If all else fails, default to utf-8 with error handling
    return 'utf-8'

def normalize_path(path: str) -> str:
    """
    Normalize a file path for cross-platform compatibility.

    Args:
        path: The path to normalize

    Returns:
        str: Normalized path
    """
    return str(Path(path).as_posix()).lower()

def sanitize_id(text: str) -> str:
    """
    Convert a string to a valid HTML id attribute value.

    Args:
        text: Input text

    Returns:
        str: Sanitized ID
    """
    return re.sub(r'[^A-Za-z0-9_-]', '-', text)

# ------------------------------------------------------------------------------
# DJANGO MODEL ANALYSIS
# ------------------------------------------------------------------------------

def setup_django_environment() -> bool:
    """
    Set up the Django environment to access models and other components.

    This function handles various Django project structures to find the settings module.

    Returns:
        bool: True if setup was successful, False otherwise
    """
    logger.info("Setting up Django environment...")

    # Add Django project root to Python path
    sys.path.insert(0, DJANGO_PROJECT_ROOT)

    # Also add parent directory to support absolute imports
    project_root = Path(DJANGO_PROJECT_ROOT).parent
    sys.path.insert(0, str(project_root))

    # Try to find the settings module
    settings_module = None

    # Look in common locations
    settings_locations = [
        # Direct settings module
        os.path.join(DJANGO_PROJECT_ROOT, 'settings.py'),
        # Common Django project structures
        os.path.join(DJANGO_PROJECT_ROOT, 'educore', 'settings.py'),
        os.path.join(DJANGO_PROJECT_ROOT, 'config', 'settings.py'),
        # Project-level settings
        os.path.join(str(project_root), 'settings.py'),
        os.path.join(str(project_root), 'config', 'settings.py')
    ]

    # Check for settings in subdirectories
    for directory in [d for d in os.listdir(DJANGO_PROJECT_ROOT) 
                     if os.path.isdir(os.path.join(DJANGO_PROJECT_ROOT, d))]:
        settings_locations.append(os.path.join(DJANGO_PROJECT_ROOT, directory, 'settings.py'))

    # Look for manage.py and extract settings module
    manage_py_locations = [
        os.path.join(DJANGO_PROJECT_ROOT, 'manage.py'),
        os.path.join(str(project_root), 'manage.py')
    ]

    for manage_path in manage_py_locations:
        if os.path.exists(manage_path):
            try:
                with open(manage_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    settings_match = re.search(r'DJANGO_SETTINGS_MODULE["\'],\s*["\']([^"\']+)', content)
                    if settings_match:
                        settings_module = settings_match.group(1)
                        logger.info(f"Found settings module '{settings_module}' from manage.py")
                        break
            except Exception as e:
                logger.debug(f"Couldn't extract settings from manage.py: {e}")

    # Find first valid settings file if not found in manage.py
    if not settings_module:
        for location in settings_locations:
            if os.path.exists(location):
                # Extract the module name from path
                if location.startswith(DJANGO_PROJECT_ROOT):
                    rel_path = os.path.relpath(location, DJANGO_PROJECT_ROOT)
                else:
                    rel_path = os.path.relpath(location, str(project_root))
                module_path = rel_path.replace(os.path.sep, '.').replace('.py', '')
                settings_module = module_path
                logger.info(f"Found settings module from path: {settings_module}")
                break

    # If still not found, ask the user
    if not settings_module:
        logger.warning("\nCould not automatically find your Django settings module.")
        settings_input = input("Please enter the name of your settings module (e.g., 'educore.settings'): ")
        settings_module = settings_input.strip()

    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
    logger.info(f"Using Django settings module: {settings_module}")

    try:
        import django
        django.setup()
        logger.info(f"Django {django.get_version()} initialized successfully.")
        return True
    except ImportError:
        logger.error("Django is not installed. Please install Django first.")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Django: {str(e)}")
        traceback.print_exc()
        return False

def get_all_models(config: dict) -> Dict[str, Dict[str, Any]]:
    """
    Get all Django models and their fields.

    Args:
        config: The configuration dictionary

    Returns:
        dict: A dictionary mapping app labels to their models
    """
    logger.info("Analyzing Django models...")

    try:
        from django.apps import apps
        from django.db.models.fields.related import ForeignKey, OneToOneField, ManyToManyField

        # Dictionary to hold models by app
        app_models = {}

        # Ignore these apps
        ignore_apps = config['backend']['ignore_apps']

        # Get apps to include if specified
        include_apps = config['backend'].get('include_apps', [])

        # Process all installed apps
        for app_config in apps.get_app_configs():
            app_label = app_config.label

            # Skip ignored apps
            if app_label in ignore_apps:
                continue

            # Skip apps not in the include list (if specified)
            if include_apps and app_label not in include_apps:
                logger.debug(f"Skipping app '{app_label}' as it's not in the specified include list")
                continue

            # Initialize app entry
            if app_label not in app_models:
                app_models[app_label] = {'models': {}}

            # Get all models for this app
            for model in app_config.get_models():
                model_name = model.__name__

                # Initialize model entry
                if model_name not in app_models[app_label]['models']:
                    app_models[app_label]['models'][model_name] = {
                        'fields': {},
                        'related_fields': {},
                        'has_serializer': False,
                        'serializer_fields': {}
                    }

                # Add fields
                for field in model._meta.get_fields():
                    field_name = field.name

                    # Skip internal fields
                    if field_name.startswith('_'):
                        continue

                    if isinstance(field, (ForeignKey, OneToOneField, ManyToManyField)):
                        app_models[app_label]['models'][model_name]['related_fields'][field_name] = {
                            'field_type': field.__class__.__name__,
                            'related_model': field.related_model.__name__ if hasattr(field, 'related_model') else None
                        }
                    else:
                        app_models[app_label]['models'][model_name]['fields'][field_name] = {
                            'field_type': field.__class__.__name__
                        }

        logger.info(f"Found {sum(len(app['models']) for app in app_models.values())} models across {len(app_models)} apps")
        return app_models

    except Exception as e:
        logger.error(f"Failed to analyze Django models: {str(e)}")
        traceback.print_exc()
        return {}

def analyze_serializers(app_models: Dict[str, Dict[str, Any]], config: dict) -> Dict[str, Dict[str, Any]]:
    """
    Analyze serializer classes to identify field transformations and mappings.
    First tries runtime import of serializers, falls back to AST parsing if that fails.

    Args:
        app_models: Dictionary of app models
        config: The configuration dictionary

    Returns:
        dict: Updated app_models with serializer information
    """
    logger.info("Analyzing Django serializers...")

    serializer_suffix = config['backend']['serializer_suffix']

    # First try runtime analysis of serializers
    try:
        return analyze_serializers_runtime(app_models, config)
    except Exception as e:
        logger.warning(f"Runtime serializer analysis failed: {e}")
        logger.info("Falling back to AST parsing for serializers")
        return analyze_serializers_ast(app_models, config)

def analyze_serializers_runtime(app_models: Dict[str, Dict[str, Any]], config: dict) -> Dict[str, Dict[str, Any]]:
    """
    Analyze serializer classes at runtime by importing them.
    This is more accurate than AST parsing.

    Args:
        app_models: Dictionary of app models
        config: The configuration dictionary

    Returns:
        dict: Updated app_models with serializer information
    """
    from django.apps import apps

    serializer_suffix = config['backend']['serializer_suffix']

    for app_label in list(app_models.keys()):
        # Try to import the serializers module
        serializers_module = None

        # Get the app configuration to determine the correct module path
        try:
            app_config = apps.get_app_config(app_label)
            # Derive the base module from the app config
            base_module = app_config.module.__name__.rsplit('.', 1)[0]
            serializer_module_name = f"{base_module}.serializers"
            try:
                serializers_module = importlib.import_module(serializer_module_name)
                logger.debug(f"Successfully imported serializers from {serializer_module_name}")
            except ImportError:
                # Try with just the app name
                try:
                    serializers_module = importlib.import_module(f"{app_label}.serializers")
                    logger.debug(f"Successfully imported serializers from {app_label}.serializers")
                except ImportError:
                    # Try one more alternative
                    try:
                        module_path = f"{Path(DJANGO_PROJECT_ROOT).name}.{app_label}.serializers"
                        serializers_module = importlib.import_module(module_path)
                        logger.debug(f"Successfully imported serializers from {module_path}")
                    except ImportError:
                        logger.debug(f"No serializers module found for app {app_label}")
                        continue
        except Exception as e:
            logger.debug(f"Error finding app configuration for {app_label}: {e}")
            continue

        if not serializers_module:
            continue

        # Find all classes that end with the serializer suffix
        for attr_name in dir(serializers_module):
            if not attr_name.endswith(serializer_suffix):
                continue

            try:
                # Get the serializer class
                serializer_class = getattr(serializers_module, attr_name)
                if not callable(serializer_class):
                    continue

                # Extract model name from serializer name
                model_name = attr_name[:-len(serializer_suffix)]

                # Find the model in app_models
                model_found = False
                for app_models_data in app_models.values():
                    if model_name in app_models_data['models']:
                        model_data = app_models_data['models'][model_name]
                        model_found = True
                        model_data['has_serializer'] = True

                        # Try to analyze the serializer fields
                        try:
                            # Try to instantiate the serializer
                            serializer_instance = serializer_class()

                            # Get Meta fields if available
                            meta = getattr(serializer_class, 'Meta', None)
                            meta_fields = None

                            if meta:
                                # Check for fields in Meta
                                if hasattr(meta, 'fields'):
                                    meta_fields = getattr(meta, 'fields')

                                    # Handle fields = '__all__' case
                                    if meta_fields == '__all__':
                                        # Use all model fields
                                        meta_fields = list(model_data['fields'].keys()) + list(model_data['related_fields'].keys())

                                    # Add all meta fields
                                    for field_name in meta_fields:
                                        if field_name != 'id':  # Skip id field as it's often implicit
                                            model_data['serializer_fields'][field_name] = {
                                                'source': field_name
                                            }

                                # Check for exclude in Meta
                                elif hasattr(meta, 'exclude'):
                                    exclude_fields = getattr(meta, 'exclude')
                                    all_fields = list(model_data['fields'].keys()) + list(model_data['related_fields'].keys())

                                    # Add non-excluded fields
                                    for field_name in all_fields:
                                        if field_name not in exclude_fields and field_name != 'id':
                                            model_data['serializer_fields'][field_name] = {
                                                'source': field_name
                                            }

                            # Also look for explicitly declared fields
                            for field_name in dir(serializer_class):
                                if field_name.startswith('_') or callable(getattr(serializer_class, field_name)):
                                    continue

                                field_obj = getattr(serializer_class, field_name)
                                source = getattr(field_obj, 'source', field_name) if hasattr(field_obj, 'source') else field_name

                                model_data['serializer_fields'][field_name] = {
                                    'source': source,
                                    'is_custom': True
                                }

                        except Exception as e:
                            logger.warning(f"Could not analyze serializer {attr_name}: {e}")
                            # If we couldn't analyze the serializer, assume it includes all model fields
                            for field_name in list(model_data['fields'].keys()) + list(model_data['related_fields'].keys()):
                                if field_name != 'id':
                                    model_data['serializer_fields'][field_name] = {
                                        'source': field_name
                                    }

                if not model_found:
                    logger.debug(f"No matching model found for serializer '{attr_name}'")

            except Exception as e:
                logger.warning(f"Error analyzing serializer {attr_name}: {e}")

    return app_models

def analyze_serializers_ast(app_models: Dict[str, Dict[str, Any]], config: dict) -> Dict[str, Dict[str, Any]]:
    """
    Analyze serializer classes using AST parsing.
    This is a fallback when runtime import fails.

    Args:
        app_models: Dictionary of app models
        config: The configuration dictionary

    Returns:
        dict: Updated app_models with serializer information
    """
    import ast

    serializer_suffix = config['backend']['serializer_suffix']

    # Find all serializer modules
    for app_label, app_data in app_models.items():
        serializers_file = None

        # Look for serializers.py in the app directory
        app_paths = [
            os.path.join(DJANGO_PROJECT_ROOT, app_label),
            os.path.join(DJANGO_PROJECT_ROOT, app_label.replace('.', os.path.sep))
        ]

        for app_path in app_paths:
            potential_file = os.path.join(app_path, 'serializers.py')
            if os.path.exists(potential_file):
                serializers_file = potential_file
                break

        if not serializers_file:
            logger.debug(f"No serializers.py found for app '{app_label}'")
            continue

        # Parse the serializers file using AST
        encoding = detect_file_encoding(serializers_file)
        try:
            with open(serializers_file, 'r', encoding=encoding) as f:
                file_content = f.read()
        except Exception as e:
            logger.warning(f"Could not read serializers file {serializers_file}: {e}")
            continue

        # Parse the file
        try:
            tree = ast.parse(file_content)
        except Exception as e:
            logger.warning(f"Could not parse serializers file {serializers_file}: {e}")
            continue

        # Find all serializer classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.endswith(serializer_suffix):
                # Extract the model name from the serializer name
                model_name = node.name[:-len(serializer_suffix)]

                # Find the model
                model_found = False
                for app_models_data in app_models.values():
                    if model_name in app_models_data['models']:
                        model_data = app_models_data['models'][model_name]
                        model_data['has_serializer'] = True
                        model_found = True

                        # Extract serializer fields
                        meta_class = None
                        for class_node in node.body:
                            if isinstance(class_node, ast.ClassDef) and class_node.name == 'Meta':
                                meta_class = class_node
                                break

                        if meta_class:
                            # Try to find fields list in Meta class
                            for meta_node in meta_class.body:
                                if isinstance(meta_node, ast.Assign):
                                    for target in meta_node.targets:
                                        if isinstance(target, ast.Name):
                                            # Handle fields attribute
                                            if target.id == 'fields':
                                                # Fields can be a list or string '__all__'
                                                if isinstance(meta_node.value, ast.List):
                                                    for elt in meta_node.value.elts:
                                                        if isinstance(elt, ast.Str):
                                                            field_name = elt.s
                                                            model_data['serializer_fields'][field_name] = {
                                                                'source': field_name
                                                            }
                                                elif isinstance(meta_node.value, ast.Str) and meta_node.value.s == '__all__':
                                                    # Add all model fields
                                                    for field_name in list(model_data['fields'].keys()) + list(model_data['related_fields'].keys()):
                                                        model_data['serializer_fields'][field_name] = {
                                                            'source': field_name
                                                        }

                                            # Handle exclude attribute
                                            elif target.id == 'exclude':
                                                if isinstance(meta_node.value, ast.List):
                                                    exclude_fields = []
                                                    for elt in meta_node.value.elts:
                                                        if isinstance(elt, ast.Str):
                                                            exclude_fields.append(elt.s)

                                                    # Add all non-excluded model fields
                                                    all_fields = list(model_data['fields'].keys()) + list(model_data['related_fields'].keys())
                                                    for field_name in all_fields:
                                                        if field_name not in exclude_fields:
                                                            model_data['serializer_fields'][field_name] = {
                                                                'source': field_name
                                                            }

                        # Look for additional fields or custom field attributes
                        for class_item in node.body:
                            if isinstance(class_item, ast.Assign):
                                for target in class_item.targets:
                                    if isinstance(target, ast.Name):
                                        field_name = target.id

                                        # Skip if it's not a field
                                        if field_name.startswith('_') or field_name in ('Meta', 'media'):
                                            continue

                                        # This looks like a serializer field
                                        if isinstance(class_item.value, ast.Call):
                                            model_data['serializer_fields'][field_name] = {
                                                'is_serializer_field': True,
                                                'source': field_name  # Default source
                                            }

                                            # Look for source attribute
                                            for keyword in class_item.value.keywords:
                                                if keyword.arg == 'source' and isinstance(keyword.value, ast.Str):
                                                    model_data['serializer_fields'][field_name]['source'] = keyword.value.s

                        # If no explicit fields were found, assume all model fields are included
                        if not model_data['serializer_fields']:
                            for field_name in list(model_data['fields'].keys()) + list(model_data['related_fields'].keys()):
                                model_data['serializer_fields'][field_name] = {
                                    'source': field_name
                                }

                if not model_found:
                    logger.debug(f"Serializer '{node.name}' found but no matching model '{model_name}' exists")

    logger.info("Serializer analysis completed")
    return app_models

# ------------------------------------------------------------------------------
# JAVASCRIPT / REACT FRONTEND ANALYSIS
# ------------------------------------------------------------------------------

def find_frontend_files(config: dict) -> List[str]:
    """
    Find all JavaScript/TypeScript files in the frontend directory.

    Args:
        config: The configuration dictionary

    Returns:
        list: List of file paths
    """
    logger.info("Finding frontend files...")

    frontend_files = []
    ignore_folders = config['frontend']['ignore_folders']
    file_extensions = config['frontend']['file_extensions']

    for root, dirs, files in os.walk(FRONTEND_ROOT):
        # Skip ignored folders
        dirs[:] = [d for d in dirs if d not in ignore_folders]

        for file in files:
            if any(file.endswith(ext) for ext in file_extensions):
                file_path = os.path.join(root, file)
                frontend_files.append(file_path)

    logger.info(f"Found {len(frontend_files)} frontend files to analyze")
    return frontend_files

def confidence_level(confidence: str) -> int:
    """
    Convert confidence string to numeric value for comparison.

    Args:
        confidence: Confidence level string

    Returns:
        int: Numeric confidence level
    """
    levels = {"high": 3, "medium": 2, "low": 1}
    return levels.get(confidence.lower(), 0)

def parse_js_file(file_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Parse a JavaScript file to extract form fields and API calls.
    This version doesn't rely on babel but uses regex patterns with confidence levels.

    Args:
        file_path: Path to the JavaScript file

    Returns:
        tuple: (form_fields, api_fields) lists of field dictionaries with confidence levels
    """
    try:
        # Detect file encoding
        encoding = detect_file_encoding(file_path)

        # Read the file
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()

        # Define patterns with confidence levels
        form_field_patterns = [
            # High confidence patterns (direct field definitions)
            (r'<(?:input|select|textarea)[^>]*name=[\'"]([^\'"]+)[\'"]', "high"),
            (r'(?:register|useField)\([\'"]([^\'"]+)[\'"]', "high"),
            (r'<Field[^>]*name=[\'"]([^\'"]+)[\'"]', "high"),
            (r'formData\.append\([\'"]([^\'"]+)[\'"]', "high"),

            # Medium confidence patterns (likely fields but could have false positives)
            (r'onChange=\{[^}]*set([A-Z][a-zA-Z0-9]*)[\},]', "medium"),
            (r'const\s+\{([^}]+)\}\s*=\s*(?:values|formData|form)', "medium"),

            # Low confidence patterns (might be display-only)
            (r'value=\{([^.}\[]+)\}', "low")
        ]

        # API call patterns
        api_call_patterns = [
            # High confidence API patterns
            (r'axios\.(?:post|put|patch)\([^,]+,\s*\{([^}]+)\}', "high"),
            (r'fetch\([^,]+,\s*\{[^}]*body:\s*JSON\.stringify\(\{([^}]+)\}\)', "high"),

            # Medium confidence API patterns
            (r'(?:axios|fetch)[^;]+(?:formData|form)[^;]+\)', "medium")
        ]

        # Extract form fields with confidence levels
        form_fields = []
        for pattern, confidence in form_field_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    # If the regex capture group returned multiple groups
                    for m in match:
                        if m.strip():
                            field_info = {
                                'name': m.strip(),
                                'confidence': confidence,
                                'pattern': pattern
                            }
                            form_fields.append(field_info)
                elif ',' in match:
                    # Handle destructured objects
                    parts = [p.strip() for p in match.split(',')]
                    for part in parts:
                        if part:
                            field_info = {
                                'name': part,
                                'confidence': confidence,
                                'pattern': pattern
                            }
                            form_fields.append(field_info)
                else:
                    field_info = {
                        'name': match.strip(),
                        'confidence': confidence,
                        'pattern': pattern
                    }
                    form_fields.append(field_info)

        # Extract API call fields with confidence levels
        api_fields = []
        for pattern, confidence in api_call_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, str) and match:
                    # Extract object properties from {...} contents
                    properties = re.findall(r'([a-zA-Z0-9_]+)(?::|\s*:)', match)
                    for prop in properties:
                        field_info = {
                            'name': prop,
                            'confidence': confidence,
                            'pattern': pattern
                        }
                        api_fields.append(field_info)

        # Clean up field names
        cleaned_form_fields = []
        for field in form_fields:
            name = field['name']
            # Skip React hook setters and event handlers
            if not name.startswith(('set', 'handle', 'on')) or field['confidence'] == "high":
                cleaned_form_fields.append(field)
            elif name.startswith('set') and len(name) > 3 and name[3].isupper():
                # It's likely a setter, extract the actual field name
                actual_name = name[3].lower() + name[4:]

                # Only add if we don't already have a high confidence match for this name
                existing_field = next((f for f in cleaned_form_fields if f['name'] == actual_name), None)
                if not existing_field or confidence_level(existing_field['confidence']) < confidence_level("medium"):
                    field['name'] = actual_name
                    field['confidence'] = "medium"
                    cleaned_form_fields.append(field)

        cleaned_api_fields = [f for f in api_fields if f['name'] not in ('headers', 'method', 'mode', 'credentials')]

        # Remove duplicates while preserving order and highest confidence
        unique_form_fields = {}
        for field in cleaned_form_fields:
            name = field['name']
            if (name not in unique_form_fields or 
                confidence_level(field['confidence']) > confidence_level(unique_form_fields[name]['confidence'])):
                unique_form_fields[name] = field

        unique_api_fields = {}
        for field in cleaned_api_fields:
            name = field['name']
            if (name not in unique_api_fields or 
                confidence_level(field['confidence']) > confidence_level(unique_api_fields[name]['confidence'])):
                unique_api_fields[name] = field

        return list(unique_form_fields.values()), list(unique_api_fields.values())

    except Exception as e:
        logger.error(f"Error parsing {file_path}: {str(e)}")
        return [], []

def analyze_frontend_files(files: List[str], config: dict) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    """
    Analyze frontend files to extract form fields and API calls.

    Args:
        files: List of frontend files to analyze
        config: The configuration dictionary

    Returns:
        dict: Dictionary mapping file paths to form fields and API calls
    """
    logger.info("Analyzing frontend files...")

    frontend_data = {}
    whitelist_fields = set(config['frontend']['whitelist_fields'])

    # Decide whether to use concurrency based on number of files
    use_threading = len(files) > 10 and sys.version_info >= (3, 8)  # More stable in Python 3.8+

    if use_threading:
        # Use concurrent execution to speed up parsing for many files
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit all parsing tasks
            future_to_file = {
                executor.submit(parse_js_file, file_path): file_path 
                for file_path in files
            }

            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_file):
                file_path = future_to_file[future]
                rel_path = Path(file_path).relative_to(Path(FRONTEND_ROOT)).as_posix()

                try:
                    form_fields, api_fields = future.result()

                    # Skip files with no fields
                    if not form_fields and not api_fields:
                        continue

                    # Filter out whitelisted fields
                    form_fields = [f for f in form_fields if f['name'] not in whitelist_fields]
                    api_fields = [f for f in api_fields if f['name'] not in whitelist_fields]

                    frontend_data[rel_path] = {
                        'form_fields': form_fields,
                        'api_fields': api_fields
                    }

                except Exception as e:
                    logger.error(f"Error processing {rel_path}: {str(e)}")
    else:
        # Process files serially for smaller projects or better debugging
        for file_path in files:
            rel_path = Path(file_path).relative_to(Path(FRONTEND_ROOT)).as_posix()

            try:
                form_fields, api_fields = parse_js_file(file_path)

                # Skip files with no fields
                if not form_fields and not api_fields:
                    continue

                # Filter out whitelisted fields
                form_fields = [f for f in form_fields if f['name'] not in whitelist_fields]
                api_fields = [f for f in api_fields if f['name'] not in whitelist_fields]

                frontend_data[rel_path] = {
                    'form_fields': form_fields,
                    'api_fields': api_fields
                }
            except Exception as e:
                logger.error(f"Error processing {rel_path}: {str(e)}")

    total_files = len(frontend_data)
    total_fields = sum(len(data['form_fields']) + len(data['api_fields']) for data in frontend_data.values())
    logger.info(f"Frontend analysis complete - found {total_fields} fields in {total_files} files")

    return frontend_data

# ------------------------------------------------------------------------------
# FIELD MATCHING AND CONSISTENCY CHECKING
# ------------------------------------------------------------------------------

def normalize_field_name(field_name: str, from_style: str, to_style: str) -> str:
    """
    Convert a field name between different naming conventions.

    Args:
        field_name: The field name to convert
        from_style: The current style ('camelCase', 'snake_case', etc.)
        to_style: The target style

    Returns:
        str: The converted field name
    """
    if from_style == 'camelCase' and to_style == 'snake_case':
        return camel_to_snake(field_name)
    elif from_style == 'snake_case' and to_style == 'camelCase':
        return snake_to_camel(field_name)
    return field_name

def get_all_backend_fields(app_models: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Extract a flattened dictionary of all backend fields.

    Args:
        app_models: Dictionary of app models

    Returns:
        dict: Dictionary mapping field names to their metadata
    """
    all_fields = {}

    for app_label, app_data in app_models.items():
        for model_name, model_data in app_data['models'].items():
            # Add regular fields
            for field_name, field_info in model_data['fields'].items():
                all_fields[field_name] = {
                    'app': app_label,
                    'model': model_name,
                    'type': field_info['field_type'],
                    'is_relation': False
                }

            # Add relation fields
            for field_name, field_info in model_data['related_fields'].items():
                all_fields[field_name] = {
                    'app': app_label,
                    'model': model_name,
                    'type': field_info['field_type'],
                    'is_relation': True,
                    'related_model': field_info['related_model']
                }

                # Also add ID field variant that's common in forms
                id_field_name = f"{field_name}_id"
                all_fields[id_field_name] = {
                    'app': app_label,
                    'model': model_name,
                    'type': 'RelationID',
                    'is_relation': True,
                    'related_model': field_info['related_model']
                }

            # Add serializer fields if available
            if model_data['has_serializer']:
                for field_name, field_info in model_data['serializer_fields'].items():
                    # If it's a custom field not in the model
                    if field_name not in model_data['fields'] and field_name not in model_data['related_fields']:
                        all_fields[field_name] = {
                            'app': app_label,
                            'model': model_name,
                            'type': 'SerializerField',
                            'is_relation': False,
                            'source': field_info.get('source')
                        }

    return all_fields

def check_field_consistency(frontend_data: Dict[str, Dict[str, List[Dict[str, Any]]]], 
                          backend_fields: Dict[str, Dict[str, Any]], 
                          config: dict) -> Dict[str, Any]:
    """
    Check consistency between frontend and backend fields.

    Args:
        frontend_data: Dictionary of frontend files and their fields
        backend_fields: Dictionary of all backend fields
        config: The configuration dictionary

    Returns:
        dict: Results of the consistency check
    """
    logger.info("Checking field consistency...")

    results = {
        'frontend_only_fields': {},
        'backend_only_fields': {},
        'matched_fields': {},
        'file_reports': {}
    }

    # Get field mapping configuration
    field_mapping_rules = config['field_mapping']['rules']
    custom_mappings = config['field_mapping']['custom_mappings']

    # Create a set of all backend fields with all possible naming conventions
    all_backend_field_variants = {}
    for field_name, field_info in backend_fields.items():
        all_backend_field_variants[field_name] = field_info

        # Add camelCase variant
        if any(rule['enabled'] and rule['backend'] == 'snake_case' and rule['frontend'] == 'camelCase' 
               for rule in field_mapping_rules):
            if '_' in field_name:
                camel_variant = snake_to_camel(field_name)
                all_backend_field_variants[camel_variant] = {
                    **field_info,
                    'original_name': field_name
                }

    # Add custom mappings
    for frontend_field, backend_field in custom_mappings.items():
        if backend_field in backend_fields:
            all_backend_field_variants[frontend_field] = {
                **backend_fields[backend_field],
                'original_name': backend_field,
                'custom_mapping': True
            }

    # Build a set of all frontend fields across all files
    all_frontend_fields = set()
    frontend_fields_sources = {}  # Track which files each field appears in

    # Process each frontend file
    for file_path, file_data in frontend_data.items():
        file_report = {
            'missing_backend_fields': [],
            'matched_fields': []
        }

        # Extract field names from form_fields and api_fields
        form_field_names = [field['name'] for field in file_data['form_fields']]
        api_field_names = [field['name'] for field in file_data['api_fields']]

        # Combine all field names from this file
        all_file_fields = list(set(form_field_names + api_field_names))

        for field_name in all_file_fields:
            all_frontend_fields.add(field_name)

            # Track which files this field appears in
            if field_name not in frontend_fields_sources:
                frontend_fields_sources[field_name] = []
            frontend_fields_sources[field_name].append(file_path)

            # Check if this field exists in backend
            if field_name in all_backend_field_variants:
                # It's a match!
                backend_info = all_backend_field_variants[field_name]
                original_name = backend_info.get('original_name', field_name)

                if field_name not in results['matched_fields']:
                    results['matched_fields'][field_name] = {
                        'backend_field': original_name,
                        'files': []
                    }

                results['matched_fields'][field_name]['files'].append(file_path)
                file_report['matched_fields'].append({
                    'frontend_field': field_name,
                    'backend_field': original_name,
                    'model': backend_info['model'],
                    'app': backend_info['app']
                })
            else:
                # Frontend field not found in backend
                file_report['missing_backend_fields'].append(field_name)

                if field_name not in results['frontend_only_fields']:
                    results['frontend_only_fields'][field_name] = []

                results['frontend_only_fields'][field_name].append(file_path)

        results['file_reports'][file_path] = file_report

    # Find backend fields that don't appear in any frontend file
    for field_name, field_info in backend_fields.items():
        # Check if this field is used as a backend_field in any match
        is_original_name_for_any_match = any(
            field_name == matched_info['backend_field'] 
            for matched_info in results['matched_fields'].values()
        )

        # Check if the field or any of its variants is used in frontend
        camel_variant = snake_to_camel(field_name)

        # A field is backend-only if:
        # 1. Neither it nor its variant appears directly in frontend
        # 2. It's not used as a backend_field in any match
        is_used_in_frontend = (
            field_name in all_frontend_fields or 
            camel_variant in all_frontend_fields or
            is_original_name_for_any_match
        )

        if not is_used_in_frontend:
            results['backend_only_fields'][field_name] = field_info

    # Calculate proper statistics (avoiding double-counting)
    all_frontend_field_set = set(all_frontend_fields)
    all_backend_field_set = set(backend_fields.keys())
    unique_fields_total = len(all_frontend_field_set.union(all_backend_field_set))

    results['stats'] = {
        'total_frontend_files': len(frontend_data),
        'total_frontend_fields': len(all_frontend_field_set),
        'total_backend_fields': len(all_backend_field_set),
        'total_unique_fields': unique_fields_total,
        'matched_fields': len(results['matched_fields']),
        'frontend_only_fields': len(results['frontend_only_fields']),
        'backend_only_fields': len(results['backend_only_fields'])
    }

    logger.info(f"Field consistency check complete - found {results['stats']['matched_fields']} matched fields")
    return results

# ------------------------------------------------------------------------------
# REPORTING
# ------------------------------------------------------------------------------

def generate_html_report(results: Dict[str, Any], app_models: Dict[str, Dict[str, Any]], config: dict) -> str:
    """
    Generate an HTML report of the consistency check results.

    Args:
        results: Results of the consistency check
        app_models: Dictionary of app models
        config: The configuration dictionary

    Returns:
        str: Path to the generated HTML report
    """
    logger.info("Generating HTML report...")

    try:
        from jinja2 import Environment, Template
        import json

        # Create environment with filters
        env = Environment()

        # Add tojson filter if not available (for compatibility with older Jinja2 versions)
        if 'tojson' not in env.filters:
            env.filters['tojson'] = lambda obj: json.dumps(obj)

        # Add sanitize_id filter
        env.filters['sanitize_id'] = sanitize_id

        # HTML report template
        template_str = '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Field Consistency Report</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }
                h1, h2, h3, h4 {
                    color: #2c3e50;
                }
                .header {
                    background-color: #2c3e50;
                    color: white;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }
                .stats {
                    display: flex;
                    flex-wrap: wrap;
                    margin-bottom: 30px;
                }
                .stat-card {
                    flex: 1;
                    min-width: 200px;
                    background: #f8f9fa;
                    padding: 15px;
                    margin: 10px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                .stat-value {
                    font-size: 24px;
                    font-weight: bold;
                    color: #2c3e50;
                }
                .section {
                    margin-bottom: 30px;
                    padding: 20px;
                    background: white;
                    border-radius: 5px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                th, td {
                    padding: 12px 15px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }
                th {
                    background-color: #f8f9fa;
                }
                tr:hover {
                    background-color: #f5f5f5;
                }
                .badge {
                    display: inline-block;
                    padding: 3px 8px;
                    font-size: 12px;
                    font-weight: bold;
                    border-radius: 3px;
                    margin-right: 5px;
                }
                .badge-success {
                    background-color: #28a745;
                    color: white;
                }
                .badge-warning {
                    background-color: #ffc107;
                    color: #212529;
                }
                .badge-danger {
                    background-color: #dc3545;
                    color: white;
                }
                .collapsible {
                    background-color: #f8f9fa;
                    color: #444;
                    cursor: pointer;
                    padding: 18px;
                    width: 100%;
                    border: none;
                    text-align: left;
                    outline: none;
                    font-size: 15px;
                    border-radius: 5px;
                    margin-bottom: 5px;
                }
                .active, .collapsible:hover {
                    background-color: #eee;
                }
                .content {
                    padding: 0 18px;
                    max-height: 0;
                    overflow: hidden;
                    transition: max-height 0.2s ease-out;
                    background-color: white;
                }
                .content.visible {
                    max-height: 1000px;
                }
                .search-container {
                    margin-bottom: 20px;
                }
                #searchInput {
                    width: 100%;
                    padding: 12px 20px;
                    margin: 8px 0;
                    box-sizing: border-box;
                    border: 2px solid #ccc;
                    border-radius: 4px;
                    font-size: 16px;
                }
                #no-results {
                    display: none;
                    padding: 20px;
                    background-color: #f8d7da;
                    color: #721c24;
                    border-radius: 5px;
                    text-align: center;
                    margin: 20px 0;
                }
                
                /* Added styles for large content handling */
                .large-content {
                    max-height: initial;
                    padding-bottom: 18px;
                }
                .lazy-load {
                    color: blue;
                    text-decoration: underline;
                    cursor: pointer;
                    margin: 10px 0;
                    display: block;
                }
                .confidence-high {
                    background-color: #d4edda;
                }
                .confidence-medium {
                    background-color: #fff3cd;
                }
                .confidence-low {
                    background-color: #f8d7da;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Field Consistency Report</h1>
                <p>Generated on {{ timestamp }}</p>
            </div>
            
            <div class="search-container">
                <input type="text" id="searchInput" placeholder="Search for fields, files, or models...">
                <div id="no-results">No matching results found</div>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <h3>Frontend Files</h3>
                    <div class="stat-value">{{ results.stats.total_frontend_files }}</div>
                </div>
                <div class="stat-card">
                    <h3>Frontend Fields</h3>
                    <div class="stat-value">{{ results.stats.total_frontend_fields }}</div>
                </div>
                <div class="stat-card">
                    <h3>Backend Fields</h3>
                    <div class="stat-value">{{ results.stats.total_backend_fields }}</div>
                </div>
                <div class="stat-card">
                    <h3>Matched Fields</h3>
                    <div class="stat-value">{{ results.stats.matched_fields }}</div>
                </div>
                <div class="stat-card">
                    <h3>Frontend-Only</h3>
                    <div class="stat-value">{{ results.stats.frontend_only_fields }}</div>
                </div>
                <div class="stat-card">
                    <h3>Backend-Only</h3>
                    <div class="stat-value">{{ results.stats.backend_only_fields }}</div>
                </div>
            </div>
            
            <!-- Matched Fields -->
            <div id="matched-section" class="section searchable-section">
                <h2>Matched Fields</h2>
                <p>These fields exist in both frontend and backend with proper mapping</p>
                
                <table>
                    <thead>
                        <tr>
                            <th>Frontend Field</th>
                            <th>Backend Field</th>
                            <th>Model</th>
                            <th>Used In</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for field_name, field_info in results.matched_fields.items() %}
                            {% set backend_field = field_info.backend_field %}
                            {% set files = field_info.files %}
                            <tr class="searchable-item">
                                <td>{{ field_name }}</td>
                                <td>{{ backend_field }}</td>
                                <td>
                                    {% for app_name, app_data in app_models.items() %}
                                        {% for model_name, model_data in app_data.models.items() %}
                                            {% if backend_field in model_data.fields or backend_field in model_data.related_fields or (model_data.serializer_fields is defined and backend_field in model_data.serializer_fields) %}
                                                {{ model_name }}
                                            {% endif %}
                                        {% endfor %}
                                    {% endfor %}
                                </td>
                                <td>
                                    {% if files|length > 10 %}
                                        <button class="collapsible">{{ files|length }} file(s)</button>
                                        <div class="content">
                                            <div id="files-{{ field_name|sanitize_id }}" data-loaded="false">
                                                <span class="lazy-load" onclick="loadFiles('files-{{ field_name|sanitize_id }}', {{ files|tojson }})">
                                                    Click to load {{ files|length }} files
                                                </span>
                                            </div>
                                        </div>
                                    {% else %}
                                        <button class="collapsible">{{ files|length }} file(s)</button>
                                        <div class="content">
                                            <ul>
                                                {% for file in files %}
                                                    <li>{{ file }}</li>
                                                {% endfor %}
                                            </ul>
                                        </div>
                                    {% endif %}
                                </td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <!-- Frontend-Only Fields -->
            <div id="frontend-only-section" class="section searchable-section">
                <h2>Frontend-Only Fields</h2>
                <p>These fields exist in the frontend but were not found in the backend</p>
                
                <table>
                    <thead>
                        <tr>
                            <th>Field Name</th>
                            <th>Used In</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for field_name, files in results.frontend_only_fields.items() %}
                            <tr class="searchable-item">
                                <td>{{ field_name }}</td>
                                <td>
                                    {% if files|length > 10 %}
                                        <button class="collapsible">{{ files|length }} file(s)</button>
                                        <div class="content">
                                            <div id="frontend-files-{{ field_name|sanitize_id }}" data-loaded="false">
                                                <span class="lazy-load" onclick="loadFiles('frontend-files-{{ field_name|sanitize_id }}', {{ files|tojson }})">
                                                    Click to load {{ files|length }} files
                                                </span>
                                            </div>
                                        </div>
                                    {% else %}
                                        <button class="collapsible">{{ files|length }} file(s)</button>
                                        <div class="content">
                                            <ul>
                                                {% for file in files %}
                                                    <li>{{ file }}</li>
                                                {% endfor %}
                                            </ul>
                                        </div>
                                    {% endif %}
                                </td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <!-- Backend-Only Fields -->
            <div id="backend-only-section" class="section searchable-section">
                <h2>Backend-Only Fields</h2>
                <p>These fields exist in the backend but were not found in the frontend</p>
                
                <table>
                    <thead>
                        <tr>
                            <th>Field Name</th>
                            <th>Model</th>
                            <th>Type</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for field_name, field_info in results.backend_only_fields.items() %}
                            <tr class="searchable-item">
                                <td>{{ field_name }}</td>
                                <td>{{ field_info.model }}</td>
                                <td>{{ field_info.type }}</td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <!-- File Reports -->
            <div id="file-reports-section" class="section searchable-section">
                <h2>File Reports</h2>
                <p>Details about each frontend file</p>
                
                {% for file_path, file_report in results.file_reports.items() %}
                    <button class="collapsible">{{ file_path }}</button>
                    <div class="content searchable-item">
                        <h3>Matched Fields</h3>
                        {% if file_report.matched_fields %}
                            <table>
                                <thead>
                                    <tr>
                                        <th>Frontend Field</th>
                                        <th>Backend Field</th>
                                        <th>Model</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for match in file_report.matched_fields %}
                                        <tr class="confidence-{% if match.confidence is defined %}{{ match.confidence }}{% else %}medium{% endif %}">
                                            <td>{{ match.frontend_field }}</td>
                                            <td>{{ match.backend_field }}</td>
                                            <td>{{ match.app }}.{{ match.model }}</td>
                                        </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        {% else %}
                            <p>No matched fields</p>
                        {% endif %}
                        
                        <h3>Missing Backend Fields</h3>
                        {% if file_report.missing_backend_fields %}
                            <ul>
                                {% for field in file_report.missing_backend_fields %}
                                    <li>{{ field }}</li>
                                {% endfor %}
                            </ul>
                        {% else %}
                            <p>All fields in this file have backend matches</p>
                        {% endif %}
                    </div>
                {% endfor %}
            </div>
            
            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    // Handle collapsible sections
                    var coll = document.getElementsByClassName("collapsible");
                    for (var i = 0; i < coll.length; i++) {
                        coll[i].addEventListener("click", function() {
                            this.classList.toggle("active");
                            var content = this.nextElementSibling;
                            if (content.style.maxHeight) {
                                content.style.maxHeight = null;
                                content.classList.remove("visible");
                            } else {
                                content.style.maxHeight = content.scrollHeight + "px";
                                content.classList.add("visible");
                                
                                // Load content dynamically if needed
                                var loadableContent = content.querySelector('[data-loaded="false"]');
                                if (loadableContent && loadableContent.firstElementChild) {
                                    loadableContent.firstElementChild.click();
                                }
                            }
                        });
                    }
                    
                    // Search functionality
                    const searchInput = document.getElementById('searchInput');
                    const noResults = document.getElementById('no-results');
                    const sections = document.querySelectorAll('.searchable-section');
                    
                    searchInput.addEventListener('keyup', function() {
                        const searchTerm = this.value.toLowerCase();
                        let anyResults = false;
                        
                        if (searchTerm.length > 2) {
                            // For each section, check if any items match
                            sections.forEach(section => {
                                const items = section.querySelectorAll('.searchable-item');
                                let sectionHasMatch = false;
                                
                                items.forEach(item => {
                                    const text = item.textContent.toLowerCase();
                                    if (text.includes(searchTerm)) {
                                        item.style.display = '';
                                        sectionHasMatch = true;
                                    } else {
                                        item.style.display = 'none';
                                    }
                                });
                                
                                if (sectionHasMatch) {
                                    section.style.display = '';
                                    anyResults = true;
                                } else {
                                    section.style.display = 'none';
                                }
                            });
                            
                            // Show/hide no results message
                            noResults.style.display = anyResults ? 'none' : 'block';
                        } else {
                            // If search term is too short, show everything
                            sections.forEach(section => {
                                section.style.display = '';
                                const items = section.querySelectorAll('.searchable-item');
                                items.forEach(item => {
                                    item.style.display = '';
                                });
                            });
                            noResults.style.display = 'none';
                        }
                    });
                });
                
                // Function to load file lists lazily
                function loadFiles(containerId, files) {
                    const container = document.getElementById(containerId);
                    if (!container) return;
                    
                    // Create list element
                    const ul = document.createElement('ul');
                    
                    // Add files to list
                    files.forEach(file => {
                        const li = document.createElement('li');
                        li.textContent = file;
                        ul.appendChild(li);
                    });
                    
                    // Replace the placeholder with the actual list
                    container.innerHTML = '';
                    container.appendChild(ul);
                    container.setAttribute('data-loaded', 'true');
                    
                    // Update parent content height if needed
                    const parentContent = container.closest('.content');
                    if (parentContent && parentContent.classList.contains('visible')) {
                        parentContent.style.maxHeight = parentContent.scrollHeight + "px";
                    }
                }
            </script>
        </body>
        </html>
        '''

        # Create template from the string using the environment
        template = env.from_string(template_str)

        # Render the template with data
        html_output = template.render(
            results=results,
            app_models=app_models,
            timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        # Ensure output directory exists
        os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)

        # Write the HTML to a file
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write(html_output)

        logger.info(f"HTML report generated: {REPORT_FILE}")
        return REPORT_FILE

    except Exception as e:
        logger.error(f"Failed to generate HTML report: {str(e)}")
        traceback.print_exc()
        return None

def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Check consistency between Django backend and React frontend fields')

    parser.add_argument('--django-root', type=str, help='Django project root directory')
    parser.add_argument('--frontend-root', type=str, help='React frontend root directory')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--report', type=str, help='Path for HTML report output')
    parser.add_argument('--non-interactive', action='store_true', help='Run in non-interactive mode')
    parser.add_argument('--format', choices=['html', 'json'], default='html', 
                        help='Output format (html or json)')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--apps', type=str, help='Comma-separated list of Django apps to process')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--quiet', action='store_true', help='Minimize console output')
    parser.add_argument('--settings', type=str, help='Django settings module to use')

    return parser.parse_args()

def main():
    """
    Main function to run the field consistency checker.

    Returns:
        int: Exit code (0 for success, 1 for error, 2 for consistency issues)
    """
    # Parse command-line arguments
    args = parse_arguments()

    # Configure logging level based on arguments
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    # Update globals from arguments if provided
    global DJANGO_PROJECT_ROOT, FRONTEND_ROOT, CONFIG_FILE, REPORT_FILE

    if args.django_root:
        DJANGO_PROJECT_ROOT = args.django_root

    if args.frontend_root:
        FRONTEND_ROOT = args.frontend_root

    if args.config:
        CONFIG_FILE = args.config

    if args.report:
        REPORT_FILE = args.report

    # If settings module provided, use it
    if args.settings:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', args.settings)

    # Print header
    print("=" * 80)
    print("DJANGO-REACT FIELD CONSISTENCY CHECKER")
    print("=" * 80)
    print(f"Django project: {DJANGO_PROJECT_ROOT}")
    print(f"React frontend: {FRONTEND_ROOT}")
    print(f"Config file: {CONFIG_FILE}")
    print(f"Report file: {REPORT_FILE}")
    print("=" * 80)

    # Check if directories exist
    if not os.path.exists(DJANGO_PROJECT_ROOT):
        logger.error(f"Django project directory not found: {DJANGO_PROJECT_ROOT}")
        return 1

    if not os.path.exists(FRONTEND_ROOT):
        logger.error(f"React frontend directory not found: {FRONTEND_ROOT}")
        return 1

    # Load configuration
    config = load_or_create_config()

    # Update config based on arguments
    if args.apps:
        app_list = [app.strip() for app in args.apps.split(',')]
        logger.info(f"Limiting analysis to apps: {', '.join(app_list)}")
        # Store the app list in config
        config['backend']['include_apps'] = app_list

    # Set up Django
    if not setup_django_environment():
        logger.error("Failed to set up Django environment. Exiting.")
        return 1

    try:
        # Get Django models
        app_models = get_all_models(config)
        if not app_models:
            logger.error("No Django models found. Exiting.")
            return 1

        # Analyze serializers
        app_models = analyze_serializers(app_models, config)

        # Get all backend fields
        backend_fields = get_all_backend_fields(app_models)
        logger.info(f"Found {len(backend_fields)} unique fields in backend models")

        # Find frontend files
        frontend_files = find_frontend_files(config)
        if not frontend_files:
            logger.error("No frontend files found. Exiting.")
            return 1

        # Analyze frontend files
        frontend_data = analyze_frontend_files(frontend_files, config)

        # Check consistency
        results = check_field_consistency(frontend_data, backend_fields, config)

        # Output results
        if args.format == 'json':
            output_path = args.output or 'field_consistency_results.json'
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {output_path}")
        else:
            # Generate HTML report
            report_path = generate_html_report(results, app_models, config)
            if report_path:
                logger.info(f"HTML report generated: {report_path}")

                # In interactive mode, offer to open the report
                if not args.non_interactive:
                    try:
                        open_report = input("\nOpen HTML report now? (y/n): ").lower() in ('y', 'yes')
                        if open_report:
                            import webbrowser
                            webbrowser.open(f"file://{os.path.abspath(report_path)}")
                    except Exception as e:
                        logger.error(f"Failed to open report: {e}")

        # Print summary
        print("\nSUMMARY:")
        print(f"  Frontend files analyzed: {results['stats']['total_frontend_files']}")
        print(f"  Frontend fields found: {results['stats']['total_frontend_fields']}")
        print(f"  Backend fields found: {results['stats']['total_backend_fields']}")
        print(f"  Matched fields: {results['stats']['matched_fields']}")
        print(f"  Frontend-only fields: {results['stats']['frontend_only_fields']}")
        print(f"  Backend-only fields: {results['stats']['backend_only_fields']}")

        match_percentage = 0
        if results['stats']['total_frontend_fields'] > 0:
            match_percentage = (results['stats']['matched_fields'] / results['stats']['total_frontend_fields']) * 100

        print(f"  Field match rate: {match_percentage:.1f}%")

        if results['stats']['frontend_only_fields'] > 0:
            print("\nConsider adding these frontend fields to your whitelist if they're intentional:")
            for field in list(results['frontend_only_fields'].keys())[:5]:
                print(f"  - {field}")
            if len(results['frontend_only_fields']) > 5:
                print(f"  ... and {len(results['frontend_only_fields']) - 5} more")

        print("\nField consistency check completed successfully!")

        # Return appropriate exit code for CI/CD integration
        # Calculate the threshold dynamically based on project size
        threshold_percentage = 70
        threshold_absolute = min(10, max(3, int(results['stats']['total_frontend_fields'] * 0.1)))

        if match_percentage < threshold_percentage and results['stats']['frontend_only_fields'] > threshold_absolute:
            logger.warning("Low field match rate detected. Check for potential issues.")
            return 2

        return 0

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        traceback.print_exc()
        return 1
    finally:
        # Stop the logging queue listener
        listener.stop()

if __name__ == "__main__":
    sys.exit(main())