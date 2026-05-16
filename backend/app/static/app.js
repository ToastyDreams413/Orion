const state = {
  data: null,
  selectedId: null,
  currentTab: 'summary',
  playing: false,
  guided: true,
  demoActive: false,
  demoStep: 0,
  speed: 1.0,
  showPred: true,
  showTrails: true,
  showEllipses: true,
  showLabels: true,
  showCatalog: true,
  view3d: false,
  viewer: null,
  region: 'Southern California',
  leftView: 'ops',
  rightView: 'inspect',
  sensorMode: 'simple',
  mapZoom: 1,
  globeNeedsFrame: false,
  cameraPreset: 'angled',
  mapPanX: 0,
  mapPanY: 0,
  dragging2D: false,
  lastDragX: 0,
  lastDragY: 0,
  expandedPanel: null,
  leftCollapsed: false,
  rightCollapsed: false,
  globePanTimer: null,
};

const REGIONS = {
  'Southern California': { lat: 33.62, lon: -117.93, cameraHeight: 120000, heading: 0.05, pitch: -1.18 },
  'Bay Area': { lat: 37.62, lon: -122.32, cameraHeight: 125000, heading: 0.05, pitch: -1.18 },
  'Nevada Test Range': { lat: 37.31, lon: -116.04, cameraHeight: 130000, heading: 0.02, pitch: -1.18 },
  'Pacific Northwest': { lat: 47.57, lon: -122.35, cameraHeight: 135000, heading: 0.0, pitch: -1.18 },
  'East Coast': { lat: 39.05, lon: -76.72, cameraHeight: 125000, heading: 0.06, pitch: -1.18 },
};


const GLOBAL_TRACK_GEO = {
  mixed_airspace: {
    A1: { lat: 34.3, lon: -130.0, area: 'Pacific approach corridor' },
    F2: { lat: 32.8, lon: -117.6, area: 'US coastal patrol' },
    D7: { lat: 33.95, lon: -118.28, area: 'Los Angeles basin' },
    U3: { lat: 55.7, lon: -161.0, area: 'Alaska approach' },
  },
  storm_intrusion: {
    WX1: { lat: 45.7, lon: -126.8, area: 'Pacific Northwest offshore' },
    JAM1: { lat: 47.4, lon: -122.4, area: 'Puget Sound electronic interference' },
    UNK2: { lat: 48.9, lon: -124.9, area: 'Northwest coastal track' },
    CM1: { lat: 41.2, lon: -146.0, area: 'North Pacific low-altitude approach' },
  },
  drone_swarm: {
    AUX1: { lat: 37.0, lon: -122.9, area: 'Bay Area support track' },
    SW1: { lat: 37.78, lon: -122.45, area: 'Bay Area swarm' },
    SW2: { lat: 37.88, lon: -122.21, area: 'Bay Area swarm' },
    SW3: { lat: 37.65, lon: -121.95, area: 'Bay Area swarm' },
    SW4: { lat: 37.46, lon: -122.05, area: 'Bay Area swarm' },
    SW5: { lat: 37.34, lon: -122.30, area: 'Bay Area swarm' },
    SW6: { lat: 37.48, lon: -122.55, area: 'Bay Area swarm' },
    SW7: { lat: 37.70, lon: -122.67, area: 'Bay Area swarm' },
    SW8: { lat: 37.94, lon: -122.57, area: 'Bay Area swarm' },
    SW9: { lat: 38.02, lon: -122.32, area: 'Bay Area swarm' },
    SW10: { lat: 37.58, lon: -122.18, area: 'Bay Area swarm' },
  },
  ballistic_approach: {
    BM1: { lat: 58.5, lon: -164.5, area: 'Alaska / Arctic approach' },
    BM2: { lat: 31.0, lon: -151.0, area: 'Pacific ballistic track' },
    CR1: { lat: 35.4, lon: -124.7, area: 'California coastal cruise track' },
    CIV1: { lat: 36.7, lon: -119.8, area: 'Central California civil corridor' },
  },
  orbital_pass: {
    SAT1: { lat: 39.0, lon: -104.5, area: 'orbital pass ground track' },
    SAT2: { lat: 28.5, lon: -80.6, area: 'orbital pass ground track' },
    DEB1: { lat: 43.0, lon: -90.0, area: 'orbital debris ground track' },
  },
  asteroid_pass: {
    NEO1: { lat: 34.8, lon: -111.7, area: 'Southwest projected corridor' },
    X1: { lat: 40.1, lon: -103.7, area: 'Central US anomalous contact' },
  },
  layered_defense_drill: {
    CIV1: { lat: 40.0, lon: -74.5, area: 'Northeast civil corridor' },
    PAT1: { lat: 38.9, lon: -77.0, area: 'National Capital Region patrol' },
    LOW1: { lat: 36.2, lon: -75.6, area: 'Atlantic low-altitude approach' },
    UAS1: { lat: 38.3, lon: -76.9, area: 'Chesapeake restricted airspace' },
    UNK1: { lat: 42.4, lon: -71.1, area: 'New England uncorrelated radar' },
  },
  false_alarm_filter: {
    MED1: { lat: 38.7, lon: -121.5, area: 'Northern California support flight' },
    CIV2: { lat: 33.9, lon: -118.4, area: 'Los Angeles civil corridor' },
    BAL1: { lat: 39.7, lon: -104.9, area: 'Denver balloon-like reflector' },
    DR1: { lat: 32.9, lon: -117.1, area: 'San Diego survey drone' },
  },
  live_public_blend: {
    A1: { lat: 34.1, lon: -135.0, area: 'Pacific civil corridor' },
    F2: { lat: 32.6, lon: -117.2, area: 'San Diego coastal patrol' },
    MS1: { lat: 47.6, lon: -152.0, area: 'North Pacific high-speed contact' },
    SAT2: { lat: 31.0, lon: -95.0, area: 'orbital pass ground track' },
    NEO1: { lat: 39.3, lon: -112.0, area: 'western US projected corridor' },
    D7: { lat: 34.0, lon: -118.2, area: 'Los Angeles unknown UAS' },
  },
};

const US_PROTECTED_AIRSPACES = [
  { id: 'NCR', name: 'National Capital Region', lat: 38.90, lon: -77.04, radius: 145000, level: 'critical' },
  { id: 'NORAD', name: 'Cheyenne / NORAD corridor', lat: 38.74, lon: -104.85, radius: 120000, level: 'critical' },
  { id: 'VAND', name: 'Vandenberg launch range', lat: 34.74, lon: -120.57, radius: 115000, level: 'suspicious' },
  { id: 'SD', name: 'San Diego naval airspace', lat: 32.72, lon: -117.16, radius: 90000, level: 'suspicious' },
  { id: 'PS', name: 'Puget Sound defense corridor', lat: 47.62, lon: -122.33, radius: 95000, level: 'suspicious' },
  { id: 'NY', name: 'New York airspace', lat: 40.71, lon: -74.00, radius: 105000, level: 'suspicious' },
  { id: 'LA', name: 'Los Angeles airspace', lat: 34.05, lon: -118.24, radius: 95000, level: 'suspicious' },
  { id: 'AK', name: 'Alaska early-warning corridor', lat: 64.84, lon: -147.72, radius: 180000, level: 'suspicious' },
];

function scenarioGeoForTrack(tr) {
  const scenario = state.data?.settings?.scenario || scenarioSel?.value || 'mixed_airspace';
  const table = GLOBAL_TRACK_GEO[scenario] || {};
  const base = table[tr.id];
  if (base) return base;
  // Deterministic fallback for user-injected objects. High-risk objects appear outside the US and aircraft/drone tracks appear near US airspace.
  let h = 0;
  for (const ch of String(tr.id || 'X')) h = ((h * 31) + ch.charCodeAt(0)) >>> 0;
  const risk = ['missile','asteroid','foreign_spaceship','unknown'].includes(tr.class_type);
  const anchors = risk
    ? [{lat: 51, lon: -168}, {lat: 24, lon: -151}, {lat: 38, lon: -52}, {lat: 56, lon: -96}]
    : [{lat: 34, lon: -118}, {lat: 38, lon: -122}, {lat: 40, lon: -74}, {lat: 47, lon: -122}, {lat: 32, lon: -97}];
  const a = anchors[h % anchors.length];
  return { lat: a.lat + (((h >> 8) % 90) - 45) / 30, lon: a.lon + (((h >> 16) % 120) - 60) / 20, area: risk ? 'outer US approach sector' : 'US airspace sector' };
}

function usThreatPosture(tr) {
  if (!tr) return 'monitor';
  if (tr.class_type === 'missile' || tr.class_type === 'foreign_spaceship' || tr.class_type === 'asteroid') return 'priority-threat';
  if (tr.threat_level === 'critical') return 'priority-threat';
  if (tr.threat_level === 'suspicious' || tr.class_type === 'unknown' || (tr.class_type === 'drone' && !tr.sensor?.transponder)) return 'watchlist';
  return 'routine';
}

function shouldShowTrackOnGlobe(tr) {
  // Satellites/debris are still in the analytical model, but the globe view emphasizes Earth/airspace objects that operators act on.
  return !['satellite','debris'].includes(tr.class_type);
}


const SCENARIO_PRESETS = {
  mixed_airspace: { weather: 'clear', wind: 0.18, visibility: 0.95, jamming: 0.06, hazard: 0.10, region: 'Southern California' },
  storm_intrusion: { weather: 'storm', wind: 0.68, visibility: 0.42, jamming: 0.48, hazard: 0.65, region: 'Pacific Northwest' },
  drone_swarm: { weather: 'clear', wind: 0.10, visibility: 0.96, jamming: 0.18, hazard: 0.16, region: 'Bay Area' },
  ballistic_approach: { weather: 'clear', wind: 0.22, visibility: 0.92, jamming: 0.08, hazard: 0.48, region: 'Nevada Test Range' },
  orbital_pass: { weather: 'clear', wind: 0.04, visibility: 0.98, jamming: 0.02, hazard: 0.08, region: 'Southern California' },
  asteroid_pass: { weather: 'clear', wind: 0.05, visibility: 0.99, jamming: 0.00, hazard: 0.22, region: 'East Coast' },
  live_public_blend: { weather: 'clear', wind: 0.16, visibility: 0.93, jamming: 0.12, hazard: 0.14, region: 'Southern California' },
  layered_defense_drill: { weather: 'clear', wind: 0.20, visibility: 0.88, jamming: 0.20, hazard: 0.24, region: 'Southern California' },
  false_alarm_filter: { weather: 'fog', wind: 0.25, visibility: 0.58, jamming: 0.10, hazard: 0.12, region: 'Bay Area' },
};

const $ = sel => document.querySelector(sel);
const scenarioSel = $('#scenario');
const weatherSel = $('#weather');
const wind = $('#wind');
const visibility = $('#visibility');
const jamming = $('#jamming');
const hazardIntensity = $('#hazardIntensity');
const objectSelect = $('#objectSelect');
const speedSelect = $('#speedSelect');
const addObjectKind = $('#addObjectKind');
const regionSelect = $('#regionSelect'); // removed from UI in global mode; kept optional for legacy code
const cameraPresetSelect = $('#cameraPresetSelect');
const responseObjectSelect = document.getElementById('responseObjectSelect');
const renameObjectInput = document.getElementById('renameObjectInput');

function severityRank(level) {
  return ({ benign: 0, unknown: 1, suspicious: 2, critical: 3 })[level] ?? 0;
}

function selectedTrack() {
  if (!state.data?.tracks?.length) return null;
  return state.data.tracks.find(t => t.id === state.selectedId) || state.data.tracks[0] || null;
}

function trackDisplayName(tr, includeType = false) {
  if (!tr) return '';
  const label = tr.label && tr.label !== tr.id ? ` — ${tr.label}` : '';
  const type = includeType ? ` · ${tr.class_type}` : '';
  return `${tr.id}${label}${type}`;
}

function pickDemoTrack() {
  if (!state.data?.tracks?.length) return null;
  return [...state.data.tracks].sort((a, b) => {
    const s = severityRank(b.threat_level) - severityRank(a.threat_level);
    if (s !== 0) return s;
    return (a.ttz ?? 999999) - (b.ttz ?? 999999);
  })[0];
}


function applyScenarioPreset(name) {
  const p = SCENARIO_PRESETS[name];
  if (!p) return;
  weatherSel.value = p.weather;
  wind.value = p.wind;
  visibility.value = p.visibility;
  jamming.value = p.jamming;
  hazardIntensity.value = p.hazard;
  state.region = p.region;
}

function scenarioAccent(name) {
  return ({
    mixed_airspace:'#7db7ff', storm_intrusion:'#ff5b72', drone_swarm:'#ffbe4d', ballistic_approach:'#ff845b', orbital_pass:'#b18cff', asteroid_pass:'#89e7d0', live_public_blend:'#9ad1ff', layered_defense_drill:'#54d38a', false_alarm_filter:'#ffd27a'
  })[name] || '#7db7ff';
}

