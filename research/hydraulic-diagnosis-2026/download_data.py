import hashlib, urllib.request, zipfile
from pathlib import Path
p=Path("hydraulic_data.zip")
if not p.exists(): urllib.request.urlretrieve("https://archive.ics.uci.edu/static/public/447/condition+monitoring+of+hydraulic+systems.zip",p)
assert hashlib.sha256(p.read_bytes()).hexdigest()=='24128aad2ee45eea7e6b63ebbd9992cdf25d0483a2cebefbfc13bc69079af1f2'
with zipfile.ZipFile(p) as z: z.extractall("data")
