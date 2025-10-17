import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';

import { agentLoop } from './lib/agent.js';
import { initializeMemory } from './lib/memory.js';
import { initLLM } from './lib/llm.js';

dotenv.config();

const app = express();
app.use(express.json());
app.use(cors());

const PORT = process.env.PORT || 3000;

app.get('/', (_req, res) => {
  res.send('🧠 Grimoire-1 Universal Agent running...');
});

app.post('/tick', async (req, res) => {
  try {
    const { task } = req.body || {};
    const result = await agentLoop(task);
    res.status(200).json(result);
  } catch (error) {
    console.error('Agent tick failed:', error);
    res.status(500).json({ error: 'Agent tick failed' });
  }
});

app.listen(PORT, async () => {
  console.log(`Server live at http://localhost:${PORT}`);
  try {
    await initializeMemory();
    await initLLM();
    console.log('Memory and LLM initialized');
  } catch (err) {
    console.error('Startup error:', err);
  }
});
