import { useState, useMemo } from 'react';
import { useUsers, useDebounce, User, UserFilters, goalLabels } from '../hooks/useApi';
import { UserCard } from './UserCard';
import { Tabs, TabsList, TabsTrigger } from './ui/tabs';
import { Card } from './ui/card';
import { Search, X, SlidersHorizontal } from 'lucide-react';

interface UserListProps {
  onSelectUser: (user: User) => void;
}

type StatusFilter = 'all' | 'buyer';

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
    <Card className="flex items-center gap-3 p-3 animate-pulse">
      <div className="w-10 h-10 rounded-full bg-secondary" />
      <div className="flex-1 space-y-2">
        <div className="h-4 bg-secondary rounded w-1/3" />
        <div className="h-3 bg-secondary rounded w-2/3" />
      </div>
    </Card>
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

  return (
    <div className="pb-20">
      {/* Sticky header */}
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur-sm">
        {/* Search */}
        <div className="px-4 pt-3 pb-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Поиск по имени или username..."
              className="w-full pl-10 pr-8 py-2.5 bg-secondary rounded-xl text-[16px] text-foreground placeholder:text-muted-foreground border border-border outline-none focus:border-primary/50"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 rounded-full bg-muted-foreground/20 flex items-center justify-center"
              >
                <X className="w-3 h-3 text-muted-foreground" />
              </button>
            )}
          </div>
        </div>

        {/* Status tabs */}
        <div className="px-4 pb-2">
          <Tabs value={status} onValueChange={(v) => {
            window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
            setStatus(v as StatusFilter);
          }}>
            <TabsList>
              <TabsTrigger value="all">Все</TabsTrigger>
              <TabsTrigger value="buyer">Покупатели</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        {/* Filters */}
        <div className="px-4 pb-2">
          <button
            onClick={() => {
              window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
              setFiltersOpen(!filtersOpen);
            }}
            className="flex items-center gap-1.5 text-sm text-primary"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            Фильтры
            {hasActiveFilters && <span className="w-1.5 h-1.5 rounded-full bg-primary" />}
          </button>

          {filtersOpen && (
            <div className="flex gap-2 pt-2">
              <select
                value={goal}
                onChange={(e) => {
                  window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
                  setGoal(e.target.value);
                }}
                className="flex-1 py-2 px-3 bg-secondary rounded-lg text-sm text-foreground border border-border outline-none appearance-none"
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
                className="flex-1 py-2 px-3 bg-secondary rounded-lg text-sm text-foreground border border-border outline-none appearance-none"
              >
                {funnelOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div className="h-px bg-border" />
      </div>

      {/* Count */}
      {!loading && !error && (
        <div className="px-4 pt-3 pb-1">
          <span className="text-xs text-muted-foreground">
            {users.length === 0 ? 'Ничего не найдено' : `${users.length} пользовател${users.length === 1 ? 'ь' : users.length < 5 ? 'я' : 'ей'}`}
          </span>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="px-4 pt-3 space-y-2">
          {Array.from({ length: 8 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="p-4 text-center">
          <div className="text-destructive mb-2 text-sm">Ошибка загрузки</div>
          <div className="text-muted-foreground text-xs">{error}</div>
        </div>
      )}

      {/* List */}
      {!loading && !error && (
        <div className="px-4 pt-2 space-y-2">
          {users.map((user) => (
            <UserCard key={user.chat_id} user={user} onClick={() => onSelectUser(user)} />
          ))}
        </div>
      )}
    </div>
  );
}
