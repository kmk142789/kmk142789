const form = document.getElementById('assistantForm');
const input = document.getElementById('chatInput');
const history = document.getElementById('chatHistory');
const statusEl = document.getElementById('assistantStatus');
const codexLimit = document.getElementById('codexLimit');

function appendMessage(role, content, extras = {}) {
  const entry = document.createElement('article');
  entry.className = `chat-entry chat-entry--${role}`;

  const roleEl = document.createElement('div');
  roleEl.className = 'chat-entry__role';
  roleEl.textContent = role === 'user' ? 'You' : 'Assistant';

  const contentEl = document.createElement('p');
  contentEl.className = 'chat-entry__content';
  contentEl.textContent = content;

  entry.appendChild(roleEl);
  entry.appendChild(contentEl);

  if (extras.suggestion) {
    entry.appendChild(renderSuggestion(extras.suggestion));
  }

  if (extras.toolCalls && extras.toolCalls.length) {
    entry.appendChild(renderToolCalls(extras.toolCalls));
  }

  if (extras.logs && extras.logs.length) {
    entry.appendChild(renderLogs(extras.logs));
  }

  history.appendChild(entry);
  history.scrollTop = history.scrollHeight;
}

function renderSuggestion(suggestion) {
  const details = document.createElement('details');
  details.className = 'chat-tools';
  details.open = true;

  const summary = document.createElement('summary');
  summary.textContent = 'Assistant program suggestion';
  details.appendChild(summary);

  const description = document.createElement('p');
  description.textContent = suggestion.description || 'No description available.';
  details.appendChild(description);

  const required = document.createElement('p');
  required.textContent = `Required inputs: ${suggestion.required_inputs.join(', ') || 'none'}`;
  details.appendChild(required);

  const program = document.createElement('pre');
  program.textContent = suggestion.program || '';
  details.appendChild(program);

  return details;
}

function renderToolCalls(calls) {
  const wrapper = document.createElement('details');
  wrapper.className = 'chat-tools';
  wrapper.open = true;

  const summary = document.createElement('summary');
  summary.textContent = `Tool calls (${calls.length})`;
  wrapper.appendChild(summary);

  const list = document.createElement('ul');
  calls.forEach((call) => {
    const item = document.createElement('li');
    const header = document.createElement('div');
    header.textContent = `${call.name}(${JSON.stringify(call.arguments)})`;
    item.appendChild(header);

    if (call.success === false) {
      const error = document.createElement('p');
      error.textContent = `Error: ${call.error}`;
      item.appendChild(error);
    } else if (call.result !== null && call.result !== undefined) {
      const result = document.createElement('pre');
      result.textContent = JSON.stringify(call.result, null, 2);
      item.appendChild(result);
    }
    list.appendChild(item);
  });
  wrapper.appendChild(list);
  return wrapper;
}

function renderLogs(logs) {
  const details = document.createElement('details');
  details.className = 'chat-tools';
  details.open = false;

  const summary = document.createElement('summary');
  summary.textContent = 'Execution logs';
  details.appendChild(summary);

  const list = document.createElement('ul');
  logs.forEach((line) => {
    const item = document.createElement('li');
    item.textContent = line;
    list.appendChild(item);
  });
  details.appendChild(list);
  return details;
}

async function sendPrompt(message) {
  const payload = { message };
  const limit = parseInt(codexLimit.value, 10);
  if (!Number.isNaN(limit) && limit > 0) {
    payload.inputs = { limit };
  }

  statusEl.textContent = 'Contacting assistant…';
  try {
    const response = await fetch('/api/assistant/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }
    const data = await response.json();
    appendMessage('assistant', data.reply || 'Ready.', {
      suggestion: data.suggestion,
      toolCalls: data.tool_calls,
      logs: data.logs,
    });
    statusEl.textContent = 'Idle.';
  } catch (error) {
    console.error('Assistant request failed', error);
    appendMessage('assistant', 'Unable to reach the assistant.', {
      logs: [error.message],
    });
    statusEl.textContent = 'Error communicating with assistant';
  }
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;
  appendMessage('user', message);
  input.value = '';
  sendPrompt(message);
  input.focus();
});
