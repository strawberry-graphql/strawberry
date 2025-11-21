# Type alias for federation version as (major, minor) tuple
FederationVersion = tuple[int, int]

# Mapping from version string (e.g., "2.5") to version tuple (e.g., (2, 5))
FEDERATION_VERSIONS: dict[str, FederationVersion] = {
    "2.0": (2, 0),
    "2.1": (2, 1),
    "2.2": (2, 2),
    "2.3": (2, 3),
    "2.4": (2, 4),
    "2.5": (2, 5),
    "2.6": (2, 6),
    "2.7": (2, 7),
    "2.8": (2, 8),
    "2.9": (2, 9),
    "2.10": (2, 10),
    "2.11": (2, 11),
}


def parse_version(version_str: str) -> FederationVersion:
    """Parse a version string like '2.5' into a tuple (2, 5)."""
    return FEDERATION_VERSIONS[version_str]


def format_version(version: FederationVersion) -> str:
    """Format a version tuple (2, 5) into a string 'v2.5'."""
    major, minor = version
    return f"v{major}.{minor}"
