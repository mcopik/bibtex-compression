
import logging
from dataclasses import dataclass
from typing import List

import bibtexparser
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.customization import author
import click

from bibtexcompression import usenix
from bibtexcompression.database import Database

# https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

@dataclass
class CompressionSettings:
    shorten_authors: bool
    remove_proceedings: bool
    remove_pages: bool
    remove_year: bool

def compress_proceedings(entry, settings: CompressionSettings):

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
            else:
                proceedings_name_key = "booktitle"
                logging.warning(f"Proceedings, entry {entry['ID']}, 'series' not found, skipping removing proceedings")

            compressed[proceedings_name_key] = entry[proceedings_name_key]

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

@click.command()
@click.argument('input', type=str)
@click.argument('output', type=str)
@click.option('--shorten-authors', type=bool, default=True, help='Replace authors with et al.')
@click.option('--remove-proceedings', type=bool, default=True, help='Remove proceeding names for conferences when venue name is provided.')
@click.option('--remove-pages', type=bool, default=True, help='Remove the page numberproceeding names for conferences when venue name is provided.')
@click.option('--remove-year', type=bool, default=True, help='Try to remove year if it already appears, e.g., in conference name.')
def compress(input, output, **kwargs):

    options = CompressionSettings(**kwargs)

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(CustomFormatter())
    logging.basicConfig(
        handlers = [handler],
        level=logging.INFO,
        format= '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    bib_database = Database(input)

    compressed_entries: List[dict] = []
    for entry in bib_database.entries:


        match entry['ENTRYTYPE']:

            case 'inproceedings':
                parsed_entry = compress_proceedings(entry, options)

            case _:
                logging.warning(f"Unknown entry type: {entry['ENTRYTYPE']}, skipping compression.")       
                parsed_entry = entry

        compressed_entries.append(parsed_entry)

    compressed_db = BibDatabase()
    compressed_db.entries = compressed_entries

    with open(output, 'w') as bibtex_out_file:
        bibtexparser.dump(compressed_db, bibtex_out_file)

if __name__ == '__main__':
    compress()

