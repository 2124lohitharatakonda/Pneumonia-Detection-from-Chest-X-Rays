/* ============================================================
   PneumoDetect — Preview App (Single-Page Application)
   All logic: routing, auth simulation, mock AI prediction,
   drag-drop upload, history, animated stats.
   ============================================================ */

/* ── State ─────────────────────────────────────────────────── */
const state = {
  loggedIn: false,
  user: null,
  history: [],
  lastResult: null,
  lastImageSrc: null,
};

/* ── Mock users DB (localStorage-backed) ──────────────────── */
function getUsers() {
  try { return JSON.parse(localStorage.getItem('pd_users') || '[]'); }
  catch { return []; }
}
function saveUsers(u) { localStorage.setItem('pd_users', JSON.stringify(u)); }
function getHistory() {
  try { return JSON.parse(localStorage.getItem('pd_history_' + (state.user && state.user.email) || '') || '[]'); }
  catch { return []; }
}
function saveHistory(h) {
  if (!state.user) return;
  localStorage.setItem('pd_history_' + state.user.email, JSON.stringify(h));
}

/* ── Router ─────────────────────────────────────────────────── */
function showPage(name) {
  // Guard private pages
  if (['analyze','history','result'].includes(name) && !state.loggedIn) {
    flash('Please login to access that page.', 'warning');
    showPage('login');
    return;
  }

  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const target = document.getElementById('page-' + name);
  if (target) { target.classList.add('active'); window.scrollTo(0, 0); }

  // Highlight nav
  document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
  const navItem = document.getElementById('nav-' + name);
  if (navItem) navItem.classList.add('active');

  // Page-specific init
  if (name === 'home') animateStats();
  if (name === 'history') renderHistory();
  if (name === 'analyze') renderRecentList();
}

/* ── Flash Messages ─────────────────────────────────────────── */
function flash(msg, type = 'info') {
  const area = document.getElementById('flashArea');
  const div = document.createElement('div');
  div.className = `alert alert-${type} alert-dismissible fade show`;
  div.innerHTML = `${msg}<button type="button" class="close" data-dismiss="alert"><span>&times;</span></button>`;
  area.appendChild(div);
  setTimeout(() => { if (div.parentNode) div.parentNode.removeChild(div); }, 4000);
}

/* ── Navbar state ────────────────────────────────────────────── */
function updateNav() {
  const loggedOut = ['nav-register', 'nav-login'];
  const loggedIn  = ['nav-analyze', 'nav-history', 'nav-user'];

  if (state.loggedIn) {
    loggedOut.forEach(id => document.getElementById(id).classList.add('d-none'));
    loggedIn.forEach(id => document.getElementById(id).classList.remove('d-none'));
    document.getElementById('navUserName').textContent = state.user.name.split(' ')[0];
    document.getElementById('navUserEmail').textContent = state.user.email;
    document.getElementById('heroLoggedOut').classList.add('d-none');
    document.getElementById('heroLoggedIn').classList.remove('d-none');
  } else {
    loggedOut.forEach(id => document.getElementById(id).classList.remove('d-none'));
    loggedIn.forEach(id => document.getElementById(id).classList.add('d-none'));
    document.getElementById('heroLoggedOut').classList.remove('d-none');
    document.getElementById('heroLoggedIn').classList.add('d-none');
  }
}

/* ── Auth: Register ──────────────────────────────────────────── */
document.getElementById('registerForm').addEventListener('submit', function(e) {
  e.preventDefault();
  const name    = document.getElementById('reg-name').value.trim();
  const email   = document.getElementById('reg-email').value.trim().toLowerCase();
  const phone   = document.getElementById('reg-phone').value.trim();
  const pwd     = document.getElementById('reg-password').value;
  const confirm = document.getElementById('reg-confirm').value;

  if (!name)  { flash('Full name is required.', 'danger'); return; }
  if (!email || !email.includes('@')) { flash('Enter a valid email address.', 'danger'); return; }
  if (pwd.length < 8) { flash('Password must be at least 8 characters.', 'danger'); return; }
  if (pwd !== confirm) { flash('Passwords do not match.', 'danger'); return; }

  const users = getUsers();
  if (users.find(u => u.email === email)) {
    flash('An account with this email already exists. Please login.', 'danger'); return;
  }

  users.push({ name, email, phone, pwd });
  saveUsers(users);
  flash('Account created successfully! Please login.', 'success');
  this.reset();
  showPage('login');
});

