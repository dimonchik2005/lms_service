from urllib.parse import urlparse

from rest_framework.serializers import ValidationError


def validate_youtube_url(value):
    """Разрешает ссылки только на домен youtube.com."""

    if not value:
        return value

    parsed_url = urlparse(value)
    hostname = (
        parsed_url.hostname or ""
    ).lower()

    valid_scheme = parsed_url.scheme in (
        "http",
        "https",
    )

    valid_hostname = (
        hostname == "youtube.com"
        or hostname.endswith(".youtube.com")
    )

    if not valid_scheme or not valid_hostname:
        raise ValidationError(
            "Разрешены ссылки только на youtube.com."
        )

    return value