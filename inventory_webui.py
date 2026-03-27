#!/usr/bin/env python3
import html
import json
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs

BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "hardware_inventory.json"
MD_FILE = BASE / "HARDWARE_INVENTORY.md"


def load_data():
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    data.setdefault("meta", {})["last_updated"] = str(date.today())
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    write_markdown(data)


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        out.append("| " + " | ".join((str(c) if c else "_(confirm)_") for c in row) + " |")
    return "\n".join(out)


def write_markdown(data):
    active = data.get("active", [])
    spare = data.get("spare", [])
    networks = data.get("networks", [])
    changelog = data.get("change_log", [])

    active_rows = [[x.get("name"), x.get("type"), x.get("hostname"), x.get("ip"), x.get("network_vlan"), x.get("primary_use"), x.get("location"), x.get("status"), x.get("notes")] for x in active]
    spare_rows = [[x.get("name"), x.get("type"), x.get("serial_id"), x.get("last_known_state"), x.get("intended_use"), x.get("notes")] for x in spare]
    network_rows = [[x.get("network"), x.get("vlan"), x.get("cidr"), x.get("intent")] for x in networks]

    md = []
    md.append("# Hardware Inventory")
    md.append("")
    md.append(f"Last updated: {data.get('meta', {}).get('last_updated', str(date.today()))}")
    md.append(f"Owner: {data.get('meta', {}).get('owner', 'Sheldon + Rune')}")
    md.append("")
    md.append("Purpose: shared source of truth for active and spare/inactive hardware, IPs, hostnames, role, and notes.")
    md.append("\n---\n")

    md.append("## Active / In Use\n")
    md.append(md_table(
        ["Name", "Type", "Hostname", "IP", "Network/VLAN", "Primary Use", "Location", "Status", "Notes"],
        active_rows,
    ))

    md.append("\n---\n")
    md.append("## Spare / Inactive / Staging\n")
    md.append(md_table(
        ["Name", "Type", "Serial/ID", "Last Known State", "Intended Use", "Notes"],
        spare_rows,
    ))

    md.append("\n---\n")
    md.append("## Networks (Reference)\n")
    md.append(md_table(["Network", "VLAN", "CIDR", "Current Intent"], network_rows))

    md.append("\n---\n")
    md.append("## Change Log (Newest First)\n")
    for line in changelog:
        md.append(f"- **{line}**")

    md.append("\n---\n")
    md.append("## Update Rules\n")
    md.append("1. Add new hardware on receipt (even if not configured yet).")
    md.append("2. Keep IP/hostname fields current whenever changed.")
    md.append("3. Move entries between **Active** and **Spare/Inactive** as status changes.")
    md.append("4. Add one-line note when role changes significantly.")
    md.append("5. Keep this file in git so both of us have history.")

    MD_FILE.write_text("\n".join(md) + "\n", encoding="utf-8")


