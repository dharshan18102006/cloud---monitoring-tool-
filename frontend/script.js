// =====================================
// System Monitoring Tool — Dashboard Script
// =====================================

const API = (window.location.protocol.startsWith('http') && window.location.port !== '8000') ? '' : 'http://localhost:5000';
const TAB_CONFIG = {
    overview:  { title: 'Dashboard Overview',  subtitle: 'Real-time system telemetry and performance monitoring' },
    processes: { title: 'Process Manager',     subtitle: 'All running processes, sorted by CPU usage. Terminate tasks directly from here.' },
    warnings:  { title: 'Alerts & Warnings',   subtitle: 'Live system health alerts, threshold rules and diagnostic events.' }
};

let allProcesses = [];
let allWarnings  = [];

// ——— Tab Switching ———
function switchTab(target) {
    document.querySelectorAll('.nav-links li').forEach(li => li.classList.remove('active'));
    document.querySelectorAll('.tab-section').forEach(sec => sec.style.display = 'none');

    const navItem = document.querySelector(`.nav-links li[data-tab="${target}"]`);
    if (navItem) navItem.classList.add('active');

    const section = document.getElementById(target);
    if (section) {
        section.style.display = 'block';
        section.classList.add('fade-in');
        setTimeout(() => section.classList.remove('fade-in'), 400);
    }

    const cfg = TAB_CONFIG[target] || {};
    document.getElementById('pageTitle').innerText    = cfg.title    || '';
    document.getElementById('pageSubtitle').innerText = cfg.subtitle || '';
}
window.switchTab = switchTab;

// ——— Protected process guard (client-side fast-fail) ———
const PROTECTED_PIDS  = new Set([0, 4]);
const PROTECTED_NAMES = new Set([
    'system idle process', 'system', 'csrss.exe',
    'smss.exe', 'wininit.exe', 'winlogon.exe',
    'services.exe', 'lsass.exe'
]);

// ——— Kill Process ———
window.killProcess = async function(pid, nameRaw) {
    const name = (nameRaw || '').toLowerCase();

    // Block critical processes immediately
    if (PROTECTED_PIDS.has(pid) || PROTECTED_NAMES.has(name)) {
        showToast(`🛡️ "${nameRaw || pid}" is a protected OS process and cannot be terminated.`, 'error');
        return;
    }

    if (!confirm(`Terminate "${nameRaw}" (PID ${pid})?\n\nThis action is irreversible.`)) return;

    // Instant visual removal with fade animation
    const row = document.querySelector(`tr[data-pid="${pid}"]`);
    if (row) {
        row.style.transition = 'opacity 0.3s, transform 0.3s';
        row.style.opacity    = '0';
        row.style.transform  = 'translateX(20px)';
        setTimeout(() => row.remove(), 320);
    }

    try {
        const res  = await fetch(`${API}/api/kill_process/${pid}`, { method: 'POST' });
        const data = await res.json();
        const ok   = data.status === 'success';
        showToast(ok ? `✅ ${data.message}` : `❌ ${data.message}`, ok ? 'success' : 'error');

        // If kill failed, restore row (re-render will happen on next socket tick)
        if (!ok && row) {
            row.style.opacity   = '1';
            row.style.transform = 'none';
        }
    } catch {
        showToast('❌ Unable to reach backend. Check server connection.', 'error');
        // restore row on network failure
        if (row) { row.style.opacity = '1'; row.style.transform = 'none'; }
    }
};

// ——— Toast Notification ———
function showToast(msg, type = 'success') {
    const t = document.createElement('div');
    t.className = `toast toast-${type}`;
    t.innerText = msg;
    document.body.appendChild(t);
    setTimeout(() => t.classList.add('show'), 10);
    setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 400); }, 3000);
}

// ——— Format bytes ———
function fmtGB(bytes) { return (bytes / 1024 / 1024 / 1024).toFixed(1); }

// ——— Set progress bar colour ———
function setBar(id, pct) {
    const el = document.getElementById(id);
    if (!el) return;
    el.style.width = Math.min(pct, 100) + '%';
    el.style.background = pct > 85 ? 'var(--danger-color)' : pct > 70 ? 'var(--warning-color)' : 'var(--accent-color)';
}

