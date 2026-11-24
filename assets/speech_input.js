export default function ({parentElement, setTriggerValue}) {
  const button = parentElement.querySelector('button');
  const status = parentElement.querySelector('[role="status"]');
  const microphoneIcon = button.innerHTML;
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) {
    button.disabled = true;
    status.textContent = 'Browser unsupported';
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
      status.textContent = 'Listening…';
    } catch {
      reset();
      status.textContent = 'Could not start';
    }
  };
  recognition.onresult = event => {
    let final = '';
    for (let i = 0; i < event.results.length; i++) {
      if (event.results[i].isFinal) final += event.results[i][0].transcript;
    }
    status.textContent = final.trim() ? 'Speech captured' : 'Listening…';
    if (final.trim()) {
      setTriggerValue('transcript', final.trim().slice(0, 120));
      recognition.stop();
    }
  };
  recognition.onerror = event => {
    failed = true;
    const messages = {'not-allowed':'Microphone permission denied', 'no-speech':'No speech detected', 'audio-capture':'No microphone found', 'network':'Service unavailable'};
    status.textContent = messages[event.error] || 'Speech recognition failed';
    reset();
  };
  recognition.onend = () => {
    reset();
    if (!failed && status.textContent.startsWith('Listening')) status.textContent = 'Microphone off';
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
