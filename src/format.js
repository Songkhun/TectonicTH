export const PRESENT_YEAR = 2026;

function num(x) {
  return Number.isInteger(x) ? String(x) : String(Math.round(x * 10) / 10);
}

export function formatAge(ma, unc, lang, presentYear = PRESENT_YEAR) {
  const th = lang === 'th';
  if (ma === 0) return th ? 'ปัจจุบัน' : 'Present';
  const yearsAgo = ma * 1e6;
  if (yearsAgo < 1000) {
    const ce = Math.round(presentYear - yearsAgo);
    return th ? `พ.ศ. ${ce + 543} (ค.ศ. ${ce})` : `${ce} CE`;
  }
  if (ma < 1) {
    const s = (Math.round(yearsAgo / 100) * 100).toLocaleString('en-US');
    return th ? `≈${s} ปีก่อน` : `≈${s} years ago`;
  }
  const u = unc ? ` ± ${num(unc)}` : '';
  return th ? `${num(ma)}${u} ล้านปีก่อน` : `${num(ma)}${u} Ma`;
}

export function formatLat(lat) {
  return `≈${Math.round(Math.abs(lat))}°${lat < 0 ? 'S' : 'N'}`;
}

const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };

export function esc(s) {
  return s == null ? '' : String(s).replace(/[&<>"']/g, c => ESC[c]);
}
