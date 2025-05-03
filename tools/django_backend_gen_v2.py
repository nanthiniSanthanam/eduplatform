#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Django Backend Scaffolder - Complete Django REST API Generator
=======================================================================

Version: 2.0.0
Created: 2025-05-02
Author: nanthiniSanthanam

OVERVIEW
--------
This enterprise-grade Django scaffolder automatically generates a complete
REST API backend with advanced cross-app relationship handling and comprehensive
documentation. It analyzes your Django models to create:

1. Serializers with proper nested relationships and imports
2. ViewSets with filtering, pagination, and permissions
3. URL routing configuration
4. Admin interface customizations
5. Comprehensive test suites
6. Advanced permission classes
7. Signal handlers (when appropriate)
8. Complete API documentation with examples

KEY FEATURES
-----------
✓ Cross-App Dependency Resolution: Handles models that reference other apps
✓ Circular Import Detection & Mitigation: Strategic import placement
✓ Visual Dependency Graphs: Mermaid diagrams of app/model relationships
✓ Smart Template System: Context-aware code generation
✓ Advanced Permission Classes: Role and ownership-based access control
✓ Idempotent Generation: Safe to run repeatedly (creates backups)
✓ Schema Generation: OpenAPI/Swagger documentation
✓ Quality Checks: Validates generated code against standards
✓ Customization: Extensive template system with override capabilities

USAGE
-----
Basic usage:
    python enhanced_django_scaffolder.py

Options:
    --app APP_NAME       Generate for specific app(s) (can specify multiple)
    --output DIR         Output directory for generated files
    --templates DIR      Custom templates directory
    --format FORMAT      Documentation format (markdown, html, swagger)
    --graph              Generate dependency graphs (requires graphviz)
    --force              Overwrite files without creating backups
    --settings MODULE    Django settings module to use
    --verbosity LEVEL    Detail level (0-3, default: 1)
    --skip-validation    Skip validation checks
    --check-only         Check for issues without generating files

CUSTOMIZATION VARIABLES
---------------------
The following variables can be modified to fit your project structure:

SETTINGS_MODULE:       Django settings module if not set in environment
TEMPLATE_DIR:          Location of Jinja2 templates for code generation
BACKUP_DIR:            Directory for file backups
DOCS_OUTPUT_DIR:       Where documentation files are saved
DOCS_FORMAT:           Default documentation format ('md', 'html', 'swagger')
API_BASE_URL:          Base URL for API endpoints (e.g., 'api/v1')
IMPORT_STYLE:          Style for import statements ('absolute'/'relative')
NAMING_CONVENTIONS:    Customization of naming patterns
PERMISSION_STYLE:      Default permission setup ('jwt'/'session'/'oauth2')

EXAMPLES
--------
Single app:
    python enhanced_django_scaffolder.py --app users

Multiple apps with documentation:
    python enhanced_django_scaffolder.py --app users --app courses --format html

Project-wide with dependency graph:
    python enhanced_django_scaffolder.py --graph

OUTPUT STRUCTURE
--------------
For each app, generates or updates:
- serializers.py
- views.py
- urls.py
- admin.py
- permissions.py
- tests/test_api.py
- tests/test_models.py
- signals.py (if needed)
- filters.py (if needed)

Project-wide output:
- docs/api_documentation.{md|html}
- docs/dependencies.{md|svg}
- docs/openapi.yaml (if swagger format selected)

