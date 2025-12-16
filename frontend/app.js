/**
 * Configure your backend URL here.
 * Local: "http://localhost:8080"
 * Deployed: "https://your-backend.onrender.com"
 */
const API_BASE = "https://meal-planner-xrtw.onrender.com";

const state = {
  token: localStorage.getItem("mp_token") || null,
  dishes: [],
  ingredients: [],
  cycle: [],
  selectedDishId: null,
  selectedIngId: null,
  dishIngredientDraft: [], // {ingredient_id, amount, unit}
};

function $(id){ return document.getElementById(id); }
function authHeaders(){
  return state.token ? { "Authorization": `Bearer ${state.token}` } : {};
}

function setAuthUI(){
  const pill = $("authState");
  const logged = !!state.token;
  pill.textContent = logged ? "Logado" : "Não logado";
  $("logoutBtn").style.display = logged ? "inline-block" : "none";
}

async function api(path, opts = {}){
  const res = await fetch(`${API_BASE}${path}`, opts);
  if(!res.ok){
    const txt = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${txt}`);
  }
  return res.json();
}

async function login(){
  const password = $("password").value;
  const data = await api("/api/login", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({password}),
  });
  state.token = data.token;
  localStorage.setItem("mp_token", state.token);
  setAuthUI();
  alert("Logado!");
}

function logout(){
  state.token = null;
  localStorage.removeItem("mp_token");
  setAuthUI();
}

function setTabs(){
  document.querySelectorAll(".tab").forEach(btn=>{
    btn.addEventListener("click", ()=>{
      document.querySelectorAll(".tab").forEach(b=>b.classList.remove("active"));
      btn.classList.add("active");
      const view = btn.dataset.view;
      document.querySelectorAll(".view").forEach(v=>v.classList.add("hidden"));
      $(`view-${view}`).classList.remove("hidden");
    });
  });
}

function fillYearMonth(){
  const y = $("year");
  const m = $("month");
  const now = new Date();
  const yearNow = now.getFullYear();
  for(let yy = yearNow - 1; yy <= yearNow + 2; yy++){
    const opt = document.createElement("option");
    opt.value = yy; opt.textContent = yy;
    if(yy === yearNow) opt.selected = true;
    y.appendChild(opt);
  }
  const names = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"];
  names.forEach((name, idx)=>{
    const opt = document.createElement("option");
    opt.value = idx+1; opt.textContent = name;
    if(idx === now.getMonth()) opt.selected = true;
    m.appendChild(opt);
  });
}

function dishOptions(selectEl, includeBlank=true){
  selectEl.innerHTML = "";
  if(includeBlank){
    const o = document.createElement("option");
    o.value = ""; o.textContent = "";
    selectEl.appendChild(o);
  }
  state.dishes.forEach(d=>{
    const o = document.createElement("option");
    o.value = d.id;
    o.textContent = d.name;
    selectEl.appendChild(o);
  });
}

async function refreshDishes(){
  state.dishes = await api("/api/dishes");
  const dishList = $("dishList");
  dishList.innerHTML = "";
  state.dishes.forEach(d=>{
    const opt = document.createElement("option");
    opt.value = d.id;
    opt.textContent = `#${d.id} - ${d.name}`;
    dishList.appendChild(opt);
  });

  dishOptions($("ovrBreakfast"));
  dishOptions($("ovrLunch"));
  dishOptions($("ovrSnack"));
  dishOptions($("ovrDinner"));

  await refreshCycle();
}

async function refreshIngredients(){
  state.ingredients = await api("/api/ingredients");
  const ingList = $("ingList");
  ingList.innerHTML = "";
  state.ingredients.forEach(i=>{
    const opt = document.createElement("option");
    opt.value = i.id;
    const p = i.unit_price != null ? ` - ${i.unit_price.toFixed(2)} ${i.price_currency}/${i.unit}` : "";
    opt.textContent = `#${i.id} - ${i.name}${p}`;
    ingList.appendChild(opt);
  });

  // ingredient dropdown in dish ingredient editor
  const di = $("diIngredient");
  di.innerHTML = "";
  state.ingredients.forEach(i=>{
    const o = document.createElement("option");
    o.value = i.id;
    o.textContent = `${i.name} (${i.unit})`;
    di.appendChild(o);
  });
}

