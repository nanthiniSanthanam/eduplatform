#!/usr/bin/env python3
"""
Frontend-Backend Analysis Tool

This script analyzes a React/Vite frontend codebase to extract information relevant 
to a Django/PostgreSQL backend. It generates a comprehensive report detailing:
1. Backend Data Requirements - Models, APIs, fields, relationships
2. Continuity Analysis - Compatibility issues, naming inconsistencies

Usage: python frontend_backend_analyzer.py --frontend-dir <frontend_directory> --output <report_file.md>
"""

import os
import re
import json
import argparse
import glob
from collections import defaultdict
import ast
from typing import Dict, List, Set, Tuple, Any
import markdown
import networkx as nx
from dataclasses import dataclass, field

# ---- Data Classes for storing extracted information ----

@dataclass
class APIEndpoint:
    """Represents an API endpoint found in frontend code"""
    url: str
    method: str = "GET"
    file_locations: List[str] = field(default_factory=list)
    params: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    response_fields: Set[str] = field(default_factory=set)
    components: List[str] = field(default_factory=list)
    
    def __hash__(self):
        return hash(self.url)

@dataclass
class DataModel:
    """Represents an inferred data model from frontend usage"""
    name: str
    fields: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    relationships: Dict[str, str] = field(default_factory=dict)
    file_locations: List[str] = field(default_factory=list)
    api_endpoints: Set[str] = field(default_factory=set)
    
    def __hash__(self):
        return hash(self.name)

@dataclass
class Component:
    """Represents a React component"""
    name: str
    file_path: str
    props: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    state_vars: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    api_calls: Set[str] = field(default_factory=set)
    imports: List[str] = field(default_factory=list)
    
    def __hash__(self):
        return hash(f"{self.name}:{self.file_path}")

@dataclass
class NamingIssue:
    """Represents a naming inconsistency or issue"""
    type: str
    description: str
    location: str
    severity: str = "medium"  # low, medium, high
    suggestion: str = ""

# ---- Main Analyzer Class ----

