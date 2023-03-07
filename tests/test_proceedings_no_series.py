
import os

import pytest

import bibtexcompression
from bibtexcompression.database import Database
from bibtexcompression.compression import compress, Settings

FILEPATH = os.path.dirname(os.path.realpath(__file__))
INPUT_PATH = os.path.join(FILEPATH, 'input', 'proceedings_no_series.bib')
OUTPUT_PATH = os.path.join(FILEPATH, 'output', 'proceedings_no_series.bib')

class Data:
    def __init__(self):
        self.input_db = Database(INPUT_PATH, sort_entries=True)
        self.ouput_db = Database(OUTPUT_PATH, sort_entries=True)

settings = Settings(
    shorten_authors=True,
    remove_year=True,
    remove_proceedings=True,
    replace_booktitle=False,
    remove_pages=True,
    beautify_arxiv=False
)

@pytest.fixture(params=zip(Data().input_db.entries, Data().ouput_db.entries))
def entry(request):
    return request.param

def test_entry(entry):

    compressed_entry = compress(entry[0], settings)
    assert compressed_entry == entry[1]