async function refreshCycle(){
  state.cycle = await api("/api/cycle");
  renderTemplateGrid();
}

function renderTemplateGrid(){
  // 7x4
  const el = $("templateGrid");
  const weekdays = ["Domingo","Segunda","Terça","Quarta","Quinta","Sexta","Sábado"];
  let html = `<table><thead><tr>${weekdays.map(w=>`<th>${w}</th>`).join("")}</tr></thead><tbody>`;
  for(let row=0; row<4; row++){
    html += "<tr>";
    for(let col=0; col<7; col++){
      const idx = row*7 + col; // 0..27
      const dayIndex = idx+1;
      const item = state.cycle[idx];
      html += `<td>
        <div class="cell-date">Dia ${dayIndex}</div>
        <div class="small">Café</div>${renderSelect(`cyc-${dayIndex}-b`, item?.breakfast_dish_id)}
        <div class="small">Almoço</div>${renderSelect(`cyc-${dayIndex}-l`, item?.lunch_dish_id)}
        <div class="small">Lanche</div>${renderSelect(`cyc-${dayIndex}-s`, item?.snack_dish_id)}
        <div class="small">Jantar</div>${renderSelect(`cyc-${dayIndex}-d`, item?.dinner_dish_id)}
      </td>`;
    }
    html += "</tr>";
  }
  html += "</tbody></table>";
  el.innerHTML = html;

  // populate all selects
  for(let i=1;i<=28;i++){
    ["b","l","s","d"].forEach(slot=>{
      const sel = document.getElementById(`cyc-${i}-${slot}`);
      dishOptions(sel);
      const key = slot==="b"?"breakfast_dish_id":slot==="l"?"lunch_dish_id":slot==="s"?"snack_dish_id":"dinner_dish_id";
      const val = state.cycle[i-1]?.[key];
      sel.value = val ?? "";
    });
  }
}

function renderSelect(id, value){
  // options filled later
  return `<select id="${id}"></select>`;
}

async function saveTemplate(){
  if(!state.token) return alert("Login necessário");
  for(let i=1;i<=28;i++){
    const b = document.getElementById(`cyc-${i}-b`).value || null;
    const l = document.getElementById(`cyc-${i}-l`).value || null;
    const s = document.getElementById(`cyc-${i}-s`).value || null;
    const d = document.getElementById(`cyc-${i}-d`).value || null;

    await api(`/api/cycle/${i}`, {
      method: "PUT",
      headers: {"Content-Type":"application/json", ...authHeaders()},
      body: JSON.stringify({
        breakfast_dish_id: b ? parseInt(b,10) : null,
        lunch_dish_id: l ? parseInt(l,10) : null,
        snack_dish_id: s ? parseInt(s,10) : null,
        dinner_dish_id: d ? parseInt(d,10) : null,
      })
    });
  }
  alert("Template salvo!");
  await refreshCycle();
  await loadCalendar();
}

async function loadCalendar(){
  const year = parseInt($("year").value,10);
  const month = parseInt($("month").value,10);
  const data = await api(`/api/calendar?year=${year}&month=${month}`);
  renderCalendar(data);
}

function renderCalendar(data){
  const monthName = new Intl.DateTimeFormat("pt-BR", { month: "long" })
  .format(new Date(data.year, data.month - 1, 1));
  $("calendarTitle").textContent = `${monthName.charAt(0).toUpperCase() + monthName.slice(1)} ${data.year}`;
  const el = $("calendarGrid");
  let html = `<table><thead><tr>${data.weekdays.map(w=>`<th>${w}</th>`).join("")}</tr></thead><tbody>`;

  for(const week of data.weeks){
    html += "<tr>";
    for(const cell of week){
      if(!cell.in_month){
        html += `<td class="small" style="opacity:0.45">-</td>`;
        continue;
      }
      
      const dayNum = parseInt(cell.date.split("-")[2], 10)
      const meals = cell.meals;
      html += `<td>

      <div class="cell-date">${dayNum}</div>
        ${renderMeal("Café", meals?.breakfast?.dish_name)}
        ${renderMeal("Almoço", meals?.lunch?.dish_name)}
        ${renderMeal("Lanche", meals?.snack?.dish_name)}
        ${renderMeal("Jantar", meals?.dinner?.dish_name)}
      </td>`;
    }
    html += "</tr>";
  }
  html += "</tbody></table>";
  el.innerHTML = html;
}

