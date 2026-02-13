import { useState, useMemo } from 'react';
import { useChatHistory } from '../hooks/useApi';
import { Button } from './ui/button';

interface ChatHistoryProps {
  sessionId: string;
}

const INITIAL_COUNT = 10;

export function ChatHistory({ sessionId }: ChatHistoryProps) {
  const { messages, loading, error } = useChatHistory(sessionId);
  const [showAll, setShowAll] = useState(false);

  const filtered = useMemo(
    () => messages.filter((msg) => msg.content && msg.content.trim() !== ''),
    [messages],
  );

  const visible = showAll ? filtered : filtered.slice(-INITIAL_COUNT);
  const hasMore = filtered.length > INITIAL_COUNT && !showAll;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin w-6 h-6 border-2 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error) {
    return <div className="text-center py-4 text-muted-foreground text-sm">Не удалось загрузить историю чата</div>;
  }

  if (filtered.length === 0) {
    return <div className="text-center py-8 text-muted-foreground text-sm">История чата пуста</div>;
  }

  return (
    <div className="space-y-2">
      {hasMore && (
        <Button variant="ghost" size="sm" className="w-full text-primary" onClick={() => setShowAll(true)}>
          Показать все ({filtered.length})
        </Button>
      )}
      {visible.map((msg) => (
        <div key={msg.id} className={`flex ${msg.type === 'human' ? 'justify-end' : 'justify-start'}`}>
          <div className={`max-w-[85%] rounded-2xl px-3.5 py-2 ${
            msg.type === 'human'
              ? 'bg-primary text-primary-foreground rounded-br-sm'
              : 'bg-card border border-border text-card-foreground rounded-bl-sm'
          }`}>
            <div className="text-sm whitespace-pre-wrap break-words">{msg.content}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
