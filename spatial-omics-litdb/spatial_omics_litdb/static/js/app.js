const form = document.querySelector("#filter-form");
if (form) {
  form.querySelectorAll("select").forEach((el) => {
    el.addEventListener("change", () => form.requestSubmit());
  });
  form.addEventListener("submit", () => {
    form.querySelectorAll("input, select").forEach((el) => {
      if (!el.value) el.disabled = true;
    });
  });
}
