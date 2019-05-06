import re
import string
from typing import List, Optional

from polyglot.detect import Detector, Language
from polyglot.detect.base import UnknownLanguage

STOPWORDS: List[str] = [
    "amv",
    "hd"
]


def remove_stopwords(string_to_be_cleaned: str) -> str:
    words: List[str] = string_to_be_cleaned.split(' ')
    filtered_words: List[str] = [word for word in words if word not in STOPWORDS]
    return ' '.join(filtered_words)


def multiple_space_remove(string_to_be_cleaned: str) -> str:
    return re.sub(' +', ' ', string_to_be_cleaned)


def remove_punctuation(string_to_be_cleaned: str) -> str:
    return re.sub('[%s]' % re.escape(string.punctuation), ' ', string_to_be_cleaned)


def clean_string(string_to_be_cleaned: str) -> str:
    removed_punctuation: str = remove_punctuation(string_to_be_cleaned).lower()
    remove_multiple_spaces: str = multiple_space_remove(removed_punctuation)
    filtered_string: str = remove_stopwords(remove_multiple_spaces)
    return filtered_string


def remove_slashes(string_to_be_cleaned: str) -> str:
    cleaned_string: str = string_to_be_cleaned
    if '/' in string_to_be_cleaned:
        cleaned_string = cleaned_string.replace('/', '')

    if r'\\' in string_to_be_cleaned:
        cleaned_string = cleaned_string.replace(r'\\', '')

    punc_remove: str = remove_punctuation(cleaned_string)
    clean_with_multiple_spaces_removed: str = multiple_space_remove(punc_remove)

    return clean_with_multiple_spaces_removed


def detect_language(string_to_be_detected: Optional[str]) -> Optional[int]:
    if string_to_be_detected is None:
        return None

    try:
        detector: Detector = Detector(string_to_be_detected)
    except UnknownLanguage:
        return None

    languages: List[Language] = detector.languages
    best_lang: Language = max(languages, key=lambda lang: lang.confidence)

    if best_lang.name == "English":
        return 1
    elif best_lang.name == "Japanese":
        return 2
    else:
        return 3
