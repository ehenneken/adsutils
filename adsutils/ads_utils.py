import re
import sys
from Unicode import UnicodeHandler
from config import config
from .utils import *

unicode_file = "%s/%s" % (config.DATA_DIR, config.UNICODE_DATA)
uh = UnicodeHandler(file=unicode_file)

def make_bibcode(data):
    needsIssue = get_data(config.DATA_DIR, config.NEEDS_ISSUE)
    IOPelec    = get_data(config.DATA_DIR, config.IOP_ELECTR)
    JGRstems = ['JGR%s' % let for let in map(chr, range(65, 72))] + ['JGR..']
    # get ingredients to build bibcode
    stem = data.get('bibstem','').strip()
    auth = data.get('author','').strip()
    vol =  data.get('volume','').strip()
    page = data.get('page','').strip()
    year = data.get('year','').strip()
    issue= data.get('issue','').strip()
    # no bibstem or year, no bibcode
    if not stem or not year or not year.isdigit():
        return
    # work on volume
    if vol:
        if stem in IOPelec:
            # IOP electronic volumes have as the first two digits 
            # the publication year
            if vol.isdigit() and int(vol) > 100:
                if len(str(year)) != 4:
                    year = 2000 + int(str(vol)[:2])
                vol = vol % 100
            vol = str(vol).zfill(2)
        elif vol.isdigit():
            vol = re.sub('^0*','',vol)
        else:
            vol = str(vol)
    # Form the journal abbreviation and volume part of bibcode
    if len(stem) > 5 and vol:
        sys.stderr.write('Overriding the volume field in stem "%s"\n'%stem)
        bibstem = stem[:5] + vol
    elif len(stem) > 9:
        sys.stderr.write('Truncating stem "%s"\n'%stem)
        stem = stem[:9]
    elif len(stem) <= 5 and vol:
        bibstem = "%s%s" % (stem.ljust(5,'.'),vol.rjust(4,'.'))
    else:
        bibstem = stem.ljust(9,' ')
    # Special handling for JGR and journals with issues
    if stem in needsIssue and issue:
        page = bib_page("%s:%s"%(issue,page))
    elif stem in JGRstems and len(page) == 6:
        stem, page = jgr_page(stem, page)
        bibstem = "%s%s" % (stem.ljust(5,'.'),vol.rjust(4,'.'))
    elif stem == 'JGR.' and int(year) > 2001:
        if issue.strip().lower() in 'abcdefg':
            biblist = list(bibstem)
            biblist[3] = issue.upper()
            bibstem = ''.join(biblist)
        elif issue:
            sys.stderr.write('Unexpected JGR issue...\n')
        else:
            sys.stderr.write('Expected (but did not find) and issue for JGR after 2001\n')
        page = bib_page(page)
    elif stem in IOPelec:
        page = iopelect_page(page)
    else:
        # 10/26/2010 -- Per Carolyn's request:
        # Can you change the Bibcode module so that if the issue has 
        # an "S" in it, it puts the S in the 14th column?  Think I
        # want only S (not A, B, etc) for the time being.
        if issue and issue[0].upper() == 'S':
            page = "S%s" % page
        if stem[:4] == 'PhRv' and page[-1] == 'R':
            page = page.replace('R','')
            sys.stderr.write('Removed trailing "R" from rapid communication page\n')
        elif stem[:4] == 'PhRv' and page[0] == 'R':
            page = page.replace('R','')
            sys.stderr.write('Removed leading "R" from rapid communication page\n')
        elif stem in ['PLoSO','PASA.'] and page[0] == 'e':
            page = str(int(page[1:]))
        page = bib_page(page)

    bibcode = "%s%s%s" % (year,bibstem,page)

    try:
        auth = uh.u2asc(auth)
    except:
        auth = ''

    try:
        bibcode += re.sub(r'^\s*\W?(\w).*',r'\1',auth).upper()
    except:
        bibcode += '.'

    return bibcode
