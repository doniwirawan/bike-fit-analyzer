/* Light / dark / auto switch, shared by every page.

   "auto" is the absence of a stored choice, so a visitor who never touches this keeps
   following their OS — including when the OS flips at sunset. Picking light or dark writes
   data-theme onto <html>, which base.css weights above the prefers-color-scheme block.

   The value is read again by a tiny inline script in each <head>; that one has to run before
   first paint, or a dark-mode reader gets a white flash on every navigation. This file only
   handles the buttons. */
(function () {
  var root = document.documentElement, KEY = "bfa-theme";

  function apply(mode) {
    if (mode === "dark" || mode === "light") {
      root.dataset.theme = mode;
      try { localStorage.setItem(KEY, mode); } catch (e) {}
    } else {
      delete root.dataset.theme;
      try { localStorage.removeItem(KEY); } catch (e) {}
    }
    var buttons = document.querySelectorAll(".themesw button");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].setAttribute("aria-pressed", String(buttons[i].dataset.theme === (mode || "auto")));
    }
  }

  var stored = "auto";
  try { stored = localStorage.getItem(KEY) || "auto"; } catch (e) {}

  var buttons = document.querySelectorAll(".themesw button");
  for (var i = 0; i < buttons.length; i++) {
    buttons[i].addEventListener("click", function () { apply(this.dataset.theme); });
  }
  apply(stored);
})();
