
import os

import pytest

import bibtexcompression
from bibtexcompression.database import Database
from bibtexcompression.usenix import extract_series

FILEPATH = os.path.dirname(os.path.realpath(__file__))
INPUT_PATH = os.path.join(FILEPATH, 'input', 'usenix.bib')
OUTPUT_PATH = os.path.join(FILEPATH, 'output', 'usenix.bib')

class Data:
    def __init__(self):
        self.input_db = Database(INPUT_PATH, sort_entries=True)
        self.ouput_db = Database(OUTPUT_PATH, sort_entries=True)

@pytest.fixture(params=zip(Data().input_db.entries, Data().ouput_db.entries))
def entry(request):
    return request.param

def test_entry(entry):

    series_name = extract_series(entry[0])
    assert series_name == entry[1]["series"]

