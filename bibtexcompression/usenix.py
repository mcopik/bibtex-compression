
import logging
import re

def remove_redundant_usenix(name):

    """
        Sometimes the extracted name will still contain USENIX or {USENIX}.
        We also want to get rid of the following space
    """

    regex = '{?USENIX}? '
    return re.sub(regex, '', name)

def remove_redundant_parentheses(name):

    """
        Verify if the conference name is not surrounded by parentheses.
        Replace (OSDI 16) -> OSDI 16.
    """
    regex = '[()]'
    return re.sub(regex, '', name)

def extract_series(entry):

    """
        USENIX does not always use a dedicated field for series but it has a very consistent
        naming scheme: XXth USENIX Symposium on Something (Blabla #Year)
        Sometimes words like USENIX or BlaBla can be surrounded by brackets {}
        Additionally, sometimes the name is prefixed with additional USENIX word within parentheses
        We want to extract BlaBla #Year
    """

    if 'series' in entry:
        series = remove_redundant_parentheses(remove_redundant_usenix(entry['series']))
    else:

        name_search = re.search('\({?(USENIX)?}? ?{?[a-zA-Z]+}? [0-9]+\)', entry['booktitle'], re.IGNORECASE)
        if name_search:
            series = remove_redundant_parentheses(remove_redundant_usenix(name_search.group(0)))
        elif 'booktitle' in entry:
            logging.warning(f'Could not extract USENIX conference name from proceedings {entry["booktitle"]}')
            series = entry['booktitle']
        else:
            logging.error('Could not parse USENIX conference name - series and booktitle are missing!')
            raise RuntimeError()


    return series

