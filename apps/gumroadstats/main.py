"""Gumroad dashboard — PyScript (in-browser) port of dashboard/data.py + views.py.

Runs entirely in Pyodide: no Flask, no server session. State lives in
module globals; file upload is read via the browser File API.
"""
import asyncio
import io

import js
import pandas as pd
import plotly.express as px
import plotly.io as pio
from pyscript import document

MONEY_COLS = ["Subtotal ($)", "Taxes ($)", "Shipping ($)", "Sale Price ($)",
              "Fees ($)", "Net Total ($)"]
DATE_COL = "Purchase Date"
DATETIME_COL = "Purchase Time (UTC timezone)"
EXTRA_COLS = ["Rating", "Review", "Discount Code", "Affiliate",
              "UTM Source", "Tip ($)", "Partial Refund ($)"]
SHOW_COLS = ["Purchase ID", "Purchase Date", "Purchase Time (UTC timezone)",
             "Item Name", "Country", "Referrer", "Payment Type",
             "Sale Price ($)", "Fees ($)", "Taxes ($)", "Net Total ($)",
             "Discover?", "Refunded?"]

BASE = pd.DataFrame()
INFO = {"excluded_totals_rows": 0, "source": "…"}
IS_DEFAULT = True
LAST_FILTERED = pd.DataFrame()

CHART_IDS = ["chart-trend", "chart-prod-units", "chart-prod-net",
             "chart-geo-units", "chart-geo-net", "chart-geo-map",
             "chart-ref-bar", "chart-ref-pie", "chart-discover",
             "chart-pay-pie", "chart-pay-bar", "chart-tax",
             "chart-heat", "chart-weekday"]


# ---------- data logic (ported from dashboard/data.py) ----------
def clean_sales(df: pd.DataFrame, source_label: str) -> tuple:
    info = {"excluded_totals_rows": 0, "source": source_label}
    n_before = len(df)
    if "Purchase ID" in df.columns:
        totals_mask = df["Purchase ID"].astype(str).str.strip().str.lower() == "totals"
        info["excluded_totals_rows"] = int(totals_mask.sum())
        df = df.loc[~totals_mask].copy()
    if len(df) and ("Item Name" in df.columns and DATE_COL in df.columns):
        last = df.iloc[-1]
        if str(last.get("Item Name", "")).strip() == "" and str(
                last.get(DATE_COL, "")).strip() == "":
            df = df.iloc[:-1].copy()
            info["excluded_totals_rows"] = max(info["excluded_totals_rows"], 1)
    info["rows_dropped_total"] = n_before - len(df)
    for c in MONEY_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    if DATE_COL in df.columns:
        df["_date"] = pd.to_datetime(df[DATE_COL], errors="coerce")
    if DATETIME_COL in df.columns:
        df["_datetime"] = pd.to_datetime(df[DATETIME_COL], utc=True, errors="coerce")
    else:
        df["_datetime"] = df.get("_date")
    df = df.dropna(subset=["_date"]).copy()
    if "Quantity" in df.columns:
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(1)
    return df, info


def options(df: pd.DataFrame, col: str) -> list:
    if col not in df.columns:
        return []
    return sorted(df[col].dropna().astype(str).unique().tolist())


def non_empty_count(df: pd.DataFrame, col: str) -> int:
    if col not in df.columns:
        return 0
    s = df[col].astype(str).str.strip().str.lower()
    return int(((s != "") & (s != "0") & (s != "nan")).sum())


def search_mask(f: pd.DataFrame, q: str):
    mask = pd.Series(False, index=f.index)
    for c in ["Purchase ID", "Purchase Email", "Item Name", "Country", "Referrer"]:
        if c in f.columns:
            mask |= f[c].astype(str).str.lower().str.contains(q.lower(), na=False)
    return mask


