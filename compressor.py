#!/usr/bin/env python

import logging
from typing import List

import bibtexparser
from bibtexparser.bibdatabase import BibDatabase
import click

from bibtexcompression.compression import compress
from bibtexcompression.compression import Settings as CompressionSettings
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

@click.command()
@click.argument('input', type=str)
@click.argument('output', type=str)
@click.option('--shorten-authors', type=bool, default=True, help='Replace authors with et al.')
@click.option('--remove-proceedings', type=bool, default=True, help='Remove proceeding names for conferences when venue name is provided.')
@click.option('--remove-pages', type=bool, default=False, help='Remove the page numberproceeding names for conferences when venue name is provided.')
@click.option('--remove-year', type=bool, default=True, help='Try to remove year if it already appears, e.g., in conference name.')
def cli(input, output, **kwargs):

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

        compressed_entries.append(compress(entry, options))


    compressed_db = BibDatabase()
    compressed_db.entries = compressed_entries

    with open(output, 'w') as bibtex_out_file:
        bibtexparser.dump(compressed_db, bibtex_out_file)

if __name__ == '__main__':
    cli()

