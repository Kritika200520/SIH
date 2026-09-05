import os

app_js_path = r'c:\Users\karti\OneDrive\Desktop\SIH-main\dashboard\app.js'
with open(app_js_path, 'r', encoding='utf-8') as f:
    content = f.read()

sw_code = """
// Cloud Offline Sync & Service Worker Registration
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then(reg => console.log('Offline Sync Service Worker Registered'))
      .catch(err => console.error('SW Registration Failed', err));
  });
}

function updateNetworkStatus() {
  const syncChip = document.getElementById('stat-sync');
  const chipContainer = document.getElementById('sync-chip');
  if (!syncChip) return;
  
  if (navigator.onLine) {
    syncChip.innerHTML = '[PASS] CLOUD ONLINE';
    syncChip.className = 'chip-v text-safe';
    chipContainer.style.borderColor = 'rgba(16, 185, 129, 0.4)';
  } else {
    syncChip.innerHTML = '[BLOCK] OFFLINE (CACHED)';
    syncChip.className = 'chip-v text-danger';
    chipContainer.style.borderColor = 'rgba(255, 42, 95, 0.4)';
  }
}
window.addEventListener('online', updateNetworkStatus);
window.addEventListener('offline', updateNetworkStatus);
document.addEventListener('DOMContentLoaded', updateNetworkStatus);
"""

if 'updateNetworkStatus' not in content:
    content = content.replace('let audioElement = null;', 'let audioElement = null;\n' + sw_code)

old_fetch = """async function fetchDashboardStatus() {
  try {
    const res = await fetch("/api/dashboard/status");
    const data = await res.json();
    renderDashboard(data);
  } catch (err) {
    console.error("API fetch error:", err);
  }
}"""

new_fetch = """async function fetchDashboardStatus() {
  try {
    const res = await fetch("/api/dashboard/status");
    const data = await res.json();
    // Save to local IndexedDB/localStorage for offline fallback
    localStorage.setItem("bhoomi_offline_cache", JSON.stringify(data));
    renderDashboard(data);
  } catch (err) {
    console.error("API fetch error (Network Offline):", err);
    // Cloud Sync Offline Fallback
    const cachedData = localStorage.getItem("bhoomi_offline_cache");
    if (cachedData) {
      console.warn("Loading dashboard from local edge cache");
      renderDashboard(JSON.parse(cachedData));
    }
  }
}"""

content = content.replace(old_fetch, new_fetch)

with open(app_js_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated successfully")