// ——— Render CPU core grid ———
function renderCores(perCore) {
    const grid = document.getElementById('coreGrid');
    if (!grid) return;
    grid.innerHTML = perCore.map((c, i) => `
        <div class="core-cell">
            <div class="core-bar-wrap">
                <div class="core-bar" style="height:${c}%;background:${c > 85 ? 'var(--danger-color)' : c > 70 ? 'var(--warning-color)' : 'var(--accent-color)'}"></div>
            </div>
            <div class="core-label">C${i}</div>
            <div class="core-val">${Math.round(c)}%</div>
        </div>
    `).join('');
}

// ——— Render process tables ———
function renderProcesses(procs) {
    allProcesses = procs;

    // Top 5 in Overview
    const top5 = document.getElementById('topProcessList');
    if (top5) {
        top5.innerHTML = procs.slice(0, 5).map(p => `
            <tr>
                <td><span class="mono">${p.pid}</span></td>
                <td>${p.name}</td>
                <td><span class="${(p.cpu_percent || 0) > 50 ? 'val-red' : ''}">${(p.cpu_percent || 0).toFixed(1)}%</span></td>
                <td>${(p.memory_percent || 0).toFixed(1)}%</td>
                <td><span class="status-badge status-${(p.status || 'unknown').toLowerCase()}">${p.status || '—'}</span></td>
            </tr>
        `).join('');
    }

    // Update total count KPI
    const pc = document.getElementById('procCount');
    if (pc) pc.innerText = procs.length;
    const tp = document.getElementById('totalProcCount');
    if (tp) tp.innerText = procs.length;

    // Proc bar (normalise to max processes visible 200)
    const procBar = document.getElementById('procBar');
    if (procBar) procBar.style.width = Math.min((procs.length / 200) * 100, 100) + '%';

    // Full list (with search filter)
    renderFilteredProcesses();
}

function renderFilteredProcesses() {
    const query = (document.getElementById('procSearch')?.value || '').toLowerCase();
    const filtered = allProcesses.filter(p =>
        String(p.pid).includes(query) || (p.name || '').toLowerCase().includes(query)
    );
    const full = document.getElementById('fullProcessList');
    if (!full) return;
    const isProtected = p => PROTECTED_PIDS.has(p.pid) || PROTECTED_NAMES.has((p.name || '').toLowerCase());
    full.innerHTML = filtered.map(p => `
        <tr data-pid="${p.pid}">
            <td><span class="mono">${p.pid}</span></td>
            <td><strong>${p.name}</strong></td>
            <td>
                <div class="cell-bar-wrap">
                    <div class="cell-bar" style="width:${Math.min(p.cpu_percent || 0, 100)}%;background:${(p.cpu_percent || 0) > 50 ? 'var(--danger-color)' : 'var(--accent-color)'}"></div>
                </div>
                <span class="${(p.cpu_percent || 0) > 50 ? 'val-red bold' : ''}">${(p.cpu_percent || 0).toFixed(1)}%</span>
            </td>
            <td>${(p.memory_percent || 0).toFixed(1)}%</td>
            <td><span class="status-badge status-${(p.status || 'unknown').toLowerCase()}">${p.status || '—'}</span></td>
            <td>
                ${isProtected(p)
                    ? `<span class="proc-protected-badge">🛡 Protected</span>`
                    : `<button class="btn-danger" onclick="killProcess(${p.pid}, '${(p.name||'').replace(/'/g, "\\'")}')">⊘ Kill</button>`
                }
            </td>
        </tr>
    `).join('') || '<tr><td colspan="6" style="text-align:center;padding:32px;color:var(--text-secondary)">No matching processes found.</td></tr>';
}

// ——— Render Warnings ———
function renderWarnings(warnings) {
    allWarnings = warnings;
    const badge = document.getElementById('warningBadge');
    if (badge) badge.innerText = warnings.length;

    // Warning summary counts
    const criticals = warnings.filter(w => ['CPU', 'Memory', 'Disk'].includes(w.type));
    const highCpu   = warnings.filter(w => w.type === 'Process');
    const okCount   = 3 - Math.min(criticals.length, 3);

    const wcc = document.getElementById('warnCritCount');
    const whc = document.getElementById('warnHighCount');
    const wok = document.getElementById('warnOkCount');
    if (wcc) wcc.innerText = criticals.length;
    if (whc) whc.innerText = highCpu.length;
    if (wok) wok.innerText = Math.max(0, okCount);

    // Rule status badges
    const ruleMap = { CPU: 'ruleCpu', Memory: 'ruleMem', Disk: 'ruleDisk', Process: 'ruleProc' };
    // Reset all to OK
    Object.values(ruleMap).forEach(id => {
        const el = document.getElementById(id);
        if (el) { el.innerText = '✅ OK'; el.className = 'rule-status rule-ok'; }
    });
    warnings.forEach(w => {
        const el = document.getElementById(ruleMap[w.type] || '');
        if (el) { el.innerText = '⚠ ALERT'; el.className = 'rule-status rule-alert'; }
    });

    // Live feed
    const container = document.getElementById('warningContainer');
    if (!container) return;

    if (warnings.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">✅</div>
                <div class="empty-title">All Systems Operational</div>
                <div class="empty-desc">No active warnings. All metrics are within normal thresholds.</div>
            </div>`;
        return;
    }

    container.innerHTML = warnings.map(w => {
        const time = new Date(w.timestamp).toLocaleTimeString();
        const isCrit = ['CPU','Memory','Disk'].includes(w.type);
        return `
            <div class="warning-item ${isCrit ? 'warning-crit' : 'warning-proc'}">
                <div class="warn-icon">${isCrit ? '🔴' : '🟡'}</div>
                <div class="warn-content">
                    <div class="warn-title">${w.type} — ${w.level}</div>
                    <div class="warn-msg">${w.message}</div>
                </div>
                <div class="warn-time">${time}</div>
            </div>`;
    }).join('');
}

