import re

import bleach
import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def rich_content(value):
    value = value or ""
    if not re.search(r"</?(?:p|ul|ol|li|h[1-6]|strong|em|div|br)\b", value):
        value = markdown.markdown(value, extensions=["nl2br", "sane_lists"])
    clean = bleach.clean(
        value,
        tags=[
            "p",
            "br",
            "ul",
            "ol",
            "li",
            "strong",
            "b",
            "em",
            "i",
            "u",
            "s",
            "h1",
            "h2",
            "h3",
            "h4",
            "blockquote",
            "a",
            "pre",
            "code",
            "sub",
            "sup",
        ],
        attributes={"a": ["href", "title"], "li": ["data-list"]},
        protocols=["http", "https", "mailto"],
        strip=True,
    )
    return mark_safe(clean)
