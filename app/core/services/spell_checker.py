"""
Portuguese Spell Checker Service
Uses LanguageTool for grammar and spelling correction
"""

import language_tool_python
from app.core.config import logger
import re

# Singleton instance to avoid repeated initialization
_tool = None

def get_tool():
    """Get or initialize LanguageTool instance (Portuguese-BR)"""
    global _tool
    if _tool is None:
        try:
            logger.info("Initializing LanguageTool for Portuguese...")
            _tool = language_tool_python.LanguageTool('pt-BR')
            logger.info("LanguageTool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LanguageTool: {e}")
            return None
    return _tool


def correct_text(text: str) -> str:
    """
    Apply spell and grammar correction to Portuguese text.
    Preserves timestamps and speaker labels.
    
    Args:
        text: Original transcription text
        
    Returns:
        Corrected text
    """
    if not text or not text.strip():
        return text
    
    tool = get_tool()
    if tool is None:
        logger.warning("LanguageTool not available, returning original text")
        return text
    
    try:
        # Split by lines to preserve structure (timestamps, speakers)
        lines = text.split('\n')
        corrected_lines = []
        
        for line in lines:
            if not line.strip():
                corrected_lines.append(line)
                continue
            
            # Extract timestamp if present (e.g., "[00:01]" or "[Speaker 1]")
            timestamp_match = re.match(r'^(\[[^\]]+\]\s*)', line)
            prefix = ""
            content = line
            
            if timestamp_match:
                prefix = timestamp_match.group(1)
                content = line[len(prefix):]
            
            # Apply correction to content only
            if content.strip():
                try:
                    corrected_content = tool.correct(content)
                    corrected_lines.append(prefix + corrected_content)
                except Exception as e:
                    logger.warning(f"Failed to correct line: {e}")
                    corrected_lines.append(line)
            else:
                corrected_lines.append(line)
        
        result = '\n'.join(corrected_lines)
        logger.info(f"Text correction completed. Original: {len(text)} chars, Corrected: {len(result)} chars")
        return result
        
    except Exception as e:
        logger.error(f"Error during spell correction: {e}")
        return text


def get_corrections(text: str) -> list:
    """
    Get list of suggested corrections without applying them.
    Useful for showing what was changed.
    
    Returns:
        List of matches with details
    """
    if not text:
        return []
    
    tool = get_tool()
    if tool is None:
        return []
    
    try:
        matches = tool.check(text)
        return [
            {
                "message": m.message,
                "context": m.context,
                "replacements": m.replacements[:3] if m.replacements else [],
                "offset": m.offset,
                "length": m.errorLength
            }
            for m in matches
        ]
    except Exception as e:
        logger.error(f"Error getting corrections: {e}")
        return []
