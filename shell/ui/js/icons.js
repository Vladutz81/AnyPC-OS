// Stroke icons, 24x24 grid. Use icon(name) to get inline SVG markup.
const P = {
  search: '<circle cx="11" cy="11" r="6.5"/><path d="M16 16 L21 21"/>',
  gear: '<circle cx="12" cy="12" r="3.2"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.3 5.3l2.1 2.1M16.6 16.6l2.1 2.1M5.3 18.7l2.1-2.1M16.6 7.4l2.1-2.1"/>',
  wifi: '<path d="M3 9.5a13 13 0 0 1 18 0M6 13a8.5 8.5 0 0 1 12 0M9 16.5a4 4 0 0 1 6 0"/><circle cx="12" cy="19.5" r="0.8"/>',
  ethernet: '<rect x="5" y="4" width="14" height="11" rx="1.5"/><path d="M9 15v4M15 15v4M12 15v5M8 8h8M8 11h8"/>',
  pad: '<path d="M7 8h10a4 4 0 0 1 4 4l.6 4.2a2.2 2.2 0 0 1-3.9 1.7L15.5 15h-7l-2.2 2.9a2.2 2.2 0 0 1-3.9-1.7L3 12a4 4 0 0 1 4-4z"/><path d="M8 10.5v3M6.5 12h3"/><circle cx="16" cy="11" r="0.8"/><circle cx="17.5" cy="13" r="0.8"/>',
  bell: '<path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z"/><path d="M10 20.5a2 2 0 0 0 4 0"/>',
  power: '<path d="M7.5 6.5a7.5 7.5 0 1 0 9 0"/><path d="M12 3v8"/>',
  volume: '<path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M15.5 9a4.5 4.5 0 0 1 0 6M18 6.5a8 8 0 0 1 0 11"/>',
  mute: '<path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M16 9.5l5 5M21 9.5l-5 5"/>',
  monitor: '<rect x="3" y="4.5" width="18" height="12" rx="2"/><path d="M9 20h6M12 16.5V20"/>',
  desktop: '<rect x="3" y="4" width="8" height="7" rx="1.5"/><rect x="13" y="4" width="8" height="7" rx="1.5"/><rect x="3" y="13" width="8" height="7" rx="1.5"/><rect x="13" y="13" width="8" height="7" rx="1.5"/>',
  home: '<path d="M4 11l8-6.5 8 6.5v8.5h-5.5v-5h-5v5H4z"/>',
  back: '<path d="M14.5 5.5L8 12l6.5 6.5"/>',
  dots: '<circle cx="6" cy="12" r="1.2"/><circle cx="12" cy="12" r="1.2"/><circle cx="18" cy="12" r="1.2"/>',
  trophy: '<path d="M8 4h8v5a4 4 0 0 1-8 0z"/><path d="M8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M8.5 20h7"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  library: '<rect x="4" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="4" y="13.5" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.5"/>',
  chip: '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9.5 3v3M14.5 3v3M9.5 18v3M14.5 18v3M3 9.5h3M3 14.5h3M18 9.5h3M18 14.5h3"/>',
  storage: '<rect x="4" y="5" width="16" height="6" rx="1.5"/><rect x="4" y="13" width="16" height="6" rx="1.5"/><circle cx="16.5" cy="8" r="0.8"/><circle cx="16.5" cy="16" r="0.8"/>',
  user: '<circle cx="12" cy="8.5" r="3.5"/><path d="M5 20a7 7 0 0 1 14 0"/>',
  refresh: '<path d="M19 12a7 7 0 1 1-2.1-5"/><path d="M17.5 3.5v4h-4"/>',
  access: '<circle cx="12" cy="4.8" r="1.6"/><path d="M5 8.5l7 1.5 7-1.5M12 10v4l-3 6M12 14l3 6"/>',
  globe: '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.5 2.6 3.5 5.4 3.5 8.5s-1 5.9-3.5 8.5c-2.5-2.6-3.5-5.4-3.5-8.5s1-5.9 3.5-8.5z"/>',
  moon: '<path d="M19 14.5A7.5 7.5 0 1 1 9.5 5a6 6 0 0 0 9.5 9.5z"/>',
  play: '<path d="M8 5.5v13l10.5-6.5z" fill="currentColor"/>',
  stop: '<rect x="6.5" y="6.5" width="11" height="11" rx="1.5"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  chevron: '<path d="M9.5 5.5L16 12l-6.5 6.5"/>',
};

export function icon(name, cls = "i") {
  return `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${P[name] || ""}</svg>`;
}

// The AnyPC OS mark: open power ring with an A rising through the gap.
export function mark(size = "2rem", extra = "") {
  return `<svg width="${size}" height="${size}" viewBox="0 0 240 240" aria-hidden="true" ${extra}>
<path d="M162.5 56.4 A85 85 0 1 1 77.5 56.4" fill="none" stroke="#FFFFFF" stroke-width="14" stroke-linecap="round"/>
<path d="M90 158 L120 30 L150 158" fill="none" stroke="#FFFFFF" stroke-width="15" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="120" cy="126" r="10" fill="#FFFFFF"/></svg>`;
}

// Abstract cover glyphs for games without artwork.
export const GLYPHS = [
  '<circle cx="50" cy="50" r="34" fill="none" stroke="rgba(255,255,255,0.55)" stroke-width="7"/>',
  '<path d="M22 78 L50 18 L78 78" fill="none" stroke="rgba(255,255,255,0.55)" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>',
  '<path d="M50 20 L50 80 M20 50 L80 50" fill="none" stroke="rgba(255,255,255,0.55)" stroke-width="8" stroke-linecap="round"/>',
  '<path d="M68 22 A36 36 0 1 1 32 22" fill="none" stroke="rgba(255,255,255,0.55)" stroke-width="7" stroke-linecap="round"/><circle cx="50" cy="56" r="7" fill="rgba(255,255,255,0.55)"/>',
];
