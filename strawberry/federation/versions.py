# Type alias for federation version as (major, minor) tuple
FederationVersion = tuple[int, int]

# Supported federation versions
FEDERATION_VERSIONS = {
    (2, 0): "v2.0",
    (2, 1): "v2.1",
    (2, 2): "v2.2",
    (2, 3): "v2.3",
    (2, 4): "v2.4",
    (2, 5): "v2.5",
    (2, 6): "v2.6",
    (2, 7): "v2.7",
    (2, 8): "v2.8",
    (2, 9): "v2.9",
    (2, 10): "v2.10",
    (2, 11): "v2.11",
}


def parse_version(version_str: str) -> FederationVersion:
    """Parse a version string like '2.5' into a tuple (2, 5)."""
    major, minor = version_str.split(".")
    return (int(major), int(minor))


def format_version(version: FederationVersion) -> str:
    """Format a version tuple (2, 5) into a string 'v2.5'."""
    major, minor = version
    return f"v{major}.{minor}"
