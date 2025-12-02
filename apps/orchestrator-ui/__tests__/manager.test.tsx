import { act, render, screen } from '@testing-library/react'
import ManagerPage from '../app/mail/manager/page'

const mockMissions = [
  {
    id: 'M-001',
    title: 'Demo mission',
    status: 'running',
    owner: 'tester',
    run_mode: 'sequential',
    updated_at: '2025-01-01T00:00:00Z'
  }
]

const mockSignals = {
  signals: [
    { id: 'S-1', type: 'notice', severity: 'info', status: 'ok', created_at: '2025-01-01T00:00:00Z', message: 'demo' }
  ]
}

beforeEach(() => {
  global.fetch = jest.fn((url: string) => {
    if (url.includes('/api/missions')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockMissions) }) as unknown as Response
    }
    if (url.includes('/api/signals')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockSignals) }) as unknown as Response
    }
    return Promise.resolve({ ok: false, json: () => Promise.resolve({}) }) as unknown as Response
  })
})

afterEach(() => {
  jest.resetAllMocks()
})

const renderPage = (lang?: string, feature = 'true') => {
  process.env.NEXT_PUBLIC_FEATURE_MANAGER_UI = feature
  return render(<ManagerPage searchParams={lang ? { lang } : {}} />)
}

const renderPageAsync = async (lang?: string, feature = 'true') => {
  await act(async () => {
    renderPage(lang, feature)
  })
}

describe('ManagerPage', () => {
  it('renders placeholder when feature flag is off', () => {
    renderPage('en', 'false')
    expect(screen.getByTestId('manager-disabled-title')).toBeInTheDocument()
    expect(screen.getByText(/Manager UI is turned off/i)).toBeInTheDocument()
  })

  it('renders manager title and language toggle', async () => {
    await renderPageAsync('en')
    expect(await screen.findByTestId('manager-title')).toHaveTextContent(/Manager/i)
    const toggle = await screen.findByTestId('language-toggle')
    expect(toggle).toHaveTextContent(/Language/i)
    expect(toggle).toHaveAttribute('href', '/mail/manager?lang=ja')
  })

  it('shows missions, task groups, and artifacts', async () => {
    await renderPageAsync('en')
    expect((await screen.findAllByTestId('mission-row')).length).toBeGreaterThan(0)
    expect((await screen.findAllByTestId('taskgroup-card')).length).toBeGreaterThan(0)
    expect((await screen.findAllByTestId('artifact-card')).length).toBeGreaterThan(0)
  })

  it('supports Japanese labels', async () => {
    await renderPageAsync('ja')
    expect(await screen.findByTestId('manager-title')).toHaveTextContent('マネージャー')
    expect((await screen.findAllByTestId('taskgroup-card'))[0]).toHaveTextContent('種別')
  })
})