/* ── Auth: Login ─────────────────────────────────────────────── */
document.getElementById('loginForm').addEventListener('submit', function(e) {
  e.preventDefault();
  const email = document.getElementById('login-email').value.trim().toLowerCase();
  const pwd   = document.getElementById('login-password').value;

  if (!email || !pwd) { flash('Please fill in all fields.', 'danger'); return; }

  // Demo shortcut: any email/password works if user has registered, OR allow demo login
  const users = getUsers();
  let user = users.find(u => u.email === email && u.pwd === pwd);

  if (!user) {
    // Allow demo account always
    if (email === 'demo@pneumodetect.ai' || pwd === 'demo1234') {
      user = { name: 'Chandra Sekhar Varma', email, phone: '+91 9876543210' };
    } else {
      flash('Invalid email or password. Try demo@pneumodetect.ai / demo1234', 'danger');
      return;
    }
  }

  state.loggedIn = true;
  state.user = user;
  state.history = getHistory();
  updateNav();
  this.reset();
  flash(`Welcome back, ${user.name.split(' ')[0]}!`, 'success');
  showPage('analyze');
});

/* ── Auth: Logout ────────────────────────────────────────────── */
function doLogout() {
  state.loggedIn = false;
  state.user = null;
  state.history = [];
  state.lastResult = null;
  updateNav();
  flash('You have been logged out.', 'info');
  showPage('home');
}

/* ── Password Toggle ─────────────────────────────────────────── */
function togglePwd(inputId, iconId) {
  const input = document.getElementById(inputId);
  const icon  = document.getElementById(iconId);
  if (input.type === 'password') {
    input.type = 'text';
    icon.classList.replace('fa-eye', 'fa-eye-slash');
  } else {
    input.type = 'password';
    icon.classList.replace('fa-eye-slash', 'fa-eye');
  }
}

/* ── File Upload ─────────────────────────────────────────────── */
function handleFile(input) {
  const file = input.files[0];
  if (!file) return;

  if (file.size > 5 * 1024 * 1024) {
    flash('File too large. Maximum size is 5 MB.', 'danger');
    input.value = '';
    return;
  }
  if (!['image/jpeg', 'image/jpg', 'image/png'].includes(file.type)) {
    flash('Invalid file type. Please upload a JPG or PNG image.', 'danger');
    input.value = '';
    return;
  }

  const reader = new FileReader();
  reader.onload = function(ev) {
    state.lastImageSrc = ev.target.result;
    document.getElementById('imagePreview').src = ev.target.result;
    document.getElementById('previewFilename').textContent = file.name + ' (' + (file.size / 1024).toFixed(1) + ' KB)';
    document.getElementById('previewContainer').classList.remove('d-none');
    document.getElementById('uploadArea').classList.add('has-file');
  };
  reader.readAsDataURL(file);
}

/* ── Drag & Drop ─────────────────────────────────────────────── */
(function setupDragDrop() {
  const area = document.getElementById('uploadArea');
  if (!area) return;

  area.addEventListener('dragover', e => {
    e.preventDefault();
    area.classList.add('drag-over');
  });
  area.addEventListener('dragleave', () => area.classList.remove('drag-over'));
  area.addEventListener('drop', e => {
    e.preventDefault();
    area.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) {
      const dt = new DataTransfer();
      dt.items.add(file);
      const inp = document.getElementById('xrayFile');
      inp.files = dt.files;
      handleFile(inp);
    }
  });
})();

