# fmt: off
# isort: skip_file

r"""

File: C:\Users\Santhanam\OneDrive\Personal\Full stack web development\eduplatform\backend\fixed_inspect_all_models.py

Purpose: This script provides a comprehensive inspection of all Django models, views, serializers, and URLs 
         in your educational platform to ensure consistency between field names and connections.

This script fixes the UnicodeEncodeError by explicitly specifying UTF-8 encoding when writing the report file.

This script will:
1. Set up the Django environment properly to access models and other components
2. Inspect all models in all apps, listing their fields, types, and relationships
3. Inspect all views in all apps, showing API endpoints and methods
4. Inspect all serializers in all apps, showing their fields
5. Inspect all URL patterns to show API endpoints
6. Generate a comprehensive report with all this information
7. Save the report to a text file for analysis using UTF-8 encoding
8. Check for field name consistency between models, serializers, and views
9. Identify potential compatibility issues

Variables to modify:
- OUTPUT_FILE: Path to the output text file (default: "model_inspection_report.txt")
- APPS_TO_INSPECT: List of app names to inspect (default: all installed apps)
- DETAILED_VIEW: Boolean to control detail level of the report (default: True)

Requirements:
- Python 3.6+
- Django 3.2+
- Access to your Django project

How to run this script:
1. Make sure your virtual environment is activated:
   venv\Scripts\activate
2. Run the script:
   python fixed_inspect_all_models.py
3. The report will be saved to "model_inspection_report.txt" in the same directory

Additional notes:
- This script is read-only and will not modify any data or code
- For frontend-backend compatibility checking, manual review of the report against your frontend code is needed
  because the script cannot directly access your frontend code structure
- This fixed version explicitly specifies UTF-8 encoding when writing the output file

Created by: Professor Santhanam
Last updated: 2025-04-27 18:15:32
"""

# Standard library imports
import os
import sys
import inspect
import importlib
import datetime
from collections import defaultdict

# Get the absolute path to the project directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Set up the Django environment
print("Setting up Django environment...")
sys.path.insert(0, SCRIPT_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'educore.settings')

import django
django.setup()

# Now we can safely import Django components
from django.apps import apps
from django.urls import get_resolver
from django.conf import settings

# Configuration variables (you can modify these)
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "model_inspection_report.txt")
APPS_TO_INSPECT = []  # Leave empty to inspect all apps
DETAILED_VIEW = True  # Set to False for a more concise report

# Initialize report content
report = []
issues = []

def add_to_report(section_title, content):
    """Add a section to the report with a title and content"""
    report.append("\n" + "=" * 80)
    report.append(section_title)
    report.append("=" * 80)
    if isinstance(content, list):
        report.extend(content)
    else:
        report.append(content)

def add_issue(issue_description):
    """Add an issue to the issues list"""
    issues.append(f"Warning: {issue_description}")

def get_timestamp():
    """Return a formatted timestamp for the report"""
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

def inspect_models():
    """Inspect all models in all apps"""
    print("Inspecting models...")
    models_report = []
    model_field_registry = {}  # To track field names across models

    # Get all installed apps or filter by APPS_TO_INSPECT
    installed_apps = [app_config for app_config in apps.get_app_configs() 
                     if not APPS_TO_INSPECT or app_config.name.split('.')[-1] in APPS_TO_INSPECT]

    for app_config in installed_apps:
        app_name = app_config.name.split('.')[-1]
        app_models = app_config.get_models()

        if not app_models:
            continue

        models_report.append(f"\nApp: {app_name}")
        models_report.append("-" * 40)

        for model in app_models:
            model_name = model.__name__
            models_report.append(f"\n  Model: {model_name}")

            # Get all fields
            fields = model._meta.get_fields()
            model_field_registry[f"{app_name}.{model_name}"] = []

            for field in fields:
                field_type = type(field).__name__
                field_info = f"    - {field.name}: {field_type}"

                # Add related model info for relation fields
                if hasattr(field, 'related_model') and field.related_model:
                    related_model_name = field.related_model.__name__
                    field_info += f" -> {related_model_name}"

                # Add additional info for fields (if DETAILED_VIEW is True)
                if DETAILED_VIEW:
                    extra_info = []
                    if hasattr(field, 'null'):
                        extra_info.append(f"null={field.null}")
                    if hasattr(field, 'blank'):
                        extra_info.append(f"blank={field.blank}")
                    if hasattr(field, 'max_length') and field.max_length:
                        extra_info.append(f"max_length={field.max_length}")
                    if hasattr(field, 'choices') and field.choices:
                        choices = [choice[0] for choice in field.choices]
                        extra_info.append(f"choices={choices}")

                    if extra_info:
                        field_info += f" ({', '.join(extra_info)})"

                models_report.append(field_info)
                model_field_registry[f"{app_name}.{model_name}"].append(field.name)

    return models_report, model_field_registry

