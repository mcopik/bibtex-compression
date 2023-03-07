
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from typing import Optional

from bibtexparser.customization import author

from bibtexcompression import usenix

@dataclass
class Settings:
    shorten_authors: bool
    remove_proceedings: bool
    remove_pages: bool
    remove_year: bool
    replace_booktitle: bool

class ConferenceMappings:

    def __init__(self, path: str):

        with open(path, 'r') as conference_data:
            self._data = json.load(conference_data)

    @property
    def conferences(self):
        return self._data

FILEPATH = os.path.dirname(os.path.realpath(__file__))
conference_mappings = ConferenceMappings(os.path.join(FILEPATH, 'conferences.json'))

def match_conference(title) -> Optional[str]:

    """
        Most of the names are in the form 'Proceedings of X', but there are some minor,
        stylistic differences - thus we can't easily extract the conference name with regex.
        Thus, it's easier to go over all mappings.
    """
    for conference, short_name in conference_mappings.conferences.items():
        if conference.lower() in title.lower():
            return short_name

    return None

def extract_series(title) -> Optional[str]:

    """
        Match the following pattern:
        #year #conference_name (BlaBla)
        BlaBla is what we need to extract.
        We match until the end to handle correctly situations such as "Proceedings of IPDPS, Workshop X"
    """

    regex = r'[0-9a-zA-z/, ]+ \((.*)\)$'
    match_regex = re.search(regex, title)
    if match_regex:
        return match_regex.group(1)
    else:
        return None

def compress_proceedings_name(entry) -> Optional[str]:

    if 'publisher' in entry and 'USENIX' in entry['publisher']:
        proceedings_name = usenix.extract_series(entry)
        return proceedings_name

    if 'series' in entry:
        return entry['series']

    # Try to extract series name with regex
    extracted_series = extract_series(entry['booktitle'])
    if extracted_series:
        return extracted_series

    # Try to match the booktitle to a known conference name
    matched_name = match_conference(entry['booktitle'])
    if matched_name:
        return matched_name

    return None

def compress_author(entry, settings):

    # we do not apply customization during parsing because writer later fails
    # e.g. author customization creates a list and writer expects a string only
    # Source: https://bibtexparser.readthedocs.io/en/master/tutorial.html#customizations
    if settings.shorten_authors:
        first_author = author(entry.copy())['author'][0]
        return f'{first_author} and others'
    else:
        return entry['author']

def compress_proceedings(entry, settings: Settings):

    compressed = {'ENTRYTYPE': 'inproceedings', 'ID': entry['ID']}

    # remove the proceedings title, leaving only conference name
    if settings.remove_proceedings:

        extracted_series = compress_proceedings_name(entry)
        if extracted_series is not None:

            proceedings_name_key = "booktitle" if settings.replace_booktitle else "series"
            compressed[proceedings_name_key] = extracted_series

        else:

            proceedings_name_key = "booktitle"
            compressed[proceedings_name_key] = entry[proceedings_name_key]
            logging.warning(f"Proceedings, entry {entry['ID']}, 'series' not found, querying for series in 'booktitle' failed, skipping removing proceedings")
    else:
        proceedings_name_key = "booktitle"
        compressed[proceedings_name_key] = entry[proceedings_name_key]

    compressed['author'] = compress_author(entry, settings)

    # year can be skipped if it is already in the series name
    if settings.remove_year:

        year = entry['year']
        shortened_year = f"'{year[2:4]}"

        if not year in compressed[proceedings_name_key] and not shortened_year in compressed[proceedings_name_key]:
            compressed['year'] = entry['year']
    else:
        compressed['year'] = entry['year']

    compressed['title'] = entry['title']

    return compressed

def compress_article(entry, settings: Settings):

    if 'journal' not in entry:
        logging.error(f"Article, ID {entry['ID']}, field journal not found - cannot compress that")
        return entry

    compressed = {
        'ENTRYTYPE': entry['ENTRYTYPE'],
        'ID': entry['ID'],
        'title': entry['title'],
    }

    for field in ['volume', 'journal', 'year']:
        if field in entry:
            compressed[field] = entry[field]

    if not settings.remove_pages and 'pages' in entry:
        compressed['pages'] = entry['pages']

    compressed['author'] = compress_author(entry, settings)

    return compressed

def compress(entry, settings: Settings):

    """
        We support the following classes of documents:
        - conference proceedings (inproceedings)
        - journal articles (article)

        We do not support the type "misc".

        Everything else is reported as warning to the user.
    """

    match entry['ENTRYTYPE']:

        case 'inproceedings':
            return compress_proceedings(entry, settings)

        case 'article':
            return compress_article(entry, settings)

        case 'misc':
            return entry

        case _:
            logging.warning(f"Unknown entry type: {entry['ENTRYTYPE']} for ID {entry['ID']}, skipping compression.")
            return entry


