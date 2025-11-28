import { render, screen } from '@testing-library/react'
import ManagerPage from '../app/mail/manager/page'

const renderPage = (lang?: string, feature = 'true') => {
  process.env.NEXT_PUBLIC_FEATURE_MANAGER_UI = feature
  return render(<ManagerPage searchParams={lang ? { lang } : {}} />)
}

describe('ManagerPage', () => {
  it('renders placeholder when feature flag is off', () => {
    renderPage('en', 'false')
    expect(screen.getByTestId('manager-disabled-title')).toBeInTheDocument()
    expect(screen.getByText(/Manager UI is turned off/i)).toBeInTheDocument()
  })

  it('renders manager title and language toggle', () => {
    renderPage('en')
    expect(screen.getByTestId('manager-title')).toHaveTextContent(/Manager/i)
    const toggle = screen.getByTestId('language-toggle')
    expect(toggle).toHaveTextContent(/Language/i)
    expect(toggle).toHaveAttribute('href', '/mail/manager?lang=ja')
  })

  it('shows missions, task groups, and artifacts', () => {
    renderPage('en')
    expect(screen.getAllByTestId('mission-row').length).toBeGreaterThan(0)
    expect(screen.getAllByTestId('taskgroup-card').length).toBeGreaterThan(0)
    expect(screen.getAllByTestId('artifact-card').length).toBeGreaterThan(0)
  })

  it('supports Japanese labels', () => {
    renderPage('ja')
    expect(screen.getByTestId('manager-title')).toHaveTextContent('マネージャー')
    expect(screen.getAllByTestId('taskgroup-card')[0]).toHaveTextContent('種別')
  })
})
