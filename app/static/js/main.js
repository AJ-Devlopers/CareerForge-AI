// ============================================================
// CareerForge AI — main.js
// ============================================================

document.addEventListener('DOMContentLoaded', function () {

  // ── Module 1 — restore results from sessionStorage ───────
  const savedResult = sessionStorage.getItem('cf-resume-result');
  const resultsEl   = document.getElementById('results');
  const emptyEl     = document.getElementById('emptyState');

  if (savedResult && resultsEl) {
    try {
      const data = JSON.parse(savedResult);
      if (emptyEl) emptyEl.style.display = 'none';
      renderResults(data);
    } catch(e) {
      sessionStorage.removeItem('cf-resume-result');
    }
  }

  // ── Module 1 — file upload ────────────────────────────────
  const fileInput  = document.getElementById('fileInput');
  const uploadZone = document.getElementById('uploadZone');
  const analyzeBtn = document.getElementById('analyzeBtn');
  const fileInfo   = document.getElementById('fileInfo');
  const fileName   = document.getElementById('fileName');

  if (fileInput && uploadZone) {
    fileInput.addEventListener('change', function () {
      const f = fileInput.files[0];
      if (!f) return;

      fileName.textContent = f.name;
      fileInfo.classList.add('show');
      analyzeBtn.disabled = true;
      uploadZone.style.borderColor = 'var(--accent)';

      const wrap  = document.getElementById('uploadProgressWrap');
      const bar   = document.getElementById('uploadProgressBar');
      const label = document.getElementById('uploadProgressLabel');

      if (wrap && bar && label) {
        bar.style.width = '0%';
        wrap.classList.add('active');
        label.classList.add('active');
        label.textContent = 'Reading file... 0%';

        let pct = 0;
        const interval = setInterval(function () {
          pct = Math.min(pct + 5, 99);
          bar.style.width = pct + '%';
          label.textContent = 'Reading file... ' + pct + '%';
          if (pct >= 99) {
            clearInterval(interval);
            setTimeout(function () {
              bar.style.width = '100%';
              label.textContent = '✓ File ready';
              analyzeBtn.disabled = false;
            }, 200);
          }
        }, 40);
      } else {
        analyzeBtn.disabled = false;
      }
    });

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
        fileInput.dispatchEvent(new Event('change'));
      } else {
        alert('Only PDF files are allowed.');
      }
    });
  }

  // ── Custom role — Enter key ───────────────────────────────
  const ci = document.getElementById('customRoleInput');
  if (ci) {
    ci.addEventListener('keypress', function (e) {
      if (e.key === 'Enter') analyzeCustomRole();
    });
  }

  // ── Update reset button state on load ─────────────────────
  updateResetBtn();
});


// ============================================================
// RESET BUTTON STATE
// ============================================================
function updateResetBtn() {
  const sidebarBtn = document.getElementById('resetSessionBtn');
  const topBtn     = document.getElementById('topResetBtn');

  const hasData = !!(
    sessionStorage.getItem('cf-resume-result') ||
    sessionStorage.getItem('cf-attempt-history') ||
    sessionStorage.getItem('selectedRole')
  );

  if (sidebarBtn) {
    sidebarBtn.classList.toggle('reset-btn--active', hasData);
    sidebarBtn.title = hasData ? 'Reset everything' : 'No active session';
  }
  if (topBtn) {
    topBtn.classList.toggle('active', hasData);
    topBtn.style.display = 'flex';
    topBtn.title = hasData ? 'Reset everything' : 'No active session';
  }
}


