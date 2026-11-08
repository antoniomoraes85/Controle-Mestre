"""Browser checks: pip install playwright; python tests/browser_intro.py.
Uses installed Chrome and the existing hermetic HTTP fixture, never personal data.
"""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_web_server import WebServerTests
from playwright.sync_api import sync_playwright, expect

fixture = WebServerTests('test_overview_empty_and_healthy')
fixture.setUp()
try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='chrome', headless=True)
        def fresh(**kwargs):
            context = browser.new_context(**kwargs)
            page = context.new_page()
            page.on('dialog', lambda dialog: dialog.dismiss())
            return context, page
        def open_intro(page):
            page.goto(fixture.base, wait_until='domcontentloaded')
            expect(page.locator('.chess-intro')).to_be_visible()
        def gone(page):
            expect(page.locator('.chess-intro')).to_have_count(0, timeout=3500)
            expect(page.locator('#hero-banner')).to_be_visible()
        context, page = fresh(viewport={'width':1440,'height':1000})
        errors=[]
        page.on('pageerror', lambda error: errors.append(str(error)))
        open_intro(page)
        gone(page)
        page.reload(); expect(page.locator('.chess-intro')).to_have_count(0)
        banner=page.locator('#hero-banner')
        expect(banner.locator('.parallax-layer')).to_have_count(5)
        box=banner.bounding_box()
        page.mouse.move(box['x']+box['width']*.85,box['y']+box['height']*.75)
        page.wait_for_timeout(200)
        assert float(banner.evaluate("el=>el.style.getPropertyValue('--px')")) > .5
        assert banner.locator('.layer-bg').evaluate('el=>getComputedStyle(el).transform') != 'none'
        page.mouse.move(0,0); page.wait_for_timeout(200)
        assert float(banner.evaluate("el=>el.style.getPropertyValue('--px')")) == 0
        page.get_by_role('button', name='▶ Estudar hoje', exact=True).click()
        expect(banner).to_have_count(0)
        page.locator('[data-page="home"]').click()
        expect(banner).to_be_visible(); expect(page.locator('.chess-intro')).to_have_count(0)
        assert not errors, errors
        context.close()
        print('PASS first visit, automatic transition, reload, navigation, five layers, parallax and buttons')
        for mode in ('button','escape','focus','motion-change'):
            context,page=fresh(); open_intro(page)
            if mode=='button': page.get_by_role('button',name='Pular introdução').click()
            elif mode=='escape': page.keyboard.press('Escape')
            elif mode=='focus': page.locator('#timer-start').focus()
            else: page.emulate_media(reduced_motion='reduce')
            gone(page); context.close()
            print('PASS',mode)
        context,page=fresh(reduced_motion='reduce')
        page.goto(fixture.base); gone(page)
        assert page.locator('.layer-bg').evaluate('el=>getComputedStyle(el).transform')=='none'
        assert page.locator('.p-dot').first.evaluate('el=>getComputedStyle(el).animationName')=='none'
        context.close(); print('PASS reduced motion')
        for resource in ('**/modules/intro.js','**/assets/branding/logo_horizontal_premium.svg','**/style.css'):
            context,page=fresh(); page.route(resource,lambda route:route.abort())
            page.goto(fixture.base); gone(page); context.close()
            print('PASS failed resource',resource)
        context,page=fresh()
        page.add_init_script("Object.defineProperty(window,'sessionStorage',{get(){throw new Error('denied')}})")
        page.goto(fixture.base); gone(page); context.close(); print('PASS denied storage')
        context,page=fresh()
        page.route('**/style.css',lambda route:route.fulfill(path=str(Path(__file__).parent.parent/'web/style.css'),content_type='text/css'))
        open_intro(page)
        page.add_style_tag(content='.chess-intro{animation:none!important}')
        gone(page);context.close();print('PASS watchdog without animationend')
        context,page=fresh(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
        open_intro(page)
        assert page.locator('.intro-skip').bounding_box()['x']>=0
        gone(page)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        banner=page.locator('#hero-banner')
        assert banner.locator('.layer-chess-scene').evaluate('el=>getComputedStyle(el).display')=='none'
        page.get_by_role('button',name='▶ Estudar hoje',exact=True).click()
        expect(banner).to_have_count(0)
        context.close();print('PASS mobile layout and navigation')
        # Freeze only for visual review; lifecycle was verified above without freezing.
        for width,height,label in ((1440,1000,'desktop'),(390,844,'mobile')):
            context,page=fresh(viewport={'width':width,'height':height})
            page.clock.install()
            open_intro(page)
            page.evaluate('document.getAnimations().forEach(a=>{a.pause();a.currentTime=1950})')
            page.screenshot(path=str(Path(__file__).parent.parent/f'intro-{label}.png'))
            context.close()
        browser.close()
finally:
    fixture.tearDown()
    fixture.doCleanups()
