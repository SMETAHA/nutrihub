console.log("📜 diary.js подключён");

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("editModal");
    const closeModal = document.getElementById("closeModal");
    const gramsInput = document.getElementById("editGrams");
    const timeInput = document.getElementById("editTime");
    const form = document.getElementById("editForm");
    let currentId = null;

    // ==========================
    // 🖊️ Открытие модалки поверх любой другой
    // ==========================
    document.body.addEventListener("click", async (e) => {
        const editBtn = e.target.closest(".btn-edit");
        if (editBtn) {
            e.stopPropagation(); // 🔸 блокируем всплытие для конфликтов с другими модалками
            currentId = editBtn.dataset.id;
            try {
                const res = await fetch(`/diary/api/get/${currentId}/`);
                if (!res.ok) throw new Error("Ошибка загрузки");
                const data = await res.json();

                gramsInput.value = data.grams;
                timeInput.value = data.time;
                modal.classList.remove("hidden");
            } catch (err) {
                console.error(err);
                alert("Не удалось загрузить данные записи.");
            }
        }
    });

    // ==========================
    // 💾 Сохранение
    // ==========================
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!currentId) return;

        const formData = new FormData();
        formData.append("grams", gramsInput.value);
        formData.append("time", timeInput.value);

        try {
            const res = await fetch(`/diary/api/edit/${currentId}/`, {
                method: "POST",
                headers: {"X-CSRFToken": getCookie("csrftoken")},
                body: formData
            });

            if (!res.ok) throw new Error("Ошибка редактирования");
            const data = await res.json();

            const row = document.querySelector(`tr[data-entry-id="${currentId}"]`);
            row.children[0].textContent = data.time;
            row.children[2].textContent = data.grams;
            row.children[3].textContent = data.kcal;
            row.children[4].textContent = data.p;
            row.children[5].textContent = data.f;
            row.children[6].textContent = data.c;

            recalcTotals();
            modal.classList.add("hidden");
        } catch (err) {
            console.error(err);
            alert("Не удалось сохранить изменения.");
        }
    });

    // ==========================
    // 🗑️ Удаление без перезагрузки
    // ==========================
    document.body.addEventListener("click", async (e) => {
        const deleteBtn = e.target.closest(".btn-delete");
        if (deleteBtn) {
            e.stopPropagation();
            const entryId = deleteBtn.dataset.id;
            if (!confirm("Удалить запись?")) return;

            try {
                const res = await fetch(`/diary/api/delete/${entryId}/`, {
                    method: "DELETE",
                    headers: {"X-CSRFToken": getCookie("csrftoken")}
                });

                if (!res.ok) throw new Error("Ошибка удаления");
                const row = document.querySelector(`tr[data-entry-id="${entryId}"]`);
                if (row) row.remove();
                recalcTotals();
            } catch (err) {
                console.error(err);
                alert("Не удалось удалить запись.");
            }
        }
    });

    // ==========================
    // ❌ Закрытие модалки
    // ==========================
    closeModal.addEventListener("click", () => modal.classList.add("hidden"));
    modal.addEventListener("click", (e) => {
        if (e.target === modal) modal.classList.add("hidden");
    });

    // ==========================
    // 📊 Пересчёт итогов БЖУ/ккал
    // ==========================
})