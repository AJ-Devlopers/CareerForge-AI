document.addEventListener('DOMContentLoaded', function () {

  // ── Elements (only on module1 page) ─────────────────────
  const fileInput  = document.getElementById('fileInput');
  const uploadZone = document.getElementById('uploadZone');
  const analyzeBtn = document.getElementById('analyzeBtn');
  const fileInfo   = document.getElementById('fileInfo');
  const fileName   = document.getElementById('fileName');

  // Guard — only run on module1 page
  if (!fileInput || !uploadZone) return;

  // ── File selected via click ──────────────────────────────
  fileInput.addEventListener('change', function () {
    var f = fileInput.files[0];
    if (!f) return;

    // Show filename immediately
    fileName.textContent = f.name;
    fileInfo.classList.add('show');
    analyzeBtn.disabled = true; // disable until upload animation done
    uploadZone.style.borderColor = 'var(--accent)';

    // Run the fake upload progress animation
    var wrap  = document.getElementById('uploadProgressWrap');
    var bar   = document.getElementById('uploadProgressBar');
    var label = document.getElementById('uploadProgressLabel');

    // Reset
    bar.style.width = '0%';
    wrap.classList.add('active');
    label.classList.add('active');
    label.textContent = 'Reading file... 0%';

    var pct      = 0;
    var fileSize = f.size;

    // Speed based on file size: small = fast, large = slower
    var speed = fileSize > 2 * 1024 * 1024 ? 8 : fileSize > 500 * 1024 ? 14 : 22;

    var interval = setInterval(function () {
      // Slow down near end for realism
      var increment = pct < 70 ? speed : pct < 90 ? Math.ceil(speed / 3) : 1;
      pct = Math.min(pct + increment, 99);

      bar.style.width = pct + '%';
      label.textContent = 'Reading file... ' + pct + '%';

      if (pct >= 99) {
        clearInterval(interval);

        // Jump to 100% and show done
        setTimeout(function () {
          bar.style.width = '100%';
          label.textContent = '✓ File ready — ' + (fileSize / 1024).toFixed(1) + ' KB';

          // Enable button + fade out bar after short delay
          setTimeout(function () {
            analyzeBtn.disabled = false;
            wrap.classList.remove('active');
            label.textContent = '✓ ' + f.name;
          }, 600);

        }, 120);
      }
    }, 40);
  });

  // ── Drag & drop ──────────────────────────────────────────
  uploadZone.addEventListener('dragover', function (e) {
    e.preventDefault();
    uploadZone.classList.add('drag-over');
  });

  uploadZone.addEventListener('dragleave', function () {
    uploadZone.classList.remove('drag-over');
  });

  uploadZone.addEventListener('drop', function (e) {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    const f = e.dataTransfer.files[0];
    if (f && f.type === 'application/pdf') {
      fileInput.files = e.dataTransfer.files;
      // Trigger change event so the progress animation runs
      fileInput.dispatchEvent(new Event('change'));
    } else {
      alert('Only PDF files are allowed.');
    }
  });

  // ── Smooth scroll (landing anchor links) ─────────────────
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

});


// ── Helpers ──────────────────────────────────────────────────
function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

async function animateSteps() {
  var steps = ['step1', 'step2', 'step3', 'step4'];
  for (var i = 0; i < steps.length; i++) {
    if (i > 0) {
      var prev = document.getElementById(steps[i - 1]);
      if (prev) prev.className = 'loading-step done';
    }
    var curr = document.getElementById(steps[i]);
    if (curr) curr.className = 'loading-step active';
    await sleep(900);
  }
}