function drawRegionBackdrop(ctx, canvas) {
  const name = state.region;
  ctx.save();
  ctx.globalAlpha = 1;
  // sea/land split
  ctx.fillStyle = 'rgba(13,34,58,0.9)';
  ctx.fillRect(0,0,canvas.width,canvas.height);
  ctx.fillStyle = 'rgba(25,58,42,0.30)';
  const coastOffset = ({'Southern California':0.22,'Bay Area':0.18,'Nevada Test Range':-1,'Pacific Northwest':0.2,'East Coast':0.78})[name] ?? 0.22;
  if (coastOffset >= 0) {
    const x0 = canvas.width * coastOffset;
    ctx.beginPath();
    ctx.moveTo(x0,0);
    for (let y=0; y<=canvas.height; y+=80) {
      const wobble = Math.sin(y/90)*18 + Math.cos(y/47)*8;
      ctx.lineTo(x0 + wobble, y);
    }
    ctx.lineTo(canvas.width, canvas.height); ctx.lineTo(canvas.width,0); ctx.closePath();
    ctx.fill();
    ctx.strokeStyle = 'rgba(149, 214, 183, 0.32)'; ctx.lineWidth=2; ctx.stroke();
  }
  // roads / corridors
  ctx.strokeStyle='rgba(255,255,255,0.06)'; ctx.lineWidth=2;
  [[0.12,0.75,0.88,0.22],[0.18,0.18,0.84,0.82],[0.05,0.52,0.95,0.56]].forEach(([x1,y1,x2,y2])=>{
    ctx.beginPath(); ctx.moveTo(canvas.width*x1,canvas.height*y1); ctx.lineTo(canvas.width*x2,canvas.height*y2); ctx.stroke();
  });
  // location label & compass
  ctx.fillStyle='rgba(234,245,255,0.82)'; ctx.font='14px sans-serif'; ctx.textAlign='left';
  ctx.fillText(name, 18, 26);
  ctx.fillStyle='rgba(234,245,255,0.36)'; ctx.font='12px sans-serif';
  ctx.fillText('Regional tactical view', 18, 44);
  ctx.strokeStyle='rgba(234,245,255,0.35)'; ctx.lineWidth=2;
  ctx.beginPath(); ctx.moveTo(canvas.width-38,58); ctx.lineTo(canvas.width-38,24); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(canvas.width-44,30); ctx.lineTo(canvas.width-38,18); ctx.lineTo(canvas.width-32,30); ctx.stroke();
  ctx.fillStyle='rgba(234,245,255,0.7)'; ctx.fillText('N', canvas.width-46, 72);
  ctx.restore();
}

function drawEnvironmentOverlay(ctx, canvas, view) {
  // weather haze
  if (weatherSel.value === 'fog') {
    ctx.fillStyle = 'rgba(220,230,240,0.10)'; ctx.fillRect(0,0,canvas.width,canvas.height);
  } else if (weatherSel.value === 'rain') {
    ctx.strokeStyle='rgba(150,190,255,0.12)'; ctx.lineWidth=1;
    for (let i=0;i<canvas.width;i+=40){ ctx.beginPath(); ctx.moveTo(i,0); ctx.lineTo(i-30,canvas.height); ctx.stroke(); }
  } else if (weatherSel.value === 'storm') {
    [[0.24,0.22,80],[0.72,0.30,110],[0.58,0.74,95]].forEach(([x,y,r])=>{
      const g=ctx.createRadialGradient(canvas.width*x,canvas.height*y,8,canvas.width*x,canvas.height*y,r);
      g.addColorStop(0,'rgba(255,91,114,0.18)'); g.addColorStop(1,'rgba(255,91,114,0)');
      ctx.fillStyle=g; ctx.beginPath(); ctx.arc(canvas.width*x,canvas.height*y,r,0,Math.PI*2); ctx.fill();
    });
  }
  // jamming rings near hazard zone
  if (parseFloat(jamming.value) > 0.12) {
    const hz = state.data.hazard_zone; const p = toScreen(hz.x, hz.y, canvas, view);
    ctx.save(); ctx.strokeStyle='rgba(255,0,110,0.18)'; ctx.setLineDash([4,6]);
    for (let r=28;r<90;r+=18){ ctx.beginPath(); ctx.arc(p.x,p.y,r,0,Math.PI*2); ctx.stroke(); }
    ctx.restore();
  }
  // wind arrows
  const windVal = parseFloat(wind.value);
  if (windVal > 0.08) {
    ctx.save(); ctx.strokeStyle='rgba(125,183,255,0.28)'; ctx.fillStyle='rgba(125,183,255,0.28)'; ctx.lineWidth=1.5;
    for (let x=120;x<canvas.width;x+=180){
      for (let y=90;y<canvas.height;y+=140){
        const len = 18 + windVal*20; const dx = len; const dy = -len*0.25;
        ctx.beginPath(); ctx.moveTo(x,y); ctx.lineTo(x+dx,y+dy); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(x+dx,y+dy); ctx.lineTo(x+dx-7,y+dy+3); ctx.lineTo(x+dx-5,y+dy+10); ctx.closePath(); ctx.fill();
      }
    }
    ctx.restore();
  }
}

function threatColor(level) {
  return ({ benign:'#54d38a', unknown:'#7db7ff', suspicious:'#ffbe4d', critical:'#ff5b72' })[level] || '#fff';
}

function typeGlyph(t) {
  return ({ aircraft:'✈', drone:'⬢', missile:'▲', satellite:'🛰', debris:'◇', asteroid:'☄', foreign_spaceship:'◆', unknown:'?' })[t] || '?';
}

const SENSOR_INFO = {
  radar_strength: 'Normalized radar return strength based on radar cross section and sensing conditions.',
  speed: 'Full 3D speed magnitude from the estimated velocity components.',
  horizontal_speed: 'Ground-plane speed, ignoring climb or descent.',
  velocity_vector: 'Estimated velocity components [vx, vy, vz].',
  acceleration: 'Estimated change in velocity per second from recent track updates.',
  heading_deg: 'Direction of travel in degrees clockwise from east on the tactical map.',
  climb_rate: 'Estimated vertical speed. Positive means climbing, negative means descending.',
  altitude: 'Estimated object altitude above the local ground reference.',
  thermal: 'Estimated heat signature level from thermal sensing.',
  radiation: 'Estimated radiation level above normal background.',
  size_est: 'Estimated physical size from sensor fusion.',
  shape_est: 'Best current shape/class silhouette estimate.',
  optical_confidence: 'Confidence from visual/optical sensing channels.',
  signal_confidence: 'Overall confidence that the current sensor packet is trustworthy.',
  dropout_count: 'Recent count of dropped or missing observations.',
  jam_estimate: 'Estimated level of jamming or interference affecting sensing.',
  rcs_est: 'Estimated radar cross section proxy.',
  acoustic: 'Estimated acoustic loudness proxy.',
  plume_index: 'Estimated strength of propulsion or exhaust plume.',
  magnetic: 'Estimated magnetic anomaly level.',
  spectral_class: 'Best current spectral/material category guess.',
  transponder: 'Whether the object appears to be broadcasting an identifying transponder.',
  impact_probability: 'Estimated probability that the projected path intersects or closely approaches the protected zone.',
  kinetic_energy_proxy: 'Rough consequence proxy based on estimated size and speed. It is not a real weapon-yield calculation.',
  predicted_zone_intersection: "Whether Orion's short-horizon projected path crosses the protected area.",
  seeker_emissions: 'Synthetic proxy for guidance or seeker-like emissions. Used only as a simulation signal.',
  ionization: 'Synthetic proxy for ionized trail or high-energy atmospheric interaction.',
  infrared_band: 'Qualitative infrared band or thermal category inferred by the optical/IR sensor model.',
  doppler_quality: 'How trustworthy the Doppler/radar velocity measurement is under current sensing conditions.',
  material_reflectivity: 'Synthetic proxy for surface reflectivity from optical/radar-style observation.',
  profile_label: 'Public or local profile family attached to the object at creation time.',
  country_or_family: 'Broad country, operator, or object family label when available from the public-informed profile.',
  distance_to_zone: 'Current distance from the object to the protected zone center.',
  closing_speed: 'Speed component taking the object toward the protected zone.'
};


const SUMMARY_INFO = {
  risk_posture: 'Overall threat status after combining rule-based scoring, confidence, environment, and model evidence.',
  behavior_pattern: "High-level interpretation of the object's movement pattern, such as direct approach, swarm-like behavior, or normal transit.",
  confidence_band: 'How trustworthy the current classification is based on sensing quality, tracking consistency, and model agreement.',
  signature_match: 'Best current match against public-source-informed object signature profiles.',
  provenance: 'Where the track evidence primarily comes from, such as simulation, public enrichment, or a fused view.',
  public_prior_use: 'Whether the classifier matched the track against a public signature profile or fell back to local priors.',
  threat_score: 'Combined threat score used to assign benign, unknown, suspicious, or critical.',
  cpa: 'Closest point of approach: the minimum projected distance to the protected zone along the short-horizon prediction.',
  ttz: 'Time to zone: estimated time before the object reaches the protected area boundary.',
  match_confidence: 'Strength of the best available public-signature match for this object.',
  evidence_link: 'Source page for the strongest public profile evidence, when available.'
};

function infoChip(label, value, key) {
  const val = (key === 'risk_posture' && ['benign','unknown','suspicious','critical'].includes(String(value))) ? `<span class=\"badge ${value}\">${value}</span>` : value;
  return `<div class=\"class-chip\"><span class=\"k\">${tip(label, SUMMARY_INFO[key] || label)}</span><span class=\"v\">${val}</span></div>`;
}

function formatValue(v) {
  return Array.isArray(v) ? '[' + v.join(', ') + ']' : v;
}

function hashId(id) {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = ((h << 5) - h + id.charCodeAt(i)) | 0;
  return Math.abs(h);
}



const spriteCache = {};

function spriteAssetForTrack(tr) {
  const profile = String(tr.sensor?.profile_label || tr.label || '').toLowerCase();
  const key = String(tr.catalog?.signature_match?.profile_key || tr.catalog?.signature_match?.label || '').toLowerCase();
  if (tr.class_type === 'aircraft') {
    if (profile.includes('f-16') || profile.includes('fighter')) return 'fighter.svg';
    if (profile.includes('c-130') || profile.includes('transport')) return 'transport.svg';
    return 'airliner.svg';
  }
  if (tr.class_type === 'drone') return 'drone.svg';
  if (tr.class_type === 'missile') {
    if (profile.includes('tomahawk') || profile.includes('cruise')) return 'cruise_missile.svg';
    if (profile.includes('hyper') || profile.includes('glide')) return 'hypersonic.svg';
    return 'ballistic_missile.svg';
  }
  if (tr.class_type === 'satellite') return 'satellite.svg';
  if (tr.class_type === 'debris') return 'debris.svg';
  if (tr.class_type === 'asteroid') return 'asteroid.svg';
  if (tr.class_type === 'foreign_spaceship') return 'spaceship.svg';
  return 'unknown.svg';
}

function spriteUrlForTrack(tr) {
  return `/static/assets/${spriteAssetForTrack(tr)}`;
}

function getSpriteForTrack(tr) {
  const url = spriteUrlForTrack(tr);
  if (!spriteCache[url]) {
    const img = new Image();
    img.src = url;
    spriteCache[url] = img;
  }
  return spriteCache[url];
}

function tip(label, text) {
  const safe = String(text).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  return `${label} <span class="info-tip" data-tip="${safe}" tabindex="0" aria-label="${safe}">?</span>`;
}


function normalizeTooltips() {
  document.querySelectorAll('.info-tip').forEach(el => {
    const text = el.getAttribute('data-tip') || el.getAttribute('title') || el.getAttribute('aria-label') || '';
    if (!text) return;
    el.setAttribute('data-tip', text);
    el.setAttribute('aria-label', text);
    if (el.hasAttribute('title')) el.removeAttribute('title');
  });
}

function hideGlobalTooltip() {
  const tip = document.getElementById('globalTooltip');
  if (!tip) return;
  tip.classList.add('hidden');
  tip.textContent = '';
}

function showGlobalTooltip(el) {
  const tip = document.getElementById('globalTooltip');
  if (!tip) return;
  const text = el.getAttribute('data-tip') || el.getAttribute('aria-label') || '';
  if (!text) return;
  tip.textContent = text;
  tip.classList.remove('hidden');
  const vw = window.innerWidth || document.documentElement.clientWidth;
  const vh = window.innerHeight || document.documentElement.clientHeight;
  const rect = el.getBoundingClientRect();
  tip.style.maxWidth = `${Math.min(420, Math.max(260, vw * 0.38))}px`;
  tip.style.left = '0px';
  tip.style.top = '0px';
  const tRect = tip.getBoundingClientRect();
  let left = rect.left + rect.width / 2 - tRect.width / 2;
  let top = rect.top - tRect.height - 14;
  if (left < 12) left = 12;
  if (left + tRect.width > vw - 12) left = Math.max(12, vw - tRect.width - 12);
  if (top < 12) top = rect.bottom + 14;
  if (top + tRect.height > vh - 12) top = Math.max(12, rect.top - tRect.height - 14);
  tip.style.left = `${left}px`;
  tip.style.top = `${top}px`;
}

function wireGlobalTooltips() {
  // Tooltips are handled by delegated document events so dynamically rendered tabs work reliably.
}

document.addEventListener('mouseover', (e) => {
  const el = e.target.closest?.('.info-tip');
  if (el) showGlobalTooltip(el);
});
document.addEventListener('mousemove', (e) => {
  const active = document.querySelector('.info-tip:hover, .info-tip:focus-visible');
  if (active) showGlobalTooltip(active);
});
document.addEventListener('mouseout', (e) => {
  const el = e.target.closest?.('.info-tip');
  if (el) hideGlobalTooltip();
});
document.addEventListener('focusin', (e) => {
  const el = e.target.closest?.('.info-tip');
  if (el) showGlobalTooltip(el);
});
document.addEventListener('focusout', (e) => {
  const el = e.target.closest?.('.info-tip');
  if (el) hideGlobalTooltip();
});

