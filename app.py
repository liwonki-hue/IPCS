#!/usr/bin/env python3
"""
EPC Piping Material Master System — Streamlit App
HTML 파일과 완전 동일한 색상/레이아웃 구현
"""

import streamlit as st
import pandas as pd
import json, math, re, io
from datetime import date, datetime
from pathlib import Path

st.set_page_config(
    page_title="EPC Piping Material Master",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════════════════════════
# CSS — HTML 완전 동일 (라이트테마 강제, Streamlit chrome 제거)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── 1. Force light mode — dark OS/browser 무시 ── */
html { color-scheme: light only !important; }
html, body, [data-testid="stApp"] {
  background: #f0f4f8 !important;
  color: #1a2332 !important;
}

/* ── 2. Remove ALL Streamlit chrome ── */
#MainMenu, footer, header, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"],
[data-testid="collapsedControl"], [data-testid="stHeader"],
section[data-testid="stSidebar"], [data-testid="manage-app-button"],
.stDeployButton, iframe[title="streamlit_analytics"] { display:none !important; }

/* ── 3. Zero padding — full width ── */
.block-container, [data-testid="stMainBlockContainer"] {
  padding: 0 !important; max-width: 100% !important;
  margin: 0 !important;
}
[data-testid="stAppViewContainer"], [data-testid="stMain"] {
  background: #f0f4f8 !important; padding: 0 !important;
}
.stMainBlockContainer > div { gap: 0 !important; }
.element-container, [data-testid="stVerticalBlock"] > div {
  margin: 0 !important; padding: 0 !important;
}
[data-testid="stHorizontalBlock"] { gap: 6px !important; }

/* ── 4. Tab bar — HTML .nav 완전 동일 ── */
[data-baseweb="tab-list"] {
  background: linear-gradient(135deg,#1a2a4a,#1e3a6e 55%,#1558c0) !important;
  border-bottom: none !important; border-radius: 0 !important;
  padding: 0 28px !important; gap: 0 !important;
}
[data-baseweb="tab"] {
  padding: 9px 18px !important; font-size: 12px !important;
  font-weight: 600 !important; color: rgba(255,255,255,.55) !important;
  background: transparent !important; border: none !important;
  border-bottom: 3px solid transparent !important;
  text-transform: uppercase !important; letter-spacing: .5px !important;
  font-family: sans-serif !important;
}
[data-baseweb="tab"]:hover { color: rgba(255,255,255,.9) !important; }
[aria-selected="true"][data-baseweb="tab"] {
  color: #fff !important;
  border-bottom: 3px solid #60a5fa !important;
  background: rgba(255,255,255,.06) !important;
}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display:none !important; }
[data-baseweb="tab-panel"] { background: #f0f4f8 !important; padding: 0 !important; }

/* ── 5. Form inputs ── */
[data-testid="stTextInput"] > div > div,
[data-testid="stTextInput"] input {
  background: #f7f9fc !important; border: 1px solid #d1dce8 !important;
  border-radius: 6px !important; color: #1a2332 !important; font-size: 12px !important;
}
[data-baseweb="select"] > div {
  background: #f7f9fc !important; border: 1px solid #d1dce8 !important;
  border-radius: 6px !important; color: #1a2332 !important; font-size: 12px !important;
  min-height: 34px !important;
}
[data-baseweb="menu"], [data-baseweb="popover"] > div {
  background: #fff !important; border: 1px solid #d1dce8 !important;
  box-shadow: 0 4px 12px rgba(0,0,0,.09) !important;
}
[data-baseweb="option"] { color: #1a2332 !important; font-size: 12px !important; }
[data-baseweb="option"]:hover { background: #e8f0fd !important; }
label[data-testid="stWidgetLabel"] p {
  color: #4a5568 !important; font-size: 11px !important;
  font-weight: 600 !important;
}

/* ── 6. Buttons ── */
.stButton > button {
  background: #1e6ee8 !important; color: #fff !important; border: none !important;
  border-radius: 6px !important; font-size: 12px !important; font-weight: 600 !important;
  padding: 6px 14px !important;
}
.stButton > button:hover { background: #1558c0 !important; }
.stDownloadButton > button {
  background: #0f9b6c !important; color: #fff !important; border: none !important;
  border-radius: 6px !important; font-size: 12px !important; font-weight: 600 !important;
}
.stDownloadButton > button:hover { background: #0a7a54 !important; }

/* ── 7. Data editor ── */
[data-testid="stDataEditorContainer"] {
  background: #fff !important; border: 1px solid #d1dce8 !important;
  border-radius: 8px !important;
}

/* ── 8. Expander ── */
[data-testid="stExpander"] {
  background: #fff !important; border: 1px solid #d1dce8 !important;
  border-radius: 8px !important; box-shadow: 0 1px 3px rgba(0,0,0,.07) !important;
}
[data-testid="stExpander"] summary { 
  background: #f7f9fc !important; color: #1a2332 !important;
  font-weight: 600 !important; font-size: 13px !important;
}
[data-testid="stExpander"] > div > div { background: #fff !important; }

/* ── 9. Form ── */
[data-testid="stForm"] {
  background: #fff !important; border: 1px solid #d1dce8 !important;
  border-radius: 8px !important; padding: 12px !important;
}

/* ── 10. Alert ── */
[data-testid="stAlert"] { border-radius: 8px !important; font-size: 12px !important; }

/* ── 11. Scrollbar (HTML 동일) ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #e8edf3; }
::-webkit-scrollbar-thumb { background: #d1dce8; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #1e6ee8; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# PATHS & CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
DATA_DIR       = Path(__file__).parent / "data"
ISSUE_LOG_FILE = DATA_DIR / "issue_log.json"
ISO_EDITS_FILE = DATA_DIR / "iso_edits.json"
RECEIVING_FILE = DATA_DIR / "receiving_live.json"

CATMAP = {
    'PIS':'Pipe','PIW':'Pipe','PIX':'Pipe',
    'EL9L':'Fitting','EL9S':'Fitting','EL4L':'Fitting','EL4S':'Fitting',
    'TEE':'Fitting','TER':'Fitting','TRP':'Fitting','RDC':'Fitting',
    'RDE':'Fitting','CAP':'Fitting','CPF':'Fitting','CPH':'Fitting',
    'SWC':'Fitting','SWE':'Fitting','WOL':'Fitting','LOL':'Fitting',
    'PIN':'Fitting','NOZ':'Fitting',
    'FLA':'Flange','FLB':'Flange',
}
CAT_LIST = ['Pipe','Fitting','Flange','Valve','Specialty','Other']
CAT_CLR  = {
    'Pipe':     ('#0f766e','#0f766e20','#0f766e40'),
    'Fitting':  ('#1e6ee8','#1e6ee820','#1e6ee840'),
    'Flange':   ('#7c3aed','#7c3aed20','#7c3aed40'),
    'Valve':    ('#dc2626','#dc262620','#dc262640'),
    'Specialty':('#f97316','#f9731620','#f9731640'),
    'Other':    ('#64748b','#64748b20','#64748b40'),
}
SYS_NAMES = {
    'ST':'Steam','WD':'Water Drain','IA':'Instrument Air','BWF':'Boiler Feed Water',
    'LC':'Level Control','AV':'Air Vent','FO':'Fuel Oil','UW':'Utility Water',
    'DW':'Demineralized Water','SA':'Service Air','IG':'Inert Gas','LO':'Lube Oil',
    'HWS':'Hot Water Supply','HWR':'Hot Water Return','CWS':'Cooling Water Supply',
    'CWR':'Cooling Water Return','CB':'Chemical Blowdown','FG':'Fuel Gas',
    'VS':'Vent Stack','SV':'Safety Valve','PW':'Process Water','RW':'Raw Water',
    'HS':'HP Steam','LS':'LP Steam','LN':'LP N2','CD':'Condensate Drain',
    'CH':'Chemical','AS':'Auxiliary Steam',
}

# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def get_cat(ic):
    k = str(ic).split('-')[0] if '-' in str(ic) else str(ic)
    return CATMAP.get(k, 'Other')

def mm_to_m(qty, uom):
    if uom == 'MM': return math.ceil(qty / 1000), 'M'
    return math.ceil(qty), uom

def parse_iso(iso):
    name  = re.sub(r'\(\d+OF\d+\)', '', iso)
    parts = name.split('-')
    return {'area': parts[2] if len(parts)>2 else '',
            'sys':  parts[5] if len(parts)>5 else '',
            'line': parts[6] if len(parts)>6 else '',
            'short': name}

def cat_badge(cat):
    c, bg, bd = CAT_CLR.get(cat,('#64748b','#64748b20','#64748b40'))
    return (f'<span style="padding:2px 7px;border-radius:4px;font-size:10px;font-weight:700;'
            f'background:{bg};color:{c};border:1px solid {bd};white-space:nowrap">{cat}</span>')

def mc_chip(mc):
    return (f'<span style="font-family:monospace;font-size:11px;font-weight:600;'
            f'color:#1558c0;background:#e8f0fd;border:1px solid rgba(30,110,232,.18);'
            f'padding:3px 7px;border-radius:4px;white-space:nowrap">{mc}</span>')

def spec_chip(s):
    return (f'<span style="background:#ede9fe;color:#7c3aed;border:1px solid rgba(124,58,237,.18);'
            f'padding:2px 7px;border-radius:4px;font-family:monospace;font-size:10px;font-weight:600">{s}</span>')

def prog_bar(pct):
    clr = '#0f9b6c' if pct>=100 else '#d97706' if pct>=50 else '#dc2626'
    fill = min(pct, 100)
    return (f'<div style="display:flex;align-items:center;gap:5px">'
            f'<div style="width:58px;height:7px;background:#e8edf3;border-radius:4px;overflow:hidden">'
            f'<div style="width:{fill:.0f}%;height:100%;background:{clr};border-radius:4px"></div></div>'
            f'<span style="font-size:11px;font-weight:700;color:{clr}">{pct:.1f}%</span></div>')

def N(v):
    try:
        f = float(v)
        return f'{f:,.0f}' if f!=0 else '0'
    except: return '0'

def df_to_excel(df, sheet='Sheet1'):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='xlsxwriter') as w:
        df.to_excel(w, index=False, sheet_name=sheet)
        ws = w.sheets[sheet]
        hf = w.book.add_format({'bold':True,'bg_color':'#1e3a6e','font_color':'#fff','border':1})
        for i, col in enumerate(df.columns):
            ws.write(0, i, col, hf)
            ml = max(df[col].astype(str).map(len).max() if not df.empty else 0, len(str(col)))+2
            ws.set_column(i, i, min(ml, 40))
    return buf.getvalue()

# ═══════════════════════════════════════════════════════════════════════════════
# HTML TABLE (HTML 파일 .tw table 완전 동일)
# ═══════════════════════════════════════════════════════════════════════════════
TH_BASE   = 'background:#1e3a6e'
TH_DESIGN = 'background:#1a52a8'
TH_RCV    = 'background:#0a6e49'
TH_ISS    = 'background:#a05510'
TH_STK    = 'background:#0a6070'
TH_PCT    = 'background:#5328b0'

TABLE_CSS = """
<style>
.ptbl{width:100%;border-collapse:collapse;font-size:12px;background:#fff;
      border:1px solid #d1dce8;border-bottom:none;border-radius:10px 10px 0 0;
      box-shadow:0 1px 3px rgba(0,0,0,.07);overflow:hidden}
.ptbl thead tr th{
  background:#1e3a6e;color:rgba(255,255,255,.85);
  border-bottom:2px solid rgba(255,255,255,.12);
  border-right:1px solid rgba(255,255,255,.08);
  padding:9px 11px;text-align:left;font-size:11px;
  font-weight:700;letter-spacing:.7px;text-transform:uppercase;white-space:nowrap}
.ptbl thead tr th:last-child{border-right:none}
.ptbl tbody tr{border-bottom:1px solid #e4eaf2}
.ptbl tbody tr:nth-child(even){background:#f7f9fc}
.ptbl tbody tr:hover{background:#e8f0fd !important}
.ptbl td{padding:7px 11px;border-right:1px solid #e4eaf2;
         vertical-align:middle;color:#4a5568}
.ptbl td:last-child{border-right:none}
.ptbl-wrap{overflow-x:auto;overflow-y:auto;border-radius:10px 10px 0 0}
.ptbl-foot{padding:6px 20px;font-size:11px;color:#8a9ab5;background:#fff;
           border:1px solid #d1dce8;border-top:none;border-radius:0 0 10px 10px;margin-bottom:14px}
</style>
"""

def html_table(headers, rows, th_styles=None, col_styles=None, height=480):
    if not rows:
        return '<div style="text-align:center;padding:50px;color:#8a9ab5;background:#fff;border:1px solid #d1dce8;border-radius:10px">🔍 결과 없음</div>'
    ths = ''
    for i, h in enumerate(headers):
        ex = (th_styles or {}).get(i, TH_BASE)
        ths += f'<th style="{ex}">{h}</th>'
    trs = ''
    for ri, row in enumerate(rows):
        trs += '<tr>'
        for ci, cell in enumerate(row):
            cs = (col_styles or {}).get(ci, '')
            trs += f'<td style="{cs}">{cell}</td>'
        trs += '</tr>'
    return f"""{TABLE_CSS}
<div class="ptbl-wrap" style="max-height:{height}px">
<table class="ptbl"><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table>
</div>"""

# ═══════════════════════════════════════════════════════════════════════════════
# KPI CARDS (HTML .stats .sc 완전 동일)
# ═══════════════════════════════════════════════════════════════════════════════
KPI_GRAD = {
    'c1':'linear-gradient(90deg,#1e6ee8,#60a5fa)',
    'c2':'linear-gradient(90deg,#0f9b6c,#34d399)',
    'c3':'linear-gradient(90deg,#d97706,#fbbf24)',
    'c4':'linear-gradient(90deg,#7c3aed,#a78bfa)',
    'c5':'linear-gradient(90deg,#0891b2,#22d3ee)',
    'c6':'linear-gradient(90deg,#dc2626,#f87171)',
}

def kpi_row(cards):
    """cards = [(label, value, sub, 'c1'..'c6')]"""
    n = len(cards); items = ''
    for label, value, sub, cc in cards:
        g = KPI_GRAD.get(cc, KPI_GRAD['c1'])
        items += f"""
<div style="background:#fff;border:1px solid #d1dce8;border-radius:10px;
            padding:12px 14px;box-shadow:0 1px 3px rgba(0,0,0,.07);position:relative;overflow:hidden">
  <div style="position:absolute;top:0;left:0;right:0;height:3px;
              border-radius:10px 10px 0 0;background:{g}"></div>
  <div style="font-size:9px;color:#8a9ab5;letter-spacing:1px;text-transform:uppercase;
              font-weight:600;margin:4px 0 4px">{label}</div>
  <div style="font-size:24px;font-weight:800;color:#1a2332;line-height:1.1;font-family:sans-serif">{value}</div>
  <div style="font-size:10px;color:#8a9ab5;margin-top:2px;font-family:monospace">{sub}</div>
</div>"""
    return f'''<div style="display:grid;grid-template-columns:repeat({n},1fr);gap:12px;
padding:14px 28px;background:#e8edf3;border-bottom:1px solid #d1dce8">{items}</div>'''

# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data
def load_master():
    with open(DATA_DIR/'master_v5.json') as f: return json.load(f)

@st.cache_data
def load_iso_bom():
    with open(DATA_DIR/'iso_bom_compact.json') as f: return json.load(f)

@st.cache_data
def load_base_receiving():
    with open(DATA_DIR/'receiving_data.json') as f: return json.load(f)['records']

@st.cache_data
def build_bom_spec(_k):
    mv5  = load_master(); spec = {}
    for r in mv5['pf_summary']:
        mc4 = '-'.join(r['MATERIAL_CODE'].split('-')[:4])
        if mc4 not in spec:
            spec[mc4] = {'matl':r['MATL1'],'size':r['SIZE'],'thick':r['THICK'],
                         'end_type':r.get('END TYPE',''),'uom':r['UOM']}
    return spec

@st.cache_data
def build_iso_maps(_k):
    iso_bom = load_iso_bom(); sm, am = {}, {}
    for iso in iso_bom:
        name  = re.sub(r'\(\d+OF\d+\)','',iso)
        parts = name.split('-')
        area  = parts[2] if len(parts)>2 else ''
        sys   = parts[5] if len(parts)>5 else ''
        sm.setdefault(sys,  []).append(iso)
        am.setdefault(area, []).append(iso)
    return sm, am

def init_session():
    if 'receiving' not in st.session_state:
        st.session_state.receiving = (json.load(open(RECEIVING_FILE)) if RECEIVING_FILE.exists()
                                      else load_base_receiving())
    if 'iso_edits' not in st.session_state:
        st.session_state.iso_edits = (json.load(open(ISO_EDITS_FILE)) if ISO_EDITS_FILE.exists() else {})
    if 'issue_log' not in st.session_state:
        st.session_state.issue_log = (json.load(open(ISSUE_LOG_FILE)) if ISSUE_LOG_FILE.exists() else [])
    if 'issue_next_no' not in st.session_state:
        st.session_state.issue_next_no = len(st.session_state.issue_log)+1

def build_store():
    store = {}
    for rec in st.session_state.receiving:
        mc5 = rec.get('MAT_CODE','')
        if not mc5: continue
        e = store.setdefault(mc5,{'r':0.0,'i':0.0,'pls':[]})
        e['r'] += float(rec.get('QTY',0) or 0)
        pl = rec.get('PACKING_LIST') or rec.get('SHIPMENT','')
        if pl and pl not in e['pls']: e['pls'].append(pl)
    for slip in st.session_state.issue_log:
        for it in slip.get('items',[]):
            for mc5, taken in it.get('deductions',{}).items():
                store.setdefault(mc5,{'r':0.0,'i':0.0,'pls':[]})['i'] += float(taken)
    return store

def rcv_for(store, mc4):
    return sum(v['r'] for k,v in store.items() if k==mc4 or k.startswith(mc4+'-'))
def iss_for(store, mc4):
    return sum(v['i'] for k,v in store.items() if k==mc4 or k.startswith(mc4+'-'))

def build_iso_rows(iso_bom):
    edits = st.session_state.iso_edits; rows = []
    for iso, items in iso_bom.items():
        p = parse_iso(iso)
        for mc4, item_name, uom, base_qty in items:
            qb, uv = mm_to_m(base_qty, uom)
            key = f'{iso}|{mc4}'; ed = edits.get(key,{})
            rows.append({'_key':key,'Area':p['area'],'ISO Drawing':iso,'System':p['sys'],
                'Category':get_cat(mc4.split('-')[0]),'Material Code':mc4,'Item':item_name,
                'Qty':ed.get('qty',qb),'UOM':uv,'Remark':ed.get('remark','')})
    return rows

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER (HTML .hdr 완전 동일)
# ═══════════════════════════════════════════════════════════════════════════════
def render_header(store, mv5):
    pfs   = mv5['pf_summary']
    tot_d = sum(float(r.get('DESIGN_QTY',0)) for r in pfs)
    tot_r = sum(rcv_for(store, r['MATERIAL_CODE']) for r in pfs)
    tot_i = sum(iss_for(store, r['MATERIAL_CODE']) for r in pfs)
    pf_items  = mv5.get('pf_total', 68989)
    bg_items  = mv5.get('bg_total', 5041)
    iso_count = mv5.get('pf_iso_count', 3903)
    mat_codes = len(pfs)
    def hk(v, l):
        return f'''<div style="text-align:center;padding:6px 14px;background:rgba(255,255,255,.08);
border-radius:6px;border:1px solid rgba(255,255,255,.12)">
<div style="font-size:18px;font-weight:800;color:#fff;line-height:1.1;font-family:sans-serif">{v}</div>
<div style="font-size:9px;color:rgba(255,255,255,.5);letter-spacing:1px;text-transform:uppercase">{l}</div>
</div>'''
    st.markdown(f'''<div style="background:linear-gradient(135deg,#1a2a4a,#1e3a6e 55%,#1558c0);
box-shadow:0 4px 16px rgba(21,88,192,.3)">
<div style="display:flex;align-items:center;justify-content:space-between;
            padding:11px 28px;border-bottom:1px solid rgba(255,255,255,.1)">
  <div style="display:flex;align-items:center;gap:12px">
    <div style="width:36px;height:36px;border-radius:9px;background:rgba(255,255,255,.15);
                border:1px solid rgba(255,255,255,.2);display:flex;align-items:center;
                justify-content:center;font-size:16px">🔧</div>
    <div>
      <div style="font-size:15px;font-weight:800;color:#fff;letter-spacing:.4px;
                  font-family:sans-serif">PIPING MATERIAL MASTER FILE</div>
      <div style="font-size:9px;color:rgba(255,255,255,.5);letter-spacing:2px;
                  text-transform:uppercase;font-family:monospace">
        EPC PROJECT · INTEGRATED BOM DATABASE</div>
    </div>
  </div>
  <div style="display:flex;gap:4px;align-items:center">
    {hk(f"{pf_items:,}", "P&F ITEMS")}
    {hk(f"{bg_items:,}", "B&G ITEMS")}
    {hk(f"{iso_count:,}", "ISO DWGS")}
    {hk(f"{mat_codes}", "MAT CODES")}
    <div style="padding:5px 10px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.12);
                border-radius:4px;font-family:monospace;font-size:10px;color:rgba(255,255,255,.5)">
      Rev.A · 2026-01-28</div>
  </div>
</div>
</div>''', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB: SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
def tab_summary(mv5, store):
    for tab_label, data_key, sk, is_pf in [
        ('⚙ PIPING & FITTING','pf_summary','pf',True),
        ('🔩 BOLT & GASKET',  'bg_summary','bg',False),
    ]:
        D = mv5[data_key]
        tot_d = sum(float(r.get('DESIGN_QTY',0)) for r in D)
        tot_r = sum(rcv_for(store,r['MATERIAL_CODE']) for r in D)
        tot_i = sum(iss_for(store,r['MATERIAL_CODE']) for r in D)
        tot_s = tot_r-tot_i
        pct   = round(tot_r/tot_d*100,1) if tot_d>0 else 0.0

        with st.expander(tab_label, expanded=is_pf):
            # KPI row (HTML .stats 완전 동일)
            st.markdown(kpi_row([
                ('Total Mat. Codes', str(len(D)),       'P&F incl. LR/SR split' if is_pf else 'B&G', 'c1'),
                ('Total Design Qty', N(tot_d),           'EA / M combined',                              'c2'),
                ('Total Received',   N(tot_r),           'Incoming receipt total',                       'c3'),
                ('Total Issued',     N(tot_i),           'Material issued to site',                      'c4'),
                ('Total Stock',      N(tot_s),           'On-hand stock (Rcv − Issued)',                 'c5'),
                ('Receipt Progress', f'{pct:.1f}%',    'Receipt progress rate',                        'c6'),
            ]), unsafe_allow_html=True)

            # Controls row (HTML .ctrl 동일)
            st.markdown('<div style="background:#fff;border-bottom:2px solid #d1dce8;padding:8px 28px;box-shadow:0 1px 3px rgba(0,0,0,.07)">', unsafe_allow_html=True)
            if is_pf:
                cc1,cc2,cc3,cc4 = st.columns([4,2,2,2])
                q    = cc1.text_input('Search', key=f'sq_{sk}', placeholder='Search code, item, spec, size...', label_visibility='collapsed')
                fi   = cc2.selectbox('Item', ['All Items']+sorted({r.get('ITEM_DISPLAY') or r.get('ITEM_CODE','') for r in D}), key=f'sfi_{sk}', label_visibility='collapsed')
                fm   = cc3.selectbox('Material', ['All Materials']+sorted({r.get('MATL1','') for r in D if r.get('MATL1')}), key=f'sfm_{sk}', label_visibility='collapsed')
                fcat = cc4.selectbox('Category', ['All Categories']+CAT_LIST, key=f'scat_{sk}', label_visibility='collapsed')
            else:
                cc1,cc2,cc3 = st.columns([4,2,2])
                q  = cc1.text_input('Search', key=f'sq_{sk}', placeholder='Search code, item...', label_visibility='collapsed')
                fi = cc2.selectbox('Item', ['All Items']+sorted({r.get('ITEM') or r.get('ITEM_CODE','') for r in D}), key=f'sfi_{sk}', label_visibility='collapsed')
                fm = 'All Materials'; fcat = 'All Categories'
                cc3.empty()
            st.markdown('</div>', unsafe_allow_html=True)

            # Filter
            filt = []
            for r in D:
                ic  = r.get('ITEM_CODE',''); cat = get_cat(ic)
                disp= r.get('ITEM_DISPLAY') or ic
                if q    and q.lower() not in json.dumps(r).lower(): continue
                if fi   != 'All Items'      and disp != fi:         continue
                if fm   != 'All Materials'  and r.get('MATL1','') != fm: continue
                if fcat != 'All Categories' and cat  != fcat:       continue
                filt.append(r)

            # Action bar
            ac1,ac2 = st.columns([8,2])
            ac1.markdown(f'<div style="padding:6px 28px;font-size:11px;color:#4a5568;font-family:monospace">Showing <span style="color:#1e6ee8;font-weight:700">{len(filt):,}</span> / {len(D):,} materials</div>', unsafe_allow_html=True)
            export_df = pd.DataFrame([{
                'Category':get_cat(r.get('ITEM_CODE','')),'Material Code':r['MATERIAL_CODE'],
                'Item':r.get('ITEM_DISPLAY') or r.get('SRC_ITEMS',''),'Spec':r.get('MATL1',''),
                'Size':r.get('SIZE',''),'Rating':r.get('THICK',''),'End Type':r.get('END TYPE',''),
                'UOM':r.get('UOM',''),
                'Design':float(r.get('DESIGN_QTY',0)),
                'Received':rcv_for(store,r['MATERIAL_CODE']),
                'Issued':iss_for(store,r['MATERIAL_CODE']),
            } for r in filt])
            if not export_df.empty:
                ac2.download_button('⬇ Export Excel',
                    data=df_to_excel(export_df,'Summary'),
                    file_name=f'Summary_{sk}_{date.today()}.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    key=f'dl_sum_{sk}', use_container_width=True)

            # HTML Table (HTML .tw table 완전 동일)
            headers = ['#','CATEGORY','MATERIAL CODE','ITEM','MATERIAL SPEC','SIZE','SCH/RATING','END TYPE','UOM','DESIGN','RECEIVED','ISSUED','STOCK','RECEIPT %']
            th_s = {0:TH_BASE,1:TH_BASE,2:TH_BASE,3:TH_BASE,4:TH_BASE,5:TH_BASE,6:TH_BASE,7:TH_BASE,8:TH_BASE,
                    9:TH_DESIGN,10:TH_RCV,11:TH_ISS,12:TH_STK,13:TH_PCT}
            rows_html = []
            for i, r in enumerate(filt):
                mc  = r['MATERIAL_CODE']; ic = r.get('ITEM_CODE',''); cat = get_cat(ic)
                rv  = rcv_for(store,mc); iv = iss_for(store,mc)
                dq  = float(r.get('DESIGN_QTY',0)); stk = rv-iv
                pbar= prog_bar(round(rv/dq*100,1) if dq>0 else 0.0)
                rv_c= '#0f9b6c' if rv>0 else '#8a9ab5'
                iv_c= '#d97706' if iv>0 else '#8a9ab5'
                sk_c= '#0f9b6c' if stk>0 else '#dc2626' if stk<0 else '#8a9ab5'
                rows_html.append([
                    f'<span style="color:#8a9ab5;font-family:monospace;font-size:11px">{i+1}</span>',
                    cat_badge(cat), mc_chip(mc),
                    f'<span style="font-weight:600;color:#1a2332">{r.get("ITEM_DISPLAY") or ic}</span>',
                    spec_chip(r.get('MATL1','—')),
                    f'<span style="color:#d97706;font-weight:700;font-family:monospace">{r.get("SIZE","—")}</span>',
                    f'<span style="color:#8a9ab5;font-family:monospace;font-size:11px">{r.get("THICK","—")}</span>',
                    r.get('END TYPE','—'),
                    f'<span style="color:#8a9ab5">{r.get("UOM","—")}</span>',
                    f'<span style="font-weight:700;font-family:sans-serif;color:#1558c0;font-size:13px">{N(dq)}</span>',
                    f'<span style="font-weight:700;font-family:sans-serif;color:{rv_c};font-size:13px">{N(rv)}</span>',
                    f'<span style="font-weight:700;font-family:sans-serif;color:{iv_c};font-size:13px">{N(iv)}</span>',
                    f'<span style="font-weight:700;font-family:sans-serif;color:{sk_c};font-size:13px">{N(stk)}</span>',
                    pbar,
                ])
            col_s = {0:'text-align:right',9:'text-align:right;background:rgba(30,110,232,.04)',
                     10:'text-align:right;background:rgba(15,155,108,.04)',
                     11:'text-align:right;background:rgba(217,119,6,.04)',
                     12:'text-align:right;background:rgba(8,96,112,.05)'}
            st.markdown(html_table(headers,rows_html,th_s,col_s,480), unsafe_allow_html=True)
            st.markdown(f'<div class="ptbl-foot">Showing <span style="color:#1e6ee8;font-weight:700">{len(filt):,}</span> / {len(D):,} records</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB: ISO LIST
# ═══════════════════════════════════════════════════════════════════════════════
def tab_iso_list(iso_bom, sys_map, area_map):
    fc1,fc2,fc3,fc4 = st.columns([2,2,2,4])
    f_sys  = fc1.selectbox('System',  ['All Systems'] +sorted(sys_map.keys(),key=lambda s:(-len(sys_map[s]),s)),
        key='il_sys', label_visibility='collapsed',
        format_func=lambda s: f'{s} — {SYS_NAMES.get(s,"")} ({len(sys_map.get(s,[]))})' if s!='All Systems' else 'All Systems')
    f_area = fc2.selectbox('Area',    ['All Areas']+sorted(area_map.keys(),key=lambda a:(-len(area_map[a]),a)),
        key='il_area',label_visibility='collapsed',
        format_func=lambda a: f'{a} ({len(area_map.get(a,[]))})' if a!='All Areas' else 'All Areas')
    f_cat  = fc3.selectbox('Category',['All Categories']+CAT_LIST,key='il_cat',label_visibility='collapsed')
    q      = fc4.text_input('Search',key='il_q',label_visibility='collapsed',placeholder='🔍  Search ISO, code, item...')

    if f_sys!='All Systems' and f_area!='All Areas':
        iso_set=set(sys_map.get(f_sys,[]))&set(area_map.get(f_area,[]))
    elif f_sys!='All Systems': iso_set=set(sys_map.get(f_sys,[]))
    elif f_area!='All Areas':  iso_set=set(area_map.get(f_area,[]))
    else: iso_set=None

    all_rows=build_iso_rows(iso_bom)
    filt=[r for r in all_rows
        if (iso_set is None or r['ISO Drawing'] in iso_set)
        and (f_cat=='All Categories' or r['Category']==f_cat)
        and (not q or q.lower() in (r['ISO Drawing']+r['Material Code']+r['Item']).lower())]

    ac1,ac2,ac3,ac4,ac5=st.columns([3,2,2,2,2])
    ac1.markdown(f'<div style="padding:8px 0;font-size:11px;color:#4a5568;font-family:monospace">Showing <b style="color:#1e6ee8">{len(filt):,}</b> / {len(all_rows):,} rows</div>',unsafe_allow_html=True)
    do_add =ac2.button('➕ Add Row',     key='il_add', use_container_width=True)
    do_imp =ac3.button('📂 Import Excel',key='il_imp', use_container_width=True)
    do_save=ac4.button('💾 Save Changes',key='il_save',type='primary',use_container_width=True)
    if filt:
        df_exp=pd.DataFrame([{k:v for k,v in r.items() if k!='_key'} for r in filt])
        ac5.download_button('⬇ Export Excel',data=df_to_excel(df_exp,'ISO List'),
            file_name=f'ISO_List_{date.today()}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            key='il_export',use_container_width=True)

    df_edit=pd.DataFrame([{k:v for k,v in r.items() if k!='_key'} for r in filt])
    edited =st.data_editor(df_edit,use_container_width=True,hide_index=True,num_rows='dynamic',
        disabled=[c for c in df_edit.columns if c not in ('Qty','Remark')],
        column_config={'Area':st.column_config.TextColumn(width=60),
            'ISO Drawing':st.column_config.TextColumn(width=225),'System':st.column_config.TextColumn(width=55),
            'Category':st.column_config.TextColumn(width=75),'Material Code':st.column_config.TextColumn(width=160),
            'Item':st.column_config.TextColumn(width=120),
            'Qty':st.column_config.NumberColumn(min_value=0,step=1,format='%d',width=65),
            'UOM':st.column_config.TextColumn(width=45),'Remark':st.column_config.TextColumn(width=180)},
        key='il_editor',height=480)

    if do_save:
        edits=st.session_state.iso_edits
        for i,row in edited.iterrows():
            if i<len(filt):
                edits[filt[i]['_key']]={'qty':int(math.ceil(float(row['Qty'] or 0))),'remark':str(row.get('Remark','') or '')}
        st.session_state.iso_edits=edits
        try:
            with open(ISO_EDITS_FILE,'w') as f: json.dump(edits,f)
            st.success('✅ Saved.'); st.cache_data.clear(); st.rerun()
        except Exception as e: st.warning(f'Session saved ({e})')

    if do_add or st.session_state.get('il_show_add'):
        st.session_state['il_show_add']=True
        with st.form('il_add_form',clear_on_submit=True):
            st.markdown('**➕ Add New Row**')
            a1,a2,a3,a4=st.columns(4)
            n_iso=a1.text_input('ISO Drawing *');n_area=a2.text_input('Area')
            n_mc4=a3.text_input('Material Code *');n_cat=a4.selectbox('Category',CAT_LIST)
            b1,b2,b3,b4=st.columns(4)
            n_item=b1.text_input('Item');n_qty=b2.number_input('Qty',min_value=0,step=1,value=0)
            n_uom=b3.selectbox('UOM',['EA','M','KG','SET']);n_rmk=b4.text_input('Remark')
            s1,s2=st.columns(2)
            if s1.form_submit_button('✅ Add',type='primary'):
                if n_iso and n_mc4:
                    st.session_state.iso_edits[f'{n_iso}|{n_mc4}']={' qty':int(n_qty),'remark':n_rmk}
                    st.session_state['il_show_add']=False;st.success('Added');st.rerun()
                else: st.error('ISO Drawing and Material Code required.')
            if s2.form_submit_button('Cancel'):
                st.session_state['il_show_add']=False;st.rerun()

    if do_imp or st.session_state.get('il_show_imp'):
        st.session_state['il_show_imp']=True
        with st.expander('📂 Import Excel',expanded=True):
            up=st.file_uploader('Upload .xlsx',type=['xlsx','xls'],key='il_upload')
            if up:
                try:
                    df_imp=pd.read_excel(up);df_imp.columns=[str(c).strip() for c in df_imp.columns]
                    st.dataframe(df_imp.head(5),use_container_width=True)
                    if st.button('✅ Confirm Import',key='il_imp_ok',type='primary'):
                        edits=st.session_state.iso_edits
                        cl={c.lower().replace(' ','_'):c for c in df_imp.columns}
                        def gc(k): return cl.get(k,cl.get(k.replace('_',' '),None))
                        added=0
                        for _,row in df_imp.iterrows():
                            iso=str(row.get(gc('iso_drawing') or gc('iso'),'') or '').strip()
                            mc4=str(row.get(gc('material_code') or gc('code'),'') or '').strip()
                            if not iso or not mc4: continue
                            edits[f'{iso}|{mc4}']={'qty':int(math.ceil(float(row.get(gc('qty'),0) or 0))),'remark':str(row.get(gc('remark'),'') or '')}
                            added+=1
                        st.session_state.iso_edits=edits;st.session_state['il_show_imp']=False
                        st.success(f'✅ Imported {added} rows.');st.rerun()
                except Exception as e: st.error(f'Import failed: {e}')
            if st.button('Close',key='il_imp_close'):
                st.session_state['il_show_imp']=False;st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB: MASTER LIST
# ═══════════════════════════════════════════════════════════════════════════════
def tab_master(mv5):
    tab1,tab2=st.tabs(['⚙ Piping & Fitting','🔩 Bolt & Gasket'])
    for tab,data_key,is_pf in [(tab1,'pf_master',True),(tab2,'bg_master',False)]:
        with tab:
            D=mv5[data_key];sk=data_key[:2]
            fc1,fc2,fc3,fc4=st.columns([4,2,2,2])
            q    =fc1.text_input('Search',key=f'mq_{sk}',placeholder='🔍  Search code, item, spec, size...',label_visibility='collapsed')
            fcat =fc2.selectbox('Category',['All Categories']+CAT_LIST,key=f'mcat_{sk}',label_visibility='collapsed')
            fi   =fc3.selectbox('Item',['All Items']+sorted({r.get('ITEM') or r.get('ITEM_CODE','') for r in D}),key=f'mfi_{sk}',label_visibility='collapsed')
            fm   =fc4.selectbox('Material',['All Materials']+sorted({r.get('MATL1','') for r in D}),key=f'mfm_{sk}',label_visibility='collapsed') if is_pf else 'All Materials'
            if not is_pf: fc4.empty()

            filt=[]
            for r in D:
                ic=r.get('ITEM_CODE','');cat=get_cat(ic);itm=r.get('ITEM') or ic
                if q    and q.lower() not in json.dumps(r).lower(): continue
                if fcat !='All Categories' and cat!=fcat: continue
                if fi   !='All Items'      and itm!=fi:  continue
                if is_pf and fm!='All Materials' and r.get('MATL1','')!=fm: continue
                filt.append(r)

            ac1,ac2=st.columns([8,2])
            ac1.markdown(f'<div style="padding:6px 0;font-size:11px;color:#4a5568;font-family:monospace">Showing <span style="color:#1e6ee8;font-weight:700">{len(filt):,}</span> / {len(D):,} materials</div>',unsafe_allow_html=True)
            if filt:
                exp_df=pd.DataFrame([{'Category':get_cat(r.get('ITEM_CODE','')),'Material Code':r.get('MATERIAL_CODE',''),
                    'Item':r.get('ITEM') or r.get('ITEM_CODE',''),'Spec':r.get('MATL1',''),
                    'Size':r.get('SIZE') or r.get('PIPE SIZE',''),'Rating':r.get('THICK',''),
                    'End Type':r.get('END TYPE',''),'UOM':r.get('UOM',''),'Total Qty':r.get('TOTAL_QTY',0),
                    'Source':r.get('SOURCES',''),} for r in filt])
                ac2.download_button('⬇ Export Excel',data=df_to_excel(exp_df,'Master'),
                    file_name=f'MasterList_{sk}_{date.today()}.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    key=f'dl_m_{sk}',use_container_width=True)

            headers=['#','CATEGORY','MATERIAL CODE','ITEM','MATERIAL SPEC','SIZE','RATING','END TYPE','UOM','TOTAL QTY','SOURCE']
            th_s={i:TH_BASE for i in range(len(headers))}
            rows_html=[]
            for i,r in enumerate(filt):
                ic=r.get('ITEM_CODE','');cat=get_cat(ic);qty=r.get('TOTAL_QTY',0)
                itm=r.get('ITEM') or ic
                rows_html.append([
                    f'<span style="color:#8a9ab5;font-family:monospace;font-size:11px">{i+1}</span>',
                    cat_badge(cat),mc_chip(r.get('MATERIAL_CODE','')),
                    f'<span style="font-weight:600;color:#1a2332">{itm}</span>',
                    spec_chip(r.get('MATL1','—')),
                    f'<span style="color:#d97706;font-weight:700;font-family:monospace">{r.get("SIZE") or r.get("PIPE SIZE","—")}</span>',
                    f'<span style="color:#8a9ab5;font-family:monospace;font-size:11px">{r.get("THICK","—")}</span>',
                    r.get('END TYPE','—'),
                    f'<span style="color:#8a9ab5">{r.get("UOM","—")}</span>',
                    f'<span style="font-weight:700;font-family:sans-serif;color:#1a2332;font-size:13px">{N(qty)}</span>',
                    r.get('SOURCES','—'),
                ])
            st.markdown(html_table(headers,rows_html,th_s,{0:'text-align:right'},520),unsafe_allow_html=True)
            st.markdown(f'<div class="ptbl-foot">Showing <span style="color:#1e6ee8;font-weight:700">{len(filt):,}</span> / {len(D):,} materials</div>',unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB: RECEIVING
# ═══════════════════════════════════════════════════════════════════════════════
def tab_receiving():
    recs =st.session_state.receiving
    ships=sorted({r.get('SHIPMENT','') for r in recs if r.get('SHIPMENT')})
    pls  =sorted({r.get('PACKING_LIST','') for r in recs if r.get('PACKING_LIST')})
    tot_q=sum(float(r.get('QTY',0) or 0) for r in recs)

    st.markdown(kpi_row([
        ('Total Records',f'{len(recs):,}','All receiving lines','c1'),
        ('Shipments',    f'{len(ships)}', 'Unique shipments',   'c2'),
        ('Total Qty',    N(tot_q),         'Sum of all received','c3'),
    ]),unsafe_allow_html=True)

    fc1,fc2,fc3,fb1,fb2,fb3=st.columns([2,2,3,2,2,2])
    f_ship=fc1.selectbox('Shipment',    ['All Shipments']+ships,key='rv_ship',label_visibility='collapsed')
    f_pl  =fc2.selectbox('Packing List',['All PL']+pls,        key='rv_pl',  label_visibility='collapsed')
    q     =fc3.text_input('Search',key='rv_q',placeholder='🔍  Shipment, code, item...',label_visibility='collapsed')
    show_add=fb1.button('➕ Add Row',   key='rv_add_btn',use_container_width=True)
    show_imp=fb2.button('📂 Import XL', key='rv_imp_btn',use_container_width=True)
    do_save =fb3.button('💾 Save',      key='rv_save_btn',type='primary',use_container_width=True)

    filt=[r for r in recs
        if (f_ship=='All Shipments' or r.get('SHIPMENT')==f_ship)
        and (f_pl=='All PL'         or r.get('PACKING_LIST')==f_pl)
        and (not q or q.lower() in json.dumps(r).lower())]

    COLS=['SHIPMENT','PACKING_LIST','ITEM','QTY','UNIT','MAT_CODE','ITEM_CODE','SIZE_INCH','SCH_CODE','REMARK']
    df_rv=pd.DataFrame(filt,columns=COLS) if filt else pd.DataFrame(columns=COLS)
    c1,c2=st.columns([8,2])
    c1.markdown(f'<div style="padding:6px 0;font-size:11px;color:#4a5568;font-family:monospace">Showing <b style="color:#1e6ee8">{len(filt):,}</b> / {len(recs):,} records</div>',unsafe_allow_html=True)
    if not df_rv.empty:
        c2.download_button('⬇ Export Excel',data=df_to_excel(df_rv,'Receiving'),
            file_name=f'Receiving_{date.today()}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            key='rv_export',use_container_width=True)

    edited_rv=st.data_editor(df_rv,use_container_width=True,hide_index=True,num_rows='dynamic',
        column_config={'QTY':st.column_config.NumberColumn(min_value=0,format='%.0f')},
        key='rv_editor',height=450)

    if do_save:
        ship_set={r.get('SHIPMENT') for r in filt}
        unchanged=[r for r in recs if r.get('SHIPMENT') not in ship_set]
        new_recs=unchanged+edited_rv.to_dict('records')
        st.session_state.receiving=new_recs
        try:
            with open(RECEIVING_FILE,'w') as f: json.dump(new_recs,f)
            st.success(f'✅ Saved {len(new_recs):,} records.')
        except Exception as e: st.warning(f'Session saved ({e})')

    if show_imp or st.session_state.get('rv_show_imp'):
        st.session_state['rv_show_imp']=True
        with st.expander('📂 Import Receiving Excel',expanded=True):
            up=st.file_uploader('Upload Receiving.xlsx',type=['xlsx','xls'],key='rv_upload')
            if up:
                try:
                    df_imp=pd.read_excel(up)
                    for skip in range(5):
                        df_t=pd.read_excel(up,skiprows=skip)
                        if any(k in ' '.join(str(c) for c in df_t.columns).upper() for k in ['ITEM','SHIPMENT','QTY']):
                            df_imp=df_t;break
                    df_imp.columns=[str(c).strip() for c in df_imp.columns]
                    st.dataframe(df_imp.head(5),use_container_width=True)
                    if st.button('✅ Confirm Import',key='rv_imp_ok',type='primary'):
                        new_recs=[]
                        for _,row in df_imp.iterrows():
                            item=str(row.get('ITEM') or row.get('Item','') or '')
                            if not item or item=='nan': continue
                            new_recs.append({'SHIPMENT':str(row.get('SHIPMENT') or '').strip(),
                                'PACKING_LIST':str(row.get('PACKING_LIST') or '').strip(),
                                'ITEM':item.strip(),'QTY':float(row.get('QTY') or 0),
                                'UNIT':str(row.get('UNIT') or 'EA').strip(),
                                'MAT_CODE':str(row.get('MAT_CODE','') or '').strip(),
                                'ITEM_CODE':str(row.get('ITEM_CODE','') or '').strip(),
                                'SIZE_INCH':str(row.get('SIZE_INCH','') or '').strip(),
                                'SCH_CODE':str(row.get('SCH_CODE','') or '').strip(),
                                'REMARK':str(row.get('REMARK','') or '').strip()})
                        st.session_state.receiving=new_recs
                        st.session_state['rv_show_imp']=False
                        st.success(f'✅ Imported {len(new_recs):,} records.');st.rerun()
                except Exception as e: st.error(f'Import failed: {e}')
            if st.button('Close',key='rv_imp_close'):
                st.session_state['rv_show_imp']=False;st.rerun()

    if show_add or st.session_state.get('rv_show_add'):
        st.session_state['rv_show_add']=True
        with st.form('rv_add_form',clear_on_submit=True):
            st.markdown('**➕ Add Receiving Record**')
            a1,a2,a3=st.columns(3)
            n_ship=a1.text_input('Shipment *');n_pl=a2.text_input('Packing List');n_item=a3.text_input('Item *')
            b1,b2,b3,b4=st.columns(4)
            n_qty=b1.number_input('Qty *',min_value=0.0,step=1.0,value=0.0)
            n_unit=b2.selectbox('Unit',['EA','M','KG','SET','PC'])
            n_mc=b3.text_input('Mat Code');n_rmk=b4.text_input('Remark')
            s1,s2=st.columns(2)
            if s1.form_submit_button('➕ Add',type='primary'):
                if n_ship and n_item:
                    st.session_state.receiving.append({'SHIPMENT':n_ship,'PACKING_LIST':n_pl,'ITEM':n_item,
                        'QTY':n_qty,'UNIT':n_unit,'MAT_CODE':n_mc,'ITEM_CODE':'','SIZE_INCH':'','SCH_CODE':'','REMARK':n_rmk})
                    st.session_state['rv_show_add']=False;st.success('Added.');st.rerun()
                else: st.error('Shipment and Item required.')
            if s2.form_submit_button('Cancel'):
                st.session_state['rv_show_add']=False;st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB: ISSUE (HTML ISSUE 탭 완전 동일)
# ═══════════════════════════════════════════════════════════════════════════════
def tab_issue(iso_bom, sys_map, area_map, bom_spec, store):
    # Legend bar (HTML 동일)
    st.markdown(f'''<div style="background:#fff;border-bottom:1px solid #d1dce8;padding:8px 28px;
display:flex;align-items:center;gap:16px;flex-wrap:wrap;font-size:11px;color:#4a5568">
  <span style="font-family:monospace;font-weight:700;color:#1e6ee8">PIPING MATERIAL MASTER FILE</span>
  <span style="color:#d1dce8">·</span>
  <span>Elbow: EL9L/EL9S (90° LR/SR) · EL4L/EL4S (45° LR/SR, 300→45D)</span>
  <span style="color:#d1dce8">·</span>
  <span>Mat.Code includes End Type</span>
  <span style="margin-left:auto;color:#8a9ab5">Rev.A · 2026-01-28 · {len(iso_bom):,} drawings</span>
</div>''', unsafe_allow_html=True)

    # Filter controls
    fc1,fc2,fc3,fc4=st.columns([2,2,4,2])
    f_sys =fc1.selectbox('System',  ['All Systems']+sorted(sys_map.keys(), key=lambda s:(-len(sys_map[s]),s)),
        key='iss_sys',label_visibility='collapsed',
        format_func=lambda s: f'{s} — {SYS_NAMES.get(s,s)}' if s!='All Systems' else 'All Systems')
    f_area=fc2.selectbox('Area',    ['All Areas']+sorted(area_map.keys(), key=lambda a:(-len(area_map[a]),a)),
        key='iss_area',label_visibility='collapsed',
        format_func=lambda a: f'Area {a}' if a!='All Areas' else 'All Areas')
    iso_q =fc3.text_input('Search ISO',key='iss_iso_q',placeholder='🔍  Search ISO drawing no...',label_visibility='collapsed')

    if f_sys!='All Systems' and f_area!='All Areas':
        iso_cands=sorted(set(sys_map.get(f_sys,[]))&set(area_map.get(f_area,[])))
    elif f_sys!='All Systems': iso_cands=sorted(sys_map.get(f_sys,[]))
    elif f_area!='All Areas':  iso_cands=sorted(area_map.get(f_area,[]))
    else: iso_cands=sorted(iso_bom.keys())
    if iso_q: iso_cands=[i for i in iso_cands if iso_q.lower() in i.lower()]

    fc4.markdown(f'<div style="padding:8px 0;font-size:12px;color:#4a5568;font-family:monospace"><b style="color:#1e6ee8">{len(iso_cands):,}</b> ISO drawings</div>',unsafe_allow_html=True)

    issued_set={s['iso'] for s in st.session_state.issue_log}

    # ISO Drawing list (HTML ISSUE 탭 row list 동일)
    iso_rows_html=''
    for i, iso in enumerate(iso_cands[:200]):
        p=parse_iso(iso); n_items=len(iso_bom.get(iso,[]))
        done=iso in issued_set
        bg='#f0f7ff' if i%2==0 else '#fff'
        iso_rows_html+=f'''<div style="display:flex;align-items:center;background:{bg};
border-bottom:1px solid #e4eaf2;padding:9px 20px">
  <span style="font-family:monospace;font-size:12px;font-weight:600;color:{"#0f9b6c" if done else "#1e6ee8"};flex:1">
    {"✓ " if done else ""}{re.sub(r"[(]\d+OF\d+[)]","",iso)}</span>
  <span style="background:#e8f0fd;color:#1558c0;font-family:monospace;font-size:10px;font-weight:700;
               padding:2px 8px;border-radius:4px;margin-right:8px">{p["area"]}</span>
  <span style="background:#e6f7f2;color:#0f9b6c;font-family:monospace;font-size:10px;font-weight:700;
               padding:2px 8px;border-radius:4px;margin-right:8px">{p["sys"]}</span>
  <span style="font-size:11px;color:#8a9ab5;font-family:monospace;white-space:nowrap">{n_items} items</span>
</div>'''

    if not iso_rows_html:
        iso_rows_html='<div style="text-align:center;padding:50px;color:#8a9ab5">🔍 No ISO drawings found</div>'

    st.markdown(f'''<div style="border:1px solid #d1dce8;border-radius:10px;background:#fff;
box-shadow:0 1px 3px rgba(0,0,0,.07);overflow:hidden;max-height:360px;overflow-y:auto;margin:10px 0">
{iso_rows_html}
</div>
{"" if len(iso_cands)<=200 else f'<div style="text-align:center;padding:6px;font-size:11px;color:#8a9ab5">Showing first 200 of {len(iso_cands):,} — use search to narrow down</div>'}''',unsafe_allow_html=True)

    sel_iso=st.selectbox('📋 Select ISO Drawing',
        [None]+iso_cands, key='iss_sel_iso',
        format_func=lambda i: '— Select Drawing —' if i is None else
            ('✓ ' if i in issued_set else '')+re.sub(r'\(\d+OF\d+\)','',i))

    if sel_iso is None:
        if st.session_state.issue_log:
            st.markdown('---')
            st.markdown(f'**📋 Issue Log ({len(st.session_state.issue_log)} slips)**')
            log=[{'Slip No.':s['slip_no'],'Date':s['date'],'ISO':re.sub(r'\(\d+OF\d+\)','',s.get('iso','')),
                  'Area':s.get('area',''),'Items':len(s.get('items',[])),'Total':s.get('total_issued',0),
                  'Req.by':s.get('req',''),'Approved':s.get('appr','')} for s in reversed(st.session_state.issue_log)]
            st.dataframe(pd.DataFrame(log),hide_index=True,use_container_width=True)
        return

    p=parse_iso(sel_iso); iso_short=re.sub(r'\(\d+OF\d+\)','',sel_iso)
    bom_items=iso_bom.get(sel_iso,[])

    st.markdown(f'''<div style="background:#1e3a6e;color:#fff;padding:10px 20px;border-radius:8px;
display:flex;justify-content:space-between;align-items:center;margin:10px 0 8px">
  <div>
    <span style="font-weight:800;font-size:13px">📤 Material Issue Slip</span>
    <span style="margin:0 10px;opacity:.4">|</span>
    <span style="font-family:monospace;color:#93c5fd;font-size:13px">{iso_short}</span>
    <span style="margin:0 8px;opacity:.4">|</span>
    <span style="font-size:11px;opacity:.8">Area: {p["area"]}  System: {p["sys"]}</span>
  </div>
  <span style="font-family:monospace;font-size:10px;opacity:.6">{len(bom_items)} items</span>
</div>''',unsafe_allow_html=True)

    hc1,hc2,hc3,hc4=st.columns(4)
    slip_date=hc1.date_input('Issue Date',value=date.today(),key='iss_date')
    slip_req =hc2.text_input('Requested by',key='iss_req', placeholder='Name / Team')
    slip_cont=hc3.text_input('Contractor',  key='iss_cont')
    slip_appr=hc4.text_input('Approved by', key='iss_appr')
    slip_rmk =st.text_input('Remarks',      key='iss_rmk',placeholder='Optional')

    bom_rows=[]
    for mc4,item_name,uom,base_qty in bom_items:
        qv,uv=mm_to_m(base_qty,uom); rv=rcv_for(store,mc4); iv=iss_for(store,mc4)
        bal=rv-iv; spec=bom_spec.get(mc4,{})
        bom_rows.append({'_mc4':mc4,'Area':p['area'],'ISO Drawing':iso_short,
            'Category':get_cat(mc4.split('-')[0]),'Material Code':mc4,'Item':item_name,
            'Spec':spec.get('matl',''),'Size':spec.get('size',''),'Rating':spec.get('thick',''),
            'End Type':spec.get('end_type',''),'UOM':uv,'Design':float(qv),
            'BOM Qty':float(qv),'Rcv Qty':float(rv),
            'Issue Qty':float(min(qv,max(0,bal))),'Balance':float(bal)})

    df_bom=pd.DataFrame(bom_rows).drop(columns=['_mc4'])
    edited_bom=st.data_editor(df_bom,use_container_width=True,hide_index=True,
        disabled=[c for c in df_bom.columns if c!='Issue Qty'],
        column_config={'Category':st.column_config.TextColumn(width=70),
            'Material Code':st.column_config.TextColumn(width=155),
            'Design':st.column_config.NumberColumn(format='%.0f',width=65),
            'BOM Qty':st.column_config.NumberColumn(format='%.0f',width=65),
            'Rcv Qty':st.column_config.NumberColumn(format='%.0f',width=65),
            'Issue Qty':st.column_config.NumberColumn(min_value=0,step=1,format='%.0f',width=80),
            'Balance':st.column_config.NumberColumn(format='%.0f',width=65)},
        key='iss_bom_ed',height=340)

    bc1,bc2,bc3=st.columns([3,2,2])
    if bc1.button('💾 Save & Generate Slip',type='primary',key='iss_save',use_container_width=True):
        issue_items=[]; total_iss=0
        for i,row in edited_bom.iterrows():
            iq=float(row.get('Issue Qty') or 0)
            if iq<=0: continue
            mc4=bom_rows[i]['_mc4']; rv=bom_rows[i]['Rcv Qty']
            if rv<=0: continue
            iq=min(iq,rv); deductions={}; remaining=iq
            matches=sorted([r for r in st.session_state.receiving
                if r.get('MAT_CODE','')==mc4 or r.get('MAT_CODE','').startswith(mc4+'-')],
                key=lambda r:r.get('SHIPMENT',''))
            for rec in matches:
                if remaining<=0: break
                mc5=rec['MAT_CODE']
                avail=max(0,store.get(mc5,{}).get('r',0)-store.get(mc5,{}).get('i',0))
                take=min(remaining,avail)
                if take>0: deductions[mc5]=deductions.get(mc5,0)+take; remaining-=take
            issue_items.append({'mc4':mc4,'item':row['Item'],'spec':row['Spec'],
                'size':row['Size'],'rating':row['Rating'],'end_type':row['End Type'],
                'uom':row['UOM'],'bom_qty':row['BOM Qty'],'rcv_qty':rv,'iss_qty':iq,
                'deductions':deductions,
                'packing_lists':list({r.get('PACKING_LIST','') for r in matches if r['MAT_CODE'] in deductions})})
            total_iss+=iq
        if not issue_items: st.warning('No items with Issue Qty > 0 and received qty.')
        else:
            slip_no=f'MIS-{st.session_state.issue_next_no:03d}'
            slip={'slip_no':slip_no,'date':str(slip_date),'iso':sel_iso,'area':p['area'],
                'sys':p['sys'],'line':p['line'],'req':slip_req,'cont':slip_cont,'appr':slip_appr,
                'rmk':slip_rmk,'items':issue_items,'total_issued':total_iss,'saved_at':datetime.now().isoformat()}
            st.session_state.issue_log.append(slip)
            st.session_state.issue_next_no+=1
            try:
                with open(ISSUE_LOG_FILE,'w') as f: json.dump(st.session_state.issue_log,f)
            except Exception: pass
            st.success(f'✅ {slip_no} — {len(issue_items)} items, {total_iss:.0f} total issued.')
            bc2.download_button('🖨 Download Slip',data=build_slip_html(slip,bom_rows),
                file_name=f'{slip_no}_{date.today()}.html',mime='text/html',key='iss_dl',use_container_width=True)

    bc3.download_button('⬇ Export BOM',data=df_to_excel(edited_bom,'BOM'),
        file_name=f'BOM_{iso_short.replace("-","_")}_{date.today()}.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        key='iss_bom_xl',use_container_width=True)

    if st.session_state.issue_log:
        with st.expander(f'📋 Issue Log ({len(st.session_state.issue_log)} slips)'):
            log=[{'Slip No.':s['slip_no'],'Date':s['date'],'ISO':re.sub(r'\(\d+OF\d+\)','',s.get('iso','')),
                  'Area':s.get('area',''),'Items':len(s.get('items',[])),'Total':s.get('total_issued',0),
                  'Req.by':s.get('req',''),'Approved':s.get('appr','')} for s in reversed(st.session_state.issue_log)]
            st.dataframe(pd.DataFrame(log),hide_index=True,use_container_width=True)

def build_slip_html(slip,bom_rows):
    iso_short=re.sub(r'\(\d+OF\d+\)','',slip.get('iso',''))
    rows_html=''
    for i,it in enumerate(slip.get('items',[])):
        pls=list({p for p in it.get('packing_lists',[]) if p});pl_text='<br>'.join(pls) if pls else '—'
        rows_html+=f'<tr><td style="text-align:center">{i+1}</td><td style="font-family:monospace;font-size:8pt">{it["mc4"]}</td><td>{it["item"]}</td><td>{it["spec"]}</td><td style="text-align:center">{it["size"]}</td><td style="text-align:center">{it["rating"]}</td><td style="text-align:center">{it["end_type"]}</td><td style="text-align:center">{it["uom"]}</td><td style="text-align:right;font-weight:700">{it["bom_qty"]:.0f}</td><td style="text-align:right;font-weight:700">{it["rcv_qty"]:.0f}</td><td style="text-align:right;font-weight:800;color:#0a6641">{it["iss_qty"]:.0f}</td><td style="font-size:8pt;color:#555">{pl_text}</td></tr>'
    total_iss=slip.get('total_issued',0)
    sigs=''.join(f'<td style="padding:8px;text-align:center;width:25%"><div style="font-size:8pt;color:#777;margin-bottom:28px">{l}</div><div style="border-top:1px solid #555;padding-top:4px;font-size:8pt;color:#aaa">Signature / Date</div></td>'
        for l in [f'Issued by',f'Requested by · {slip.get("req","")}','Checked by',f'Approved by · {slip.get("appr","")}'])
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Material Issue Slip {slip["slip_no"]}</title>
<style>body{{font-family:Arial,sans-serif;font-size:10pt;margin:20px}}
table{{width:100%;border-collapse:collapse}}th,td{{border:1px solid #ccc;padding:4px 7px}}
thead tr{{background:#1a2332;color:#fff;font-size:8pt}}tfoot tr{{background:#f0f4f8;font-weight:800}}
.il td{{border:1px solid #d1dce8}}.lb{{background:#f5f7fa;font-size:8pt;font-weight:700;color:#666;width:14%}}
@media print{{@page{{size:A4 landscape;margin:15mm}}}}</style></head><body>
<div style="display:flex;justify-content:space-between;border-bottom:2.5px solid #1a2332;padding-bottom:10px;margin-bottom:12px">
<div><div style="font-size:16pt;font-weight:900;color:#1a2332">MATERIAL ISSUE SLIP</div>
<div style="font-size:9pt;color:#666">EPC Project · Piping Material Management · FIFO Basis</div></div>
<div style="text-align:right"><div style="font-size:8pt;color:#666;font-weight:700">ISO DRAWING NO.</div>
<div style="font-family:monospace;font-size:12pt;font-weight:900;color:#1e6ee8">{iso_short}</div></div></div>
<table class="il" style="margin-bottom:10px"><tr>
<td class="lb">SLIP NO.</td><td style="font-weight:800;color:#1e6ee8;width:19%">{slip["slip_no"]}</td>
<td class="lb">DATE</td><td style="width:19%">{slip["date"]}</td>
<td class="lb">AREA</td><td>{slip.get("area","—")}</td></tr>
<tr><td class="lb">LINE NO.</td><td>{slip.get("line","—")}</td>
<td class="lb">REQUESTED BY</td><td>{slip.get("req","—")}</td>
<td class="lb">CONTRACTOR</td><td>{slip.get("cont","—")}</td></tr>
<tr><td class="lb">APPROVED BY</td><td colspan="5">{slip.get("appr","—")}</td></tr></table>
<table><thead><tr><th>#</th><th>Material Code</th><th>Item</th><th>Spec</th>
<th>Size</th><th>Rating</th><th>End Type</th><th>UOM</th>
<th>BOM Qty</th><th>Rcv Qty</th><th style="background:#0a6641">Issue Qty</th>
<th style="background:#1a3a1a">Packing List (FIFO)</th></tr></thead>
<tbody>{rows_html}</tbody><tfoot><tr><td colspan="10" style="text-align:right">TOTAL</td>
<td style="text-align:right;color:#0a6641;font-size:11pt">{total_iss:.0f}</td><td></td></tr></tfoot></table>
<table style="margin-top:28px"><tr>{sigs}</tr></table>
<div style="text-align:right;font-size:7pt;color:#bbb;margin-top:8px">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
<script>window.onload=function(){{window.print()}}</script></body></html>'''

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    mv5     =load_master()
    iso_bom =load_iso_bom()
    bom_spec=build_bom_spec('v1')
    sys_map,area_map=build_iso_maps('v1')
    init_session()
    store=build_store()
    render_header(store,mv5)

    t1,t2,t3,t4,t5=st.tabs(['📊 SUMMARY','📋 ISO LIST','📃 MASTER LIST','📦 RECEIVING','📤 ISSUE'])
    with t1: tab_summary(mv5,store)
    with t2: tab_iso_list(iso_bom,sys_map,area_map)
    with t3: tab_master(mv5)
    with t4: tab_receiving()
    with t5: tab_issue(iso_bom,sys_map,area_map,bom_spec,store)

if __name__=='__main__':
    main()