// ============================================================
// RESET SESSION — clears EVERYTHING frontend + backend
// ============================================================
async function resetSession() {
  if (!confirm('Reset everything and start fresh?\n\nThis will clear your resume, all interview attempts, and scores.')) return;

  // ── 1. Clear ALL frontend storage immediately ──
  sessionStorage.clear();
  localStorage.removeItem('cf-theme');  // keep theme? optional - remove if you want full wipe
  // Actually keep theme pref, only wipe data keys
  const theme = localStorage.getItem('cf-theme');
  localStorage.clear();
  if (theme) localStorage.setItem('cf-theme', theme);

  // ── 2. Clear ALL backend session via API ──
  try {
    await fetch('/session/clear-all', { method: 'POST' });
  } catch(e) {
    console.warn('Could not clear server session:', e);
  }

  // ── 3. Update UI ──
  updateResetBtn();

  // ── 4. Redirect to homepage (fresh start) ──
  window.location.href = '/';
}


// ============================================================
// HELPERS
// ============================================================
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function animateNumber(el, target, duration) {
  let current = 0;
  const step  = Math.ceil(target / (duration / 20));
  const timer = setInterval(function () {
    current = Math.min(current + step, target);
    el.textContent = current;
    if (current >= target) clearInterval(timer);
  }, 20);
}

function animateCircle(score) {
  const circle = document.getElementById('progressCircle');
  const label  = document.getElementById('circleLabel');
  if (!circle || !label) return;

  const r             = 52;
  const circumference = 2 * Math.PI * r;

  let color = 'var(--red)';
  if (score >= 75)     color = 'var(--green)';
  else if (score >= 50) color = 'var(--amber)';

  circle.style.stroke = color;

  let current = 0;
  const step  = score / 60;
  const timer = setInterval(function () {
    current = Math.min(current + step, score);
    const offset = circumference - (current / 100) * circumference;
    circle.style.strokeDashoffset = offset;
    label.textContent = Math.round(current);
    if (current >= score) clearInterval(timer);
  }, 16);
}


// ============================================================
// MODULE 1 — ANALYZE RESUME
// ============================================================
async function analyzeResume() {
  const fileInput  = document.getElementById('fileInput');
  const analyzeBtn = document.getElementById('analyzeBtn');

  if (!fileInput || !fileInput.files[0]) {
    alert('Please upload a PDF file first.');
    return;
  }

  const emptyEl   = document.getElementById('emptyState');
  const loadingEl = document.getElementById('loadingState');
  const resultsEl = document.getElementById('results');

  if (emptyEl)    emptyEl.style.display = 'none';
  if (resultsEl)  resultsEl.classList.remove('show');
  if (loadingEl)  loadingEl.classList.add('show');
  if (analyzeBtn) analyzeBtn.disabled = true;

  const steps = ['step1', 'step2', 'step3', 'step4'];
  steps.forEach(function (s, i) {
    const el = document.getElementById(s);
    if (!el) return;
    el.className = 'loading-step';
    setTimeout(function () {
      if (i > 0) {
        const prev = document.getElementById(steps[i - 1]);
        if (prev) prev.className = 'loading-step done';
      }
      el.className = 'loading-step active';
    }, i * 900);
  });

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);

  try {
    const res  = await fetch('/module1/upload', { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || 'Server error');

    if (loadingEl) loadingEl.classList.remove('show');

    const last = document.getElementById('step4');
    if (last) last.className = 'loading-step done';

    sessionStorage.setItem('cf-resume-result', JSON.stringify(data));
    updateResetBtn();

    renderResults(data);

  } catch (err) {
    if (loadingEl) loadingEl.classList.remove('show');
    if (emptyEl)   emptyEl.style.display = 'flex';
    alert('Analysis failed: ' + err.message);
  } finally {
    if (analyzeBtn) analyzeBtn.disabled = false;
  }
}