function positionTooltips() {
  normalizeTooltips();
  wireGlobalTooltips();
}

function syncPlayButton() {
  $('#playBtn').classList.toggle('active', state.playing);
  $('#playBtn').textContent = state.playing ? 'Pause' : 'Play';
}

function syncModeButtons() {
  $('#guidedToggle').classList.toggle('active', state.guided);
  $('#analystToggle').classList.toggle('active', !state.guided);
}

function setViewButtons() {
  $('#view2d').classList.toggle('active', !state.view3d);
  $('#view3d').classList.toggle('active', state.view3d);
  $('#mapWrap').classList.toggle('active', !state.view3d);
  $('#globeWrap').classList.toggle('active', state.view3d);
}

function syncModeUI() {
  if (state.guided && state.currentTab !== 'summary') {
    state.currentTab = 'summary';
    document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
    document.querySelector('.tab[data-tab="summary"]').classList.add('active');
  }
}

function renderSideViews() {
  document.body.classList.toggle('left-collapsed', !!state.leftCollapsed);
  document.body.classList.toggle('right-collapsed', !!state.rightCollapsed);
  document.getElementById('toggleLeftPanel') && (document.getElementById('toggleLeftPanel').textContent = state.leftCollapsed ? 'Show setup' : 'Hide setup');
  document.getElementById('toggleRightPanel') && (document.getElementById('toggleRightPanel').textContent = state.rightCollapsed ? 'Show analysis' : 'Hide analysis');
  document.querySelectorAll('[data-left-view]').forEach(btn => btn.classList.toggle('active', btn.dataset.leftView === state.leftView));
  document.querySelectorAll('[data-right-view], [data-right-jump]').forEach(btn => btn.classList.toggle('active', btn.dataset.rightView === state.rightView || btn.dataset.rightJump === state.rightView));
  $('#leftOps').classList.toggle('hidden', state.leftView !== 'ops');
  $('#leftEnv').classList.toggle('hidden', state.leftView !== 'env');
  $('#rightInspect').classList.toggle('hidden', state.rightView !== 'inspect');
  $('#rightLegend').classList.toggle('hidden', state.rightView !== 'legend');
  $('#rightEvents').classList.toggle('hidden', state.rightView !== 'events');
  $('#rightDeepdive').classList.toggle('hidden', state.rightView !== 'deepdive');
  $('#rightResponse').classList.toggle('hidden', state.rightView !== 'response');
  $('#rightAssistant').classList.toggle('hidden', state.rightView !== 'assistant');
}

function clearTourFocus() {
  document.querySelectorAll('.tour-focus').forEach(el => el.classList.remove('tour-focus'));
}

function applyTourFocus(selector) {
  clearTourFocus();
  const el = document.querySelector(selector);
  if (el) el.classList.add('tour-focus');
}

const tourSteps = [
  {
    title: 'This is the monitored region',
    body: 'The center view is the active monitored region. Orion tracks objects here and compares them against protected, restricted, and hazardous zones.',
    focus: '[data-tour-id="mapPanel"]',
    enter() {
      state.view3d = false;
      setViewButtons();
      state.currentTab = 'summary';
      state.rightView = 'inspect';
    }
  },
  {
    title: 'Colors communicate urgency',
    body: 'Blue marks the protected area. Amber marks restricted airspace. Red marks hazardous conditions. Object colors reflect Orion’s estimated threat level.',
    focus: '[data-tour-id="legendPanel"]',
    enter() { state.rightView = 'legend'; }
  },
  {
    title: 'Each object is a track',
    body: 'Every object shown here is an active track with estimated motion, sensor readings, and a classification. Orion can represent aircraft, drones, missiles, satellites, debris, asteroid-like objects, and unknown tracks.',
    focus: '[data-tour-id="objectPanel"]',
    enter() {
      state.rightView = 'inspect';
      const tr = pickDemoTrack();
      if (tr) state.selectedId = tr.id;
      state.currentTab = 'summary';
    }
  },
  {
    title: 'Why Orion flags an object',
    body: 'Orion combines motion behavior, sensor evidence, environmental conditions, machine learning signals, and public-data-informed signatures to estimate both risk and confidence.',
    focus: '[data-tour-id="objectPanel"]',
    enter() { state.rightView = 'inspect'; state.currentTab = 'summary'; }
  },
  {
    title: 'Scenarios change the problem',
    body: 'Different scenarios change the object mix, environment, and behavior patterns. That lets the same detection pipeline be tested under very different conditions.',
    focus: '[data-tour-id="scenarioPanel"]',
    enter() { state.leftView = 'ops'; }
  },
  {
    title: '2D for analysis, 3D for spatial context',
    body: 'The 2D view is best for overview and inspection. The 3D view helps show altitude, spacing, and relative position more clearly.',
    focus: '[data-tour-id="modeBar"]'
  },
  {
    title: 'Testing mode lets you inject new objects',
    body: 'You can add your own objects into the scene and observe how Orion’s sensors, scoring, ML, and visualization respond.',
    focus: '[data-tour-id="testingPanel"]',
    enter() { state.leftView = 'ops'; }
  },
  {
    title: 'The timeline shows how the situation evolves',
    body: 'Orion records important changes over time, such as scenario loads, anomaly spikes, zone entries, and threat escalations.',
    focus: '[data-right-view="events"]',
    enter() { state.rightView = 'events'; }
  },
  {
    title: 'You’re ready to explore',
    body: 'You can now switch scenarios, inspect objects, compare views, and test how Orion reacts under different conditions.',
    focus: '[data-tour-id="playbackBar"]'
  }
];

function renderTour() {
  const card = $('#tourCard');
  const scrim = $('#tourScrim');
  if (!state.demoActive) {
    card.classList.add('hidden');
    scrim.classList.add('hidden');
    document.body.classList.remove('demo-lock');
    clearTourFocus();
    return;
  }
  document.body.classList.add('demo-lock');
  card.classList.remove('hidden');
  scrim.classList.remove('hidden');
  const step = tourSteps[state.demoStep];
  $('#tourStepLabel').textContent = `Step ${state.demoStep + 1} of ${tourSteps.length}`;
  $('#tourTitle').textContent = step.title;
  $('#tourBody').textContent = step.body;
  $('#tourNext').textContent = state.demoStep === tourSteps.length - 1 ? 'Start live simulation' : 'Next';
  applyTourFocus(step.focus);
}

async function getState() {
  const r = await fetch('/api/state');
  state.data = await r.json();
  if (!state.selectedId && state.data.tracks?.length) state.selectedId = state.data.tracks[0].id;
  if (!state._initialPresetApplied) { applyScenarioPreset(state.data.settings?.scenario || scenarioSel.value); state._initialPresetApplied = true; }
  renderAll();
}

async function step(dt = 1.0) {
  const r = await fetch('/api/step', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dt })
  });
  state.data = await r.json();
  if (!state.selectedId && state.data.tracks?.length) state.selectedId = state.data.tracks[0].id;
  renderAll();
}

async function applySettings(reset = false) {
  const payload = {
    scenario: scenarioSel.value,
    weather: weatherSel.value,
    wind: parseFloat(wind.value),
    visibility: parseFloat(visibility.value),
    jamming: parseFloat(jamming.value),
    hazard_intensity: parseFloat(hazardIntensity.value),
    live_data: true,
    guided_mode: state.guided,
    three_d: state.view3d,
  };
  const r = await fetch(reset ? '/api/reset' : '/api/settings', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  });
  state.data = await r.json();
  if (!state.selectedId && state.data.tracks?.length) state.selectedId = state.data.tracks[0].id;
  renderAll();
}

async function resetScenario() {
  state.playing = false;
  state.mapZoom = 1;
  state.mapPanX = 0;
  state.mapPanY = 0;
  state.globeNeedsFrame = true;
  syncPlayButton();
  await applySettings(true);
}

async function addObject(kind) {
  state.playing = false;
  syncPlayButton();
  const r = await fetch('/api/add_object', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ kind })
  });
  state.data = await r.json();
  const newest = state.data.tracks[state.data.tracks.length - 1];
  if (newest) state.selectedId = newest.id;
  renderAll();
}

async function removeSelectedObject() {
  const tr = selectedTrack();
  if (!tr) return;
  state.playing = false;
  syncPlayButton();
  const r = await fetch('/api/remove_object', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ track_id: tr.id })
  });
  state.data = await r.json();
  state.selectedId = state.data.tracks?.[0]?.id || null;
  renderAll();
}

async function startGuidedDemo() {
  state.playing = false;
  state.mapZoom = 1;
  state.mapPanX = 0;
  state.mapPanY = 0;
  state.guided = true;
  state.demoActive = true;
  state.demoStep = 0;
  state.globeNeedsFrame = true;
  syncModeButtons();
  syncPlayButton();
  tourSteps[0].enter?.();
  renderAll();
  renderTour();
  try {
    await applySettings(true);
  } catch (e) {
    console.error('Guided demo reset failed', e);
  }
  const tr = pickDemoTrack();
  if (tr) state.selectedId = tr.id;
  tourSteps[0].enter?.();
  renderAll();
  renderTour();
  positionTooltips();
}


function endGuidedDemo(startPlaying = true) {
  state.demoActive = false;
  if (startPlaying) state.playing = true;
  syncPlayButton();
  renderTour();
  positionTooltips();
}


function nextTourStep() {
  if (!state.demoActive) return;
  if (state.demoStep < tourSteps.length - 1) {
    state.demoStep += 1;
    tourSteps[state.demoStep].enter?.();
    renderAll();
    renderTour();
  } else {
    endGuidedDemo(true);
  }
}

function syncControls() {
  const s = state.data.settings;
  scenarioSel.innerHTML = Object.entries(state.data.scenarios).map(([k]) => `<option value="${k}" ${k===s.scenario?'selected':''}>${k.replaceAll('_',' ')}</option>`).join('');
  weatherSel.value = s.weather;
  wind.value = s.wind;
  visibility.value = s.visibility;
  jamming.value = s.jamming;
  hazardIntensity.value = s.hazard_intensity;
  speedSelect.value = String(state.speed);
  if (regionSelect) regionSelect.innerHTML = Object.keys(REGIONS).map(name => `<option value="${name}" ${name===state.region?'selected':''}>${name}</option>`).join('');
  cameraPresetSelect.value = state.cameraPreset;

  const tracks = [...state.data.tracks].sort((a,b) => severityRank(b.threat_level)-severityRank(a.threat_level) || a.id.localeCompare(b.id));
  if (!tracks.find(tr => tr.id === state.selectedId)) state.selectedId = tracks[0]?.id || null;
  objectSelect.innerHTML = tracks.map(tr => `<option value="${tr.id}" ${tr.id===state.selectedId?'selected':''}>${trackDisplayName(tr, true)} · ${tr.threat_level}</option>`).join('');
  if (renameObjectInput) { const st = selectedTrack(); if (st && document.activeElement !== renameObjectInput) renameObjectInput.value = st.label || ''; }
  const descEl = $('#scenarioDescription');
  if (descEl) descEl.textContent = state.data.scenarios[s.scenario] || '';
}


function setStats() {
  const sum = state.data.summary;
  $('#summaryMessage').textContent = state.loadingScenario ? `Loading ${scenarioSel.value.replaceAll('_',' ')}…` : sum.message;
  $('#statTotal').textContent = sum.total;
  $('#statBenign').textContent = sum.benign;
  $('#statUnknown').textContent = sum.unknown;
  $('#statSuspicious').textContent = sum.suspicious;
  $('#statCritical').textContent = sum.critical;
  $('#statPenalty').textContent = sum.sensor_penalty;
}


function renderScenarioReadout() {
  const box = document.querySelector('#scenarioReadout');
  if (!box || !state.data) return;
  const desc = state.data.scenarios[state.data.settings.scenario] || '';
  box.innerHTML = `<div class="scenario-title">Scenario</div><div class="scenario-body">${desc}</div>`;
}

function renderSourceStrip() {
  const links = state.data?.live_catalog?.links || {};
  const pills = [
    ['OpenSky', links.opensky],
    ['CelesTrak', links.celestrak],
    ['NASA/JPL CAD', links.jpl_cad],
  ].map(([label, url]) => `<span class="source-pill">${label}${url ? ` · <a href="${url}" target="_blank" rel="noreferrer">source</a>` : ''}</span>`);
  $('#sourceStrip').innerHTML = pills.join('');
}

function computeView(canvas) {
  const pts = [];
  const add = (x, y) => pts.push([x, y]);
  const addZone = (z) => { add(z.x-z.radius, z.y-z.radius); add(z.x+z.radius, z.y+z.radius); };
  addZone(state.data.zone); addZone(state.data.hazard_zone); addZone(state.data.no_fly_zone);
  state.data.tracks.forEach(tr => {
    add(tr.x, tr.y);
    tr.history?.forEach(h => add(h[0], h[1]));
    tr.predicted_path?.forEach(p => add(p[0], p[1]));
  });
  let minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity;
  pts.forEach(([x,y])=>{ minX=Math.min(minX,x); maxX=Math.max(maxX,x); minY=Math.min(minY,y); maxY=Math.max(maxY,y); });
  const pad = 52;
  const width = Math.max(1, maxX-minX); const height = Math.max(1, maxY-minY);
  const baseScale = Math.min((canvas.width-pad*2)/width, (canvas.height-pad*2)/height);
  const scale = baseScale * (state.mapZoom || 1);
  return { scale, centerX:(minX+maxX)/2 - (state.mapPanX || 0) / scale, centerY:(minY+maxY)/2 + (state.mapPanY || 0) / scale };
}

