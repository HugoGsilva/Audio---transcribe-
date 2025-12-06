from hypothesis import given, strategies as st
import pytest
from unittest.mock import MagicMock, patch
from app.validation import FileValidator

# Strategies
valid_extensions = st.sampled_from(["mp3", "wav", "m4a", "ogg", "webm", "flac"])
invalid_extensions = st.text(min_size=1, max_size=5).filter(lambda x: x not in ["mp3", "wav", "m4a", "ogg", "webm", "flac"])
valid_filenames = st.builds(lambda name, ext: f"{name}.{ext}", st.text(min_size=1, alphabet=st.characters(whitelist_categories=('L', 'N'))), valid_extensions)
invalid_filenames = st.builds(lambda name, ext: f"{name}.{ext}", st.text(min_size=1), invalid_extensions)

@given(valid_filenames)
def test_valid_extension_accepted(filename):
    """Property 1: Valid audio formats are accepted (filename check)"""
    validator = FileValidator()
    is_valid, msg = validator.validate_filename(filename)
    assert is_valid
    assert msg == "Valid filename"

@given(invalid_filenames)
def test_invalid_extension_rejected(filename):
    """Property 2: Invalid file types are rejected (filename check)"""
    validator = FileValidator()
    is_valid, msg = validator.validate_filename(filename)
    assert not is_valid
    assert "Invalid file extension" in msg

@given(st.integers(min_value=1, max_value=100*1024*1024))
def test_valid_size_accepted(size):
    """Property 1/3 related: Valid size accepted"""
    validator = FileValidator(max_size_mb=100)
    is_valid, msg = validator.validate_size(size)
    assert is_valid

@given(st.integers(min_value=100*1024*1024 + 1))
def test_oversized_rejected(size):
    """Property 3: Oversized files are rejected"""
    validator = FileValidator(max_size_mb=100)
    is_valid, msg = validator.validate_size(size)
    assert not is_valid
    assert "exceeds limit" in msg

# Mock magic for content validation to avoid dependency issues on host
@given(st.sampled_from(["audio/mpeg", "audio/wav"]))
def test_valid_content_accepted(mime_type):
    """Property 1: Valid audio formats accepted (content check)"""
    with patch("magic.Magic") as MockMagic:
        instance = MockMagic.return_value
        instance.from_buffer.return_value = mime_type
        
        validator = FileValidator()
        # content doesn't matter as we mock the return
        is_valid, msg = validator.validate_content(b"fake headers")
        assert is_valid

@given(st.sampled_from(["application/pdf", "image/png", "text/plain"]))
def test_invalid_content_rejected(mime_type):
    """Property 2: Invalid file types rejected (content check)"""
    with patch("magic.Magic") as MockMagic:
        instance = MockMagic.return_value
        instance.from_buffer.return_value = mime_type
        
        validator = FileValidator()
        is_valid, msg = validator.validate_content(b"fake headers")
        assert not is_valid
        assert "Invalid file content type" in msg

@given(valid_filenames, st.integers(min_value=1, max_value=100*1024*1024))
def test_validation_order(filename, size):
    """Property 9: Validation occurs before processing"""
    # This specifically tests that validate() calls the checks
    # We can infer order by mocking the individual methods if we want strict order check
    # But usually just ensuring all are called is enough for unit test
    
    with patch.object(FileValidator, 'validate_size', return_value=(True, "OK")) as mock_size, \
         patch.object(FileValidator, 'validate_filename', return_value=(True, "OK")) as mock_name, \
         patch.object(FileValidator, 'validate_content', return_value=(True, "OK")) as mock_content:
        
        validator = FileValidator()
        validator.validate(filename, size, b"header")
        
        # Verify all were called
        mock_size.assert_called()
        mock_name.assert_called()
        mock_content.assert_called()

        # To strictly test order: return False in the first one and ensure second is not called
        mock_size.return_value = (False, "Too big")
        mock_name.reset_mock()
        
        res, _ = validator.validate(filename, size, b"header")
        assert not res
        mock_name.assert_not_called()  # verifying short-circuit