REQUIREMENTS
-----------
- Python ≥3.9
- Django ≥3.2
- Django REST Framework
- Jinja2 (for templates)
- PyYAML (for OpenAPI schema)
- Graphviz (optional, for dependency visualization)
"""

import argparse
import ast
import datetime as dt
import difflib
import importlib
import inspect
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import warnings
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

# ───────────────────────────────────────────────────────────────────────────────
# Configuration - modify these variables to match your project structure
# ───────────────────────────────────────────────────────────────────────────────
SETTINGS_MODULE = "config.settings"    # Django settings module if not set in environment
TEMPLATE_DIR = "scaffolder_templates"  # Directory for template files
BACKUP_DIR = Path("scaffolder_backups") # Directory for backup files
DOCS_OUTPUT_DIR = Path("docs")         # Where documentation files are saved
DOCS_FORMAT = "md"                     # Default format (md, html, swagger)
API_BASE_URL = "api/v1"                # Base URL for API endpoints
IMPORT_STYLE = "absolute"              # 'absolute' or 'relative'
CODEGEN_BANNER = """# ==========  AUTO-GENERATED – DO NOT EDIT MANUALLY  ==========
# Generated by Enhanced Django Scaffolder at {timestamp}
# https://github.com/myusername/enhanced-django-scaffolder
"""

# Verbose logging is helpful for debugging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger("django-scaffolder")

# ───────────────────────────────────────────────────────────────────────────────
# Dependency check and imports with helpful error messages
# ───────────────────────────────────────────────────────────────────────────────
def check_dependencies():
    """Check required dependencies and provide helpful installation instructions."""
    try:
        import django
        from django.conf import settings
        from django.apps import apps
        logger.info(f"Using Django {django.get_version()}")
    except ImportError:
        sys.exit("ERROR: Django is not installed. Run: pip install django")

    try:
        import rest_framework
        logger.info(f"Using Django REST Framework {rest_framework.VERSION}")
    except ImportError:
        sys.exit("ERROR: Django REST Framework is not installed. Run: pip install djangorestframework")

    try:
        import jinja2
        logger.info(f"Using Jinja2 {jinja2.__version__}")
    except ImportError:
        sys.exit("ERROR: Jinja2 is not installed. Run: pip install jinja2")

    # Optional dependencies
    try:
        import yaml
    except ImportError:
        logger.warning("PyYAML not installed. OpenAPI schema generation disabled. Run: pip install pyyaml")

    try:
        import graphviz
    except ImportError:
        logger.warning("Graphviz Python bindings not installed. Dependency visualization disabled. Run: pip install graphviz")
    
    return True

# Now that we've checked dependencies, import what we need
try:
    import django
    from django.apps import apps
    from django.conf import settings
    from django.core.management import call_command
    from django.db import models
    from django.db.models import fields
    from django.db.models.fields.related import ForeignKey, ManyToManyField, OneToOneField
    from django.urls import path, include, reverse
    
    import jinja2
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    
    try:
        import yaml
        YAML_AVAILABLE = True
    except ImportError:
        YAML_AVAILABLE = False
    
    try:
        import graphviz
        GRAPHVIZ_AVAILABLE = True
    except ImportError:
        GRAPHVIZ_AVAILABLE = False
        
except Exception as e:
    sys.exit(f"ERROR: {str(e)}")

# ───────────────────────────────────────────────────────────────────────────────
# Data structures for model analysis
# ───────────────────────────────────────────────────────────────────────────────
@dataclass
class FieldInfo:
    """Information about a model field."""
    name: str
    field_type: str
    null: bool = False
    blank: bool = False
    unique: bool = False
    related_model: Optional[str] = None
    related_app: Optional[str] = None
    related_name: Optional[str] = None
    help_text: str = ""
    verbose_name: str = ""
    choices: List[Tuple[Any, str]] = field(default_factory=list)
    is_relation: bool = False
    max_length: Optional[int] = None
    default: Any = None
    editable: bool = True
    auto_created: bool = False
    primary_key: bool = False
    many_to_many: bool = False
    one_to_one: bool = False
    searchable: bool = False
    filterable: bool = False
    
    def __post_init__(self):
        """Set searchable and filterable flags based on field type."""
        # Text fields are searchable
        if self.field_type in ("CharField", "TextField", "SlugField", "EmailField"):
            self.searchable = True
        
        # Most fields are filterable except large text/binary fields
        if self.field_type not in ("TextField", "FileField", "ImageField", "BinaryField"):
            self.filterable = True
            
    def get_json_example(self) -> Any:
        """Return an example value for this field suitable for JSON documentation."""
        if self.field_type == "CharField" or self.field_type == "TextField":
            return f"Example {self.name}"
        elif self.field_type == "IntegerField" or self.field_type == "PositiveIntegerField":
            return 42
        elif self.field_type == "FloatField" or self.field_type == "DecimalField":
            return 3.14
        elif self.field_type == "BooleanField":
            return True
        elif self.field_type == "DateField":
            return "2025-05-02"
        elif self.field_type == "DateTimeField":
            return "2025-05-02T12:30:45Z"
        elif self.field_type == "EmailField":
            return "user@example.com"
        elif self.field_type == "URLField":
            return "https://example.com"
        elif self.field_type == "UUIDField":
            return "123e4567-e89b-12d3-a456-426655440000"
        elif self.field_type == "JSONField":
            return {"key": "value"}
        elif self.field_type == "ForeignKey" or self.field_type == "OneToOneField":
            return 1
        elif self.field_type == "ManyToManyField":
            return [1, 2]
        elif self.choices:
            return self.choices[0][0]
        else:
            return None


@dataclass
class ModelInfo:
    """Information about a Django model."""
    name: str
    app_label: str
    fields: List[FieldInfo] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    has_user_field: bool = False
    has_owner_field: bool = False
    
    @property
    def route_name(self) -> str:
        """Convert model name to URL route name (CamelCase to kebab-case)."""
        return re.sub(r'(?<!^)(?=[A-Z])', '-', self.name).lower()
    
    @property
    def plural_name(self) -> str:
        """Return plural form of the model name for URL routes."""
        # This is a simple pluralization - for production use a proper
        # pluralization library might be better
        if self.name.endswith(('s', 'x', 'z', 'ch', 'sh')):
            return f"{self.name}es"
        elif self.name.endswith('y') and not self.name[-2] in 'aeiou':
            return f"{self.name[:-1]}ies"
        else:
            return f"{self.name}s"
            
    @property
    def api_route(self) -> str:
        """Return the API route for this model."""
        return f"{self.route_name}s"
        
    @property
    def needs_owner_permission(self) -> bool:
        """Check if this model needs owner-based permissions."""
        owner_fields = ('owner', 'user', 'created_by', 'author', 'creator')
        for field in self.fields:
            if field.name in owner_fields:
                return True
        return False
    
    def get_related_models(self) -> List[Tuple[str, str, str]]:
        """Get list of related models as (app, model, field_name) tuples."""
        related = []
        for field in self.fields:
            if field.is_relation and field.related_app and field.related_model:
                related.append((field.related_app, field.related_model, field.name))
        return related
    
    def get_admin_list_display(self, max_fields: int = 5) -> List[str]:
        """Generate a suitable list_display for the admin."""
        display = []
        
        # Always include the primary key
        pk_field = next((f.name for f in self.fields if f.primary_key), None)
        if pk_field:
            display.append(pk_field)
            
        # Add name/title fields if they exist
        common_display_fields = ('name', 'title', 'slug', 'email', 'username')
        for field_name in common_display_fields:
            if field_name in [f.name for f in self.fields] and len(display) < max_fields:
                display.append(field_name)
                
        # Add timestamp fields
        timestamp_fields = ('created_at', 'updated_at', 'date_joined', 'last_modified')
        for field_name in timestamp_fields:
            if field_name in [f.name for f in self.fields] and len(display) < max_fields:
                display.append(field_name)
                
        # Add any string fields until we reach the limit
        for field in self.fields:
            if (field.searchable and field.name not in display and len(display) < max_fields):
                display.append(field.name)
                
        # If we still don't have enough, add other fields
        if len(display) < max_fields:
            for field in self.fields:
                if field.name not in display and not field.many_to_many and len(display) < max_fields:
                    display.append(field.name)
                    
        return display
    
    def get_serializer_fields(self) -> List[str]:
        """Get the list of fields to include in the serializer."""
        # By default include all fields except those that are auto-created
        return [f.name for f in self.fields if not f.auto_created]
        
    def get_search_fields(self) -> List[str]:
        """Get fields suitable for text search."""
        return [f.name for f in self.fields if f.searchable]
        
    def get_filterset_fields(self) -> List[str]:
        """Get fields suitable for filtering."""
        return [f.name for f in self.fields if f.filterable]


@dataclass
class AppInfo:
    """Information about a Django app and its models."""
    label: str
    name: str
    models: List[ModelInfo] = field(default_factory=list)
    
    def get_model_names(self) -> List[str]:
        """Get list of model names in this app."""
        return [m.name for m in self.models]
    
    def get_model_by_name(self, name: str) -> Optional[ModelInfo]:
        """Get a model by its name."""
        for model in self.models:
            if model.name == name:
                return model
        return None


@dataclass
class ProjectInfo:
    """Project-wide information about all apps and their dependencies."""
    apps: List[AppInfo] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    
    def get_app_labels(self) -> List[str]:
        """Get list of app labels."""
        return [a.label for a in self.apps]
    
    def get_app_by_label(self, label: str) -> Optional[AppInfo]:
        """Get an app by its label."""
        for app in self.apps:
            if app.label == label:
                return app
        return None
    
    def get_model_by_path(self, app_label: str, model_name: str) -> Optional[ModelInfo]:
        """Get a model by its app label and name."""
        app = self.get_app_by_label(app_label)
        if app:
            return app.get_model_by_name(model_name)
        return None
    
    def find_dependencies(self, app_label: str) -> List[str]:
        """Find app labels that this app depends on."""
        dependencies = []
        app = self.get_app_by_label(app_label)
        if not app:
            return dependencies
            
        for model in app.models:
            for field in model.fields:
                if field.is_relation and field.related_app and field.related_app != app_label:
                    if field.related_app not in dependencies:
                        dependencies.append(field.related_app)
        
        return dependencies
    
    def find_dependent_apps(self, app_label: str) -> List[str]:
        """Find apps that depend on this app."""
        dependents = []
        
        for app in self.apps:
            if app.label == app_label:
                continue
                
            for model in app.models:
                for field in model.fields:
                    if field.is_relation and field.related_app == app_label:
                        if app.label not in dependents:
                            dependents.append(app.label)
                            break
        
        return dependents
    
    def has_circular_dependencies(self) -> bool:
        """Check if there are circular dependencies between apps."""
        # Build dependency graph
        graph = {}
        for app_label in self.get_app_labels():
            graph[app_label] = self.find_dependencies(app_label)
        
        # Check for cycles using DFS
        visited = set()
        path = set()
        
        def dfs(node):
            if node in path:
                return True  # Found a cycle
                
            if node in visited:
                return False
                
            visited.add(node)
            path.add(node)
            
            for neighbor in graph.get(node, []):
                if dfs(neighbor):
                    return True
                    
            path.remove(node)
            return False
        
        for app_label in graph:
            if dfs(app_label):
                return True
                
        return False
    
    def get_circular_dependencies(self) -> List[List[str]]:
        """Find all circular dependencies between apps."""
        # Build dependency graph
        graph = {}
        for app_label in self.get_app_labels():
            graph[app_label] = self.find_dependencies(app_label)
        
        # Find cycles using Johnson's algorithm
        cycles = []
        
        def find_cycles_from_node(start_node):
            stack = [(start_node, [start_node])]
            while stack:
                node, path = stack.pop()
                
                # Get neighbors
                neighbors = graph.get(node, [])
                
                for neighbor in neighbors:
                    if neighbor == start_node:
                        # Found a cycle
                        cycle = path.copy()
                        cycle.append(neighbor)
                        # Check if this cycle is already in our list (regardless of starting point)
                        cycle_exists = False
                        for existing_cycle in cycles:
                            if set(cycle) == set(existing_cycle):
                                cycle_exists = True
                                break
                        if not cycle_exists:
                            cycles.append(cycle)
                    elif neighbor not in path:
                        new_path = path.copy()
                        new_path.append(neighbor)
                        stack.append((neighbor, new_path))
        
        for app_label in graph:
            find_cycles_from_node(app_label)
            
        return cycles

# ───────────────────────────────────────────────────────────────────────────────
# Django integration - model analysis and introspection
# ───────────────────────────────────────────────────────────────────────────────
def bootstrap_django(settings_module: str):
    """Initialize Django with the given settings module."""
    if "DJANGO_SETTINGS_MODULE" not in os.environ:
        os.environ["DJANGO_SETTINGS_MODULE"] = settings_module
    django.setup()
    logger.info(f"Django initialized with settings module: {os.environ.get('DJANGO_SETTINGS_MODULE')}")


def extract_field_info(field) -> FieldInfo:
    """Extract detailed information about a model field."""
    field_info = FieldInfo(
        name=field.name,
        field_type=field.__class__.__name__,
        null=getattr(field, 'null', False),
        blank=getattr(field, 'blank', False),
        unique=getattr(field, 'unique', False),
        help_text=str(getattr(field, 'help_text', '')),
        verbose_name=str(getattr(field, 'verbose_name', '')),
        is_relation=field.is_relation if hasattr(field, 'is_relation') else False,
        max_length=getattr(field, 'max_length', None),
        editable=getattr(field, 'editable', True),
        primary_key=getattr(field, 'primary_key', False),
        auto_created=getattr(field, 'auto_created', False),
    )
    
    # Handle choices if they exist
    if hasattr(field, 'choices') and field.choices:
        field_info.choices = field.choices
    
    # Handle default value
    if field.has_default():
        default_value = field.get_default()
        # Skip callable defaults which can't be easily represented
        if not callable(default_value):
            field_info.default = default_value
    
    # Handle relation fields
    if field.is_relation:
        field_info.is_relation = True
        related_model = field.related_model
        
        if related_model:
            field_info.related_model = related_model.__name__
            field_info.related_app = related_model._meta.app_label
            
        if hasattr(field, 'remote_field') and hasattr(field.remote_field, 'related_name'):
            field_info.related_name = field.remote_field.related_name
            
        # Set relationship type flags
        if isinstance(field, ManyToManyField):
            field_info.many_to_many = True
        elif isinstance(field, OneToOneField):
            field_info.one_to_one = True
            
    return field_info


def analyze_model(model) -> ModelInfo:
    """Analyze a Django model and return structured information."""
    model_info = ModelInfo(
        name=model.__name__,
        app_label=model._meta.app_label,
        meta={
            'verbose_name': str(model._meta.verbose_name),
            'verbose_name_plural': str(model._meta.verbose_name_plural),
            'ordering': list(model._meta.ordering) if model._meta.ordering else [],
            'unique_together': list(model._meta.unique_together) if model._meta.unique_together else [],
            'abstract': model._meta.abstract,
            'app_label': model._meta.app_label,
            'db_table': model._meta.db_table,
        }
    )
    
    # Analyze fields
    for field in model._meta.get_fields():
        field_info = extract_field_info(field)
        model_info.fields.append(field_info)
        
        # Check for user/owner fields for permission generation
        if field.is_relation and field.related_model:
            if field.related_model.__name__ == 'User' and field.related_model._meta.app_label == 'auth':
                model_info.has_user_field = True
                if field.name in ('owner', 'user', 'author', 'creator', 'created_by'):
                    model_info.has_owner_field = True
    
    return model_info


def collect_project_info(app_labels: Optional[List[str]] = None) -> ProjectInfo:
    """Analyze the Django project structure and return comprehensive information."""
    project_info = ProjectInfo()
    
    # Get selected apps or all apps
    app_configs = []
    if app_labels:
        app_configs = [apps.get_app_config(label) for label in app_labels]
    else:
        app_configs = [app for app in apps.get_app_configs() 
                      if not app.name.startswith('django.') and app.models]
    
    # Analyze each app and its models
    for app_config in app_configs:
        app_info = AppInfo(
            label=app_config.label,
            name=app_config.name
        )
        
        # Skip apps without models
        if not app_config.models:
            continue
            
        # Analyze each model in the app
        for model in app_config.get_models():
            # Skip abstract models
            if model._meta.abstract:
                continue
                
            model_info = analyze_model(model)
            app_info.models.append(model_info)
            
        # Only add apps that have at least one concrete model
        if app_info.models:
            project_info.apps.append(app_info)
    
    # Process relationships between models
    for app_info in project_info.apps:
        for model_info in app_info.models:
            for field in model_info.fields:
                if field.is_relation and field.related_model and field.related_app:
                    relationship = {
                        'from_app': app_info.label,
                        'from_model': model_info.name,
                        'from_field': field.name,
                        'to_app': field.related_app,
                        'to_model': field.related_model,
                        'relationship_type': field.field_type,
                        'many_to_many': field.many_to_many,
                        'one_to_one': field.one_to_one,
                    }
                    project_info.relationships.append(relationship)
    
    return project_info


def check_import_conflicts(project_info: ProjectInfo) -> Dict[str, List[Tuple[str, str]]]:
    """Identify potential import conflicts between apps."""
    conflicts = {}
    
    # Check for apps with models having the same name
    model_map = {}  # Maps model_name -> [(app_label, model)]
    
    for app in project_info.apps:
        for model in app.models:
            if model.name not in model_map:
                model_map[model.name] = []
            model_map[model.name].append((app.label, model.name))
    
    # Record conflicts (same model name in different apps)
    for model_name, instances in model_map.items():
        if len(instances) > 1:
            conflicts[model_name] = instances
    
    return conflicts

# ───────────────────────────────────────────────────────────────────────────────
# Template system
# ───────────────────────────────────────────────────────────────────────────────
def ensure_template_dir(template_dir: str) -> None:
    """Ensure the template directory exists and contains all necessary templates."""
    # Create the template directory if it doesn't exist
    template_path = Path(template_dir)
    template_path.mkdir(exist_ok=True)
    
    # Define all the templates here as a dictionary: filename -> content
    templates = {
        # Serializers template with support for related models
        "serializers.py.j2": """
{{ banner }}
from rest_framework import serializers
{% for import_app, models in model_imports.items() %}
from {{ import_app }}.models import {% for model in models %}{{ model }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endfor %}

