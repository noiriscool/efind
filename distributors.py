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
    "d34d54b89e49450fa7780d44a4336059": "SongCast",
    "e5627993ff8d48b59dfa9b39505640b5": "RouteNote",
    "bd2ab50fb53045798299479555e32033": "Qanawat",
    "a487b60b717849d8bd2be071a9b573c0": "EngineEars",
    "38ae51e8ddee4916853e9280a9ddba3e": "Boep",
    "f4556f1e41604048bf9f93112ca6c6c2": "Too Lost",
    "17ae1e9e35ed421c954fbd421cfce541": "SonoSuite",
    "aa45cf37a7f84ddda54d7a4425b98ca7": "Ditto",
    "e0b063f7069449558ac1b5e967fb01bd": "SounDrop",
    "b3d83eb6b2ba444eacf033e311aac3cc": "Limbo Music",
    "4b67a8da63cd4496afa99dac7684a60e": "Virgin Music Group",
    "a830a34f35844bd784eac9a7fb395996": "TuneCore",
    "ffb2c5e7bae04301b176bd7a5e3be782": "AudioSalad",
    "15a1c99b7fbf4183a3b9ffbeaf853b04": "GYROStream",
    "18fbcef4fb624fc58d4a7fdd230bd523": "DistroKid",
    "de1a64817bd2471a9bd5bd2023d07390": "Avex Music",
    "0f26cfca536a4a69a2baed1eca0a42ec": "FUGA",
    "2bdd92df315b492c9f4bb0ce407ce7de": "CDBaby",
    "c71b29ea9e1e48c6931da2dd7c0bf5d5": "Believe Music",
    "0c06d78a83ce4770b8a41b0459448a04": "Horus Music",
    "8337a6aeaca744a7b32050f0c66e138f": "Warner Music Group",
    "fe358ea987e2424d9021c2665a0667b7": "Universal Music Group",
    "747ab24b5b044fb9879e601f9814e4a2": "Jumpstr.io",
    "ac0671a5a2764f2199f7b0ffa22c0616": "Venice Music",
    "c69ceeaff4294b5e90a5acfab76b1a0c": "ALOADED",
    "39b9d97125fe487c8c49f5c7e34ffb34": "FreshTunes",
    "17f1e95c76384428a3ff665716c8c168": "Zoningo",
    "f26f07c695ac484fb3f1602a5711e8d3": "Nudacy Records",
    "353f6fa840854b0699981556c18c1fed": "MUGO",
    "af064b03a15e4224ab24764efe200841": "Label Engine / CMG",
    "db6e0c92eb6f4a8cb30f815eefeb3b1d": "AudioProDistro",
    "603be731bd0444d0a0936645c3b4977d": "Phonographic Digital India",
    "1564813dc9d246388befd3f3c50e4909": "Random Sounds",
    "75ce59b02e8f439bb9e0fc2d493c9994": "Daredo",
    "d3378295da4d4180bf1ba7b745f7c7ae": "emuze",
    "3f1980e65bb740b89118d2c5806d3c7d": "OneRPM",
    "67714a8c229042c68617dc5e3f52f616": "SoundOn",
    "58a1eb2962f14be29d203dd036cc2484": "Revelator",
    "2f1eee71461f4a8da1b33aa5014d2456": "Zojak World Wide",
    "53359c6a3bcb47e880d57db050de1e12": "OFFStep",

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

