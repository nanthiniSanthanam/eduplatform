#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Django Backend Super‑Scaffolder (v 3.3.2)
========================================
A **fully‑runnable** script that scaffolds a complete Django REST backend,
produces a *front‑end bible* Markdown doc, and can optionally emit
OpenAPI YAML and Graphviz model diagrams.

### CLI flags
```
--app label       one or more app labels; defaults to all project apps
--depth N         nested‑serializer depth (default 2)
--swagger         write docs/openapi.yaml (needs PyYAML)
--graph           write docs/<app>_model_graph.svg (needs graphviz)
--dry-run         show diffs only, write nothing
--force           overwrite without timestamp backup
--skip-validation skip django check + makemigrations --check
--settings mod    Django settings module (default config.settings)
```

To run:
python super_scaffolder.py --app your_app --depth 3 --swagger --graph --dry-run

### Quick start
```bash
pip install django djangorestframework django-filter jinja2 pytest pyyaml graphviz
python super_scaffolder.py --app myapp --depth 3 --swagger --graph
```
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

# ─── constants ─────────────────────────────────────────────────────────────
SETTINGS_MODULE = "config.settings"
TEMPLATE_DIR = Path("scaffolder_templates")
BACKUP_DIR = Path("scaffolder_backups")
DOCS_DIR = Path("docs")
API_BASE = "api/v1"
BANNER = (
    "# ==========  AUTO‑GENERATED – DO NOT EDIT MANUALLY  =========="
    "\n# Generated: {timestamp}\n"
)

# ─── dependency guard ──────────────────────────────────────────────────────
REQ = {
    "django": "django>=3.2",
    "rest_framework": "djangorestframework",
    "jinja2": "jinja2",
    "django_filters": "django-filter",
}
missing = [pkg for pkg in REQ if importlib.util.find_spec(pkg) is None]
if missing:
    sys.exit("Missing deps: " + ", ".join(missing) + "\nRun: pip install " + " ".join(REQ[pkg] for pkg in missing))

import django  # type: ignore
from django.apps import apps  # type: ignore
from django.core.management import call_command  # type: ignore
from jinja2 import Environment, FileSystemLoader  # type: ignore

GV = importlib.util.find_spec("graphviz") is not None
YAML = importlib.util.find_spec("yaml") is not None

# ─── bootstrap ─────────────────────────────────────────────────────────────

def bootstrap(settings: str) -> None:
    if "DJANGO_SETTINGS_MODULE" not in os.environ:
        os.environ["DJANGO_SETTINGS_MODULE"] = settings
    django.setup()

# ─── template seeding ------------------------------------------------------