{% for model in models %}
class {{ model.name }}Serializer(serializers.ModelSerializer):
    {% for field in model.fields if field.is_relation %}
    {% if field.many_to_many %}
    {{ field.name }} = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    {% elif field.one_to_one %}
    {{ field.name }} = serializers.PrimaryKeyRelatedField(read_only=True)
    {% endif %}
    {% endfor %}
    
    class Meta:
        model = {{ model.name }}
        fields = [
            {% for field_name in model.get_serializer_fields() %}
            '{{ field_name }}',
            {% endfor %}
        ]
        read_only_fields = [
            {% for field in model.fields if field.auto_created or not field.editable %}
            '{{ field.name }}',
            {% endfor %}
        ]

{% endfor %}

{% for model in models %}
class {{ model.name }}DetailSerializer(serializers.ModelSerializer):
    {% for field in model.fields if field.is_relation %}
    {% if field.many_to_many %}
    {{ field.name }} = serializers.SerializerMethodField()
    {% elif field.related_model %}
    {{ field.name }} = serializers.SerializerMethodField()
    {% endif %}
    {% endfor %}

    class Meta:
        model = {{ model.name }}
        fields = [
            {% for field_name in model.get_serializer_fields() %}
            '{{ field_name }}',
            {% endfor %}
        ]
        read_only_fields = [
            {% for field in model.fields if field.auto_created or not field.editable %}
            '{{ field.name }}',
            {% endfor %}
        ]

    {% for field in model.fields if field.is_relation and field.related_model %}
    def get_{{ field.name }}(self, obj):
        {% if field.many_to_many %}
        return [{'id': item.id, 'str': str(item)} for item in obj.{{ field.name }}.all()]
        {% else %}
        related = getattr(obj, '{{ field.name }}', None)
        if related:
            return {'id': related.id, 'str': str(related)}
        return None
        {% endif %}
    {% endfor %}

