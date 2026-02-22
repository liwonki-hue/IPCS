#!/usr/bin/env python3
"""
EPC Piping Material Master System
Streamlit Multi-Tab App
Tabs: SUMMARY | ISO LIST | MASTER LIST | RECEIVING | ISSUE
"""

import streamlit as st
import pandas as pd
import json, math, re, io, os
from datetime import date, datetime
from pathlib import Path

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EPC Piping Material Master",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Main background */
.stApp { background-color: #0f172a; color: #e2e8f0; }
/* Metric cards */
div[data-testid="metric-container"] {
    background:#1e293b; border:1px solid #334155;
    border-radius:10px; padding:12px 16px;
}
div[data-testid="metric-container"] label { color:#94a3b8; font-size:11px; }
div[data-testid="metric-container"] [data-testid="stMetricValue"] { color:#f1f5f9; font-size:24px; font-weight:800; }
/* Tabs */
button[data-baseweb="tab"] { font-size:13px; font-weight:600; }
/* Dataframe */
.stDataFrame { border-radius:8px; }
/* Headers */
h1,h2,h3 { color:#f1f5f9; }
/* Buttons */
.stButton>button { border-radius:6px; font-weight:600; }
/* Category badge colors */
.cat-Pipe    { background:#134e4a; color:#5eead4; border:1px solid #0d9488; border-radius:4px; padding:2px 7px; font-size:11px; }
.cat-Fitting { background:#1e3a5f; color:#93c5fd; border:1px solid #3b82f6; border-radius:4px; padding:2px 7px; font-size:11px; }
.cat-Flange  { background:#3b1f5e; color:#d8b4fe; border:1px solid #9333ea; border-radius:4px; padding:2px 7px; font-size:11px; }
.cat-Valve   { background:#5e1f1f; color:#fca5a5; border:1px solid #dc2626; border-radius:4px; padding:2px 7px; font-size:11px; }
.cat-Specialty{background:#5e3a1f; color:#fdba74; border:1px solid #f97316; border-radius:4px; padding:2px 7px; font-size:11px; }
.cat-Other   { background:#334155; color:#94a3b8; border:1px solid #64748b; border-radius:4px; padding:2px 7px; font-size:11px; }
div.stSpinner > div { border-top-color: #3b82f6 !important; }
</style>
""", unsafe_allow_html=True)

# ─── PATHS ────────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"
ISSUE_LOG_FILE    = DATA_DIR / "issue_log.json"
ISO_EDITS_FILE    = DATA_DIR / "iso_edits.json"
RECEIVING_FILE    = DATA_DIR / "receiving_live.json"

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
CATMAP = {
    'PIS':'Pipe','PIW':'Pipe','PIX':'Pipe',
    'EL9L':'Fitting','EL9S':'Fitting','EL4L':'Fitting','EL4S':'Fitting',
    'TEE':'Fitting','TER':'Fitting','TRP':'Fitting',
    'RDC':'Fitting','RDE':'Fitting','CAP':'Fitting',
    'CPF':'Fitting','CPH':'Fitting','SWC':'Fitting','SWE':'Fitting',
    'WOL':'Fitting','LOL':'Fitting','PIN':'Fitting','NOZ':'Fitting',
    'FLA':'Flange','FLB':'Flange',
}
CAT_LIST = ['Pipe','Fitting','Flange','Valve','Specialty','Other']
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

# ─── DATA LOADING ─────────────────────────────────────────────────────────────
@st.cache_data
def load_master():
    with open(DATA_DIR / "master_v5.json") as f:
        return json.load(f)

@st.cache_data
def load_iso_bom():
    with open(DATA_DIR / "iso_bom_compact.json") as f:
        return json.load(f)

@st.cache_data
def load_base_receiving():
    with open(DATA_DIR / "receiving_data.json") as f:
        return json.load(f)["records"]

@st.cache_data
def build_bom_spec(mv5_json: str):
    mv5 = json.loads(mv5_json)
    spec = {}
    for r in mv5["pf_summary"]:
        mc5   = r["MATERIAL_CODE"]
        mc4   = "-".join(mc5.split("-")[:4])
        if mc4 not in spec:
            spec[mc4] = {
                "item_code": r["ITEM_CODE"],
                "matl":      r["MATL1"],
                "size":      r["SIZE"],
                "thick":     r["THICK"],
                "end_type":  r.get("END TYPE", ""),
                "uom":       r["UOM"],
            }
    return spec

@st.cache_data
def build_iso_maps(iso_bom_json: str):
    iso_bom = json.loads(iso_bom_json)
    sys_map  = {}   # sys_code → [iso, ...]
    area_map = {}   # area    → [iso, ...]
    for iso in iso_bom:
        name  = re.sub(r"\(\d+OF\d+\)", "", iso)
        parts = name.split("-")
        area  = parts[2] if len(parts) > 2 else ""
        sys   = parts[5] if len(parts) > 5 else ""
        sys_map.setdefault(sys,  []).append(iso)
        area_map.setdefault(area, []).append(iso)
    return sys_map, area_map

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def get_cat(item_code: str) -> str:
    return CATMAP.get(item_code, "Other")

def mm_to_m(qty: float, uom: str):
    if uom == "MM":
        return math.ceil(qty / 1000), "M"
    return math.ceil(qty), uom

def parse_iso(iso: str) -> dict:
    name  = re.sub(r"\(\d+OF\d+\)", "", iso)
    parts = name.split("-")
    return {
        "area": parts[2] if len(parts) > 2 else "",
        "sys":  parts[5] if len(parts) > 5 else "",
        "line": parts[6] if len(parts) > 6 else "",
        "short": name,
    }

def df_to_excel(df: pd.DataFrame, sheet: str = "Sheet1") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
        df.to_excel(w, index=False, sheet_name=sheet)
        ws = w.sheets[sheet]
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(str(col))) + 2
            ws.set_column(i, i, min(max_len, 40))
    return buf.getvalue()

# ─── SESSION STATE ────────────────────────────────────────────────────────────
def init_session():
    # Receiving records (mutable)
    if "receiving" not in st.session_state:
        live = RECEIVING_FILE
        if live.exists():
            with open(live) as f:
                st.session_state.receiving = json.load(f)
        else:
            st.session_state.receiving = load_base_receiving()

    # ISO list edits {(iso,mc4): {qty, remark}}
    if "iso_edits" not in st.session_state:
        if ISO_EDITS_FILE.exists():
            with open(ISO_EDITS_FILE) as f:
                st.session_state.iso_edits = json.load(f)
        else:
            st.session_state.iso_edits = {}

    # Issue log
    if "issue_log" not in st.session_state:
        if ISSUE_LOG_FILE.exists():
            with open(ISSUE_LOG_FILE) as f:
                st.session_state.issue_log = json.load(f)
        else:
            st.session_state.issue_log = []

    if "issue_next_no" not in st.session_state:
        st.session_state.issue_next_no = len(st.session_state.issue_log) + 1

# ─── STORE: RECEIVED / ISSUED per 5-part MC ───────────────────────────────────
def build_store() -> dict:
    store = {}
    for rec in st.session_state.receiving:
        mc5 = rec.get("MAT_CODE", "")
        qty = float(rec.get("QTY", 0) or 0)
        e   = store.setdefault(mc5, {"r": 0.0, "i": 0.0, "pls": []})
        e["r"] += qty
        pl = rec.get("PACKING_LIST", rec.get("SHIPMENT", ""))
        if pl and pl not in e["pls"]:
            e["pls"].append(pl)
    for slip in st.session_state.issue_log:
        for it in slip.get("items", []):
            for mc5, taken in it.get("deductions", {}).items():
                e = store.setdefault(mc5, {"r": 0.0, "i": 0.0, "pls": []})
                e["i"] += taken
    return store

def rcv_for(store, mc4):
    return sum(v["r"] for k, v in store.items() if k == mc4 or k.startswith(mc4 + "-"))

def iss_for(store, mc4):
    return sum(v["i"] for k, v in store.items() if k == mc4 or k.startswith(mc4 + "-"))

# ─── ISO LIST ROWS ────────────────────────────────────────────────────────────
def build_iso_rows(iso_bom: dict) -> list[dict]:
    """Build flat ISO BOM rows, applying any saved edits."""
    edits = st.session_state.iso_edits
    rows  = []
    for iso, items in iso_bom.items():
        p = parse_iso(iso)
        for mc4, item_name, uom, base_qty in items:
            qty_base, uom_v = mm_to_m(base_qty, uom)
            key = f"{iso}|{mc4}"
            ed  = edits.get(key, {})
            rows.append({
                "_key":   key,
                "Area":   p["area"],
                "ISO Drawing": iso,
                "System": p["sys"],
                "Category": get_cat(mc4.split("-")[0]),
                "Material Code": mc4,
                "Item":   item_name,
                "Qty":    ed.get("qty", qty_base),
                "UOM":    uom_v,
                "Remark": ed.get("remark", ""),
            })
    return rows

# ─── SUMMARY TAB ──────────────────────────────────────────────────────────────
def tab_summary(mv5, store):
    st.subheader("📊 Summary")

    for tab_label, data_key, store_key in [
        ("⚙ Piping & Fitting", "pf_summary", "pf"),
        ("🔩 Bolt & Gasket",   "bg_summary", "bg"),
    ]:
        D = mv5[data_key]

        # KPIs
        tot_d = sum(float(r.get("DESIGN_QTY", 0)) for r in D)
        tot_r = sum(rcv_for(store, r["MATERIAL_CODE"]) for r in D)
        tot_i = sum(iss_for(store, r["MATERIAL_CODE"]) for r in D)
        tot_s = tot_r - tot_i
        pct   = round(tot_r / tot_d * 100, 1) if tot_d > 0 else 0.0

        with st.expander(tab_label, expanded=(tab_label.startswith("⚙"))):
            c1,c2,c3,c4,c5 = st.columns(5)
            c1.metric("📐 Design Total", f"{tot_d:,.0f}")
            c2.metric("📦 Received",     f"{tot_r:,.0f}")
            c3.metric("📤 Issued",       f"{tot_i:,.0f}")
            c4.metric("🏪 On-Hand Stock",f"{tot_s:,.0f}")
            c5.metric("✅ Coverage",     f"{pct:.1f}%")

            # Filters
            fc1, fc2, fc3 = st.columns([3,2,2])
            q    = fc1.text_input("🔍 Search", key=f"sq_{store_key}", placeholder="Code, item, spec, size…")
            fi   = fc2.selectbox("Item Type", ["All Items"] + sorted({r.get("ITEM_DISPLAY") or r.get("ITEM_CODE","") for r in D}), key=f"sfi_{store_key}")
            fcat = fc3.selectbox("Category", ["All Categories"] + CAT_LIST, key=f"scat_{store_key}")

            rows = []
            for r in D:
                ic   = r.get("ITEM_CODE","")
                cat  = get_cat(ic)
                disp = r.get("ITEM_DISPLAY") or ic
                if q and q.lower() not in json.dumps(r).lower(): continue
                if fi   != "All Items"      and disp != fi:   continue
                if fcat != "All Categories" and cat  != fcat: continue
                mc   = r["MATERIAL_CODE"]
                rv   = rcv_for(store, mc)
                iv   = iss_for(store, mc)
                dq   = float(r.get("DESIGN_QTY", 0))
                rows.append({
                    "Category":     cat,
                    "Material Code":mc,
                    "Item":         r.get("ITEM_DISPLAY") or r.get("SRC_ITEMS",""),
                    "Spec":         r.get("MATL1",""),
                    "Size":         r.get("SIZE",""),
                    "Rating":       r.get("THICK",""),
                    "End Type":     r.get("END TYPE",""),
                    "UOM":          r.get("UOM",""),
                    "Design":       dq,
                    "Received":     rv,
                    "Issued":       iv,
                    "Stock":        rv - iv,
                    "Coverage%":    round(rv/dq*100,1) if dq>0 else 0.0,
                })

            df = pd.DataFrame(rows)
            if not df.empty:
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Category":     st.column_config.TextColumn(width=80),
                        "Material Code":st.column_config.TextColumn(width=160),
                        "Design":       st.column_config.NumberColumn(format="%.0f"),
                        "Received":     st.column_config.NumberColumn(format="%.0f"),
                        "Issued":       st.column_config.NumberColumn(format="%.0f"),
                        "Stock":        st.column_config.NumberColumn(format="%.0f"),
                        "Coverage%":    st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
                    },
                    height=500,
                )
                st.caption(f"Showing {len(df):,} / {len(D):,} materials")
                st.download_button(
                    "⬇ Export Excel",
                    data=df_to_excel(df, "Summary"),
                    file_name=f"Summary_{store_key}_{date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_sum_{store_key}",
                )

# ─── ISO LIST TAB ─────────────────────────────────────────────────────────────
def tab_iso_list(iso_bom: dict, sys_map: dict, area_map: dict):
    st.subheader("📋 ISO List")

    # ── Filters ──────────────────────────────────────────────────────────────
    fc1,fc2,fc3,fc4,fc5 = st.columns([2,2,2,2,3])
    sys_opts  = ["All Systems"]  + sorted(sys_map.keys(),  key=lambda s: (-len(sys_map[s]), s))
    area_opts = ["All Areas"]    + sorted(area_map.keys(), key=lambda a: (-len(area_map[a]),a))
    f_sys  = fc1.selectbox("System",   sys_opts,  key="il_sys")
    f_area = fc2.selectbox("Area",     area_opts, key="il_area")
    f_cat  = fc3.selectbox("Category", ["All Categories"]+CAT_LIST, key="il_cat")
    f_iso_opts = ["All ISOs"]
    if f_sys  != "All Systems":  f_iso_opts += sorted(sys_map[f_sys])
    elif f_area!= "All Areas":   f_iso_opts += sorted(area_map[f_area])
    f_iso  = fc4.selectbox("ISO Drawing", f_iso_opts, key="il_iso")
    q      = fc5.text_input("🔍 Search", key="il_q", placeholder="ISO, code, item…")

    # ── Build filtered rows ───────────────────────────────────────────────────
    all_rows = build_iso_rows(iso_bom)

    # Candidate ISOs
    if f_sys != "All Systems" and f_area != "All Areas":
        sys_set  = set(sys_map.get(f_sys, []))
        area_set = set(area_map.get(f_area, []))
        iso_set  = sys_set & area_set
    elif f_sys != "All Systems":
        iso_set = set(sys_map.get(f_sys, []))
    elif f_area != "All Areas":
        iso_set = set(area_map.get(f_area, []))
    else:
        iso_set = None

    filtered = []
    for r in all_rows:
        if iso_set is not None and r["ISO Drawing"] not in iso_set: continue
        if f_iso != "All ISOs" and r["ISO Drawing"] != f_iso:       continue
        if f_cat != "All Categories" and r["Category"] != f_cat:    continue
        if q and q.lower() not in (r["ISO Drawing"]+r["Material Code"]+r["Item"]).lower(): continue
        filtered.append(r)

    st.caption(f"Showing **{len(filtered):,}** / {len(all_rows):,} rows")

    # ── Import Excel ─────────────────────────────────────────────────────────
    with st.expander("📂 Import Excel"):
        up = st.file_uploader("Upload ISO List Excel (.xlsx)", type=["xlsx","xls"], key="il_upload")
        if up and st.button("✅ Confirm Import", key="il_import_ok"):
            try:
                df_imp = pd.read_excel(up)
                df_imp.columns = [c.strip() for c in df_imp.columns]
                col_map = {c.lower():c for c in df_imp.columns}
                def gc(k): return col_map.get(k, col_map.get(k.replace(" ","_"), None))
                added = 0
                edits = st.session_state.iso_edits
                for _, row in df_imp.iterrows():
                    iso = str(row.get(gc("iso drawing") or gc("iso"), "")).strip()
                    mc4 = str(row.get(gc("material code") or gc("code"), "")).strip()
                    if not iso or not mc4: continue
                    key = f"{iso}|{mc4}"
                    edits[key] = {
                        "qty":    int(math.ceil(float(row.get(gc("qty"),0) or 0))),
                        "remark": str(row.get(gc("remark"),"") or ""),
                    }
                    added += 1
                st.session_state.iso_edits = edits
                st.success(f"✅ Imported {added} rows.")
            except Exception as e:
                st.error(f"Import failed: {e}")

    # ── Editable table ────────────────────────────────────────────────────────
    if filtered:
        df_edit = pd.DataFrame([{
            "_key":         r["_key"],
            "Area":         r["Area"],
            "ISO Drawing":  r["ISO Drawing"],
            "System":       r["System"],
            "Category":     r["Category"],
            "Material Code":r["Material Code"],
            "Item":         r["Item"],
            "Qty":          r["Qty"],
            "UOM":          r["UOM"],
            "Remark":       r["Remark"],
        } for r in filtered])

        edited = st.data_editor(
            df_edit.drop(columns=["_key"]),
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            disabled=["Area","ISO Drawing","System","Category","Material Code","Item","UOM"],
            column_config={
                "Qty":    st.column_config.NumberColumn(min_value=0, step=1, format="%d"),
                "Remark": st.column_config.TextColumn(width=200),
            },
            key="il_editor",
            height=500,
        )

        # ── Action buttons ────────────────────────────────────────────────────
        bc1,bc2,bc3,bc4 = st.columns([2,2,2,3])

        # Add Row
        if bc1.button("➕ Add Row", key="il_add"):
            st.session_state["il_show_add"] = True

        # Save Changes
        if bc2.button("💾 Save Changes", type="primary", key="il_save"):
            edits = st.session_state.iso_edits
            for i, row in edited.iterrows():
                key = df_edit.iloc[i]["_key"]
                edits[key] = {
                    "qty":    int(math.ceil(float(row["Qty"] or 0))),
                    "remark": str(row["Remark"] or ""),
                }
            st.session_state.iso_edits = edits
            try:
                with open(ISO_EDITS_FILE, "w") as f:
                    json.dump(edits, f)
                st.success("✅ Saved. Summary Design Qty updated.")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.warning(f"Saved to session (file write failed: {e})")

        # Export Excel
        export_df = edited.drop(columns=[], errors="ignore")
        bc3.download_button(
            "⬇ Export Excel",
            data=df_to_excel(export_df, "ISO List"),
            file_name=f"ISO_List_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="il_export",
        )
        bc4.caption(f"{len(edited):,} rows in current view")

        # ── Add Row Modal ──────────────────────────────────────────────────────
        if st.session_state.get("il_show_add"):
            with st.form("il_add_form"):
                st.markdown("**➕ Add New Row**")
                ac1,ac2,ac3,ac4 = st.columns(4)
                n_iso  = ac1.text_input("ISO Drawing*", placeholder="CCP-W-B133-PI-140-ST-411(1OF1)")
                n_area = ac2.text_input("Area",         placeholder="B133")
                n_mc4  = ac3.text_input("Material Code*",placeholder="EL9L-CS05-D040-S80")
                n_cat  = ac4.selectbox("Category", CAT_LIST)
                ac5,ac6,ac7,ac8 = st.columns(4)
                n_item = ac5.text_input("Item",     placeholder="ELBOW LR 90D")
                n_qty  = ac6.number_input("Qty", min_value=0, step=1, value=0)
                n_uom  = ac7.selectbox("UOM", ["EA","M","KG","SET"])
                n_rmk  = ac8.text_input("Remark")
                sub,cancel = st.columns(2)
                if sub.form_submit_button("✅ Add", type="primary"):
                    if n_iso and n_mc4:
                        key = f"{n_iso}|{n_mc4}"
                        st.session_state.iso_edits[key] = {"qty": int(n_qty), "remark": n_rmk}
                        # Also add to iso_bom if new
                        st.session_state["il_show_add"] = False
                        st.success(f"Row added: {n_iso} / {n_mc4}")
                        st.rerun()
                    else:
                        st.error("ISO Drawing and Material Code are required.")
                if cancel.form_submit_button("Cancel"):
                    st.session_state["il_show_add"] = False
                    st.rerun()
    else:
        st.info("No rows match the current filters.")

# ─── MASTER LIST TAB ──────────────────────────────────────────────────────────
def tab_master(mv5):
    st.subheader("📃 Master List")

    tab1, tab2 = st.tabs(["⚙ Piping & Fitting", "🔩 Bolt & Gasket"])

    for tab, data_key in [(tab1,"pf_master"), (tab2,"bg_master")]:
        with tab:
            D  = mv5[data_key]
            sk = data_key[:2]

            fc1,fc2,fc3,fc4 = st.columns([3,2,2,2])
            q    = fc1.text_input("🔍 Search", key=f"mq_{sk}", placeholder="Code, item, spec, size…")
            fcat = fc2.selectbox("Category", ["All Categories"]+CAT_LIST, key=f"mcat_{sk}")
            fi   = fc3.selectbox("Item",
                ["All Items"]+sorted({r.get("ITEM") or r.get("ITEM_CODE","") for r in D}),
                key=f"mfi_{sk}")
            if sk == "pf":
                fm = fc4.selectbox("Material",
                    ["All Materials"]+sorted({r.get("MATL1","") for r in D}),
                    key=f"mfm_{sk}")
            else:
                fm = "All Materials"

            rows = []
            for r in D:
                ic  = r.get("ITEM_CODE","")
                cat = get_cat(ic)
                itm = r.get("ITEM") or r.get("ITEM_CODE","")
                if q  and q.lower() not in json.dumps(r).lower():         continue
                if fcat!="All Categories" and cat  != fcat:               continue
                if fi  !="All Items"      and itm  != fi:                 continue
                if fm  !="All Materials"  and r.get("MATL1","") != fm:    continue
                row = {
                    "Category":     cat,
                    "Material Code":r.get("MATERIAL_CODE",""),
                    "Item":         itm,
                    "Spec":         r.get("MATL1",""),
                    "Size":         r.get("SIZE") or r.get("PIPE SIZE",""),
                    "Rating":       r.get("THICK",""),
                    "End Type":     r.get("END TYPE",""),
                    "UOM":          r.get("UOM",""),
                    "Total Qty":    r.get("TOTAL_QTY",0),
                    "Source":       r.get("SOURCES",""),
                }
                rows.append(row)

            df = pd.DataFrame(rows)
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True,
                    column_config={
                        "Category":     st.column_config.TextColumn(width=80),
                        "Material Code":st.column_config.TextColumn(width=160),
                        "Total Qty":    st.column_config.NumberColumn(format="%.0f"),
                    }, height=520)
                st.caption(f"Showing {len(df):,} / {len(D):,}")
                st.download_button("⬇ Export Excel", data=df_to_excel(df,"Master"),
                    file_name=f"MasterList_{sk}_{date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_master_{sk}")
            else:
                st.info("No records match the filters.")

# ─── RECEIVING TAB ────────────────────────────────────────────────────────────
def tab_receiving():
    st.subheader("📦 Receiving")

    # KPIs
    recs = st.session_state.receiving
    ships = sorted({r.get("SHIPMENT","") for r in recs})
    tot_qty = sum(float(r.get("QTY",0) or 0) for r in recs)
    k1,k2,k3 = st.columns(3)
    k1.metric("Total Records",   f"{len(recs):,}")
    k2.metric("Shipments",       f"{len(ships)}")
    k3.metric("Total Qty",       f"{tot_qty:,.0f}")

    # Import Excel
    with st.expander("📂 Import Excel (Receiving.xlsx)"):
        up = st.file_uploader("Upload Receiving Excel", type=["xlsx","xls"], key="rv_up")
        if up and st.button("✅ Confirm Import", key="rv_imp"):
            try:
                df_raw = pd.read_excel(up)
                df_raw.columns = [str(c).strip() for c in df_raw.columns]
                # Auto-detect header row
                for skip in range(5):
                    df_try = pd.read_excel(up, skiprows=skip)
                    df_try.columns = [str(c).strip() for c in df_try.columns]
                    if any(k in " ".join(df_try.columns).upper() for k in ["ITEM","SHIPMENT","QTY"]):
                        df_raw = df_try; break
                new_recs = []
                for _, row in df_raw.iterrows():
                    r = {
                        "SHIPMENT":     str(row.get("SHIPMENT") or row.get("Shipment","")).strip(),
                        "PACKING_LIST": str(row.get("PACKING_LIST") or row.get("Packing List","")).strip(),
                        "ITEM":         str(row.get("ITEM") or row.get("Item","")).strip(),
                        "QTY":          float(row.get("QTY") or row.get("Q'ty") or row.get("Qty",0) or 0),
                        "UNIT":         str(row.get("UNIT") or row.get("Unit","EA")).strip(),
                        "MAT_CODE":     str(row.get("MAT_CODE","")).strip(),
                        "ITEM_CODE":    str(row.get("ITEM_CODE","")).strip(),
                        "SIZE_INCH":    str(row.get("SIZE_INCH","")).strip(),
                        "SCH_CODE":     str(row.get("SCH_CODE","")).strip(),
                        "REMARK":       str(row.get("REMARK") or row.get("Remark","")).strip(),
                    }
                    if r["ITEM"] and r["ITEM"] != "nan": new_recs.append(r)
                st.session_state.receiving = new_recs
                st.success(f"✅ Imported {len(new_recs):,} records.")
                st.rerun()
            except Exception as e:
                st.error(f"Import failed: {e}")

    # Filters
    fc1,fc2,fc3 = st.columns([2,2,3])
    f_ship = fc1.selectbox("Shipment", ["All Shipments"]+ships, key="rv_ship")
    f_pls  = sorted({r.get("PACKING_LIST","") for r in recs if r.get("PACKING_LIST")})
    f_pl   = fc2.selectbox("Packing List", ["All PL"]+f_pls, key="rv_pl")
    q      = fc3.text_input("🔍 Search", key="rv_q", placeholder="Shipment, code, item…")

    filtered = [r for r in recs
        if (f_ship == "All Shipments" or r.get("SHIPMENT") == f_ship)
        and (f_pl == "All PL" or r.get("PACKING_LIST") == f_pl)
        and (not q or q.lower() in json.dumps(r).lower())]

    df_rv = pd.DataFrame(filtered, columns=[
        "SHIPMENT","PACKING_LIST","ITEM","QTY","UNIT",
        "MAT_CODE","ITEM_CODE","SIZE_INCH","SCH_CODE","REMARK"
    ]) if filtered else pd.DataFrame()

    st.caption(f"Showing {len(filtered):,} / {len(recs):,} records")

    # Editable data editor
    edited_rv = st.data_editor(
        df_rv,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "QTY": st.column_config.NumberColumn(min_value=0, format="%.0f"),
        },
        key="rv_editor",
        height=450,
    )

    bc1,bc2,bc3 = st.columns([2,2,3])

    if bc1.button("💾 Save Changes", type="primary", key="rv_save"):
        # Merge edited back into full list
        # Replace filtered records with edited version
        ship_filter = set(r.get("SHIPMENT") for r in filtered)
        unchanged   = [r for r in recs if r.get("SHIPMENT") not in ship_filter]
        new_recs    = unchanged + edited_rv.to_dict("records")
        st.session_state.receiving = new_recs
        try:
            with open(RECEIVING_FILE, "w") as f:
                json.dump(new_recs, f)
            st.success(f"✅ Saved {len(new_recs):,} records.")
        except Exception as e:
            st.warning(f"Session saved (file: {e})")

    bc2.download_button(
        "⬇ Export Excel",
        data=df_to_excel(edited_rv, "Receiving"),
        file_name=f"Receiving_{date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="rv_export",
    )

    # Add single row form
    with st.expander("➕ Add Single Record"):
        with st.form("rv_add"):
            a1,a2,a3 = st.columns(3)
            n_ship = a1.text_input("Shipment*",    placeholder="PGU-DE-0443")
            n_pl   = a2.text_input("Packing List", placeholder="PGU-DE-0443-BOP-FDR-001")
            n_item = a3.text_input("Item*",        placeholder="FLANGE-A105 / DN 100…")
            b1,b2,b3,b4 = st.columns(4)
            n_qty  = b1.number_input("Qty*", min_value=0.0, step=1.0, value=0.0)
            n_unit = b2.selectbox("Unit", ["EA","M","KG","SET","PC"])
            n_mc   = b3.text_input("Mat Code",  placeholder="FLA-CS05-D040-C150-RF")
            n_rmk  = b4.text_input("Remark")
            if st.form_submit_button("➕ Add", type="primary"):
                if n_ship and n_item:
                    new_r = {
                        "SHIPMENT":n_ship,"PACKING_LIST":n_pl,"ITEM":n_item,
                        "QTY":n_qty,"UNIT":n_unit,"MAT_CODE":n_mc,
                        "ITEM_CODE":"","SIZE_INCH":"","SCH_CODE":"","REMARK":n_rmk
                    }
                    st.session_state.receiving.append(new_r)
                    st.success("Record added.")
                    st.rerun()

# ─── ISSUE TAB ────────────────────────────────────────────────────────────────
def tab_issue(iso_bom: dict, sys_map: dict, area_map: dict, bom_spec: dict, store: dict):
    st.subheader("📤 Material Issue")

    left, right = st.columns([1, 3])

    # ── Left panel: System/Area/ISO selector ─────────────────────────────────
    with left:
        st.markdown("**Select ISO Drawing**")
        sys_opts  = ["All"] + sorted(sys_map.keys(), key=lambda s: (-len(sys_map[s]),s))
        f_sys     = st.selectbox("System",  sys_opts,  key="iss_sys",
            format_func=lambda s: f"{s} — {SYS_NAMES.get(s,s)} ({len(sys_map.get(s,[]))}) " if s!="All" else "All Systems")
        area_opts = ["All"] + sorted(area_map.keys(), key=lambda a:(-len(area_map[a]),a))
        f_area    = st.selectbox("Area",    area_opts, key="iss_area",
            format_func=lambda a: f"Area {a} ({len(area_map.get(a,[]))})" if a!="All" else "All Areas")

        # Candidate ISOs
        if f_sys != "All" and f_area != "All":
            iso_cands = sorted(set(sys_map.get(f_sys,[])) & set(area_map.get(f_area,[])))
        elif f_sys != "All":
            iso_cands = sorted(sys_map.get(f_sys,[]))
        elif f_area != "All":
            iso_cands = sorted(area_map.get(f_area,[]))
        else:
            iso_cands = sorted(iso_bom.keys())

        issued_set = {s["iso"] for s in st.session_state.issue_log}
        iso_q = st.text_input("🔍 Search ISO", key="iss_iso_q", placeholder="Drawing no…")
        if iso_q:
            iso_cands = [i for i in iso_cands if iso_q.lower() in i.lower()]

        st.caption(f"{len(iso_cands):,} ISO drawings")
        iso_opts = [None] + iso_cands
        sel_iso = st.selectbox("ISO Drawing", iso_opts, key="iss_sel_iso",
            format_func=lambda i: "— Select —" if i is None else
                ("✓ " if i in issued_set else "") + re.sub(r"\(\d+OF\d+\)","",i))

    # ── Right panel: BOM table + issue ───────────────────────────────────────
    with right:
        if sel_iso is None:
            st.info("← Select an ISO Drawing to load its BOM.")

            # ── Issue Log ────────────────────────────────────────────────────
            if st.session_state.issue_log:
                st.markdown("---")
                st.markdown("**📋 Issue Log**")
                log_rows = []
                for i, sl in enumerate(reversed(st.session_state.issue_log)):
                    ri = len(st.session_state.issue_log)-1-i
                    log_rows.append({
                        "#": ri+1,
                        "Slip No.":    sl["slip_no"],
                        "Date":        sl["date"],
                        "ISO Drawing": re.sub(r"\(\d+OF\d+\)","",sl.get("iso","")),
                        "Area":        sl.get("area",""),
                        "Items":       len(sl.get("items",[])),
                        "Total Issued":sl.get("total_issued",0),
                        "Req. by":     sl.get("req",""),
                        "Approved":    sl.get("appr",""),
                    })
                df_log = pd.DataFrame(log_rows)
                st.dataframe(df_log, hide_index=True, use_container_width=True)
            return

        p = parse_iso(sel_iso)
        bom_items = iso_bom.get(sel_iso, [])

        # Build BOM rows with rcv/iss/balance
        bom_rows = []
        for mc4, item_name, uom, base_qty in bom_items:
            qty_v, uom_v = mm_to_m(base_qty, uom)
            rv = rcv_for(store, mc4)
            iv = iss_for(store, mc4)
            bal = rv - iv
            spec = bom_spec.get(mc4, {})
            bom_rows.append({
                "_mc4":        mc4,
                "Area":        p["area"],
                "ISO Drawing": re.sub(r"\(\d+OF\d+\)","",sel_iso),
                "Category":    get_cat(mc4.split("-")[0]),
                "Material Code": mc4,
                "Item":        item_name,
                "Spec":        spec.get("matl",""),
                "Size":        spec.get("size",""),
                "Rating":      spec.get("thick",""),
                "End Type":    spec.get("end_type",""),
                "UOM":         uom_v,
                "Design":      float(qty_v),
                "BOM Qty":     float(qty_v),
                "Rcv Qty":     float(rv),
                "Issue Qty":   float(min(qty_v, max(0, bal))),
                "Balance":     float(bal),
            })

        # Slip header
        st.markdown(f"**📤 Material Issue Slip** | ISO: `{re.sub(chr(40)+r'.*'+chr(41),'',sel_iso)}` | Area: {p['area']} | System: {p['sys']}")
        hc1,hc2,hc3,hc4 = st.columns(4)
        slip_date = hc1.date_input("Issue Date", value=date.today(), key="iss_date")
        slip_req  = hc2.text_input("Requested by", key="iss_req", placeholder="Name / Team")
        slip_cont = hc3.text_input("Contractor",   key="iss_cont")
        slip_appr = hc4.text_input("Approved by",  key="iss_appr")
        slip_rmk  = st.text_input("Remarks",       key="iss_rmk", placeholder="Optional")

        # Editable BOM table (Issue Qty column)
        df_bom = pd.DataFrame(bom_rows).drop(columns=["_mc4"])
        edited_bom = st.data_editor(
            df_bom,
            use_container_width=True,
            hide_index=True,
            disabled=[c for c in df_bom.columns if c != "Issue Qty"],
            column_config={
                "Design":     st.column_config.NumberColumn(format="%.0f"),
                "BOM Qty":    st.column_config.NumberColumn(format="%.0f"),
                "Rcv Qty":    st.column_config.NumberColumn(format="%.0f"),
                "Issue Qty":  st.column_config.NumberColumn(min_value=0, step=1, format="%.0f"),
                "Balance":    st.column_config.NumberColumn(format="%.0f"),
            },
            key="iss_bom_ed",
            height=380,
        )

        bc1,bc2,bc3 = st.columns([3,2,2])

        # Save & Print
        if bc1.button("💾 Save & Generate Slip", type="primary", key="iss_save"):
            issue_items = []
            total_iss   = 0
            for i, row in edited_bom.iterrows():
                iq = float(row["Issue Qty"] or 0)
                if iq <= 0: continue
                mc4 = bom_rows[i]["_mc4"]
                rv  = bom_rows[i]["Rcv Qty"]
                if rv <= 0: continue
                iq  = min(iq, rv)
                # FIFO deductions
                deductions = {}
                remaining  = iq
                matches = sorted(
                    [r for r in st.session_state.receiving
                     if r["MAT_CODE"]==mc4 or r["MAT_CODE"].startswith(mc4+"-")],
                    key=lambda r: r.get("SHIPMENT","")
                )
                for rec in matches:
                    if remaining <= 0: break
                    mc5   = rec["MAT_CODE"]
                    avail = max(0, store.get(mc5,{}).get("r",0) - store.get(mc5,{}).get("i",0))
                    take  = min(remaining, avail)
                    if take > 0:
                        deductions[mc5] = deductions.get(mc5,0) + take
                        remaining -= take
                issue_items.append({
                    "mc4":        mc4,
                    "item":       row["Item"],
                    "spec":       row["Spec"],
                    "size":       row["Size"],
                    "rating":     row["Rating"],
                    "end_type":   row["End Type"],
                    "uom":        row["UOM"],
                    "bom_qty":    row["BOM Qty"],
                    "rcv_qty":    rv,
                    "iss_qty":    iq,
                    "deductions": deductions,
                    "packing_lists": [
                        r.get("PACKING_LIST","") for r in matches
                        if r["MAT_CODE"] in deductions
                    ],
                })
                total_iss += iq

            if not issue_items:
                st.warning("No items with Issue Qty > 0 and received qty.")
            else:
                slip_no = f"MIS-{st.session_state.issue_next_no:03d}"
                slip = {
                    "slip_no":     slip_no,
                    "date":        str(slip_date),
                    "iso":         sel_iso,
                    "area":        p["area"],
                    "sys":         p["sys"],
                    "line":        p["line"],
                    "req":         slip_req,
                    "cont":        slip_cont,
                    "appr":        slip_appr,
                    "rmk":         slip_rmk,
                    "items":       issue_items,
                    "total_issued":total_iss,
                    "saved_at":    datetime.now().isoformat(),
                }
                st.session_state.issue_log.append(slip)
                st.session_state.issue_next_no += 1
                try:
                    with open(ISSUE_LOG_FILE, "w") as f:
                        json.dump(st.session_state.issue_log, f)
                except Exception:
                    pass
                st.success(f"✅ {slip_no} saved. {len(issue_items)} items, total {total_iss:.0f} issued.")

                # Generate printable HTML slip
                slip_html = build_slip_html(slip, bom_rows)
                bc2.download_button(
                    "🖨 Download Slip",
                    data=slip_html,
                    file_name=f"{slip_no}_{date.today()}.html",
                    mime="text/html",
                    key="iss_dl",
                )

        # Export BOM
        bc3.download_button(
            "⬇ Export BOM",
            data=df_to_excel(edited_bom, "BOM"),
            file_name=f"BOM_{re.sub(r'[^a-zA-Z0-9]','_',sel_iso)}_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="iss_bom_xl",
        )

        # Issue Log at bottom
        if st.session_state.issue_log:
            with st.expander(f"📋 Issue Log ({len(st.session_state.issue_log)} slips)"):
                log_rows = []
                for i, sl in enumerate(reversed(st.session_state.issue_log)):
                    log_rows.append({
                        "Slip No.":    sl["slip_no"],
                        "Date":        sl["date"],
                        "ISO":         re.sub(r"\(\d+OF\d+\)","",sl.get("iso","")),
                        "Area":        sl.get("area",""),
                        "Items":       len(sl.get("items",[])),
                        "Total Issued":sl.get("total_issued",0),
                        "Req. by":     sl.get("req",""),
                        "Approved":    sl.get("appr",""),
                    })
                st.dataframe(pd.DataFrame(log_rows), hide_index=True, use_container_width=True)


# ─── ISSUE SLIP HTML GENERATOR ────────────────────────────────────────────────
def build_slip_html(slip: dict, bom_rows: list) -> str:
    iso_short = re.sub(r"\(\d+OF\d+\)","",slip.get("iso",""))
    rows_html = ""
    bom_by_mc4 = {r["_mc4"]: r for r in bom_rows}
    for i, it in enumerate(slip.get("items",[])):
        pls = list({p for p in it.get("packing_lists",[]) if p})
        pl_text = "<br>".join(pls) if pls else "—"
        rows_html += f"""<tr>
          <td style="text-align:center">{i+1}</td>
          <td style="font-family:monospace;font-size:8pt">{it['mc4']}</td>
          <td>{it['item']}</td>
          <td>{it['spec']}</td>
          <td style="text-align:center">{it['size']}</td>
          <td style="text-align:center">{it['rating']}</td>
          <td style="text-align:center">{it['end_type']}</td>
          <td style="text-align:center">{it['uom']}</td>
          <td style="text-align:right;font-weight:700">{it['bom_qty']:.0f}</td>
          <td style="text-align:right;font-weight:700">{it['rcv_qty']:.0f}</td>
          <td style="text-align:right;font-weight:800;color:#0a6641">{it['iss_qty']:.0f}</td>
          <td style="font-size:8pt;color:#555">{pl_text}</td>
        </tr>"""
    total_iss = slip.get("total_issued",0)
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>Material Issue Slip {slip['slip_no']}</title>
<style>
  body{{font-family:Arial,sans-serif;font-size:10pt;margin:20px;}}
  table{{width:100%;border-collapse:collapse;}}
  th,td{{border:1px solid #ccc;padding:4px 7px;}}
  thead tr{{background:#1a2332;color:#fff;font-size:8pt;}}
  tfoot tr{{background:#f0f4f8;font-weight:800;}}
  .info-table td{{border:1px solid #d1dce8;}}
  .info-table .lbl{{background:#f5f7fa;font-size:8pt;font-weight:700;color:#666;width:14%;}}
  @media print{{@page{{size:A4 landscape;margin:15mm;}}}}
</style>
</head><body>
<div style="display:flex;justify-content:space-between;border-bottom:2.5px solid #1a2332;padding-bottom:10px;margin-bottom:12px;">
  <div>
    <div style="font-size:16pt;font-weight:900;color:#1a2332">MATERIAL ISSUE SLIP</div>
    <div style="font-size:9pt;color:#666">EPC Project · Piping Material Management · FIFO Basis</div>
  </div>
  <div style="text-align:right">
    <div style="font-size:8pt;color:#666;font-weight:700">ISO DRAWING NO.</div>
    <div style="font-family:monospace;font-size:12pt;font-weight:900;color:#1e6ee8">{iso_short}</div>
  </div>
</div>
<table class="info-table" style="margin-bottom:10px">
  <tr>
    <td class="lbl">SLIP NO.</td>
    <td style="font-weight:800;color:#1e6ee8;width:19%">{slip['slip_no']}</td>
    <td class="lbl">DATE</td>
    <td style="width:19%">{slip['date']}</td>
    <td class="lbl">AREA</td>
    <td>{slip.get('area','—')}</td>
  </tr>
  <tr>
    <td class="lbl">LINE NO.</td>
    <td>{slip.get('line','—')}</td>
    <td class="lbl">REQUESTED BY</td>
    <td>{slip.get('req','—')}</td>
    <td class="lbl">CONTRACTOR</td>
    <td>{slip.get('cont','—')}</td>
  </tr>
  <tr>
    <td class="lbl">APPROVED BY</td>
    <td colspan="5">{slip.get('appr','—')}&nbsp;
      {'<span style="color:#888;font-size:8pt">Remarks: '+slip['rmk']+'</span>' if slip.get('rmk') else ''}
    </td>
  </tr>
</table>
<table>
  <thead><tr>
    <th style="width:22px">#</th>
    <th>Material Code</th><th>Item</th><th>Spec</th>
    <th>Size</th><th>Rating</th><th>End Type</th><th>UOM</th>
    <th>BOM Qty</th><th>Rcv Qty</th>
    <th style="background:#0a6641">Issue Qty</th>
    <th style="background:#1a3a1a">Received Packing List (FIFO)</th>
  </tr></thead>
  <tbody>{rows_html}</tbody>
  <tfoot><tr>
    <td colspan="10" style="text-align:right;font-size:9pt">TOTAL ISSUE QTY</td>
    <td style="text-align:right;font-size:11pt;color:#0a6641">{total_iss:.0f}</td>
    <td></td>
  </tr></tfoot>
</table>
<table style="margin-top:28px">
  <tr>
    {''.join(f'<td style="padding:8px;text-align:center;width:25%"><div style="font-size:8pt;color:#777;margin-bottom:28px">{lbl}</div><div style="border-top:1px solid #555;padding-top:4px;font-size:8pt;color:#aaa">Signature / Date</div></td>'
      for lbl in ['Issued by (Storekeeper)', f"Requested by · {slip.get('req','')}", 'Checked by', f"Approved by · {slip.get('appr','')}"])}
  </tr>
</table>
<div style="text-align:right;font-size:7pt;color:#bbb;margin-top:8px">
  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} · EPC Piping Material Master · FIFO Basis
</div>
<script>window.onload=function(){{window.print();}}</script>
</body></html>"""

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    mv5       = load_master()
    iso_bom   = load_iso_bom()
    bom_spec  = build_bom_spec(json.dumps(mv5))
    sys_map, area_map = build_iso_maps(json.dumps(iso_bom))

    init_session()
    store = build_store()

    # Header
    st.markdown("""
    <div style="display:flex;align-items:center;gap:14px;padding:14px 0 10px;border-bottom:1px solid #334155;margin-bottom:16px">
      <span style="font-size:28px">🔧</span>
      <div>
        <div style="font-size:18px;font-weight:900;color:#f1f5f9;letter-spacing:.5px">EPC PIPING MATERIAL MASTER</div>
        <div style="font-size:11px;color:#64748b">EPC Project · Integrated Material Management System</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Tabs
    t1, t2, t3, t4, t5 = st.tabs([
        "📊 SUMMARY",
        "📋 ISO LIST",
        "📃 MASTER LIST",
        "📦 RECEIVING",
        "📤 ISSUE",
    ])

    with t1: tab_summary(mv5, store)
    with t2: tab_iso_list(iso_bom, sys_map, area_map)
    with t3: tab_master(mv5)
    with t4: tab_receiving()
    with t5: tab_issue(iso_bom, sys_map, area_map, bom_spec, store)


if __name__ == "__main__":
    main()
