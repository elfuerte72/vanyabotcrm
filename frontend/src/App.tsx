import { useState, useEffect, useCallback } from 'react';
import { UserList } from './components/UserList';
import { UserDetail } from './components/UserDetail';
import { RecentUsers } from './components/RecentUsers';
import { User } from './hooks/useApi';
import { Users, UserPlus } from 'lucide-react';

type View = 'list' | 'detail';
type Tab = 'clients' | 'recent';

function App() {
  const [view, setView] = useState<View>('list');
  const [activeTab, setActiveTab] = useState<Tab>('clients');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  const handleSelectUser = useCallback((user: User) => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
    setSelectedUser(user);
    setView('detail');
  }, []);

  const handleBack = useCallback(() => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
    setView('list');
    setSelectedUser(null);
  }, []);

  const handleTabChange = useCallback((tab: Tab) => {
    if (tab === activeTab) return;
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
    setActiveTab(tab);
  }, [activeTab]);

  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (tg) { tg.ready(); tg.expand(); }
  }, []);

  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (!tg) return;
    if (view === 'detail') {
      tg.BackButton.show();
      tg.BackButton.onClick(handleBack);
    } else {
      tg.BackButton.hide();
    }
    return () => { tg.BackButton.offClick(handleBack); };
  }, [view, handleBack]);

  return (
    <div className="min-h-screen bg-background">
      {view === 'list' && (
        <>
          {activeTab === 'clients' && <UserList onSelectUser={handleSelectUser} />}
          {activeTab === 'recent' && <RecentUsers onSelectUser={handleSelectUser} />}
        </>
      )}
      {view === 'detail' && selectedUser && <UserDetail user={selectedUser} onBack={handleBack} />}

      {view === 'list' && (
        <div className="fixed bottom-0 left-0 right-0 z-20 bg-background/95 backdrop-blur-sm border-t border-border" style={{ paddingBottom: 'var(--safe-area-bottom, 0px)' }}>
          <div className="flex">
            <button
              onClick={() => handleTabChange('clients')}
              className={`flex-1 flex flex-col items-center gap-0.5 py-2 ${activeTab === 'clients' ? 'text-primary' : 'text-muted-foreground'}`}
            >
              <Users className="w-5 h-5" />
              <span className="text-[10px] font-medium">Клиенты</span>
            </button>
            <button
              onClick={() => handleTabChange('recent')}
              className={`flex-1 flex flex-col items-center gap-0.5 py-2 ${activeTab === 'recent' ? 'text-primary' : 'text-muted-foreground'}`}
            >
              <UserPlus className="w-5 h-5" />
              <span className="text-[10px] font-medium">Новые</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
