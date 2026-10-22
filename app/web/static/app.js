const MONEY = new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 2 });
const MONTHS_IN = ["январе", "феврале", "марте", "апреле", "мае", "июне", "июле", "августе", "сентябре", "октябре", "ноябре", "декабре"];

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const app = $("#app");
const dialog = $("#pay-dialog");
const form = $("#pay-form");
const toast = $("#toast");
const ui = {
  card: $("#student-card"),
  avatar: $("#student-avatar"),
  name: $("#student-name"),
  meta: $("#student-meta"),
  change: $("#student-change"),
  studentField: $("#student-field"),
  select: $("#pay-student"),
  amount: $("#pay-amount"),
  date: $("#pay-date"),
  fee: $("#sum-fee"),
  paid: $("#sum-paid"),
  after: $("#sum-after"),
  submit: $("#pay-submit"),
  amountError: $("#err-amount"),
  formError: $("#err-form"),
};

const state = { month: "", monthLabel: "", today: "", students: new Map(), group: "", query: "" };

const money = (value) => MONEY.format(Number(value));
const debtOf = (student) => Math.max(student.fee - student.paid, 0);
const initials = (name) => name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
const normalize = (text) => text.toLowerCase().replace(/[^\p{L}\p{N}]/gu, "");

function readPageData() {
  const data = JSON.parse($("#page-data", app).textContent);
  state.month = data.month;
  state.monthLabel = data.month_label;
  state.today = data.today;
  state.students = new Map(data.students.map((student) => [String(student.id), student]));
}

function applyFilters() {
  if (state.group && !$$("[data-tab]", app).some((tab) => tab.dataset.tab === state.group)) state.group = "";
  const query = normalize(state.query);
  let visible = 0;
  for (const row of $$("tr[data-student]", app)) {
    const show = (!state.group || row.dataset.group === state.group) && (!query || row.dataset.search.includes(query));
    row.hidden = !show;
    if (show) visible += 1;
  }
  const noMatch = $("[data-no-match]", app);
  if (noMatch) noMatch.hidden = visible > 0;
  for (const tab of $$("[data-tab]", app)) {
    const on = tab.dataset.tab === state.group;
    tab.classList.toggle("is-on", on);
    tab.setAttribute("aria-pressed", String(on));
  }
}

