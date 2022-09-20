
import logging
import re
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

def extract_series(title) -> Optional[str]:

    """
        Match the following pattern:
        #year #conference_name (BlaBla)
        BlaBla is what we need to extract
    """

    regex = r'[0-9]+ [a-zA-z/ ]+ \((.*)\)'
    match_regex = re.search(regex, title)
    if match_regex:
        return match_regex.group(1)
    else:
        return None

def compress_proceedings(entry, settings: Settings):

    compressed = {'ENTRYTYPE': 'inproceedings', 'ID': entry['ID']}

    # remove the proceedings title, leaving only conference name
    if settings.remove_proceedings:

        if 'publisher' in entry and 'USENIX' in entry['publisher']:
            proceedings_name = usenix.extract_series(entry)
            proceedings_name_key = "series"
            compressed[proceedings_name_key] = proceedings_name
        else:

            if 'series' in entry:
                proceedings_name_key = "series"
                compressed[proceedings_name_key] = entry[proceedings_name_key]
            else:
                proceedings_name_key = ""
                extracted_series = extract_series(entry['booktitle'])

                if extracted_series:
                    proceedings_name_key = "series"
                    compressed[proceedings_name_key] = extracted_series
                else:
                    proceedings_name_key = "booktitle"
                    compressed[proceedings_name_key] = entry[proceedings_name_key]
                    logging.warning(f"Proceedings, entry {entry['ID']}, 'series' not found, querying for series in 'booktitle' failed, skipping removing proceedings")

    else:
        proceedings_name_key = "booktitle"

    # we do not apply customization during parsing because writer later fails
    # e.g. author customization creates a list and writer expects a string only
    # Source: https://bibtexparser.readthedocs.io/en/master/tutorial.html#customizations
    if settings.shorten_authors:
        first_author = author(entry.copy())['author'][0]
        compressed['author'] = f'{first_author} et al.'
    else:
        compressed['author'] = entry['author']

    if not settings.remove_pages:
        compressed['pages'] = entry['pages']

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

def compress(entry, settings: Settings):

    match entry['ENTRYTYPE']:

        case 'inproceedings':
            return compress_proceedings(entry, settings)

        case _:
            logging.warning(f"Unknown entry type: {entry['ENTRYTYPE']}, skipping compression.")       
            return entry

