import os,sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0,BASE_DIR)
from aioCrawler.utils.template import render_templatefile, string_camelcase
from os.path import join
from sys import argv
import shutil
def _genspider(name):
    spiders_dir = "..\\taskscript\\"
    tvars = {
                'name': name,
                'classname': '%sSpider' % ''.join(s.capitalize() \
                    for s in name.split('_')),
                'routing_key':'%s_request'%name
            }
    spider_file = "%s.py" % join(spiders_dir, name)
    render_templatefile(spider_file, **tvars)


if __name__=="__main__":
    print(argv)
    assert len(argv) == 2, 'func run need 1 parmas,%s given' % (len(argv) - 1)
    _genspider(argv[-1])


