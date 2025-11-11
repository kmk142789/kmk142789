import { before, after, test } from 'node:test';
import assert from 'node:assert/strict';
import { join } from 'node:path';
import { promises as fs } from 'node:fs';
import request from 'supertest';
import { app, LOG_DIRECTORY, PUZZLE_DIRECTORY } from '../server.mjs';

const logPath = join(LOG_DIRECTORY, 'test-log-viewer.log');
const puzzlePath = join(PUZZLE_DIRECTORY, 'test-puzzle-solution.md');
const futureTimestamp = new Date('2030-01-01T00:05:00Z');

before(async () => {
  await fs.mkdir(LOG_DIRECTORY, { recursive: true });
  await fs.mkdir(PUZZLE_DIRECTORY, { recursive: true });
  const logPayload = new Array(200).fill('echo-cycle-entry\n').join('');
  await fs.writeFile(logPath, logPayload);
  await fs.writeFile(puzzlePath, 'Puzzle transcript');
  await fs.utimes(logPath, futureTimestamp, futureTimestamp);
  await fs.utimes(puzzlePath, futureTimestamp, futureTimestamp);
});

after(async () => {
  await fs.rm(logPath, { force: true });
  await fs.rm(puzzlePath, { force: true });
});

function encodeQuery(params) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      search.set(key, value);
    }
  }
  return search.toString();
}

test('log chunk endpoint returns paginated data', async () => {
  const initial = await request(app)
    .get(`/logs/test-log-viewer.log/chunk?${encodeQuery({ limit: 4 })}`)
    .expect(200);

  assert.equal(initial.body.name, 'test-log-viewer.log');
  assert.equal(typeof initial.body.chunk, 'string');
  assert.ok(initial.body.previousCursor !== null, 'expected a previous cursor value');

  const older = await request(app)
    .get(
      `/logs/test-log-viewer.log/chunk?${encodeQuery({
        cursor: initial.body.previousCursor,
        direction: 'backward',
        limit: 8,
      })}`
    )
    .expect(200);

  assert.ok(older.body.chunk.length > 0, 'older chunk should include data');
  assert.equal(older.body.end, initial.body.previousCursor);
});

test('metrics endpoint respects explicit time ranges', async () => {
  const metricsResponse = await request(app)
    .get(
      `/metrics/overview?${encodeQuery({
        from: '2029-12-31T23:00:00.000Z',
        to: '2030-01-01T01:00:00.000Z',
      })}`
    )
    .expect(200);

  const { metrics } = metricsResponse.body;
  assert.equal(metrics.logVolume.total, 200);
  assert.equal(metrics.puzzleSolutions.total >= 1, true);
  assert.equal(metrics.codexMerges.total >= 0, true);
});
