import { callLLM } from './llm.js';
import { enqueueTask, readNextTask, storeResult } from './memory.js';

export async function agentLoop(manualTask) {
  if (manualTask && typeof manualTask === 'string' && manualTask.trim().length > 0) {
    await enqueueTask(manualTask.trim());
  }

  const task = await readNextTask();
  if (!task) {
    return { status: 'idle', message: 'No tasks in queue.' };
  }

  const llmResponse = await callLLM(task);
  await storeResult(task, llmResponse);

  return { status: 'executed', task, response: llmResponse };
}
