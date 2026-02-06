import { User, goalLabels } from '../hooks/useApi';

interface UserCardProps {
  user: User;
  onClick: () => void;
  index?: number;
}

export function UserCard({ user, onClick, index = 0 }: UserCardProps) {
  const displayName = user.first_name || user.username || `User ${user.chat_id}`;
  const goalLabel = user.goal ? goalLabels[user.goal] || user.goal : null;

  const handleClick = () => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
    onClick();
  };

  return (
    <div
      onClick={handleClick}
      className={`flex items-center gap-3 px-4 py-3 cursor-pointer active:scale-[0.98] transition-transform duration-100 animate-fadeInUp stagger-${Math.min(index + 1, 10)}`}
    >
      {/* Avatar */}
      <div className="w-10 h-10 rounded-full bg-tg-button/15 flex-shrink-0 flex items-center justify-center text-tg-button font-semibold text-sm">
        {displayName.charAt(0).toUpperCase()}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-tg-text truncate">{displayName}</span>
          {user.is_buyer && (
            <span className="px-1.5 py-0.5 text-[10px] rounded-full bg-tg-button/15 text-tg-button font-medium flex-shrink-0">
              Покупатель
            </span>
          )}
        </div>
        <div className="text-sm text-tg-hint truncate">
          {[
            user.username ? `@${user.username}` : null,
            goalLabel,
            user.funnel_stage != null ? `Этап ${user.funnel_stage}` : null,
          ].filter(Boolean).join(' · ')}
        </div>
      </div>

      {/* Chevron */}
      <svg className="w-4 h-4 text-tg-hint/50 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="9 18 15 12 9 6" />
      </svg>
    </div>
  );
}