{% endfor %}
""",

        # Views template with filtering, search, and permissions
        "views.py.j2": """
{{ banner }}
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

{% for import_app, models in model_imports.items() %}
from {{ import_app }}.models import {% for model in models %}{{ model }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endfor %}

from .serializers import {% for model in models %}{{ model.name }}Serializer, {{ model.name }}DetailSerializer, {% endfor %}
{% if needs_custom_permissions %}
from .permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly
{% endif %}

{% for model in models %}
class {{ model.name }}ViewSet(viewsets.ModelViewSet):
    """API endpoint for {{ model.name }} objects."""
    queryset = {{ model.name }}.objects.all()
    serializer_class = {{ model.name }}Serializer
    permission_classes = [
        permissions.IsAuthenticated{% if model.needs_owner_permission %}, 
        IsOwnerOrReadOnly{% endif %}
    ]
    filter_backends = [
        DjangoFilterBackend, 
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = [
        {% for field in model.get_filterset_fields() %}
        '{{ field }}',
        {% endfor %}
    ]
    search_fields = [
        {% for field in model.get_search_fields() %}
        '{{ field }}',
        {% endfor %}
    ]
    ordering_fields = '__all__'

    def get_serializer_class(self):
        """Return different serializers for list vs detail views."""
        if self.action == 'retrieve':
            return {{ model.name }}DetailSerializer
        return {{ model.name }}Serializer
    {% if model.has_owner_field %}

    def perform_create(self, serializer):
        """Set the owner automatically to the current user."""
        serializer.save(owner=self.request.user)
    {% endif %}

{% endfor %}
""",

        # URLs template
        "urls.py.j2": """
{{ banner }}
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = '{{ app_label }}'

router = DefaultRouter()
{% for model in models %}
router.register(r'{{ model.api_route }}', views.{{ model.name }}ViewSet)
{% endfor %}

urlpatterns = [
    path('', include(router.urls)),
]
""",

        # Admin template
        "admin.py.j2": """
{{ banner }}
from django.contrib import admin
{% for import_app, models in model_imports.items() %}
from {{ import_app }}.models import {% for model in models %}{{ model }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endfor %}

{% for model in models %}
@admin.register({{ model.name }})
class {{ model.name }}Admin(admin.ModelAdmin):
    list_display = {{ model.get_admin_list_display() }}
    search_fields = [
        {% for field in model.get_search_fields() %}
        '{{ field }}',
        {% endfor %}
    ]
    list_filter = [
        {% for field in model.fields if field.filterable and not field.many_to_many %}
        {% if loop.index <= 5 %}
        '{{ field.name }}',
        {% endif %}
        {% endfor %}
    ]
    {% if model.meta.get('ordering') %}
    ordering = {{ model.meta.get('ordering') }}
    {% endif %}

{% endfor %}
""",

        # Custom permissions
        "permissions.py.j2": """
{{ banner }}
from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        {% if has_explicit_owner %}
        # Check if the object has an owner attribute
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'author'):
            return obj.author == request.user
        {% else %}
        # Customize this based on your model structure
        return obj.owner == request.user
        {% endif %}
        
        # Default deny
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to modify objects.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to admin users
        return request.user and request.user.is_staff
