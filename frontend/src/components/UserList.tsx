import { useState, useMemo } from 'react';
import { useUsers, useDebounce, User, UserFilters, goalLabels } from '../hooks/useApi';
import { UserCard } from './UserCard';

interface UserListProps {
  onSelectUser: (user: User) => void;
}

type StatusFilter = 'all' | 'buyer' | 'lead';

const statusOptions: { value: StatusFilter; label: string }[] = [
  { value: 'all', label: 'Все' },
  { value: 'buyer', label: 'Покупатели' },
  { value: 'lead', label: 'Лиды' },
];

const goalOptions = [
  { value: '', label: 'Все цели' },
  ...Object.entries(goalLabels).map(([value, label]) => ({ value, label })),
];

const funnelOptions = [
  { value: '', label: 'Все этапы' },
  ...Array.from({ length: 7 }, (_, i) => ({ value: String(i), label: `Этап ${i}` })),
];

function SkeletonCard() {
  return (
    <div className="flex items-center gap-3 px-4 py-3 animate-pulse">
      <div className="w-10 h-10 rounded-full bg-tg-secondary-bg" />
      <div className="flex-1 space-y-2">
        <div className="h-4 bg-tg-secondary-bg rounded w-1/3" />
        <div className="h-3 bg-tg-secondary-bg rounded w-2/3" />
      </div>
    </div>
  );
}

export function UserList({ onSelectUser }: UserListProps) {
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState<StatusFilter>('all');
  const [goal, setGoal] = useState('');
  const [funnelStage, setFunnelStage] = useState('');
  const [filtersOpen, setFiltersOpen] = useState(false);

  const debouncedSearch = useDebounce(search, 300);

  const filters: UserFilters = useMemo(() => ({
    search: debouncedSearch || undefined,
    status: status !== 'all' ? status : undefined,
    goal: goal || undefined,
    funnel_stage: funnelStage || undefined,
  }), [debouncedSearch, status, goal, funnelStage]);

  const { users, loading, error } = useUsers(filters);

  const hasActiveFilters = goal !== '' || funnelStage !== '';

  const handleStatusChange = (s: StatusFilter) => {
    window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
    setStatus(s);
  };

  const handleClearSearch = () => {
    setSearch('');
  };

  return (
    <div className="pb-20">
      {/* Sticky search + filters header */}
      <div className="sticky top-0 z-10 bg-tg-bg/80 backdrop-blur-lg">
        {/* Search bar */}
        <div className="px-4 pt-3 pb-2">
          <div className="relative">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tg-hint" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Поиск по имени или username..."
              className="w-full pl-10 pr-8 py-2.5 bg-tg-secondary-bg rounded-xl text-[16px] text-tg-text placeholder:text-tg-hint border-none outline-none"
            />
            {search && (
              <button
                onClick={handleClearSearch}
                className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 rounded-full bg-tg-hint/30 flex items-center justify-center"
              >
                <svg className="w-3 h-3 text-tg-hint" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            )}
          </div>
        </div>

        {/* Status segment control */}
        <div className="px-4 pb-2 flex gap-1">
          {statusOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => handleStatusChange(opt.value)}
              className={`flex-1 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                status === opt.value
                  ? 'bg-tg-button text-tg-button-text'
                  : 'text-tg-hint'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* Filter toggle + collapsible panel */}
        <div className="px-4 pb-2">
          <button
            onClick={() => {
              window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
              setFiltersOpen(!filtersOpen);
            }}
            className="flex items-center gap-1.5 text-sm text-tg-button"
          >
            <svg className={`w-3.5 h-3.5 transition-transform duration-200 ${filtersOpen ? 'rotate-180' : ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="6 9 12 15 18 9" />
            </svg>
            Фильтры
            {hasActiveFilters && (
              <span className="w-1.5 h-1.5 rounded-full bg-tg-button" />
            )}
          </button>

          <div
            className="overflow-hidden transition-all duration-200 ease-out"
            style={{ maxHeight: filtersOpen ? '120px' : '0px', opacity: filtersOpen ? 1 : 0 }}
          >
            <div className="flex gap-2 pt-2">
              <select
                value={goal}
                onChange={(e) => {
                  window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
                  setGoal(e.target.value);
                }}
                className="flex-1 py-2 px-3 bg-tg-secondary-bg rounded-lg text-sm text-tg-text border-none outline-none appearance-none"
              >
                {goalOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
              <select
                value={funnelStage}
                onChange={(e) => {
                  window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
                  setFunnelStage(e.target.value);
                }}
                className="flex-1 py-2 px-3 bg-tg-secondary-bg rounded-lg text-sm text-tg-text border-none outline-none appearance-none"
              >
                {funnelOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Divider */}
        <div className="h-px bg-tg-secondary-bg" />
      </div>

      {/* Result count */}
      {!loading && !error && (
        <div className="px-4 pt-3 pb-1">
          <span className="text-xs text-tg-hint">
            {users.length === 0 ? 'Ничего не найдено' : `${users.length} пользовател${users.length === 1 ? 'ь' : users.length < 5 ? 'я' : 'ей'}`}
          </span>
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="pt-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="p-4 text-center">
          <div className="text-tg-destructive mb-2 text-sm">Ошибка загрузки</div>
          <div className="text-tg-hint text-xs">{error}</div>
        </div>
      )}

      {/* User list */}
      {!loading && !error && (
        <div className="divide-y divide-tg-secondary-bg">
          {users.map((user, i) => (
            <UserCard
              key={user.chat_id}
              user={user}
              index={i}
              onClick={() => onSelectUser(user)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
