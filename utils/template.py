"""Helper functions for working with templates"""

import os
import re
import string


def render_templatefile(path, **kwargs):
    assert os.path.exists(path)==False,'%s is already exist'%path.split('\\')[-1]
    with open('../templetes/base.tmpl', 'rb') as fp:
        raw = fp.read().decode('utf8')

    content = string.Template(raw).substitute(**kwargs)


    with open(path, 'wb') as fp:
        fp.write(content.encode('utf8'))
    if path.endswith('.tmpl'):
        os.remove(path)


CAMELCASE_INVALID_CHARS = re.compile('[^a-zA-Z\d]')
def string_camelcase(string):
    """ Convert a word  to its CamelCase version and remove invalid chars

    >>> string_camelcase('lost-pound')
    'LostPound'

    >>> string_camelcase('missing_images')
    'MissingImages'

    """
    return CAMELCASE_INVALID_CHARS.sub('', string.title())