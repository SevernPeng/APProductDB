(() => {
  const normalize = (value) => value.toLocaleLowerCase().replace(/[\s\-_]+/g, "");

  document.querySelectorAll("[data-product-autocomplete]").forEach((component) => {
    const search = component.querySelector("[data-product-search]");
    const value = component.querySelector("[data-product-value]");
    const menu = component.querySelector("[data-product-menu]");
    const options = Array.from(component.querySelectorAll("[data-product-option]"));
    const empty = component.querySelector("[data-product-empty]");
    let activeIndex = -1;

    const visibleOptions = () => options.filter((option) => !option.classList.contains("d-none"));
    const close = () => {
      menu.classList.add("d-none");
      search.setAttribute("aria-expanded", "false");
      activeIndex = -1;
    };
    const activate = (index) => {
      const visible = visibleOptions();
      visible.forEach((option) => option.classList.remove("active"));
      if (!visible.length) return;
      activeIndex = (index + visible.length) % visible.length;
      visible[activeIndex].classList.add("active");
      visible[activeIndex].scrollIntoView({ block: "nearest" });
    };
    const select = (option) => {
      search.value = option.dataset.label;
      value.value = option.dataset.value;
      search.setCustomValidity("");
      close();
      search.dispatchEvent(new Event("change", { bubbles: true }));
    };
    const filter = () => {
      const query = normalize(search.value.trim());
      let shown = 0;
      options.forEach((option) => {
        const matches = !query || normalize(option.dataset.search).includes(query);
        const show = matches && shown < 20;
        option.classList.toggle("d-none", !show);
        if (show) shown += 1;
      });
      if (empty) empty.classList.toggle("d-none", shown !== 0);
      menu.classList.remove("d-none");
      search.setAttribute("aria-expanded", "true");
      activeIndex = -1;
    };

    search.addEventListener("focus", filter);
    search.addEventListener("input", () => {
      const exact = options.find((option) => option.dataset.label === search.value);
      value.value = exact ? exact.dataset.value : "";
      search.setCustomValidity("");
      filter();
    });
    search.addEventListener("keydown", (event) => {
      const visible = visibleOptions();
      if (event.key === "ArrowDown") {
        event.preventDefault();
        activate(activeIndex + 1);
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        activate(activeIndex - 1);
      } else if (event.key === "Enter" && !menu.classList.contains("d-none") && visible.length) {
        event.preventDefault();
        select(visible[activeIndex >= 0 ? activeIndex : 0]);
      } else if (event.key === "Escape") {
        close();
      }
    });
    options.forEach((option) => option.addEventListener("click", () => select(option)));
    component.closest("form")?.addEventListener("submit", (event) => {
      if (search.value.trim() && !value.value) {
        search.setCustomValidity("请从自动联想列表中选择有效产品。");
        search.reportValidity();
        event.preventDefault();
      }
    });
    document.addEventListener("click", (event) => {
      if (!component.contains(event.target)) close();
    });
  });
})();
