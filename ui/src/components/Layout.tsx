import { Outlet, NavLink } from 'react-router-dom';

export function Layout() {
    return (
        <div className="flex h-screen">
            {/* Sidebar */}
            <aside className="w-64 flex-shrink-0 bg-[hsl(var(--color-bg-secondary))] border-r border-[hsl(var(--color-border))]">
                <div className="p-6">
                    {/* Logo */}
                    <div className="flex items-center gap-3 mb-8">
                        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                        </div>
                        <div>
                            <h1 className="text-lg font-semibold text-[hsl(var(--color-text-primary))]">Windtunnel</h1>
                            <p className="text-xs text-[hsl(var(--color-text-secondary))]">Workflow Testing</p>
                        </div>
                    </div>

                    {/* Navigation */}
                    <nav className="space-y-1">
                        <NavItem to="/" icon={<RunsIcon />} label="Runs" />
                        <NavItem to="/settings" icon={<SettingsIcon />} label="Settings" />
                    </nav>
                </div>
            </aside>

            {/* Main content */}
            <main className="flex-1 overflow-auto bg-[hsl(var(--color-bg-primary))]">
                <div className="p-8">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}

interface NavItemProps {
    to: string;
    icon: React.ReactNode;
    label: string;
}

function NavItem({ to, icon, label }: NavItemProps) {
    return (
        <NavLink
            to={to}
            className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${isActive
                    ? 'bg-[hsl(var(--color-bg-elevated))] text-[hsl(var(--color-text-primary))]'
                    : 'text-[hsl(var(--color-text-secondary))] hover:bg-[hsl(var(--color-bg-elevated))] hover:text-[hsl(var(--color-text-primary))]'
                }`
            }
        >
            <span className="w-5 h-5">{icon}</span>
            {label}
        </NavLink>
    );
}

function RunsIcon() {
    return (
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
        </svg>
    );
}

function SettingsIcon() {
    return (
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
    );
}
