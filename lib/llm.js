import fetch from 'node-fetch';

export async function initLLM() {
  if (!process.env.OPENAI_API_KEY) {
    console.warn('No OPENAI_API_KEY configured. LLM calls will return a placeholder response.');
  }
  return true;
}

export async function callLLM(prompt) {
  if (!prompt || typeof prompt !== 'string') {
    throw new Error('callLLM requires a non-empty prompt string.');
  }

  const trimmedPrompt = prompt.trim();
  if (trimmedPrompt.length === 0) {
    throw new Error('callLLM requires a non-empty prompt string.');
  }

  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    return `Simulated response for: ${trimmedPrompt}`;
  }

  const projectId = process.env.PROJECT_ID;
  const organizationId = process.env.OPENAI_ORG_ID;

  const body = {
    model: 'gpt-4o',
    messages: [
      { role: 'system', content: 'You are a helpful, concise assistant.' },
      { role: 'user', content: trimmedPrompt },
    ],
    temperature: 0.7,
  };

  const headers = {
    Authorization: `Bearer ${apiKey}`,
    'Content-Type': 'application/json',
  };

  if (projectId) {
    headers['OpenAI-Project'] = projectId;
  }
  if (organizationId) {
    headers['OpenAI-Organization'] = organizationId;
  }

  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`OpenAI request failed with status ${response.status}: ${errorText}`);
  }

  const data = await response.json();
  return data.choices?.[0]?.message?.content?.trim() || 'No response';
}
