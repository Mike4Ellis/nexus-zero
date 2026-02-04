import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BriefCard } from '../BriefCard';

// Mock fetch
global.fetch = vi.fn();

describe('BriefCard', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('renders loading state initially', () => {
    (fetch as any).mockImplementation(() => new Promise(() => {}));
    
    render(<BriefCard />);
    
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders brief data after fetching', async () => {
    const mockBrief = {
      id: 1,
      title: 'Test Brief',
      date: '2026-02-04',
      totalContents: 42,
      platforms: { x: 15, reddit: 12, rss: 15 },
      heatTopCount: 10,
      potentialCount: 5,
    };

    (fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockBrief,
    });

    render(<BriefCard />);

    await waitFor(() => {
      expect(screen.getByText('Test Brief')).toBeInTheDocument();
    });

    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('收录内容')).toBeInTheDocument();
  });

  it('renders fallback data when API fails', async () => {
    (fetch as any).mockRejectedValueOnce(new Error('API Error'));

    render(<BriefCard />);

    await waitFor(() => {
      expect(screen.getByText(/Nexus Zero 每日简报/)).toBeInTheDocument();
    });
  });

  it('has accessible button with aria-label', async () => {
    (fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        id: 1,
        title: 'Test',
        date: '2026-02-04',
        totalContents: 42,
        platforms: {},
        heatTopCount: 10,
        potentialCount: 5,
      }),
    });

    render(<BriefCard />);

    await waitFor(() => {
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label', '查看简报详情');
    });
  });
});
