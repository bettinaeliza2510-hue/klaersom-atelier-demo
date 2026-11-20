// KlærSøm front-end helpers. The page works without JavaScript; this only adds conveniences.
(function () {
  // Sample-size buttons fill the measurement fields (the user can still edit every value).
  document.querySelectorAll("[data-preset]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var preset = window.KLAERSOM_PRESETS[btn.dataset.preset];
      Object.keys(preset).forEach(function (key) {
        var field = document.getElementById(key);
        if (field) field.value = preset[key];
      });
    });
  });

  // Live value next to each slider.
  document.querySelectorAll("input[type=range]").forEach(function (slider) {
    var out = document.querySelector('output[data-for="' + slider.id + '"]');
    slider.addEventListener("input", function () { if (out) out.textContent = slider.value; });
  });

  // Reference-image preview, with drag-and-drop highlight. Only present on the studio page.
  var input = document.getElementById("reference_image");
  var preview = document.getElementById("preview");
  var zone = document.getElementById("dropzone");
  var text = document.getElementById("dropText");
  if (input && preview && zone && text) {
    var showFile = function () {
      var file = input.files && input.files[0];
      if (!file) { preview.hidden = true; return; }
      if (preview.dataset.url) URL.revokeObjectURL(preview.dataset.url);
      preview.dataset.url = URL.createObjectURL(file);
      preview.src = preview.dataset.url;
      preview.hidden = false;
      text.textContent = file.name;
    };
    input.addEventListener("change", showFile);
    ["dragenter", "dragover"].forEach(function (ev) {
      zone.addEventListener(ev, function (e) { e.preventDefault(); zone.classList.add("over"); });
    });
    ["dragleave", "drop"].forEach(function (ev) {
      zone.addEventListener(ev, function () { zone.classList.remove("over"); });
    });
    zone.addEventListener("drop", function (e) {
      e.preventDefault();
      if (e.dataTransfer.files.length) { input.files = e.dataTransfer.files; showFile(); }
    });
  }

  // Stop double submissions and show progress while the server drafts.
  var form = document.getElementById("designForm");
  var submit = document.getElementById("submitBtn");
  if (form && submit) {
    form.addEventListener("submit", function () {
      if (form.checkValidity()) {
        submit.disabled = true;
        submit.classList.add("is-loading");
        submit.textContent = "Drafting your pattern...";
      }
    });

    // If the user comes back with the browser's Back button, make the button usable again.
    window.addEventListener("pageshow", function () {
      submit.disabled = false;
      submit.classList.remove("is-loading");
      submit.textContent = "Draft my dress pattern";
    });
  }

  // Jump to the results after drafting.
  var results = document.getElementById("results");
  if (results) results.scrollIntoView({ behavior: "smooth" });

  // Gentle fade/slide-in for the main sections as they enter view.
  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && reveals.length) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("in");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08 });
    reveals.forEach(function (el) { observer.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("in"); });
  }

  // Back-to-top button, shown once the page has scrolled a little.
  var toTop = document.getElementById("toTop");
  if (toTop) {
    toTop.hidden = false;
    var toggleToTop = function () { toTop.classList.toggle("show", window.scrollY > 420); };
    window.addEventListener("scroll", toggleToTop, { passive: true });
    toggleToTop();
    toTop.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: "smooth" }); });
  }

  // Slim the fixed nav bar down once the hero has scrolled past.
  var topbar = document.getElementById("topbar");
  if (topbar) {
    var toggleTopbar = function () { topbar.classList.toggle("scrolled", window.scrollY > 40); };
    window.addEventListener("scroll", toggleTopbar, { passive: true });
    toggleTopbar();
  }
})();
