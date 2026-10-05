"""Start the packaged simulator with prebuilt UI. Run from any directory."""
import getpass,os,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
os.chdir(root)
if (root/'.env').exists():
    for line in (root/'.env').read_text().splitlines():
        if line.strip() and not line.lstrip().startswith('#') and '=' in line:
            key,value=line.split('=',1);os.environ.setdefault(key.strip(),value.strip().strip('"').strip("'"))
if not os.getenv('ADMIN_PASSWORD'):
    os.environ['ADMIN_PASSWORD']=getpass.getpass('Admin password (12+ characters; used only on first launch): ')
if len(os.environ['ADMIN_PASSWORD'])<12:raise SystemExit('Password must contain at least 12 characters.')
if not (root/'frontend/dist/index.html').exists():raise SystemExit('Build UI first: cd frontend && npm ci && npm run build')
sys.path.insert(0,str(root/'backend'))
import uvicorn
print('Open http://127.0.0.1:8000 — username: admin — simulation only')
uvicorn.run('app.main:app',host='127.0.0.1',port=int(os.getenv('PORT','8000')),workers=1)