def apply_filters(base: pd.DataFrame, fs: dict) -> pd.DataFrame:
    f = base.copy()
    if fs["start"]:
        f = f[f["_date"].dt.date.astype(str) >= fs["start"]]
    if fs["end"]:
        f = f[f["_date"].dt.date.astype(str) <= fs["end"]]
    for key, col in [("items", "Item Name"), ("countries", "Country"),
                     ("referrers", "Referrer"), ("payments", "Payment Type")]:
        if fs[key] and col in f.columns:
            f = f[f[col].astype(str).isin(fs[key])]
    if fs["discover_only"] and "Discover?" in f.columns:
        f = f[pd.to_numeric(f["Discover?"], errors="coerce").fillna(0).astype(int) == 1]
    if fs["exclude_refunded"]:
        for c in ["Refunded?", "Fully Refunded?", "Disputed?"]:
            if c in f.columns:
                f = f[pd.to_numeric(f[c], errors="coerce").fillna(0).astype(int) == 0]
    return f


# ---------- DOM helpers ----------
def el(id_: str):
    return document.querySelector("#" + id_)


def alert(msg: str, kind: str = "info"):
    el("alertBox").innerHTML = (
        f"<div class='alert alert-{kind} alert-dismissible fade show' role='alert'>"
        f"{msg}<button type='button' class='btn-close' data-bs-dismiss='alert'></button></div>")


def set_status(text: str):
    el("loadStatus").textContent = text


def get_selected(id_: str) -> list:
    sel = el(id_)
    out = []
    # Indexed access: iterating a JsProxy options collection directly is unreliable.
    for i in range(int(sel.options.length)):
        o = sel.options.item(i)
        if o.selected:
            out.append(o.value)
    return out


def set_options(id_: str, values: list, selected: list | None = None):
    sel = None if selected is None else set(selected)
    html = "".join(
        f"<option value='{v}'{' selected' if (sel is None or v in sel) else ''}>{v}</option>"
        for v in values)
    el(id_).innerHTML = html


def to_table(df: pd.DataFrame, limit: int = 500) -> str:
    return df.head(limit).to_html(
        classes="table table-striped table-hover table-sm mb-0",
        index=False, border=0, justify="left")


def show_fig(fig, div_id: str):
    """Render a plotly Figure via the global Plotly.js (innerHTML scripts don't run)."""
    node = el(div_id)
    if fig is None:
        js.Plotly.purge(node)
        node.innerHTML = ""
        return
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=380)
    obj = js.JSON.parse(pio.to_json(fig))
    js.Plotly.react(node, obj.data, obj.layout)


def clear_charts():
    for cid in CHART_IDS:
        try:
            js.Plotly.purge(el(cid))
        except Exception:
            pass
        el(cid).innerHTML = ""


# ---------- filter state ----------
def read_filters() -> dict:
    return {
        "start": el("f-start").value,
        "end": el("f-end").value,
        "items": get_selected("f-items"),
        "countries": get_selected("f-countries"),
        "referrers": get_selected("f-referrers"),
        "payments": get_selected("f-payments"),
        "grain": el("f-grain").value or "Daily",
        "metric": el("f-metric").value or "Net Total ($)",
        "stacked": bool(el("f-stacked").checked),
        "discover_only": bool(el("f-discover").checked),
        "exclude_refunded": bool(el("f-exref").checked),
        "q": el("f-q").value.strip(),
    }


def populate_filter_defaults():
    """Fill selects + date range from BASE (all selected, full range)."""
    if BASE.empty:
        return
    min_d = BASE["_date"].min().date().isoformat()
    max_d = BASE["_date"].max().date().isoformat()
    for id_, attr in [("f-start", "min"), ("f-end", "min")]:
        el(id_).setAttribute("min", min_d)
    for id_, attr in [("f-start", "max"), ("f-end", "max")]:
        el(id_).setAttribute("max", max_d)
    el("f-start").value = min_d
    el("f-end").value = max_d
    set_options("f-items", options(BASE, "Item Name"))
    set_options("f-countries", options(BASE, "Country"))
    set_options("f-referrers", options(BASE, "Referrer"))
    set_options("f-payments", options(BASE, "Payment Type"))


def update_source_ui():
    el("navSource").textContent = INFO.get("source", "")
    badge = el("sourceBadge")
    badge.textContent = INFO.get("source", "")
    badge.className = "badge " + ("bg-success" if IS_DEFAULT else "bg-primary")
    el("sourceMeta").textContent = (
        f"{len(BASE)} sales rows ({INFO.get('excluded_totals_rows', 0)} totals row(s) excluded)")


