import { useState, useMemo } from 'react';
import { useChatHistory } from '../hooks/useApi';

interface ChatHistoryProps {
  sessionId: string;
}

const INITIAL_COUNT = 10;

export function ChatHistory({ sessionId }: ChatHistoryProps) {
  const { messages, loading, error } = useChatHistory(sessionId);
  const [showAll, setShowAll] = useState(false);

  // Filter out tool_call-only messages (no content, only tool_calls)
  const filtered = useMemo(
    () => messages.filter((msg) => msg.content && msg.content.trim() !== ''),
    [messages],
  );

  const visible = showAll ? filtered : filtered.slice(-INITIAL_COUNT);
  const hasMore = filtered.length > INITIAL_COUNT && !showAll;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin w-6 h-6 border-2 border-tg-button border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-4 text-tg-hint text-sm">
        Не удалось загрузить историю чата
      </div>
    );
  }

  if (filtered.length === 0) {
    return (
      <div className="text-center py-8 text-tg-hint text-sm">
        История чата пуста
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {hasMore && (
        <button
          onClick={() => setShowAll(true)}
          className="w-full text-center py-2 text-sm text-tg-button"
        >
          Показать все ({filtered.length})
        </button>
      )}
      {visible.map((msg, i) => (
        <div
          key={msg.id}
          className={`flex ${msg.type === 'human' ? 'justify-end' : 'justify-start'} animate-fadeInUp stagger-${Math.min(i + 1, 10)}`}
        >
          <div
            className={`max-w-[85%] rounded-2xl px-3.5 py-2 ${
              msg.type === 'human'
                ? 'bg-tg-button text-tg-button-text rounded-br-sm'
                : 'bg-tg-secondary-bg text-tg-text rounded-bl-sm'
            }`}
          >
            <div className="text-sm whitespace-pre-wrap break-words">
              {msg.content}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
