const $ = (id) => document.getElementById(id);
// Keep raw HTML escaped and use markdown-it's unsafe-link validation.
const markdown = window.markdownit({ html: false, breaks: true }).disable("image");
const STATUSES = {
  pending: "Pending",
  approved: "Approved",
  rejected: "Rejected",
  cancelled: "Cancelled",
  paid: "Paid",
};
const reviewMessages = new Map();
const state = {
  filter: "",
  ownership: "all",
  listLoaded: false,
  detailSignature: "",
  selectedId: null,
  rows: [],
  active: false,
  busy: false,
  epoch: 0,
  listVersion: 0,
  detailVersion: 0,
};
const money = (cents) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(
    cents / 100,
  );
const when = (iso) =>
  new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
function el(tag, text, cls) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (cls) node.className = cls;
  return node;
}
function banner(text = "") {
  $("banner").textContent = text;
  $("banner").hidden = !text;
}
function expenseIdButton(id) {
  const button = el("button", undefined, "expense-id-copy");
  button.type = "button";
  button.setAttribute("aria-label", `Copy expense ID ${id}`);
  button.title = "Copy expense ID";
  const icon = el("span", undefined, "copy-icon");
  icon.setAttribute("aria-hidden", "true");
  button.append(el("span", id), icon);
  let reset;
  button.addEventListener("click", async (event) => {
    event.stopPropagation();
    if (button.disabled) return;
    button.disabled = true;
    clearTimeout(reset);
    button.classList.remove("copied");
    const status = $("copy-status");
    status.textContent = "";
    try {
      await navigator.clipboard.writeText(id);
      button.classList.add("copied");
      button.title = "Copied";
      status.textContent = `Copied ${id}`;
    } catch {
      button.title = "Copy expense ID";
      status.textContent = `Could not copy ${id}. Select the ID text and copy it manually.`;
    } finally {
      button.disabled = false;
    }
    const feedback = status.textContent;
    reset = setTimeout(() => {
      button.classList.remove("copied");
      button.title = "Copy expense ID";
      if (status.textContent === feedback) status.textContent = "";
    }, 2500);
  });
  return button;
}
function addExpenseCopies(content) {
  const walker = document.createTreeWalker(content, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) {
    if (!walker.currentNode.parentElement.closest("a, button, pre")) nodes.push(walker.currentNode);
  }
  for (const node of nodes) {
    const matches = [...node.textContent.matchAll(/\bEXP\d+\b/g)];
    if (!matches.length) continue;
    const fragment = document.createDocumentFragment();
    let offset = 0;
    for (const match of matches) {
      fragment.append(node.textContent.slice(offset, match.index), expenseIdButton(match[0]));
      offset = match.index + match[0].length;
    }
    fragment.append(node.textContent.slice(offset));
    node.replaceWith(fragment);
  }
}
async function api(path, options = {}) {
  const epoch = state.epoch;
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    if (response.status === 401 && epoch === state.epoch) await bootstrap();
    throw Error(data.error || "Expense Desk could not complete that request.");
  }
  return response;
}
// Only identical, in-flight reads are shared. No cross-session response cache.
const pendingReads = new Map();
function cancelReads() {
  for (const read of pendingReads.values()) read.controller.abort();
  pendingReads.clear();
}
function readJSON(lane, path) {
  const key = `${state.epoch}:${path}`;
  const existing = pendingReads.get(lane);
  if (existing?.key === key) return existing.promise;
  existing?.controller.abort();
  const controller = new AbortController();
  const read = { key, controller };
  read.promise = api(path, {
    signal: AbortSignal.any([controller.signal, AbortSignal.timeout(25000)]),
  }).then((response) => response.json()).finally(() => {
    if (pendingReads.get(lane) === read) pendingReads.delete(lane);
  });
  pendingReads.set(lane, read);
  return read.promise;
}
function message(role, text) {
  $("welcome")?.remove();
  const item = el("div", undefined, "message " + role);
  const content = el("div", text, "text");
  if (role === "assistant") content.innerHTML = markdown.render(text);
  addExpenseCopies(content);
  item.append(
    el("div", role === "user" ? "You" : "Expense Desk", "speaker"),
    content,
  );
  $("messages").append(item);
  $("messages").scrollTop = $("messages").scrollHeight;
}
function renderRows() {
  $("rows").replaceChildren();
  for (const row of state.rows) {
    const button = el("div", undefined, "expense-row");
    if (row.unverified_submitter) button.classList.add("unverified");
    button.dataset.id = row.id;
    button.dataset.selected = String(row.id === state.selectedId);
    const select = el("button", undefined, "expense-select");
    select.type = "button";
    select.setAttribute("aria-pressed", String(row.id === state.selectedId));
    select.append(
      el("span", row.memo || "No memo", "memo"),
      el("span", money(row.amount_cents)),
    );
    const meta = el("span", undefined, "meta");
    meta.append(expenseIdButton(row.id), el("span", row.submitter_label || row.submitter));
    button.append(select, meta,
      el(
        "span",
        STATUSES[row.status] || row.status,
        "status " + (STATUSES[row.status] ? row.status : ""),
      ),
    );
    button.addEventListener("click", () => {
      state.selectedId = row.id;
      renderRows();
      if (state.detailId !== row.id) renderDetail(row, []);
      loadDetail();
    });
    $("rows").append(button);
  }
}
function updateFilterNotice() {
  $("detail-filter-notice")?.remove();
  const row = state.detailRow;
  if (!row) return;
  let text = "";
  if (state.filter && row.status !== state.filter)
    text = "This expense is outside the selected status filter.";
  else if (state.ownership === "mine" && !state.rows.some((item) => item.id === row.id))
    text = "This expense is outside the current list filters.";
  if (text) {
    const notice = el("p", text, "muted");
    notice.id = "detail-filter-notice";
    $("detail").querySelector("h2")?.after(notice);
  }
}
function renderDetail(row, activity) {
  state.detailRow = row;
  state.detailId = row.id;
  state.detailSignature = JSON.stringify([row, activity]);
  const detail = $("detail");
  detail.replaceChildren();
  const heading = el("h2");
  heading.append(
    expenseIdButton(row.id),
    el("span", STATUSES[row.status] || row.status, "status"),
  );
  detail.append(heading, el("div", money(row.amount_cents), "amount"));
  if (row.unverified_submitter) detail.append(el("p", "Unverified submitter", "muted"));
  updateFilterNotice();
  const fields = el("dl");
  for (const [name, value] of [
    ["Created by", row.submitter_label || row.submitter],
    ["Memo", row.memo || "none"],
    ["Decided by", row.approver_label || row.approver],
    ["Created", when(row.created_at)],
    ["Updated", when(row.updated_at)],
  ]) {
    if (value) fields.append(el("dt", name), el("dd", value));
  }
  if (row.review) {
    detail.append(el("p", row.review.message));
    const version = JSON.stringify(row.review);
    if (reviewMessages.get(row.id) !== version) {
      reviewMessages.set(row.id, version);
      message("assistant", `${row.id}: ${row.review.message}`);
    }
  }
  detail.append(fields);
  if (row.status === "pending") {
    const approve = el("button", "Approve", "primary");
    approve.id = "approve";
    approve.type = "button";
    approve.disabled = state.busy;
    approve.onclick = () => {
      if (state.busy) return;
      $("message").value = `Approve expense ${row.id}`;
      $("composer").requestSubmit();
    };
    detail.append(approve);
  }
  detail.append(el("h3", "Activity"));
  const list = el("ul", undefined, "activity");
  for (const event of activity) {
    const item = el("li");
    item.append(
      el("time", when(event.at)),
      el("span", `${event.action} by ${event.actor_label || event.actor}`),
    );
    const identities = el("details", undefined, "activity-identities");
    identities.append(el("summary", "Identity details"));
    for (const [label, value] of [["Actor ID", event.actor]]) {
      const field = el("div");
      const email = event.actor_label?.includes("@") && event.actor_label !== value
        ? event.actor_label
        : "";
      field.append(
        el("span", label + ": "),
        el("code", email && value ? `${email} | ${value}` : value || "Unknown"),
      );
      if (value) {
        const copy = el("button", "Copy " + label.toLowerCase());
        copy.type = "button";
        copy.onclick = async () => {
          try {
            await navigator.clipboard.writeText(value);
            copy.textContent = "Copied";
          } catch {
            copy.textContent = "Select the ID to copy";
          }
        };
        field.append(copy);
      }
      identities.append(field);
    }
    item.append(identities);
    if (event.detail?.message) item.append(el("div", event.detail.message));
    if (event.detail?.reason) item.append(el("div", event.detail.reason));
    list.append(item);
  }
  detail.append(list);
  const approval = activity.find(
    (event) =>
      event.action === "approved" && event.actor?.startsWith("urn:agent:app:"),
  );
  if (
    row.status === "approved" &&
    approval &&
    reviewMessages.get(row.id) !== "approved"
  ) {
    reviewMessages.set(row.id, "approved");
    message(
      "assistant",
      `The agent approved ${row.id}. ${approval.detail?.reason || ""}`,
    );
  }
}
async function loadDetail({ quiet = false } = {}) {
  const id = state.selectedId,
    version = ++state.detailVersion,
    epoch = state.epoch;
  if (!id || !state.active) return true;
  $("detail-loading")?.remove();
  const loading = el("p", "Loading Activity…", "muted");
  loading.id = "detail-loading";
  if (!quiet) $("detail").append(loading);
  try {
    const data = await readJSON("detail", "/api/expenses/" + encodeURIComponent(id));
    if (version !== state.detailVersion || epoch !== state.epoch || id !== state.selectedId)
      return true;
    if (state.detailSignature !== JSON.stringify([data.expense, data.activity]))
      renderDetail(data.expense, data.activity);
    else loading.remove();
    return true;
  } catch (error) {
    if (version === state.detailVersion && epoch === state.epoch && error.name !== "AbortError") {
      loading.textContent = "Activity could not refresh. " + error.message;
      $("detail").append(loading);
      return false;
    }
    return true;
  }
}
async function loadList({ quiet = false } = {}) {
  const version = ++state.listVersion, epoch = state.epoch;
  $("list-state").textContent = state.listLoaded ? "Refreshing expenses…" : "Loading expenses…";
  $("list-state").classList.add("loading");
  try {
    const rows = (await readJSON("list", "/api/expenses?status=" + encodeURIComponent(state.filter) +
      "&ownership=" + state.ownership)).slice().reverse();
    if (version !== state.listVersion || epoch !== state.epoch) return true;
    if (JSON.stringify(state.rows) !== JSON.stringify(rows) || !state.listLoaded) {
      state.rows = rows;
      renderRows();
    }
    $("list-state").classList.remove("loading");
    state.listLoaded = true;
    updateFilterNotice();
    $("list-state").textContent = rows.length ? "" :
      "Nothing matches these filters. Ask the agent to file an expense or choose All expenses.";
    return true;
  } catch (error) {
    if (version === state.listVersion && epoch === state.epoch && error.name !== "AbortError") {
      $("list-state").classList.remove("loading");
      $("list-state").textContent = "Expenses could not refresh. " + error.message + " Click Refresh to retry.";
      return false;
    }
    return true;
  }
}
async function refresh(options = {}) {
  if (!state.active) return true;
  const results = await Promise.all([loadList(options), loadDetail(options)]);
  return results.every(Boolean);
}
let bootstrapPromise;
function bootstrap() {
  if (!bootstrapPromise)
    bootstrapPromise = bootstrapSession().finally(() => { bootstrapPromise = null; });
  return bootstrapPromise;
}
async function bootstrapSession() {
  state.epoch++;
  cancelReads();
  state.listLoaded = false;
  state.detailId = null;
  state.detailRow = null;
  state.active = false;
  state.detailSignature = "";
  $("rows").replaceChildren();
  state.listVersion++;
  state.detailVersion++;
  const data = await (await fetch("/api/session")).json();
  state.selectedId = null;
  state.rows = [];
  reviewMessages.clear();
  state.ownership = data.mode === "user" ? "mine" : "all";
  $("ownership").value = state.ownership;
  $("ownership").disabled = data.mode !== "user";
  $("detail").replaceChildren(
    el("p", "Choose an expense to see its details and Activity.", "muted"),
  );
  state.active = data.mode !== "signed_out";
  $("gate").hidden = state.active;
  $("desk").hidden = !state.active;
  $("signout").hidden = data.mode !== "user";
  $("signin").hidden = !data.login || data.mode === "user";
  $("application").hidden = !data.login;
  $("identity").textContent = data.mode === "user" || data.mode === "application" ? data.identity : "";
  $("messages").replaceChildren();
  for (const item of data.messages) message(item.role, item.text);
  if (!data.messages.length) {
    $("messages").append($("welcome-template").content.cloneNode(true));
  }
}
async function changeSession(action) {
  banner();
  try {
    const data = await (
      await api("/api/session/" + action, { method: "POST" })
    ).json();
    if (data.url) {
      location.assign(data.url);
      return;
    }
    reviewMessages.clear();
    state.selectedId = null;
    state.rows = [];
    state.filter = "";
    $("status").value = "";
    $("rows").replaceChildren();
    $("detail").replaceChildren(
      el("p", "Choose an expense to see its details and Activity.", "muted"),
    );
    await bootstrap();
    await refresh();
  } catch (error) {
    banner(error.message);
  }
}
$("application").onclick = () => changeSession("agent");
$("signin").onclick = () => changeSession("login");
$("signout").onclick = () => changeSession("signout");
$("refresh").onclick = () => refresh();
$("ownership").onchange = () => {
  state.ownership = $("ownership").value;
  refresh();
};
$("status").onchange = () => {
  state.filter = $("status").value;
  refresh();
};
$("message").onkeydown = (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    $("composer").requestSubmit();
  }
};
$("composer").onsubmit = async (event) => {
  event.preventDefault();
  const prompt = $("message").value.trim();
  if (!prompt || state.busy) return;
  state.busy = true;
  const epoch = state.epoch;
  $("send").disabled = true;
  $("signout").disabled = true;
  $("signin").disabled = true;
  if ($("approve")) $("approve").disabled = true;
  banner();
  message("user", prompt);
  $("message").value = "";
  $("progress").textContent = "Thinking...";
  let ended = false;
  try {
    const response = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message: prompt, selected_id: state.selectedId }),
    });
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();
      for (const line of lines) {
        if (!line) continue;
        const item = JSON.parse(line);
        if (epoch !== state.epoch) continue;
        if (item.type === "progress") $("progress").textContent = item.text.replace(/(?:…|\.{3}|·{3})+\s*$/u, "").trimEnd() + "...";
        if (item.type === "result" || item.type === "error") {
          message("assistant", item.text);
          ended = true;
        }
        if (item.type === "refresh" && item.request_id) {
          if (!state.selectedId && item.request_id)
            state.selectedId = item.request_id;
        }
      }
    }
    if (!ended && epoch === state.epoch)
      throw Error(
        "The connection ended before the result was confirmed. Check the expense and its Activity before trying again.",
      );
  } catch (error) {
    if (epoch === state.epoch) banner(error.message);
  } finally {
    state.busy = false;
    $("send").disabled = false;
    $("signout").disabled = false;
    $("signin").disabled = false;
    if ($("approve")) $("approve").disabled = false;
    $("progress").textContent = "";
    cancelReads(); // Reads started before this write may describe the previous state.
    await refresh({ quiet: true });
    $("message").focus();
  }
};
if (new URLSearchParams(location.search).has("signin")) {
  banner(
    "Sign-in did not complete. Try again, or contact your administrator.",
  );
  history.replaceState(null, "", "/");
}
bootstrap().then(() => refresh()).catch(() =>
  banner("Expense Desk could not connect. Reload the page to try again."),
);
