import asyncio, threading, functools, http.server, socketserver, json, re, glob, os
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
H=functools.partial(Q, directory=ROOT)
class S(socketserver.ThreadingTCPServer): allow_reuse_address=True; daemon_threads=True
srv=S(('127.0.0.1',8767),H); threading.Thread(target=srv.serve_forever,daemon=True).start()
B='http://127.0.0.1:8767'
paths=sorted('/'+os.path.dirname(os.path.relpath(f,ROOT))+'/' for f in glob.glob(ROOT+'/**/index.html',recursive=True))
paths=[p.replace('//','/') for p in paths]
JS=open(os.path.join(os.path.dirname(__file__),'audit_js.txt')).read()
from playwright.async_api import async_playwright
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    for name,vp,t in [('mob',{'width':390,'height':844},True),('desk',{'width':1440,'height':900},False)]:
      ctx=await b.new_context(viewport=vp,is_mobile=t,has_touch=t)
      for path in paths:
        pg=await ctx.new_page(); errs=[]; bad=[]
        pg.on('pageerror',lambda e:errs.append(str(e)[:60]))
        pg.on('response',lambda r: bad.append(r.url) if r.status>=400 and '127.0.0.1' in r.url else None)
        await pg.goto(B+path,wait_until='networkidle')
        await pg.evaluate("async()=>{document.querySelectorAll('.rv').forEach(e=>e.classList.add('in'));document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager');await new Promise(r=>setTimeout(r,500))}")
        r=await pg.evaluate(JS); r['errs']=errs; r['404']=bad
        print(name,path,json.dumps(r,ensure_ascii=False)); await pg.close()
      await ctx.close()
    await b.close()
asyncio.run(m()); srv.shutdown()
