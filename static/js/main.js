const themeSelect = document.querySelector('select[name="theme"]');
const htmlEl = document.documentElement;

// Загружаем сохранённую тему
const savedTheme = localStorage.getItem('theme');
if (savedTheme) {
  htmlEl.setAttribute('data-theme', savedTheme);
  if (themeSelect) themeSelect.value = savedTheme;
} else {
  // если не выбрано — авто
  htmlEl.removeAttribute('data-theme');
  if (themeSelect) themeSelect.value = 'auto';
}

// Слушаем изменение
if (themeSelect) {
  themeSelect.addEventListener('change', e => {
    const val = e.target.value;
    if (val === 'auto') {
      htmlEl.removeAttribute('data-theme');
      localStorage.removeItem('theme');
    } else {
      htmlEl.setAttribute('data-theme', val);
      localStorage.setItem('theme', val);
    }
  });
}

const avatarInput = document.querySelector('input[name="avatar"]');
if (avatarInput) {
  avatarInput.addEventListener('change', e => {
    const file = e.target.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      let img = document.getElementById('avatar-preview');
      if (!img) {
        img = document.createElement('img');
        img.id = 'avatar-preview';
        img.style.width = '120px';
        img.style.borderRadius = '50%';
        img.style.marginTop = '10px';
        avatarInput.parentNode.appendChild(img);
      }
      img.src = url;
    }
  });
}

// ---- utils ----


