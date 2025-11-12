import { before, after, test } from 'node:test';
import assert from 'node:assert/strict';
import { promises as fs } from 'node:fs';
import request from 'supertest';
import { app, WHISPERVAULT_POLICY_PATH } from '../server.mjs';

let originalPolicyContents = '';

before(async () => {
  originalPolicyContents = await fs.readFile(WHISPERVAULT_POLICY_PATH, 'utf8');
});

after(async () => {
  if (originalPolicyContents) {
    await fs.writeFile(WHISPERVAULT_POLICY_PATH, originalPolicyContents);
  }
});

test('whispervault policy endpoint exposes thresholds', async () => {
  const response = await request(app).get('/whispervault/policy').expect(200);
  const { policy } = response.body;
  assert.equal(policy.id, 'whispervault-spending');
  assert.equal(policy.selfApproveMax, 500);
  assert.equal(policy.dualApproveMin, 500);
  assert.equal(policy.governanceMin, 10000);
  assert.equal(policy.cashWithdrawalCap, 200);
});

test('whispervault policy update persists changes to yaml', async () => {
  const nextPolicy = {
    id: 'whispervault-spending',
    selfApproveMax: 750,
    dualApproveMin: 1250,
    governanceMin: 15000,
    cashWithdrawalCap: 350,
  };

  const updateResponse = await request(app).put('/whispervault/policy').send(nextPolicy).expect(200);
  assert.deepEqual(updateResponse.body.policy, nextPolicy);

  const confirmResponse = await request(app).get('/whispervault/policy').expect(200);
  assert.deepEqual(confirmResponse.body.policy, nextPolicy);

  const fileContents = await fs.readFile(WHISPERVAULT_POLICY_PATH, 'utf8');
  assert.match(fileContents, /self_approve_max:\s*750/);
  assert.match(fileContents, /dual_approve_min:\s*1250/);
  assert.match(fileContents, /governance_min:\s*15000/);
  assert.match(fileContents, /cash_withdrawal_cap:\s*350/);
});
