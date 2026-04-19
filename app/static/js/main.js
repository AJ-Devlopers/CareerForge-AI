async function uploadResume() {
    const fileInput = document.getElementById("resumeFile");
    const file = fileInput.files[0];

    if (!file) {
        alert("Upload a PDF");
        return;
    }

    document.getElementById("loader").classList.remove("hidden");

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("/module1/upload", {
        method: "POST",
        body: formData
    });

    const data = await response.json();

    document.getElementById("loader").classList.add("hidden");

    displayResult(data);
}

function displayResult(data) {
    const resultDiv = document.getElementById("result");

    let html = `
        <div class="skill-box">
            <h2>Skills</h2>
            <p>${data.skills.join(", ")}</p>
        </div>
    `;

    html += `<h2 style="text-align:center;">Recommended Roles</h2>`;

    data.roles.forEach(role => {
        html += `
            <div class="role-card">
                <h3>${role.role} (${role.match}%)</h3>
                <p>${role.description}</p>
            </div>
        `;
    });

    resultDiv.innerHTML = html;
}