""",

        # Integration tests
        "tests/test_api.py.j2": """
{{ banner }}
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

{% for import_app, models in model_imports.items() %}
from {{ import_app }}.models import {% for model in models %}{{ model }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endfor %}

pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

{% for model in models %}
class Test{{ model.name }}API:
    """Test the {{ model.name }} API endpoints."""
    
    def test_list(self, api_client):
        """Test retrieving a list of {{ model.name }} objects."""
        url = reverse('{{ app_label }}:{{ model.api_route }}-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
    
    def test_create(self, api_client):
        """Test creating a {{ model.name }} object."""
        url = reverse('{{ app_label }}:{{ model.api_route }}-list')
        # Requires authentication and valid data
        # Uncomment and customize for actual testing
        # data = {
        {% for field in model.fields if not field.auto_created and field.editable and not field.many_to_many %}
        #    '{{ field.name }}': {{ field.get_json_example()|tojson }},
        {% endfor %}
        # }
        # response = api_client.post(url, data, format='json')
        # assert response.status_code == status.HTTP_201_CREATED
    
    def test_detail(self, api_client):
        """Test retrieving a specific {{ model.name }} object."""
        # Create test object first
        # {{ model_name_var }} = {{ model.name }}.objects.create(...)
        # url = reverse('{{ app_label }}:{{ model.api_route }}-detail', args=[{{ model_name_var }}.id])
        # response = api_client.get(url)
        # assert response.status_code == status.HTTP_200_OK

{% endfor %}
""",

        # Model tests
        "tests/test_models.py.j2": """
{{ banner }}
import pytest

{% for import_app, models in model_imports.items() %}
from {{ import_app }}.models import {% for model in models %}{{ model }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endfor %}

pytestmark = pytest.mark.django_db

{% for model in models %}
class Test{{ model.name }}:
    """Test suite for {{ model.name }} model."""
    
    def test_create(self):
        """Test creating a {{ model.name }} instance."""
        # Customize this test with valid model data
        # {{ model_name_var }} = {{ model.name }}.objects.create(
        {% for field in model.fields if field.name != 'id' and not field.auto_created and field.editable and not field.many_to_many and not field.is_relation %}
        #    {{ field.name }}={{ field.get_json_example()|tojson }},
        {% endfor %}
        # )
        # assert {{ model_name_var }}.id is not None
    
    def test_string_representation(self):
        """Test the string representation of {{ model.name }}."""
        # {{ model_name_var }} = {{ model.name }}.objects.create(...)
        # assert str({{ model_name_var }}) == '...'

{% endfor %}
""",

        # Signals template
        "signals.py.j2": """
{{ banner }}
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
{% for import_app, models in model_imports.items() %}
from {{ import_app }}.models import {% for model in models %}{{ model }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endfor %}

{% for model in models %}
@receiver(post_save, sender={{ model.name }})
def {{ model.name.lower() }}_post_save(sender, instance, created, **kwargs):
    """Handle post-save operations for {{ model.name }}."""
    if created:
        # Add logic for newly created objects
        pass
    else:
        # Add logic for updated objects
        pass

{% endfor %}
""",

        # API Documentation
        "api_docs.md.j2": """
# API Documentation
_Generated: {{ timestamp }}_

## Overview

This document provides a comprehensive guide to the API endpoints available in this project.
Use it as a reference for frontend development.

{% for app in apps %}
## {{ app.name|capitalize }} API
{% for model in app.models %}
### {{ model.name }}

**Endpoint**: `/{{ api_base_url }}/{{ model.api_route }}/`

#### Fields

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
{% for field in model.fields %}
| `{{ field.name }}` | {{ field.field_type }} | {{ "Yes" if not field.null else "No" }} | {{ "Yes" if field.unique else "No" }} | {{ field.help_text or field.verbose_name }} |
{% endfor %}

#### Operations

- `GET /{{ api_base_url }}/{{ model.api_route }}/` - List all {{ model.name }} objects
- `POST /{{ api_base_url }}/{{ model.api_route }}/` - Create a new {{ model.name }}
- `GET /{{ api_base_url }}/{{ model.api_route }}/{id}/` - Retrieve a specific {{ model.name }}
- `PUT /{{ api_base_url }}/{{ model.api_route }}/{id}/` - Update a {{ model.name }}
- `DELETE /{{ api_base_url }}/{{ model.api_route }}/{id}/` - Delete a {{ model.name }}

#### Example Response

```json
{
    {% for field in model.fields %}
    "{{ field.name }}": {{ field.get_json_example()|tojson }}{% if not loop.last %},{% endif %}
    {% endfor %}
}