// ——— Main update function ———
function updateDashboard(stats, warnings) {
    const now = new Date().toLocaleTimeString();
    const lu = document.getElementById('lastUpdated');
    if (lu) lu.innerText = now;

    // CPU
    const cpuPct = stats.cpu.total;
    if (document.getElementById('cpuText'))  document.getElementById('cpuText').innerText  = `${cpuPct}%`;
    if (document.getElementById('cpuCores')) document.getElementById('cpuCores').innerText = `${stats.cpu.cores} Cores`;
    if (document.getElementById('sidebarCpu')) document.getElementById('sidebarCpu').innerText = `${cpuPct}%`;
    setBar('cpuBar', cpuPct); setBar('hCpuBar', cpuPct);
    const hcpu = document.getElementById('healthCpu');
    if (hcpu) { hcpu.innerText = cpuPct > 80 ? '⚠ HIGH' : '✅ OK'; hcpu.className = cpuPct > 80 ? 'val-red' : 'val-green'; }

    // Memory
    const memPct = stats.memory.percent;
    if (document.getElementById('memText'))  document.getElementById('memText').innerText  = `${memPct}%`;
    if (document.getElementById('memDesc'))  document.getElementById('memDesc').innerText  = `${fmtGB(stats.memory.used)} GB / ${fmtGB(stats.memory.total)} GB`;
    if (document.getElementById('sidebarMem')) document.getElementById('sidebarMem').innerText = `${memPct}%`;
    setBar('memBar', memPct); setBar('hMemBar', memPct);
    const hmem = document.getElementById('healthMem');
    if (hmem) { hmem.innerText = memPct > 85 ? '⚠ HIGH' : '✅ OK'; hmem.className = memPct > 85 ? 'val-red' : 'val-green'; }

    // Disk
    const diskPct = stats.disk.percent;
    if (document.getElementById('diskText'))  document.getElementById('diskText').innerText  = `${diskPct}%`;
    if (document.getElementById('diskDesc'))  document.getElementById('diskDesc').innerText  = `${fmtGB(stats.disk.used)} GB / ${fmtGB(stats.disk.total)} GB`;
    if (document.getElementById('sidebarDisk')) document.getElementById('sidebarDisk').innerText = `${diskPct}%`;
    setBar('diskBar', diskPct); setBar('hDiskBar', diskPct);
    const hdisk = document.getElementById('healthDisk');
    if (hdisk) { hdisk.innerText = diskPct > 90 ? '⚠ HIGH' : '✅ OK'; hdisk.className = diskPct > 90 ? 'val-red' : 'val-green'; }

    renderCores(stats.cpu.per_core || []);
    renderProcesses(stats.processes || []);
    renderWarnings(warnings || []);
}

