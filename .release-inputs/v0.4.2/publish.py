import hashlib,json,os,pathlib,subprocess
base=pathlib.Path(__file__).resolve().parent
meta=json.loads((base/'release.json').read_bytes())
asset=base/meta['file']
assert asset.stat().st_size==meta['size'] and hashlib.sha256(asset.read_bytes()).hexdigest()==meta['sha256']
repo=os.environ['GITHUB_REPOSITORY']
assert repo=='saoxxins-netizen/eatwf-launcher'
subprocess.run(['gh','release','create',meta['tag'],str(asset),'--repo',repo,'--target',os.environ['GITHUB_SHA'],'--title','EATWF Launcher 0.4.2','--notes-file',str(base/'RELEASE-NOTES.md'),'--prerelease','--draft'],check=True)
release=json.loads(subprocess.check_output(['gh','api',f"repos/{repo}/releases/tags/{meta['tag']}"]))
rows=[a for a in release['assets'] if a['name']==meta['file']]
assert len(rows)==1 and rows[0]['size']==meta['size'] and rows[0]['digest']=='sha256:'+meta['sha256']
subprocess.run(['gh','release','edit',meta['tag'],'--repo',repo,'--draft=false','--prerelease','--latest=false'],check=True)
print('Verified launcher prerelease published: '+meta['tag'])