# ---------- main render (ported from build_dashboard) ----------
def render(*_args):
    global LAST_FILTERED
    if BASE.empty:
        el("emptyWarn").style.display = "block"
        return
    fs = read_filters()
    f = apply_filters(BASE, fs)
    metric = fs["metric"] if fs["metric"] in f.columns else "Net Total ($)"
    clear_charts()
    for tid in ["tbl-trend", "tbl-products", "tbl-geo", "tbl-referrers",
                "tbl-discover", "tbl-transactions"]:
        el(tid).innerHTML = ""
    el("extrasBox").innerHTML = ""
    el("discoverWrap").style.display = "none"

    if f.empty:
        el("emptyWarn").style.display = "block"
        for k in ["kpi-net", "kpi-gross", "kpi-units", "kpi-aov", "kpi-buyers", "kpi-fees"]:
            el(k).textContent = "–"
        LAST_FILTERED = f
        return
    el("emptyWarn").style.display = "none"

    gross = float(f["Sale Price ($)"].sum()) if "Sale Price ($)" in f.columns else 0.0
    net = float(f["Net Total ($)"].sum()) if "Net Total ($)" in f.columns else 0.0
    units = len(f)
    el("kpi-net").textContent = f"${net:.2f}"
    el("kpi-gross").textContent = f"${gross:.2f}"
    el("kpi-units").textContent = str(units)
    el("kpi-aov").textContent = f"${net / units:.2f}" if units else "–"
    el("kpi-buyers").textContent = str(
        f["Purchase Email"].nunique() if "Purchase Email" in f.columns else units)
    fees = float(f["Fees ($)"].sum()) if "Fees ($)" in f.columns else 0.0
    taxes = float(f["Taxes ($)"].sum()) if "Taxes ($)" in f.columns else 0.0
    el("kpi-fees").textContent = f"${fees:.2f} / ${taxes:.2f}"
    el("paySummary").textContent = (
        f"Gross: ${gross:.2f} · Fees: ${fees:.2f} · Taxes: ${taxes:.2f} · Net: ${net:.2f}")

    # Trend
    g = f.copy()
    g["_period"] = (g["_date"].dt.to_period("M").dt.to_timestamp()
                    if fs["grain"] == "Monthly" else g["_date"].dt.floor("D"))
    if fs["stacked"] and "Item Name" in g.columns:
        agg = g.groupby(["_period", "Item Name"], as_index=False)[metric].sum()
        show_fig(px.bar(agg, x="_period", y=metric, color="Item Name",
                        title=f"{metric} per {'month' if fs['grain'] == 'Monthly' else 'day'}"),
                 "chart-trend")
    else:
        agg = g.groupby("_period", as_index=False)[metric].sum()
        show_fig(px.bar(agg, x="_period", y=metric,
                        title=f"{metric} per {'month' if fs['grain'] == 'Monthly' else 'day'}"),
                 "chart-trend")
    el("tbl-trend").innerHTML = to_table(agg.sort_values("_period"))

    # Products
    if "Item Name" in f.columns:
        lb = f.groupby("Item Name").agg(
            units=("Item Name", "size"),
            gross=("Sale Price ($)", "sum"),
            net=("Net Total ($)", "sum"),
        ).reset_index().sort_values("net", ascending=False)
        lb["share_net_%"] = round(lb["net"] / lb["net"].sum() * 100, 1) if lb["net"].sum() else 0
        show_fig(px.bar(lb, x="Item Name", y="units", title="Units by ebook"), "chart-prod-units")
        show_fig(px.bar(lb, x="Item Name", y="net", title="Net revenue by ebook"), "chart-prod-net")
        el("tbl-products").innerHTML = to_table(lb)

    # Geography
    if "Country" in f.columns:
        geo = f.groupby("Country").agg(units=("Country", "size"),
                                       net=("Net Total ($)", "sum")
                                       ).reset_index().sort_values("net", ascending=False)
        show_fig(px.bar(geo.head(15), x="Country", y="units",
                        title="Top countries by units"), "chart-geo-units")
        show_fig(px.bar(geo.head(15), x="Country", y="net",
                        title="Top countries by net revenue"), "chart-geo-net")
        try:
            m = px.choropleth(geo, locations="Country", locationmode="country names",
                              color="net", title="Net revenue by country")
            m.update_layout(height=420)
            show_fig(m, "chart-geo-map")
        except Exception as e:
            el("chart-geo-map").innerHTML = (
                f"<div class='alert alert-warning'>Map unavailable: {e}</div>")
        el("tbl-geo").innerHTML = to_table(geo)

    # Acquisition
    if "Referrer" in f.columns:
        ref = f.groupby("Referrer").agg(units=("Referrer", "size"),
                                        net=("Net Total ($)", "sum")
                                        ).reset_index().sort_values("units", ascending=False)
        show_fig(px.bar(ref, x="Referrer", y="units", title="Sales by referrer"), "chart-ref-bar")
        show_fig(px.pie(ref, names="Referrer", values="units",
                        title="Share of sales by referrer"), "chart-ref-pie")
        el("tbl-referrers").innerHTML = to_table(ref)
    if "Discover?" in f.columns:
        d = pd.to_numeric(f["Discover?"], errors="coerce").fillna(0).astype(int)
        agg_d = pd.DataFrame({
            "Channel": d.map({1: "Discover", 0: "Other"}).values,
            "net": f["Net Total ($)"].values if "Net Total ($)" in f.columns else 1,
        }).groupby("Channel").agg(units=("Channel", "size"), net=("net", "sum")).reset_index()
        el("discoverWrap").style.display = "block"
        show_fig(px.pie(agg_d, names="Channel", values="units",
                        title="Discover vs other channels"), "chart-discover")
        el("tbl-discover").innerHTML = to_table(agg_d)

    # Payments
    if "Payment Type" in f.columns:
        pay = f.groupby("Payment Type").agg(units=("Payment Type", "size"),
                                            net=("Net Total ($)", "sum")).reset_index()
        show_fig(px.pie(pay, names="Payment Type", values="units",
                        title="Sales by payment type"), "chart-pay-pie")
        show_fig(px.bar(pay, x="Payment Type", y="net",
                        title="Net revenue by payment type"), "chart-pay-bar")
    if "Tax Type" in f.columns:
        tt = f["Tax Type"].fillna("").replace("", "No tax").value_counts().reset_index()
        tt.columns = ["Tax Type", "units"]
        show_fig(px.bar(tt, x="Tax Type", y="units", title="Sales by tax type"), "chart-tax")

    # Timing
    t = f.dropna(subset=["_datetime"]).copy()
    if not t.empty:
        t["_weekday"] = t["_datetime"].dt.day_name()
        t["_hour"] = t["_datetime"].dt.hour
        order = ["Monday", "Tuesday", "Wednesday", "Thursday",
                 "Friday", "Saturday", "Sunday"]
        piv = t.pivot_table(index="_weekday", columns="_hour", values="Purchase ID",
                            aggfunc="count", fill_value=0).reindex(order)
        heat = px.imshow(piv, labels=dict(x="Hour (UTC)", y="Weekday", color="Sales"),
                         title="Sales heatmap: weekday × hour (UTC)")
        heat.update_layout(height=380)
        show_fig(heat, "chart-heat")
        wd = t["_weekday"].value_counts().reindex(order).reset_index()
        wd.columns = ["Weekday", "units"]
        show_fig(px.bar(wd, x="Weekday", y="units", title="Sales by weekday"), "chart-weekday")

    # Transactions (+ search)
    cols = [c for c in SHOW_COLS if c in f.columns]
    out = f[cols] if cols else f
    if fs["q"]:
        out = out.loc[search_mask(f, fs["q"])]
    el("txCount").textContent = str(len(out))
    el("tbl-transactions").innerHTML = to_table(out)
    LAST_FILTERED = out

    # Extras
    extras_html = ""
    for col in EXTRA_COLS:
        n = non_empty_count(f, col)
        if n > 0:
            extras_html += (
                f"<h6>{col} — {n} non-empty values</h6>"
                f"<div class='table-responsive mb-3'>"
                f"{to_table(f[col].value_counts().head(20).reset_index(), 20)}</div>")
    if extras_html:
        el("extrasBox").innerHTML = (
            "<div class='card mb-3'><div class='card-header fw-bold'>"
            "Additional fields in this file</div><div class='card-body'>"
            + extras_html + "</div></div>")