def seed_templates() -> None:
    """Write default Jinja templates if they don’t exist."""
    TEMPLATE_DIR.mkdir(exist_ok=True)
    hdr = "AUTO‑GENERATED – DO NOT EDIT BELOW THE CONFIG DICT"
    templates: Dict[str, str] = {
        "serializers.py.j2": (
            "{{ banner }}\n"+hdr+"\nCONFIG = {}\nfrom rest_framework import serializers\nfrom .models import {% for m in models %}{{ m.name }}{% if not loop.last %}, {% endif %}{% endfor %}\n\n"
            "{% for m in models %}class {{ m.name }}Serializer(serializers.ModelSerializer):\n    class Meta:\n        model = {{ m.name }}\n        depth = {{ depth }}\n        exclude = []\n\nclass {{ m.name }}DetailSerializer({{ m.name }}Serializer):\n    class Meta({{ m.name }}Serializer.Meta):\n        pass\n\n{% endfor %}"
        ),
        "views.py.j2": (
            "{{ banner }}\n"+hdr+"\nCONFIG = {'page_size': 50}\nfrom rest_framework import viewsets, filters\nfrom django_filters.rest_framework import DjangoFilterBackend\nfrom rest_framework.permissions import IsAuthenticatedOrReadOnly\nfrom .models import {% for m in models %}{{ m.name }}{% if not loop.last %}, {% endif %}{% endfor %}\nfrom .serializers import {% for m in models %}{{ m.name }}Serializer, {{ m.name }}DetailSerializer{% if not loop.last %}, {% endif %}{% endfor %}\n{% if needs_owner_perm %}from .permissions import IsOwnerOrReadOnly\n{% endif %}\n{% for m in models %}class {{ m.name }}ViewSet(viewsets.ModelViewSet):\n    queryset = {{ m.name }}.objects.all()\n    serializer_class = {{ m.name }}Serializer\n    permission_classes = [IsAuthenticatedOrReadOnly{% if m.owner %}, IsOwnerOrReadOnly{% endif %}]\n    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]\n    search_fields = {{ m.search }}\n    filterset_fields = {{ m.filters }}\n    ordering_fields = '__all__'\n\n    def get_serializer_class(self):\n        return {{ m.name }}DetailSerializer if self.action == 'retrieve' else {{ m.name }}Serializer\n\n{% endfor %}"
        ),
        "urls.py.j2": (
            "{{ banner }}\n"+hdr+"\nCONFIG = {}\nfrom django.urls import path, include\nfrom rest_framework.routers import DefaultRouter\nfrom . import views\n\napp_name = '{{ app_label }}'\nrouter = DefaultRouter()\n{% for m in models %}router.register(r'{{ m.route }}', views.{{ m.name }}ViewSet, basename='{{ m.route }}')\n{% endfor %}\nurlpatterns = [path('', include(router.urls))]\n"
        ),
        "admin.py.j2": (
            "{{ banner }}\n"+hdr+"\nCONFIG = {}\nfrom django.contrib import admin\nfrom .models import {% for m in models %}{{ m.name }}{% if not loop.last %}, {% endif %}{% endfor %}\n\n{% for m in models %}@admin.register({{ m.name }})\nclass {{ m.name }}Admin(admin.ModelAdmin):\n    list_display = ('id', {% for f in m.display %}'{{ f }}'{% if not loop.last %}, {% endif %}{% endfor %})\n    search_fields = {{ m.search }}\n\n{% endfor %}"
        ),
        "permissions.py.j2": (
            "{{ banner }}\n"+hdr+"\nCONFIG = {}\nfrom rest_framework.permissions import BasePermission, SAFE_METHODS\nclass IsOwnerOrReadOnly(BasePermission):\n    def has_object_permission(self, request, view, obj):\n        if request.method in SAFE_METHODS:\n            return True\n        return getattr(obj, 'owner_id', None) == getattr(request.user, 'id', None)\n"
        ),
        "api_docs.md.j2": (
            "# Front‑end Bible – {{ app_label }}\n_Generated: {{ timestamp }}_\n\n## Files generated\n{% for f in file_list %}- {{ f }}{% endfor %}\n\n{% for m in models %}### {{ m.name }}\nEndpoint `/{{ api_base }}/{{ m.route }}/`\n| Field | Type |\n|-------|------|\n{% for fld in m.fields %}| {{ fld.name }} | {{ fld.type }} |\n{% endfor %}\n\n{% endfor %}"
        ),
    }
    for name, txt in templates.items():
        p = TEMPLATE_DIR / name
        if not p.exists():
            p.write_text(txt.strip(), encoding="utf-8")

# ─── Jinja environment -----------------------------------------------------

def jenv() -> Environment:
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=False)
    env.filters["tojson"] = lambda v: json.dumps(v, ensure_ascii=False)
    return env

# ─── meta collection -------------------------------------------------------

def collect_meta(label: str) -> Tuple[List[Dict], bool]:
    meta: List[Dict] = []
    need_owner = False
    for mdl in apps.get_app_config(label).get_models():
        if mdl._meta.abstract:
            continue
        fields, srch, flt, disp, owns = [], [], [], [], False
        for f in mdl._meta.get_fields():
            t = type(f).__name__
            if t in {"CharField", "TextField", "EmailField", "SlugField"}:
                srch.append(f.name)
            if not f.is_relation:
                flt.append(f.name)
            if f.name in {"name", "title"}:
                disp.append(f.name)
            if f.name in {"owner", "user"}:
                owns = True
            fields.append({"name": f.name, "type": t})
        need_owner |= owns
        meta.append({"name": mdl.__name__, "route": mdl.__name__.lower(), "fields": fields, "search": srch or ["id"], "filters": flt, "display": disp, "owner": owns})
    return meta, need_owner

# ─── render ---------------------------------------------------------------

