import sys,os; from playwright.sync_api import sync_playwright
fps=30; N=int(15*fps); os.makedirs('ov',exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/opt/pw-browsers/chromium',args=['--allow-file-access-from-files'])
    pg=b.new_page(viewport={'width':1080,'height':1920}); pg.goto('file://'+os.path.abspath('overlay.html'))
    pg.wait_for_function('window.ready===true'); pg.evaluate('document.fonts.ready')
    for i in range(N):
        pg.evaluate(f'seek({i/fps})'); pg.screenshot(path=f'ov/{i:04d}.png',omit_background=True)
    b.close()
print('ok',N)
