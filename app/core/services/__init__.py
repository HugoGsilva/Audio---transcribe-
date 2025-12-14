# Services module initialization
# Re-export whisper_service from parent module for backward compatibility
from app.services.transcription import TranscriptionService
from app.core.config import settings
from . import spell_checker

# Singleton instance (matching app.core.services.py behavior)
whisper_service = TranscriptionService(settings)