def render(label: str, meta, owner: bool, depth: int) -> Dict[str, str]:
    env = jenv()
    ctx = {
        "banner": BANNER.format(timestamp=dt.datetime.now().isoformat(timespec="seconds")),
        "app_label": label,
        "models": meta,
        "api_base": API_BASE,
        "needs_owner_perm": owner,
        "depth": depth,
    }
    files: Dict[str, str] = {}
    for tpl in TEMPLATE_DIR.glob("*.j2"):
        name = tpl.stem + (".py" if not tpl.stem.endswith("md") else ".md")
        files[name] = env.get_template(tpl.name).render(**ctx, file_list=[])
    files["frontend_bible.md"] = env.get_template("api_docs.md.j2").render(**ctx, file_list=sorted(files))
    return files

# ─── writing --------------------------------------------------------------

def atomic_write(path: Path, content: str, force: bool, dry: bool) -> None:
    if path.exists():
        diff = difflib.unified_diff(path.read_text().splitlines(1), content.splitlines(1), fromfile=str(path), tofile="NEW")
        print("".join(diff))
    if dry:
        return
    if path.exists() and not force:
        BACKUP_DIR.mkdir(exist_ok=True)
        shutil.copy2(path, BACKUP_DIR / f"{path.name}.{dt.datetime.now():%Y%m%d%H%M%S}.bak")
    fd, tmp = tempfile.mkstemp(dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(content)
    os.replace(tmp, path)


def write_app(label: str, files: Dict[str, str], force: bool, dry: bool) -> None:
    app_root = Path(apps.get_app_config(label).path)
    for fname, code in files.items():
        target = DOCS_DIR / fname if fname.endswith(".md") else app_root / fname
        target.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(target, code, force, dry)

# ─── extras ---------------------------------------------------------------

def generate_swagger(enabled: bool) -> None:
    if not enabled:
        return
    if not YAML:
        print("⚠️  PyYAML missing – skipping OpenAPI export")
        return
    DOCS_DIR.mkdir(exist_ok=True)
    out = DOCS_DIR / "openapi.yaml"
    call_command("generateschema", "--format", "openapi", "--output", str(out))
    print("📝  Swagger schema written to", out)


def graph_app(label: str, meta: List[Dict], enabled: bool) -> None:
    if not enabled:
        return
    if not GV:
        print("⚠️  graphviz missing – skipping diagram for", label)
        return
    from graphviz import Digraph  # type: ignore
    g = Digraph(label, graph_attr={"rankdir": "LR"})
    for m in meta:
        g.node(m["name"], shape="box")
    for m in meta:
        src = m["name"]
        for f in m["fields"]:
            if f["type"] in {"ForeignKey", "OneToOneField"}:
                tgt = f["type"].replace("Field", "")
                g.edge(src, tgt, label=f["name"])
    DOCS_DIR.mkdir(exist_ok=True)
    g.render((DOCS_DIR / f"{label}_model_graph").as_posix(), format="svg", cleanup=True)
    print("📈  Diagram written for", label)

# ─── validation -----------------------------------------------------------

def validate(skip: bool) -> None:
    if skip:
        return
    call_command("check", verbosity=0)
    subprocess.run([sys.executable, "manage.py", "makemigrations", "--check", "--dry-run"], check=True)

# ─── CLI ------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description="Generate DRF scaffold + docs")
    p.add_argument("--app", action="append", help="Target app (repeatable)")
    p.add_argument("--depth", type=int, default=2)
    p.add_argument("--swagger", action="store_true")
    p.add_argument("--graph", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--skip-validation", action="store_true")
    p.add_argument("--settings", default=SETTINGS_MODULE)
    args = p.parse_args()

    bootstrap(args.settings)
    seed_templates()

    targets = args.app or [cfg.label for cfg in apps.get_app_configs() if list(cfg.get_models())]
    for label in targets:
        meta, owner_flag = collect_meta(label)
        files = render(label, meta, owner_flag, args.depth)
        write_app(label, files, args.force, args.dry_run)
        # smoke import
        importlib.import_module(f"{label}.serializers")
        importlib.import_module(f"{label}.views")
        importlib.import_module(f"{label}.urls")
        graph_app(label, meta, args.graph)
    generate_swagger(args.swagger)
    validate(args.skip_validation)
    print("✅  Done – scaffold + docs generated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
