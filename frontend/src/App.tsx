import { useState, useEffect, useCallback } from 'react';
import { UserList } from './components/UserList';
import { UserDetail } from './components/UserDetail';
import { User } from './hooks/useApi';

type View = 'list' | 'detail';

function App() {
  const [view, setView] = useState<View>('list');
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

  // Initialize Telegram WebApp
  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
    }
  }, []);

  // Handle BackButton
  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (!tg) return;

    if (view === 'detail') {
      tg.BackButton.show();
      tg.BackButton.onClick(handleBack);
    } else {
      tg.BackButton.hide();
    }

    return () => {
      tg.BackButton.offClick(handleBack);
    };
  }, [view, handleBack]);

  return (
    <div className="min-h-screen bg-tg-bg">
      {view === 'list' && (
        <div key="list" className="animate-slideInLeft">
          <UserList onSelectUser={handleSelectUser} />
        </div>
      )}
      {view === 'detail' && selectedUser && (
        <div key="detail" className="animate-slideInRight">
          <UserDetail user={selectedUser} />
        </div>
      )}
    </div>
  );
}

export default App;
