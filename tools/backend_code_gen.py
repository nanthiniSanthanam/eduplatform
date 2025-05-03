#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backend_codegen_full.py – **failsafe** Django REST scaffolder & documentation tool - ChatGPT
================================================================================
This single script will:

1. **Inspect** the models of one (or all) Django apps.
2. **Generate** every routine backend file you need (`serializers.py`, `views.py`,
   `urls.py`, `admin.py`, `permissions.py`, `tests/`, plus a Markdown report).
3. **Validate** the generated code by importing the modules and running
   `django check` + `makemigrations --check`.
4. **Write atomically** with automatic backups to avoid half‑written states.

Designed for beginners – you only need to
```bash
pip install django djangorestframework django-filter jinja2 pytest
python backend_codegen_full.py --app myapp  # repeat --app for multiple apps, or omit for all
```
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import importlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List

# ─── 3rd‑party safety checks ────────────────────────────────────────────────
try:
    import django  # type: ignore
    from django.apps import apps  # type: ignore
    from django.core.management import call_command  # type: ignore
except ModuleNotFoundError:
    sys.exit("❌  Django not installed.  Run:  pip install django\n")

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape  # type: ignore
except ModuleNotFoundError:
    sys.exit("❌  Jinja2 not installed.  Run:  pip install jinja2\n")

# ─── configuration ──────────────────────────────────────────────────────────
DEFAULT_SETTINGS_MODULE = "config.settings"
TEMPLATE_DIR = Path("codegen_templates")
BACKUP_DIR = Path("codegen_backups")
DOCS_DIR = Path("docs")
BANNER = (
    "# ==========  AUTO‑GENERATED – DO NOT EDIT BY HAND  ==========\n"
    "# Your changes will be overwritten the next time backend_codegen_full.py runs.\n"
)

# ─── Jinja template strings (written on first run) ──────────────────────────
_TEMPLATE_SRC: Dict[str, str] = {
    "serializers.py.j2": (
        "{{ banner }}from rest_framework import serializers\n"
        "from .models import {% for m in models %}{{ m.name }}, {% endfor %}\n\n"
        "{% for m in models %}class {{ m.name }}Serializer(serializers.ModelSerializer):\n"
        "    class Meta:\n        model = {{ m.name }}\n        exclude = {{ m.exclude }}\n\n{% endfor %}"
    ),
    "permissions.py.j2": (
        "{{ banner }}from rest_framework.permissions import BasePermission, SAFE_METHODS\n\n"
        "class IsOwnerOrReadOnly(BasePermission):\n    \"\"\"Owner can edit; others read‑only.\"\"\"\n"
        "    def has_object_permission(self, request, view, obj):\n        if request.method in SAFE_METHODS:\n            return True\n        return getattr(obj, 'owner_id', None) == getattr(request.user, 'id', None)\n"
    ),
    "views.py.j2": (
        "{{ banner }}from rest_framework import viewsets, filters\n"
        "from rest_framework.permissions import IsAuthenticatedOrReadOnly\n"
        "from django_filters.rest_framework import DjangoFilterBackend\n"
        "from .models import {% for m in models %}{{ m.name }}, {% endfor %}\n"
        "from .serializers import {% for m in models %}{{ m.name }}Serializer, {% endfor %}\n"
        "from .permissions import IsOwnerOrReadOnly\n\n"
        "{% for m in models %}class {{ m.name }}ViewSet(viewsets.ModelViewSet):\n"
        "    queryset = {{ m.name }}.objects.all()\n    serializer_class = {{ m.name }}Serializer\n"
        "    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]\n"
        "    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]\n"
        "    search_fields = {{ m.search }}\n    filterset_fields = {{ m.filters }}\n    ordering_fields = '__all__'\n\n{% endfor %}"
    ),
    "urls.py.j2": (
        "{{ banner }}from rest_framework.routers import DefaultRouter\n"
        "from django.urls import path, include\nfrom . import views\n\napp_name = '{{ app_label }}'\nrouter = DefaultRouter()\n"
        "{% for m in models %}router.register(r'{{ m.route }}', views.{{ m.name }}ViewSet, basename='{{ m.route }}')\n{% endfor %}\n"
        "urlpatterns = [path('', include(router.urls))]\n"
    ),
    "admin.py.j2": (
        "{{ banner }}from django.contrib import admin\nfrom .models import {% for m in models %}{{ m.name }}, {% endfor %}\n\n"
        "{% for m in models %}@admin.register({{ m.name }})\nclass {{ m.name }}Admin(admin.ModelAdmin):\n"
        "    list_display = {{ m.list_display }}\n    search_fields = {{ m.search_admin }}\n    list_filter = {{ m.list_filter }}\n\n{% endfor %}"
    ),
    "tests/test_api.py.j2": (
        "{{ banner }}import pytest\nfrom rest_framework.test import APIClient\nfrom django.urls import reverse\n\npytestmark = pytest.mark.django_db\nclient = APIClient()\n"
        "{% for m in models %}\n
def test_{{ m.route }}_list():\n    url = reverse('{{ app_label }}:{{ m.route }}-list')\n    resp = client.get(url)\n    assert resp.status_code == 200\n{% endfor %}"
    ),
    "report.md.j2": (
        "# {{ app_label }} – Backend Integration Report\n_Generated: {{ timestamp }}_\n\n"
        "## Models\n{% for m in models %}- **{{ m.name }}** ({{ m.num_fields }} fields)\n{% endfor %}\n\n---\n"
        "{% for m in models %}### {{ m.name }}\n| Field | Type | Null | Unique | Relation |\n|-------|------|------|--------|----------|\n{% for f in m.fields %}| {{ f.name }} | {{ f.type }} | {{ f.null }} | {{ f.unique }} | {{ f.rel }} |\n{% endfor %}\n\nEndpoint → `/api/v1/{{ m.route }}/`\n\n---\n{% endfor %}"
    ),
}

