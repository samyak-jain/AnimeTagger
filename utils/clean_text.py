import re
import string


def multiple_space_remove(string_to_be_cleaned: str) -> str:
    return re.sub(' +', ' ', string_to_be_cleaned)


def remove_punctuation(string_to_be_cleaned: str) -> str:
    return re.sub('[%s]' % re.escape(string.punctuation), ' ', string_to_be_cleaned)


def clean_string(string_to_be_cleaned: str) -> str:
    removed_punctuation: str = remove_punctuation(string_to_be_cleaned).lower()
    remove_multiple_spaces: str = multiple_space_remove(removed_punctuation)
    return remove_multiple_spaces


def remove_slashes(string_to_be_cleaned: str) -> str:
    cleaned_string: str = string_to_be_cleaned
    if '/' in string_to_be_cleaned:
        cleaned_string = cleaned_string.replace('/', '')

    if r'\\' in string_to_be_cleaned:
        cleaned_string = cleaned_string.replace(r'\\', '')

    punc_remove: str = remove_punctuation(cleaned_string)
    clean_with_multiple_spaces_removed: str = multiple_space_remove(punc_remove)

    return clean_with_multiple_spaces_removed
