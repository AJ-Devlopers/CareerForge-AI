document.addEventListener('DOMContentLoaded', function () {

  // ================================
  // MODULE 1 LOGIC
  // ================================

  const fileInput  = document.getElementById('fileInput');
  const uploadZone = document.getElementById('uploadZone');
  const analyzeBtn = document.getElementById('analyzeBtn');
  const fileInfo   = document.getElementById('fileInfo');
  const fileName   = document.getElementById('fileName');

  if (fileInput && uploadZone) {

    fileInput.addEventListener('change', function () {
      var f = fileInput.files[0];
      if (!f) return;

      fileName.textContent = f.name;
      fileInfo.classList.add('show');
      analyzeBtn.disabled = true;
      uploadZone.style.borderColor = 'var(--accent)';

      var wrap  = document.getElementById('uploadProgressWrap');
      var bar   = document.getElementById('uploadProgressBar');
      var label = document.getElementById('uploadProgressLabel');

      bar.style.width = '0%';
      wrap.classList.add('active');
      label.classList.add('active');
      label.textContent = 'Reading file... 0%';

      var pct = 0;
      var interval = setInterval(function () {
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
        alert('Only PDF files allowed');
      }
    });
  }

  // ================================
  // MODULE 2 LOGIC (CHAT)
  // ================================
  const chatBox  = document.getElementById("chatBox");
  const inputBox = document.getElementById("inputBox");
  const sendBtn  = document.getElementById("sendBtn");

  if (chatBox && inputBox && sendBtn) {
    sendBtn.addEventListener("click", sendMessage);
    inputBox.addEventListener("keypress", function (e) {
      if (e.key === "Enter") sendMessage();
    });
  }
});


// ================================
// MODULE 1 — ANALYZE
// ================================
function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function analyzeResume() {
  var fileInput  = document.getElementById('fileInput');
  var analyzeBtn = document.getElementById('analyzeBtn');

  if (!fileInput || !fileInput.files[0]) {
    alert("Upload file first");
    return;
  }

  var file = fileInput.files[0];

  document.getElementById('emptyState').style.display   = 'none';
  document.getElementById('loadingState').classList.add('show');

  // Animate loading steps
  const steps = ['step1','step2','step3','step4'];
  steps.forEach((s,i) => {
    setTimeout(() => {
      if (i > 0) document.getElementById(steps[i-1]).classList.replace('active','done');
      document.getElementById(s).classList.add('active');
    }, i * 900);
  });

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res  = await fetch("/module1/upload", { method: "POST", body: formData });
    const data = await res.json();

    document.getElementById('loadingState').classList.remove('show');
    // Mark last step done
    document.getElementById('step4').classList.replace('active','done');

    renderResults(data);
  } catch (err) {
    document.getElementById('loadingState').classList.remove('show');
    alert("Analysis failed. Please try again.");
  }
}


// ================================
// MODULE 1 — RENDER RESULTS
// ================================
function renderResults(data) {

  // ── ATS Score ──
  const score = data.ats_score || 0;
  document.getElementById("scoreNum").textContent  = score;
  document.getElementById("scoreFill").style.width = score + "%";

  // Set score bar color + badge
  const fill  = document.getElementById("scoreFill");
  const badge = document.getElementById("atsBadge");
  if (score >= 75) {
    fill.className  = "score-fill fill-green";
    badge.className = "ats-badge badge-excellent";
    badge.textContent = "Excellent";
  } else if (score >= 50) {
    fill.className  = "score-fill fill-amber";
    badge.className = "ats-badge badge-good";
    badge.textContent = "Good";
  } else {
    fill.className  = "score-fill fill-red";
    badge.className = "ats-badge badge-fair";
    badge.textContent = "Needs Work";
  }

  // ── Stats cards ──
  const skills = data.skills_found || [];
  const roles  = data.roles        || [];

  document.getElementById("skillCount").textContent = skills.length;

  const topMatchPct = roles.length > 0 ? roles[0].match : 0;
  document.getElementById("topMatch").textContent = topMatchPct + "%";

  // ── Skills grid ──
  document.getElementById("skillsGrid").innerHTML = skills.length
    ? skills.map(s => `<span class="skill-tag">${s}</span>`).join("")
    : `<span style="font-family:var(--mono);font-size:0.68rem;color:var(--muted)">No skills detected — try a more detailed resume.</span>`;

  // ── Roles list ──
  document.getElementById("rolesList").innerHTML = roles.length
    ? roles.map(r => {
        const pct   = r.match || 0;
        const color = pct >= 60 ? 'var(--green)' : pct >= 35 ? 'var(--amber)' : 'var(--red)';
        return `
          <div class="role-item">
            <div class="role-top">
              <div class="role-name">${r.role}</div>
              <div class="role-pct" style="color:${color}">${pct}%</div>
            </div>
            <div class="role-bar">
              <div class="role-bar-fill" id="bar-${r.role.replace(/\s/g,'_')}"
                   style="width:0%;background:${color}"></div>
            </div>
            <div class="role-desc">
              Matched <strong>${r.matched_skills || 0}</strong> skills out of required skill set.
            </div>
            <button class="role-select-btn" onclick="selectRole('${r.role}')">
              Start Interview →
            </button>
          </div>`;
      }).join("")
    : `<div style="font-family:var(--mono);font-size:0.68rem;color:var(--muted);padding:1rem 0">No role matches found.</div>`;

  // Animate bars after DOM paint
  requestAnimationFrame(() => {
    setTimeout(() => {
      roles.forEach(r => {
        const el = document.getElementById('bar-' + r.role.replace(/\s/g,'_'));
        if (el) el.style.width = (r.match || 0) + '%';
      });
    }, 100);
  });

  document.getElementById("results").classList.add("show");
}


