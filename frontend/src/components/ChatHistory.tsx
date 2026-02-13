import { useState, useMemo } from 'react';
import { useChatHistory, useUserEvents, eventButtonLabels, UserEvent } from '../hooks/useApi';
import { Button } from './ui/button';
import { MousePointerClick, Mail, Bot } from 'lucide-react';

interface ChatHistoryProps {
  sessionId: string;
}

type TimelineItem =
  | { kind: 'message'; id: number; type: string; content: string; timestamp?: string }
  | { kind: 'event'; event: UserEvent };

const INITIAL_COUNT = 20;

function formatTime(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function EventCard({ event }: { event: UserEvent }) {
  const info = eventButtonLabels[event.event_data];
  const label = info?.label || event.event_data;
  const botResponse = info?.botResponse || '';
  const isFunnel = event.event_type === 'funnel_message';
  const Icon = isFunnel ? Mail : MousePointerClick;

  return (
    <div className="flex flex-col gap-1 my-1">
      {/* User pressed button */}
      <div className="flex justify-end">
        <div className="flex items-center gap-2 max-w-[85%] rounded-2xl px-3.5 py-2 bg-accent/50 border border-accent rounded-br-sm">
          <Icon className="w-3.5 h-3.5 text-primary shrink-0" />
          <div className="text-sm">
            <span className="text-foreground font-medium">
              {isFunnel ? label : `Нажал: "${label}"`}
            </span>
          </div>
          <span className="text-[10px] text-muted-foreground shrink-0 ml-1">
            {formatTime(event.created_at)}
          </span>
        </div>
      </div>
      {/* Bot response */}
      {botResponse && (
        <div className="flex justify-start">
          <div className="flex items-center gap-2 max-w-[85%] rounded-2xl px-3.5 py-2 bg-muted/50 border border-border rounded-bl-sm">
            <Bot className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
            <span className="text-sm text-muted-foreground">{botResponse}</span>
          </div>
        </div>
      )}
    </div>
  );
}

export function ChatHistory({ sessionId }: ChatHistoryProps) {
  const { messages, loading: chatLoading, error: chatError } = useChatHistory(sessionId);
  const { events, loading: eventsLoading, error: eventsError } = useUserEvents(sessionId);
  const [showAll, setShowAll] = useState(false);

  const loading = chatLoading || eventsLoading;
  const error = chatError || eventsError;

  const timeline = useMemo(() => {
    const items: TimelineItem[] = [];

    // Add chat messages
    messages
      .filter((msg) => msg.content && msg.content.trim() !== '')
      .forEach((msg) => {
        items.push({ kind: 'message', id: msg.id, type: msg.type, content: msg.content });
      });

    // Add events
    events.forEach((evt) => {
      items.push({ kind: 'event', event: evt });
    });

    // Messages don't have timestamps in the current schema, so events go after messages.
    // We keep messages in their original DB order, and events sorted by created_at at the end.
    // If messages had timestamps we could interleave them.
    return items;
  }, [messages, events]);

  const visible = showAll ? timeline : timeline.slice(-INITIAL_COUNT);
  const hasMore = timeline.length > INITIAL_COUNT && !showAll;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin w-6 h-6 border-2 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error) {
    return <div className="text-center py-4 text-muted-foreground text-sm">Не удалось загрузить данные</div>;
  }

  if (timeline.length === 0) {
    return <div className="text-center py-8 text-muted-foreground text-sm">История пуста</div>;
  }

  return (
    <div className="space-y-2">
      {hasMore && (
        <Button variant="ghost" size="sm" className="w-full text-primary" onClick={() => setShowAll(true)}>
          Показать все ({timeline.length})
        </Button>
      )}
      {visible.map((item) => {
        if (item.kind === 'event') {
          return <EventCard key={`evt-${item.event.id}`} event={item.event} />;
        }
        return (
          <div key={`msg-${item.id}`} className={`flex ${item.type === 'human' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-2xl px-3.5 py-2 ${
              item.type === 'human'
                ? 'bg-primary text-primary-foreground rounded-br-sm'
                : 'bg-card border border-border text-card-foreground rounded-bl-sm'
            }`}>
              <div className="text-sm whitespace-pre-wrap break-words">{item.content}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
