import importlib.util,json,os,re,subprocess,tarfile,tempfile,unittest,io
from pathlib import Path
H=Path(__file__).resolve().parents[3]
class Contract(unittest.TestCase):
 def test_dependencies_and_entries(self):
  for path,dep in [('optimemachine/optimemachine','+linkspace'),('kaiplus/kaiplus','+optimemachine')]:
   self.assertIn(dep,(H/'apps'/path/'Makefile').read_text())
  manifest=json.loads((H/'apps/optimemachine/optimemachine/files/usr/share/optimemachine/optimemachine-plugin.json').read_text())
  self.assertEqual(manifest['backend']['transport'],'unix');self.assertEqual(manifest['standalone']['basePath'],'/apps/optimemachine/')
  for package in ['optimemachine','linkspace']:
   release=(H/'apps'/package/package/'release.mk').read_text();self.assertEqual(len(re.findall(r'HASH_(?:x86_64|aarch64):=[0-9a-f]{64}',release)),2)
 def test_candidate_hooks_and_descriptor_ownership(self):
  report=json.loads(Path(os.environ['OTM_CANDIDATE_PACKAGES']).read_text())
  for name,item in report['packages'].items():
   with tarfile.open(item['path'],'r:gz') as outer:
    control=tarfile.open(fileobj=io.BytesIO(outer.extractfile('./control.tar.gz').read()),mode='r:gz')
    data=tarfile.open(fileobj=io.BytesIO(outer.extractfile('./data.tar.gz').read()),mode='r:gz')
    names=data.getnames()
    self.assertEqual('./usr/share/linkspace/dependency.json' in names,name=='linkspace')
    self.assertNotIn('./usr/share/optimemachine/dependency.json',names)
    with tempfile.TemporaryDirectory() as folder:
     root=Path(folder);data.extractall(root,filter='fully_trusted')
     keep=root/'existing-backup';keep.write_text('preserved')
     for phase in ['preinst','postinst','prerm']:
      try:body=control.extractfile('./'+phase).read()
      except KeyError:continue
      script=root/(phase+'.sh');script.write_bytes(body);subprocess.run(['sh','-n',str(script)],check=True);subprocess.run(['sh',str(script)],env={**os.environ,'IPKG_INSTROOT':str(root)},check=True)
     self.assertEqual(keep.read_text(),'preserved')
if __name__=='__main__':unittest.main()