/* ── Mock AI Prediction ──────────────────────────────────────── */
function mockPredict(modelName) {
  // Weighted random: ~60% pneumonia, ~40% normal (mimics real dataset imbalance)
  const isPneumonia = Math.random() < 0.60;

  let pneumoniaScore, normalScore;
  if (isPneumonia) {
    // High confidence pneumonia
    pneumoniaScore = 0.88 + Math.random() * 0.11;   // 0.88–0.99
    normalScore    = 1 - pneumoniaScore;
  } else {
    // High confidence normal
    normalScore    = 0.82 + Math.random() * 0.15;    // 0.82–0.97
    pneumoniaScore = 1 - normalScore;
  }

  pneumoniaScore = parseFloat(pneumoniaScore.toFixed(4));
  normalScore    = parseFloat(normalScore.toFixed(4));

  const result     = isPneumonia ? 'PNEUMONIA' : 'NORMAL';
  const confidence = isPneumonia ? pneumoniaScore : normalScore;

  const precautions = {
    PNEUMONIA: [
      'Consult a doctor or pulmonologist immediately.',
      'Rest and stay well-hydrated.',
      'Take prescribed antibiotics or antivirals as directed.',
      'Monitor oxygen saturation levels.',
      'Avoid smoking and second-hand smoke.',
      'Follow up with a chest X-ray after treatment.',
    ],
    NORMAL: [
      'No pneumonia detected — chest X-ray appears normal.',
      'Continue regular health check-ups.',
      'Maintain a balanced diet and exercise routine.',
      'Avoid exposure to respiratory irritants.',
      'Consult a physician if symptoms persist.',
    ],
  };

  return {
    result,
    confidence: parseFloat(confidence.toFixed(4)),
    model_used: modelName,
    raw_scores: {
      PNEUMONIA: pneumoniaScore,
      NORMAL:    normalScore,
    },
    precautions: precautions[result],
  };
}

/* ── Run Analysis ────────────────────────────────────────────── */
function runAnalysis() {
  if (!state.lastImageSrc) {
    flash('Please upload a chest X-ray image first.', 'warning');
    return;
  }

  const modelChoice = document.getElementById('modelChoice').value;
  const modelLabel  = modelChoice === 'resnet50' ? 'ResNet50' : 'MobileNetV2';

  // Show loading overlay
  const overlay = document.getElementById('loadingOverlay');
  overlay.classList.remove('d-none');
  overlay.style.display = 'flex';

  // Simulate inference delay (1.5–3 seconds)
  const delay = 1500 + Math.random() * 1500;
  setTimeout(() => {
    overlay.classList.add('d-none');
    overlay.style.display = '';

    const prediction = mockPredict(modelLabel);
    state.lastResult  = prediction;

    // Save to history
    const entry = {
      id:         Date.now(),
      date:       new Date().toLocaleString(),
      imageSrc:   state.lastImageSrc,
      result:     prediction.result,
      confidence: prediction.confidence,
      model:      prediction.model_used,
      raw_scores: prediction.raw_scores,
    };
    state.history.unshift(entry);
    if (state.history.length > 20) state.history.pop();
    saveHistory(state.history);

    // Render result page
    renderResult(prediction, state.lastImageSrc);
    showPage('result');
  }, delay);
}

