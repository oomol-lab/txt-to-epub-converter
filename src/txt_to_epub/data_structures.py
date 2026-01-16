from typing import Optional, List, NamedTuple

# Define data structures
class Section(NamedTuple):
    """Data structure representing a section"""
    title: str
    content: str

class Chapter(NamedTuple):
    """Data structure representing a chapter"""
    title: str
    content: str
    sections: List[Section]

class Volume(NamedTuple):
    """Data structure representing a volume/part/book"""
    title: Optional[str]
    chapters: List[Chapter]