// ---- глобальное делегирование клика по кнопке удаления ----
document.addEventListener('click', async (e) => {
  const btn = e.target.closest('.js-diary-delete');
  if (!btn) return;

  e.preventDefault();
  const url = btn.dataset.url || `/diary/api/delete/${btn.dataset.id}/`;

  if (!confirm('Удалить запись?')) return;

  try {
    const res = await fetch(url, {
      method: 'DELETE',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'X-Requested-With': 'XMLHttpRequest'
      }
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error || `HTTP ${res.status}`);
    }

    const row = btn.closest('tr');
    if (row) {
      // небольшая анимация исчезновения
      row.style.transition = 'opacity .15s ease';
      row.style.opacity = '0';
      setTimeout(() => {
        row.remove();
        recalcDiaryTotals(btn);
      }, 150);
    }
  } catch (err) {
    console.error(err);
    alert('Ошибка при удалении записи.');
  }
});
// ==============================
// 🍳 Recipes module (list/form)
// ==============================
(function () {
  const ingList = document.getElementById('ing-list');
  if (!ingList) return; // не на странице рецептов

  console.log('🍳 Recipes module loaded');

  // csrf
  function getCookie(name) {
    let v = null;
    if (document.cookie) {
      for (let c of document.cookie.split(';')) {
        c = c.trim();
        if (c.startsWith(name + '=')) { v = decodeURIComponent(c.slice(name.length + 1)); break; }
      }
    }
    return v;
  }

  const debounce = (fn, ms=250) => { let t; return (...a)=>{ clearTimeout(t); t=setTimeout(()=>fn(...a),ms); }; };

  async function apiSearch(q) {
    const res = await fetch(`/recipes/api/products/?q=${encodeURIComponent(q)}`);
    if (!res.ok) return [];
    const data = await res.json().catch(()=>({results:[]}));
    return data.results || [];
  }

  function renderResults(row, items) {
    const box = row.querySelector('.ing-results');
    if (!box) return;
    if (!items.length) { box.innerHTML=''; box.style.display='none'; return; }
    box.innerHTML = items.map(p=>`
      <div class="ing-result" data-id="${p.id}" data-name="${p.name}" data-brand="${p.brand||''}"
           data-kcal="${p.kcal||0}" data-p="${p.p||0}" data-f="${p.f||0}" data-c="${p.c||0}">
        <span>${p.name}${p.brand?` <span class="brand">(${p.brand})</span>`:''}</span>
        <span class="meta">${Math.round(p.kcal||0)} ккал</span>
      </div>`).join('');
    box.style.display='block';
  }

  function fillProduct(row, product) {
    const idx = row.dataset.index;
    const hidden = row.querySelector(`#id_recipeingredient_set-${idx}-product`);
    if (hidden) hidden.value = product.id;
    const input = row.querySelector('.ing-search-input');
    if (input) input.value = product.name + (product.brand ? ` (${product.brand})` : '');
    const hint = row.querySelector('.ing-hint');
    if (hint) hint.textContent = `100 г: ${Math.round(product.kcal||0)} ккал • Б ${product.p||0} • Ж ${product.f||0} • У ${product.c||0}`;
    const box = row.querySelector('.ing-results'); if (box) { box.innerHTML=''; box.style.display='none'; }
    previewTotals(); // сразу пересчёт
  }

  function addRow() {
    const total = document.getElementById('id_recipeingredient_set-TOTAL_FORMS');
    const idx = parseInt(total.value, 10);
    const tpl = document.getElementById('ing-empty-template');
    if (!tpl) { console.error('❌ ing-empty-template missing'); return; }
    const html = tpl.innerHTML.replace(/__prefix__/g, idx);
    const tmp = document.createElement('div');
    tmp.innerHTML = html.trim();
    const row = tmp.firstElementChild;
    row.dataset.index = String(idx);
    ingList.appendChild(row);
    total.value = idx + 1;
  }




  function markDelete(row) {
    const idx = row.dataset.index;
    const del = row.querySelector(`#id_recipeingredient_set-${idx}-DELETE`);
    if (del) del.checked = true; // это чекбокс — именно checked!
    row.classList.add('deleted');
    row.style.display = 'none';
    previewTotals();
  }

  // превью итогов через API
  async function previewTotals() {
    const items = [];
    ingList.querySelectorAll('.ing-row:not(.deleted)').forEach(row=>{
      const idx = row.dataset.index;
      const productId = Number(row.querySelector(`#id_recipeingredient_set-${idx}-product`)?.value || 0);
      const amount = Number(row.querySelector(`#id_recipeingredient_set-${idx}-amount`)?.value || 0);
      const unit = row.querySelector(`#id_recipeingredient_set-${idx}-unit`)?.value || 'g';
      const piece = Number(row.querySelector(`#id_recipeingredient_set-${idx}-piece_grams`)?.value || 0);
      if (productId && amount>0) items.push({product_id:productId, amount, unit, piece_grams:piece});
    });
    const servings = Number(document.getElementById('id_servings')?.value || 1);

    const res = await fetch('/recipes/api/preview/', {
      method: 'POST',
      headers: { 'Content-Type':'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify({ items, servings })
    });
    if (!res.ok) return;
    const { totals } = await res.json();

    const set = (k,v)=>{ const el=document.querySelector(`[data-t="${k}"]`); if(el) el.textContent=v; };
    set('g', totals.grams);
    set('kcal', totals.kcal);
    set('p', totals.p);
    set('f', totals.f);
    set('c', totals.c);
    set('per100', totals.per100_kcal);
    set('perServing', totals.per_serving_kcal);
  }

  // делегирование
  ingList.addEventListener('input', debounce(async (e)=>{
    const inp = e.target.closest('.ing-search-input');
    if (inp) {
      const row = e.target.closest('.ing-row');
      const q = inp.value.trim();
      if (q.length < 2) { renderResults(row, []); return; }
      renderResults(row, await apiSearch(q));
    }
    if (e.target.matches('.ing-amount, .ing-unit-select, .ing-piece')) previewTotals();
  }, 250));

  ingList.addEventListener('click', (e)=>{
    const item = e.target.closest('.ing-result');
    if (item) {
      const row = e.target.closest('.ing-row');
      fillProduct(row, {
        id:Number(item.dataset.id), name:item.dataset.name, brand:item.dataset.brand,
        kcal:Number(item.dataset.kcal), p:Number(item.dataset.p),
        f:Number(item.dataset.f), c:Number(item.dataset.c)
      });
      return;
    }
    const delBtn = e.target.closest('.js-ing-remove');
    if (delBtn) {
      markDelete(e.target.closest('.ing-row'));
    }
  });

  ingList.addEventListener('change', (e)=>{
    const sel = e.target.closest('.ing-unit-select');
    if (!sel) return;
    const row = e.target.closest('.ing-row');
    const pg = row.querySelector('.ing-piece-grams');
    if (pg) pg.style.display = sel.value === 'pcs' ? '' : 'none';
    previewTotals();
  });

  document.getElementById('add-row')?.addEventListener('click', addRow);
  document.getElementById('id_servings')?.addEventListener('input', debounce(previewTotals, 250));

  // первичный пересчёт
  previewTotals();
})();

// Открыть/закрыть меню
const menuBtn  = document.getElementById('menuToggle');
const backdrop = document.getElementById('backdrop');

menuBtn?.addEventListener('click', () => {
  document.body.classList.toggle('nav-open');
});
backdrop?.addEventListener('click', () => {
  document.body.classList.remove('nav-open');
});
// Закрытие по ESC
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') document.body.classList.remove('nav-open');
});
// Клик по пункту меню — тоже закрывает
document.querySelectorAll('.sidebar a').forEach(a => {
  a.addEventListener('click', () => document.body.classList.remove('nav-open'));
});

