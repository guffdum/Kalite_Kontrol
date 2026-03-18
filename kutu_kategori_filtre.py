import pandas as pd
import json
import os

# ============================================================
#  CONFIGURE YOUR FILES HERE
#  Add or remove filenames from this list
#  Only files listed here will be read and shown in the HTML.
# ============================================================
DATA_FILES = [
    "AHT.xlsx",
    "AST.xlsx",
    "AT.xlsx",
    "BBT.xlsx",
    "C.xlsx",
    "EK.xlsx",
    "EST.xlsx",
    "HK.xlsx",
    "HT.xlsx",
    "HUN.xlsx",
    "JL.xlsx",
    "JS.xlsx",
    "KMN.xlsx",
    "LYL.xlsx",
    "MEST.xlsx",
    "MESTKAL.xlsx",
    "ML.xlsx",
    "MT.xlsx",
    "NS.xlsx",
    "NT.xlsx",
    "OCT.xlsx",
    "PS.xlsx",
    "PST.xlsx",
    "SC.xlsx",
    "SKA.xlsx",
    "SKR.xlsx",
    "SKT.xlsx",
    "STD.xlsx",
    "SUBAR.xlsx",
    "TK.xlsx",
    "TSY.xlsx",
    "YCK.xlsx",
    "YHT.xlsx",
    "YKS.xlsx",
    "YST.xlsx",
    "YT.xlsx",
]
# ============================================================

def find_header_and_data_rows(df):
    for i, row in df.iterrows():
        row_vals = [str(v).strip() for v in row.tolist()]
        if 'Kutu' in row_vals and 'Kategori' in row_vals:
            kutu_col = row_vals.index('Kutu')
            kat_col  = row_vals.index('Kategori')
            data_rows = []
            for j in range(i + 1, len(df)):
                data_row = [str(v).strip() if str(v).strip() not in ('nan', 'NaN') else '' for v in df.iloc[j].tolist()]
                kutu_val = data_row[kutu_col]
                # Normalize: treat "-" as "Kutusuz" so the Kutusuz button matches it
                if kutu_val == '-':
                    data_row[kutu_col] = 'Kutusuz'
                if kutu_val != '':
                    data_rows.append(data_row)
            return row_vals, kutu_col, kat_col, data_rows
    return None, None, None, []

def build_data():
    kutular     = pd.read_excel('Kutular.xlsx').iloc[:, 0].dropna().tolist()
    kategoriler = pd.read_excel('Kategoriler.xlsx').iloc[:, 0].dropna().tolist()

    file_data = {}
    for fname in DATA_FILES:
        if not os.path.exists(fname):
            print('  WARNING: {} not found, skipping.'.format(fname))
            continue
        df = pd.read_excel(fname, header=None)
        headers, kutu_col, kat_col, data_rows = find_header_and_data_rows(df)
        if headers is None:
            print('  SKIPPED: {} — no Kutu/Kategori columns found. Check that the header row contains both "Kutu" and "Kategori".'.format(fname))
            continue
        file_data[fname.replace('.xlsx', '')] = {
            'headers':  headers,
            'kutu_col': kutu_col,
            'kat_col':  kat_col,
            'rows':     data_rows,
        }
        print('  OK: {} - {} row(s)'.format(fname, len(data_rows)))

    return {'kutular': kutular, 'kategoriler': kategoriler, 'file_data': file_data}

