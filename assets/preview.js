// Progressive enhancement: the page and bilingual preview work without JavaScript.
const modes = document.querySelector('.preview-modes');
const captions = document.querySelector('.captions');
if (modes && captions) {
  modes.hidden = false;
  modes.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-mode]');
    if (!button) return;
    captions.className = `captions ${button.dataset.mode}`;
    modes.querySelectorAll('button').forEach((item) => {
      item.setAttribute('aria-pressed', String(item === button));
    });
  });
}