function toScreen(x, y, canvas, view) {
  return {
    x: canvas.width / 2 + (x - view.centerX) * view.scale,
    y: canvas.height / 2 - (y - view.centerY) * view.scale
  };
}


function drawObjectIcon(ctx, tr, p) {
  const color = threatColor(tr.threat_level);
  const size = ({ aircraft: 20, drone: 16, missile: 18, satellite: 18, debris: 16, asteroid: 22, foreign_spaceship: 22, unknown: 18 })[tr.class_type] || 18;
  const vel = tr.sensor?.velocity_vector || [1, 0, 0];
  const heading = Math.atan2(vel[1] || 0, vel[0] || 1);
  const alt = tr.sensor?.altitude ?? tr.z ?? 0;
  const lift = Math.max(3, Math.min(18, alt / 1800));
  const sig = tr.catalog?.signature_match?.confidence || 0;
  const glow = 10 + sig * 14;
  const idHash = hashId(tr.id);
  const spread = Math.min(11, alt / 4200);
  const spreadAngle = (idHash % 360) * Math.PI / 180;
  const px = p.x + Math.cos(spreadAngle) * spread * 0.55;
  const py = p.y + Math.sin(spreadAngle) * spread * 0.55;

  ctx.save();
  ctx.translate(px, py);
  ctx.strokeStyle = 'rgba(255,255,255,0.14)';
  ctx.lineWidth = 1.2;
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(0, lift + 1);
  ctx.stroke();
  ctx.fillStyle = 'rgba(0,0,0,0.18)';
  ctx.beginPath();
  ctx.ellipse(0, lift + 5, size * 0.9, Math.max(4, size * 0.35), 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.rotate(heading + Math.PI / 2);
  const sprite = getSpriteForTrack(tr);
  ctx.shadowColor = color;
  ctx.shadowBlur = glow;
  if (sprite && sprite.complete) {
    const drawW = size * 2.7;
    const drawH = size * 2.7;
    ctx.drawImage(sprite, -drawW / 2, -drawH / 2, drawW, drawH);
  } else {
    ctx.fillStyle = 'rgba(255,255,255,0.10)';
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.2;
    ctx.beginPath();
    ctx.arc(0, 0, size * 0.7, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  }
  if (state.selectedId === tr.id) {
    ctx.shadowBlur = 0;
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2.0;
    ctx.beginPath();
    ctx.arc(0, 0, size * 1.5, 0, Math.PI * 2);
    ctx.stroke();
  }
  ctx.restore();
}

function renderSourceStrip() {
  const links = state.data?.live_catalog?.links || {};
  const pills = [
    ['OpenSky', links.opensky],
    ['CelesTrak', links.celestrak],
    ['NASA/JPL CAD', links.jpl_cad],
  ].map(([label, url]) => `<span class="source-pill">${label}${url ? ` · <a href="${url}" target="_blank" rel="noreferrer">source</a>` : ''}</span>`);
  $('#sourceStrip').innerHTML = pills.join('');
}

function computeView(canvas) {
  const pts = [];
  const add = (x, y) => pts.push([x, y]);
  const addZone = (z) => { add(z.x-z.radius, z.y-z.radius); add(z.x+z.radius, z.y+z.radius); };
  addZone(state.data.zone); addZone(state.data.hazard_zone); addZone(state.data.no_fly_zone);
  state.data.tracks.forEach(tr => {
    add(tr.x, tr.y);
    tr.history?.forEach(h => add(h[0], h[1]));
    tr.predicted_path?.forEach(p => add(p[0], p[1]));
  });
  let minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity;
  pts.forEach(([x,y])=>{ minX=Math.min(minX,x); maxX=Math.max(maxX,x); minY=Math.min(minY,y); maxY=Math.max(maxY,y); });
  const pad = 52;
  const width = Math.max(1, maxX-minX); const height = Math.max(1, maxY-minY);
  const baseScale = Math.min((canvas.width-pad*2)/width, (canvas.height-pad*2)/height);
  const scale = baseScale * (state.mapZoom || 1);
  return { scale, centerX:(minX+maxX)/2 - (state.mapPanX || 0) / scale, centerY:(minY+maxY)/2 + (state.mapPanY || 0) / scale };
}

function toScreen(x, y, canvas, view) {
  return {
    x: canvas.width / 2 + (x - view.centerX) * view.scale,
    y: canvas.height / 2 - (y - view.centerY) * view.scale
  };
}

function draw2D() {
  const canvas = $('#mapCanvas');
  const ctx = canvas.getContext('2d');
  const view = computeView(canvas);
  ctx.clearRect(0,0,canvas.width,canvas.height);
  drawRegionBackdrop(ctx, canvas);
  const grd = ctx.createRadialGradient(canvas.width/2, canvas.height/2, 40, canvas.width/2, canvas.height/2, 420);
  grd.addColorStop(0,'rgba(34,160,255,0.05)'); grd.addColorStop(1,'rgba(0,0,0,0)'); ctx.fillStyle=grd; ctx.fillRect(0,0,canvas.width,canvas.height);

  ctx.strokeStyle='rgba(123,190,255,0.08)'; ctx.lineWidth=1;
  for(let i=0;i<canvas.width;i+=80){ ctx.beginPath(); ctx.moveTo(i,0); ctx.lineTo(i,canvas.height); ctx.stroke(); }
  for(let i=0;i<canvas.height;i+=80){ ctx.beginPath(); ctx.moveTo(0,i); ctx.lineTo(canvas.width,i); ctx.stroke(); }

  const drawZone = (obj, fill, stroke) => {
    const p = toScreen(obj.x, obj.y, canvas, view); const r = obj.radius * view.scale;
    ctx.beginPath(); ctx.arc(p.x,p.y,r,0,Math.PI*2); ctx.fillStyle=fill; ctx.fill(); ctx.strokeStyle=stroke; ctx.setLineDash([]); ctx.stroke();
  };
  drawEnvironmentOverlay(ctx, canvas, view);
  drawZone(state.data.hazard_zone, 'rgba(255,91,114,0.18)', 'rgba(255,91,114,0.85)');
  drawZone(state.data.no_fly_zone, 'rgba(255,190,77,0.16)', 'rgba(255,190,77,0.85)');
  drawZone(state.data.zone, 'rgba(125,183,255,0.16)', 'rgba(125,183,255,0.85)');

  state.data.tracks.forEach(tr => {
    const showLineForTrack = (!state.guided) || tr.id === state.selectedId;
    if(state.showTrails && showLineForTrack && tr.history?.length>1){
      ctx.beginPath(); tr.history.forEach((pt,i)=>{ const p=toScreen(pt[0],pt[1],canvas,view); i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y); });
      ctx.strokeStyle='rgba(255,255,255,0.18)'; ctx.setLineDash([]); ctx.stroke();
    }
    if(state.showPred && showLineForTrack && tr.predicted_path?.length){
      ctx.beginPath(); tr.predicted_path.forEach((pt,i)=>{ const p=toScreen(pt[0],pt[1],canvas,view); i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y); });
      ctx.strokeStyle=threatColor(tr.threat_level); ctx.setLineDash([6,6]); ctx.stroke();
    }
    const p = toScreen(tr.x, tr.y, canvas, view);
    if(state.showEllipses){
      ctx.beginPath(); ctx.ellipse(p.x,p.y, Math.max(8,tr.uncertainty*0.12), Math.max(6,tr.uncertainty*0.08), 0,0,Math.PI*2);
      ctx.strokeStyle='rgba(255,255,255,0.15)'; ctx.setLineDash([4,4]); ctx.stroke();
    }
    ctx.setLineDash([]);
    drawObjectIcon(ctx, tr, p);
    if (state.selectedId === tr.id){ ctx.beginPath(); ctx.arc(p.x,p.y,24,0,Math.PI*2); ctx.strokeStyle='rgba(255,255,255,0.9)'; ctx.lineWidth = 1.6; ctx.stroke(); }
    if(state.showLabels){ const text = tr.label ? `${tr.id} — ${tr.label}` : tr.id; ctx.font='12px sans-serif'; ctx.textAlign='center'; const tw = ctx.measureText(text).width; ctx.fillStyle='rgba(8,20,36,0.72)'; ctx.fillRect(p.x - tw/2 - 6, p.y - 32, tw + 12, 16); ctx.fillStyle='#eaf5ff'; ctx.fillText(text, p.x, p.y-20); }
    tr._screen = p;
  });
}

function renderTimeline() {
  $('#timeline').innerHTML = state.data.events.map(e => `<div class="event ${e.kind}"><div class="event-head"><span class="event-kind">${e.kind}</span><b>t=${e.time}s</b></div><div>${e.message}</div></div>`).join('') || '<div class="subtle">No major events yet.</div>';
}

