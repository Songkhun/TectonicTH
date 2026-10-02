// Headless-Chrome QA for dist/index.html. Usage: node tools/browser_check.mjs "$PWD/dist/index.html" <screenshot-dir>
import { spawn } from 'node:child_process';
import { writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const [html, out] = process.argv.slice(2);
const chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const proc = spawn(chrome, ['--headless=new', '--remote-debugging-port=9333', '--no-first-run', '--no-default-browser-check',
  `--user-data-dir=${mkdtempSync(join(tmpdir(), 'cdp-'))}`, 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let targets;
for (let i = 0; i < 50; i++) { try { targets = await (await fetch('http://127.0.0.1:9333/json')).json(); break; } catch { await sleep(200); } }
const page = targets.find(t => t.type === 'page');
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r));
let id = 0; const pending = new Map(); const logs = [];
ws.addEventListener('message', ev => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  if (m.method === 'Runtime.exceptionThrown') logs.push('EXCEPTION ' + JSON.stringify(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text));
  if (m.method === 'Runtime.consoleAPICalled') logs.push(m.params.type + ' ' + m.params.args.map(a => a.value ?? a.description).join(' '));
});
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async expr => (await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true })).result?.result?.value;
const shot = async name => { const r = await send('Page.captureScreenshot', { format: 'png' }); writeFileSync(join(out, name), Buffer.from(r.result.data, 'base64')); };
const view = (w, h, mobile = false) => send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile });
const report = {};

await send('Runtime.enable'); await send('Page.enable'); await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: 'light' }] });
await view(1440, 900);
await send('Page.navigate', { url: 'file://' + html }); await sleep(1500);
report.title = await ev('document.title');
report.readout_start = await ev("document.getElementById('readout').textContent");
report.rows = await ev("document.querySelectorAll('.tl-row').length");
report.landFill = await ev(`(() => { const c = document.getElementById('globe'); const x = c.getContext('2d');
  const d = x.getImageData(0, 0, c.width, c.height).data; let land = 0, px = 0;
  const lc = getComputedStyle(c).getPropertyValue('--globe-land').trim();
  const [r, g, b] = [1, 3, 5].map(i => parseInt(lc.slice(i, i + 2), 16));
  for (let i = 0; i < d.length; i += 4) { if (d[i + 3] > 0) { px++; if (Math.abs(d[i] - r) < 6 && Math.abs(d[i + 1] - g) < 6 && Math.abs(d[i + 2] - b) < 6) land++; } }
  return +(land / px).toFixed(3); })()`);
await shot('01-desktop-start.png');
// polarity strip
report.pol_strips_on = await ev("document.querySelectorAll('.tl-pol').length");
await ev("document.getElementById('timeline').scrollTop = document.getElementById('timeline').scrollHeight"); await sleep(900);
await shot('01b-polarity-recent.png');
report.pol_tip = await ev("(() => { const s = [...document.querySelectorAll('.tl-pol')].pop(); s.click(); return document.getElementById('poltip').textContent; })()");
await ev("document.getElementById('chk-polarity').click()"); await sleep(300);
report.pol_strips_off = await ev("document.querySelectorAll('.tl-pol').length");
await send('Page.reload'); await sleep(1500);
report.pol_off_after_reload = await ev("!document.getElementById('chk-polarity').checked && document.querySelectorAll('.tl-pol').length === 0");
await ev("document.getElementById('chk-polarity').click()"); await sleep(300);
await ev("document.getElementById('timeline').scrollTop = 0"); await sleep(900);
// scroll through every row; collect distinct readouts
report.readouts = await ev(`(async () => { const tl = document.getElementById('timeline'); const seen = [];
  for (let y = 0; y <= tl.scrollHeight; y += 40) { tl.scrollTop = y; await new Promise(r => setTimeout(r, 60));
    const t = document.getElementById('readout').textContent; if (seen[seen.length - 1] !== t) seen.push(t); }
  return seen; })()`);
report.active_at_bottom = await ev("document.querySelector('.tl-row.is-active')?.title");
await sleep(800); await shot('02-desktop-end.png');
await ev("document.getElementById('timeline').scrollTop = 0"); await sleep(800);
report.active_at_top = await ev("document.querySelector('.tl-row.is-active')?.title");
// card
await ev("document.querySelector('.tl-row.lane-local').click()"); await sleep(200);
report.card = await ev("document.getElementById('card').innerText");
await shot('03-card.png');
// evidence on lecture stops
await ev("document.getElementById('btn-lecture').click()"); await sleep(1200);
report.evidence_by_stop = [];
for (let i = 0; i < 8; i++) {
  report.evidence_by_stop.push(await ev(`({ title: document.querySelector('#card h2')?.innerText, items: document.querySelectorAll('#card .ev-item').length, compare: [...document.querySelectorAll('#card .ev-compare')].map(x => x.textContent) })`));
  if (i === 0) await shot('03b-evidence.png');
  await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'ArrowRight', code: 'ArrowRight' });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'ArrowRight', code: 'ArrowRight' });
  await sleep(900);
}
await ev("document.getElementById('btn-lecture').click()"); await sleep(400);
// language toggle
await ev("document.getElementById('btn-lang').click()"); await sleep(300);
report.lang_after_toggle = await ev("document.documentElement.lang + ' | ' + document.querySelector('.topbar h1').innerText + ' | ' + document.getElementById('readout').textContent + ' | ' + document.getElementById('card').innerText.slice(0, 80)");
report.stored = await ev("localStorage.getItem('dt-lang')");
await send('Page.reload'); await sleep(1500);
report.lang_after_reload = await ev('document.documentElement.lang');
await ev("document.getElementById('btn-lang').click()");
// lecture mode
await ev("document.getElementById('btn-lecture').click()"); await sleep(1200);
const key = async k => { await send('Input.dispatchKeyEvent', { type: 'keyDown', key: k, code: k }); await send('Input.dispatchKeyEvent', { type: 'keyUp', key: k, code: k }); await sleep(900); };
report.lecture_stops = [await ev("document.querySelector('#card h2')?.innerText")];
for (let i = 0; i < 9; i++) { await key('ArrowRight'); report.lecture_stops.push(await ev("document.querySelector('#card h2')?.innerText")); }
report.lecture_scale = await ev("getComputedStyle(document.body).fontSize");
await shot('04-lecture.png');
await key('Escape'); report.lecture_off = await ev("document.body.classList.contains('lecture')");
// about
await ev("document.getElementById('btn-about').click()"); await sleep(200);
report.about = await ev("document.getElementById('about-body').innerText.slice(0, 400)");
await shot('05-about.png'); await ev("document.getElementById('about').close()");
// phone
await view(375, 812, true); await sleep(500); await ev("window.dispatchEvent(new Event('resize'))"); await sleep(600);
report.phone_hscroll = await ev("document.documentElement.scrollWidth > window.innerWidth");
report.phone_globe_h = await ev("Math.round(document.getElementById('globe').getBoundingClientRect().height)");
await ev("document.getElementById('timeline').scrollTop = 600"); await sleep(900);
await shot('06-phone.png');
// dark
await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: 'dark' }] }); await sleep(900);
report.dark_bg = await ev("getComputedStyle(document.body).backgroundColor");
await shot('07-phone-dark.png');
await view(1440, 900); await ev("window.dispatchEvent(new Event('resize'))"); await sleep(900); await shot('08-desktop-dark.png');
// reduced motion
await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
await send('Page.reload'); await sleep(1500);
report.reduced_readout = await ev("document.getElementById('readout').textContent");
report.logs = logs;
console.log(JSON.stringify(report, null, 1));
ws.close(); proc.kill();
