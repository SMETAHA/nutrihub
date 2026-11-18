console.log("🍳 recipes_new.js loaded");

let ingredients = [];
let selectedProduct = null;

// Если редактирование — парсим JSON из скрытого поля
const ingredientsField = document.getElementById("ingredients_json");
try {
  ingredients = JSON.parse(ingredientsField.value || "[]");
} catch {
  ingredients = [];
}

const list = document.getElementById("ingredient-list");
const searchInput = document.getElementById("product-search");
const resultsBox = document.getElementById("product-results");
const amountInput = document.getElementById("product-amount");
const unitSelect = document.getElementById("product-unit");
const pieceInput = document.getElementById("product-piece");

function renderList() {
  list.innerHTML = "";
  let totalKcal = 0;

  ingredients.forEach((ing, i) => {
    const gramsEq = ing.unit === "pcs" ? (ing.amount * (ing.piece_grams || 0)) : ing.amount;
    const kcal = (ing.kcal || 0) * (gramsEq / 100);
    totalKcal += kcal;

    const row = document.createElement("div");
    row.className = "ingredient-item";
    row.innerHTML = `
      <div class="left">
        <span>🥄</span>
        <span><b>${ing.name}</b></span>
        <span class="pill">${ing.amount}${ing.unit}${ing.unit === 'pcs' && ing.piece_grams ? ` · ${ing.piece_grams} г/шт` : ''}</span>
        <span class="kcal">(${Math.round(kcal)} ккал)</span>
      </div>
      <button type="button" class="del-ing" data-i="${i}" title="Удалить">✕</button>
    `;
    list.appendChild(row);
  });

  document.getElementById("total-kcal").textContent = Math.round(totalKcal);
  ingredientsField.value = JSON.stringify(ingredients);
}


function renderResults(items) {
  resultsBox.innerHTML = "";
  for (const item of items) {
    const div = document.createElement("div");
    div.className = "result-item";
    div.textContent = `${item.name} (${item.kcal} ккал)`;
    div.onclick = () => {
      selectedProduct = item;
      searchInput.value = item.name;
      resultsBox.innerHTML = "";
    };
    resultsBox.appendChild(div);
  }
}

let searchTimeout;
searchInput.addEventListener("input", () => {
  clearTimeout(searchTimeout);
  const q = searchInput.value.trim();
  if (q.length < 2) {
    resultsBox.innerHTML = "";
    return;
  }
  searchTimeout = setTimeout(async () => {
    const res = await fetch(`/recipes/api/products/?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    renderResults(data.results);
  }, 300);
});

unitSelect.addEventListener("change", () => {
  pieceInput.style.display = unitSelect.value === "pcs" ? "" : "none";
});

document.getElementById("add-ingredient").addEventListener("click", () => {
  if (!selectedProduct) return alert("Выберите продукт");
  const amount = parseFloat(amountInput.value) || 0;
  if (amount <= 0) return alert("Укажите количество");

  ingredients.push({
    product_id: selectedProduct.id,
    name: selectedProduct.name,
    brand: selectedProduct.brand,
    amount: amount,
    unit: unitSelect.value,
    piece_grams: parseFloat(pieceInput.value) || 0,
    kcal: selectedProduct.kcal,
    p: selectedProduct.p,
    f: selectedProduct.f,
    c: selectedProduct.c
  });

  selectedProduct = null;
  searchInput.value = "";
  amountInput.value = "";
  pieceInput.value = "";
  renderList();
});

list.addEventListener("click", (e) => {
  if (e.target.classList.contains("del-ing")) {
    const idx = parseInt(e.target.dataset.i);
    ingredients.splice(idx, 1);
    renderList();
  }
});

// при загрузке отрисовываем существующие ингредиенты
renderList();