function renderSelected() {
  const tr = selectedTrack();
  if(!tr){ $('#objectHeader').innerHTML=''; $('#tabContent').innerHTML=''; return; }
  state.selectedId = tr.id;
  $('#objectHeader').innerHTML = `<div><h3 class="object-title-line"><span>${tr.id}</span>${tr.label ? `<span class="object-call-sign">${tr.label}</span>` : ''} <span class="badge ${tr.threat_level}">${tr.threat_level}</span></h3><div class="subtle">${tr.class_type} · ${tr.origin_type} · ${tr.source_type}</div></div>`;
  let html = '';
  if(state.currentTab==='summary'){
    const behavior = tr.swarm_likelihood > 0.45 ? 'Coordinated / swarm-like' : tr.directness > 0.75 ? 'Direct approach' : tr.no_fly_intrusion ? 'Restricted-zone violator' : 'Nominal / low-complexity';
    const confidenceBand = tr.sub_scores?.confidence > 0.7 ? 'High confidence' : tr.sub_scores?.confidence > 0.45 ? 'Moderate confidence' : 'Low confidence';
    const provenance = tr.source_type === 'simulated' ? 'Simulated track with public priors' : `Public-source aware (${tr.source_type})`;
    const sig = tr.catalog?.signature_match || {};
    html += `<div class="class-grid">
      ${infoChip('Risk posture', tr.threat_level, 'risk_posture')}
      ${infoChip('Behavior pattern', behavior, 'behavior_pattern')}
      ${infoChip('Confidence band', confidenceBand, 'confidence_band')}
      ${infoChip('Signature match', sig.label || 'No strong match yet', 'signature_match')}
      ${infoChip('Provenance', provenance, 'provenance')}
      ${infoChip('Public prior use', sig.source_evidence || 'Fallback priors', 'public_prior_use')}
    </div>`;
    html += `<div class="summary-story"><div class="summary-story-title">Why Orion flagged this object</div><p>Orion flagged this object because its motion, sensor evidence, and contextual signals differ from normal activity in the current scenario.</p></div>`;
    html += `<p>${tr.summary}</p>`;
    html += `<div class="quick-actions">${tr.explanation.map(x=>`<span class="badge ${tr.threat_level}">${x}</span>`).join('')}</div>`;
    html += `<table>
      <tr><td>${tip('Threat score', SUMMARY_INFO.threat_score)}</td><td>${tr.threat_score}</td></tr>
      <tr><td>${tip('Closest approach', SUMMARY_INFO.cpa)}</td><td>${tr.cpa}</td></tr>
      <tr><td>${tip('Time to zone', SUMMARY_INFO.ttz)}</td><td>${tr.ttz ?? 'n/a'} s</td></tr>
      <tr><td>${tip('Profile match confidence', SUMMARY_INFO.match_confidence)}</td><td>${tr.catalog?.signature_match?.confidence ?? 'n/a'}</td></tr>
      <tr><td>${tip('Evidence link', SUMMARY_INFO.evidence_link)}</td><td>${tr.catalog?.signature_match?.source_url ? `<a href="${tr.catalog.signature_match.source_url}" target="_blank" rel="noreferrer">open source page</a>` : '—'}</td></tr>
    </table>`;
    if(state.guided) html += `<p class="subtle">Switch to Analyst mode for the full sensor stack, sub-scores, and model details.</p>`;
  }
  if(state.currentTab==='sensors'){
    html += `<p class="tab-intro">Raw and derived sensor-style readings used to analyze this object.</p>`;
    const preferred = state.sensorMode === 'simple'
      ? ['radar_strength','speed','acceleration','distance_to_zone','closing_speed','impact_probability','thermal','radiation','plume_index','size_est','shape_est','signal_confidence','profile_label','transponder']
      : ['radar_strength','speed','horizontal_speed','velocity_vector','acceleration','heading_deg','climb_rate','altitude','distance_to_zone','closing_speed','thermal','radiation','size_est','shape_est','optical_confidence','signal_confidence','dropout_count','jam_estimate','rcs_est','acoustic','plume_index','magnetic','spectral_class','infrared_band','seeker_emissions','ionization','doppler_quality','material_reflectivity','impact_probability','kinetic_energy_proxy','predicted_zone_intersection','profile_label','country_or_family','transponder'];
    html += `<table>${preferred.filter(k=>tr.sensor[k]!==undefined).map(k=>`<tr><td>${tip(k, SENSOR_INFO[k] || k)}</td><td>${Array.isArray(tr.sensor[k]) ? '[' + tr.sensor[k].join(', ') + ']' : tr.sensor[k]}</td></tr>`).join('')}</table>`;
  }
  if(state.currentTab==='analysis'){
    html += `<p class="tab-intro">Threat logic, ML signals, clustering, and model-supported interpretation.</p>`;
    const ml = tr.catalog?.ml_assessment || {};
    html += `<table>
      <tr><td>${tip('Intent','Rule-based estimate of hostile intent based on approach geometry and behavior.')}</td><td>${tr.sub_scores.intent}</td></tr>
      <tr><td>${tip('Capability','Rule-based estimate of how dangerous the object could be if hostile.')}</td><td>${tr.sub_scores.capability}</td></tr>
      <tr><td>${tip('Confidence','Confidence in the current assessment given sensor quality and track consistency.')}</td><td>${tr.sub_scores.confidence}</td></tr>
      <tr><td>${tip('Environmental risk','Extra risk caused by weather, hazards, or degraded sensing.')}</td><td>${tr.sub_scores.environment}</td></tr>
      <tr><td>${tip('Anomaly score','Isolation Forest anomaly score. Higher means more behavior unlike normal training examples.')}</td><td>${tr.anomaly_score.toFixed(3)}</td></tr>
      <tr><td>${tip('ML predicted label','Random Forest prediction from the current sensor and motion features.')}</td><td>${ml.predicted_label || 'n/a'}</td></tr>
      <tr><td>${tip('Cluster ID','KMeans behavior cluster assignment for this track.')}</td><td>${ml.cluster_id ?? 'n/a'}</td></tr>
      <tr><td>${tip('Directness','How directly the object is moving toward the protected zone.')}</td><td>${tr.directness}</td></tr>
      <tr><td>${tip('Swarm likelihood','How strongly this object appears to be coordinated with nearby tracks.')}</td><td>${tr.swarm_likelihood}</td></tr>
      <tr><td>${tip('No-fly intrusion','Whether the track is currently inside the restricted zone.')}</td><td>${tr.no_fly_intrusion}</td></tr>
      <tr><td>${tip('Hazard nearby','Whether the track is currently inside or near the hazard zone.')}</td><td>${tr.hazard_nearby}</td></tr>
    </table>`;
    if (ml.probabilities) {
      html += `<h4>ML label probabilities</h4><table>${Object.entries(ml.probabilities).map(([k,v]) => `<tr><td>${k}</td><td>${v}</td></tr>`).join('')}</table>`;
    }
    if (ml.top_features?.length) {
      html += `<h4>Most influential model features</h4><table>${ml.top_features.map(([k,v]) => `<tr><td>${k}</td><td>${v.toFixed ? v.toFixed(3) : v}</td></tr>`).join('')}</table>`;
    }
  }
  if(state.currentTab==='catalog'){
    html += `<p class="tab-intro">Reference-profile evidence and supporting source matches.</p>`;
    const live = state.data.live_catalog || {};
    const sig = tr.catalog?.signature_match || {};
    html += `<table>
      <tr><td>Source type</td><td>${tr.source_type}</td></tr>
      <tr><td>Origin</td><td>${tr.origin_type}</td></tr>
      <tr><td>Label</td><td>${tr.label || '—'}</td></tr>
      <tr><td>OpenSky rows</td><td>${live.opensky?.length || 0}</td></tr>
      <tr><td>ISS hint</td><td>${live.iss?.name || 'not loaded'}</td></tr>
      <tr><td>NEO hint</td><td>${live.neo?.des || live.neo?.desig || 'not loaded'}</td></tr>
      <tr><td>Public signature evidence</td><td>${sig.source_evidence || 'fallback priors'}</td></tr>
      <tr><td>Profile source</td><td>${sig.source_url ? `<a href="${sig.source_url}" target="_blank" rel="noreferrer">open source page</a>` : 'local/fallback'}</td></tr>
      <tr><td>Top candidates</td><td>${(sig.candidates || []).map(c => typeof c === 'string' ? c : `${c.label ?? 'candidate'} · ${c.country_or_family ?? c.family ?? 'n/a'} (${c.confidence ?? 'n/a'})`).join(', ') || 'n/a'}</td></tr>
    </table>`;
    if ((sig.feature_alignment || []).length) {
      html += `<h4>Matched sensor values</h4><table class="match-table">
        ${(sig.feature_alignment || []).map(row => `<tr><td>${row.name}</td><td>${row.observed}</td><td>${row.profile}</td><td>${Math.round(row.match * 100)}%</td></tr>`).join('')}
      </table>`;
    }

  }
  if(state.currentTab==='model'){
    html += `<p class="tab-intro">The main logic and model layers currently contributing to this classification.</p>`;
    const ml = tr.catalog?.ml_assessment || {};
    html += `<table>
      <tr><td>Physics model</td><td>${tr.physics_model}</td></tr>
      <tr><td>Tracking model</td><td>${tr.tracking_model}</td></tr>
      <tr><td>Prediction model</td><td>${tr.prediction_model}</td></tr>
      <tr><td>AI model</td><td>${tr.ai_model}</td></tr>
      <tr><td>Additional ML</td><td>${(ml.models || ['RandomForest','KMeans']).join(', ')}</td></tr>
      <tr><td>Public-signature matcher</td><td>Profile matching against public-source-informed priors</td></tr>
    </table>`;
  }
  $('#tabContent').innerHTML = html;
  normalizeTooltips();
  positionTooltips();
}


function objectHeightMeters(tr) {
  return {
    aircraft: Math.max(900, tr.z * 0.22),
    drone: Math.max(180, tr.z * 0.18),
    missile: Math.max(2800, tr.z * 0.24),
    satellite: 42000,
    debris: 46000,
    asteroid: 62000,
    unknown: Math.max(1600, tr.z * 0.22)
  }[tr.class_type] ?? Math.max(3000, tr.z * 0.3);
}

function worldToGeo(x, y, z = 0, tr = null, options = {}) {
  if (tr) {
    const fromBackend = (typeof tr.sensor?.global_lat === 'number' && typeof tr.sensor?.global_lon === 'number')
      ? { lat: tr.sensor.global_lat, lon: tr.sensor.global_lon, area: tr.sensor.global_area || 'global track sector' }
      : null;
    const base = fromBackend || scenarioGeoForTrack(tr);
    // Keep the assigned global sector stable, but allow tiny motion so predictions/trails show direction.
    const localScale = options.prediction ? 140000 : 220000;
    const lat = base.lat + (y / localScale);
    const lon = base.lon + (x / (localScale * Math.max(0.25, Math.cos(base.lat * Math.PI / 180))));
    const h = objectHeightMeters(tr);
    return { lat, lon, h, area: base.area || 'global track sector' };
  }
  const base = REGIONS[state.region] || REGIONS['Southern California'];
  const lat = base.lat + (y / 18000);
  const lon = base.lon + (x / (18000 * Math.cos(base.lat * Math.PI / 180)));
  return { lat, lon, h: Math.max(0, z * 0.2), area: state.region };
}

function ensureViewer() {
  if (state.viewer) return state.viewer;
  if (!window.Cesium) return null;
  try {
    const viewer = new Cesium.Viewer('globe', {
      animation:false, timeline:false, baseLayerPicker:false, geocoder:false, sceneModePicker:false,
      homeButton:false, fullscreenButton:false, infoBox:false, selectionIndicator:false, shouldAnimate:false,
      imageryProvider: false,
      terrainProvider: new Cesium.EllipsoidTerrainProvider()
    });
    const imagery = new Cesium.OpenStreetMapImageryProvider({
      url: 'https://tile.openstreetmap.org/'
    });
    viewer.imageryLayers.removeAll();
    viewer.imageryLayers.addImageryProvider(imagery);
    viewer.scene.globe.baseColor = Cesium.Color.fromCssColorString('#13243d');
    viewer.scene.globe.show = true;
    viewer.scene.globe.enableLighting = false;
    viewer.scene.globe.depthTestAgainstTerrain = true;
    viewer.scene.skyAtmosphere.show = false;
    viewer.scene.globe.showGroundAtmosphere = false;
    viewer.scene.backgroundColor = Cesium.Color.BLACK;
    viewer.scene.screenSpaceCameraController.minimumZoomDistance = 80;
    viewer.scene.screenSpaceCameraController.maximumZoomDistance = 30000000;
    viewer.scene.screenSpaceCameraController.enableCollisionDetection = false;
    viewer.scene.screenSpaceCameraController.lookEventTypes = [Cesium.CameraEventType.RIGHT_DRAG];
    viewer.scene.screenSpaceCameraController.rotateEventTypes = [Cesium.CameraEventType.LEFT_DRAG];
    viewer.scene.screenSpaceCameraController.tiltEventTypes = [Cesium.CameraEventType.MIDDLE_DRAG, { eventType: Cesium.CameraEventType.LEFT_DRAG, modifier: Cesium.KeyboardEventModifier.CTRL }];
    viewer.scene.screenSpaceCameraController.zoomEventTypes = [Cesium.CameraEventType.WHEEL, Cesium.CameraEventType.PINCH];
    viewer.camera.percentageChanged = 0.01;
    viewer.camera.moveEnd.addEventListener(() => { state.globeNeedsFrame = false; });

    viewer.cesiumWidget.screenSpaceEventHandler.removeInputAction(Cesium.ScreenSpaceEventType.LEFT_DOUBLE_CLICK);
    const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
    const pickTrackAt = (pos) => {
      const picked = viewer.scene.pick(pos);
      return picked?.id?.properties?.trackId?.getValue?.() || picked?.id?.properties?.trackId || null;
    };
    handler.setInputAction((movement) => {
      const trackId = pickTrackAt(movement.position);
      if (trackId) {
        state.selectedId = trackId;
        renderAll();
      }
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
    handler.setInputAction((movement) => {
      const trackId = pickTrackAt(movement.position);
      if (trackId) {
        state.selectedId = trackId;
        renderAll();
        setTimeout(() => focusSelectedObject3D(false), 50);
      }
    }, Cesium.ScreenSpaceEventType.LEFT_DOUBLE_CLICK);
    viewer.scene.canvas.addEventListener('dblclick', (ev) => {
      const rect = viewer.scene.canvas.getBoundingClientRect();
      const trackId = pickTrackAt(new Cesium.Cartesian2(ev.clientX - rect.left, ev.clientY - rect.top));
      if (trackId) {
        ev.preventDefault();
        state.selectedId = trackId;
        renderAll();
        setTimeout(() => focusSelectedObject3D(false), 20);
      }
    });
    viewer.orionHandler = handler;
    state.viewer = viewer;
    // Start 3D mode with the whole globe centered. Without this explicit
    // nadir view, Cesium's default/pitched camera can place Earth low in
    // the viewport until the first reset finishes animating.
    try {
      const o = presetGlobalCamera();
      viewer.camera.setView({
        destination: Cesium.Cartesian3.fromDegrees(o.lon, o.lat, o.height),
        orientation: { heading: o.heading, pitch: o.pitch, roll: o.roll }
      });
    } catch (_) {}
    return viewer;
  } catch (e) {
    return null;
  }
}


function entityVisibleFromCamera(position, maxBacksideAllowance = 0.02) {
  if (!state.viewer || !window.Cesium) return true;
  const cam = Cesium.Cartesian3.normalize(state.viewer.camera.positionWC, new Cesium.Cartesian3());
  const obj = Cesium.Cartesian3.normalize(position, new Cesium.Cartesian3());
  return Cesium.Cartesian3.dot(cam, obj) > maxBacksideAllowance;
}

function distanceBandForTrack(tr) {
  const posture = usThreatPosture(tr);
  if (posture === 'priority-threat') return { near: 0, far: 30000000 };
  if (posture === 'watchlist') return { near: 0, far: 18000000 };
  return { near: 0, far: 9000000 };
}

function labelForTrack(tr) {
  const posture = usThreatPosture(tr);
  const base = tr.label ? `${tr.id} — ${tr.label}` : `${tr.id}`;
  if (posture === 'priority-threat') return `⚠ ${base}`;
  if (posture === 'watchlist') return `◇ ${base}`;
  return base;
}

function makeEntityGraphics(tr, position) {
  const color = Cesium.Color.fromCssColorString(threatColor(tr.threat_level));
  const selected = state.selectedId === tr.id;
  const headingDeg = Number(tr.sensor?.heading_deg ?? tr.heading_deg ?? 0);
  const heading = Cesium.Math.toRadians(90 - headingDeg);
  const orientation = Cesium.Transforms.headingPitchRollQuaternion(position, new Cesium.HeadingPitchRoll(heading, 0, 0));
  const entities = [];
  const posture = usThreatPosture(tr);
  const high = posture === 'priority-threat';
  const watch = posture === 'watchlist';
  const band = distanceBandForTrack(tr);
  const visible = new Cesium.CallbackProperty(() => entityVisibleFromCamera(position), false);
  const labelVisible = new Cesium.CallbackProperty(() => state.showLabels && entityVisibleFromCamera(position), false);
  const font = high ? 'bold 16px sans-serif' : watch ? 'bold 13px sans-serif' : '11px sans-serif';
  const label = state.showLabels ? {
    text: labelForTrack(tr),
    font,
    fillColor: high ? Cesium.Color.fromCssColorString('#fff2d6') : watch ? Cesium.Color.fromCssColorString('#eaf5ff') : Cesium.Color.fromCssColorString('#d7edff'),
    outlineColor: Cesium.Color.BLACK,
    outlineWidth: high ? 3 : 2,
    style: Cesium.LabelStyle.FILL_AND_OUTLINE,
    pixelOffset: new Cesium.Cartesian2(0, high ? -34 : -25),
    showBackground: true,
    backgroundColor: (high ? Cesium.Color.fromCssColorString('#3b1017') : Cesium.Color.BLACK).withAlpha(high ? 0.78 : 0.48),
    distanceDisplayCondition: new Cesium.DistanceDisplayCondition(band.near, band.far),
    show: labelVisible
  } : undefined;

  const pointSize = high ? 15 : watch ? 10 : 6;
  const point = {
    pixelSize: selected ? pointSize + 4 : pointSize,
    color: color.withAlpha(high ? 0.96 : watch ? 0.88 : 0.74),
    outlineColor: Cesium.Color.WHITE.withAlpha(selected || high ? 0.95 : 0.45),
    outlineWidth: selected || high ? 2.5 : 1,
    distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, high ? 30000000 : watch ? 18000000 : 10000000)
  };
  const spriteSize = high ? 42 : watch ? 34 : 25;
  const billboard = {
    image: spriteUrlForTrack(tr),
    width: selected ? spriteSize + 8 : spriteSize,
    height: selected ? spriteSize + 8 : spriteSize,
    rotation: -heading,
    alignedAxis: Cesium.Cartesian3.ZERO,
    color: Cesium.Color.WHITE.withAlpha(high ? 1.0 : watch ? 0.94 : 0.82),
    verticalOrigin: Cesium.VerticalOrigin.CENTER,
    horizontalOrigin: Cesium.HorizontalOrigin.CENTER,
    distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, high ? 26000000 : watch ? 15000000 : 8500000),
    disableDepthTestDistance: high ? 9000000 : 0
  };
  entities.push({ position, orientation, point, billboard, label, show: visible });

  if (tr.class_type === 'aircraft') {
    entities.push({ position, orientation, show: visible, ellipsoid: { radii: new Cesium.Cartesian3(75, 320, 55), material: color.withAlpha(0.52), outline: true, outlineColor: color.withAlpha(0.78), distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 4500000) } });
    entities.push({ position, orientation, show: visible, box: { dimensions: new Cesium.Cartesian3(820, 28, 10), material: color.withAlpha(0.42), outline: false, distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 4500000) } });
  } else if (tr.class_type === 'drone') {
    entities.push({ position, orientation, show: visible, ellipsoid: { radii: new Cesium.Cartesian3(70, 70, 28), material: color.withAlpha(0.58), outline: true, outlineColor: color.withAlpha(0.85), distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 4200000) } });
  } else if (tr.class_type === 'missile') {
    entities.push({ position, orientation, show: visible, ellipsoid: { radii: new Cesium.Cartesian3(65, 65, 680), material: color.withAlpha(0.86), outline: true, outlineColor: Cesium.Color.WHITE.withAlpha(0.9) } });
  } else if (tr.class_type === 'asteroid') {
    entities.push({ position, orientation, show: visible, ellipsoid: { radii: new Cesium.Cartesian3(360, 260, 220), material: new Cesium.ImageMaterialProperty({ image: spriteUrlForTrack(tr), transparent: true, color: Cesium.Color.WHITE.withAlpha(0.96) }), outline: true, outlineColor: color.withAlpha(0.96) } });
  } else if (tr.class_type === 'foreign_spaceship') {
    entities.push({ position, orientation, show: visible, ellipsoid: { radii: new Cesium.Cartesian3(280, 280, 90), material: color.withAlpha(0.80), outline: true, outlineColor: Cesium.Color.WHITE.withAlpha(0.92) } });
    entities.push({ position, orientation, show: visible, ellipsoid: { radii: new Cesium.Cartesian3(95, 95, 55), material: color.withAlpha(0.58), outline: false } });
  } else {
    entities.push({ position, orientation, show: visible, ellipsoid: { radii: new Cesium.Cartesian3(110, 110, 44), material: color.withAlpha(0.64), outline: true, outlineColor: color.withAlpha(0.9), distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 7000000) } });
  }

  if (high || selected) {
    entities.push({ position, show: visible, ellipse: { semiMajorAxis: high ? 85000 : 52000, semiMinorAxis: high ? 85000 : 52000, material: color.withAlpha(high ? 0.13 : 0.08), outline: true, outlineColor: (selected ? Cesium.Color.WHITE : color).withAlpha(0.95), height: 0, distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, high ? 12000000 : 6000000) } });
  }
  return entities;
}