/* ── Render Result Page ──────────────────────────────────────── */
function renderResult(pred, imgSrc) {
  const isPneumonia = pred.result === 'PNEUMONIA';
  const pct = (pred.confidence * 100).toFixed(1);
  const pneumoniaPct = (pred.raw_scores.PNEUMONIA * 100).toFixed(1);
  const normalPct    = (pred.raw_scores.NORMAL * 100).toFixed(1);

  // Banner
  const banner = document.getElementById('resultBanner');
  if (isPneumonia) {
    banner.innerHTML = `
      <div class="alert alert-danger shadow-sm d-flex align-items-center py-4" role="alert">
        <i class="fas fa-exclamation-circle fa-3x mr-4"></i>
        <div>
          <h4 class="font-weight-bold mb-1">Pneumonia Detected</h4>
          <p class="mb-0">The AI model has identified signs of pneumonia in the uploaded X-ray with <strong>${pct}%</strong> confidence.</p>
        </div>
      </div>`;
  } else {
    banner.innerHTML = `
      <div class="alert alert-success shadow-sm d-flex align-items-center py-4" role="alert">
        <i class="fas fa-check-circle fa-3x mr-4"></i>
        <div>
          <h4 class="font-weight-bold mb-1">No Pneumonia Detected</h4>
          <p class="mb-0">The chest X-ray appears <strong>normal</strong>. No signs of pneumonia were detected (<strong>${pct}%</strong> confidence).</p>
        </div>
      </div>`;
  }

  // Image
  document.getElementById('resultImage').src = imgSrc;

  // Primary confidence bar
  document.getElementById('primaryLabel').textContent = pred.result;
  const primaryBadge = document.getElementById('primaryBadge');
  primaryBadge.textContent = pct + '%';
  primaryBadge.className = `badge badge-pill px-3 py-2 badge-${isPneumonia ? 'danger' : 'success'}`;
  const primaryBar = document.getElementById('primaryBar');
  primaryBar.className = `progress-bar progress-bar-striped progress-bar-animated bg-${isPneumonia ? 'danger' : 'success'}`;
  setTimeout(() => { primaryBar.style.width = pct + '%'; }, 100);

  // Pneumonia bar
  document.getElementById('pneumoniaScoreLabel').textContent = pneumoniaPct + '%';
  setTimeout(() => { document.getElementById('pneumoniaBar').style.width = pneumoniaPct + '%'; }, 200);

  // Normal bar
  document.getElementById('normalScoreLabel').textContent = normalPct + '%';
  setTimeout(() => { document.getElementById('normalBar').style.width = normalPct + '%'; }, 300);

  // Meta
  document.getElementById('modelUsedLabel').textContent = pred.model_used;
  document.getElementById('confidenceLabel').textContent = pct + '%';

  // Guidance
  const guidanceHeader = document.getElementById('guidanceHeader');
  const guidanceBox    = document.getElementById('guidanceBox');
  guidanceHeader.innerHTML = `<i class="fas fa-${isPneumonia ? 'notes-medical text-danger' : 'heartbeat text-success'} mr-2"></i>${isPneumonia ? 'Clinical Guidance — Pneumonia Detected' : 'Clinical Guidance — No Pneumonia Detected'}`;
  guidanceBox.className = `precaution-box border-left pl-3 border-${isPneumonia ? 'danger' : 'success'}`;
  if (isPneumonia) {
    guidanceBox.innerHTML = `<p class="font-weight-bold text-danger mb-2">Recommended Actions:</p><ol class="mb-0">` +
      pred.precautions.map(p => `<li class="mb-1">${p}</li>`).join('') + `</ol>`;
  } else {
    guidanceBox.innerHTML = `<ul class="list-unstyled mb-0">` +
      pred.precautions.map(p => `<li class="mb-2"><i class="fas fa-check text-success mr-2"></i>${p}</li>`).join('') + `</ul>`;
  }
}

