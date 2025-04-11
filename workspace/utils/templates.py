"""Utility functions for working with Jinja2 templates."""

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

# Get the absolute path to the templates directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# Create Jinja2 environment with the templates directory
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    extensions=["jinja2.ext.do"],
    trim_blocks=True,
    lstrip_blocks=True,
    undefined=StrictUndefined,
)


# Register custom filters
def format_datetime(dt_str):
    """Format an ISO datetime string to a human-readable format."""
    if isinstance(dt_str, str):
        dt = datetime.fromisoformat(dt_str)
    else:
        dt = dt_str
    return dt.strftime("%Y-%m-%d %H:%M")


jinja_env.filters["format_datetime"] = format_datetime


def render_template(template_path: str, **context):
    """Render a template with the given context.

    Args:
        template_path: Path to the template relative to the templates directory
        **context: Variables to pass to the template

    Returns:
        Rendered template as string
    """
    template = jinja_env.get_template(template_path)
    return template.render(**context)
