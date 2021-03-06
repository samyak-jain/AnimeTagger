import re
import string
from difflib import SequenceMatcher
from typing import List, Optional, Tuple

import pycld2
from polyglot.detect import Detector, Language
from polyglot.detect.base import UnknownLanguage
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

STOPWORDS: List[str] = [
    "amv",
    "hd",
    'lyrics'
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

    # Remove non printable characters
    cleaned_string: str = ' '.join([char for char in string_to_be_detected if char.isprintable()])
    try:
        detector: Detector = Detector(cleaned_string)
    except (UnknownLanguage, pycld2.error):
        return None

    languages: List[Language] = detector.languages
    best_lang: Language = max(languages, key=lambda lang: lang.confidence)

    if best_lang.name == "English":
        return 1
    elif best_lang.name == "Japanese":
        return 2
    else:
        return 3


def calculate_similarity(str_a: str, str_b: str) -> float:
    cleaned_a: str = clean_string(str_a)
    cleaned_b: str = clean_string(str_b)

    return SequenceMatcher(None, cleaned_a, cleaned_b).ratio()


def calculate_tfidf(str_a: str, list_str: List[Tuple[int, str]]) -> np.ndarray:
    vect = TfidfVectorizer(min_df=1)
    tfidf = vect.fit_transform([str_a] + [element[1] for element in list_str])
    return (tfidf * tfidf.T).A[0][1:]
