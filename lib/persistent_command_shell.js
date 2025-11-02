import fs from 'fs/promises';

const workflows = new Map();
const sessionState = {
  lastCommand: null,
  workflowRuns: [],
};

export const persistentCommandShell = {
  getSessionState() {
    return {
      lastCommand: sessionState.lastCommand,
      workflows: Array.from(workflows.keys()),
      workflowRuns: sessionState.workflowRuns.slice(-5),
    };
  },

  async executeCommand(command, language = 'shell', options = {}) {
    sessionState.lastCommand = { command, language, options, timestamp: Date.now() };
    return {
      ...sessionState.lastCommand,
      output: `Executed ${language} command: ${command}`,
    };
  },

  async executeScript(scriptPath, language = 'shell') {
    try {
      const content = await fs.readFile(scriptPath, 'utf-8');
      sessionState.lastCommand = { command: scriptPath, language, timestamp: Date.now() };
      return {
        scriptPath,
        language,
        lines: content.split('\n').length,
        status: 'executed',
      };
    } catch (error) {
      return {
        scriptPath,
        language,
        status: 'error',
        message: error instanceof Error ? error.message : String(error),
      };
    }
  },

  async createPersistentWorkflow(workflowName, commands, options = {}) {
    if (!Array.isArray(commands) || commands.length === 0) {
      throw new Error('Workflow requires at least one command.');
    }
    const workflow = { commands, options, createdAt: Date.now() };
    workflows.set(workflowName, workflow);
    return { workflowName, ...workflow };
  },

  async executeWorkflow(workflowName) {
    const workflow = workflows.get(workflowName);
    if (!workflow) {
      throw new Error(`Workflow ${workflowName} not found`);
    }
    const run = {
      workflowName,
      executedAt: Date.now(),
      commandCount: workflow.commands.length,
    };
    sessionState.workflowRuns.push(run);
    return { ...run, commands: workflow.commands };
  },
};
