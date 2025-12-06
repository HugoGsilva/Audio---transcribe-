from hypothesis import given, strategies as st, settings, HealthCheck
import pytest
from unittest.mock import MagicMock, patch
from app.whisper_service import WhisperService

# Mocking faster_whisper to avoid downloading models or needing real audio
@pytest.fixture
def mock_whisper_model():
    with patch("app.whisper_service.WhisperModel") as MockModel:
        instance = MockModel.return_value
        yield instance

@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.lists(st.text(min_size=1), min_size=1, max_size=10), st.text(min_size=2, max_size=2), st.floats(min_value=0.1, max_value=100.0))
def test_transcription_reassembly_property(mock_whisper_model, segments_text, language, duration):
    """
    Property: Transcription returns complete text.
    Validates that the service correctly concatenates all segments returned by the model.
    """
    # Setup the mock to return the generated segments
    mock_segments = []
    expected_full_text = ""
    
    for text in segments_text:
        # segment object usually has start, end, text
        segment = MagicMock()
        segment.text = text
        mock_segments.append(segment)
        expected_full_text += text

    expected_full_text = expected_full_text.strip()
    
    # Mock info object
    mock_info = MagicMock()
    mock_info.language = language
    mock_info.duration = duration

    mock_whisper_model.transcribe.return_value = (iter(mock_segments), mock_info)

    # Initialize service (mocks are applied)
    service = WhisperService(model_size="tiny", device="cpu")
    
    # Create a dummy file path (it checks existence, so we mock os.path.exists)
    with patch("os.path.exists", return_value=True):
        result = service.transcribe("dummy_audio.mp3")

    # Assertions
    assert result["text"] == expected_full_text
    assert result["language"] == language
    assert result["duration"] == duration
