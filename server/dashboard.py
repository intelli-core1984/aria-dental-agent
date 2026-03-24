"""
ARIA Admin Dashboard — HTML template.
Served at GET /admin/dashboard?key=ADMIN_KEY
Data injected server-side via __REGISTRATIONS_JSON__ placeholder.
"""

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>ARIA Admin</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #080d12;
    color: #e8edf2;
    font-family: 'Courier New', Courier, monospace;
    font-size: 12px;
    min-height: 100vh;
  }

  .topbar {
    background: #0f1419;
    border-bottom: 1px solid #1e2d3d;
    padding: 0 28px;
    height: 54px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 10;
  }
  .logo { color: #00e5a0; font-size: 14px; font-weight: bold; letter-spacing: 0.1em; }
  .refresh-note { color: #3a5a6a; font-size: 10px; }

  .stats {
    display: flex;
    gap: 14px;
    padding: 22px 28px 0;
    flex-wrap: wrap;
  }
  .stat-card {
    background: #0f1419;
    border: 1px solid #1e2d3d;
    border-radius: 8px;
    padding: 16px 24px;
    min-width: 130px;
  }
  .stat-label {
    color: #3a5a6a;
    font-size: 9px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 8px;
  }
  .stat-value           { color: #e8edf2; font-size: 28px; font-weight: bold; }
  .stat-value.pending   { color: #f0a500; }
  .stat-value.approved  { color: #00e5a0; }
  .stat-value.today     { color: #5a9fd4; }

  .section-title {
    padding: 22px 28px 10px;
    color: #3a5a6a;
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }

  .table-wrap {
    margin: 0 28px 32px;
    border: 1px solid #1e2d3d;
    border-radius: 8px;
    overflow: hidden;
    overflow-x: auto;
  }
  table { width: 100%; border-collapse: collapse; min-width: 780px; }
  thead { background: #0f1419; }
  th {
    padding: 10px 14px;
    text-align: left;
    color: #3a5a6a;
    font-size: 9px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    border-bottom: 1px solid #1e2d3d;
    white-space: nowrap;
  }
  td {
    padding: 11px 14px;
    border-bottom: 1px solid #0f1720;
    vertical-align: middle;
  }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: #0b1118; }

  .key-prefix { color: #3a5a6a; font-size: 10px; }
  .ip-addr    { color: #5a7a8a; font-size: 11px; }
  .email-col  { font-size: 11px; }

  .badge {
    display: inline-block;
    padding: 3px 9px;
    border-radius: 10px;
    font-size: 9px;
    font-weight: bold;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
  .badge-pending  { background:#2a1f00; color:#f0a500; border:1px solid #3a2d00; }
  .badge-approved { background:#001f14; color:#00e5a0; border:1px solid #003020; }
  .badge-rejected { background:#1f0000; color:#e05050; border:1px solid #2d0000; }

  .trial-bar-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .trial-bar {
    height: 4px;
    background: #1e2d3d;
    border-radius: 2px;
    width: 60px;
    overflow: hidden;
  }
  .trial-bar-fill {
    height: 100%;
    background: #f0a500;
    border-radius: 2px;
    transition: width 0.3s;
  }
  .trial-text { color: #5a7a8a; font-size: 10px; white-space: nowrap; }

  .btn {
    border: none;
    border-radius: 4px;
    padding: 5px 12px;
    font-family: inherit;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 0.06em;
    cursor: pointer;
    transition: opacity 0.15s;
    white-space: nowrap;
  }
  .btn:hover    { opacity: 0.75; }
  .btn:disabled { opacity: 0.25; cursor: not-allowed; }
  .btn-approve  { background: #00e5a0; color: #000; margin-right: 6px; }
  .btn-reject   { background: #1f0000; color: #e05050; border: 1px solid #3a0000; }

  .empty {
    text-align: center;
    padding: 52px;
    color: #3a5a6a;
  }

  #toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: #161d26;
    border: 1px solid #1e2d3d;
    border-radius: 6px;
    padding: 11px 20px;
    font-size: 11px;
    opacity: 0;
    transition: opacity 0.25s;
    pointer-events: none;
    z-index: 999;
  }
  #toast.show { opacity: 1; }
  #toast.ok  { border-color: #00e5a0; color: #00e5a0; }
  #toast.err { border-color: #e05050; color: #e05050; }
</style>
</head>
<body>

<div class="topbar">
  <span class="logo">⬡ &nbsp;ARIA &nbsp;·&nbsp; Admin</span>
  <span class="refresh-note" id="refresh-note">auto-refresh in 30s</span>
</div>

<div class="stats" id="stats"></div>

<div class="section-title">Registrations</div>
<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th>Email</th>
        <th>License Key</th>
        <th>IP Address</th>
        <th>Device</th>
        <th>Registered</th>
        <th>Status</th>
        <th>Trial Used</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
</div>

<div id="toast"></div>

<script>
const ROWS      = __REGISTRATIONS_JSON__;
const ADMIN_KEY = new URLSearchParams(window.location.search).get('key') || '';

function fmtDate(ts) {
  if (!ts) return '—';
  const d = new Date(ts * 1000);
  return d.toLocaleDateString('en-CA') + ' '
       + d.toLocaleTimeString('en-CA', { hour: '2-digit', minute: '2-digit' });
}

function parseDevice(ua) {
  if (!ua) return '—';
  if (/Windows/.test(ua)) return 'Windows';
  if (/Macintosh|Mac OS/.test(ua)) return 'Mac';
  if (/Linux/.test(ua)) return 'Linux';
  if (/iPhone|iPad/.test(ua)) return 'iOS';
  if (/Android/.test(ua)) return 'Android';
  return ua.slice(0, 20);
}

function badge(status) {
  return `<span class="badge badge-${status}">${status}</span>`;
}

function trialBar(used, limit) {
  const pct = Math.min(100, Math.round((used / limit) * 100));
  return `
    <div class="trial-bar-wrap">
      <div class="trial-bar">
        <div class="trial-bar-fill" style="width:${pct}%"></div>
      </div>
      <span class="trial-text">${used} / ${limit}</span>
    </div>`;
}

function toast(msg, isErr) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'show ' + (isErr ? 'err' : 'ok');
  clearTimeout(t._t);
  t._t = setTimeout(() => { t.className = ''; }, 3200);
}

function renderStats(rows) {
  const total    = rows.length;
  const pending  = rows.filter(r => r.status === 'pending').length;
  const approved = rows.filter(r => r.status === 'approved').length;
  const cutoff   = Date.now() / 1000 - 86400;
  const today    = rows.filter(r => r.install_date > cutoff).length;

  document.getElementById('stats').innerHTML = `
    <div class="stat-card"><div class="stat-label">Total</div>
      <div class="stat-value">${total}</div></div>
    <div class="stat-card"><div class="stat-label">Pending</div>
      <div class="stat-value pending">${pending}</div></div>
    <div class="stat-card"><div class="stat-label">Approved</div>
      <div class="stat-value approved">${approved}</div></div>
    <div class="stat-card"><div class="stat-label">Last 24h</div>
      <div class="stat-value today">${today}</div></div>
  `;
}

function renderTable(rows) {
  const tbody = document.getElementById('tbody');
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="empty">No registrations yet.</td></tr>';
    return;
  }
  tbody.innerHTML = rows.map(r => {
    const isPending  = r.status === 'pending';
    const isRejected = r.status === 'rejected';
    const keyShort   = r.license_key.length > 26
      ? r.license_key.slice(0, 26) + '…' : r.license_key;

    return `
    <tr id="row-${r.id}">
      <td class="email-col">${r.email}</td>
      <td><span class="key-prefix">${keyShort}</span></td>
      <td><span class="ip-addr">${r.ip_address || '—'}</span></td>
      <td>${parseDevice(r.user_agent)}</td>
      <td>${fmtDate(r.install_date)}</td>
      <td>${badge(r.status)}</td>
      <td>${trialBar(r.trial_requests, r.trial_limit)}</td>
      <td>
        <button class="btn btn-approve"
          ${isPending ? '' : 'disabled'}
          onclick="doAction('approve','${r.license_key}',${r.id})">
          APPROVE
        </button>
        <button class="btn btn-reject"
          ${isRejected ? 'disabled' : ''}
          onclick="doAction('reject','${r.license_key}',${r.id})">
          REJECT
        </button>
      </td>
    </tr>`;
  }).join('');
}

async function doAction(action, licenseKey, rowId) {
  const btns = document.querySelectorAll(`#row-${rowId} .btn`);
  btns.forEach(b => b.disabled = true);
  try {
    const res = await fetch(`/admin/registrations/${action}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-admin-key': ADMIN_KEY },
      body: JSON.stringify({ license_key: licenseKey })
    });
    if (!res.ok) {
      const e = await res.json().catch(() => ({}));
      throw new Error(e.detail || res.statusText);
    }
    toast(`${licenseKey.slice(0, 20)}… ${action}d ✓`, false);
    setTimeout(() => window.location.reload(), 900);
  } catch(e) {
    toast('Error: ' + e.message, true);
    btns.forEach(b => b.disabled = false);
  }
}

// Auto-refresh countdown
let secs = 30;
const note = document.getElementById('refresh-note');
setInterval(() => {
  secs--;
  note.textContent = `auto-refresh in ${secs}s`;
  if (secs <= 0) window.location.reload();
}, 1000);

renderStats(ROWS);
renderTable(ROWS);
</script>
</body>
</html>
"""