def write_html(data):
    data_json = json.dumps(data, ensure_ascii=False, default=str)
    # Escape forward slashes to prevent </script> in cell values from breaking the HTML
    data_json = data_json.replace("<", "\u003c").replace(">", "\u003e").replace("&", "\u0026")

    html = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kutu Filtre Goruntüleyici</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: "Segoe UI", Arial, sans-serif; background: #faf4f0; color: #2e1a0e; }
  header { background: linear-gradient(135deg, #7a3418, #a04720); color: white; padding: 20px 30px; box-shadow: 0 2px 8px rgba(122,52,24,0.35); }
  header h1 { font-size: 1.6rem; font-weight: 600; }
  header p  { font-size: 0.85rem; opacity: 0.8; margin-top: 4px; }
  .container { max-width: 1300px; margin: 0 auto; padding: 24px 16px; }
  .filters { display: flex; flex-direction: column; gap: 18px; margin-bottom: 28px; }
  .filter-row { background: white; border-radius: 10px; padding: 16px 20px; box-shadow: 0 1px 5px rgba(160,71,32,0.1); }
  .filter-label { font-size: 0.75rem; font-weight: 700; color: #a04720; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 10px; }
  .btn-group { display: flex; flex-wrap: wrap; gap: 8px; }
  .kutu-btn { padding: 8px 18px; border: 2px solid #d25e28; background: white; color: #d25e28; border-radius: 20px; font-size: 0.9rem; font-weight: 600; cursor: pointer; transition: all 0.18s; }
  .kutu-btn:hover { background: #f5e6de; }
  .kutu-btn.active { background: #d25e28; color: white; }
  .kat-btn { padding: 8px 18px; border: 2px solid #7a3418; background: white; color: #7a3418; border-radius: 20px; font-size: 0.9rem; font-weight: 600; cursor: pointer; transition: all 0.18s; text-transform: capitalize; }
  .kat-btn:hover { background: #f5e6de; }
  .kat-btn.active { background: #7a3418; color: white; }
  .section-title { font-size: 1.1rem; font-weight: 700; color: #7a3418; margin-bottom: 14px; padding-bottom: 6px; border-bottom: 2px solid #f0d0be; }
  .no-result { text-align: center; padding: 40px; color: #b07050; font-size: 1rem; }
  .file-block { background: white; border-radius: 10px; box-shadow: 0 1px 6px rgba(160,71,32,0.12); margin-bottom: 20px; overflow: hidden; }
  .file-header { background: #d25e28; color: white; padding: 12px 18px; font-weight: 700; font-size: 1rem; display: flex; align-items: center; gap: 10px; }
  .file-header .badge { background: rgba(255,255,255,0.25); border-radius: 12px; padding: 2px 10px; font-size: 0.78rem; font-weight: 500; }
  .table-wrap { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 0.87rem; }
  thead tr { background: #f5e6de; }
  thead th { padding: 9px 13px; text-align: left; font-weight: 600; color: #7a3418; white-space: nowrap; border-bottom: 2px solid #f0d0be; }
  tbody tr:nth-child(even) { background: #fdf7f4; }
  tbody tr:hover { background: #fdeee5; }
  tbody td { padding: 8px 13px; border-bottom: 1px solid #f0e0d6; white-space: nowrap; }
  .kutu-cell { font-weight: 700; color: #d25e28; }
  .kat-cell  { font-weight: 600; color: #7a3418; font-style: italic; }
  .kat-filter-wrap { display: flex; align-items: flex-start; gap: 12px; width: 100%; }
  .kat-filter-wrap .btn-group { flex: 1; }
  .sadece-btn { padding: 8px 18px; border: 2px solid #b91c1c; background: white; color: #b91c1c; border-radius: 20px; font-size: 0.9rem; font-weight: 700; cursor: pointer; transition: all 0.18s; white-space: nowrap; opacity: 0.3; pointer-events: none; align-self: flex-start; }
  .sadece-btn:hover { background: #fee2e2; }
  .sadece-btn.enabled { opacity: 1; pointer-events: auto; }
  .sadece-btn.active { background: #b91c1c; color: white; }
  .search-row { background: white; border-radius: 10px; padding: 16px 20px; box-shadow: 0 1px 5px rgba(160,71,32,0.1); }
  .search-input { width: 100%; padding: 10px 16px; border: 2px solid #d25e28; border-radius: 20px; font-size: 0.95rem; color: #2e1a0e; outline: none; transition: border-color 0.18s; }
  .search-input:focus { border-color: #7a3418; }
  .search-input::placeholder { color: #c0a090; }
</style>
</head>
<body>
<header>
  <h1>&#128230; Kutu Kategorileri</h1>
  <p>Kutu ve/veya kategori secerek urunleri filtreleyin</p>
</header>
<div class="container">
  <div class="filters">
    <div class="filter-row">
      <div class="filter-label">Kutu</div>
      <div class="btn-group" id="kutu-grid"></div>
    </div>
    <div class="filter-row">
      <div class="filter-label">Kategori</div>
      <div class="kat-filter-wrap">
        <div class="btn-group" id="kat-grid"></div>
        <button class="sadece-btn" id="sadece-btn">Sadece</button>
      </div>
    </div>
    <div class="search-row">
      <div class="filter-label">Ara</div>
      <input type="text" class="search-input" id="search-input" placeholder="Herhangi bir degerde ara..." />
    </div>
  </div>
  <div id="results"></div>
</div>
<script>
var DATA = """ + data_json + """;
var activeKutu = null;
var activeKat = {};
var sadeceMode = false;
var searchTerm = "";

function handleKutuClick(e) {
  var btn = e.target.closest(".kutu-btn");
  if (!btn) return;
  var val = btn.getAttribute("data-val");
  var all = document.querySelectorAll(".kutu-btn");
  for (var i = 0; i < all.length; i++) all[i].classList.remove("active");
  if (val === "__all__") {
    activeKutu = null;
    btn.classList.add("active");
  } else {
    if (activeKutu === val) {
      activeKutu = null;
      document.querySelector('.kutu-btn[data-val="__all__"]').classList.add("active");t.add("active");
    } else {
      btn.classList.add("active");
      activeKutu = val;
    }
  }
  renderResults();
}

function updateSadeceBtn() {
  var sadece = document.getElementById("sadece-btn");
  var count = Object.keys(activeKat).length;
  if (count === 1) {
    sadece.classList.add("enabled");
  } else {
    sadece.classList.remove("enabled");
    sadece.classList.remove("active");
    sadeceMode = false;
  }
}

function handleKatClick(e) {
  var btn = e.target.closest(".kat-btn");
  if (!btn) return;
  var val = btn.getAttribute("data-val");
  if (val === "__all__") {
    activeKat = {};
    sadeceMode = false;
    var all = document.querySelectorAll(".kat-btn");
    for (var i = 0; i < all.length; i++) all[i].classList.remove("active");
    btn.classList.add("active");
  } else {
    if (activeKat[val]) {
      delete activeKat[val];
    } else {
      activeKat[val] = true;
    }
    var hepsi = document.querySelector('.kat-btn[data-val="__all__"]');
    var anyActive = Object.keys(activeKat).length > 0;
    hepsi.classList.toggle("active", !anyActive);
    btn.classList.toggle("active", !!activeKat[val]);
  }
  updateSadeceBtn();
  renderResults();
}

function handleSadeceClick() {
  var count = Object.keys(activeKat).length;
  if (count !== 1) return;
  sadeceMode = !sadeceMode;
  document.getElementById("sadece-btn").classList.toggle("active", sadeceMode);
  renderResults();
}

function buildButtons() {
  var kg = document.getElementById("kutu-grid");
  kg.innerHTML = "";
  var hk = document.createElement("button");
  hk.className = "kutu-btn active"; hk.textContent = "Hepsi"; hk.setAttribute("data-val", "__all__");
  kg.appendChild(hk);
  for (var i = 0; i < DATA.kutular.length; i++) {
    var b = document.createElement("button");
    b.className = "kutu-btn"; b.textContent = DATA.kutular[i]; b.setAttribute("data-val", DATA.kutular[i]);
    kg.appendChild(b);
  }
  kg.removeEventListener("click", handleKutuClick);
  kg.addEventListener("click", handleKutuClick);

  var katg = document.getElementById("kat-grid");
  katg.innerHTML = "";
  var hkat = document.createElement("button");
  hkat.className = "kat-btn active"; hkat.textContent = "Hepsi"; hkat.setAttribute("data-val", "__all__");
  katg.appendChild(hkat);
  for (var j = 0; j < DATA.kategoriler.length; j++) {
    var b2 = document.createElement("button");
    b2.className = "kat-btn"; b2.textContent = DATA.kategoriler[j]; b2.setAttribute("data-val", DATA.kategoriler[j]);
    katg.appendChild(b2);
  }
  katg.removeEventListener("click", handleKatClick);
  katg.addEventListener("click", handleKatClick);
}

function rowMatchesKutu(row, kutu_col) {
  if (!activeKutu) return true;
  return String(row[kutu_col]).trim() === activeKutu;
}

function rowMatchesKat(row, kat_col) {
  var selected = Object.keys(activeKat);
  if (selected.length === 0) return true;
  var parts = String(row[kat_col]).split(",");
  var rowKats = {};
  for (var i = 0; i < parts.length; i++) rowKats[parts[i].trim()] = true;
  if (sadeceMode) {
    // exact match: row must have ONLY the selected category (nothing more)
    var rowKatList = Object.keys(rowKats);
    if (rowKatList.length !== selected.length) return false;
    for (var k = 0; k < selected.length; k++) {
      if (!rowKats[selected[k]]) return false;
    }
    return true;
  }
  for (var j = 0; j < selected.length; j++) {
    if (!rowKats[selected[j]]) return false;
  }
  return true;
}

function rowMatchesSearch(row) {
  if (!searchTerm) return true;
  for (var i = 0; i < row.length; i++) {
    if (String(row[i]).toLowerCase().indexOf(searchTerm) !== -1) return true;
  }
  return false;
}

function renderResults() {
  var container = document.getElementById("results");
  var matchingFiles = [];
  var keys = Object.keys(DATA.file_data);
  for (var i = 0; i < keys.length; i++) {
    var fname = keys[i];
    var finfo = DATA.file_data[fname];
    var filteredRows = [];
    for (var r = 0; r < finfo.rows.length; r++) {
      var row = finfo.rows[r];
      if (rowMatchesKutu(row, finfo.kutu_col) && rowMatchesKat(row, finfo.kat_col) && rowMatchesSearch(row)) filteredRows.push(row);
    }
    if (filteredRows.length > 0) matchingFiles.push({ name: fname, headers: finfo.headers, kutu_col: finfo.kutu_col, kat_col: finfo.kat_col, rows: filteredRows });
  }
  if (matchingFiles.length === 0) {
    var lbl = [];
    if (activeKutu) lbl.push(activeKutu);
    var selKat2 = Object.keys(activeKat);
    if (selKat2.length > 0) lbl.push(selKat2.join(" + "));
    var msg = lbl.length > 0 ? lbl.join(" & ") + " icin kayit bulunamadi." : "Hic kayit bulunamadi.";
    container.innerHTML = "<div class=\\"no-result\\">" + msg + "</div>";
    return;
  }
  var lbl2 = [];
  if (activeKutu) lbl2.push(activeKutu);
  var selKat = Object.keys(activeKat);
  if (selKat.length > 0) lbl2.push(selKat.join(" + "));
  var prefix = lbl2.length > 0 ? lbl2.join(" &amp; ") + " &#8212; " : "";
  var html = "<div class=\\"section-title\\">" + prefix + matchingFiles.length + " dosya bulundu</div>";
  for (var f = 0; f < matchingFiles.length; f++) {
    var file = matchingFiles[f];
    html += "<div class=\\"file-block\\"><div class=\\"file-header\\"><span>" + file.name + "</span><span class=\\"badge\\">" + file.rows.length + " satir</span></div><div class=\\"table-wrap\\"><table><thead><tr>";
    for (var h = 0; h < file.headers.length; h++) {
      var hv = file.headers[h];
      html += "<th>" + (hv && hv !== "nan" ? hv : "&#8212;") + "</th>";
    }
    html += "</tr></thead><tbody>";
    for (var ri = 0; ri < file.rows.length; ri++) {
      html += "<tr>";
      var row2 = file.rows[ri];
      for (var c = 0; c < row2.length; c++) {
        var cell = (row2[c] !== "" && row2[c] !== "nan") ? row2[c] : "&#8212;";
        var cls = (c === file.kutu_col) ? " class=\\"kutu-cell\\"" : (c === file.kat_col ? " class=\\"kat-cell\\"" : "");
        html += "<td" + cls + ">" + cell + "</td>";
      }
      html += "</tr>";
    }
    html += "</tbody></table></div></div>";
  }
  container.innerHTML = html;
}

function init() {
  buildButtons();
  var si = document.getElementById("search-input");
  si.removeEventListener("input", handleSearch);
  si.addEventListener("input", handleSearch);
  var sb = document.getElementById("sadece-btn");
  sb.removeEventListener("click", handleSadeceClick);
  sb.addEventListener("click", handleSadeceClick);
  renderResults();
}

function handleSearch(e) {
  searchTerm = e.target.value.toLowerCase();
  renderResults();
}

var _inited = false;
function safeInit() { if (_inited) return; _inited = true; init(); }
document.addEventListener("DOMContentLoaded", safeInit);
window.addEventListener("load", safeInit);
</script>
</body>
</html>"""

    with open('kutu_viewer.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('Written: kutu_viewer.html')

if __name__ == '__main__':
    print('Reading files...')
    data = build_data()
    write_html(data)
    print()
    print('Kutular:    ', data['kutular'])
    print('Kategoriler:', data['kategoriler'])
    print('Files:      ', list(data['file_data'].keys()))
