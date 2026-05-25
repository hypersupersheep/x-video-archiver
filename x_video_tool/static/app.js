const form = document.querySelector("#resolve-form");
const result = document.querySelector("#result");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = form.querySelector("button");
  const formData = new FormData(form);
  const url = String(formData.get("url") || "").trim();

  button.disabled = true;
  button.textContent = "解析中";
  result.hidden = false;
  result.innerHTML = "<p class=\"meta\">Resolving...</p>";

  try {
    const response = await fetch("/api/resolve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Resolve failed.");
    }
    renderResult(data);
  } catch (error) {
    result.innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
  } finally {
    button.disabled = false;
    button.textContent = "解析";
  }
});

function renderResult(data) {
  const video = data.videos[0];
  const thumb = video.thumbnail
    ? `<img class="thumb" src="${escapeAttr(video.thumbnail)}" alt="" />`
    : "<div class=\"thumb\" aria-hidden=\"true\"></div>";
  const formats = video.formats
    .slice(0, 6)
    .map((format) => {
      const label = format.height ? `${format.height}p` : format.format_id || "mp4";
      return `<a class="format-link" href="${escapeAttr(format.url)}" rel="noreferrer">${escapeHtml(label)}</a>`;
    })
    .join("");

  result.innerHTML = `
    <div class="media">
      ${thumb}
      <div>
        <h2 class="title">${escapeHtml(video.title || data.title || "X video")}</h2>
        <p class="meta">${video.duration ? `${Math.round(video.duration)}s` : "mp4"} · ${escapeHtml(data.filename)}</p>
        <a class="download-link" href="${escapeAttr(data.download_url)}" rel="noreferrer">下载最佳版本</a>
        <div class="formats">${formats}</div>
      </div>
    </div>
  `;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value);
}