def inspect_views():
    """Inspect all views in all apps"""
    print("Inspecting views...")
    views_report = []
    view_registry = defaultdict(list)

    # Get all installed apps or filter by APPS_TO_INSPECT
    installed_apps = [app_config for app_config in apps.get_app_configs() 
                     if not APPS_TO_INSPECT or app_config.name.split('.')[-1] in APPS_TO_INSPECT]

    for app_config in installed_apps:
        app_name = app_config.name.split('.')[-1]
        views_module_name = f"{app_config.name}.views"

        try:
            # Try to import the views module
            views_module = importlib.import_module(views_module_name)
            views_report.append(f"\nApp: {app_name}")
            views_report.append("-" * 40)

            # Look for class-based views
            for name, obj in inspect.getmembers(views_module):
                # Check if it's a class and inherits from Django's View
                if inspect.isclass(obj) and hasattr(obj, 'as_view'):
                    views_report.append(f"\n  View: {name}")

                    # Check for HTTP methods
                    for method in ['get', 'post', 'put', 'patch', 'delete']:
                        if hasattr(obj, method):
                            views_report.append(f"    - HTTP Method: {method.upper()}")

                    # Check for model attribute in ModelViewSet and similar classes
                    if hasattr(obj, 'model') and obj.model:
                        views_report.append(f"    - Model: {obj.model.__name__}")
                        view_registry[app_name].append((name, obj.model.__name__))

                    # Check for queryset attribute
                    if hasattr(obj, 'queryset') and obj.queryset is not None:
                        queryset_model = obj.queryset.model.__name__ if hasattr(obj.queryset, 'model') else "Unknown"
                        views_report.append(f"    - Queryset Model: {queryset_model}")
                        if queryset_model != "Unknown":
                            view_registry[app_name].append((name, queryset_model))

                    # Check for serializer class
                    if hasattr(obj, 'serializer_class') and obj.serializer_class:
                        serializer_name = obj.serializer_class.__name__
                        views_report.append(f"    - Serializer: {serializer_name}")

        except ModuleNotFoundError:
            # No views module found for this app
            continue
        except Exception as e:
            views_report.append(f"    Error inspecting views: {str(e)}")

    return views_report, view_registry

def inspect_serializers():
    """Inspect all serializers in all apps"""
    print("Inspecting serializers...")
    serializers_report = []
    serializer_field_registry = {}

    # Get all installed apps or filter by APPS_TO_INSPECT
    installed_apps = [app_config for app_config in apps.get_app_configs() 
                     if not APPS_TO_INSPECT or app_config.name.split('.')[-1] in APPS_TO_INSPECT]

    for app_config in installed_apps:
        app_name = app_config.name.split('.')[-1]
        serializers_module_name = f"{app_config.name}.serializers"

        try:
            # Try to import the serializers module
            serializers_module = importlib.import_module(serializers_module_name)
            serializers_report.append(f"\nApp: {app_name}")
            serializers_report.append("-" * 40)

            # Try to find DRF's serializers
            for name, obj in inspect.getmembers(serializers_module):
                # Look for classes that might be serializers
                if inspect.isclass(obj) and hasattr(obj, 'Meta'):
                    serializers_report.append(f"\n  Serializer: {name}")

                    # Check for model attribute in Meta
                    if hasattr(obj.Meta, 'model'):
                        model_name = obj.Meta.model.__name__
                        serializers_report.append(f"    - Model: {model_name}")

                        # Check for fields attribute in Meta
                        if hasattr(obj.Meta, 'fields'):
                            fields = obj.Meta.fields
                            if fields == '__all__':
                                serializers_report.append(f"    - Fields: All model fields")
                            else:
                                fields_str = ", ".join(fields)
                                serializers_report.append(f"    - Fields: {fields_str}")
                                serializer_field_registry[f"{app_name}.{name}"] = list(fields)

                        # Check for exclude attribute in Meta
                        if hasattr(obj.Meta, 'exclude'):
                            exclude_str = ", ".join(obj.Meta.exclude)
                            serializers_report.append(f"    - Excluded: {exclude_str}")

                    # Check for explicitly declared fields
                    explicit_fields = []
                    for field_name, field_obj in inspect.getmembers(obj):
                        if not field_name.startswith('_') and not inspect.ismethod(field_obj) and not inspect.isfunction(field_obj):
                            if hasattr(field_obj, 'field_name'):
                                explicit_fields.append(field_name)

                    if explicit_fields:
                        explicit_fields_str = ", ".join(explicit_fields)
                        serializers_report.append(f"    - Explicit fields: {explicit_fields_str}")

                        # Add explicit fields to registry
                        if f"{app_name}.{name}" in serializer_field_registry:
                            serializer_field_registry[f"{app_name}.{name}"].extend(explicit_fields)
                        else:
                            serializer_field_registry[f"{app_name}.{name}"] = explicit_fields

        except ModuleNotFoundError:
            # No serializers module for this app
            continue
        except Exception as e:
            serializers_report.append(f"    Error inspecting serializers: {str(e)}")

    return serializers_report, serializer_field_registry