/* ── Render History ──────────────────────────────────────────── */
function renderHistory() {
  const grid = document.getElementById('historyGrid');
  const hist = state.history;
  document.getElementById('histCount').textContent = hist.length;

  if (!hist.length) {
    grid.innerHTML = `
      <div class="col-12 text-center py-5">
        <i class="fas fa-history fa-4x text-muted mb-3"></i>
        <h5 class="text-muted">No predictions yet</h5>
        <p class="text-muted">Upload a chest X-ray to get started.</p>
        <a href="#" onclick="showPage('analyze')" class="btn btn-primary mt-2">
          <i class="fas fa-x-ray mr-2"></i>Analyze X-Ray
        </a>
      </div>`;
    return;
  }

  grid.innerHTML = hist.map((entry, idx) => {
    const isPneumonia = entry.result === 'PNEUMONIA';
    const pct = (entry.confidence * 100).toFixed(1);
    return `
      <div class="col-lg-4 col-md-6 mb-4">
        <div class="card border-0 shadow-sm h-100">
          <div class="card-img-top" style="height:180px;overflow:hidden;background:#f8f9fa;display:flex;align-items:center;justify-content:center;">
            <img src="${entry.imageSrc}" alt="X-Ray" style="max-height:180px;max-width:100%;object-fit:cover;"/>
          </div>
          <div class="card-body p-3">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <span class="badge badge-${isPneumonia ? 'danger' : 'success'} badge-pill px-3 py-2 font-weight-bold">
                <i class="fas fa-${isPneumonia ? 'exclamation-circle' : 'check-circle'} mr-1"></i>${entry.result}
              </span>
              <small class="text-muted">#${hist.length - idx}</small>
            </div>
            <div class="mb-2">
              <div class="d-flex justify-content-between mb-1">
                <small class="font-weight-bold">Confidence</small>
                <small>${pct}%</small>
              </div>
              <div class="progress" style="height:6px;">
                <div class="progress-bar bg-${isPneumonia ? 'danger' : 'success'}" style="width:${pct}%;"></div>
              </div>
            </div>
            <small class="text-muted d-block"><i class="fas fa-network-wired mr-1"></i>${entry.model}</small>
            <small class="text-muted d-block"><i class="fas fa-clock mr-1"></i>${entry.date}</small>
          </div>
        </div>
      </div>`;
  }).join('');
}

/* ── Render Recent List (on Analyze page) ────────────────────── */
function renderRecentList() {
  const list = document.getElementById('recentList');
  const hist = state.history.slice(0, 5);
  if (!hist.length) {
    list.innerHTML = `<div class="list-group-item text-muted text-center py-4"><i class="fas fa-inbox fa-2x mb-2 d-block"></i>No history yet</div>`;
    return;
  }
  list.innerHTML = hist.map(entry => {
    const isPneumonia = entry.result === 'PNEUMONIA';
    const pct = (entry.confidence * 100).toFixed(1);
    return `
      <div class="list-group-item list-group-item-action py-2 px-3">
        <div class="d-flex align-items-center">
          <img src="${entry.imageSrc}" alt="" style="width:42px;height:42px;object-fit:cover;border-radius:6px;margin-right:12px;"/>
          <div class="flex-grow-1 min-width-0">
            <div class="d-flex justify-content-between align-items-center">
              <span class="badge badge-${isPneumonia ? 'danger' : 'success'} badge-pill">${entry.result}</span>
              <small class="text-muted">${pct}%</small>
            </div>
            <small class="text-muted">${entry.date}</small>
          </div>
        </div>
      </div>`;
  }).join('');
}

/* ── Animated Stats Counter ──────────────────────────────────── */
function animateStats() {
  const targets = [
    { id: 'stat1', target: 99.19, suffix: '%', decimals: 2 },
    { id: 'stat2', target: 97.25, suffix: '%', decimals: 2 },
    { id: 'stat3', target: 98.21, suffix: '%', decimals: 2 },
    { id: 'stat4', target: 98.24, suffix: '%', decimals: 2 },
  ];
  targets.forEach(({ id, target, suffix, decimals }) => {
    const el = document.getElementById(id);
    if (!el) return;
    let current = 0;
    const step = target / 60;
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = current.toFixed(decimals) + suffix;
      if (current >= target) clearInterval(timer);
    }, 16);
  });
}

/* ── Init ────────────────────────────────────────────────────── */
(function init() {
  updateNav();
  showPage('home');
})();