class Handler(BaseHTTPRequestHandler):
    def _redirect(self, to="/"):
        self.send_response(302)
        self.send_header("Location", to)
        self.end_headers()

    def _body(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        return {k: v[0] for k, v in parse_qs(raw).items()}

    @staticmethod
    def _to_index(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def do_GET(self):
        data = load_data()
        active = data.get("active", [])
        spare = data.get("spare", [])

        def esc(v):
            return html.escape(v or "")

        active_rows = ""
        for i, x in enumerate(active):
            active_rows += f"""
<tr>
  <form method='post' action='/update_active'>
    <input type='hidden' name='idx' value='{i}'>
    <td><input name='name' value='{esc(x.get('name'))}' required></td>
    <td><input name='type' value='{esc(x.get('type'))}'></td>
    <td><input name='hostname' value='{esc(x.get('hostname'))}'></td>
    <td><input name='ip' value='{esc(x.get('ip'))}'></td>
    <td><input name='network_vlan' value='{esc(x.get('network_vlan'))}'></td>
    <td><input name='primary_use' value='{esc(x.get('primary_use'))}'></td>
    <td><input name='location' value='{esc(x.get('location'))}'></td>
    <td><input name='status' value='{esc(x.get('status'))}'></td>
    <td><input name='notes' value='{esc(x.get('notes'))}'></td>
    <td class='actions'>
      <button type='submit' class='btn btn-save'>Save</button>
  </form>
  <form method='post' action='/delete_active' onsubmit="return confirm('Delete {esc(x.get('name', 'this item'))}?');">
      <input type='hidden' name='idx' value='{i}'>
      <button type='submit' class='btn btn-del'>Del</button>
  </form>
  <form method='post' action='/move'>
      <input type='hidden' name='name' value='{esc(x.get('name'))}'>
      <input type='hidden' name='target' value='spare'>
      <button type='submit' class='btn btn-move'>&#8594; Spare</button>
  </form>
    </td>
</tr>
"""

        spare_rows = ""
        for i, x in enumerate(spare):
            spare_rows += f"""
<tr>
  <form method='post' action='/update_spare'>
    <input type='hidden' name='idx' value='{i}'>
    <td><input name='name' value='{esc(x.get('name'))}' required></td>
    <td><input name='type' value='{esc(x.get('type'))}'></td>
    <td><input name='serial_id' value='{esc(x.get('serial_id'))}'></td>
    <td><input name='last_known_state' value='{esc(x.get('last_known_state'))}'></td>
    <td><input name='intended_use' value='{esc(x.get('intended_use'))}'></td>
    <td><input name='notes' value='{esc(x.get('notes'))}'></td>
    <td class='actions'>
      <button type='submit' class='btn btn-save'>Save</button>
  </form>
  <form method='post' action='/delete_spare' onsubmit="return confirm('Delete {esc(x.get('name', 'this item'))}?');">
      <input type='hidden' name='idx' value='{i}'>
      <button type='submit' class='btn btn-del'>Del</button>
  </form>
  <form method='post' action='/move'>
      <input type='hidden' name='name' value='{esc(x.get('name'))}'>
      <input type='hidden' name='target' value='active'>
      <button type='submit' class='btn btn-move'>&#8594; Active</button>
  </form>
    </td>
</tr>
"""

        active_count = len(active)
        spare_count = len(spare)

        html_page = """
<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Hardware Inventory</title>
<style>
:root {{
  --bg: #f0f2f5;
  --surface: #fff;
  --border: #dee2e6;
  --header-bg: #1a1d23;
  --accent: #0d6efd;
  --danger: #dc3545;
  --success: #198754;
  --muted: #6c757d;
  --text: #212529;
  --row-alt: #f8f9fb;
  --shadow: 0 1px 4px rgba(0,0,0,.1);
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); }}

.topbar {{ background: var(--header-bg); color: #fff; padding: 14px 24px; display: flex; align-items: baseline; gap: 14px; }}
.topbar h1 {{ font-size: 1.15rem; font-weight: 600; }}
.topbar .sub {{ font-size: .78rem; opacity: .6; }}

.main {{ max-width: 1450px; margin: 0 auto; padding: 0 16px 48px; }}

.filterbar {{ position: sticky; top: 0; z-index: 100; background: var(--surface); border-bottom: 1px solid var(--border); padding: 10px 16px; display: flex; gap: 10px; flex-wrap: wrap; align-items: flex-end; margin: 0 -16px; box-shadow: var(--shadow); }}
.filterbar .field {{ display: flex; flex-direction: column; gap: 3px; min-width: 150px; flex: 1; }}
.filterbar .field label {{ font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }}
.filterbar input, .filterbar select {{ border: 1px solid var(--border); border-radius: 6px; padding: 6px 10px; font-size: 13px; background: var(--bg); }}
.filterbar input:focus, .filterbar select:focus {{ border-color: var(--accent); outline: none; background: #fff; }}
.chips {{ display: flex; flex-direction: column; gap: 3px; }}
.chips label {{ font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }}
.chips-row {{ display: flex; gap: 5px; flex-wrap: wrap; }}
.chip {{ background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 4px 11px; font-size: 12px; cursor: pointer; line-height: 1.4; }}
.chip:hover {{ border-color: var(--accent); color: var(--accent); }}
.chip-clear {{ color: var(--muted); }}

.section-wrap {{ margin-top: 24px; }}
.section-header {{ display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }}
.section-header h2 {{ font-size: 1rem; font-weight: 700; }}
.badge {{ background: var(--accent); color: #fff; border-radius: 9px; padding: 2px 8px; font-size: 11px; font-weight: 700; }}

.table-wrap {{ overflow-x: auto; border-radius: 8px; box-shadow: var(--shadow); }}
table {{ border-collapse: collapse; width: 100%; font-size: 12.5px; background: var(--surface); }}
th {{ background: #2d3240; color: #e8eaf0; padding: 9px 8px; text-align: left; font-weight: 600; white-space: nowrap; font-size: 12px; }}
th.sortable {{ cursor: pointer; user-select: none; }}
th.sortable:hover {{ background: #3d4255; }}
td {{ padding: 5px 8px; border-bottom: 1px solid #eef0f3; vertical-align: middle; }}
tr:last-child td {{ border-bottom: none; }}
tr:nth-child(even) td {{ background: var(--row-alt); }}
tr:hover td {{ background: #edf2ff; }}

td input {{ border: 1px solid transparent; border-radius: 4px; padding: 4px 5px; width: 100%; font-size: 12px; background: transparent; min-width: 55px; font-family: inherit; }}
td input:focus {{ border-color: var(--accent); background: #fff; outline: none; box-shadow: 0 0 0 2px rgba(13,110,253,.15); }}
td input[name='notes'] {{ min-width: 150px; }}

.actions {{ white-space: nowrap; min-width: 105px; }}
.actions form {{ display: inline; }}
.btn {{ display: inline-flex; align-items: center; padding: 3px 8px; border-radius: 4px; border: 1px solid; font-size: 11px; cursor: pointer; margin: 1px 0; font-family: inherit; line-height: 1.5; }}
.btn-save {{ background: var(--success); color: #fff; border-color: var(--success); }}
.btn-save:hover {{ background: #146c43; }}
.btn-del {{ background: transparent; color: var(--danger); border-color: #f5c2c7; }}
.btn-del:hover {{ background: var(--danger); color: #fff; border-color: var(--danger); }}
.btn-move {{ background: transparent; color: var(--muted); border-color: var(--border); }}
.btn-move:hover {{ border-color: var(--accent); color: var(--accent); }}

details.add-panel {{ margin-top: 10px; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; box-shadow: var(--shadow); }}
details.add-panel summary {{ padding: 10px 16px; font-size: 13px; font-weight: 600; cursor: pointer; list-style: none; color: var(--accent); }}
details.add-panel summary::-webkit-details-marker {{ display: none; }}
details.add-panel summary::before {{ content: '+ '; }}
details.add-panel[open] summary::before {{ content: '− '; }}
.add-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(175px, 1fr)); gap: 10px; padding: 4px 16px 12px; }}
.add-grid label {{ display: flex; flex-direction: column; gap: 3px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); }}
.add-grid input {{ border: 1px solid var(--border); border-radius: 5px; padding: 6px 8px; font-size: 13px; font-family: inherit; }}
.add-grid input:focus {{ border-color: var(--accent); outline: none; }}
.add-footer {{ padding: 0 16px 14px; }}
.btn-primary {{ background: var(--accent); color: #fff; border: none; border-radius: 6px; padding: 8px 20px; font-size: 13px; font-weight: 600; cursor: pointer; font-family: inherit; }}
.btn-primary:hover {{ background: #0b5ed7; }}
</style></head><body>

<div class='topbar'>
  <h1>Hardware Inventory</h1>
  <span class='sub'>hardware_inventory.json &nbsp;&middot;&nbsp; Edit fields inline and click Save &nbsp;&middot;&nbsp; Click headers to sort</span>
</div>

<div class='main'>
<div class='filterbar'>
  <div class='field'>
    <label>Search</label>
    <input id='globalFilter' placeholder='name, IP, type, notes&hellip;'>
  </div>
  <div class='field'>
    <label>Section</label>
    <select id='sectionFilter'>
      <option value='all'>All sections</option>
      <option value='active'>Active only</option>
      <option value='spare'>Spare only</option>
    </select>
  </div>
  <div class='field'>
    <label>Type</label>
    <input id='typeFilter' placeholder='SBC, NAS, Robot&hellip;'>
  </div>
  <div class='chips'>
    <label>Quick filter</label>
    <div class='chips-row'>
      <button type='button' class='chip' onclick="quickType('RPI')">RPI</button>
      <button type='button' class='chip' onclick="quickType('SBC')">SBC</button>
      <button type='button' class='chip' onclick="quickType('Robot')">Robot</button>
      <button type='button' class='chip chip-clear' onclick="clearFilters()">&times; Clear</button>
    </div>
  </div>
</div>

<div class='section-wrap' id='activeWrap'>
  <div class='section-header'>
    <h2>Active / In Use</h2>
    <span class='badge' id='activeCount'>__ACTIVE_COUNT__</span>
  </div>
  <div class='table-wrap'>
    <table id='activeTable'>
    <tr>
      <th class='sortable' data-col='0'>Name</th>
      <th class='sortable' data-col='1'>Type</th>
      <th class='sortable' data-col='2'>Hostname</th>
      <th class='sortable' data-col='3'>IP</th>
      <th class='sortable' data-col='4'>Network/VLAN</th>
      <th class='sortable' data-col='5'>Primary Use</th>
      <th class='sortable' data-col='6'>Location</th>
      <th class='sortable' data-col='7'>Status</th>
      <th class='sortable' data-col='8'>Notes</th>
      <th>Actions</th>
    </tr>
    __ACTIVE_ROWS__
    </table>
  </div>
  <details class='add-panel' id='addActivePanel'>
    <summary>Add Active Item</summary>
    <form method='post' action='/add_active'>
    <div class='add-grid'>
      <label>Name *<input name='name' required></label>
      <label>Type<input name='type'></label>
      <label>Hostname<input name='hostname'></label>
      <label>IP<input name='ip'></label>
      <label>Network/VLAN<input name='network_vlan'></label>
      <label>Primary Use<input name='primary_use'></label>
      <label>Location<input name='location'></label>
      <label>Status<input name='status' value='Active'></label>
      <label>Notes<input name='notes'></label>
    </div>
    <div class='add-footer'><button type='submit' class='btn-primary'>Add Active Item</button></div>
    </form>
  </details>
</div>

<div class='section-wrap' id='spareWrap'>
  <div class='section-header'>
    <h2>Spare / Inactive / Staging</h2>
    <span class='badge' id='spareCount'>__SPARE_COUNT__</span>
  </div>
  <div class='table-wrap'>
    <table id='spareTable'>
    <tr>
      <th class='sortable' data-col='0'>Name</th>
      <th class='sortable' data-col='1'>Type</th>
      <th class='sortable' data-col='2'>Serial/ID</th>
      <th class='sortable' data-col='3'>Last Known State</th>
      <th class='sortable' data-col='4'>Intended Use</th>
      <th class='sortable' data-col='5'>Notes</th>
      <th>Actions</th>
    </tr>
    __SPARE_ROWS__
    </table>
  </div>
  <details class='add-panel' id='addSparePanel'>
    <summary>Add Spare Item</summary>
    <form method='post' action='/add_spare'>
    <div class='add-grid'>
      <label>Name *<input name='name' required></label>
      <label>Type<input name='type'></label>
      <label>Serial/ID<input name='serial_id'></label>
      <label>Last Known State<input name='last_known_state'></label>
      <label>Intended Use<input name='intended_use'></label>
      <label>Notes<input name='notes'></label>
    </div>
    <div class='add-footer'><button type='submit' class='btn-primary'>Add Spare Item</button></div>
    </form>
  </details>
</div>

</div>

<script>
const state = {{
  sort: {{ active: {{ col: 0, dir: 1 }}, spare: {{ col: 0, dir: 1 }} }}
}};

function cellText(row, idx) {{
  const cell = row.cells[idx];
  if (!cell) return '';
  const input = cell.querySelector('input');
  return (input ? input.value : cell.textContent || '').trim().toLowerCase();
}}

function ipToNum(ip) {{
  const parts = (ip || '').split('.');
  if (parts.length !== 4) return -1;
  return parts.reduce((acc, p) => acc * 256 + (parseInt(p) || 0), 0);
}}

function sortTable(tableId, colIdx) {{
  const table = document.getElementById(tableId);
  const section = tableId === 'activeTable' ? 'active' : 'spare';
  const rows = Array.from(table.querySelectorAll('tr')).slice(1);
  const s = state.sort[section];
  if (s.col === colIdx) s.dir *= -1; else {{ s.col = colIdx; s.dir = 1; }}
  const headerText = (table.rows[0].cells[colIdx] || {{}}).textContent || '';
  const isIP = headerText.trim() === 'IP';
  rows.sort((a, b) => {{
    if (isIP) return (ipToNum(cellText(a, colIdx)) - ipToNum(cellText(b, colIdx))) * s.dir;
    return cellText(a, colIdx).localeCompare(cellText(b, colIdx)) * s.dir;
  }});
  rows.forEach(r => table.appendChild(r));
  applyFilters();
}}

function quickType(t) {{
  document.getElementById('typeFilter').value = t;
  applyFilters();
}}

function clearFilters() {{
  document.getElementById('globalFilter').value = '';
  document.getElementById('typeFilter').value = '';
  document.getElementById('sectionFilter').value = 'all';
  applyFilters();
}}

function rowMatches(row, globalQ, typeQ) {{
  const txt = row.innerText.toLowerCase();
  const typeCell = row.cells[1];
  const typeInput = typeCell ? typeCell.querySelector('input') : null;
  const typeVal = (typeInput ? typeInput.value : typeCell ? typeCell.textContent : '').toLowerCase().trim();
  if (globalQ && !txt.includes(globalQ)) return false;
  if (typeQ && typeVal !== typeQ) return false;
  return true;
}}

function updateCounts() {{
  const aTbl = document.getElementById('activeTable');
  const sTbl = document.getElementById('spareTable');
  const aRows = Array.from(aTbl.querySelectorAll('tr')).slice(1);
  const sRows = Array.from(sTbl.querySelectorAll('tr')).slice(1);
  const aVis = aRows.filter(r => r.style.display !== 'none').length;
  const sVis = sRows.filter(r => r.style.display !== 'none').length;
  document.getElementById('activeCount').textContent = aVis === aRows.length ? aRows.length : aVis + ' / ' + aRows.length;
  document.getElementById('spareCount').textContent = sVis === sRows.length ? sRows.length : sVis + ' / ' + sRows.length;
}}

function applyFilters() {{
  const globalQ = document.getElementById('globalFilter').value.trim().toLowerCase();
  const typeQ = document.getElementById('typeFilter').value.trim().toLowerCase();
  const section = document.getElementById('sectionFilter').value;

  const activeTable = document.getElementById('activeTable');
  const spareTable = document.getElementById('spareTable');

  Array.from(activeTable.querySelectorAll('tr')).slice(1).forEach(r => {{
    r.style.display = rowMatches(r, globalQ, typeQ) ? '' : 'none';
  }});
  Array.from(spareTable.querySelectorAll('tr')).slice(1).forEach(r => {{
    r.style.display = rowMatches(r, globalQ, typeQ) ? '' : 'none';
  }});

  document.getElementById('activeWrap').style.display = (section === 'spare') ? 'none' : '';
  document.getElementById('spareWrap').style.display = (section === 'active') ? 'none' : '';

  updateCounts();
}}

document.querySelectorAll('th.sortable').forEach(th => {{
  th.addEventListener('click', () => {{
    const table = th.closest('table');
    sortTable(table.id, parseInt(th.dataset.col, 10));
  }});
}});

document.getElementById('globalFilter').addEventListener('input', applyFilters);
document.getElementById('typeFilter').addEventListener('input', applyFilters);
document.getElementById('sectionFilter').addEventListener('change', applyFilters);
updateCounts();
</script>

</body></html>
"""
        html_page = html_page.replace("__ACTIVE_ROWS__", active_rows).replace("__SPARE_ROWS__", spare_rows)
        html_page = html_page.replace("__ACTIVE_COUNT__", str(active_count)).replace("__SPARE_COUNT__", str(spare_count))
        html_page = html_page.replace("{{", "{").replace("}}", "}")
        out = html_page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def do_POST(self):
        data = load_data()
        form = self._body()

        if self.path == "/add_active":
            data.setdefault("active", []).append({
                "name": form.get("name", ""),
                "type": form.get("type", ""),
                "hostname": form.get("hostname", ""),
                "ip": form.get("ip", ""),
                "network_vlan": form.get("network_vlan", ""),
                "primary_use": form.get("primary_use", ""),
                "location": form.get("location", ""),
                "status": form.get("status", "Active"),
                "notes": form.get("notes", ""),
            })
            data.setdefault("change_log", []).insert(0, f"{date.today()}: Added active item '{form.get('name', '')}' via WebUI.")
            save_data(data)
            return self._redirect()

        if self.path == "/add_spare":
            data.setdefault("spare", []).append({
                "name": form.get("name", ""),
                "type": form.get("type", ""),
                "serial_id": form.get("serial_id", ""),
                "last_known_state": form.get("last_known_state", ""),
                "intended_use": form.get("intended_use", ""),
                "notes": form.get("notes", ""),
            })
            data.setdefault("change_log", []).insert(0, f"{date.today()}: Added spare item '{form.get('name', '')}' via WebUI.")
            save_data(data)
            return self._redirect()

        if self.path == "/update_active":
            idx = self._to_index(form.get("idx"))
            active = data.get("active", [])
            if idx is not None and 0 <= idx < len(active):
                active[idx] = {
                    "name": form.get("name", ""),
                    "type": form.get("type", ""),
                    "hostname": form.get("hostname", ""),
                    "ip": form.get("ip", ""),
                    "network_vlan": form.get("network_vlan", ""),
                    "primary_use": form.get("primary_use", ""),
                    "location": form.get("location", ""),
                    "status": form.get("status", "Active"),
                    "notes": form.get("notes", ""),
                }
                data.setdefault("change_log", []).insert(0, f"{date.today()}: Updated active item '{form.get('name', '')}' via WebUI.")
                save_data(data)
            return self._redirect()

        if self.path == "/update_spare":
            idx = self._to_index(form.get("idx"))
            spare = data.get("spare", [])
            if idx is not None and 0 <= idx < len(spare):
                spare[idx] = {
                    "name": form.get("name", ""),
                    "type": form.get("type", ""),
                    "serial_id": form.get("serial_id", ""),
                    "last_known_state": form.get("last_known_state", ""),
                    "intended_use": form.get("intended_use", ""),
                    "notes": form.get("notes", ""),
                }
                data.setdefault("change_log", []).insert(0, f"{date.today()}: Updated spare item '{form.get('name', '')}' via WebUI.")
                save_data(data)
            return self._redirect()

        if self.path == "/delete_active":
            idx = self._to_index(form.get("idx"))
            active = data.get("active", [])
            if idx is not None and 0 <= idx < len(active):
                name = active[idx].get("name", "")
                active.pop(idx)
                data.setdefault("change_log", []).insert(0, f"{date.today()}: Deleted active item '{name}' via WebUI.")
                save_data(data)
            return self._redirect()

        if self.path == "/delete_spare":
            idx = self._to_index(form.get("idx"))
            spare = data.get("spare", [])
            if idx is not None and 0 <= idx < len(spare):
                name = spare[idx].get("name", "")
                spare.pop(idx)
                data.setdefault("change_log", []).insert(0, f"{date.today()}: Deleted spare item '{name}' via WebUI.")
                save_data(data)
            return self._redirect()

        if self.path == "/move":
            name = (form.get("name") or "").strip().lower()
            target = form.get("target", "active")
            if name:
                source_key = "active" if target == "spare" else "spare"
                source = data.get(source_key, [])
                dest = data.setdefault(target, [])
                idx = next((i for i, x in enumerate(source) if (x.get("name", "").strip().lower() == name)), None)
                if idx is not None:
                    item = source.pop(idx)
                    if target == "active":
                        item.setdefault("hostname", "")
                        item.setdefault("ip", "")
                        item.setdefault("network_vlan", "")
                        item.setdefault("primary_use", item.get("intended_use", ""))
                        item.setdefault("location", "")
                        item.setdefault("status", "Active")
                    else:
                        item.setdefault("serial_id", "")
                        item.setdefault("last_known_state", item.get("status", "Inactive"))
                        item.setdefault("intended_use", item.get("primary_use", ""))
                    dest.append(item)
                    data.setdefault("change_log", []).insert(0, f"{date.today()}: Moved '{item.get('name', '')}' to {target} via WebUI.")
                    save_data(data)
            return self._redirect()

        self.send_response(404)
        self.end_headers()


if __name__ == "__main__":
    write_markdown(load_data())
    host = "0.0.0.0"
    port = 8787
    print(f"Inventory WebUI running on http://{host}:{port}")
    HTTPServer((host, port), Handler).serve_forever()
