/* Capture the real local app in a fresh browser, never a personal browser profile. */
const path = require('path');
const fs = require('fs');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

(async () => {
  const browser = await chromium.launch({headless:true, executablePath:process.env.EDGE_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
  const context = await browser.newContext({viewport:{width:1440,height:1050}, deviceScaleFactor:1, reducedMotion:'reduce'});
  const page = await context.newPage();
  const url = process.env.FOCUS_URL || 'http://127.0.0.1:8650';
  const out = path.resolve('docs/media'); fs.mkdirSync(out,{recursive:true});
  const errors = [];
  page.on('pageerror', error => errors.push(String(error)));
  await page.goto(url);
  await page.waitForTimeout(2500);
  await page.screenshot({path:path.join(out,'initial-check.png'),fullPage:true});
  await page.getByRole('button',{name:/Explore sample workspace/}).click();
  await page.getByRole('heading',{name:'Make room for what matters, Zubair.'}).waitFor();
  await page.waitForTimeout(900);
  if(process.env.FOCUS_MOBILE_ONLY) {
    await page.getByRole('link',{name:'Projects & board',exact:false}).click();
    await page.getByRole('heading',{name:'From idea to done.'}).waitFor();
    await page.setViewportSize({width:390,height:844});
    await page.waitForTimeout(500);
    await page.locator('[data-testid="stMain"]').evaluate(el=>el.scrollTop=0);
    await page.screenshot({path:path.join(out,'mobile-board.png'),fullPage:true});
    await browser.close();
    console.log('Refreshed clean mobile screenshot');
    return;
  }
  await page.keyboard.press('Control+k');
  await page.getByRole('textbox',{name:'Search tasks and notes',exact:true}).fill('networking');
  await page.getByRole('textbox',{name:'Search tasks and notes',exact:true}).press('Enter');
  await page.getByRole('button',{name:/Study networking fundamentals/}).waitFor();
  await page.keyboard.press('Escape');
  await page.getByRole('textbox',{name:'Search tasks and notes',exact:true}).waitFor({state:'hidden'});
  await page.screenshot({path:path.join(out,'today.png'),fullPage:true});
  async function visit(label, heading, filename) {
    await page.getByRole('link',{name:label,exact:false}).click();
    await page.getByRole('heading',{name:heading,exact:true}).waitFor();
    await page.waitForTimeout(500);
    await page.locator('[data-testid="stMain"]').evaluate(el=>el.scrollTop=0);
    await page.screenshot({path:path.join(out,filename),fullPage:true});
    const exceptions = await page.locator('[data-testid="stException"]').count();
    if(exceptions) throw new Error('Streamlit exception on '+label);
  }
  await visit('Projects & board','From idea to done.','board.png');
  await visit('Notes','A place to think clearly.','notes.png');
  await page.getByRole('tab',{name:'Preview',exact:true}).click();
  await page.waitForTimeout(200);
  await page.screenshot({path:path.join(out,'note-preview.png'),fullPage:true});
  await visit('Focus room','One thing. Your full attention.','focus-setup.png');
  const existing = page.getByRole('button',{name:/Resume/});
  if(await existing.count()) {
    await existing.click();
  } else {
    await page.getByRole('textbox',{name:'Session intention',exact:true}).fill('Refine the landing page');
    await page.getByRole('button',{name:/Start focusing/}).click();
  }
  await page.getByRole('button',{name:/Pause/}).waitFor();
  await page.waitForTimeout(1300);
  await page.screenshot({path:path.join(out,'focus.png'),fullPage:true});
  await page.getByRole('button',{name:/Pause/}).click();
  await page.getByRole('button',{name:/Resume/}).waitFor();
  await visit('Activity & review','Notice the work you have done.','review.png');
  await visit('Settings & backup','Make it feel like yours.','settings.png');
  await page.getByRole('tab',{name:'Export & backup',exact:true}).click();
  await page.waitForTimeout(200);
  await page.screenshot({path:path.join(out,'backup.png'),fullPage:true});
  await page.getByRole('tab',{name:'Appearance & routine',exact:true}).click();
  const compact = page.getByRole('switch',{name:'Compact spacing',exact:true});
  if(!await compact.isChecked()) {
    await compact.focus();
    await compact.press('Space');
  }
  await page.getByRole('button',{name:/Save preferences/}).click();
  // Check mobile overflow on the same authenticated-free local demo session.
  await page.getByRole('link',{name:'Projects & board',exact:false}).click();
  await page.getByRole('heading',{name:'From idea to done.'}).waitFor();
  await page.setViewportSize({width:390,height:844});
  await page.waitForTimeout(500);
  await page.locator('[data-testid="stMain"]').evaluate(el=>el.scrollTop=0);
  const overflow = await page.evaluate(() => ({width:innerWidth,scroll:document.documentElement.scrollWidth}));
  const banner = await page.locator('[data-testid="stAlert"]').first().boundingBox();
  const header = await page.locator('[data-testid="stHeader"]').boundingBox();
  if(banner && header && banner.y < header.y+header.height) throw new Error('Mobile banner overlaps the header');
  await page.screenshot({path:path.join(out,'mobile-board.png'),fullPage:true});
  fs.writeFileSync(path.join(out,'visual-check.json'),JSON.stringify({errors,overflow,quickFindShortcut:true,mobileCompactHeaderClear:true,source:'Real app; separate labelled sample workspace'},null,2));
  console.log(JSON.stringify({errors,overflow,screenshots:fs.readdirSync(out).filter(n=>n.endsWith('.png'))}));
  await browser.close();
})().catch(error=>{console.error(error);process.exit(1);});