function addProtectedAirspaces(viewer) {
  US_PROTECTED_AIRSPACES.forEach((z) => {
    const color = Cesium.Color.fromCssColorString(z.level === 'critical' ? '#ff5b72' : '#7db7ff');
    const nearBand = new Cesium.DistanceDisplayCondition(0, 4200000);
    const pos = Cesium.Cartesian3.fromDegrees(z.lon, z.lat, 0);
    const visible = new Cesium.CallbackProperty(() => entityVisibleFromCamera(pos), false);
    viewer.entities.add({
      id: `protected-${z.id}`,
      show: visible,
      position: pos,
      properties: { protectedAirspace: true },
      ellipse: {
        semiMajorAxis: z.radius,
        semiMinorAxis: z.radius,
        material: color.withAlpha(0.08),
        outline: true,
        outlineColor: color.withAlpha(0.85),
        height: 0,
        distanceDisplayCondition: nearBand
      },
      label: {
        text: z.name,
        font: '12px sans-serif',
        fillColor: Cesium.Color.fromCssColorString('#d7edff'),
        pixelOffset: new Cesium.Cartesian2(0, 18),
        showBackground: true,
        backgroundColor: Cesium.Color.BLACK.withAlpha(0.35),
        distanceDisplayCondition: nearBand,
        show: visible
      }
    });
  });
}

function addZoneEllipse(viewer, zone, color, baseHeight = 0, extrude = 900) {
  const g = worldToGeo(zone.x, zone.y, 0);
  viewer.entities.add({
    id: `zone-${zone.name || baseHeight}`,
    properties: { localZone: true },
    position: Cesium.Cartesian3.fromDegrees(g.lon, g.lat, baseHeight),
    ellipse: {
      semiMajorAxis: zone.radius * 240,
      semiMinorAxis: zone.radius * 240,
      material: color.withAlpha(0.12),
      outline: true,
      outlineColor: color,
      height: baseHeight,
      extrudedHeight: baseHeight + extrude,
      classificationType: Cesium.ClassificationType.TERRAIN
    }
  });
}


function presetGlobalCamera() {
  // US-perspective global picture. Keep the reset/default view looking nearly
  // straight down at North America so Earth is centered and fully visible in
  // the 3D viewport instead of sitting at the bottom of the screen.
  if (state.cameraPreset === 'topdown') {
    return { lon: -98, lat: 52, height: 26000000, heading: 0.0, pitch: -Cesium.Math.PI_OVER_TWO, roll: 0 };
  }
  if (state.cameraPreset === 'height') {
    return { lon: -105, lat: 42, height: 23500000, heading: 0.25, pitch: -1.48, roll: 0 };
  }
  return { lon: -104, lat: 44, height: 25500000, heading: 0.0, pitch: -Cesium.Math.PI_OVER_TWO, roll: 0 };
}

function moveCameraGlobal(viewer) {
  state.globeNeedsFrame = false;
  const o = presetGlobalCamera();
  viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(o.lon, o.lat, o.height),
    orientation: { heading: o.heading, pitch: o.pitch, roll: o.roll },
    duration: 0.65
  });
}

function frameGlobeGlobal(viewer) {
  // The 3D mode is now intentionally a global satellite-style picture, so
  // resetting/framing should show the whole Earth rather than zooming into
  // only the local scenario cluster.
  moveCameraGlobal(viewer);
}


function focusSelectedObject3D(overhead = false) {
  if (!state.viewer || !window.Cesium || !state.data?.tracks?.length) return;
  const tr = selectedTrack();
  if (!tr) return;
  const g = worldToGeo(tr.x, tr.y, tr.z, tr);
  const viewer = state.viewer;
  const baseRange = Math.max(70000, Math.min(180000, g.h * 1.2 + 70000));
  if (overhead) {
    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(g.lon, g.lat, g.h + baseRange * 1.35),
      orientation: { heading: 0.0, pitch: -Cesium.Math.PI_OVER_TWO + 0.03, roll: 0 },
      duration: 0.9
    });
    return;
  }
  viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(g.lon - 0.045, g.lat - 0.03, g.h + baseRange),
    orientation: { heading: 0.58, pitch: -0.72, roll: 0 },
    duration: 0.9
  });
}
function renderGlobe() {
  if (!state.view3d) return;
  if (!window.Cesium) { $('#globeFallback').classList.remove('hidden'); return; }
  const viewer = ensureViewer();
  if (!viewer) { $('#globeFallback').classList.remove('hidden'); return; }
  $('#globeFallback').classList.add('hidden');
  viewer.entities.removeAll();

  addProtectedAirspaces(viewer);

  state.data.tracks.filter(shouldShowTrackOnGlobe).forEach(tr => {
    const g = worldToGeo(tr.x, tr.y, tr.z, tr);
    const color = Cesium.Color.fromCssColorString(threatColor(tr.threat_level));
    const position = Cesium.Cartesian3.fromDegrees(g.lon, g.lat, g.h);
    const predictedPositions = (tr.predicted_path || []).slice(0, 10).map(p => {
      const pg = worldToGeo(p[0], p[1], tr.z, tr, { prediction: true });
      return Cesium.Cartesian3.fromDegrees(pg.lon, pg.lat, pg.h);
    });
    const parts = makeEntityGraphics(tr, position);
    parts.forEach((part, idx) => viewer.entities.add({ id: idx === 0 ? tr.id : `${tr.id}__${idx}`, properties: { trackId: tr.id, localTrack: true }, ...part }));
    if (state.showPred && predictedPositions.length) {
      const visible = new Cesium.CallbackProperty(() => entityVisibleFromCamera(position), false);
      viewer.entities.add({ id: `${tr.id}__path`, show: visible, properties: { trackId: tr.id, localTrack: true }, polyline: { positions: predictedPositions, width: usThreatPosture(tr) === 'priority-threat' ? 3.5 : 2, material: color.withAlpha(0.7), clampToGround: false, distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 12000000) } });
    }
  });

  renderGlobalAircraft(viewer);

  if (state.globeNeedsFrame) frameGlobeGlobal(viewer);
}

function renderGlobalAircraft(viewer) {
  const global = state.data?.global_aircraft || [];
  if (!global.length || !window.Cesium) return;
  global.forEach(ac => {
    const position = Cesium.Cartesian3.fromDegrees(ac.lon, ac.lat, Math.max(7000, (ac.altitude_ft || 30000) * 0.3048));
    const heading = Cesium.Math.toRadians(90 - Number(ac.heading || 0));
    const orientation = Cesium.Transforms.headingPitchRollQuaternion(position, new Cesium.HeadingPitchRoll(heading, 0, 0));
    const category = String(ac.category || '').toLowerCase();
    const watch = category.includes('unknown') || category.includes('military') || category.includes('patrol');
    const color = Cesium.Color.fromCssColorString(watch ? '#ffbe4d' : '#9ad1ff');
    const visible = new Cesium.CallbackProperty(() => entityVisibleFromCamera(position), false);
    viewer.entities.add({
      id: `global-${ac.id}`,
      position,
      orientation,
      show: visible,
      properties: { globalAircraft: true },
      point: {
        pixelSize: watch ? 6 : 4,
        color: color.withAlpha(watch ? 0.80 : 0.48),
        outlineColor: Cesium.Color.BLACK.withAlpha(0.5),
        outlineWidth: 1,
        distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, watch ? 15000000 : 9000000)
      },
      ellipsoid: {
        radii: new Cesium.Cartesian3(52, 190, 35),
        material: color.withAlpha(watch ? 0.36 : 0.22),
        outline: watch,
        outlineColor: color.withAlpha(0.65),
        distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 3800000)
      },
      label: {
        text: watch ? `${ac.id} · ${ac.category}` : ac.id,
        font: watch ? 'bold 11px sans-serif' : '10px sans-serif',
        fillColor: watch ? Cesium.Color.fromCssColorString('#fff2d6') : Cesium.Color.fromCssColorString('#b7d8ef'),
        pixelOffset: new Cesium.Cartesian2(0, watch ? -20 : -15),
        showBackground: watch,
        backgroundColor: Cesium.Color.BLACK.withAlpha(0.36),
        distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, watch ? 9000000 : 5000000),
        show: new Cesium.CallbackProperty(() => state.showLabels && entityVisibleFromCamera(position), false)
      }
    });
  });
}





function renderScenarioReadout() {
  const name = scenarioSel.value || state.data?.settings?.scenario || 'mixed_airspace';
  const desc = state.data?.scenarios?.[name] || '';
  const accent = scenarioAccent(name);
  const presets = SCENARIO_PRESETS[name] || {};
  $('#scenarioDescription').innerHTML = `<div class="scenario-chip" style="--accent:${accent}">${name.replaceAll('_',' ')}</div><div>${desc}</div>`;
  $('#scenarioReadout').innerHTML = `<div class="scenario-readout-head"><span class="scenario-chip large" style="--accent:${accent}">${name.replaceAll('_',' ')}</span><span class="scenario-meta">Global simulation · ${weatherSel.value} · wind ${Number(wind.value).toFixed(2)} · jamming ${Number(jamming.value).toFixed(2)}</span></div><div class="scenario-readout-body">${desc}</div>`;
}


