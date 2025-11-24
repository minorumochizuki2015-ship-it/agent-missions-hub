import { render, screen, act } from '@testing-library/react'
import Dashboard from '../app/page'

global.fetch = jest.fn()

jest.mock('recharts', () => {
  const Actual = jest.requireActual('recharts')
  return {
    ...Actual,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div style={{ width: 600, height: 400 }}>{children}</div>
    )
  }
})

if (!('ResizeObserver' in globalThis)) {
  class MockResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  ;(globalThis as any).ResizeObserver = MockResizeObserver
}

describe('Dashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(global.fetch as jest.Mock).mockReset()
  })

  const okResponse = (data: any = {}) =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve(data)
    })

  it('renders loading state initially', () => {
    render(<Dashboard />)
    expect(screen.getByText('Loading SafeOps Dashboard...')).toBeInTheDocument()
  })

  it('renders dashboard header', async () => {
    // Mock successful API responses
    ;(global.fetch as jest.Mock).mockImplementation((url: string) => {
      if (typeof url !== 'string') {
        return okResponse()
      }
      if (url.includes('/api/safeops/kpi')) {
        return okResponse({
          dangerous_without_approval: 0,
          total_approvals: 5,
          pending_approvals: 2,
          recent_commands: 10,
          ci_success_rate: 95,
          last_updated: new Date().toISOString()
        })
      }
      if (url.includes('/api/approvals')) {
        return okResponse({
          content: '|appr1|task1|pending|user1|auditor1|2024-01-01|'
        })
      }
      return okResponse()
    })

    await act(async () => {
      render(<Dashboard />)
    })

    // Wait for data to load
    await screen.findByText('Glass-mode Dashboard')
    expect(screen.getByText('SafeOps Orchestrator')).toBeInTheDocument()
  })

  it('displays KPI cards when data is loaded', async () => {
    ;(global.fetch as jest.Mock).mockImplementation((url: string) => {
      if (typeof url !== 'string') {
        return okResponse()
      }
      if (url.includes('/api/safeops/kpi')) {
        return okResponse({
          dangerous_without_approval: 0,
          total_approvals: 5,
          pending_approvals: 2,
          recent_commands: 10,
          ci_success_rate: 95,
          last_updated: new Date().toISOString()
        })
      }
      if (url.includes('/api/approvals')) {
        return okResponse({
          content: '|appr1|task1|pending|user1|auditor1|2024-01-01|'
        })
      }
      return okResponse()
    })

    await act(async () => {
      render(<Dashboard />)
    })

    await screen.findByText('Approvals / Audit / Dangerous')
    expect(screen.getByText('Approvals Ledger')).toBeInTheDocument()
    expect(screen.getByText('Approvals Pending')).toBeInTheDocument()
    expect(screen.getByText('CI Success %')).toBeInTheDocument()
  })

  it('renders Codex Sessions from status API', async () => {
    ;(global.fetch as jest.Mock).mockImplementation((url: string) => {
      if (typeof url !== 'string') {
        return okResponse()
      }
      if (url.includes('/api/orchestrator/status')) {
        return okResponse({ cli_sessions: [{ session_id: 'sid-1', phase: 'plan', role: 'planner', started_at: new Date().toISOString(), exited_at: new Date().toISOString() }] })
      }
      return okResponse()
    })
    await act(async () => {
      render(<Dashboard />)
    })
    await screen.findByText('Codex Sessions')
  })

  it('handles API errors gracefully', async () => {
    (global.fetch as jest.Mock).mockImplementation(() => {
      return Promise.resolve({ ok: false })
    })

    await act(async () => {
      render(<Dashboard />)
    })

    // Should still render the dashboard even with API errors
    await screen.findByText('SafeOps Orchestrator Dashboard')
    await screen.findByText('Refresh')
  })
})