function renderMeal(label, name){
  const t = name ? name : "<span class='small'></span>";
  return `<div class="meal"><b>${label}:</b> ${t}</div>`;
}

// --- Overrides ---
async function loadOverride(){
  const date = $("overrideDate").value;
  if(!date) return alert("Selecione uma data");
  // Get calendar for month then find cell meals; also check override list
  const d = new Date(date+"T00:00:00");
  const data = await api(`/api/overrides?year=${d.getFullYear()}&month=${d.getMonth()+1}`);
  const row = data.find(x => x.date === date);
  // selects
  $("ovrBreakfast").value = row?.breakfast_dish_id ?? "";
  $("ovrLunch").value = row?.lunch_dish_id ?? "";
  $("ovrSnack").value = row?.snack_dish_id ?? "";
  $("ovrDinner").value = row?.dinner_dish_id ?? "";
}

async function saveOverride(){
  if(!state.token) return alert("Login necessário");
  const date = $("overrideDate").value;
  if(!date) return alert("Selecione uma data");

  const b = $("ovrBreakfast").value || null;
  const l = $("ovrLunch").value || null;
  const s = $("ovrSnack").value || null;
  const d = $("ovrDinner").value || null;

  await api(`/api/override/${date}`, {
    method: "PUT",
    headers: {"Content-Type":"application/json", ...authHeaders()},
    body: JSON.stringify({
      breakfast_dish_id: b ? parseInt(b,10) : null,
      lunch_dish_id: l ? parseInt(l,10) : null,
      snack_dish_id: s ? parseInt(s,10) : null,
      dinner_dish_id: d ? parseInt(d,10) : null,
    })
  });
  alert("Override saved!");
  await loadCalendar();
}

async function clearOverride(){
  if(!state.token) return alert("Login necessário");
  const date = $("overrideDate").value;
  if(!date) return alert("Selecione uma data");
  await api(`/api/override/${date}`, { method: "DELETE", headers: authHeaders() });
  alert("Override limpo!");
  await loadCalendar();
  await loadOverride();
}

// --- Ingredients UI ---
function bindIngredients(){
  $("ingList").addEventListener("change", ()=>{
    const id = parseInt($("ingList").value,10);
    state.selectedIngId = id;
    const ing = state.ingredients.find(x=>x.id===id);
    if(!ing) return;
    $("ingName").value = ing.name;
    $("ingUnit").value = ing.unit;
    $("ingPrice").value = ing.unit_price ?? "";
    $("ingCurrency").value = ing.price_currency ?? "BRL";
  });

  $("createIng").addEventListener("click", async ()=>{
    if(!state.token) return alert("Login necessário");
    const body = {
      name: $("ingName").value.trim(),
      unit: $("ingUnit").value.trim() || "und",
      unit_price: $("ingPrice").value ? parseFloat($("ingPrice").value) : null,
      price_currency: ($("ingCurrency").value.trim() || "BRL"),
    };
    await api("/api/ingredients", {method:"POST", headers: {"Content-Type":"application/json", ...authHeaders()}, body: JSON.stringify(body)});
    await refreshIngredients();
  });

  $("updateIng").addEventListener("click", async ()=>{
    if(!state.token) return alert("Login necessário");
    if(!state.selectedIngId) return alert("Selecione um ingrediente");
    const body = {
      name: $("ingName").value.trim(),
      unit: $("ingUnit").value.trim() || "und",
      unit_price: $("ingPrice").value ? parseFloat($("ingPrice").value) : null,
      price_currency: ($("ingCurrency").value.trim() || "BRL"),
    };
    await api(`/api/ingredients/${state.selectedIngId}`, {method:"PUT", headers: {"Content-Type":"application/json", ...authHeaders()}, body: JSON.stringify(body)});
    await refreshIngredients();
  });

  $("deleteIng").addEventListener("click", async ()=>{
    if(!state.token) return alert("Login necessário");
    if(!state.selectedIngId) return alert("Selecione um ingrediente");
    if(!confirm("Deletar ingrediente?")) return;
    try {
      await api(`/api/ingredients/${state.selectedIngId}`, {method:"DELETE", headers: authHeaders()});
      state.selectedIngId = null;
      await refreshIngredients();
      alert("Ingrediente deletado!");
    } catch(e){
      alert(e.message);
    }
  });
}

