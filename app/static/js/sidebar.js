(function () {
  const shell = document.querySelector(".app-shell");
  const toggleBtn = document.getElementById("sidebar-toggle-btn");
  if (!shell || !toggleBtn) return;

  toggleBtn.addEventListener("click", () => {
    const collapsed = shell.hasAttribute("data-sidebar-collapsed");
    if (collapsed) {
      shell.removeAttribute("data-sidebar-collapsed");
    } else {
      shell.setAttribute("data-sidebar-collapsed", "");
    }
    document.cookie = `sidebar_collapsed=${collapsed ? "0" : "1"}; path=/; max-age=31536000; samesite=lax`;
  });
})();