def inspect_urls():
    """Inspect all URLs in the project"""
    print("Inspecting URLs...")
    urls_report = []

    # Get the URL resolver
    resolver = get_resolver()

    urls_report.append("\nURL Patterns:")
    urls_report.append("-" * 40)

    # Recursively get all URL patterns
    def extract_patterns(resolver, prefix=""):
        patterns = []

        for pattern in resolver.url_patterns:
            path = prefix + str(pattern.pattern)

            # If it's a path that includes other patterns
            if hasattr(pattern, 'url_patterns'):
                patterns.extend(extract_patterns(pattern, path))
            else:
                # Get view name
                view_name = ""
                if hasattr(pattern, 'callback'):
                    if hasattr(pattern.callback, '__name__'):
                        view_name = pattern.callback.__name__
                    elif hasattr(pattern.callback, '__class__'):
                        view_name = pattern.callback.__class__.__name__

                patterns.append((path, view_name))

        return patterns

    all_patterns = extract_patterns(resolver)

    # Format URL patterns
    for path, view_name in sorted(all_patterns):
        urls_report.append(f"  {path} -> {view_name}")

    return urls_report

def check_consistency(model_field_registry, serializer_field_registry):
    """Check consistency between models and serializers"""
    print("Checking consistency between models and serializers...")
    consistency_report = []

    consistency_report.append("\nConsistency Check:")
    consistency_report.append("-" * 40)

    for serializer_key, serializer_fields in serializer_field_registry.items():
        app_name, serializer_name = serializer_key.split('.')

        # Try to find a corresponding model based on naming convention
        # Usually serializers are named as ModelNameSerializer
        possible_model_name = serializer_name.replace('Serializer', '')
        model_key = f"{app_name}.{possible_model_name}"

        if model_key in model_field_registry:
            model_fields = model_field_registry[model_key]

            # Check for fields in serializer not in model
            for field in serializer_fields:
                if field not in model_fields and field != 'id' and field != 'url':
                    issue = f"Field '{field}' in serializer '{serializer_name}' not found in model '{possible_model_name}'"
                    consistency_report.append(f"Warning: {issue}")
                    add_issue(issue)

            consistency_report.append(f"Checked serializer '{serializer_name}' against model '{possible_model_name}'")

    return consistency_report