// --- Dishes UI ---
function bindDishes(){
  $("dishList").addEventListener("change", async ()=>{
    const id = parseInt($("dishList").value,10);
    state.selectedDishId = id;
    const dish = state.dishes.find(x=>x.id===id);
    if(!dish) return;
    $("dishName").value = dish.name;
    $("dishNotes").value = dish.notes ?? "";
    await loadDishIngredients();
  });

  $("createDish").addEventListener("click", async ()=>{
    if(!state.token) return alert("Login necessário");
    const body = { name: $("dishName").value.trim(), notes: $("dishNotes").value };
    await api("/api/dishes", {method:"POST", headers: {"Content-Type":"application/json", ...authHeaders()}, body: JSON.stringify(body)});
    await refreshDishes();
  });

  $("updateDish").addEventListener("click", async ()=>{
    if(!state.token) return alert("Login necessário");
    if(!state.selectedDishId) return alert("Selecione um prato");
    const body = { name: $("dishName").value.trim(), notes: $("dishNotes").value };
    await api(`/api/dishes/${state.selectedDishId}`, {method:"PUT", headers: {"Content-Type":"application/json", ...authHeaders()}, body: JSON.stringify(body)});
    await refreshDishes();
  });

  $("deleteDish").addEventListener("click", async ()=>{
    if(!state.token) return alert("Login necessário");
    if(!state.selectedDishId) return alert("Selecione um prato");
    if(!confirm("Deletar prato?")) return;
  
    try {
      await api(`/api/dishes/${state.selectedDishId}`, { method:"DELETE", headers: authHeaders() });
      state.selectedDishId = null;
      await refreshDishes();
      await loadCalendar();
      alert("Prato deletado!");
    } catch(e){
      alert(e.message);
    }
  });
  
  $("addDishIngredient").addEventListener("click", ()=>{
    if(!state.selectedDishId) return alert("Selecione um prato primeiro");
    const ingId = parseInt($("diIngredient").value,10);
    const amt = parseFloat($("diAmount").value);
    if(!ingId || isNaN(amt)) return alert("Escolha um ingrediente + quantidade");
    const unit = $("diUnit").value.trim() || null;
    state.dishIngredientDraft.push({ingredient_id: ingId, amount: amt, unit});
    $("diAmount").value = "";
    $("diUnit").value = "";
    renderDishIngredientDraft();
  });

  $("saveDishIngredients").addEventListener("click", async ()=>{
    if(!state.token) return alert("Login necessário");
    if(!state.selectedDishId) return alert("Selecione um prato");
    await api(`/api/dishes/${state.selectedDishId}/ingredients`, {
      method: "PUT",
      headers: {"Content-Type":"application/json", ...authHeaders()},
      body: JSON.stringify({ items: state.dishIngredientDraft })
    });
    alert("Ingredientes do prato salvos!");
    await loadDishIngredients();
  });
}

async function loadDishIngredients(){
  if(!state.selectedDishId){
    $("dishIngredients").innerHTML = "<div class='small'>Selecione um prato.</div>";
    return;
  }
  const list = await api(`/api/dishes/${state.selectedDishId}/ingredients`);
  state.dishIngredientDraft = list.map(x=>({ingredient_id:x.ingredient_id, amount:x.amount, unit:x.unit}));
  renderDishIngredientDraft();
}

