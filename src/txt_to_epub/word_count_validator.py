"""
Word count validator for comparing text quantity before and after conversion (Backward Compatibility Wrapper)

This module provides backward compatibility with the old API.
The implementation has been refactored into multiple modules under the validator package.
"""

# Re-export everything from the new modular structure
from .validator import (
    WordCountValidator,
    validate_conversion_integrity
)

__all__ = [
    'WordCountValidator',
    'validate_conversion_integrity',
]
