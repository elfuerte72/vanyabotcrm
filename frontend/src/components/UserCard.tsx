import { User, goalLabels } from '../hooks/useApi';
import { Card } from './ui/card';
import { Avatar, AvatarFallback } from './ui/avatar';
import { Badge } from './ui/badge';
import { ChevronRight } from 'lucide-react';

interface UserCardProps {
  user: User;
  onClick: () => void;
}

export function UserCard({ user, onClick }: UserCardProps) {
  const displayName = user.first_name || user.username || `User ${user.chat_id}`;
  const goalLabel = user.goal ? goalLabels[user.goal] || user.goal : null;

  const handleClick = () => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
    onClick();
  };

  return (
    <Card
      onClick={handleClick}
      className="flex items-center gap-3 p-3 cursor-pointer active:bg-secondary/50"
    >
      <Avatar className="w-10 h-10">
        <AvatarFallback className="text-sm">
          {displayName.charAt(0).toUpperCase()}
        </AvatarFallback>
      </Avatar>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-foreground truncate">{displayName}</span>
          {user.is_buyer && (
            <Badge variant="buyer" className="text-[10px] px-1.5 py-0">
              Покупатель
            </Badge>
          )}
        </div>
        <div className="text-sm text-muted-foreground truncate mt-0.5">
          {[
            user.username ? `@${user.username}` : null,
            goalLabel,
            user.funnel_stage != null ? `Этап ${user.funnel_stage}` : null,
          ].filter(Boolean).join(' · ')}
        </div>
      </div>

      <ChevronRight className="w-4 h-4 text-muted-foreground/50 flex-shrink-0" />
    </Card>
  );
}