function renderDishIngredientDraft(){
  const out = $("dishIngredients");
  if(!state.dishIngredientDraft.length){
    out.innerHTML = "<div class='small'>(nenhum ingrediente ainda)</div>";
    return;
  }
  const byId = Object.fromEntries(state.ingredients.map(i=>[i.id,i]));
  out.innerHTML = state.dishIngredientDraft.map((x, idx)=>{
    const ing = byId[x.ingredient_id];
    const name = ing ? ing.name : `#${x.ingredient_id}`;
    const unit = x.unit || (ing ? ing.unit : "und");
    return `<div class="row" style="justify-content:space-between;border-bottom:1px solid rgba(255,255,255,0.06);padding:6px 0">
      <div>${name}</div>
      <div class="small">${x.amount} ${unit}</div>
      <button class="ghost danger" data-del="${idx}">Remover</button>
    </div>`;
  }).join("");

  out.querySelectorAll("button[data-del]").forEach(btn=>{
    btn.addEventListener("click", ()=>{
      const idx = parseInt(btn.dataset.del,10);
      state.dishIngredientDraft.splice(idx,1);
      renderDishIngredientDraft();
    });
  });
}

// --- Shopping UI ---
function bindShopping(){
  $("loadShopping").addEventListener("click", async ()=>{
    const start = $("shopStart").value;
    const end = $("shopEnd").value;
    if(!start || !end) return alert("Selecione datas de início e fim");
    const data = await api(`/api/shopping?start=${start}&end=${end}`);
    renderShopping(data);
  });
}

function renderShopping(data){
  const el = $("shoppingOut");
  if(!data.items.length){
    el.innerHTML = "<div class='small'>Sem itens. Adicione ingredientes de pratos e planeje refeições primeiro.</div>";
    return;
  }
  let html = "<table><thead><tr><th>Ingrediente</th><th>Quantidade</th><th>Preço de Unidade</th><th>Custo Estimado</th></tr></thead><tbody>";
  for(const it of data.items){
    const up = it.unit_price != null ? `${it.unit_price.toFixed(2)} ${it.price_currency}/${it.unit}` : "-";
    const cost = it.estimated_cost != null ? `${it.estimated_cost.toFixed(2)} ${it.price_currency}` : "-";
    html += `<tr><td>${it.ingredient_name}</td><td>${it.amount.toFixed(0)} ${it.unit}</td><td>${up}</td><td>${cost}</td></tr>`;
  }
  html += `</tbody></table>
    <div class="hint">Custo estimado total: <b>${data.estimated_total.toFixed(2)} ${data.currency || ""}</b></div>`;
  el.innerHTML = html;
}

// --- Boot ---
async function boot(){
  setTabs();
  fillYearMonth();
  setAuthUI();

  $("loginBtn").addEventListener("click", ()=>login().catch(e=>alert(e.message)));
  $("logoutBtn").addEventListener("click", logout);

  $("loadCalendar").addEventListener("click", ()=>loadCalendar().catch(e=>alert(e.message)));
  $("loadOverride").addEventListener("click", ()=>loadOverride().catch(e=>alert(e.message)));
  $("saveOverride").addEventListener("click", ()=>saveOverride().catch(e=>alert(e.message)));
  $("clearOverride").addEventListener("click", ()=>clearOverride().catch(e=>alert(e.message)));

  $("saveTemplate").addEventListener("click", ()=>saveTemplate().catch(e=>alert(e.message)));

  bindIngredients();
  bindDishes();
  bindShopping();

  // Load base data
  try {
    await refreshIngredients();
    await refreshDishes();
    await loadCalendar();
  } catch(e){
    alert("Backend not reachable. Start the Python API first.\n\n" + e.message);
  }

  // default dates for shopping: this month
  const now = new Date();
  const y = now.getFullYear();
  const m = now.getMonth(); // 0-based
  const start = new Date(y, m, 1);
  const end = new Date(y, m+1, 0);
  $("shopStart").value = start.toISOString().slice(0,10);
  $("shopEnd").value = end.toISOString().slice(0,10);
}

boot();
