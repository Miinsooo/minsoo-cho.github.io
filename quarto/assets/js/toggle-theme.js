(function () {
  var root = document.documentElement;
  var icon = document.getElementById("theme-icon");
  var btn = document.getElementById("theme-toggle-btn");

  function syncIcon() {
    if (!icon) return;
    var isDark = root.getAttribute("data-theme") === "dark";
    icon.classList.toggle("fa-sun", !isDark);
    icon.classList.toggle("fa-moon", isDark);
  }

  syncIcon();

  if (btn) {
    btn.addEventListener("click", function () {
      var isDark = root.getAttribute("data-theme") === "dark";
      if (isDark) {
        root.removeAttribute("data-theme");
        try { localStorage.setItem("theme", "light"); } catch (e) {}
      } else {
        root.setAttribute("data-theme", "dark");
        try { localStorage.setItem("theme", "dark"); } catch (e) {}
      }
      syncIcon();
    });
  }
})();
