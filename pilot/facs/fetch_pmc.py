"""Fetch flow-cytometry figures from the PMC Open Access subset (AWS bulk service).

Finds papers through E-utilities (figure caption mentions flow cytometry), then
reads each paper's XML and figure files from the public pmc-oa-opendata bucket.
Only figures whose caption mentions flow cytometry / FACS are downloaded.

  python3 fetch_pmc.py --out DIR --n 400 [--start 0] [--years 2019:2024]
"""
import argparse, json, os, re, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

UA = 'figure-integrity-research-pilot/0.1 (python-urllib)'
S3 = 'https://pmc-oa-opendata.s3.amazonaws.com/'
EU = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
PAT = re.compile(r'flow cytometr|FACS|cytometric', re.I)
XL = '{http://www.w3.org/1999/xlink}href'


def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None
            time.sleep(2 * (i + 1))
        except Exception:
            time.sleep(2 * (i + 1))
    return None


def search(n, start, years):
    term = ('"flow cytometry"[Figure/Table Caption] AND open access[filter] '
            'AND %s[pdat]' % years)
    q = urllib.parse.urlencode({'db': 'pmc', 'retmode': 'json', 'retmax': n,
                                'retstart': start, 'term': term})
    d = json.loads(get(EU + '?' + q))
    return d['esearchresult']['idlist'], int(d['esearchresult']['count'])


def text(el):
    return re.sub(r'\s+', ' ', ''.join(el.itertext())).strip() if el is not None else ''


def latest_meta(pmcid):
    for v in (1, 2, 3):
        b = get('%s%s.%d/%s.%d.json' % (S3, pmcid, v, pmcid, v))
        if b:
            last = json.loads(b)
        else:
            break
    else:
        return last
    return last if v > 1 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--n', type=int, default=400)
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--years', default='2019:2024')
    a = ap.parse_args()
    os.makedirs(os.path.join(a.out, 'figs'), exist_ok=True)
    logp = os.path.join(a.out, 'figs.jsonl')
    done = set()
    if os.path.exists(logp):
        done = {json.loads(l)['pmcid'] for l in open(logp)}
    ids, count = search(a.n, a.start, a.years)
    print('search count', count, 'taking', len(ids), flush=True)
    out = open(logp, 'a')
    for k, i in enumerate(ids):
        pmcid = 'PMC' + i
        if pmcid in done:
            continue
        meta = latest_meta(pmcid)
        if not meta or not meta.get('xml_url'):
            out.write(json.dumps({'pmcid': pmcid, 'skip': 'no bulk record'}) + '\n')
            continue
        base = meta['xml_url'].split('s3://pmc-oa-opendata/')[1].split('?')[0].rsplit('/', 1)[0]
        media = {}
        for m in meta.get('media_urls', []):
            name = m.split('/')[-1].split('?')[0]
            media[name.rsplit('.', 1)[0]] = name
        xml = get(S3 + base + '/' + base + '.xml')
        if not xml:
            continue
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            continue
        nfig = 0
        for fig in root.iter('fig'):
            cap = text(fig.find('caption'))
            if not PAT.search(cap):
                continue
            g = fig.find('.//graphic')
            if g is None:
                continue
            href = g.get(XL, '').split('/')[-1]
            name = media.get(href) or media.get(href.rsplit('.', 1)[0])
            if not name or not name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                continue
            b = get(S3 + base + '/' + name)
            if not b:
                continue
            fn = '%s_%s' % (pmcid, name)
            open(os.path.join(a.out, 'figs', fn), 'wb').write(b)
            nfig += 1
            out.write(json.dumps({
                'pmcid': pmcid, 'file': fn, 'fig_id': fig.get('id'),
                'label': text(fig.find('label')), 'caption': cap,
                'license': meta.get('license_code'), 'retracted': meta.get('is_retracted'),
                'title': meta.get('title'), 'citation': meta.get('citation'),
                'doi': meta.get('doi')}) + '\n')
        if nfig == 0:
            out.write(json.dumps({'pmcid': pmcid, 'skip': 'no matching figure file'}) + '\n')
        out.flush()
        print('[%d/%d] %s figs=%d' % (k + 1, len(ids), pmcid, nfig), flush=True)
        time.sleep(0.2)


if __name__ == '__main__':
    main()
