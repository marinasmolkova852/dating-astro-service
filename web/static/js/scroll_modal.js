const inputs = document.querySelectorAll(".scroll-date");
const modalBackdrop = document.getElementById("modalBackdrop");
const okBtn = document.getElementById("ok");
const cancelBtn = document.getElementById("cancel");

const dayWheel = document.getElementById("day");
const monthWheel = document.getElementById("month");
const yearWheel = document.getElementById("year");

const months = [ "Январь","Февраль","Март","Апрель","Май","Июнь","Июль","Август","Сентябрь","Октябрь","Ноябрь","Декабрь" ];

const currentYear = new Date().getFullYear();
const minYear = currentYear - 100;
const maxYear = currentYear;

let activeInput = null;

function daysInMonth(month, year) {
    return new Date(year, month, 0).getDate();
}

function fillWheel(el, values) {
    el.innerHTML = '';
    el.appendChild(createPlaceholder());
    values.forEach(v => {
      const div = document.createElement("div");
      div.textContent = v;
      div.dataset.value = v;
      el.appendChild(div);
    });
    el.appendChild(createPlaceholder());
}

function createPlaceholder() {
    const p = document.createElement("div");
    p.classList.add("placeholder");
    p.textContent = '';
    return p;
}

function getSelected(el) {
    const center = el.getBoundingClientRect().top + el.clientHeight / 2;
    const children = [...el.children];
    return children.reduce((closest, c) => {
      if (c.classList.contains('placeholder')) return closest;
      const boxCenter = c.getBoundingClientRect().top + c.clientHeight / 2;
      const dist = Math.abs(boxCenter - center);
      return dist < closest.dist ? { el: c, dist } : closest;
    }, { el: null, dist: Infinity }).el;
}

function updateSelectedStyles(el) {
    const selected = getSelected(el);
    [...el.children].forEach(c => c.classList.toggle('selected', c === selected));
}

function scrollToValue(el, value) {
    const target = [...el.children].find(c => c.dataset.value === value);
    if (target) {
      const top = target.offsetTop - el.clientHeight / 2 + target.clientHeight / 2;
      el.scrollTo({ top, behavior: "smooth" });
    }
}

function updateDayWheel() {
    const mDiv = getSelected(monthWheel);
    const yDiv = getSelected(yearWheel);
    if (!mDiv || !yDiv) return;
    
    const month = months.indexOf(mDiv.dataset.value) + 1;
    const year = parseInt(yDiv.dataset.value);
    if (!month || isNaN(year)) return;
    
    const maxDay = daysInMonth(month, year);
    const selected = getSelected(dayWheel);
    const current = parseInt(selected?.dataset.value || "1");
    
    const existing = [...dayWheel.children].filter(d => !d.classList.contains("placeholder")).map(d => d.dataset.value);
    const required = Array.from({ length: maxDay }, (_, i) => (i + 1).toString().padStart(2, "0"));
    
    if (existing.join(",") !== required.join(",")) {
      const newValue = Math.min(current, maxDay).toString().padStart(2, "0");
      fillWheel(dayWheel, required);
      scrollToValue(dayWheel, newValue);
    }

    updateSelectedStyles(dayWheel);
}

function getDateString() {
    const d = getSelected(dayWheel)?.dataset.value || "01";
    const mName = getSelected(monthWheel)?.dataset.value;
    const y = getSelected(yearWheel)?.dataset.value;
    
    const mIndex = months.indexOf(mName);
    const m = (mIndex + 1).toString().padStart(2, "0");
    return `${d}.${m}.${y}`;
}

function initScrollListeners(el) {
    el.addEventListener("scroll", () => {
      clearTimeout(el._timer);
      el._timer = setTimeout(() => {
        updateSelectedStyles(el);
        if (el === monthWheel || el === yearWheel) updateDayWheel();
      }, 100);
    });

    el.addEventListener("click", e => {
      const target = e.target;
      if (target.tagName === "DIV" && !target.classList.contains("placeholder")) {
        scrollToValue(el, target.dataset.value);
        updateSelectedStyles(el);
        if (el === monthWheel || el === yearWheel) updateDayWheel();
      }
    });
}

// Заполнение колес
fillWheel(monthWheel, months);
fillWheel(yearWheel, Array.from({ length: maxYear - minYear + 1 }, (_, i) => (maxYear - i).toString()));
fillWheel(dayWheel, Array.from({ length: 31 }, (_, i) => (i + 1).toString().padStart(2, "0")));

[dayWheel, monthWheel, yearWheel].forEach(initScrollListeners);

// Обработчик открытия модалки
inputs.forEach(input => {
    input.addEventListener("click", () => {
      activeInput = input;
      modalBackdrop.classList.add("active");
    
      if (input.value) {
        const [d, m, y] = input.value.split(".");
        const mName = months[parseInt(m, 10) - 1];
        scrollToValue(dayWheel, d);
        scrollToValue(monthWheel, mName);
        scrollToValue(yearWheel, y);
      } else {
        const today = new Date();
        scrollToValue(dayWheel, today.getDate().toString().padStart(2, "0"));
        scrollToValue(monthWheel, months[today.getMonth()]);
        scrollToValue(yearWheel, today.getFullYear().toString());
      }
    
      // Ждём прокрутки, чтобы подсветка сработала корректно
      setTimeout(() => {
        updateSelectedStyles(dayWheel);
        updateSelectedStyles(monthWheel);
        updateSelectedStyles(yearWheel);
        updateDayWheel();
      }, 100);
    });
});

cancelBtn.addEventListener("click", () => {
    modalBackdrop.classList.remove("active");
    activeInput = null;
});

okBtn.addEventListener("click", () => {
    if (activeInput) {
      activeInput.value = getDateString();
    }
    modalBackdrop.classList.remove("active");
    activeInput = null;
});

modalBackdrop.addEventListener("click", e => {
    if (e.target === modalBackdrop) {
      modalBackdrop.classList.remove("active");
      activeInput = null;
    }
});