def reset_filters(*_args):
    populate_filter_defaults()
    el("f-grain").value = "Daily"
    el("f-metric").value = "Net Total ($)"
    el("f-stacked").checked = True
    el("f-discover").checked = False
    el("f-exref").checked = True
    el("f-q").value = ""
    render()


async def load_upload(*_args):
    global BASE, INFO, IS_DEFAULT
    js.console.log("load_upload: started")
    files = el("csvFile").files
    js.console.log(f"load_upload: files.length={files.length if files else 'no-files-obj'}")
    if not files or files.length == 0:
        alert("No file selected.", "warning")
        return
    set_status("Reading uploaded CSV…")
    jsfile = files.item(0)
    name = jsfile.name
    alert(f"Reading {name}…", "info")
    if not name.lower().endswith(".csv"):
        alert("Please choose a .csv file.", "danger")
        return
    try:
        buf = await jsfile.arrayBuffer()
        # ArrayBuffer -> Uint8Array -> Python bytes (buf.to_py() alone is unreliable)
        raw = js.Uint8Array.new(buf).to_py().tobytes()
        df = pd.read_csv(io.BytesIO(raw))
        BASE, INFO = clean_sales(df, name)
        IS_DEFAULT = False
        update_source_ui()
        populate_filter_defaults()
        reset_scalars()
        render()
        alert(f"Loaded {name}. Totals row excluded.", "success")
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            js.console.error(f"CSV load failed: {e}")
        except Exception:
            pass
        alert(f"Could not parse CSV: {e}", "danger")
    finally:
        set_status("Ready.")


