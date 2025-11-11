import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MetricsPanel from '../MetricsPanel';
import type { MetricsOverview } from '../../lib/types';
import { apiGet } from '../../lib/api';

vi.mock('../../lib/api');

const mockedApiGet = vi.mocked(apiGet);

const metricsResponse: MetricsOverview = {
  range: { from: '2024-01-01T00:00:00.000Z', to: '2024-01-02T00:00:00.000Z' },
  metrics: {
    codexMerges: { label: 'Codex merges', total: 2, series: [] },
    puzzleSolutions: { label: 'Puzzle solutions', total: 1, series: [] },
    logVolume: { label: 'Log entries', total: 10, series: [] },
    attestationStored: null,
  },
};

describe('MetricsPanel', () => {
  afterEach(() => {
    mockedApiGet.mockReset();
  });

  it('requests metrics for the default 24h range', async () => {
    mockedApiGet.mockResolvedValueOnce(metricsResponse);

    render(<MetricsPanel />);

    const firstCall = await waitFor(() => {
      expect(mockedApiGet).toHaveBeenCalled();
      return mockedApiGet.mock.calls[0][0];
    });

    const params = new URLSearchParams(firstCall.split('?')[1]);
    const from = params.get('from');
    const to = params.get('to');
    expect(from).toBeTruthy();
    expect(to).toBeTruthy();
    const duration = new Date(to as string).getTime() - new Date(from as string).getTime();
    const oneDayMs = 24 * 60 * 60 * 1000;
    expect(duration).toBeGreaterThan(oneDayMs - 1000);
    expect(duration).toBeLessThan(oneDayMs + 1000);
    const codexLabel = await screen.findByText((content, element) => {
      return element?.tagName === 'P' && element.textContent?.trim() === 'Codex merges';
    });
    expect(codexLabel).toBeInTheDocument();
  });

  it('re-fetches metrics when selecting a different range', async () => {
    mockedApiGet
      .mockResolvedValueOnce(metricsResponse)
      .mockResolvedValueOnce({
        ...metricsResponse,
        range: { from: '2023-12-26T00:00:00.000Z', to: '2024-01-02T00:00:00.000Z' },
      });

    const user = userEvent.setup();
    render(<MetricsPanel />);

    await waitFor(() => expect(mockedApiGet).toHaveBeenCalledTimes(1));

    const select = await screen.findByLabelText(/time range/i);
    await user.selectOptions(select, '7d');

    const secondCall = await waitFor(() => {
      expect(mockedApiGet).toHaveBeenCalledTimes(2);
      return mockedApiGet.mock.calls[1][0];
    });

    const params = new URLSearchParams(secondCall.split('?')[1]);
    const from = params.get('from');
    const to = params.get('to');
    expect(from).toBeTruthy();
    expect(to).toBeTruthy();
    const duration = new Date(to as string).getTime() - new Date(from as string).getTime();
    const sevenDaysMs = 7 * 24 * 60 * 60 * 1000;
    expect(duration).toBeGreaterThan(sevenDaysMs - 1000);
    expect(duration).toBeLessThan(sevenDaysMs + 1000);
  });
});
