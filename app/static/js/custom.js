/* ============================================================
   PneumoDetect — Custom JavaScript
   ============================================================ */

(function () {
  'use strict';

  // ── Auto-dismiss flash alerts after 5 seconds ──────────────
  document.addEventListener('DOMContentLoaded', function () {
    var alerts = document.querySelectorAll('.alert.alert-dismissible');
    alerts.forEach(function (alert) {
      setTimeout(function () {
        var bsAlert = $(alert);
        if (bsAlert.length) {
          bsAlert.fadeTo(500, 0, function () {
            bsAlert.slideUp(300, function () { bsAlert.remove(); });
          });
        }
      }, 5000);
    });

    // ── Animate progress bars on result page ─────────────────
    var bars = document.querySelectorAll('.progress-bar');
    bars.forEach(function (bar) {
      var target = bar.style.width;
      bar.style.width = '0%';
      setTimeout(function () {
        bar.style.width = target;
      }, 200);
    });

    // ── File size client-side check ───────────────────────────
    var fileInput = document.getElementById('image');
    if (fileInput) {
      fileInput.addEventListener('change', function () {
        var maxBytes = 5 * 1024 * 1024; // 5 MB
        if (this.files && this.files[0]) {
          if (this.files[0].size > maxBytes) {
            alert('File is too large. Maximum allowed size is 5 MB.');
            this.value = '';
            var previewBox = document.getElementById('previewContainer');
            if (previewBox) previewBox.classList.add('d-none');
          }
        }
      });
    }

    // ── Tooltip initialisation (Bootstrap 4) ─────────────────
    $('[data-toggle="tooltip"]').tooltip();

    // ── Confirm logout ────────────────────────────────────────
    var logoutLink = document.querySelector('a[href*="logout"]');
    if (logoutLink) {
      logoutLink.addEventListener('click', function (e) {
        if (!confirm('Are you sure you want to log out?')) {
          e.preventDefault();
        }
      });
    }
  });

})();
