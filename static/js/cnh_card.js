// Injects a CNH status card on Home (/) and fills with API data.
document.addEventListener('DOMContentLoaded', async () => {
  const path = location.pathname.replace(/\/+$/, '');
  const isHome = (path === '' || path === '/');
  if (!isHome) return;

  const container = document.querySelector('.container');
  if (!container) return;

  // Try to find first row to append; create one if not found
  let row = container.querySelector('.row');
  if (!row) {
    row = document.createElement('div');
    row.className = 'row g-3';
    container.prepend(row);
  }

  const col = document.createElement('div');
  col.className = 'col-12 col-sm-6 col-md-4 col-lg-3';
  col.innerHTML = `
    <div class="card shadow-sm">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-center">
          <h6 class="card-title mb-0">CNHs (Motoristas)</h6>
          <span class="badge text-bg-secondary" id="cnh-horizon">...</span>
        </div>
        <div class="mt-2 d-flex gap-2">
          <span class="badge text-bg-warning" id="cnh-a-vencer">--</span>
          <span class="badge text-bg-danger" id="cnh-vencidas">--</span>
        </div>
        <small class="text-muted">a vencer / vencidas</small>
      </div>
    </div>
  `;
  row.prepend(col);

  try {
    const r = await fetch('/api/cnh-stats');
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const j = await r.json();
    document.getElementById('cnh-a-vencer').textContent = j.cnh_a_vencer ?? '--';
    document.getElementById('cnh-vencidas').textContent = j.cnh_vencidas ?? '--';
    if (j.horizon_days != null) {
      document.getElementById('cnh-horizon').textContent = `<= ${j.horizon_days}d`;
    } else {
      document.getElementById('cnh-horizon').style.display = 'none';
    }
  } catch (e) {
    console.error('Falha ao carregar CNH stats:', e);
    document.getElementById('cnh-a-vencer').textContent = '?';
    document.getElementById('cnh-vencidas').textContent = '?';
    document.getElementById('cnh-horizon').style.display = 'none';
  }
});
