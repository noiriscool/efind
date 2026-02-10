"""
Hardcoded distributor mappings.
Map UUID (GID) to distributor name.
"""

# Example structure - you'll populate this with your manual mappings
# Format: {uuid_hex_string: "Distributor Name"}
DISTRIBUTOR_MAP = {
    # Add your mappings here
    # Example:
    # "0123456789abcdef0123456789abcdef": "DistroKid",
    # "fedcba9876543210fedcba9876543210": "CD Baby",
    "7cd978677487466fb9aea2f219ba290b": "iGroove",
    "ede63b46782e46e19045255f32c0ff0f": "The Orchard",
    
}

def get_distributor(uuid: str) -> str:
    """
    Get distributor name for a given UUID.
    
    Args:
        uuid: Hex UUID string (32 characters)
    
    Returns:
        Distributor name if found, None otherwise
    """
    # Normalize UUID (remove dashes if present, ensure lowercase)
    uuid_normalized = uuid.lower().replace('-', '')
    
    return DISTRIBUTOR_MAP.get(uuid_normalized)

