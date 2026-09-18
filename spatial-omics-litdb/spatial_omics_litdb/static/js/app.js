document.querySelectorAll("#filter-form select").forEach((el) => {
  el.addEventListener("change", () => el.form.requestSubmit());
});