# ─── helpers ────────────────────────────────────────────────────────────────

def ensure_template_files() -> None:
    """Write Jinja template files to disk the first time."""
    TEMPLATE_DIR.mkdir(exist_ok=True)
    for name, text in _TEMPLATE_SRC.items():
        p = TEMPLATE_DIR / name
        if not p.exists():
            p.write_text(text, encoding="utf-8")


def bootstrap(settings_module: str) -> None:
    if "DJANGO_SETTINGS_MODULE" not in os.environ:
        os.environ["DJANGO_SETTINGS_MODULE"] = settings_module
    django.setup()


def collect_model_meta(app_label: str) -> List[dict]:
    out: List[dict] = []
    for model in apps.get_app_config(app_label).get_models():
        fld_meta = []
        search, filters, exclude = [], [], []
        list_display = ["id"]
        for f in model._meta.get_fields():
            info = {
                "name": f.name,
                "type": type(f).__name__,
                "null": getattr(f, "null", False),
                "unique": getattr(f, "unique", False),
                "rel": f.is_relation,
            }
            # search & filter logic
            if info["type"] in {"CharField", "TextField", "SlugField", "EmailField"} and getattr(f, "max_length", 0):
                search.append(f.name)
            if not f.is_relation and len(list_display) < 4:
                list_display.append(f.name)
            if f.is_relation:
                filters.append(f.name)
            if info["type"] in {"PasswordField", "BinaryField"} or f.name in {"password", "secret_key"}:
                exclude.append(f.name)
            fld_meta.append(info)
        out.append({
            "name": model.__name__,
            "route": model.__name__.lower(),
            "num_fields": len(fld_meta),
            "fields": fld_meta,
            "search": search or list_display,
            "filters": filters,
            "exclude": exclude or [],
            "list_display": list_display,
            "search_admin": search or list_display,
            "list_filter": filters,
        })
    return out


def jinja_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(disabled=True),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["banner"] = BANNER
    return env


def render_templates(app_label: str, meta: List[dict]) -> Dict[str, str]:
    ctx = {
        "app_label": app_label,
        "models": meta,
        "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
    }
    env = jinja_env()
    out: Dict[str, str] = {}
    for tpl_name in _TEMPLATE_SRC:
        target_rel = tpl_name.replace(".j2", "")
        out[target_rel] = env.get_template(tpl_name).render(**ctx)
    return out


def atomic_write(path: Path, content: str, overwrite: bool) -> None:
    """Write to temp file then move, backing up replaced file."""
    if path.exists():
        if not overwrite:
            BACKUP_DIR.mkdir(exist_ok=True)
            bkp = BACKUP_DIR / f"{path.name}.{dt.datetime.now():%Y%m%d%H%M%S}.bak"
            shutil.copy2(path, bkp)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=str(path.parent))
    with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_fp:
        tmp_fp.write(content)
    os.replace(tmp_path, path)


def write_files(app_label: str, rendered: Dict[str, str], overwrite: bool):
    app_dir = Path(apps.get_app_config(app_label).path)
    for rel, code in rendered.items():
        target = app_dir / rel
        if rel.startswith("tests/"):
            target.parent.mkdir(exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
        # diff preview
        if target.exists():
            diff = difflib.unified_diff(target.read_text().splitlines(True), code.splitlines(True),
                                        fromfile=str(target), tofile="NEW")
            dtxt = "".join(diff)
            if dtxt:
                print(f"🔄 Updating {target}\n{dtxt}")
        else:
            print(f"🆕 Creating {target}")
        atomic_write(target, code, overwrite)


def import_check(app_label: str):
    for m in ("serializers", "views", "urls", "admin"):
        importlib.import_module(f"{app_label}.{m}")


def validations():
    call_command("check", verbosity=0)
    subprocess.run([sys.executable, "manage.py", "makemigrations", "--check", "--dry-run"], check=True)


def write_report(app_label: str, meta: List[dict]):
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    env = jinja_env()
    md = env.get_template("report.md.j2").render(app_label=app_label, models=meta,
                                                  timestamp=dt.datetime.now().isoformat(timespec="seconds"))
    (DOCS_DIR / f"{app_label}_backend_report.md").write_text(md, encoding="utf-8")


# ─── CLI entrypoint ─────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(description="Generate DRF scaffolding & docs")
    p.add_argument("--app", action="append", help="App label (can repeat). Defaults to all INSTALLED_APPS with models.")
    p.add_argument("--overwrite", action="store_true", help="Overwrite files without asking (backups are still kept).")
    p.add_argument("--settings", default=DEFAULT_SETTINGS_MODULE, help="Django settings module if not default.")
    args = p.parse_args()

    try:
        bootstrap(args.settings)
        ensure_template_files()

        target_apps = args.app if args.app else [cfg.label for cfg in apps.get_app_configs() if list(cfg.get_models())]
        if not target_apps:
            print("⚠️  No apps with models found – nothing to do.")
            return 0

        for label in target_apps:
            print(f"
=== Processing app: {label} ===")
            meta = collect_model_meta(label)
            rendered = render_templates(label, meta)
            write_files(label, rendered, args.overwrite)
            import_check(label)
            write_report(label, meta)

        validations()
        print("
🎉  Generation complete – remember to run tests & commit your changes!")
        return 0
    except Exception as exc:  # pylint: disable=broad-except
        print("❌  Error during generation:
", exc)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
