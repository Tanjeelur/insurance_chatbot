import re
from typing import List

class TextProcessor:
    """Utility class for text processing operations"""
    
    @staticmethod
    def clean_whitespace(text: str) -> str:
        """Remove excessive whitespace from text"""
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()
    
    @staticmethod
    def identify_sections(text: str, sections: List[str]) -> List[str]:
        """Identify section headers in text"""
        structured_lines = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line:
                # Check if line might be a section header
                if any(section in line.lower() for section in sections):
                    structured_lines.append(f"\n=== {line} ===")
                else:
                    structured_lines.append(line)
        
        return structured_lines
    
    @staticmethod
    def ensure_word_count(text: str, target_words: int, padding_words: List[str]) -> str:
        """Ensure text has exactly the target number of words"""
        words = text.split()
        if len(words) != target_words:
            if len(words) > target_words:
                text = " ".join(words[:target_words])
            else:
                # Pad with additional context if too short
                while len(words) < target_words and padding_words:
                    words.append(padding_words.pop(0))
                text = " ".join(words[:target_words])
        return text