function updateResponseTarget() {
  const el = document.getElementById('responseTarget');
  if (!el) return;
  const top = pickDemoTrack();
  if (!top) { el.textContent = 'No tracks available.'; return; }
  el.innerHTML = `Current top priority: ${trackDisplayName(top, true)} <span class="badge ${top.threat_level}">${top.threat_level}</span>`;
}

const RESPONSE_LABELS = {
  monitor: 'monitor only',
  increase_tracking: 'raise sensor priority',
  identity_check: 'identity / transponder check',
  contact_aircraft: 'attempt communications',
  scramble_patrol: 'dispatch patrol aircraft',
  airspace_advisory: 'airspace advisory',
  evacuation_advisory: 'civil protection advisory',
  simulate_intercept: 'simulate defensive workflow'
};

async function submitResponse(action, sourceButton = null) {
  const tr = selectedTrack() || pickDemoTrack();
  if (!tr) {
    appendAdvisorMessage('No track is available to log a response for yet.', 'bot');
    return;
  }

  const previousLabel = sourceButton ? sourceButton.textContent : '';
  if (sourceButton) {
    sourceButton.disabled = true;
    sourceButton.textContent = 'Logging...';
  }

  try {
    const r = await fetch('/api/respond', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({track_id: tr.id, action})
    });
    state.data = await r.json();
    state.rightView = 'response';
    renderAll();
    const label = RESPONSE_LABELS[action] || action.replaceAll('_', ' ');
    appendAdvisorMessage(`Logged simulated response for ${trackDisplayName(tr, true)}: ${label}. You can see it in the Event Log too.`, 'bot');
  } catch (err) {
    appendAdvisorMessage('I could not log that response. Make sure the backend server is still running, then try again.', 'bot');
  } finally {
    const liveBtn = sourceButton?.isConnected ? sourceButton : document.querySelector(`.response-btn[data-response="${action}"]`);
    if (liveBtn) {
      liveBtn.disabled = false;
      liveBtn.textContent = previousLabel || liveBtn.textContent.replace('Logging...', 'Log response');
    }
  }
}

function appendAssistantMessage(text, who='bot', meta='') {
  const box = document.getElementById('assistantMessages');
  if (!box) return null;
  const msg = document.createElement('div');
  msg.className = `assistant-msg ${who}`;
  msg.textContent = text;
  box.appendChild(msg);
  let metaNode = null;
  if (meta) {
    metaNode = document.createElement('div');
    metaNode.className = 'assistant-meta';
    metaNode.textContent = meta;
    box.appendChild(metaNode);
  }
  box.scrollTop = box.scrollHeight;
  return { msg, metaNode };
}

function showAssistantTyping() {
  const box = document.getElementById('assistantMessages');
  if (!box) return null;
  const wrap = document.createElement('div');
  wrap.className = 'assistant-msg bot typing';
  wrap.innerHTML = '<span></span><span></span><span></span>';
  box.appendChild(wrap);
  box.scrollTop = box.scrollHeight;
  return wrap;
}

async function typeAssistantResponse(text, meta='') {
  const created = appendAssistantMessage('', 'bot');
  if (!created) return;
  const target = created.msg;
  const chunk = Math.max(2, Math.min(8, Math.floor((text || '').length / 70) || 3));
  for (let i = 0; i < (text || '').length; i += chunk) {
    target.textContent = (text || '').slice(0, i + chunk);
    const box = document.getElementById('assistantMessages');
    if (box) box.scrollTop = box.scrollHeight;
    await new Promise(r => setTimeout(r, 12));
  }
  if (meta) {
    const box = document.getElementById('assistantMessages');
    const m = document.createElement('div');
    m.className = 'assistant-meta';
    m.textContent = meta;
    box?.appendChild(m);
    if (box) box.scrollTop = box.scrollHeight;
  }
}

async function refreshAssistantStatus() {
  const statusEl = document.getElementById('assistantStatus');
  if (!statusEl) return;
  try {
    const r = await fetch('/api/ask_status');
    const data = await r.json();
    if (data.llm_enabled) {
      statusEl.textContent = `Grounded LLM active (${data.model}) using Orion's knowledge base.`;
    } else {
      statusEl.textContent = 'Local retrieval active. Add OPENAI_API_KEY to enable grounded GPT-4o-mini answers.';
    }
  } catch (e) {
    statusEl.textContent = 'Assistant status unavailable.';
  }
}

async function refreshAdvisorStatus() {
  const statusEl = document.getElementById('advisorStatus');
  if (!statusEl) return;
  try {
    const r = await fetch('/api/advisor_status');
    const data = await r.json();
    if (data.llm_enabled) {
      statusEl.textContent = `LLM active (${data.model}) + local playbook fallback.`;
      statusEl.classList.add('live');
    } else {
      statusEl.textContent = 'Local playbook fallback active. Add OPENAI_API_KEY to enable LLM synthesis.';
      statusEl.classList.remove('live');
    }
  } catch (e) {
    statusEl.textContent = 'Advisor status unavailable.';
    statusEl.classList.remove('live');
  }
}

async function askAssistant(question) {
  const q = (question || document.getElementById('assistantInput')?.value || '').trim();
  if (!q) return;
  appendAssistantMessage(q, 'user');
  const inp = document.getElementById('assistantInput');
  if (inp) inp.value = '';
  const typing = showAssistantTyping();
  try {
    const r = await fetch('/api/ask', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({question:q})});
    const data = await r.json();
    typing?.remove();
    const metaParts = [];
    if (data.used_model) metaParts.push(`${data.used_model}`);
    if (data.sources && data.sources.length) metaParts.push(`Sources: ${data.sources.join(', ')}`);
    await typeAssistantResponse(data.answer || "I could not answer that from Orion's knowledge base.", metaParts.join(' | '));
  } catch (e) {
    typing?.remove();
    await typeAssistantResponse('The Orion assistant could not reach the backend. Check that the FastAPI server is still running.');
  }
}

function appendAdvisorMessage(text, who='bot', meta='') {
  const box = document.getElementById('advisorMessages');
  if (!box) return null;
  const msg = document.createElement('div');
  msg.className = `assistant-msg ${who}`;
  msg.textContent = text;
  box.appendChild(msg);
  if (meta) {
    const m = document.createElement('div');
    m.className = 'assistant-meta';
    m.textContent = meta;
    box.appendChild(m);
  }
  box.scrollTop = box.scrollHeight;
  return msg;
}

async function typeAdvisorResponse(text, meta='') {
  const created = appendAdvisorMessage('', 'bot');
  if (!created) return;
  const target = created;
  const chunk = Math.max(3, Math.min(10, Math.floor((text || '').length / 80) || 4));
  for (let i = 0; i < (text || '').length; i += chunk) {
    target.textContent = (text || '').slice(0, i + chunk);
    const box = document.getElementById('advisorMessages');
    if (box) box.scrollTop = box.scrollHeight;
    await new Promise(r => setTimeout(r, 10));
  }
  if (meta) {
    const box = document.getElementById('advisorMessages');
    const m = document.createElement('div');
    m.className = 'assistant-meta';
    m.textContent = meta;
    box?.appendChild(m);
    if (box) box.scrollTop = box.scrollHeight;
  }
}

function showAdvisorTyping() {
  const box = document.getElementById('advisorMessages');
  if (!box) return null;
  const wrap = document.createElement('div');
  wrap.className = 'assistant-msg bot typing';
  wrap.innerHTML = '<span></span><span></span><span></span>';
  box.appendChild(wrap);
  box.scrollTop = box.scrollHeight;
  return wrap;
}

async function askAdvisor(question) {
  const q = (question || document.getElementById('advisorInput')?.value || '').trim();
  if (!q) return;
  appendAdvisorMessage(q, 'user');
  const inp = document.getElementById('advisorInput');
  if (inp) inp.value = '';
  const typing = showAdvisorTyping();
  try {
    const r = await fetch('/api/advisor', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({question:q})});
    const data = await r.json();
    typing?.remove();
    const meta = `${data.used_model || 'state fusion'} · recommendation: ${data.recommendation || 'n/a'} · confidence: ${Math.round((data.confidence || 0) * 100)}%`;
    await typeAdvisorResponse(data.answer || 'The advisor could not produce a recommendation from the current state.', meta);
  } catch (e) {
    typing?.remove();
    await typeAdvisorResponse('The scenario advisor could not reach the backend. Check that the FastAPI server is still running.');
  }
}

async function renameSelectedObject() {
  const tr = selectedTrack();
  const label = (renameObjectInput?.value || '').trim();
  if (!tr || !label) return;
  const r = await fetch('/api/rename_object', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({track_id: tr.id, label})});
  state.data = await r.json();
  renderAll();
}


function rotateGlobe(direction, multiplier = 1) {
  if (!state.view3d || state.demoActive || !state.viewer || !window.Cesium) return;
  const cam = state.viewer.camera;
  const height = Math.max(1, cam.positionCartographic?.height || 12000000);
  const step = Math.max(0.0025, Math.min(0.026, 700000 / height)) * multiplier;
  try {
    if (direction === 'left') cam.rotate(Cesium.Cartesian3.UNIT_Z, step);
    else if (direction === 'right') cam.rotate(Cesium.Cartesian3.UNIT_Z, -step);
    else if (direction === 'up') cam.rotateUp(step);
    else if (direction === 'down') cam.rotateDown(step);
    else if (direction === 'reset') moveCameraGlobal(state.viewer);
  } catch (e) {
    try {
      if (direction === 'left') cam.rotateLeft(step);
      else if (direction === 'right') cam.rotateRight(step);
      else if (direction === 'up') cam.rotateUp(step);
      else if (direction === 'down') cam.rotateDown(step);
    } catch (_) {}
  }
}

function startGlobePan(direction) {
  rotateGlobe(direction, 1.4);
  clearInterval(state.globePanTimer);
  if (direction === 'reset') return;
  state.globePanTimer = setInterval(() => rotateGlobe(direction, 1.7), 55);
}

function stopGlobePan() {
  clearInterval(state.globePanTimer);
  state.globePanTimer = null;
}

function jumpRight(view, expand = false) {
  if (state.demoActive) return;
  state.rightView = view;
  state.rightCollapsed = false;
  renderAll();
  if (expand && (view === 'assistant' || view === 'response')) setExpandedPanel(view === 'response' ? 'response' : 'assistant');
}

function jumpLeft(view) {
  if (state.demoActive) return;
  state.leftView = view;
  state.leftCollapsed = false;
  renderAll();
}

function renderAll() {
  syncControls();
  syncModeButtons();
  syncModeUI();
  renderSideViews();
  syncPlayButton();
  setViewButtons();
  setStats();
  renderScenarioReadout();
  renderSourceStrip();
  draw2D();
  renderTimeline();
  renderSelected();
  updateResponseTarget();
  normalizeTooltips();
  renderGlobe();
  renderTour();
  positionTooltips();
}


$('#mapCanvas').addEventListener('click', e => {
  if (state.demoActive) return;
  const rect = e.target.getBoundingClientRect();
  const x = (e.clientX - rect.left) * (e.target.width / rect.width);
  const y = (e.clientY - rect.top) * (e.target.height / rect.height);
  let best = null, bestD = 1e9;
  state.data.tracks.forEach(tr => {
    if(!tr._screen) return;
    const d = Math.hypot(tr._screen.x-x, tr._screen.y-y);
    if(d < bestD){ bestD = d; best = tr; }
  });
  if(best && bestD < 30){ state.selectedId = best.id; renderAll(); }
});
$('#mapCanvas').addEventListener('wheel', e => { if(state.demoActive) return; e.preventDefault(); state.mapZoom = Math.max(0.5, Math.min(4, (state.mapZoom || 1) * (e.deltaY < 0 ? 1.12 : 1/1.12))); draw2D(); }, { passive: false });

$('#mapCanvas').addEventListener('mousedown', e => {
  if (state.demoActive || e.button !== 0) return;
  state.dragging2D = true;
  state.lastDragX = e.clientX;
  state.lastDragY = e.clientY;
});
window.addEventListener('mousemove', e => {
  if (!state.dragging2D) return;
  state.mapPanX += (e.clientX - state.lastDragX);
  state.mapPanY += (e.clientY - state.lastDragY);
  state.lastDragX = e.clientX;
  state.lastDragY = e.clientY;
  draw2D();
});
window.addEventListener('mouseup', () => { state.dragging2D = false; });
$('#mapCanvas').addEventListener('mouseleave', () => { if(!state.dragging2D) return; state.dragging2D = false; });

document.querySelectorAll('.tab').forEach(btn => btn.addEventListener('click', () => {
  document.querySelectorAll('.tab').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  state.currentTab = btn.dataset.tab;
  renderSelected();
}));