// ——— INIT ———
document.addEventListener('DOMContentLoaded', () => {

    // Logout
    document.getElementById('logoutBtn')?.addEventListener('click', async () => {
        await fetch(`${API}/api/logout`, { method: 'POST' });
        window.location.href = 'login.html';
    });

    // Tab clicks
    document.querySelectorAll('.nav-links li').forEach(li => {
        li.addEventListener('click', () => switchTab(li.getAttribute('data-tab')));
    });

    // Process search
    document.getElementById('procSearch')?.addEventListener('input', renderFilteredProcesses);

    // Chatbot toggle
    document.getElementById('chatToggle')?.addEventListener('click', () => {
        const body = document.getElementById('chatBody');
        const chevron = document.querySelector('.chevron');
        if (!body) return;
        const isHidden = body.style.display === 'none';
        body.style.display = isHidden ? 'flex' : 'none';
        if (chevron) chevron.style.transform = isHidden ? 'rotate(180deg)' : '';
    });

    // Chatbot form
    document.getElementById('chatForm')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = document.getElementById('chatInput');
        const msgs  = document.getElementById('chatMessages');
        const text  = input.value.trim();
        if (!text) return;

        msgs.innerHTML += `<div class="msg user">${text}</div>`;
        input.value = '';
        msgs.scrollTop = msgs.scrollHeight;

        const typing = document.createElement('div');
        typing.className = 'msg bot typing';
        typing.innerHTML = '<span></span><span></span><span></span>';
        msgs.appendChild(typing);
        msgs.scrollTop = msgs.scrollHeight;

        try {
            const res  = await fetch(`${API}/api/chat`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            const data = await res.json();
            typing.remove();
            msgs.innerHTML += `<div class="msg bot">${data.response}</div>`;
        } catch {
            typing.remove();
            msgs.innerHTML += `<div class="msg bot" style="color:var(--danger-color)">⚠ Could not reach the AI assistant.</div>`;
        }
        msgs.scrollTop = msgs.scrollHeight;
    });

    // Fetch immediate system stats on load
    fetch(`${API}/api/stats`)
        .then(r => r.json())
        .then(data => {
            if (data && data.stats) updateDashboard(data.stats, data.warnings);
        })
        .catch(() => {});

    // Check URL parameters for tab and chat
    const params = new URLSearchParams(window.location.search);
    const tabParam = params.get('tab') || window.location.hash.replace('#', '');
    if (tabParam && TAB_CONFIG[tabParam]) {
        switchTab(tabParam);
    }
    if (params.get('chat') === 'open') {
        const body = document.getElementById('chatBody');
        const chevron = document.getElementById('chatChevron');
        if (body) body.style.display = 'flex';
        if (chevron) chevron.style.transform = 'rotate(180deg)';
        const msgs = document.getElementById('chatMessages');
        if (msgs && msgs.children.length === 0) {
            msgs.innerHTML = '<div class="msg bot">Hello! I am your AI Cloud System Monitor assistant. Ask me about CPU, memory, disk, or running processes!</div>';
        }
    }

    // Socket.IO connection
    let receivedSocketData = false;
    if (typeof io !== 'undefined') {
        try {
            const socket = io(API, { transports: ['websocket', 'polling'], timeout: 3000 });

            socket.on('connect', () => {
                const si = document.getElementById('statusIndicator');
                if (si) { si.innerHTML = '<span class="pulse-dot"></span> Socket Connected'; si.style.color = 'var(--success-color)'; }
            });

            socket.on('disconnect', () => {
                const si = document.getElementById('statusIndicator');
                if (si && !receivedSocketData) { si.innerHTML = '<span class="pulse-dot"></span> Live (HTTP)'; si.style.color = 'var(--success-color)'; }
            });

            // Full system update every 2s
            socket.on('system_data', ({ stats, warnings }) => {
                receivedSocketData = true;
                updateDashboard(stats, warnings);
            });

            // ——— process_update: fired immediately after a kill ———
            socket.on('process_update', (processes) => {
                renderProcesses(processes);
                const lu = document.getElementById('lastUpdated');
                if (lu) lu.innerText = new Date().toLocaleTimeString();
            });
        } catch(e) {
            console.log('Socket initialization skipped, relying on HTTP polling');
        }
    }

    // Serverless HTTP Polling Fallback (for Vercel & environments without persistent WebSockets)
    async function pollStats() {
        if (!receivedSocketData) {
            try {
                const res = await fetch(`${API}/api/stats`);
                if (res.ok) {
                    const data = await res.json();
                    if (data && data.stats) {
                        updateDashboard(data.stats, data.warnings || []);
                        const si = document.getElementById('statusIndicator');
                        if (si) { si.innerHTML = '<span class="pulse-dot"></span> Live'; si.style.color = 'var(--success-color)'; }
                    }
                }
            } catch (err) {
                // Backend may still be spinning up
            }
        }
    }
    // Initial fetch and continuous interval
    pollStats();
    setInterval(pollStats, 2000);
});