def find_frontend_backend_api_connections():
    """Identify API endpoints that frontend likely connects to"""
    print("Identifying potential frontend-backend connections...")
    connections_report = []

    connections_report.append("\nPotential Frontend-Backend API Connections:")
    connections_report.append("-" * 40)

    # Get the URL resolver
    resolver = get_resolver()

    # Recursively get all URL patterns that look like API endpoints
    def extract_api_patterns(resolver, prefix=""):
        patterns = []

        for pattern in resolver.url_patterns:
            path = prefix + str(pattern.pattern)

            # If it's a path that includes other patterns
            if hasattr(pattern, 'url_patterns'):
                patterns.extend(extract_api_patterns(pattern, path))
            else:
                # Check if it looks like an API endpoint
                if 'api' in path.lower() or path.endswith('/'):
                    view_name = ""
                    if hasattr(pattern, 'callback'):
                        if hasattr(pattern.callback, '__name__'):
                            view_name = pattern.callback.__name__
                        elif hasattr(pattern.callback, '__class__'):
                            view_name = pattern.callback.__class__.__name__

                    patterns.append((path, view_name))

        return patterns

    api_patterns = extract_api_patterns(resolver)

    # Group API endpoints by resource type
    resource_apis = defaultdict(list)

    for path, view_name in api_patterns:
        # Try to extract resource name from URL pattern
        parts = path.strip('/').split('/')
        if parts:
            resource = parts[-1]
            if not resource:  # If path ends with '/', use the previous part
                resource = parts[-2] if len(parts) > 1 else "unknown"
            resource_apis[resource].append((path, view_name))

    # List potential frontend connections
    connections_report.append("\nFrontend components likely need to connect to these API endpoints:")

    for resource, endpoints in resource_apis.items():
        connections_report.append(f"\n  Resource: {resource.capitalize()}")
        for path, view_name in endpoints:
            connections_report.append(f"    - {path} -> {view_name}")

        connections_report.append(f"    Frontend components that might use this:")
        connections_report.append(f"      * {resource.capitalize()}List.js or {resource.capitalize()}List.vue (for listings)")
        connections_report.append(f"      * {resource.capitalize()}Detail.js or {resource.capitalize()}Detail.vue (for details)")
        connections_report.append(f"      * {resource.capitalize()}Form.js or {resource.capitalize()}Form.vue (for creating/editing)")

    return connections_report

def run_inspection():
    """Run a full inspection of the project"""
    # Add report header
    add_to_report("MODEL INSPECTION REPORT",
                 [f"Generated: {get_timestamp()}",
                  f"Django Version: {django.get_version()}",
                  f"Project: Educational Platform with Three-Tier Access"])

    # Inspect models
    models_report, model_field_registry = inspect_models()
    add_to_report("MODELS", models_report)

    # Inspect views
    views_report, view_registry = inspect_views()
    add_to_report("VIEWS", views_report)

    # Inspect serializers
    serializers_report, serializer_field_registry = inspect_serializers()
    add_to_report("SERIALIZERS", serializers_report)

    # Inspect URLs
    urls_report = inspect_urls()
    add_to_report("URLs", urls_report)

    # Check consistency
    consistency_report = check_consistency(model_field_registry, serializer_field_registry)
    add_to_report("CONSISTENCY CHECK", consistency_report)

    # Find potential frontend-backend connections
    connections_report = find_frontend_backend_api_connections()
    add_to_report("FRONTEND-BACKEND CONNECTIONS", connections_report)

    # Add issues summary if any
    if issues:
        add_to_report("ISSUES SUMMARY", issues)
    else:
        add_to_report("ISSUES SUMMARY", ["No issues detected!"])

    # Add conclusion
    add_to_report("CONCLUSION", [
        "This report provides a comprehensive overview of your Django models, views, serializers, and URLs.",
        "Use it to ensure consistency between your backend components and to guide frontend development.",
        "",
        "For frontend-backend consistency:",
        "1. Ensure your frontend forms have field names that match your models and serializers",
        "2. Make sure your API calls from the frontend match the URLs identified in this report",
        "3. Check for any issues highlighted in the ISSUES SUMMARY section",
        "",
        "Remember that model fields should be the single source of truth for your application's data structure."
    ])

    # Write report to file - FIXED: Using UTF-8 encoding
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"\nInspection complete! Report saved to: {OUTPUT_FILE}")

    return '\n'.join(report)

if __name__ == "__main__":
    print("=" * 80)
    print("EDUCATIONAL PLATFORM - UNIVERSAL MODEL INSPECTION TOOL")
    print("=" * 80)
    print("This script will inspect all Django models, views, serializers, and URLs")
    print("and generate a comprehensive report for analysis.")
    print("\nThe report will be saved to:")
    print(OUTPUT_FILE)
    print("\nThis is a read-only operation and will not modify any files or data.")

    # Ask for confirmation
    response = input("\nDo you want to continue? (y/n): ")
    if response.lower() in ('y', 'yes'):
        # Run inspection
        report_content = run_inspection()

        # Ask if user wants to view the report
        view_response = input("\nDo you want to view the report now? (y/n): ")
        if view_response.lower() in ('y', 'yes'):
            print("\n" + "=" * 80)
            print("REPORT PREVIEW (First 2000 characters):")
            print("=" * 80)
            print(report_content[:2000] + "...\n")
            print(f"Full report available at: {OUTPUT_FILE}")
    else:
        print("\nOperation cancelled.")

    print("\nDone!")