
import logging
from dataclasses import dataclass
from typing import List

import bibtexparser
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import *
import click

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
        if 'series' in entry:
            proceedings_name_key = "series"
        else:
            proceedings_name_key = "booktitle"
            logging.warning("Proceedings, entry 'series' not found, skipping removing proceedings")

        compressed[proceedings_name_key] = entry[proceedings_name_key]
    else:
        proceedings_name_key = "booktitle"

    if settings.shorten_authors:
        first_author = entry['author'][0]
        compressed['author'] = f'{first_author} et al.'
    else:
        compressed['author'] = entry['author']

    if not settings.remove_pages:
        compressed['pages'] = entry['pages']

    # year can be skipped if it is already in the series name
    if settings.remove_year:
        
        year = entry['year']
        shortened_year = f"'{year[2:4]}"

        if not year in entry[proceedings_name_key] and not shortened_year in entry[proceedings_name_key]:
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

    # Create customizations to enable non-standard parsing.
    # Source: https://bibtexparser.readthedocs.io/en/master/tutorial.html#customizations
    def customizations(record):
        record = type(record)
        record = author(record)
        return record

    options = CompressionSettings(**kwargs)

    with open(input, 'r') as bibtex_file:

        parser = BibTexParser()
        parser.customization = customizations
        bib_database = bibtexparser.load(bibtex_file, parser=parser)

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

