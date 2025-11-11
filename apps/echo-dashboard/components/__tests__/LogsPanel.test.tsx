import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LogsPanel from '../LogsPanel';
import type { LogChunkDescriptor } from '../../lib/types';
import { apiGet } from '../../lib/api';

vi.mock('../../lib/api');

const mockedApiGet = vi.mocked(apiGet);

const baseChunk: LogChunkDescriptor = {
  name: 'test.log',
  chunk: 'alpha\n',
  start: 0,
  end: 6,
  size: 6,
  hasMoreBackward: false,
  hasMoreForward: false,
  previousCursor: null,
  nextCursor: null,
};

describe('LogsPanel', () => {
  afterEach(() => {
    mockedApiGet.mockReset();
  });

  it('loads the latest chunk when a log file is selected', async () => {
    mockedApiGet.mockResolvedValueOnce(baseChunk);

    render(
      <LogsPanel files={['test.log']} error={null} selected="test.log" onSelect={() => {}} />
    );

    await waitFor(() => {
      expect(mockedApiGet).toHaveBeenCalledWith(
        expect.stringContaining('/logs/test.log/chunk')
      );
    });

    expect(mockedApiGet.mock.calls[0][0]).toContain('cursor=latest');
    expect(await screen.findByText(/alpha/)).toBeInTheDocument();
  });

  it('requests older chunks when the user loads historical data', async () => {
    const latestChunk: LogChunkDescriptor = {
      ...baseChunk,
      chunk: 'recent\n',
      start: 50,
      end: 100,
      size: 120,
      hasMoreBackward: true,
      previousCursor: 50,
    };
    const olderChunk: LogChunkDescriptor = {
      ...baseChunk,
      chunk: 'historical\n',
      start: 20,
      end: 50,
      size: 120,
      hasMoreBackward: false,
      hasMoreForward: true,
      previousCursor: 20,
      nextCursor: 50,
    };

    mockedApiGet
      .mockResolvedValueOnce(latestChunk)
      .mockResolvedValueOnce(olderChunk);

    const user = userEvent.setup();
    render(
      <LogsPanel files={['test.log']} error={null} selected="test.log" onSelect={() => {}} />
    );

    await screen.findByText(/recent/);
    const loadOlderButton = await screen.findByRole('button', { name: /load older/i });
    await waitFor(() => expect(loadOlderButton).not.toBeDisabled());

    await user.click(loadOlderButton);

    await waitFor(() => {
      expect(mockedApiGet).toHaveBeenLastCalledWith(
        expect.stringContaining('direction=backward')
      );
    });

    const logContent = await screen.findByText(/historical/, { selector: 'pre' });
    expect(logContent).toBeInTheDocument();
  });
});
