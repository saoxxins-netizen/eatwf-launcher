import hashlib,json,os,pathlib,subprocess,urllib.request,urllib.parse
base=pathlib.Path(__file__).resolve().parent
meta=json.loads((base/'release.json').read_bytes())
asset=base/meta['file']
assert asset.stat().st_size==meta['size'] and hashlib.sha256(asset.read_bytes()).hexdigest()==meta['sha256']
repo=os.environ['GITHUB_REPOSITORY']
assert repo=='saoxxins-netizen/eatwf-launcher'
def api(path,data=None):
    cmd=['gh','api',path]
    if data is not None: cmd+=['--method','POST','--input','-']
    p=subprocess.run(cmd,input=json.dumps(data).encode() if data is not None else None,capture_output=True)
    if p.returncode: raise RuntimeError(p.stderr.decode(errors='replace').strip())
    return json.loads(p.stdout)
try:
    releases=api(f'repos/{repo}/releases?per_page=100')
    matches=[r for r in releases if r['tag_name']==meta['tag']]
    assert len(matches)<=1,'Duplicate version releases'
    if matches:
        release=matches[0]
        print('::notice::Found existing release; draft='+str(release['draft']))
    else:
        release=api(f'repos/{repo}/releases',dict(tag_name=meta['tag'],target_commitish=os.environ['GITHUB_SHA'],name='EATWF Launcher 0.4.2',body=(base/'RELEASE-NOTES.md').read_text(),draft=True,prerelease=True))
        print('::notice::Created release draft')
    rows=[a for a in release['assets'] if a['name']==meta['file']]
    assert len(rows)<=1,'Duplicate asset'
    if not rows:
        assert release['draft'],'Existing published release has no expected asset'
        url=release['upload_url'].split('{',1)[0]
        assert urllib.parse.urlsplit(url).hostname=='uploads.github.com'
        request=urllib.request.Request(url+'?name='+urllib.parse.quote(asset.name),data=asset.read_bytes(),headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Content-Type':'application/octet-stream','Accept':'application/vnd.github+json'},method='POST')
        with urllib.request.urlopen(request,timeout=180) as response: rows=[json.load(response)]
    assert rows[0]['size']==meta['size'] and rows[0]['digest']=='sha256:'+meta['sha256'],'Uploaded asset mismatch'
    print('::notice::Uploaded asset size and digest verified')
    if release['draft']:
        cmd=['gh','api',f"repos/{repo}/releases/{release['id']}",'--method','PATCH','--input','-']
        result=subprocess.run(cmd,input=json.dumps(dict(draft=False,prerelease=True,make_latest='false')).encode(),capture_output=True)
        if result.returncode: raise RuntimeError(result.stderr.decode(errors='replace').strip())
        assert json.loads(result.stdout)['draft'] is False
    print('::notice::Verified launcher prerelease published: '+meta['tag'])
except Exception as error:
    message=(type(error).__name__+': '+str(error)).replace('%','%25').replace('\r','%0D').replace('\n','%0A')
    print('::error::'+message)
    raise
