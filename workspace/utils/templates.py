"""Utility functions for working with Jinja2 templates."""

from datetime import datetime
from pathlib import Path

from jinja2 import BaseLoader, Environment, FileSystemLoader, StrictUndefined

# Get the absolute path to the templates directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


# Register custom filters
def format_datetime(dt_str: str | datetime) -> str:
    """Format an ISO datetime string to a human-readable format."""
    if isinstance(dt_str, str):
        dt = datetime.fromisoformat(dt_str)
    else:
        dt = dt_str
    return dt.strftime("%Y-%m-%d %H:%M")


def get_jinja_environment(directory: str | Path | None = None) -> Environment:
    """Create a Jinja2 environment for rendering templates.

    Args:
        directory: Directory containing the templates (default: None)

    Returns:
        Jinja2 Environment configured for the specified directory
    """
    if directory is not None:
        loader = FileSystemLoader(str(directory))
    else:
        loader = BaseLoader()

    environment = Environment(
        loader=loader,
        extensions=["jinja2.ext.do"],
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=StrictUndefined,
    )
    environment.filters["format_datetime"] = format_datetime

    return environment


def render_template(template_path: str, **context):
    """Render a template with the given context.

    Args:
        template_path: Path to the template relative to the templates directory
        **context: Variables to pass to the template

    Returns:
        Rendered template as string
    """
    env = get_jinja_environment(TEMPLATES_DIR)
    template = env.get_template(template_path)
    return template.render(**context)


def render_string_template(template_string: str, **context):
    """Render a string template with the given context.

    Args:
        template_string: The Jinja2 template as a string
        **context: Variables to pass to the template

    Returns:
        Rendered template as string
    """
    env = get_jinja_environment()
    template = env.from_string(template_string)
    return template.render(**context)