class FrontendBackendAnalyzer:
    """Main analyzer class that processes frontend files and generates a report"""
    
    # Common patterns for identifying API requests
    API_PATTERNS = [
        r'(?:axios|fetch)\s*\.\s*(?:get|post|put|delete|patch)\s*\(\s*[\'"`](.*?)[\'"`]',
        r'(?:axios|fetch)\s*\(\s*[\'"`](.*?)[\'"`]',
        r'(?:axios|fetch)\s*\(\s*{\s*url\s*:\s*[\'"`](.*?)[\'"`]',
        r'const\s+\w+\s*=\s*await\s+(?:axios|fetch)\s*\(\s*[\'"`](.*?)[\'"`]',
    ]
    
    # Patterns for identifying data structures
    MODEL_PATTERNS = [
        r'(?:interface|type)\s+(\w+)\s*{([^}]*)}',
        r'const\s+\[?(\w+)(?:,\s*set\w+)?\]?\s*=\s*(?:useState|useReducer)',
        r'class\s+(\w+)\s+(?:extends|implements)',
    ]
    
    def __init__(self, frontend_dir: str):
        self.frontend_dir = os.path.abspath(frontend_dir)
        self.api_endpoints = set()
        self.data_models = {}
        self.components = {}
        self.naming_issues = []
        self.graph = nx.DiGraph()
        
    def analyze(self):
        """Main analysis entry point"""
        print(f"Analyzing frontend code in: {self.frontend_dir}")
        
        # Find all JS/JSX files
        js_files = self.find_js_files()
        print(f"Found {len(js_files)} JavaScript/JSX files to analyze")
        
        # Process each file
        for file_path in js_files:
            self.process_file(file_path)
        
        # Build relationships between components and models
        self.build_relationships()
        
        # Find naming inconsistencies and other issues
        self.check_naming_consistency()
        
        print(f"Analysis complete:")
        print(f"- {len(self.api_endpoints)} API endpoints identified")
        print(f"- {len(self.data_models)} data models inferred")
        print(f"- {len(self.components)} React components analyzed")
        print(f"- {len(self.naming_issues)} naming/consistency issues found")
    
    def find_js_files(self) -> List[str]:
        """Find all JavaScript and JSX files in the frontend directory"""
        js_files = []
        for ext in ['js', 'jsx', 'ts', 'tsx']:
            pattern = os.path.join(self.frontend_dir, '**', f'*.{ext}')
            js_files.extend(glob.glob(pattern, recursive=True))
        
        # Exclude node_modules, build directories, and test files
        excluded_patterns = ['node_modules', 'dist', 'build', '.test.', '.spec.']
        filtered_files = []
        
        for file_path in js_files:
            if not any(pattern in file_path for pattern in excluded_patterns):
                filtered_files.append(file_path)
                
        return filtered_files
    
    def process_file(self, file_path: str):
        """Process a single JavaScript/JSX file"""
        rel_path = os.path.relpath(file_path, self.frontend_dir)
        component_name = self.extract_component_name(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract component information
            if component_name:
                component = Component(
                    name=component_name,
                    file_path=rel_path
                )
                
                # Extract imports
                component.imports = self.extract_imports(content)
                
                # Extract props and state
                component.props = self.extract_props(content)
                component.state_vars = self.extract_state(content)
                
                self.components[component_name] = component
                
            # Extract API endpoints
            self.extract_api_endpoints(content, rel_path, component_name)
            
            # Extract data models/structures
            self.extract_data_models(content, rel_path, component_name)
            
        except Exception as e:
            print(f"Error processing file {rel_path}: {str(e)}")
    
    def extract_component_name(self, file_path: str) -> str:
        """Extract React component name from file path or content"""
        # First try from filename (common convention)
        base_name = os.path.basename(file_path)
        name, _ = os.path.splitext(base_name)
        
        # PascalCase convention for components
        if name[0].isupper():
            return name
        
        # Try to read file to find component name
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for component definition patterns
            patterns = [
                r'function\s+([A-Z]\w+)\s*\(',
                r'const\s+([A-Z]\w+)\s*=',
                r'class\s+([A-Z]\w+)\s+extends',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content)
                if match and match.group(1)[0].isupper():
                    return match.group(1)
        except:
            pass
            
        # Fallback: use filename with first letter capitalized
        return name[0].upper() + name[1:] if name else ""
    
    def extract_imports(self, content: str) -> List[str]:
        """Extract import statements from file content"""
        imports = []
        import_pattern = r'import\s+(?:{[^}]*}|[^\s;]+)\s+from\s+[\'"]([^\'"]*)[\'"]'
        
        for match in re.finditer(import_pattern, content):
            imports.append(match.group(1))
            
        return imports
    
    def extract_props(self, content: str) -> Dict[str, Set[str]]:
        """Extract component props from file content"""
        props = defaultdict(set)
        
        # Extract props from destructuring patterns
        prop_patterns = [
            r'function\s+\w+\s*\(\s*{\s*([^}]*)\s*}\s*\)',
            r'const\s+\w+\s*=\s*\(\s*{\s*([^}]*)\s*}\s*\)',
            r'const\s+{\s*([^}]*)\s*}\s*=\s*props',
        ]
        
        for pattern in prop_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                for prop in re.split(r',\s*', match):
                    prop = prop.strip()
                    if prop and not prop.startswith('//'):
                        # Handle default values and typing
                        prop_name = prop.split('=')[0].split(':')[0].strip()
                        if prop_name:
                            prop_type = "unknown"
                            type_match = re.search(r':\s*(\w+)', prop)
                            if type_match:
                                prop_type = type_match.group(1)
                            props[prop_name].add(prop_type)
        
        # Look for propTypes definitions
        prop_types_pattern = r'(\w+)\.propTypes\s*=\s*{\s*([^}]*)\s*}'
        matches = re.findall(prop_types_pattern, content)
        for match in matches:
            component_name, prop_types_str = match
            for prop_line in prop_types_str.split(','):
                if ':' in prop_line:
                    prop_name = prop_line.split(':')[0].strip()
                    prop_type = prop_line.split(':')[1].strip()
                    if prop_name:
                        props[prop_name].add(prop_type)
        
        return props
    
    def extract_state(self, content: str) -> Dict[str, Set[str]]:
        """Extract component state variables from file content"""
        state_vars = defaultdict(set)
        
        # Extract useState hooks
        use_state_pattern = r'const\s+\[(\w+),\s*set(\w+)\]\s*=\s*useState\(\s*(.*?)\s*\)'
        for match in re.finditer(use_state_pattern, content):
            var_name = match.group(1)
            initial_value = match.group(3)
            
            var_type = "unknown"
            if initial_value == '[]':
                var_type = "array"
            elif initial_value == '{}':
                var_type = "object"
            elif initial_value in ['true', 'false']:
                var_type = "boolean"
            elif initial_value.isdigit() or (initial_value and initial_value[0] == '-' and initial_value[1:].isdigit()):
                var_type = "number"
            elif initial_value.startswith('"') or initial_value.startswith("'"):
                var_type = "string"
                
            state_vars[var_name].add(var_type)
        
        # Extract useReducer state
        reducer_pattern = r'const\s+\[(\w+),\s*\w+\]\s*=\s*useReducer\(\s*\w+,\s*({[^}]*})'
        for match in re.finditer(reducer_pattern, content):
            state_name = match.group(1)
            initial_state = match.group(2)
            
            # Try to extract object structure
            field_pattern = r'(\w+):\s*([^,}]+)'
            for field_match in re.finditer(field_pattern, initial_state):
                field_name = field_match.group(1)
                field_value = field_match.group(2).strip()
                
                field_type = "unknown"
                if field_value == '[]':
                    field_type = "array"
                elif field_value == '{}':
                    field_type = "object"
                elif field_value in ['true', 'false']:
                    field_type = "boolean"
                elif field_value.isdigit():
                    field_type = "number"
                elif field_value.startswith('"') or field_value.startswith("'"):
                    field_type = "string"
                    
                state_vars[f"{state_name}.{field_name}"].add(field_type)
        
        return state_vars
    
    def extract_api_endpoints(self, content: str, file_path: str, component_name: str):
        """Extract API endpoints from file content"""
        for pattern in self.API_PATTERNS:
            for match in re.finditer(pattern, content):
                url = match.group(1)
                
                # Skip relative URLs like './something.json'
                if url.startswith('./') or url.startswith('../'):
                    continue
                
                # Normalize URL by stripping http(s) and domain
                normalized_url = re.sub(r'^https?://[^/]+', '', url)
                
                # Extract HTTP method
                method = "GET"  # Default
                method_match = re.search(r'\.(get|post|put|delete|patch)', match.group(0).lower())
                if method_match:
                    method = method_match.group(1).upper()
                
                # Find or create API endpoint
                endpoint = next((ep for ep in self.api_endpoints if ep.url == normalized_url and ep.method == method), None)
                if not endpoint:
                    endpoint = APIEndpoint(url=normalized_url, method=method)
                    self.api_endpoints.add(endpoint)
                
                # Record file location
                if file_path not in endpoint.file_locations:
                    endpoint.file_locations.append(file_path)
                
                # Record component
                if component_name and component_name not in endpoint.components:
                    endpoint.components.append(component_name)
                
                # Update component's API calls
                if component_name and component_name in self.components:
                    self.components[component_name].api_calls.add(normalized_url)
                
                # Try to extract request params and response fields
                self.extract_request_response_details(content, match.start(), endpoint)
    
    def extract_request_response_details(self, content: str, position: int, endpoint: APIEndpoint):
        """Extract request parameters and response fields for an API endpoint"""
        # Look for request data in the 100 chars after the API call
        request_context = content[position:position+200]
        
        # Extract request parameters
        data_patterns = [
            r'data:\s*({[^}]*})',
            r'params:\s*({[^}]*})',
            r'body:\s*JSON\.stringify\(({[^}]*})\)',
        ]
        
        for pattern in data_patterns:
            data_match = re.search(pattern, request_context)
            if data_match:
                data_obj = data_match.group(1)
                field_pattern = r'(\w+):\s*([^,}]+)'
                for field_match in re.finditer(field_pattern, data_obj):
                    param_name = field_match.group(1)
                    param_value = field_match.group(2).strip()
                    
                    param_type = "unknown"
                    if param_value == '[]':
                        param_type = "array"
                    elif param_value == '{}':
                        param_type = "object"
                    elif param_value in ['true', 'false']:
                        param_type = "boolean"
                    elif param_value.isdigit():
                        param_type = "number"
                    elif param_value.startswith('"') or param_value.startswith("'"):
                        param_type = "string"
                    
                    endpoint.params[param_name].add(param_type)
        
        # Look for response processing after the API call
        response_context = content[position:position+500]
        
        # Look for destructuring of response data
        response_patterns = [
            r'const\s+{\s*(.*?)\s*}\s*=\s*(?:response|res|data|result)',
            r'(?:response|res|data|result)\.(\w+)',
            r'setData\(\s*response\.data\s*\)',
        ]
        
        for pattern in response_patterns:
            for resp_match in re.finditer(pattern, response_context):
                if resp_match.group(1):
                    for field in re.split(r',\s*', resp_match.group(1)):
                        field = field.strip()
                        if field and not field.startswith('//'):
                            # Handle renaming during destructuring
                            field_name = field.split(':')[0].strip()
                            endpoint.response_fields.add(field_name)
    
    def extract_data_models(self, content: str, file_path: str, component_name: str):
        """Extract data models/structures from file content"""
        # Look for TypeScript interfaces/types
        interface_pattern = r'(?:interface|type)\s+(\w+)(?:\s+extends\s+(\w+))?\s*{([^}]*)}'
        for match in re.finditer(interface_pattern, content):
            model_name = match.group(1)
            parent_model = match.group(2)
            fields_str = match.group(3)
            
            # Create or update model
            if model_name not in self.data_models:
                self.data_models[model_name] = DataModel(name=model_name)
            
            model = self.data_models[model_name]
            
            # Record file location
            if file_path not in model.file_locations:
                model.file_locations.append(file_path)
                
            # Record parent relationship
            if parent_model:
                model.relationships[parent_model] = "extends"
            
            # Extract fields
            field_pattern = r'(\w+)\s*(?::\s*([^;,]+))?'
            for field_match in re.finditer(field_pattern, fields_str):
                field_name = field_match.group(1)
                field_type = field_match.group(2).strip() if field_match.group(2) else "any"
                model.fields[field_name].add(field_type)
        
        # Look for object destructuring patterns that might indicate models
        destruct_pattern = r'const\s+{\s*(.*?)\s*}\s*=\s*(\w+)'
        for match in re.finditer(destruct_pattern, content):
            fields_str = match.group(1)
            obj_name = match.group(2)
            
            # Skip common non-model variable names
            if obj_name in ['props', 'state', 'event', 'e', 'options']:
                continue
                
            # Create or update model
            if obj_name not in self.data_models:
                self.data_models[obj_name] = DataModel(name=obj_name)
                
            model = self.data_models[obj_name]
            
            # Record file location
            if file_path not in model.file_locations:
                model.file_locations.append(file_path)
                
            # Extract fields
            for field in re.split(r',\s*', fields_str):
                field = field.strip()
                if field and not field.startswith('//'):
                    # Handle renaming during destructuring
                    parts = field.split(':')
                    field_name = parts[0].strip()
                    model.fields[field_name].add("unknown")
    
    def build_relationships(self):
        """Build relationships between components, models, and API endpoints"""
        # Connect components based on imports
        for component_name, component in self.components.items():
            self.graph.add_node(component_name, type="component")
            
            # Look for imports of other components
            for imp in component.imports:
                # Extract component name from import path
                imported_name = os.path.basename(imp).split('.')[0]
                imported_name = imported_name[0].upper() + imported_name[1:] if imported_name else ""
                
                if imported_name in self.components:
                    self.graph.add_edge(component_name, imported_name, type="imports")
        
        # Connect models to API endpoints
        for endpoint in self.api_endpoints:
            endpoint_key = f"{endpoint.method}:{endpoint.url}"
            self.graph.add_node(endpoint_key, type="endpoint")
            
            # Connect to components that use this endpoint
            for component_name in endpoint.components:
                if component_name in self.components:
                    self.graph.add_edge(component_name, endpoint_key, type="calls")
            
            # Try to infer model from endpoint
            parts = endpoint.url.strip('/').split('/')
            if parts:
                # Try to infer model name (usually last non-parameter part of URL)
                model_candidates = []
                for part in parts:
                    if not part.startswith(':') and not part.startswith('{'):
                        # Convert plural to singular and snake_case to PascalCase
                        singular = part[:-1] if part.endswith('s') else part
                        pascal_case = ''.join(w.capitalize() for w in re.split(r'[-_]', singular))
                        model_candidates.append(pascal_case)
                
                # Connect endpoint to potential models
                for model_name in self.data_models:
                    if model_name in model_candidates or any(model_name.lower() in c.lower() for c in model_candidates):
                        self.graph.add_edge(endpoint_key, model_name, type="references")
                        self.data_models[model_name].api_endpoints.add(endpoint.url)
    
    def check_naming_consistency(self):
        """Find naming inconsistencies and other potential issues"""
        # Check for snake_case vs camelCase inconsistencies in API endpoints
        url_format_patterns = {
            'snake_case': r'_\w',
            'camelCase': r'[a-z][A-Z]',
            'kebab-case': r'-\w',
        }
        
        url_formats = defaultdict(set)
        for endpoint in self.api_endpoints:
            for format_name, pattern in url_format_patterns.items():
                if re.search(pattern, endpoint.url):
                    url_formats[format_name].add(endpoint.url)
        
        # If multiple formats are used, flag as inconsistency
        if len(url_formats) > 1:
            formats_str = ', '.join(url_formats.keys())
            self.naming_issues.append(NamingIssue(
                type="API URL Format",
                description=f"Inconsistent URL formats used: {formats_str}",
                location="API Endpoints",
                severity="medium",
                suggestion="Standardize on one URL format for all API endpoints"
            ))
            
        # Check for inconsistencies between model names and endpoint URLs
        for model_name, model in self.data_models.items():
            model_snake = ''.join('_' + c.lower() if c.isupper() else c.lower() for c in model_name).lstrip('_')
            model_plural = model_snake + 's'
            
            for endpoint in self.api_endpoints:
                if model_plural in endpoint.url:
                    # Check if fields referenced in API match model fields
                    for param in endpoint.params:
                        if param not in model.fields:
                            self.naming_issues.append(NamingIssue(
                                type="Field Mismatch",
                                description=f"API param '{param}' not found in model '{model_name}'",
                                location=f"Endpoint {endpoint.url}",
                                severity="high",
                                suggestion=f"Add '{param}' field to {model_name} model or update API"
                            ))
        
        # Check for inconsistent field naming patterns within models
        for model_name, model in self.data_models.items():
            camel_case_count = 0
            snake_case_count = 0
            
            for field in model.fields:
                if '_' in field:
                    snake_case_count += 1
                elif field and field[0].islower() and any(c.isupper() for c in field):
                    camel_case_count += 1
            
            if camel_case_count > 0 and snake_case_count > 0:
                self.naming_issues.append(NamingIssue(
                    type="Field Naming",
                    description=f"Mixed camelCase and snake_case fields in model '{model_name}'",
                    location=f"Model {model_name}",
                    severity="medium",
                    suggestion="Standardize on one naming convention for all fields"
                ))
    
    def generate_report(self, output_file: str = "frontend_backend_report.md"):
        """Generate a markdown report with the analysis results"""
        report = []
        
        # Header
        report.append("# Frontend-Backend Analysis Report")
        report.append(f"\nGenerated from: `{self.frontend_dir}`\n")
        
        # Section 1: Backend Data
        report.append("## 1. Backend Data")
        
        # Data Models
        report.append("\n### 1.1 Data Models")
        if self.data_models:
            for model_name, model in sorted(self.data_models.items()):
                report.append(f"\n#### {model_name}")
                
                # Model fields
                if model.fields:
                    report.append("\n**Fields:**\n")
                    report.append("| Field | Types | Used In |")
                    report.append("|-------|-------|---------|")
                    
                    for field_name, types in sorted(model.fields.items()):
                        types_str = ", ".join(sorted(types))
                        
                        # Find where this field is used
                        used_in = []
                        for endpoint in self.api_endpoints:
                            if field_name in endpoint.params or field_name in endpoint.response_fields:
                                used_in.append(f"`{endpoint.method} {endpoint.url}`")
                        
                        used_str = "<br>".join(used_in) if used_in else "-"
                        report.append(f"| {field_name} | {types_str} | {used_str} |")
                
                # Model relationships
                if model.relationships:
                    report.append("\n**Relationships:**\n")
                    for related_model, rel_type in sorted(model.relationships.items()):
                        report.append(f"- {rel_type} `{related_model}`")
                
                # Associated API endpoints
                if model.api_endpoints:
                    report.append("\n**API Endpoints:**\n")
                    for endpoint in sorted(model.api_endpoints):
                        report.append(f"- `{endpoint}`")
                
                # File locations
                if model.file_locations:
                    report.append("\n**Referenced in:**\n")
                    for location in sorted(model.file_locations):
                        report.append(f"- `{location}`")
        else:
            report.append("\nNo data models could be inferred from the frontend code.\n")
        
        # API Endpoints
        report.append("\n### 1.2 API Endpoints")
        if self.api_endpoints:
            endpoints_by_prefix = defaultdict(list)
            
            # Group endpoints by prefix for better organization
            for endpoint in sorted(self.api_endpoints, key=lambda e: e.url):
                parts = endpoint.url.strip('/').split('/')
                prefix = parts[0] if parts else ""
                endpoints_by_prefix[prefix].append(endpoint)
            
            for prefix, endpoints in sorted(endpoints_by_prefix.items()):
                if prefix:
                    report.append(f"\n#### /{prefix}\n")
                else:
                    report.append("\n#### Root Endpoints\n")
                
                for endpoint in endpoints:
                    report.append(f"##### `{endpoint.method} {endpoint.url}`\n")
                    
                    # Request parameters
                    if endpoint.params:
                        report.append("**Request Parameters:**\n")
                        report.append("| Parameter | Types |")
                        report.append("|-----------|-------|")
                        
                        for param, types in sorted(endpoint.params.items()):
                            types_str = ", ".join(sorted(types))
                            report.append(f"| {param} | {types_str} |")
                        
                        report.append("")
                    
                    # Response fields
                    if endpoint.response_fields:
                        report.append("**Response Fields:**\n")
                        report.append("- " + "\n- ".join(sorted(endpoint.response_fields)))
                        report.append("")
                    
                    # Components using this endpoint
                    if endpoint.components:
                        report.append("**Used in Components:**\n")
                        report.append("- " + "\n- ".join(sorted(endpoint.components)))
                        report.append("")
                    
                    # File locations
                    if endpoint.file_locations:
                        report.append("**Referenced in:**\n")
                        report.append("- " + "\n- ".join(sorted(endpoint.file_locations)))
                        report.append("")
        else:
            report.append("\nNo API endpoints were found in the frontend code.\n")
        
        # URL Patterns
        report.append("\n### 1.3 URL Patterns")
        all_urls = [endpoint.url for endpoint in self.api_endpoints]
        if all_urls:
            url_patterns = self.extract_url_patterns(all_urls)
            report.append("\nBased on the API endpoints found, the following Django URL pattern structure is suggested:\n")
            report.append("```python")
            report.append("# urls.py")
            report.append("from django.urls import path, include")
            report.append("\nurlpatterns = [")
            
            for pattern in url_patterns:
                report.append(f"    {pattern}")
                
            report.append("]")
            report.append("```")
        else:
            report.append("\nNo URL patterns could be inferred from the frontend code.\n")

        # Suggested Models
        report.append("\n### 1.4 Suggested Django Models")
        if self.data_models:
            report.append("\nBased on the data structures found in the frontend, here are suggested Django model definitions:\n")
            report.append("```python")
            report.append("# models.py")
            report.append("from django.db import models\n")
            
            # Sort models to put base models first
            sorted_models = []
            model_deps = {model_name: set(model.relationships.keys()) 
                         for model_name, model in self.data_models.items()}
            
            while model_deps:
                # Find models with no dependencies or dependencies already processed
                independent = [m for m, deps in model_deps.items()
                              if not deps or deps.issubset(set(m.name for m in sorted_models))]
                
                if not independent:
                    # Handle circular dependencies
                    independent = [next(iter(model_deps.keys()))]
                    
                for model_name in independent:
                    if model_name in self.data_models:
                        sorted_models.append(self.data_models[model_name])
                    model_deps.pop(model_name, None)
            
            # Generate model code
            for model in sorted_models:
                report.append(f"class {model.name}(models.Model):")
                
                if not model.fields:
                    report.append("    # No fields could be inferred")
                    report.append("    pass\n")
                    continue
                    
                for field_name, types in sorted(model.fields.items()):
                    field_type = next(iter(types)) if types else "unknown"
                    django_field = self.get_django_field_type(field_type, field_name)
                    report.append(f"    {field_name} = {django_field}")
                
                report.append("")
                report.append("    def __str__(self):")
                report.append(f"        return str(self.id)  # Consider using a name field if available")
                report.append("")
            
            report.append("```")
        else:
            report.append("\nNo Django models could be inferred from the frontend code.\n")
        
        # Section 2: Continuity and Connectivity
        report.append("\n## 2. Continuity and Connectivity")
        
        # Naming Issues
        report.append("\n### 2.1 Naming Consistency Issues")
        if self.naming_issues:
            report.append("\n| Type | Description | Location | Severity | Suggestion |")
            report.append("|------|-------------|----------|----------|------------|")
            
            for issue in sorted(self.naming_issues, key=lambda i: i.severity):
                severity_marker = {
                    "high": "🔴",
                    "medium": "🟠",
                    "low": "🟡"
                }.get(issue.severity, "")
                
                report.append(f"| {issue.type} | {issue.description} | {issue.location} | {severity_marker} {issue.severity} | {issue.suggestion} |")
        else:
            report.append("\nNo naming consistency issues were found.\n")
        
        # Component Relationships
        report.append("\n### 2.2 Component Relationships")
        if self.components:
            report.append("\nThe following diagram shows the relationships between components and API endpoints:\n")
            
            report.append("```")
            report.append("Component Hierarchy:")
            
            # Build simplified tree
            top_level = [node for node in self.graph.nodes if self.graph.in_degree(node) == 0 and node in self.components]
            if not top_level and self.components:
                # If no clear top level, just use components with fewest dependencies
                top_level = sorted(self.components.keys(), 
                                  key=lambda n: self.graph.in_degree(n))[:3]
            
            for i, component in enumerate(sorted(top_level)):
                self._print_component_tree(component, "", i == len(top_level) - 1, report, set())
            
            report.append("```")
            
            # API usage statistics
            report.append("\n**API Usage by Component:**\n")
            report.append("| Component | API Endpoints Used |")
            report.append("|-----------|-------------------|")
            
            for component_name, component in sorted(self.components.items()):
                if component.api_calls:
                    api_list = "<br>".join(f"`{api}`" for api in sorted(component.api_calls))
                    report.append(f"| {component_name} | {api_list} |")
        else:
            report.append("\nNo component relationships could be inferred.\n")
        
        # Data Flow Analysis
        report.append("\n### 2.3 Data Flow Analysis")
        if self.api_endpoints and self.data_models:
            report.append("\n**Data Flow Diagram:**\n")
            
            report.append("```")
            report.append("Frontend Components → API Endpoints → Backend Models")
            report.append("")
            
            # Group endpoints by model they likely affect
            model_endpoints = defaultdict(list)
            for endpoint in self.api_endpoints:
                endpoint_key = f"{endpoint.method} {endpoint.url}"
                
                # Try to associate endpoint with models
                assigned = False
                for model_name, model in self.data_models.items():
                    model_snake = ''.join('_' + c.lower() if c.isupper() else c.lower() for c in model_name).lstrip('_')
                    if model_snake in endpoint.url or model_name.lower() in endpoint.url.lower():
                        model_endpoints[model_name].append(endpoint_key)
                        assigned = True
                
                if not assigned:
                    model_endpoints["Other"].append(endpoint_key)
            
            # Print model-endpoint relationships
            for model_name, endpoints in sorted(model_endpoints.items()):
                report.append(f"{model_name}:")
                for endpoint in sorted(endpoints):
                    report.append(f"  ← {endpoint}")
                report.append("")
                
            report.append("```")
        else:
            report.append("\nInsufficient data to generate data flow analysis.\n")
        
        # Recommendations
        report.append("\n### 2.4 Recommendations")
        
        # Generate general recommendations
        recommendations = [
            "Ensure consistent naming conventions between frontend and backend",
            "Implement proper error handling for all API endpoints",
            "Add authentication middleware for protected endpoints",
            "Use Django serializers that match the frontend data structures",
            "Implement proper validation for all incoming data"
        ]
        
        # Add model-specific recommendations
        for model_name, model in self.data_models.items():
            if len(model.fields) > 10:
                recommendations.append(f"Consider breaking down the {model_name} model as it has many fields")
        
        # Add API-specific recommendations
        http_method_counts = defaultdict(int)
        for endpoint in self.api_endpoints:
            http_method_counts[endpoint.method] += 1
            
        if http_method_counts.get("GET", 0) > 0 and http_method_counts.get("POST", 0) == 0:
            recommendations.append("The frontend only uses GET requests - ensure proper data modification methods are implemented")
            
        report.append("\n".join(f"- {recommendation}" for recommendation in recommendations))
        
        # Write report to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(report))
            
        print(f"Report generated: {output_file}")
        
        return output_file
    
    def _print_component_tree(self, node: str, prefix: str, is_last: bool, report: List[str], visited: Set[str]):
        """Helper to print component tree structure"""
        if node in visited:
            report.append(f"{prefix}{'└── ' if is_last else '├── '}{node} (circular reference)")
            return
            
        visited.add(node)
        report.append(f"{prefix}{'└── ' if is_last else '├── '}{node}")
        
        # Get children that are components
        children = [n for n in self.graph.neighbors(node) 
                   if n in self.components and n != node]
        
        if not children:
            return
            
        new_prefix = prefix + ('    ' if is_last else '│   ')
        for i, child in enumerate(sorted(children)):
            self._print_component_tree(
                child, new_prefix, i == len(children) - 1, report, visited.copy()
            )
    
    def extract_url_patterns(self, urls: List[str]) -> List[str]:
        """Extract Django URL patterns from API endpoint URLs"""
        patterns = []
        url_groups = defaultdict(list)
        
        # Group URLs by first path segment
        for url in urls:
            parts = url.strip('/').split('/')
            if parts:
                prefix = parts[0]
                url_groups[prefix].append(url)
            else:
                url_groups["root"].append(url)
        
        # Generate patterns
        for prefix, group_urls in sorted(url_groups.items()):
            if prefix == "root" or not prefix:
                for url in group_urls:
                    pattern = self._url_to_django_pattern(url)
                    patterns.append(f"path('{pattern[0]}', views.{pattern[1]}),")
            else:
                patterns.append(f"path('{prefix}/', include('{prefix}.urls')),")
        
        return patterns
    
    def _url_to_django_pattern(self, url: str) -> Tuple[str, str]:
        """Convert an API URL to a Django URL pattern and view name"""
        parts = url.strip('/').split('/')
        pattern_parts = []
        param_names = []
        
        for part in parts:
            # Check if this part is a parameter (e.g., :id, {id}, etc.)
            if part.startswith(':') or (part.startswith('{') and part.endswith('}')):
                param_name = part.strip(':{}')
                pattern_parts.append(f'<{param_name}>')
                param_names.append(param_name)
            else:
                pattern_parts.append(part)
        
        pattern = '/'.join(pattern_parts)
        
        # Generate a view name based on the URL pattern
        if not parts:
            view_name = "index"
        else:
            # Use the last non-parameter part as the base name
            base_parts = [p for p in parts if not (p.startswith(':') or (p.startswith('{') and p.endswith('}')))]
            view_base = base_parts[-1] if base_parts else parts[0].strip(':{}')
            
            # Add parameter indicators
            if param_names:
                view_name = f"{view_base}_detail"
            else:
                view_name = f"{view_base}_list"
        
        return pattern, view_name
    
    def get_django_field_type(self, field_type: str, field_name: str) -> str:
        """Convert a JavaScript/TypeScript type to a Django model field type"""
        field_name = field_name.lower()
        
        # Handle common field name patterns
        if field_name == 'id' or field_name.endswith('_id'):
            return "models.AutoField(primary_key=True)" if field_name == 'id' else "models.IntegerField()"
            
        if field_name in ['created_at', 'updated_at', 'created', 'modified', 'date_created']:
            return "models.DateTimeField(auto_now_add=True)" if 'created' in field_name else "models.DateTimeField(auto_now=True)"
            
        if field_name in ['is_active', 'is_deleted', 'active', 'enabled', 'published']:
            return "models.BooleanField(default=True)"
            
        # Handle types
        if field_type in ['string', 'String']:
            if any(kw in field_name for kw in ['description', 'content', 'text', 'body']):
                return "models.TextField()"
            elif any(kw in field_name for kw in ['email']):
                return "models.EmailField(max_length=255)"
            elif any(kw in field_name for kw in ['url', 'link', 'website']):
                return "models.URLField(max_length=255)"
            else:
                return "models.CharField(max_length=255)"
                
        elif field_type in ['number', 'Number', 'int', 'integer', 'Integer']:
            return "models.IntegerField()"
            
        elif field_type in ['float', 'Float', 'double', 'Double']:
            return "models.FloatField()"
            
        elif field_type in ['boolean', 'Boolean', 'bool']:
            return "models.BooleanField(default=False)"
            
        elif field_type in ['Date', 'date']:
            return "models.DateField()"
            
        elif field_type in ['DateTime', 'datetime']:
            return "models.DateTimeField()"
            
        elif field_type in ['array', 'Array', '[]']:
            return "models.JSONField()"
            
        elif field_type in ['object', 'Object', '{}']:
            return "models.JSONField()"
            
        else:
            # Default
            return "models.CharField(max_length=255)  # Type not determined"


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Frontend-Backend Analysis Tool')
    parser.add_argument('--frontend-dir', '-f', required=True, help='Frontend directory path')
    parser.add_argument('--output', '-o', default='frontend_backend_report.md', help='Output report file')
    
    args = parser.parse_args()
    
    analyzer = FrontendBackendAnalyzer(args.frontend_dir)
    analyzer.analyze()
    report_path = analyzer.generate_report(args.output)
    
    print(f"Analysis complete. Report saved to: {report_path}")
    

if __name__ == "__main__":
    main()