#!/usr/bin/env python3
"""Assemble local test IPKs from explicit dirty sources; never a feed/release build.

Executes the runtime and metadata install recipes with GNU make, stages LuCI
without minification, and uses the supplied, checksummed OpenWrt ipkg-build.
No SDK state, feed, system package database or release pointer is modified.
"""
import argparse, hashlib, json, os, re, shutil, subprocess, tarfile
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--binary-dir',type=Path,required=True)
p.add_argument('--tools',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
root=Path(__file__).resolve().parents[1]
out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
tools=a.tools.resolve()
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
version=re.search(r'^PKG_VERSION:=(.+)$',(root/'fastnet/Makefile').read_text(),re.M)[1]
assert version=='0.8.2'
record={'scope':'local source candidate; explicit inputs; not a canonical feed build or publication','version':version,'sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'tools':{n:digest(tools/n) for n in ['ipkg-build','meta.mk','po2lmo']},'sourceFiles':{str(f.relative_to(root)):digest(f) for f in sorted(root.rglob('*')) if f.is_file() and '__pycache__' not in str(f)},'packages':[]}
# Deterministic runtime archive is the exact future PKG_SOURCE input.
runtime=out/'runtime'/('fastnet-binary-'+version);runtime.mkdir(parents=True,exist_ok=True)
for arch in ['x86_64','aarch64','arm']:shutil.copy2(a.binary_dir/('FastNet.'+arch),runtime/('FastNet.'+arch))
(runtime/'version.txt').write_text('VERSION='+version+'\n'+''.join('FASTNET_'+arch.upper()+'_SHA256='+digest(runtime/('FastNet.'+arch))+'\n' for arch in ['x86_64','aarch64','arm']))
archive=out/(runtime.name+'.tar.gz')
import gzip
with archive.open('wb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,filename='') as gz,tarfile.open(fileobj=gz,mode='w') as tar:
 for f in sorted(runtime.rglob('*')):
  if f.is_file():
   item=tar.gettarinfo(str(f),runtime.name+'/'+f.name);item.uid=item.gid=item.mtime=0;item.uname=item.gname='';tar.addfile(item,f.open('rb'))
record['runtime']={'path':str(archive),'sha256':digest(archive)}
harness=out/'recipe-harness';(harness/'include').mkdir(parents=True,exist_ok=True)
(harness/'rules.mk').write_text('')
(harness/'include/package.mk').write_text('')
collection=out/'source';shutil.copytree(root,collection/'fastnet',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
shutil.copy2(tools/'meta.mk',collection/'meta.mk')
def run_recipe(name,destination,arch):
 cwd=collection/'fastnet'/name
 make=harness/(name+'.mk')
 make.write_text(f'''empty:=
space:=$(empty) $(empty)
comma:=,
define newline


endef
TOPDIR:={harness}
INCLUDE_DIR:={harness}/include
BUILD_DIR:={out}/runtime
ARCH:={arch}
INSTALL_DIR:=install -d -m0755
INSTALL_BIN:=install -m0755
INSTALL_DATA:=install -m0644
INSTALL_CONF:=install -m0600
include {cwd}/Makefile
stage:
\t$(call Package/{name}/install,{destination})
hooks:
\t$(if $(Package/{name}/postinst),$(file >{destination}/CONTROL/postinst,$(Package/{name}/postinst)))
\t$(if $(Package/{name}/prerm),$(file >{destination}/CONTROL/prerm,$(Package/{name}/prerm)))
''')
 # Standalone postinst scripts have been rendered by the actual make recipes.
 subprocess.run(['make','--no-print-directory','-f',str(make),'stage','hooks'],cwd=cwd,check=True,stdout=subprocess.DEVNULL)
def package(name,version,arch,depends,payload):
 control=payload/'CONTROL';control.mkdir(parents=True,exist_ok=True)
 (control/'control').write_text(f'Package: {name}\nVersion: {version}\nArchitecture: {arch}\nMaintainer: FastNet local candidate\nSection: net\nPriority: optional\nDescription: FastNet explicit source candidate\n'+('Depends: '+depends+'\n' if depends else ''))
 for f in control.iterdir():f.chmod(0o755 if f.name in ['postinst','prerm'] else 0o644)
 env={**os.environ,'SOURCE_DATE_EPOCH':'0'}
 subprocess.run(['fakeroot','sh','-c','chown -R 0:0 "$1"; exec sh "$2" "$1" "$3"','candidate',str(payload),str(tools/'ipkg-build'),str(out/'ipk')],check=True,env=env,stdout=subprocess.DEVNULL)
 ipk=out/'ipk'/f'{name}_{version}_{arch}.ipk'
 assert ipk.is_file(),ipk
 record['packages'].append({'path':str(ipk),'name':name,'version':version,'arch':arch,'sha256':digest(ipk),'depends':depends,'files':{str(f.relative_to(payload)):digest(f) for f in sorted(payload.rglob('*')) if f.is_file() and not f.is_symlink()}})
(out/'ipk').mkdir(exist_ok=True)
for arch in ['x86_64','aarch64']:
 dest=out/'payload'/arch/'fastnet';(dest/'CONTROL').mkdir(parents=True,exist_ok=True)
 run_recipe('fastnet',dest,arch)
 (dest/'CONTROL/conffiles').write_text('/etc/config/fastnet\n')
 package('fastnet',version+'-1','aarch64_generic' if arch=='aarch64' else arch,'linkease-app-entry',dest)
dest=out/'payload/all/luci-app-fastnet';(dest/'CONTROL').mkdir(parents=True,exist_ok=True)
shutil.copytree(root/'luci-app-fastnet/luasrc',dest/'usr/lib/lua/luci',dirs_exist_ok=True)
shutil.copytree(root/'luci-app-fastnet/root',dest,dirs_exist_ok=True)
text=(root/'luci-app-fastnet/Makefile').read_text()
for hook in ['postinst','prerm']:
 body=re.search(r'define Package/luci-app-fastnet/'+hook+r'\n(.*?)\nendef',text,re.S)[1]
 (dest/'CONTROL'/hook).write_text(body.replace('$$','$')+'\n')
package('luci-app-fastnet',version+'-r1','all','fastnet (>= 0.8.2-1), luci-lib-linkeaseauth, linkease-app-entry, luci-lua-runtime',dest)
dest=out/'payload/all/luci-i18n-fastnet-zh-cn';(dest/'usr/lib/lua/luci/i18n').mkdir(parents=True,exist_ok=True)
subprocess.run([str(tools/'po2lmo'),str(root/'luci-app-fastnet/po/zh-cn/fastnet.po'),str(dest/'usr/lib/lua/luci/i18n/fastnet.zh-cn.lmo')],check=True)
package('luci-i18n-fastnet-zh-cn',re.search(r'^PKG_PO_VERSION:=(.+)$',text,re.M)[1],'all','luci-app-fastnet',dest)
dest=out/'payload/all/app-meta-fastnet';(dest/'CONTROL').mkdir(parents=True,exist_ok=True)
run_recipe('app-meta-fastnet',dest,'x86_64')
package('app-meta-fastnet',version+'-10','all','fastnet (>= 0.8.2-1), luci-app-fastnet (>= 0.8.2-r1), luci-i18n-fastnet-zh-cn',dest)
(out/'candidate.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'packages':len(record['packages']),'runtimeSha256':record['runtime']['sha256']}))
