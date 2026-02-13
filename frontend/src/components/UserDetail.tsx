import { User, goalLabels, activityLabels } from '../hooks/useApi';
import { ChatHistory } from './ChatHistory';
import { Card, CardContent } from './ui/card';
import { Avatar, AvatarFallback } from './ui/avatar';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import {
  User as UserIcon,
  Calendar,
  Ruler,
  Weight,
  Activity,
  Target,
  Flame,
  Beef,
  Droplets,
  Wheat,
  ArrowLeft,
} from 'lucide-react';

interface UserDetailProps {
  user: User;
  onBack?: () => void;
}

export function UserDetail({ user, onBack }: UserDetailProps) {
  const displayName = user.first_name || user.username || `User ${user.chat_id}`;
  const funnelPercent = Math.round(((user.funnel_stage || 0) / 6) * 100);

  return (
    <div className="pb-20">
      {/* Back Button */}
      {onBack && (
        <div className="sticky top-0 z-10 bg-background/95 backdrop-blur-sm border-b border-border">
          <button
            onClick={onBack}
            className="flex items-center gap-1.5 px-4 py-3 text-sm text-primary active:opacity-70"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Назад</span>
          </button>
        </div>
      )}

      {/* Hero Header */}
      <div className="flex flex-col items-center pt-6 pb-5">
        <Avatar className="w-20 h-20">
          <AvatarFallback className="text-3xl bg-primary/20">
            {displayName.charAt(0).toUpperCase()}
          </AvatarFallback>
        </Avatar>
        <h1 className="text-xl font-bold text-foreground mt-3">{displayName}</h1>
        {user.username && (
          <div className="text-sm text-muted-foreground mt-0.5">@{user.username}</div>
        )}
        <div className="flex gap-2 mt-3">
          {user.is_buyer && <Badge variant="buyer">Покупатель</Badge>}
          {user.get_food && <Badge variant="secondary">Получает еду</Badge>}
        </div>
      </div>

      {/* Basic Info */}
      <section className="px-4 mb-4">
        <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 px-1">
          Основная информация
        </h2>
        <Card>
          <CardContent className="p-0">
            <InfoRow icon={<UserIcon className="w-4 h-4" />} label="Пол" value={user.sex === 'male' ? 'Мужской' : user.sex === 'female' ? 'Женский' : '-'} />
            <Separator />
            <InfoRow icon={<Calendar className="w-4 h-4" />} label="Возраст" value={user.age ? `${user.age} лет` : '-'} />
            <Separator />
            <InfoRow icon={<Ruler className="w-4 h-4" />} label="Рост" value={user.height ? `${user.height} см` : '-'} />
            <Separator />
            <InfoRow icon={<Weight className="w-4 h-4" />} label="Вес" value={user.weight ? `${user.weight} кг` : '-'} />
            <Separator />
            <InfoRow icon={<Activity className="w-4 h-4" />} label="Активность" value={user.activity_level ? activityLabels[user.activity_level] || user.activity_level : '-'} />
            <Separator />
            <InfoRow icon={<Target className="w-4 h-4" />} label="Цель" value={user.goal ? goalLabels[user.goal] || user.goal : '-'} />
          </CardContent>
        </Card>
      </section>

      {/* Nutrition KBJU */}
      {user.calories && (
        <section className="px-4 mb-4">
          <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 px-1">
            КБЖУ
          </h2>
          <div className="grid grid-cols-2 gap-2">
            <NutrientCard icon={<Flame className="w-4 h-4" />} label="Калории" value={user.calories} unit="ккал" accent />
            <NutrientCard icon={<Beef className="w-4 h-4" />} label="Белки" value={user.protein} unit="г" />
            <NutrientCard icon={<Droplets className="w-4 h-4" />} label="Жиры" value={user.fats} unit="г" />
            <NutrientCard icon={<Wheat className="w-4 h-4" />} label="Углеводы" value={user.carbs} unit="г" />
          </div>
        </section>
      )}

      {/* Restrictions */}
      {(user.allergies || user.excluded_foods) && (
        <section className="px-4 mb-4">
          <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 px-1">
            Ограничения
          </h2>
          <Card>
            <CardContent className="p-0">
              {user.allergies && (
                <div className="px-4 py-3">
                  <div className="text-xs text-muted-foreground mb-1">Аллергии</div>
                  <div className="flex flex-wrap gap-1.5">
                    {user.allergies.split(',').map((item, i) => (
                      <Badge key={i} variant="outline" className="text-xs">{item.trim()}</Badge>
                    ))}
                  </div>
                </div>
              )}
              {user.allergies && user.excluded_foods && <Separator />}
              {user.excluded_foods && (
                <div className="px-4 py-3">
                  <div className="text-xs text-muted-foreground mb-1">Исключённые продукты</div>
                  <div className="flex flex-wrap gap-1.5">
                    {user.excluded_foods.split(',').map((item, i) => (
                      <Badge key={i} variant="outline" className="text-xs">{item.trim()}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </section>
      )}

      {/* Funnel */}
      <section className="px-4 mb-4">
        <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 px-1">
          Воронка продаж
        </h2>
        <Card>
          <CardContent className="p-4">
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm text-foreground font-medium">Этап {user.funnel_stage || 0} из 6</span>
              <span className="text-sm text-muted-foreground">{funnelPercent}%</span>
            </div>
            <div className="flex gap-1.5">
              {[1, 2, 3, 4, 5, 6].map((stage) => (
                <div
                  key={stage}
                  className={`h-2 flex-1 rounded-full ${stage <= (user.funnel_stage || 0) ? 'bg-primary' : 'bg-secondary'}`}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Chat History */}
      <section className="px-4">
        <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 px-1">
          История взаимодействий
        </h2>
        <ChatHistory sessionId={String(user.chat_id)} />
      </section>
    </div>
  );
}

function InfoRow({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center px-4 min-h-[44px]">
      <span className="text-muted-foreground mr-3">{icon}</span>
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm text-foreground font-medium ml-auto">{value}</span>
    </div>
  );
}

function NutrientCard({ icon, label, value, unit, accent }: { icon: React.ReactNode; label: string; value: number | null; unit: string; accent?: boolean }) {
  return (
    <Card className={accent ? 'border-primary/30 bg-primary/5' : ''}>
      <CardContent className="p-3 text-center">
        <div className={`flex justify-center mb-1.5 ${accent ? 'text-primary' : 'text-muted-foreground'}`}>{icon}</div>
        <div className={`text-xl font-bold ${accent ? 'text-primary' : 'text-foreground'}`}>{value || 0}</div>
        <div className="text-xs text-muted-foreground">{unit}</div>
        <div className="text-xs text-muted-foreground mt-0.5">{label}</div>
      </CardContent>
    </Card>
  );
}
