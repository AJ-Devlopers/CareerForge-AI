// =============================
// FILE INPUT + UI HANDLING (SSR SAFE)
// =============================

const fileInput = document.querySelector('input[type="file"]');
const uploadZone = document.querySelector('.upload-zone');

// 🔹 Show selected file name
if (fileInput) {
  fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];

    if (file) {
      console.log("Selected:", file.name);

      // Create or update file label
      let info = document.getElementById("fileNameDisplay");

      if (!info) {
        info = document.createElement("div");
        info.id = "fileNameDisplay";
        info.style.marginTop = "10px";
        info.style.fontSize = "12px";
        info.style.color = "var(--accent)";
        uploadZone.appendChild(info);
      }

      info.textContent = file.name;
    }
  });
}


// =============================
// DRAG & DROP (UI ONLY)
// =============================

if (uploadZone && fileInput) {

  uploadZone.addEventListener("click", () => fileInput.click());

  uploadZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadZone.classList.add("drag-over");
  });

  uploadZone.addEventListener("dragleave", () => {
    uploadZone.classList.remove("drag-over");
  });

  uploadZone.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadZone.classList.remove("drag-over");

    const file = e.dataTransfer.files[0];

    if (file && file.type === "application/pdf") {
      fileInput.files = e.dataTransfer.files;

      // trigger change manually
      fileInput.dispatchEvent(new Event("change"));
    } else {
      alert("Only PDF files allowed");
    }
  });
}


// =============================
// OPTIONAL: SMOOTH SCROLL
// =============================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute("href"));
    if (target) {
      target.scrollIntoView({ behavior: "smooth" });
    }
  });
});