// ── analyzeResume — called by onclick on the button ──────────
async function analyzeResume() {
  var fileInput  = document.getElementById('fileInput');
  var analyzeBtn = document.getElementById('analyzeBtn');

  if (!fileInput || !fileInput.files[0]) {
    alert('Please select a PDF file first.');
    return;
  }

  var file         = fileInput.files[0];
  var emptyState   = document.getElementById('emptyState');
  var loadingState = document.getElementById('loadingState');
  var results      = document.getElementById('results');

  if (emptyState)   emptyState.style.display = 'none';
  if (results)      results.classList.remove('show');
  if (loadingState) loadingState.classList.add('show');
  if (analyzeBtn)   analyzeBtn.disabled = true;

  ['step1','step2','step3','step4'].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.className = 'loading-step';
  });

  animateSteps();

  var formData = new FormData();
  formData.append('file', file);

  try {
    var res  = await fetch('/module1/upload', { method: 'POST', body: formData });
    var data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Server error');
    await sleep(400);
    if (loadingState) loadingState.classList.remove('show');
    renderResults(data);
  } catch (err) {
    if (loadingState) loadingState.classList.remove('show');
    if (emptyState)   emptyState.style.display = 'flex';
    alert('Error: ' + err.message);
  } finally {
    if (analyzeBtn) analyzeBtn.disabled = false;
  }
}


// ── renderResults ────────────────────────────────────────────
function renderResults(data) {
  var score   = data.ats_score || Math.min((data.total_skills || 0) * 8 + 20, 95);
  var scoreEl = document.getElementById('scoreNum');
  var fillEl  = document.getElementById('scoreFill');
  var badge   = document.getElementById('atsBadge');

  // Animate counter
  var current = 0;
  var timer = setInterval(function () {
    current += 2;
    if (scoreEl) scoreEl.textContent = current;
    if (current >= score) {
      if (scoreEl) scoreEl.textContent = score;
      clearInterval(timer);
    }
  }, 20);

  // Bar + badge
  setTimeout(function () {
    if (fillEl) fillEl.style.width = score + '%';
    if (score >= 75) {
      if (fillEl) fillEl.className = 'score-fill fill-green';
      if (badge)  { badge.className = 'ats-badge badge-excellent'; badge.textContent = 'Excellent'; }
    } else if (score >= 50) {
      if (fillEl) fillEl.className = 'score-fill fill-amber';
      if (badge)  { badge.className = 'ats-badge badge-good'; badge.textContent = 'Good'; }
    } else {
      if (fillEl) fillEl.className = 'score-fill fill-red';
      if (badge)  { badge.className = 'ats-badge badge-fair'; badge.textContent = 'Needs work'; }
    }
  }, 100);

  // Stats
  var skillCount = document.getElementById('skillCount');
  var topMatch   = document.getElementById('topMatch');
  if (skillCount) skillCount.textContent = data.total_skills || 0;
  if (topMatch)   topMatch.textContent   = ((data.roles && data.roles[0] && data.roles[0].match) || 0) + '%';

  // Skills
  var skillsGrid = document.getElementById('skillsGrid');
  if (skillsGrid) {
    skillsGrid.innerHTML = (data.skills_found || [])
      .map(function (s) { return '<span class="skill-tag">' + s + '</span>'; })
      .join('');
  }

  // Roles
  var rolesList = document.getElementById('rolesList');
  if (rolesList) {
    rolesList.innerHTML = (data.roles || []).map(function (r) {
      return (
        '<div class="role-item">' +
          '<div class="role-top">' +
            '<div class="role-name">' + r.role + '</div>' +
            '<div class="role-pct">' + r.match + '%</div>' +
          '</div>' +
          '<div class="role-bar"><div class="role-bar-fill" style="width:0%" data-width="' + r.match + '%"></div></div>' +
          '<div class="role-desc">' + (r.description || 'A strong role match based on your current skill profile.') + '</div>' +
          '<div class="role-learn">Learn next: <span>' + (r.learn_next || 'Docker, SQL, Git') + '</span></div>' +
          '<button class="role-select-btn" onclick="selectRole(\'' + r.role.replace(/'/g,"&#39;") + '\')">Start interview as ' + r.role + ' \u2192</button>' +
        '</div>'
      );
    }).join('');

    setTimeout(function () {
      document.querySelectorAll('.role-bar-fill').forEach(function (el) {
        el.style.width = el.getAttribute('data-width');
      });
    }, 200);
  }

  var results = document.getElementById('results');
  if (results) {
    results.classList.add('show');
    results.scrollIntoView({ behavior: 'smooth' });
  }
}


// ── selectRole ───────────────────────────────────────────────
function selectRole(role) {
  sessionStorage.setItem('selectedRole', role);
  window.location.href = '/module2?role=' + encodeURIComponent(role);
}