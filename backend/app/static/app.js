const form = document.querySelector('#auth-form');
const statusMessage = document.querySelector('#status');
const formTitle = document.querySelector('#form-title');
const submitButton = document.querySelector('#submit-button');
let mode = 'login';

document.querySelectorAll('.tab').forEach((tab) => {
  tab.addEventListener('click', () => {
    mode = tab.dataset.mode;
    document.querySelectorAll('.tab').forEach((item) => item.classList.toggle('active', item === tab));
    formTitle.textContent = mode === 'login' ? 'Sign in' : 'Create account';
    submitButton.innerHTML = mode === 'login' ? 'Continue <span>-></span>' : 'Create account <span>-></span>';
    statusMessage.textContent = '';
  });
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  statusMessage.textContent = '';
  submitButton.disabled = true;
  let response;
  let data;
  try {
    response = await fetch(`/auth/${mode}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: form.email.value, password: form.password.value }) });
    data = await response.json();
  } catch {
    statusMessage.textContent = 'The server is unavailable. Check that Uvicorn is running.';
    submitButton.disabled = false;
    return;
  }
  submitButton.disabled = false;
  if (!response.ok) { statusMessage.textContent = data.detail || 'Something went wrong.'; return; }
  if (mode === 'register') { mode = 'login'; document.querySelector('[data-mode="login"]').click(); statusMessage.textContent = data.message; form.password.value = ''; return; }
  document.querySelector('.shell').innerHTML = `<section class="intro"><p class="eyebrow">SMART HOSTEL</p><h1>Welcome home.</h1><p class="intro-copy">You are signed in as ${data.email}. This is your starting point; the workspace comes next.</p></section>`;
});