document.querySelectorAll('[data-left-view]').forEach(btn => btn.addEventListener('click', () => { if(state.demoActive) return; state.leftView = btn.dataset.leftView; renderAll(); }));
document.querySelectorAll('[data-right-view]').forEach(btn => btn.addEventListener('click', () => { if(state.demoActive) return; state.rightView = btn.dataset.rightView; renderAll(); }));
document.querySelectorAll('[data-right-jump]').forEach(btn => btn.addEventListener('click', () => jumpRight(btn.dataset.rightJump, btn.dataset.rightJump === 'response')));
document.querySelectorAll('[data-left-jump]').forEach(btn => btn.addEventListener('click', () => jumpLeft(btn.dataset.leftJump)));
document.getElementById('toggleLeftPanel')?.addEventListener('click', () => { state.leftCollapsed = !state.leftCollapsed; renderAll(); });
document.getElementById('toggleRightPanel')?.addEventListener('click', () => { state.rightCollapsed = !state.rightCollapsed; renderAll(); });
document.getElementById('collapseLeftInline')?.addEventListener('click', () => { state.leftCollapsed = true; renderAll(); });
document.getElementById('collapseRightInline')?.addEventListener('click', () => { state.rightCollapsed = true; renderAll(); });
document.getElementById('restoreLeftPanel')?.addEventListener('click', () => { state.leftCollapsed = false; renderAll(); });
document.getElementById('restoreRightPanel')?.addEventListener('click', () => { state.rightCollapsed = false; renderAll(); });
document.getElementById('dockFocusSelected')?.addEventListener('click', () => { if (!state.view3d) { state.view3d = true; renderAll(); } setTimeout(() => focusSelectedObject3D(false), 50); });
document.querySelectorAll('[data-globe-pan]').forEach(btn => {
  const dir = btn.dataset.globePan;
  btn.addEventListener('pointerdown', (e) => { e.preventDefault(); startGlobePan(dir); });
  btn.addEventListener('pointerup', stopGlobePan);
  btn.addEventListener('pointerleave', stopGlobePan);
  btn.addEventListener('pointercancel', stopGlobePan);
  btn.addEventListener('click', (e) => { if (dir === 'reset') { e.preventDefault(); rotateGlobe('reset'); } });
});
$('#simpleSensors').onclick = () => { state.sensorMode = 'simple'; $('#simpleSensors').classList.add('active'); $('#complexSensors').classList.remove('active'); renderSelected(); };
$('#complexSensors').onclick = () => { state.sensorMode = 'complex'; $('#complexSensors').classList.add('active'); $('#simpleSensors').classList.remove('active'); renderSelected(); };



function setExpandedPanel(name) {
  state.expandedPanel = name;
  if (name === 'assistant') state.rightView = 'assistant';
  if (name === 'response') state.rightView = 'response';
  const backdrop = document.getElementById('panelBackdrop');
  const assistant = document.querySelector('.assistant-card');
  const response = document.querySelector('.response-card');
  assistant?.classList.toggle('panel-expanded', name === 'assistant');
  response?.classList.toggle('panel-expanded', name === 'response');
  document.getElementById('expandAssistantBtn')?.classList.toggle('hidden', name === 'assistant');
  document.getElementById('closeAssistantBtn')?.classList.toggle('hidden', name !== 'assistant');
  document.getElementById('expandResponseBtn')?.classList.toggle('hidden', name === 'response');
  document.getElementById('closeResponseBtn')?.classList.toggle('hidden', name !== 'response');
  backdrop?.classList.toggle('hidden', !name);
  document.getElementById('assistantLauncher')?.classList.toggle('hidden', !!name);
}


function openTechOverlay() {
  $('#techOverlay').classList.add('show');
}

function closeTechOverlay() {
  $('#techOverlay').classList.remove('show');
}

function closeLandingOverlay() {
  const overlay = document.getElementById('helpOverlay');
  overlay?.classList.remove('show');
  if (overlay) overlay.setAttribute('aria-hidden', 'true');
  document.getElementById('howItWorksPanel')?.classList.add('hidden');
  state.demoActive = false;
  state.playing = false;
  renderAll();
  setTimeout(() => {
    if (state.view3d && state.viewer) moveCameraGlobal(state.viewer);
  }, 50);
}

document.getElementById('closeHelp')?.addEventListener('click', () => {
  document.getElementById('helpOverlay')?.classList.remove('show');
  document.getElementById('helpOverlay')?.setAttribute('aria-hidden', 'true');
  startGuidedDemo();
});
document.getElementById('closeHelpX')?.addEventListener('click', closeLandingOverlay);
document.addEventListener('orion-start-demo', () => { startGuidedDemo(); });
document.getElementById('skipHelp')?.addEventListener('click', closeLandingOverlay);
document.getElementById('howBtn')?.addEventListener('click', () => { document.getElementById('howItWorksPanel')?.classList.toggle('hidden'); });
document.getElementById('techBtnIntro')?.addEventListener('click', () => { openTechOverlay(); });
document.getElementById('techBtnTop')?.addEventListener('click', () => { openTechOverlay(); });
document.getElementById('closeTech')?.addEventListener('click', () => { closeTechOverlay(); });
document.getElementById('closeTechX')?.addEventListener('click', () => { closeTechOverlay(); });
document.getElementById('helpOverlay')?.addEventListener('click', (e) => { if (e.target.id === 'helpOverlay') closeLandingOverlay(); });
document.getElementById('techOverlay')?.addEventListener('click', (e) => { if (e.target.id === 'techOverlay') closeTechOverlay(); });
document.getElementById('panelBackdrop')?.addEventListener('click', () => setExpandedPanel(null));
document.getElementById('assistantLauncher')?.addEventListener('click', () => { state.rightView = 'assistant'; renderAll(); setExpandedPanel('assistant'); });
document.getElementById('helpBtn')?.addEventListener('click', () => { $('#helpOverlay').classList.add('show'); $('#helpOverlay').removeAttribute('aria-hidden'); document.getElementById('howItWorksPanel')?.classList.add('hidden'); closeTechOverlay(); });
$('#tourNext').onclick = () => nextTourStep();
$('#tourSkip').onclick = () => endGuidedDemo(true);
$('#guidedToggle').onclick = () => { if(state.demoActive) return; state.guided = true; renderAll(); };
$('#analystToggle').onclick = () => { if(state.demoActive) return; state.guided = false; renderAll(); };
$('#view2d').onclick = () => { if(state.demoActive) return; state.view3d = false; renderAll(); };
$('#view3d').onclick = () => { if(state.demoActive) return; state.view3d = true; state.globeNeedsFrame = true; renderAll(); if (state.viewer) { moveCameraGlobal(state.viewer); } };
$('#playBtn').onclick = () => { if(state.demoActive) return; state.playing = !state.playing; syncPlayButton(); };
$('#stepBtn').onclick = () => { if(state.demoActive) return; step(0.9 * state.speed); };
$('#resetBtn').onclick = () => { if(state.demoActive) return; resetScenario(); };
$('#applySettings').onclick = () => { if(state.demoActive) return; applySettings(false); };
$('#addObjectBtn').onclick = () => { if(state.demoActive) return; addObject(addObjectKind.value); };
$('#removeObjectBtn').onclick = () => { if(state.demoActive) return; removeSelectedObject(); };
$('#removeObjectBtnSecondary').onclick = () => { if(state.demoActive) return; removeSelectedObject(); };
objectSelect.addEventListener('change', e => { if(state.demoActive) return; state.selectedId = e.target.value; renderAll(); });
responseObjectSelect?.addEventListener('change', e => { if(state.demoActive) return; state.selectedId = e.target.value; renderAll(); });
document.getElementById('renameObjectBtn')?.addEventListener('click', () => { if(state.demoActive) return; renameSelectedObject(); });
renameObjectInput?.addEventListener('keydown', e => { if(e.key === 'Enter') renameSelectedObject(); });

$('#focusObject3DBtn').onclick = () => {
  if (state.demoActive) return;
  if (!state.view3d) {
    state.view3d = true;
    renderAll();
  }
  if (state.viewer) {
    focusSelectedObject3D(false);
  } else {
    setTimeout(() => { if (state.viewer) focusSelectedObject3D(false); }, 300);
  }
};
$('#focusObjectTopDownBtn').onclick = () => {
  if (state.demoActive) return;
  if (!state.view3d) {
    state.view3d = true;
    renderAll();
  }
  if (state.viewer) {
    focusSelectedObject3D(true);
  } else {
    setTimeout(() => { if (state.viewer) focusSelectedObject3D(true); }, 300);
  }
};

if (regionSelect) regionSelect.addEventListener('change', e => { state.region = e.target.value; state.globeNeedsFrame = true; renderAll(); if (state.view3d && state.viewer) { moveCameraGlobal(state.viewer); } });
$('#recenter2d').onclick = () => { if(state.demoActive) return; state.mapZoom = 1; state.mapPanX = 0; state.mapPanY = 0; draw2D(); };
$('#recenter3d').onclick = () => { if(state.demoActive) return; state.globeNeedsFrame = true; if(state.view3d && state.viewer) { moveCameraGlobal(state.viewer); } };
$('#zoomInBtn').onclick = () => { if(state.demoActive) return; state.mapZoom = Math.min(4, (state.mapZoom || 1) * 1.2); draw2D(); };
$('#zoomOutBtn').onclick = () => { if(state.demoActive) return; state.mapZoom = Math.max(0.5, (state.mapZoom || 1) / 1.2); draw2D(); };
$('#zoomResetBtn').onclick = () => { if(state.demoActive) return; state.mapZoom = 1; state.mapPanX = 0; state.mapPanY = 0; draw2D(); };
speedSelect.addEventListener('change', e => { state.speed = parseFloat(e.target.value); });
cameraPresetSelect.addEventListener('change', e => { state.cameraPreset = e.target.value; state.globeNeedsFrame = true; if (state.view3d && state.viewer) { moveCameraGlobal(state.viewer); } });
$('#zoomIn3DBtn').onclick = () => { if(state.demoActive || !state.viewer) return; state.viewer.camera.zoomIn(state.viewer.camera.positionCartographic.height * 0.18); };
$('#zoomOut3DBtn').onclick = () => { if(state.demoActive || !state.viewer) return; state.viewer.camera.zoomOut(state.viewer.camera.positionCartographic.height * 0.22); };
$('#zoomReset3DBtn').onclick = () => { if(state.demoActive || !state.viewer) return; state.globeNeedsFrame = true; moveCameraGlobal(state.viewer); };
scenarioSel.addEventListener('change', async () => {
  if (state.demoActive) return;
  const selectedScenario = scenarioSel.value;
  state.loadingScenario = true;
  applyScenarioPreset(selectedScenario);
  state.mapZoom = 1;
  state.mapPanX = 0;
  state.mapPanY = 0;
  state.globeNeedsFrame = true;
  setStats();
  renderScenarioReadout();
  const payload = {
    scenario: selectedScenario,
    weather: weatherSel.value,
    wind: parseFloat(wind.value),
    visibility: parseFloat(visibility.value),
    jamming: parseFloat(jamming.value),
    hazard_intensity: parseFloat(hazardIntensity.value),
    live_data: true,
    guided_mode: state.guided,
    three_d: state.view3d,
  };
  const r = await fetch('/api/reset', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  });
  state.data = await r.json();
  state.selectedId = state.data.tracks?.[0]?.id || null;
  state.loadingScenario = false;
  renderAll();
  if (state.view3d && state.viewer) { moveCameraGlobal(state.viewer); }
});


document.querySelectorAll('.response-btn').forEach(btn => btn.addEventListener('click', () => { if(state.demoActive) return; submitResponse(btn.dataset.response, btn); }));
document.getElementById('expandAssistantBtn')?.addEventListener('click', () => setExpandedPanel('assistant'));
document.getElementById('closeAssistantBtn')?.addEventListener('click', () => setExpandedPanel(null));
document.getElementById('expandResponseBtn')?.addEventListener('click', () => setExpandedPanel('response'));
document.getElementById('closeResponseBtn')?.addEventListener('click', () => setExpandedPanel(null));
const assistantAskBtn = document.getElementById('assistantAskBtn');
if (assistantAskBtn) assistantAskBtn.addEventListener('click', () => askAssistant());
const assistantInput = document.getElementById('assistantInput');
if (assistantInput) assistantInput.addEventListener('keydown', e => { if(e.key === 'Enter') askAssistant(); });
document.querySelectorAll('.assistant-chip:not(.advisor-chip)').forEach(btn => btn.addEventListener('click', () => askAssistant(btn.dataset.question)));
const advisorAskBtn = document.getElementById('advisorAskBtn');
if (advisorAskBtn) advisorAskBtn.addEventListener('click', () => askAdvisor());
const advisorInput = document.getElementById('advisorInput');
if (advisorInput) advisorInput.addEventListener('keydown', e => { if(e.key === 'Enter') askAdvisor(); });
document.querySelectorAll('.advisor-chip').forEach(btn => btn.addEventListener('click', () => askAdvisor(btn.dataset.question)));

setInterval(() => {
  if(state.playing && state.data && !state.demoActive) step(0.8 * state.speed);
}, 1400);

getState();
refreshAssistantStatus();
refreshAdvisorStatus();

window.addEventListener('resize', () => { try { positionTooltips(); } catch(e) {} });
window.addEventListener('scroll', () => { try { positionTooltips(); } catch(e) {} }, {passive:true});

window.addEventListener('keydown', e => {
  const tag = (document.activeElement?.tagName || '').toLowerCase();
  const typing = tag === 'input' || tag === 'textarea' || tag === 'select' || document.activeElement?.isContentEditable;
  if (e.key === 'Escape') {
    if (state.expandedPanel) { setExpandedPanel(null); return; }
    closeTechOverlay();
    if ($('#helpOverlay').classList.contains('show')) { closeLandingOverlay(); }
    return;
  }
  if (!typing && state.view3d && ['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)) {
    e.preventDefault();
    const dir = {ArrowLeft:'left', ArrowRight:'right', ArrowUp:'up', ArrowDown:'down'}[e.key];
    rotateGlobe(dir, e.shiftKey ? 3 : 1.5);
  }
});
window.addEventListener('keyup', e => { if (['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)) stopGlobePan(); });