// ============================================================
// MODULE 1 — RENDER RESULTS
// ============================================================
function renderResults(data) {

  const score    = data.ats_score || 0;
  const grade    = data.grade     || '';
  const feedback = data.feedback  || '';

  const scoreNumEl = document.getElementById('scoreNum');
  const atsBadgeEl = document.getElementById('atsBadge');
  const feedbackEl = document.getElementById('atsFeedback');

  if (scoreNumEl) animateNumber(scoreNumEl, score, 800);
  setTimeout(function () { animateCircle(score); }, 200);

  if (atsBadgeEl) {
    atsBadgeEl.textContent = grade;
    atsBadgeEl.className   = 'ats-badge ' + (
      score >= 75 ? 'badge-excellent' : score >= 50 ? 'badge-good' : 'badge-fair'
    );
  }

  if (feedbackEl) feedbackEl.textContent = feedback;

  const skills = data.skills_found || [];
  const roles  = data.roles        || [];

  const skillCountEl = document.getElementById('skillCount');
  const topMatchEl   = document.getElementById('topMatch');

  if (skillCountEl) skillCountEl.textContent = skills.length;
  if (topMatchEl)   topMatchEl.textContent   = (roles[0]?.match || 0) + '%';

  renderBreakdown(data.breakdown || {}, data);
  renderImprovements(data.improvements || []);

  const skillsGrid = document.getElementById('skillsGrid');
  if (skillsGrid) {
    skillsGrid.innerHTML = skills.length
      ? skills.map(s => `<span class="skill-tag">${s}</span>`).join('')
      : `<span class="no-data">No skills detected.</span>`;
  }

  const rolesList = document.getElementById('rolesList');
  if (rolesList) {
    rolesList.innerHTML = roles.length
      ? roles.map(function (r) {
          const pct     = r.match || 0;
          const color   = pct >= 60 ? 'var(--green)' : pct >= 35 ? 'var(--amber)' : 'var(--red)';
          const barId   = 'bar-' + r.role.replace(/\s+/g, '_');
          const matched = r.matched_skills || [];
          const missing = r.missing_skills || [];

          const allRequired = [
            ...matched.map(s => ({ name: s, matched: true })),
            ...missing.map(s => ({ name: s, matched: false }))
          ];

          const skillTagsHtml = allRequired.length
            ? allRequired.map(function (s) {
                const label = typeof s.name === 'string'
                  ? s.name.charAt(0).toUpperCase() + s.name.slice(1)
                  : s.name;
                return `<span class="skill-tag ${s.matched ? 'skill-match' : ''}">${label}</span>`;
              }).join('')
            : '<span class="no-data">No skill data</span>';

          return `
            <div class="role-item-card">
              <div class="role-card-top">
                <div>
                  <div class="role-name">${r.role}</div>
                  <div class="role-card-sublabel">Compatibility match</div>
                </div>
                <div class="role-pct" style="color:${color}">${pct}%</div>
              </div>
              <div class="role-bar">
                <div class="role-bar-fill" id="${barId}" style="width:0%;background:${color}"></div>
              </div>
              <div class="section-head" style="margin-top:1rem">Required skills</div>
              <div class="skills-grid" style="margin-bottom:1rem">
                ${skillTagsHtml}
              </div>
              <button class="role-select-btn" onclick="selectRole('${r.role}')">
                Start Interview as ${r.role} →
              </button>
            </div>`;
        }).join('')
      : `<div class="no-data">No role matches found.</div>`;

    requestAnimationFrame(function () {
      setTimeout(function () {
        roles.forEach(function (r) {
          const el = document.getElementById('bar-' + r.role.replace(/\s+/g, '_'));
          if (el) el.style.width = (r.match || 0) + '%';
        });
      }, 120);
    });
  }

  const resultsEl = document.getElementById('results');
  if (resultsEl) {
    resultsEl.classList.add('show');
    resultsEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}


// ============================================================
// BREAKDOWN — expandable cards with tick/cross
// ============================================================
function renderBreakdown(breakdown, data) {
  const el = document.getElementById('atsBreakdown');
  if (!el) return;

  const labels = {
    skills_keywords:  'Skills & Keywords',
    resume_structure: 'Resume Structure',
    quantification:   'Quantification',
    action_verbs:     'Action Verbs',
    education:        'Education',
    role_match:       'Role Match',
    ai_analysis:      'AI Analysis'
  };

  const keys = Object.keys(labels);
  if (!keys.some(k => breakdown[k])) { el.style.display = 'none'; return; }

  el.style.display = 'block';
  el.innerHTML = keys.map(function (k) {
    const item  = breakdown[k] || {};
    const score = item.score || 0;
    const max   = item.max   || 10;
    const pct   = Math.round((score / max) * 100);
    const color = pct >= 70 ? 'var(--green)' : pct >= 45 ? 'var(--amber)' : 'var(--red)';

    let subChecksHtml = '';

    if (k === 'resume_structure') {
      const found   = item.sections_found   || [];
      const missing = item.sections_missing || [];
      const all = ['contact','education','experience','skills','projects','achievements'];
      subChecksHtml = `<div class="bd-subchecks">` +
        all.map(function (s) {
          const present = found.includes(s) || (!missing.includes(s) && found.length > 0);
          return `
            <div class="bd-subcheck-item">
              <span class="bd-subcheck-icon ${present ? 'ok' : 'fail'}">${present ? '✓' : '✗'}</span>
              <span class="bd-subcheck-label">${s.charAt(0).toUpperCase() + s.slice(1)}</span>
            </div>`;
        }).join('') + `</div>`;

    } else if (k === 'skills_keywords') {
      const tier1 = item.tier1_found || [];
      const tier2 = item.tier2_found || [];
      subChecksHtml = `<div class="bd-subchecks">`;
      if (tier1.length) subChecksHtml += tier1.map(s =>
        `<div class="bd-subcheck-item"><span class="bd-subcheck-icon ok">✓</span><span class="bd-subcheck-label">${s}</span></div>`
      ).join('');
      if (tier2.length) subChecksHtml += tier2.map(s =>
        `<div class="bd-subcheck-item"><span class="bd-subcheck-icon warn">✓</span><span class="bd-subcheck-label">${s}</span></div>`
      ).join('');
      if (!tier1.length && !tier2.length) subChecksHtml +=
        `<div class="bd-subcheck-item"><span class="bd-subcheck-icon fail">✗</span><span class="bd-subcheck-label">No matching skills found</span></div>`;
      subChecksHtml += `</div>`;

    } else if (k === 'action_verbs') {
      const strong = item.strong_count || 0;
      const weak   = item.weak_count   || 0;
      subChecksHtml = `<div class="bd-subchecks">
        <div class="bd-subcheck-item">
          <span class="bd-subcheck-icon ${strong > 0 ? 'ok' : 'fail'}">${strong > 0 ? '✓' : '✗'}</span>
          <span class="bd-subcheck-label">${strong} strong action verbs found</span>
        </div>
        <div class="bd-subcheck-item">
          <span class="bd-subcheck-icon ${weak === 0 ? 'ok' : 'fail'}">${weak === 0 ? '✓' : '✗'}</span>
          <span class="bd-subcheck-label">${weak} weak verbs ${weak === 0 ? '— great!' : '— replace these'}</span>
        </div>
      </div>`;

    } else if (k === 'quantification') {
      const metrics = item.metrics_found || 0;
      const verbs   = item.impact_verbs  || 0;
      subChecksHtml = `<div class="bd-subchecks">
        <div class="bd-subcheck-item">
          <span class="bd-subcheck-icon ${metrics >= 5 ? 'ok' : metrics >= 1 ? 'warn' : 'fail'}">${metrics >= 1 ? '✓' : '✗'}</span>
          <span class="bd-subcheck-label">${metrics} numbers / metrics found</span>
        </div>
        <div class="bd-subcheck-item">
          <span class="bd-subcheck-icon ${verbs >= 3 ? 'ok' : verbs >= 1 ? 'warn' : 'fail'}">${verbs >= 1 ? '✓' : '✗'}</span>
          <span class="bd-subcheck-label">${verbs} impact verbs found</span>
        </div>
      </div>`;

    } else {
      subChecksHtml = item.details
        ? `<div class="bd-card-detail">${item.details}</div>` : '';
    }

    return `
      <div class="bd-card" onclick="toggleBdCard(this)">
        <div class="bd-card-header">
          <div class="bd-card-left">
            <div class="bd-card-label">${labels[k]}</div>
            <div class="bd-card-bar-wrap">
              <div class="bd-card-bar-fill" data-width="${pct}%" style="width:0%;background:${color}"></div>
            </div>
          </div>
          <div class="bd-card-right">
            <span class="bd-card-score" style="color:${color}">${score}</span>
            <span class="bd-card-max">/${max}</span>
            <svg class="bd-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </div>
        </div>
        <div class="bd-card-body">
          ${item.details ? `<div class="bd-card-detail" style="margin-bottom:0.6rem">${item.details}</div>` : ''}
          ${subChecksHtml}
        </div>
      </div>`;
  }).join('');

  requestAnimationFrame(function () {
    setTimeout(function () {
      el.querySelectorAll('.bd-card-bar-fill').forEach(function (bar) {
        bar.style.width = bar.dataset.width;
      });
    }, 150);
  });
}

function toggleBdCard(card) {
  card.classList.toggle('open');
}

function renderImprovements(improvements) {
  const block = document.getElementById('improvementsBlock');
  const el    = document.getElementById('improvementsList');
  if (!el || !block) return;

  if (!improvements || !improvements.length) {
    block.style.display = 'none';
    return;
  }

  block.style.display = 'block';
  el.innerHTML = improvements.map(function (tip) {
    return `
      <div class="improvement-item">
        <span class="improvement-icon">→</span>
        <span>${tip}</span>
      </div>`;
  }).join('');
}


// ============================================================
// ROLE SELECT → MODULE 2
// ============================================================
function selectRole(role) {
  sessionStorage.setItem('selectedRole', role);
  window.location.href = '/module2?role=' + encodeURIComponent(role);
}


// ============================================================
// CUSTOM ROLE ANALYSIS (Module 1 bottom section)
// ============================================================
async function analyzeCustomRole() {
  const input = document.getElementById('customRoleInput');
  if (!input) return;

  const role = input.value.trim();
  if (!role) { alert('Please enter a role name.'); return; }

  const resultEl  = document.getElementById('customRoleResult');
  const loadingEl = document.getElementById('customRoleLoading');
  const loadText  = document.getElementById('customRoleLoadingText');

  if (resultEl)  resultEl.style.display  = 'none';
  if (loadingEl) loadingEl.style.display = 'block';
  if (loadText)  loadText.textContent    = '⏳ Fetching required skills via AI...';

  try {
    const res  = await fetch('/module1/analyze-custom-role', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ role })
    });
    const data = await res.json();

    if (loadingEl) loadingEl.style.display = 'none';
    if (data.error) { alert(data.error); return; }

    const roleNameEl  = document.getElementById('customRoleName');
    const matchPctEl  = document.getElementById('customRoleMatchPct');
    const barEl       = document.getElementById('customRoleBar');
    const skillsEl    = document.getElementById('customRoleSkills');
    const interviewEl = document.getElementById('customRoleInterviewBtn');

    if (roleNameEl) roleNameEl.textContent = data.role;
    if (matchPctEl) {
      matchPctEl.textContent = data.match + '%';
      matchPctEl.style.color = data.match >= 60
        ? 'var(--green)' : data.match >= 35 ? 'var(--amber)' : 'var(--red)';
    }
    if (barEl) barEl.style.width = '0%';

    if (skillsEl) {
      const matchedSet = new Set((data.matched_skills || []).map(s => s.toLowerCase()));
      skillsEl.innerHTML = (data.role_skills || []).map(function (s) {
        const matched = matchedSet.has(s.toLowerCase());
        return `<span class="skill-tag ${matched ? 'skill-match' : ''}">${s}</span>`;
      }).join('');
    }

    if (interviewEl) interviewEl.onclick = function () { selectRole(data.role); };
    if (resultEl)    resultEl.style.display = 'block';

    requestAnimationFrame(function () {
      setTimeout(function () { if (barEl) barEl.style.width = data.match + '%'; }, 80);
    });

  } catch (err) {
    if (loadingEl) loadingEl.style.display = 'none';
    alert('Error analyzing role. Please try again.');
  }
}