// static/js/tabs.js
document.addEventListener("DOMContentLoaded", () => {
const tabs = document.querySelectorAll('[role="tab"]');
const panels = document.querySelectorAll('[role="tabpanel"]');

function activateTab(tab) {
// deactivate all
tabs.forEach(t => {
    t.setAttribute("aria-selected", "false");
    t.classList.remove("active");
    t.tabIndex = -1;
});
panels.forEach(p => {
    p.hidden = true;
    p.classList.remove("active");
});

// activate chosen
const targetId = tab.getAttribute("aria-controls");
const panel = document.getElementById(targetId);
tab.setAttribute("aria-selected", "true");
tab.classList.add("active");
tab.tabIndex = 0;
if (panel) {
    panel.hidden = false;
    panel.classList.add("active");
}
}

// click support
tabs.forEach(tab => {
tab.addEventListener("click", () => activateTab(tab));
});

// keyboard support (ArrowLeft/ArrowRight/Home/End)
const tablist = document.querySelector('[role="tablist"]');
if (tablist) {
tablist.addEventListener("keydown", (e) => {
    const current = document.activeElement;
    if (!current || current.getAttribute("role") !== "tab") return;

    const list = Array.from(tabs);
    const i = list.indexOf(current);
    let next = null;

    switch (e.key) {
    case "ArrowRight": next = list[(i + 1) % list.length]; break;
    case "ArrowLeft":  next = list[(i - 1 + list.length) % list.length]; break;
    case "Home":       next = list[0]; break;
    case "End":        next = list[list.length - 1]; break;
    default: return;
    }
    e.preventDefault();
    next.focus();
    activateTab(next);
});
}

// open "Quizzes" by default if nothing selected
const selected = document.querySelector('[role="tab"][aria-selected="true"]');
activateTab(selected || tabs[0]);
});
