import tempfile
import re
import logging
try:
    from vyos import utils
except ImportError:
    print('Unable to load vyos extention, loading frr config will fail')

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


class FrrError(Exception):
    pass


class ConfigSectionNotFound(FrrError):
    """
    Removal of configuration failed because it is not existing in the supplied configuration
    """
    pass


def _find_first_block(config, start_pattern, stop_pattern, start_at=0):
    '''Find start and stop line numbers for a config block'''
    LOG.debug(f'_find_first_block: find start={repr(start_pattern)} stop={repr(stop_pattern)} start_at={start_at}')
    _start = None
    for i, element in enumerate(config[start_at:], start=start_at):
        # LOG.debug(f'_find_first_block: running line {i:3} "{element}"')
        if not _start:
            if not re.match(start_pattern, element):
                LOG.debug(f'_find_first_block: no match     {i:3} "{element}"')
                continue
            _start = i
            LOG.debug(f'_find_first_block: Found start  {i:3} "{element}"')
            continue

        if not re.match(stop_pattern, element):
            LOG.debug(f'_find_first_block: no match     {i:3} "{element}"')
            continue

        LOG.debug(f'_find_first_block: Found stop   {i:3} "{element}"')
        return (_start, i)

    LOG.debug('_find_first_block: exit start={repr(start_pattern)} stop={repr(stop_pattern)} start_at={start_at}')
    return None


def _find_first_element(config, pattern, start_at=0):
    """Find the first element that matches the current pattern in config
    TODO: for now it returns -1 on a no-match because 0 also returns as False
    TODO: that means that we can not use False matching to tell if its
    """
    for i, element in enumerate(config[start_at:], start=0):
        LOG.debug(f'_find_first_element: running line {i} "{element}"')
        if re.match(pattern + '$', element):
            LOG.debug(f'_find_first_element: Found stop line at {i} "{element}"')
            return i
        LOG.debug(f'_find_first_element: Did not find any match, exiting')
    return -1


def _find_elements(config, pattern, start_at=0):
    """Find all instances of pattern and return a list containing all element indexes"""
    return [i for i, element in enumerate(config[start_at:], start=0) if re.match(pattern + '$', element)]


class frr:
    def __init__(self, config=[]):
        if isinstance(config, list):
            self.config = config.copy()
            self.original_config = config.copy()
        elif isinstance(config, str):
            self.config = config.split('\n')
            self.original_config = config.copy()
        else:
            raise ValueError('The config element needs to be a string or list type object')

    def modify_section(self, start_pattern, replacement=[], stop_pattern=r'\S+', remove_stop_mark=False, count=0):
        if isinstance(replacement, str):
            replacement = replacement.split('\n')
        elif not isinstance(replacement, list):
            return ValueError("The replacement element needs to be a string or list type object")
        LOG.debug(f'modify_section: starting search for {repr(start_pattern)} until {repr(stop_pattern)}')

        _count = 0
        _next_start = 0
        while True:
            if count and count <= _count:
                # Break out of the loop after specified amount of matches
                LOG.debug(f'modify_section: reached element limitexit loop at element {_count}')
                break
            # While searching, always assume that the user wants to search for the exact pattern he entered
            # To be more specific the user needs a override, eg. a "pattern.*"
            _w = _find_first_block(self.config, start_pattern+'$', stop_pattern, start_at=_next_start)
            if not _w:
                # Reached the end, no more elements to remove
                LOG.debug(f'modify_section: didnt find anything more')
                break
            start_element, end_element = _w
            LOG.debug(f'modify_section:   found match between {start_element} and {end_element},' +
                      f'remove and replace old config')
            for i, e in enumerate(self.config[start_element:end_element+1 if remove_stop_mark else end_element],
                                  start=start_element):
                LOG.debug(f'modify_section:   remove       {i:3} {e}')
            del self.config[start_element:end_element+1 if remove_stop_mark else end_element]
            if replacement:
                # Append the replacement config at the current position
                for i, e in enumerate(replacement, start=start_element):
                    LOG.debug(f'modify_section:   replace      {i:3} {e}')
                self.config[start_element:start_element] = replacement
            _count += 1
            _next_start = start_element + len(replacement)

        return _count

    def add_before(self, before_pattern, addition):
        '''Add config block before this element in the configuration'''
        if isinstance(addition, str):
            addition = addition.split('\n')
        elif not isinstance(addition, list):
            return ValueError("The replacement element needs to be a string or list type object")

        start = _find_first_element(self.config, before_pattern)
        if start < 0:
            return False

        self.config[start:start] = addition
        return True

    def __str__(self):
        return '\n'.join(self.config)

    def __repr__(self):
        return f'frr({repr(str(self))})'
