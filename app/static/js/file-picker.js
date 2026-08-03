(() => {
  document.querySelectorAll("[data-file-picker]").forEach((picker) => {
    const input = picker.querySelector('input[type="file"]');
    const fileName = picker.querySelector("[data-file-name]");

    if (!input || !fileName) return;

    const updateFileName = () => {
      fileName.textContent = input.files?.[0]?.name || "No file chosen";
    };

    input.addEventListener("change", updateFileName);
    updateFileName();
  });
})();
