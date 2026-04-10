import { useState, useMemo } from 'react';
import { useChatHistory, useUserEvents, eventButtonLabels, funnelStageLabels } from '../hooks/useApi';
import type { ChatMessage, UserEvent } from '../../shared/types';
import { Button } from './ui/button';
import { MousePointerClick, Bot, ClipboardList, Megaphone } from 'lucide-react';

interface ChatHistoryProps {
  sessionId: string;
}

type TimelineItem =
  | { kind: 'message'; ts: string | null; msg: ChatMessage }
  | { kind: 'funnel'; ts: string; event: UserEvent }
  | { kind: 'button'; ts: string; event: UserEvent };

const INITIAL_COUNT = 50;

const dataLabels: Record<string, string> = {
  sex: 'Пол', weight: 'Вес', height: 'Рост', age: 'Возраст',
  activity_level: 'Активность', goal: 'Цель', allergies: 'Аллергии',
  excluded_foods: 'Исключения',
};

const valueLabels: Record<string, string> = {
  male: 'мужской', female: 'женский',
  weight_loss: 'похудение', weight_gain: 'набор массы',
  maintenance: 'поддержание', muscle_gain: 'набор мышц',
  sedentary: 'сидячий', light: 'лёгкая', moderate: 'умеренная',
  active: 'высокая', very_active: 'очень высокая',
  none: 'нет',
};

function formatJsonContent(content: string): { formatted: string; isJson: boolean } {
  const jsonMatch = content.match(/```json\s*([\s\S]*?)```/);
  if (!jsonMatch) return { formatted: content, isJson: false };

  try {
    const data = JSON.parse(jsonMatch[1]);
    const lines: string[] = [];
    for (const [key, value] of Object.entries(data)) {
      if (key === 'is_finished') continue;
      const label = dataLabels[key] || key;
      const val = valueLabels[String(value)] || String(value);
      lines.push(`${label}: ${val}`);
    }
    return { formatted: lines.join('\n'), isJson: true };
  } catch {
    return { formatted: content, isJson: false };
  }
}

/** Convert Telegram HTML to safe display HTML */
function sanitizeHtml(html: string): string {
  return html
    .replace(/<br\s*\/?>/gi, '\n')
    // Keep only safe tags: b, strong, i, em, u, s, a
    .replace(/<(?!\/?(?:b|strong|i|em|u|s|a\s))[^>]+>/gi, '')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

/** Strip ALL HTML tags for plain-text (used for length calculation) */
function stripHtml(html: string): string {
  return html.replace(/<[^>]+>/g, '').replace(/&[a-z]+;/gi, ' ').trim();
}

function formatTime(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}

/** Collapsible text/html block */
function CollapsibleText({ text, html, limit = 400 }: { text?: string; html?: string; limit?: number }) {
  const [expanded, setExpanded] = useState(false);
  const plainLength = html ? stripHtml(html).length : (text?.length || 0);
  const isLong = plainLength > limit;

  if (html) {
    const display = isLong && !expanded ? sanitizeHtml(html).slice(0, limit) + '...' : sanitizeHtml(html);
    return (
      <>
        <div className="text-sm whitespace-pre-wrap break-words" dangerouslySetInnerHTML={{ __html: display }} />
        {isLong && (
          <button className="text-xs text-primary mt-1" onClick={() => setExpanded(!expanded)}>
            {expanded ? 'Свернуть' : 'Показать полностью'}
          </button>
        )}
      </>
    );
  }

  return (
    <>
      <div className="text-sm whitespace-pre-wrap break-words">
        {isLong && !expanded ? (text || '').slice(0, limit) + '...' : text}
      </div>
      {isLong && (
        <button className="text-xs text-primary mt-1" onClick={() => setExpanded(!expanded)}>
          {expanded ? 'Свернуть' : 'Показать полностью'}
        </button>
      )}
    </>
  );
}

/** Funnel message from bot */
function FunnelCard({ event }: { event: UserEvent }) {
  const stageLabel = funnelStageLabels[event.event_data] || event.event_data;

  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] rounded-2xl px-3.5 py-2 bg-card border border-border text-card-foreground rounded-bl-sm">
        <div className="flex items-center gap-1.5 mb-1">
          <Megaphone className="w-3.5 h-3.5 text-primary shrink-0" />
          <span className="text-xs font-medium text-primary">{stageLabel}</span>
          <span className="text-[10px] text-muted-foreground ml-auto shrink-0">
            {formatTime(event.created_at)}
          </span>
        </div>
        {event.message_text ? (
          <CollapsibleText html={event.message_text} />
        ) : (
          <div className="text-xs text-muted-foreground italic">Текст не сохранён</div>
        )}
      </div>
    </div>
  );
}

