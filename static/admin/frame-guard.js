"use strict";

// GitHub Pages cannot deliver frame-ancestors or X-Frame-Options headers.
// Stop loading the editor if another site tries to embed it in a frame.
if (window.self !== window.top) {
  window.stop();
  document.documentElement.textContent = "";
}
