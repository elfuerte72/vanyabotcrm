import { User, goalLabels, activityLabels } from '../hooks/useApi';
import { ChatHistory } from './ChatHistory';

interface UserDetailProps {
  user: User;
}

export function UserDetail({ user }: UserDetailProps) {
  const displayName = user.first_name || user.username || `User ${user.chat_id}`;

  return (
    <div className="pb-20">
      {/* Hero Header */}
      <div className="flex flex-col items-center pt-6 pb-4 animate-fadeIn">
        <div className="w-20 h-20 rounded-full bg-tg-button/15 flex items-center justify-center text-tg-button text-3xl font-semibold mb-3">
          {displayName.charAt(0).toUpperCase()}
        </div>
        <h1 className="text-xl font-bold text-tg-text">{displayName}</h1>
        {user.username && (
          <div className="text-sm text-tg-hint mt-0.5">@{user.username}</div>
        )}
        <div className="flex gap-2 mt-2">
          {user.is_buyer && (
            <span className="px-2 py-0.5 text-xs rounded-full bg-tg-button/15 text-tg-button font-medium">
              Покупатель
            </span>
          )}
          {user.get_food && (
            <span className="px-2 py-0.5 text-xs rounded-full bg-tg-button/15 text-tg-button font-medium">
              Получает еду
            </span>
          )}
        </div>
      </div>

      {/* Basic Info */}
      <section className="px-4 mb-6 animate-fadeInUp stagger-1">
        <h2 className="text-xs font-medium text-tg-hint uppercase tracking-wide mb-2 px-1">
          Основная информация
        </h2>
        <div className="bg-tg-secondary-bg rounded-xl divide-y divide-tg-bg">
          <InfoRow label="Пол" value={user.sex === 'male' ? 'Мужской' : user.sex === 'female' ? 'Женский' : '-'} />
          <InfoRow label="Возраст" value={user.age ? `${user.age} лет` : '-'} />
          <InfoRow label="Рост" value={user.height ? `${user.height} см` : '-'} />
          <InfoRow label="Вес" value={user.weight ? `${user.weight} кг` : '-'} />
          <InfoRow
            label="Активность"
            value={user.activity_level ? activityLabels[user.activity_level] || user.activity_level : '-'}
          />
          <InfoRow
            label="Цель"
            value={user.goal ? goalLabels[user.goal] || user.goal : '-'}
          />
        </div>
      </section>

      {/* Nutrition */}
      {user.calories && (
        <section className="px-4 mb-6 animate-fadeInUp stagger-2">
          <h2 className="text-xs font-medium text-tg-hint uppercase tracking-wide mb-2 px-1">
            КБЖУ
          </h2>
          <div className="grid grid-cols-4 gap-2">
            <NutrientCard label="Калории" value={user.calories} unit="ккал" />
            <NutrientCard label="Белки" value={user.protein} unit="г" />
            <NutrientCard label="Жиры" value={user.fats} unit="г" />
            <NutrientCard label="Углеводы" value={user.carbs} unit="г" />
          </div>
        </section>
      )}

      {/* Restrictions */}
      {(user.allergies || user.excluded_foods) && (
        <section className="px-4 mb-6 animate-fadeInUp stagger-3">
          <h2 className="text-xs font-medium text-tg-hint uppercase tracking-wide mb-2 px-1">
            Ограничения
          </h2>
          <div className="bg-tg-secondary-bg rounded-xl divide-y divide-tg-bg">
            {user.allergies && (
              <div className="px-4 py-3 min-h-[44px] flex flex-col justify-center">
                <div className="text-xs text-tg-hint mb-0.5">Аллергии</div>
                <div className="text-sm text-tg-text">{user.allergies}</div>
              </div>
            )}
            {user.excluded_foods && (
              <div className="px-4 py-3 min-h-[44px] flex flex-col justify-center">
                <div className="text-xs text-tg-hint mb-0.5">Исключённые продукты</div>
                <div className="text-sm text-tg-text">{user.excluded_foods}</div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Funnel */}
      <section className="px-4 mb-6 animate-fadeInUp stagger-4">
        <h2 className="text-xs font-medium text-tg-hint uppercase tracking-wide mb-2 px-1">
          Воронка продаж
        </h2>
        <div className="bg-tg-secondary-bg rounded-xl p-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-tg-text">Этап {user.funnel_stage || 0} из 6</span>
            <span className="text-sm text-tg-hint">
              {Math.round(((user.funnel_stage || 0) / 6) * 100)}%
            </span>
          </div>
          <div className="flex gap-1">
            {[1, 2, 3, 4, 5, 6].map((stage) => (
              <div
                key={stage}
                className={`h-2 flex-1 rounded-full ${
                  stage <= (user.funnel_stage || 0)
                    ? 'bg-tg-button'
                    : 'bg-tg-bg'
                }`}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Chat History */}
      <section className="px-4 animate-fadeInUp stagger-5">
        <h2 className="text-xs font-medium text-tg-hint uppercase tracking-wide mb-2 px-1">
          История чата
        </h2>
        <ChatHistory sessionId={String(user.chat_id)} />
      </section>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center px-4 min-h-[44px]">
      <span className="text-sm text-tg-hint">{label}</span>
      <span className="text-sm text-tg-text font-medium">{value}</span>
    </div>
  );
}

function NutrientCard({
  label,
  value,
  unit,
}: {
  label: string;
  value: number | null;
  unit: string;
}) {
  return (
    <div className="bg-tg-secondary-bg rounded-xl p-3 text-center">
      <div className="text-lg font-bold text-tg-text">{value || 0}</div>
      <div className="text-xs text-tg-hint">{unit}</div>
      <div className="text-xs text-tg-hint mt-0.5">{label}</div>
    </div>
  );
}
