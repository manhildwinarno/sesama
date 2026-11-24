export default function ({parentElement, setTriggerValue}) {
  const button = parentElement.querySelector('button');
  const status = parentElement.querySelector('[role="status"]');
  const microphoneIcon = button.innerHTML;
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) {
    button.disabled = true;
    status.textContent = 'Speech input unavailable. Use Chrome or Edge, or type below.';
    return;
  }
  const recognition = new Recognition();
  recognition.lang = 'id-ID';
  recognition.continuous = false;
  recognition.interimResults = true;
  let active = false;
  let failed = false;
  const reset = () => {
    active = false;
    button.setAttribute('aria-pressed', 'false');
    button.setAttribute('aria-label', 'Turn microphone on');
    button.innerHTML = microphoneIcon;
  };
  button.onclick = () => {
    if (active) { recognition.stop(); return; }
    failed = false;
    try {
      recognition.start();
      active = true;
      button.setAttribute('aria-pressed', 'true');
      button.setAttribute('aria-label', 'Turn microphone off');
      button.textContent = '■';
      status.textContent = 'Listening… Speak now.';
    } catch {
      reset();
      status.textContent = 'Microphone could not start. Try again.';
    }
  };
  recognition.onresult = event => {
    let final = '', interim = '';
    for (let i = 0; i < event.results.length; i++) {
      if (event.results[i].isFinal) final += event.results[i][0].transcript;
      else interim += event.results[i][0].transcript;
    }
    status.textContent = interim || final || 'Listening…';
    if (final.trim()) {
      setTriggerValue('transcript', final.trim().slice(0, 120));
      recognition.stop();
    }
  };
  recognition.onerror = event => {
    failed = true;
    const messages = {'not-allowed':'Microphone permission denied. Allow access in browser settings.', 'no-speech':'No speech detected. Try again.', 'audio-capture':'No microphone available.', 'network':'Speech service unavailable. Check your connection.'};
    status.textContent = messages[event.error] || 'Speech recognition failed. Try again or type below.';
    reset();
  };
  recognition.onend = () => {
    reset();
    if (!failed && status.textContent.startsWith('Listening')) status.textContent = 'Microphone off. Tap to try again.';
  };
  const stop = () => recognition.abort();
  const visibility = () => { if (document.hidden) stop(); };
  window.addEventListener('pagehide', stop);
  document.addEventListener('visibilitychange', visibility);
  return () => {
    recognition.onresult = recognition.onerror = recognition.onend = null;
    recognition.abort();
    window.removeEventListener('pagehide', stop);
    document.removeEventListener('visibilitychange', visibility);
  };
}