/** Button click from user */
function ButtonClickCard({ event }: { event: UserEvent }) {
  const info = eventButtonLabels[event.event_data];
  const label = info?.label || event.event_data;

  return (
    <div className="flex justify-end">
      <div className="flex items-center gap-2 max-w-[85%] rounded-2xl px-3.5 py-2 bg-accent/50 border border-accent rounded-br-sm">
        <MousePointerClick className="w-3.5 h-3.5 text-primary shrink-0" />
        <span className="text-sm text-foreground font-medium">{label}</span>
        <span className="text-[10px] text-muted-foreground shrink-0 ml-1">
          {formatTime(event.created_at)}
        </span>
      </div>
    </div>
  );
}

/** Chat message (human or AI) */
function ChatMessageCard({ msg }: { msg: ChatMessage }) {
  const { formatted, isJson } = formatJsonContent(msg.content);
  const isHuman = msg.type === 'human';
  const isMealPlan = !isHuman && (msg.content.includes('ПЛАН ПИТАНИЯ') || msg.content.includes('MEAL PLAN') || msg.content.includes('ИТОГО ЗА ДЕНЬ'));
  const hasHtml = !isHuman && /<[a-z][\s\S]*>/i.test(msg.content);

  return (
    <div className={`flex ${isHuman ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[85%] rounded-2xl px-3.5 py-2 ${
        isHuman
          ? 'bg-primary text-primary-foreground rounded-br-sm'
          : 'bg-card border border-border text-card-foreground rounded-bl-sm'
      }`}>
        {isJson && (
          <div className="flex items-center gap-1.5 mb-1">
            <ClipboardList className="w-3.5 h-3.5 text-primary" />
            <span className="text-xs font-medium text-primary">Собранные данные</span>
          </div>
        )}
        {isMealPlan && (
          <div className="flex items-center gap-1.5 mb-1">
            <Bot className="w-3.5 h-3.5 text-primary" />
            <span className="text-xs font-medium text-primary">Рацион питания</span>
          </div>
        )}
        {hasHtml ? (
          <CollapsibleText html={msg.content} />
        ) : (
          <CollapsibleText text={isJson ? formatted : msg.content} />
        )}
        {msg.created_at && (
          <div className="text-[10px] text-muted-foreground mt-1 text-right">
            {formatTime(msg.created_at)}
          </div>
        )}
      </div>
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

    // Add chat messages (skip empty)
    messages
      .filter((msg) => msg.content && msg.content.trim() !== '')
      .forEach((msg) => {
        items.push({ kind: 'message', ts: msg.created_at, msg });
      });

    // Add events
    events.forEach((evt) => {
      if (evt.event_type === 'funnel_message') {
        items.push({ kind: 'funnel', ts: evt.created_at, event: evt });
      } else {
        items.push({ kind: 'button', ts: evt.created_at, event: evt });
      }
    });

    // Sort chronologically: items with timestamps sorted by time,
    // items without timestamps (old chat messages) come first, sorted by id
    items.sort((a, b) => {
      const tsA = a.ts ? new Date(a.ts).getTime() : 0;
      const tsB = b.ts ? new Date(b.ts).getTime() : 0;

      // Both have no timestamp — sort by message id
      if (!a.ts && !b.ts) {
        const idA = a.kind === 'message' ? a.msg.id : 0;
        const idB = b.kind === 'message' ? b.msg.id : 0;
        return idA - idB;
      }
      // One has no timestamp — put it first (old messages before events)
      if (!a.ts) return -1;
      if (!b.ts) return 1;
      // Both have timestamps — chronological order
      return tsA - tsB;
    });

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
        if (item.kind === 'funnel') {
          return <FunnelCard key={`funnel-${item.event.id}`} event={item.event} />;
        }
        if (item.kind === 'button') {
          return <ButtonClickCard key={`btn-${item.event.id}`} event={item.event} />;
        }
        return <ChatMessageCard key={`msg-${item.msg.id}`} msg={item.msg} />;
      })}
    </div>
  );
}
