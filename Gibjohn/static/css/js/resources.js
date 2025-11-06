(function () {
const dz   = document.getElementById('dropzone');
const pick = document.getElementById('pick-btn');
const input= document.getElementById('file-input');
const list = document.getElementById('file-list');

if (!dz || !pick || !input || !list) return;

function renderList(fileList) {
list.innerHTML = '';
Array.from(fileList).forEach(f => {
    const li = document.createElement('li');
    li.textContent = `${f.name} — ${Math.round(f.size/1024)} KB`;
    list.appendChild(li);
});
}

function addFiles(files) {
// Preserve already selected files + add new ones
const dt = new DataTransfer();
for (const f of input.files) dt.items.add(f);
for (const f of files)       dt.items.add(f);
input.files = dt.files;
renderList(input.files);
}

// Drag & drop
dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag'); });
dz.addEventListener('dragleave', () => dz.classList.remove('drag'));
dz.addEventListener('drop', e => {
e.preventDefault();
dz.classList.remove('drag');
if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
    addFiles(e.dataTransfer.files);
}
});

// Button opens hidden input
pick.addEventListener('click', e => {
e.preventDefault();           // avoid accidental form submit
input.click();
});

// When user picked via dialog
input.addEventListener('change', () => addFiles(input.files));
})();