def reset_scalars():
    el("f-grain").value = "Daily"
    el("f-metric").value = "Net Total ($)"
    el("f-stacked").checked = True
    el("f-discover").checked = False
    el("f-exref").checked = True
    el("f-q").value = ""


async def load_default(*_args):
    global BASE, INFO, IS_DEFAULT
    set_status("Loading default sales.csv…")
    try:
        # [[fetch]] in pyscript.toml places sales.csv in the WASM FS;
        # fall back to HTTP for local dev without fetch support.
        try:
            df = pd.read_csv("sales.csv")
            src = "sales.csv"
        except Exception:
            from pyodide.http import open_url
            df = pd.read_csv(open_url("./sales.csv"))
            src = "sales.csv"
        BASE, INFO = clean_sales(df, src)
        IS_DEFAULT = True
        el("csvFile").value = ""
        update_source_ui()
        populate_filter_defaults()
        reset_scalars()
        render()
        set_status("Ready.")
    except Exception as e:
        set_status("Failed to load sales.csv.")
        alert(f"Default sales.csv not found: {e}", "warning")


def download(*_args):
    if LAST_FILTERED.empty:
        alert("Nothing to download with current filters.", "warning")
        return
    js.window.downloadCSV(LAST_FILTERED.to_csv(index=False), "gumroad_filtered.csv")


async def boot():
    set_status("Waiting for pandas/plotly… (imports done, loading data)")
    await load_default()
    try:
        document.querySelector("#loader").style.display = "none"
    except Exception:
        pass


_BUSY = False


async def on_upload(event=None):
    """PyScript-native click entry point (see py-click in index.html).

    PyScript awaits async py-click handlers directly, unlike
    addEventListener where a returned coroutine is silently dropped.
    """
    global _BUSY
    if _BUSY:
        return
    _BUSY = True
    try:
        await load_upload()
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            js.console.error(f"upload handler failed: {e}")
        except Exception:
            pass
        alert(f"Upload failed: {e}", "danger")
    finally:
        _BUSY = False


async def on_default(event=None):
    global _BUSY
    if _BUSY:
        return
    _BUSY = True
    try:
        await load_default()
    except Exception as e:
        alert(f"Failed: {e}", "danger")
    finally:
        _BUSY = False


def on_apply(event=None):
    js.console.log(f"apply: {len(get_selected('f-items'))} items, "
                   f"{el('f-start').value}..{el('f-end').value}")
    render()


def on_reset(event=None):
    reset_filters()


def on_download(event=None):
    download()


# NOTE: all buttons are wired via py-click attributes in index.html
# (on_apply/on_reset/on_download/on_upload/on_default). Manual
# addEventListener with throwaway lambdas is avoided: the lambda's proxy
# can be garbage-collected, silently killing the listener.

asyncio.ensure_future(boot())
