"""Run in the distribution repository's GitHub Actions contents-write scope."""
import base64,hashlib,json,os,pathlib,subprocess,urllib.request,urllib.parse
base=pathlib.Path(__file__).parent
meta=json.loads((base/'release-meta.json').read_bytes())
repo=os.environ['GITHUB_REPOSITORY'];assert repo=='saoxxins-netizen/eatwf-launcher'
def api(path,data=None,method=None):
    cmd=['gh','api',path]
    if method:cmd+=['--method',method]
    if data is not None:cmd+=['--input','-']
    p=subprocess.run(cmd,input=json.dumps(data).encode()if data is not None else None,capture_output=True)
    if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace'))
    return json.loads(p.stdout)if p.stdout.strip()else None

# Verify the new asset before removing any archived release.
with urllib.request.urlopen(meta['source'],timeout=180)as response:blob=json.load(response)
assert blob['encoding']=='base64'
raw=base64.b64decode(blob['content']);assert len(raw)==meta['size'] and hashlib.sha256(raw).hexdigest()==meta['sha256']
asset=base/meta['file'];asset.write_bytes(raw)
releases=api(f'repos/{repo}/releases?per_page=100')
allowed={r['id']:r['tag_name']for r in meta['oldReleases']}

matches=[r for r in releases if r['tag_name']==meta['tag']];assert len(matches)<=1
release=matches[0]if matches else api(f'repos/{repo}/releases',dict(tag_name=meta['tag'],target_commitish=os.environ['GITHUB_SHA'],name='EATWF Launcher 0.5.15 / Client 44.1.0.2',body='U44.1 客户端补丁与登录器双通道更新。请先通过官方启动器或 Steam 更新游戏至 2026.10.06.16.12，再使用此登录器安装补丁。',draft=True,prerelease=False),method='POST')
rows=[a for a in release['assets']if a['name']==meta['file']]
if not rows:
    url=release['upload_url'].split('{',1)[0];assert urllib.parse.urlsplit(url).hostname=='uploads.github.com'
    request=urllib.request.Request(url+'?name='+urllib.parse.quote(asset.name),data=raw,headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Content-Type':'application/octet-stream','Accept':'application/vnd.github+json'},method='POST')
    with urllib.request.urlopen(request,timeout=180)as response:rows=[json.load(response)]
assert len(rows)==1 and rows[0]['size']==meta['size'] and rows[0]['digest']=='sha256:'+meta['sha256']
if release['draft']:api(f"repos/{repo}/releases/{release['id']}",dict(draft=False,prerelease=False,make_latest='true'),method='PATCH')
print('VERIFIED launcher 0.5.15 release; previous release retained.')