// ================================
// ROLE SELECT → MODULE 2
// ================================
function selectRole(role) {
  sessionStorage.setItem("selectedRole", role);
  window.location.href = "/module2?role=" + encodeURIComponent(role);
}


// ================================
// MODULE 2 — ROUND SELECTION
// ================================
let selectedRound = null;

const ROUND_LABELS = {
  screening:    'Initial Screening',
  technical:    'Technical Round',
  coding:       'Coding / DSA Round',
  project:      'Project Round',
  behavioral:   'Behavioural Round',
  system_design:'System Design',
  hr:           'HR Round',
  discussion:   'General Discussion'
};

function selectRound(round, el) {
  selectedRound = round;
  document.querySelectorAll('.round-card').forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');
  document.getElementById('startInterviewBtn').disabled = false;
}

function startInterview() {
  if (!selectedRound) return;
  document.getElementById('chatSubtitle').textContent = ROUND_LABELS[selectedRound] || selectedRound;
  document.getElementById('roundSelectionScreen').style.display = 'none';
  document.getElementById('chatScreen').style.display = 'flex';
}

function backToRounds() {
  document.getElementById('chatScreen').style.display    = 'none';
  document.getElementById('roundSelectionScreen').style.display = 'flex';
}


// ================================
// MODULE 2 — CHAT
// ================================
async function sendMessage() {
  const inputBox = document.getElementById("inputBox");
  const chatBox  = document.getElementById("chatBox");
  const message  = inputBox.value.trim();
  if (!message) return;

  // User bubble
  const userDiv = document.createElement('div');
  userDiv.className = 'user';
  userDiv.textContent = message;
  chatBox.appendChild(userDiv);
  inputBox.value = "";
  chatBox.scrollTop = chatBox.scrollHeight;

  // Typing indicator
  const typingDiv = document.createElement('div');
  typingDiv.className = 'bot typing-indicator';
  typingDiv.innerHTML = '<span></span><span></span><span></span>';
  chatBox.appendChild(typingDiv);
  chatBox.scrollTop = chatBox.scrollHeight;

  const role  = sessionStorage.getItem("selectedRole") || "Software Engineer";
  const round = selectedRound || "technical";

  try {
    const res  = await fetch("/module2/next-question", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role, round, answer: message })
    });
    const data = await res.json();

    chatBox.removeChild(typingDiv);

    const botDiv = document.createElement('div');
    botDiv.className = 'bot';
    botDiv.textContent = data.question;
    chatBox.appendChild(botDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
  } catch (err) {
    chatBox.removeChild(typingDiv);
    const errDiv = document.createElement('div');
    errDiv.className = 'bot';
    errDiv.textContent = '⚠️ Error getting question. Please try again.';
    chatBox.appendChild(errDiv);
  }
}


// ================================
// VOICE
// ================================
function startVoice() {
  if (!('webkitSpeechRecognition' in window)) {
    alert("Voice not supported in this browser");
    return;
  }
  const recognition = new webkitSpeechRecognition();
  recognition.lang = 'en-US';
  recognition.start();
  recognition.onresult = function (event) {
    document.getElementById("inputBox").value = event.results[0][0].transcript;
  };
}


// ================================
// CUSTOM ROLE ANALYSIS
// ================================
async function analyzeCustomRole() {
  const input = document.getElementById('customRoleInput');
  const role  = input.value.trim();

  if (!role) {
    alert("Please enter a role name");
    return;
  }

  document.getElementById('customRoleResult').style.display  = 'none';
  document.getElementById('customRoleLoading').style.display = 'block';
  document.getElementById('customRoleLoadingText').textContent = '⏳ Fetching required skills via AI...';

  try {
    const res  = await fetch('/module1/analyze-custom-role', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role })
    });
    const data = await res.json();

    document.getElementById('customRoleLoading').style.display = 'none';

    if (data.error) {
      alert(data.error);
      return;
    }

    document.getElementById('customRoleName').textContent      = data.role;
    document.getElementById('customRoleMatch').textContent     = data.match + '%';
    document.getElementById('customRoleBar').style.width       = '0%';

    const matchedSet = new Set(data.matched_skills.map(s => s.toLowerCase()));
    document.getElementById('customRoleSkills').innerHTML =
      data.role_skills.map(s => {
        const isMatch = matchedSet.has(s.toLowerCase());
        return `<span class="skill-tag ${isMatch ? 'skill-match' : ''}">${s}</span>`;
      }).join('');

    document.getElementById('customRoleInterviewBtn').onclick = () => selectRole(data.role);
    document.getElementById('customRoleResult').style.display = 'block';

    // Animate bar
    requestAnimationFrame(() => {
      setTimeout(() => {
        document.getElementById('customRoleBar').style.width = data.match + '%';
      }, 80);
    });

  } catch (err) {
    document.getElementById('customRoleLoading').style.display = 'none';
    alert('Error analyzing role. Please try again.');
  }
}

// Allow Enter key in custom role input
document.addEventListener('DOMContentLoaded', function () {
  const ci = document.getElementById('customRoleInput');
  if (ci) {
    ci.addEventListener('keypress', function (e) {
      if (e.key === 'Enter') analyzeCustomRole();
    });
  }
});