async function loadMonth(month, { push = true } = {}) {
  app.classList.add("is-loading");
  try {
    const response = await fetch(`/?month=${encodeURIComponent(month)}`, { headers: { "X-Partial": "1" } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    app.innerHTML = await response.text();
    readPageData();
    const search = $("#search", app);
    if (search) search.value = state.query;
    applyFilters();
    document.title = `Должники · ${state.monthLabel}`;
    if (push) history.pushState({ month: state.month }, "", `?month=${state.month}`);
  } catch {
    showToast("Не удалось загрузить данные. Проверьте соединение и попробуйте ещё раз.");
  } finally {
    app.classList.remove("is-loading");
  }
}

function showToast(text) {
  toast.textContent = text;
  toast.hidden = false;
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => { toast.hidden = true; }, 3500);
}

function formatAmount(raw) {
  const cleaned = raw.replace(/[^\d.,]/g, "").replace(",", ".");
  const [whole = "", ...rest] = cleaned.split(".");
  const grouped = whole.replace(/^0+(?=\d)/, "").replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  return cleaned.includes(".") ? `${grouped},${rest.join("").slice(0, 2)}` : grouped;
}

const amountValue = () => ui.amount.value.replace(/\s/g, "").replace(",", ".");
const currentStudent = () => state.students.get(ui.select.value) ?? null;

function setOn(attribute, value) {
  for (const button of $$(`[data-${attribute}]`, form)) button.classList.toggle("is-on", button.dataset[attribute] === value);
}

function fillStudents() {
  const options = [...state.students.values()].map((s) => new Option(`${s.name} · ${s.group}`, String(s.id)));
  ui.select.replaceChildren(new Option("Выберите ученика", ""), ...options);
}

function showCard(on) {
  const student = currentStudent();
  ui.card.hidden = !(on && student);
  ui.studentField.hidden = Boolean(on && student);
  if (student) {
    ui.avatar.textContent = initials(student.name);
    ui.name.textContent = student.name;
    const debt = debtOf(student);
    ui.meta.textContent = debt > 0 ? `${student.group} · долг ${money(debt)}` : `${student.group} · оплачено`;
  }
}

function setAmount(mode, { focus = false } = {}) {
  setOn("amount", mode);
  const student = currentStudent();
  const debt = student ? debtOf(student) : 0;
  let value = "";
  if (student && mode === "full") value = debt > 0 ? debt : student.fee;
  if (student && mode === "half") value = Math.round(((debt > 0 ? debt : student.fee) / 2) * 100) / 100;
  ui.amount.value = value === "" ? "" : formatAmount(String(value));
  if (focus) ui.amount.focus();
  updateSummary();
}

function shiftDay(iso, days) {
  const day = new Date(`${iso}T12:00:00Z`);
  day.setUTCDate(day.getUTCDate() + days);
  return day.toISOString().slice(0, 10);
}

function setDate(mode) {
  setOn("date", mode);
  if (mode === "today") ui.date.value = state.today;
  if (mode === "yesterday") ui.date.value = shiftDay(state.today, -1);
  ui.date.hidden = mode !== "pick";
  if (mode === "pick") {
    ui.date.value ||= state.today;
    ui.date.focus();
  }
  updateSummary();
}

function updateSummary() {
  const student = currentStudent();
  const amount = Number(amountValue()) || 0;
  ui.submit.textContent = amount > 0 ? `Принять ${money(amount)}` : "Принять";
  ui.after.classList.remove("is-clear");
  if (!student) {
    ui.fee.textContent = ui.paid.textContent = ui.after.textContent = "—";
    return;
  }
  ui.fee.textContent = money(student.fee);
  ui.paid.textContent = money(student.paid);
  const paidOn = ui.date.value || state.today;
  if (paidOn.slice(0, 7) !== state.month) {
    const [year, month] = paidOn.split("-");
    ui.after.textContent = `оплата учтётся в ${MONTHS_IN[Number(month) - 1]} ${year}`;
    return;
  }
  const debt = debtOf(student);
  const after = Math.max(debt - amount, 0);
  if (debt === 0) {
    ui.after.textContent = "уже оплачено за месяц";
  } else if (after === 0 && amount > 0) {
    ui.after.textContent = "0 · выйдет из должников";
    ui.after.classList.add("is-clear");
  } else {
    ui.after.textContent = money(after);
  }
}

function clearErrors() {
  ui.amountError.hidden = ui.formError.hidden = true;
  ui.amount.removeAttribute("aria-invalid");
}

function showAmountError(text) {
  ui.amountError.textContent = text;
  ui.amountError.hidden = false;
  ui.amount.setAttribute("aria-invalid", "true");
  ui.amount.focus();
}

function showFormError(text) {
  ui.formError.textContent = text;
  ui.formError.hidden = false;
}

function amountMessage(issue) {
  const messages = {
    greater_than: "Сумма должна быть больше 0",
    decimal_max_places: "Не больше двух знаков после запятой",
    decimal_max_digits: "Слишком большая сумма",
    decimal_parsing: "Введите сумму числом",
  };
  return messages[issue?.type] ?? "Проверьте сумму";
}

function openPayment(studentId) {
  form.reset();
  clearErrors();
  fillStudents();
  ui.select.value = studentId ?? "";
  showCard(Boolean(studentId));
  setDate("today");
  setAmount(studentId ? "full" : "custom");
  dialog.showModal();
  (studentId ? ui.amount : ui.select).focus();
}

async function submitPayment(event) {
  event.preventDefault();
  clearErrors();
  const student = currentStudent();
  const amount = amountValue();
  if (!student) return showFormError("Выберите ученика");
  if (!(Number(amount) > 0)) return showAmountError("Введите сумму больше 0");

  ui.submit.disabled = true;
  try {
    const response = await fetch("/api/v1/payments", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ student_id: student.id, amount, paid_on: ui.date.value || state.today }),
    });
    if (response.status === 201) {
      dialog.close();
      showToast(`Принято ${money(amount)} · ${student.name}`);
      await loadMonth(state.month, { push: false });
      return;
    }
    const body = await response.json().catch(() => ({}));
    const issue = Array.isArray(body.detail) ? body.detail[0] : null;
    if (issue?.loc?.includes("amount")) showAmountError(amountMessage(issue));
    else if (typeof body.detail === "string") showFormError(body.detail);
    else showFormError("Не удалось сохранить оплату. Проверьте данные и попробуйте ещё раз.");
  } catch {
    showFormError("Нет связи с сервером. Оплата не сохранена, попробуйте ещё раз.");
  } finally {
    ui.submit.disabled = false;
  }
}

document.addEventListener("click", (event) => {
  const target = event.target;
  const step = target.closest("[data-month]");
  if (step && app.contains(step)) {
    event.preventDefault();
    loadMonth(step.dataset.month);
    return;
  }
  const tab = target.closest("[data-tab]");
  if (tab) {
    state.group = tab.dataset.tab;
    applyFilters();
    return;
  }
  if (target.closest("[data-pay-new]")) {
    openPayment(null);
    return;
  }
  const row = target.closest("tr[data-student]");
  if (row && app.contains(row)) openPayment(row.dataset.student);
});

document.addEventListener("keydown", (event) => {
  const row = event.target.closest?.("tr[data-student]");
  if (row && (event.key === "Enter" || event.key === " ")) {
    event.preventDefault();
    openPayment(row.dataset.student);
  }
});

app.addEventListener("input", (event) => {
  if (event.target.id !== "search") return;
  state.query = event.target.value;
  applyFilters();
});

form.addEventListener("click", (event) => {
  const amountButton = event.target.closest("[data-amount]");
  if (amountButton) setAmount(amountButton.dataset.amount, { focus: amountButton.dataset.amount === "custom" });
  const dateButton = event.target.closest("[data-date]");
  if (dateButton) setDate(dateButton.dataset.date);
  if (event.target.closest("[data-close]")) dialog.close();
});

ui.amount.addEventListener("input", () => {
  ui.amount.value = formatAmount(ui.amount.value);
  setOn("amount", "custom");
  clearErrors();
  updateSummary();
});

ui.select.addEventListener("change", () => {
  clearErrors();
  showCard(Boolean(ui.select.value));
  setAmount("full");
});

ui.change.addEventListener("click", () => {
  showCard(false);
  ui.select.focus();
});

ui.date.addEventListener("change", updateSummary);
form.addEventListener("submit", submitPayment);
dialog.addEventListener("click", (event) => { if (event.target === dialog) dialog.close(); });

window.addEventListener("popstate", (event) => {
  const month = event.state?.month ?? new URLSearchParams(location.search).get("month") ?? "";
  loadMonth(month, { push: false });
});

readPageData();
history.replaceState({ month: state.month }, "", location.href);
applyFilters();
