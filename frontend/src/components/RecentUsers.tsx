import { useState } from 'react';
import { useRecentUsers, User } from '../hooks/useApi';
import { UserCard } from './UserCard';
import { Tabs, TabsList, TabsTrigger } from './ui/tabs';
import { Card } from './ui/card';

interface RecentUsersProps {
  onSelectUser: (user: User) => void;
}

const periodOptions = [
  { value: '1', label: 'Сегодня' },
  { value: '3', label: '3 дня' },
  { value: '7', label: 'Неделя' },
  { value: '30', label: 'Месяц' },
];

function formatRelativeDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return 'сегодня';
  if (diffDays === 1) return 'вчера';
  if (diffDays < 5) return `${diffDays} дня назад`;
  if (diffDays < 21) return `${diffDays} дней назад`;
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
}

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

export function RecentUsers({ onSelectUser }: RecentUsersProps) {
  const [days, setDays] = useState(7);
  const { users, loading, error } = useRecentUsers(days);

  return (
    <div className="pb-20">
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur-sm">
        <div className="px-4 pt-3 pb-2">
          <h2 className="text-lg font-semibold text-foreground">Новые клиенты</h2>
        </div>

        <div className="px-4 pb-2">
          <Tabs value={String(days)} onValueChange={(v) => {
            window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
            setDays(Number(v));
          }}>
            <TabsList>
              {periodOptions.map((opt) => (
                <TabsTrigger key={opt.value} value={opt.value}>{opt.label}</TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        </div>

        <div className="h-px bg-border" />
      </div>

      {!loading && !error && (
        <div className="px-4 pt-3 pb-1">
          <span className="text-xs text-muted-foreground">
            {users.length === 0
              ? 'Нет новых клиентов за выбранный период'
              : `${users.length} новых пользовател${users.length === 1 ? 'ь' : users.length < 5 ? 'я' : 'ей'}`}
          </span>
        </div>
      )}

      {loading && (
        <div className="px-4 pt-3 space-y-2">
          {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      )}

      {error && (
        <div className="p-4 text-center">
          <div className="text-destructive mb-2 text-sm">Ошибка загрузки</div>
          <div className="text-muted-foreground text-xs">{error}</div>
        </div>
      )}

      {!loading && !error && (
        <div className="px-4 pt-2 space-y-2">
          {users.map((user) => (
            <div key={user.chat_id} className="relative">
              {user.created_at && (
                <span className="absolute top-2 right-2 text-[10px] text-muted-foreground z-10">
                  {formatRelativeDate(user.created_at)}
                </span>
              )}
              <UserCard user={user} onClick={() => onSelectUser(user)} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
