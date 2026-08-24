(function () {
  var endpoint = 'https://beacon-telemetry.alicempektas.workers.dev/web';
  var visitID;

  function randomID() {
    if (window.crypto && typeof window.crypto.randomUUID === 'function') {
      return 'web-' + window.crypto.randomUUID();
    }
    return 'web-' + Date.now().toString(16) + '-' + Math.random().toString(16).slice(2);
  }

  try {
    visitID = window.sessionStorage.getItem('beacon-web-visit');
    if (!visitID) {
      visitID = randomID();
      window.sessionStorage.setItem('beacon-web-visit', visitID);
    }
  } catch (_) {
    visitID = randomID();
  }

  function record(event) {
    var body = JSON.stringify({
      event: event,
      source: 'organic_search',
      visit_id: visitID,
      event_id: randomID()
    });
    var blob = new Blob([body], { type: 'text/plain;charset=UTF-8' });
    if (navigator.sendBeacon && navigator.sendBeacon(endpoint, blob)) return;
    fetch(endpoint, { method: 'POST', body: blob, keepalive: true }).catch(function () {});
  }

  record('web_landing_view');
  document.querySelectorAll('[data-download]').forEach(function (link) {
    link.addEventListener('click', function () { record('web_download_click'); }, { once: true });
  });
})();