// =========================
// 🔥 Перенос плана в дневник
// =========================
// 📥 Перенос плана в дневник
document.addEventListener('click', async (e) => {
  const btn = e.target.closest('.js-planner-transfer');
  if (!btn) return;

  const url = btn.dataset.url;
  try {
    const res = await fetch(url, {
      method: 'DELETE',
      headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    const data = await res.json();
    console.log('TRANSFER DATA:', data);

    if (!data.success) return;

    // 🧽 Удаляем строку плана
    const row = btn.closest('tr');
    if (row) {
      row.style.transition = 'opacity 0.15s ease';
      row.style.opacity = '0';
      setTimeout(() => {
        row.remove();
        checkPlannerEmpty();
      }, 150);
    }

    // 🆕 Вставляем запись в дневник
    const diaryTable = document.querySelector('.diary-table tbody');
    if (!diaryTable) return;

    const newRow = document.createElement('tr');
    newRow.dataset.entryId = data.id;
    newRow.innerHTML = `
      <td>${data.time}</td>
      <td>${data.name}</td>
      <td>${data.grams}</td>
      <td>${data.kcal}</td>
      <td>${data.protein}</td>
      <td>${data.fat}</td>
      <td>${data.carbs}</td>
      <td class="actions">
        <button class="js-diary-delete" data-url="${data.delete_url}" title="Удалить">🗑️</button>
      </td>
    `;

    // ✨ Анимация появления
    newRow.style.opacity = '0';
    diaryTable.appendChild(newRow);
    setTimeout(() => {
      newRow.style.transition = 'opacity 0.25s ease';
      newRow.style.opacity = '1';
    }, 10);

    recalcDiaryTotals(newRow);
  } catch (err) {
    console.error('Ошибка переноса плана:', err);
    location.reload();

  }
});

// ✅ Универсальный пересчёт итогов
function recalcDiaryTotals(fromEl) {
  const table = fromEl?.closest?.('.diary-table') || document.querySelector('.diary-table');
  if (!table) return;

  let kcal = 0, p = 0, f = 0, c = 0;
  table.querySelectorAll('tbody tr').forEach(row => {
    const cells = row.children;
    kcal += Number(cells[3]?.textContent) || 0;
    p    += Number(cells[4]?.textContent) || 0;
    f    += Number(cells[5]?.textContent) || 0;
    c    += Number(cells[6]?.textContent) || 0;
  });

  table.querySelector('#total-kcal').textContent = Math.round(kcal);
  table.querySelector('#total-p').textContent = Math.round(p);
  table.querySelector('#total-f').textContent = Math.round(f);
  table.querySelector('#total-c').textContent = Math.round(c);
}

// 🧹 Проверка на пустую таблицу планов
function checkPlannerEmpty() {
  const plannerTable = document.querySelector('.planner-table');
  if (!plannerTable) return;
  const rows = plannerTable.querySelectorAll('tbody tr');
  const msgId = 'no-plans-msg';

  if (rows.length === 0) {
    plannerTable.style.display = 'none';
    if (!document.querySelector(`#${msgId}`)) {
      const msg = document.createElement('p');
      msg.id = msgId;
      msg.textContent = '📭 Нет запланированных приёмов';
      plannerTable.parentNode.appendChild(msg);
    }
  } else {
    plannerTable.style.display = '';
    const msg = document.querySelector(`#${msgId}`);
    if (msg) msg.remove();
  }
}

// подсветка активного пункта топ-навигации (если нужно)
(function(){
  const path = location.pathname.replace(/\/+$/, '');
  document.querySelectorAll('.actions a[href^="/"]').forEach(a=>{
    const href = a.getAttribute('href').replace(/\/+$/, '');
    if (href && href !== '/' && path.startsWith(href)) a.classList.add('active');
  });
})();


