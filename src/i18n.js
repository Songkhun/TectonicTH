export const I18N_STRINGS = {
  th: {
    app_title: 'ย้อนเวลาธรณีกาญจนบุรี',
    app_subtitle: 'ประวัติธรณีวิทยากาญจนบุรีเทียบกับโลก บนลูกโลกยุคโบราณ',
    btn_lecture: 'โหมดบรรยาย',
    btn_about: 'เกี่ยวกับ',
    btn_lang: 'English',
    lane_period: 'ยุค',
    lane_local: 'กาญจนบุรี',
    lane_world: 'เอเชียตะวันออกเฉียงใต้และโลก',
    lane_life: 'ชีวิต',
    draft: 'ร่าง',
    visit: 'ดูของจริงได้ที่',
    source: 'ที่มา',
    approx_slice: 'ตำแหน่งจากแบบจำลองช่วงอายุใกล้เคียง',
    paleo_label: 'กาญจนบุรีอยู่ที่',
    ma_short: 'ล้านปีก่อน',
    prev: 'ก่อนหน้า',
    next: 'ถัดไป',
    close: 'ปิด',
    globe_label: 'ลูกโลกแสดงตำแหน่งกาญจนบุรีในอดีต',
    about_title: 'เกี่ยวกับหน้านี้',
    about_intro: 'สื่อการสอนของสาขาวิชาธรณีศาสตร์ มหาวิทยาลัยมหิดล วิทยาเขตกาญจนบุรี เลื่อนเส้นเวลาเพื่อดูว่ากาญจนบุรีอยู่ที่ใดบนโลกในแต่ละยุค',
    credit_model: 'แบบจำลองแผ่นธรณี: Torsvik & Cocks (2017) ผ่าน GPlates Web Service (EarthByte)',
    credit_timescale: 'ตารางธรณีกาล: International Commission on Stratigraphy (ICS)',
    credit_inspiration: 'แรงบันดาลใจ: เว็บ “สยามและโลก เส้นเวลาคู่ขนาน”',
    citations_heading: 'แหล่งอ้างอิงของเหตุการณ์',
  },
  en: {
    app_title: 'Deep Time Kanchanaburi',
    app_subtitle: "Kanchanaburi's geologic history beside the world's, on an ancient globe",
    btn_lecture: 'Lecture mode',
    btn_about: 'About',
    btn_lang: 'ไทย',
    lane_period: 'Period',
    lane_local: 'Kanchanaburi',
    lane_world: 'SE Asia & world',
    lane_life: 'Life',
    draft: 'Draft',
    visit: 'See it at',
    source: 'Source',
    approx_slice: '≈ position from nearest reconstruction',
    paleo_label: 'Kanchanaburi at',
    ma_short: 'Ma',
    prev: 'Previous',
    next: 'Next',
    close: 'Close',
    globe_label: "Globe showing Kanchanaburi's past position",
    about_title: 'About this page',
    about_intro: 'A teaching resource from the Geoscience Division, Mahidol University Kanchanaburi Campus. Scroll the timeline to see where Kanchanaburi was on Earth at each time.',
    credit_model: 'Plate model: Torsvik & Cocks (2017), via the GPlates Web Service (EarthByte)',
    credit_timescale: 'Time scale: International Commission on Stratigraphy (ICS)',
    credit_inspiration: 'Inspired by the “Siam & World parallel timeline”',
    citations_heading: 'Event sources',
  },
};

const STORAGE_KEY = 'dt-lang';
let lang = 'th';
let store = null;
const listeners = [];

export function initLang(storage) {
  store = storage;
  let saved = null;
  try { saved = storage ? storage.getItem(STORAGE_KEY) : null; } catch (_) { saved = null; }
  lang = saved === 'en' ? 'en' : 'th';
  return lang;
}

export function getLang() { return lang; }

export function setLang(next) {
  if (next !== 'th' && next !== 'en') return;
  lang = next;
  try { if (store) store.setItem(STORAGE_KEY, next); } catch (_) { /* storage blocked */ }
  listeners.forEach(fn => fn(next));
}

export function onLangChange(fn) { listeners.push(fn); }

export function t(key) {
  return I18N_STRINGS[lang][key] ?? I18N_STRINGS.en[key] ?? key;
}

export function field(obj, base) {
  return obj[`${base}_${lang}`] || obj[`${base}_en`] || '';
}
