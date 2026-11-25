from linkml_map.utils.extensions import safe_function
import re
@safe_function
def regex_int(s, pattern):
    if s is None: return None
    m = re.search(pattern, s)
    return int(m.group(1)) if m else None
@safe_function
def accession_ns(acc):
    if acc is None: return None
    return {'GCA': 'insdc.gca', 'GCF': 'insdc.gcf'}.get(acc[:3], 'unspecified')
@safe_function
def taxon_id(uri):
    return regex_int(uri, r'taxonomy:(\d+)$')
@safe_function(distributes=False)
def zip3(a, b, c):
    return list(zip(a or [], b or [], c or []))
