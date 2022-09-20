
from typing import List

import bibtexparser
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bparser import BibTexParser

class Database:

    def __init__(self, path: str, sort_entries = False):

        try:
            with open(path, 'r') as bibtex_file:
                self._database = bibtexparser.load(bibtex_file)

        # support non-numerical month names
        except bibtexparser.bibdatabase.UndefinedString:

            with open(path, 'r') as bibtex_file:
                parser = BibTexParser(common_strings=True)
                self._database = bibtexparser.load(bibtex_file, parser=parser)

        if sort_entries:
            self._entries = sorted(
                self._database.entries,
                key=lambda entry: BibDatabase.entry_sort_key(entry, ['ID'])
            )
        else:
            self._entries = self._database.entries

    @property
    def entries(self) -> List[dict]:
        return self._entries

