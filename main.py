import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Check,
  Flame,
  Plus,
  X,
  Sparkles,
  User,
  Quote as QuoteIcon,
  Target,
  ArrowLeft,
  Home
} from 'lucide-react';

export default function App() {
  const [habits, setHabits] = useState([]);

  // Заменяем отдельные булевые стейты на единую систему роутинга (страниц)
  const [activePage, setActivePage] = useState('home'); // 'home', 'add', 'profile', 'quotes'

  // Стейт для новой привычки
  const [newHabit, setNewHabit] = useState({
    title: '',
    sub: '',
    color: '#4ECDC4',
    type: 'single',
    target: 1
  });

  const [completedCount, setCompletedCount] = useState(0);

  // Обновленный список цитат с авторами (развернут для читаемости)
  const quotes = [
    {
      text: "Дисциплина — это решение делать то, чего очень не хочется делать, чтобы достичь того, чего очень хочется.",
      author: "Джон Максвелл"
    },
    {
      text: "Не жди идеального момента, бери момент и делай его идеальным.",
      author: "Аарон Бальик"
    },
    {
      text: "Секрет успеха — в постоянстве цели.",
      author: "Бенджамин Дизраэли"
    },
    {
      text: "Каждый день — это новая возможность стать лучше, чем вчера.",
      author: "Неизвестный"
    },
    {
      text: "Маленькие шаги каждый день ведут к большим результатам.",
      author: "Роберт Кольер"
    }
  ];

  const [currentQuote, setCurrentQuote] = useState(quotes[0]);

  useEffect(() => {
    setCompletedCount(habits.filter(h => h.done).length);
  }, [habits]);

  const toggle = (id) => {
    setHabits(habits.map(h => {
      if (h.id === id) {
        if (h.done) {
          // Если уже выполнено - сбрасываем
          return {
            ...h,
            currentProgress: 0,
            done: false,
            streak: Math.max(0, h.streak - 1),
            totalCompleted: Math.max(0, (h.totalCompleted || 0) - 1)
          };
        } else {
          // Увеличиваем прогресс
          const newProgress = (h.currentProgress || 0) + 1;
          const isDone = newProgress >= h.target;

          return {
            ...h,
            currentProgress: newProgress,
            done: isDone,
            streak: isDone ? h.streak + 1 : h.streak,
            totalCompleted: isDone ? (h.totalCompleted || 0) + 1 : (h.totalCompleted || 0)
          };
        }
      }
      return h;
    }));
  };

  const addHabit = () => {
    if (!newHabit.title.trim()) return;
    setHabits([...habits, {
      id: Date.now(),
      title: newHabit.title,
      sub: newHabit.sub || (newHabit.type === 'multiple' ? `${newHabit.target} раз(а) в день` : 'каждый день'),
      done: false,
      currentProgress: 0,
      target: newHabit.type === 'multiple' ? newHabit.target : 1,
      color: newHabit.color,
      streak: 0,
      totalCompleted: 0
    }]);

    // Сброс формы и возврат на главную
    setNewHabit({
      title: '',
      sub: '',
      color: '#4ECDC4',
      type: 'single',
      target: 1
    });
    setActivePage('home');
  };

  const deleteHabit = (id) => {
    setHabits(habits.filter(h => h.id !== id));
  };

  const days = useMemo(() => {
    const current = new Date();
    const dayOfWeek = current.getDay() === 0 ? 7 : current.getDay();
    const dayNames = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];

    return Array.from({ length: 7 }).map((_, i) => {
      const d = new Date(current);
      d.setDate(current.getDate() - dayOfWeek + i + 1);
      return {
        n: dayNames[d.getDay()],
        d: d.getDate(),
        today: d.toDateString() === current.toDateString()
      };
    });
  }, []);

  const colors = [
    '#FF6B35', '#4ECDC4', '#95E1D3', '#F38181', '#AA96DA',
    '#FCBAD3', '#FFFFD2', '#A8E6CF', '#FFD93D', '#6BCB77'
  ];

  const progress = habits.length > 0 ? Math.round((completedCount / habits.length) * 100) : 0;

  // Функция для скрытия клавиатуры при нажатии Enter
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      e.target.blur(); // Убирает фокус, что автоматически прячет клавиатуру на iOS/Android
    }
  };

  const pageVariants = {
    initial: { opacity: 0, x: 20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -20 }
  };

  return (
      // Используем 100dvh для фиксации высоты экрана и предотвращения слетания верстки
      <div
          style={{ height: '100dvh' }}
          className="bg-[#0a0a0f] text-white font-sans overflow-hidden relative selection:bg-cyan-500/30"
      >

        {/* ФОН (Анимации) */}
        <div className="fixed inset-0 pointer-events-none z-0">
          <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-purple-600/10 rounded-full blur-[120px] animate-pulse" />
          <div
              className="absolute bottom-[-10%] right-[-10%] w-[400px] h-[400px] bg-pink-500/10 rounded-full blur-[100px] animate-pulse"
              style={{ animationDelay: '2s' }}
          />
          <div
              className="absolute top-[40%] right-[20%] w-[300px] h-[300px] bg-cyan-500/8 rounded-full blur-[80px] animate-pulse"
              style={{ animationDelay: '4s' }}
          />
        </div>

        {/* ГЛАВНЫЙ СКРОЛЛИРУЕМЫЙ КОНТЕЙНЕР */}
        <div className="h-full overflow-y-auto scroll-smooth relative z-10 pb-28">
          <AnimatePresence mode="wait">

            {/* ================= ГЛАВНАЯ СТРАНИЦА ================= */}
            {activePage === 'home' && (
                <motion.div
                    key="home"
                    variants={pageVariants}
                    initial="initial"
                    animate="animate"
                    exit="exit"
                    className="px-4 pt-10 max-w-[480px] mx-auto flex flex-col min-h-full"
                >

                  <motion.div
                      initial={{ opacity: 0, y: -20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex justify-between items-start mb-6"
                  >
                    <div>
                      <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-white via-white to-gray-400 bg-clip-text text-transparent">
                        Мои привычки
                      </h1>
                      <p className="text-gray-400 text-sm mt-1">Достигай большего каждый день</p>
                    </div>
                  </motion.div>

                  {/* Progress Ring */}
                  <motion.div
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.1 }}
                      className="mb-8 p-5 rounded-3xl bg-gradient-to-br from-white/[0.07] to-white/[0.02] border border-white/10 backdrop-blur-xl"
                  >
                    <div className="flex items-center gap-5">
                      <div className="relative w-16 h-16 flex-shrink-0">
                        <svg className="w-16 h-16 -rotate-90" viewBox="0 0 64 64">
                          <circle cx="32" cy="32" r="28" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="6" />
                          <circle
                              cx="32" cy="32" r="28" fill="none"
                              stroke="url(#progressGradient)"
                              strokeWidth="6"
                              strokeLinecap="round"
                              strokeDasharray={`${progress * 1.76} 176`}
                              className="transition-all duration-700 ease-out"
                          />
                          <defs>
                            <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                              <stop offset="0%" stopColor="#4ECDC4" />
                              <stop offset="100%" stopColor="#FF6B35" />
                            </linearGradient>
                          </defs>
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="text-sm font-bold">{progress}%</span>
                        </div>
                      </div>
                      <div className="flex-1">
                        <p className="text-gray-400 text-sm">Сегодня выполнено</p>
                        <div className="flex items-baseline gap-1 mt-1">
                          <span className="text-2xl font-bold">{completedCount}</span>
                          <span className="text-gray-500 text-sm">из {habits.length}</span>
                        </div>
                        {completedCount === habits.length && habits.length > 0 && (
                            <motion.div
                                initial={{ opacity: 0, scale: 0 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="flex items-center gap-1 mt-1"
                            >
                              <Sparkles size={12} className="text-yellow-400" />
                              <span className="text-yellow-400 text-xs font-medium">Все выполнены!</span>
                              <Sparkles size={12} className="text-yellow-400" />
                            </motion.div>
                        )}
                      </div>
                    </div>
                  </motion.div>

                  {/* Calendar */}
                  <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.2 }}
                      className="flex gap-2 mb-8 overflow-x-auto pb-2 scrollbar-hide"
                  >
                    {days.map((day, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 + i * 0.05 }}
                            className={`flex-1 min-w-[44px] flex flex-col items-center gap-1.5 py-3 rounded-2xl cursor-pointer transition-all ${
                                day.today
                                    ? 'bg-white/10 border border-white/20 shadow-lg shadow-white/5'
                                    : 'hover:bg-white/5 border border-transparent'
                            }`}
                        >
                    <span className={`text-[10px] font-bold uppercase tracking-wider ${day.today ? 'text-white' : 'text-gray-500'}`}>
                      {day.n}
                    </span>
                          <div className={`w-9 h-9 rounded-xl flex items-center justify-center text-sm font-semibold ${
                              day.today
                                  ? (completedCount === habits.length && habits.length > 0)
                                      ? 'bg-gradient-to-br from-green-400 to-emerald-500 text-white shadow-lg shadow-green-500/30'
                                      : 'bg-white/10 text-white'
                                  : 'text-gray-400'
                          }`}>
                            {day.today && completedCount === habits.length && habits.length > 0 ? <Check size={16} strokeWidth={3} /> : day.d}
                          </div>
                        </motion.div>
                    ))}
                  </motion.div>

                  {/* Habits Grid */}
                  <div className="space-y-3 flex-1 pb-10">
                    {habits.length === 0 ? (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="text-center py-10 opacity-50 flex flex-col items-center justify-center"
                        >
                          <div className="w-16 h-16 mb-4 rounded-2xl bg-white/5 flex items-center justify-center border border-white/10">
                            <Target size={24} className="text-gray-400" />
                          </div>
                          <p className="text-sm text-gray-400">
                            Список привычек пуст.<br/>Нажмите + чтобы добавить первую.
                          </p>
                        </motion.div>
                    ) : (
                        <AnimatePresence>
                          {habits.map((h, i) => (
                              <motion.div
                                  key={h.id}
                                  initial={{ opacity: 0, x: -20 }}
                                  animate={{ opacity: 1, x: 0 }}
                                  exit={{ opacity: 0, x: 20, height: 0 }}
                                  transition={{ delay: 0.1 + i * 0.05 }}
                                  layout
                                  className={`group relative rounded-2xl border overflow-hidden cursor-pointer transition-all duration-300 ${
                                      h.done
                                          ? 'border-white/10 shadow-lg'
                                          : 'border-white/[0.06] hover:border-white/15'
                                  }`}
                                  style={{
                                    background: h.done
                                        ? `linear-gradient(135deg, ${h.color}22 0%, ${h.color}11 100%)`
                                        : 'linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.02) 100%)'
                                  }}
                                  onClick={() => toggle(h.id)}
                              >
                                <div
                                    className="absolute left-0 top-0 bottom-0 w-1 transition-all duration-300"
                                    style={{ backgroundColor: h.color, opacity: h.done ? 1 : 0.3 }}
                                />
                                <div className="p-4 pl-5">
                                  <div className="flex items-start justify-between">
                                    <div className="flex items-center gap-4 flex-1">
                                      <motion.div
                                          whileTap={{ scale: 0.85 }}
                                          className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 transition-all duration-300 ${
                                              h.done ? 'shadow-lg' : 'border-2 border-gray-600 hover:border-gray-400'
                                          }`}
                                          style={{
                                            backgroundColor: h.done ? h.color : 'transparent',
                                            boxShadow: h.done ? `0 4px 12px ${h.color}40` : 'none'
                                          }}
                                      >
                                        {h.done ? (
                                            <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', stiffness: 300, damping: 20 }}>
                                              <Check size={18} className="text-white" strokeWidth={3} />
                                            </motion.div>
                                        ) : (
                                            h.target > 1 && (
                                                <span className="text-[12px] font-bold text-gray-300">
                                      {h.currentProgress}/{h.target}
                                    </span>
                                            )
                                        )}
                                      </motion.div>

                                      <div className="flex-1 min-w-0">
                                        <h3 className={`text-[16px] font-semibold leading-tight transition-all duration-300 ${
                                            h.done ? 'text-white line-through decoration-white/30' : 'text-gray-200'
                                        }`}>
                                          {h.title}
                                        </h3>
                                        <p className="text-xs text-gray-500 mt-1">{h.sub}</p>
                                      </div>
                                    </div>

                                    <div className="flex items-center gap-2">
                                      {h.streak > 0 && (
                                          <motion.div className="flex items-center gap-1 px-2 py-1 rounded-lg bg-white/5" whileHover={{ scale: 1.05 }}>
                                            <Flame size={12} className={h.streak >= 7 ? 'text-orange-400 fill-orange-400' : 'text-gray-500'} />
                                            <span className={`text-xs font-bold ${h.streak >= 7 ? 'text-orange-400' : 'text-gray-400'}`}>
                                    {h.streak}
                                  </span>
                                          </motion.div>
                                      )}
                                      <motion.button
                                          whileTap={{ scale: 0.85 }}
                                          onClick={(e) => { e.stopPropagation(); deleteHabit(h.id); }}
                                          className="w-7 h-7 rounded-lg flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all bg-white/5 hover:bg-red-500/20"
                                      >
                                        <X size={12} className="text-gray-500 hover:text-red-400" />
                                      </motion.button>
                                    </div>
                                  </div>
                                </div>
                              </motion.div>
                          ))}
                        </AnimatePresence>
                    )}
                  </div>
                </motion.div>
            )}

            {/* ================= СТРАНИЦА ПРОФИЛЯ ================= */}
            {activePage === 'profile' && (
                <motion.div
                    key="profile"
                    variants={pageVariants}
                    initial="initial"
                    animate="animate"
                    exit="exit"
                    className="px-4 pt-10 max-w-[480px] mx-auto min-h-full"
                >
                  <h2 className="text-3xl font-bold mb-8">Профиль</h2>
                  <div className="p-6 rounded-3xl bg-white/[0.05] border border-white/10 backdrop-blur-xl">
                    <div className="flex items-center gap-4 mb-8 pb-6 border-b border-white/10">
                      <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-cyan-500 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
                        <User size={28} className="text-white" />
                      </div>
                      <div>
                        <h3 className="font-bold text-xl leading-tight">Мой прогресс</h3>
                        <p className="text-sm text-gray-400">Статистика по привычкам</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-5 rounded-2xl bg-black/40 border border-white/5 text-center flex flex-col items-center justify-center relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-16 h-16 bg-cyan-500/10 rounded-bl-full blur-xl"></div>
                        <div className="text-4xl font-bold text-white mb-2">
                          {habits.reduce((acc, h) => acc + (h.totalCompleted || 0), 0)}
                        </div>
                        <div className="text-[11px] text-gray-400 uppercase tracking-wider font-medium">
                          Всего выполнено
                        </div>
                      </div>
                      <div className="p-5 rounded-2xl bg-black/40 border border-white/5 text-center flex flex-col items-center justify-center relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-16 h-16 bg-orange-500/10 rounded-br-full blur-xl"></div>
                        <div className="text-4xl font-bold bg-gradient-to-b from-orange-400 to-red-500 bg-clip-text text-transparent mb-2">
                          {habits.length > 0 ? Math.max(...habits.map(h => h.streak)) : 0}
                        </div>
                        <div className="text-[11px] text-gray-400 uppercase tracking-wider font-medium">
                          Дней в строю (Max)
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
            )}

            {/* ================= СТРАНИЦА ЦИТАТ ================= */}
            {activePage === 'quotes' && (
                <motion.div
                    key="quotes"
                    variants={pageVariants}
                    initial="initial"
                    animate="animate"
                    exit="exit"
                    className="px-4 pt-10 max-w-[480px] mx-auto min-h-full flex flex-col"
                >
                  <h2 className="text-3xl font-bold mb-8">Мотивация</h2>
                  <div className="flex-1 flex flex-col justify-center pb-20">
                    <div className="p-8 rounded-3xl bg-black border border-white/10 shadow-2xl relative">
                      <QuoteIcon size={80} className="absolute top-4 left-4 text-white/[0.03] rotate-180" />

                      <div className="flex items-center gap-2 mb-6 relative z-10">
                        <Sparkles size={20} className="text-yellow-400" />
                        <span className="font-semibold text-white/50 uppercase tracking-wider text-xs">
                      Цитата дня
                    </span>
                      </div>

                      <div className="relative z-10 my-8">
                        <p className="text-white text-2xl font-medium leading-relaxed mb-6">
                          "{currentQuote.text}"
                        </p>
                        <p className="text-gray-400 text-base italic border-t border-white/10 pt-4">
                          — {currentQuote.author}
                        </p>
                      </div>

                      <button
                          onClick={() => setCurrentQuote(quotes[Math.floor(Math.random() * quotes.length)])}
                          className="w-full py-4 rounded-xl bg-white/5 hover:bg-white/10 text-xs uppercase tracking-widest text-white font-bold transition-colors border border-white/5"
                      >
                        Следующая цитата
                      </button>
                    </div>
                  </div>
                </motion.div>
            )}

            {/* ================= СТРАНИЦА ДОБАВЛЕНИЯ ПРИВЫЧКИ ================= */}
            {activePage === 'add' && (
                <motion.div
                    key="add"
                    variants={pageVariants}
                    initial="initial"
                    animate="animate"
                    exit="exit"
                    className="px-4 pt-8 pb-32 max-w-[480px] mx-auto min-h-full"
                >
                  <div className="flex items-center gap-4 mb-8">
                    <button
                        onClick={() => setActivePage('home')}
                        className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center hover:bg-white/10 transition-all"
                    >
                      <ArrowLeft size={20} />
                    </button>
                    <h2 className="text-2xl font-bold">Новая привычка</h2>
                  </div>

                  <div className="space-y-6">
                    <div>
                      <label className="text-xs text-gray-400 uppercase tracking-wider font-medium mb-2 block">
                        Название
                      </label>
                      <input
                          type="text"
                          value={newHabit.title}
                          onChange={(e) => setNewHabit({ ...newHabit, title: e.target.value })}
                          onKeyDown={handleKeyDown}
                          placeholder="Например: Читать книгу"
                          className="w-full px-4 py-4 rounded-2xl bg-black/50 border border-white/10 text-white placeholder-gray-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all text-[16px]"
                          autoFocus
                      />
                    </div>

                    <div>
                      <label className="text-xs text-gray-400 uppercase tracking-wider font-medium mb-2 block">
                        Тип выполнения
                      </label>
                      <div className="flex gap-2">
                        <button
                            onClick={() => setNewHabit({...newHabit, type: 'single', target: 1})}
                            className={`flex-1 py-3 rounded-2xl text-sm font-medium transition-all border ${
                                newHabit.type === 'single'
                                    ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-400'
                                    : 'bg-black/50 border-white/5 text-gray-400 hover:bg-white/5'
                            }`}
                        >
                          Один раз
                        </button>
                        <button
                            onClick={() => setNewHabit({...newHabit, type: 'multiple', target: 3})}
                            className={`flex-1 py-3 rounded-2xl text-sm font-medium transition-all border ${
                                newHabit.type === 'multiple'
                                    ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-400'
                                    : 'bg-black/50 border-white/5 text-gray-400 hover:bg-white/5'
                            }`}
                        >
                          Несколько раз
                        </button>
                      </div>
                    </div>

                    {newHabit.type === 'multiple' && (
                        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}>
                          <label className="text-xs text-gray-400 uppercase tracking-wider font-medium mb-2 mt-2 block">
                            Сколько раз в день?
                          </label>
                          <div className="flex items-center gap-3">
                            <input
                                type="number"
                                min="2"
                                max="100"
                                value={newHabit.target}
                                onChange={(e) => setNewHabit({ ...newHabit, target: parseInt(e.target.value) || 2 })}
                                onKeyDown={handleKeyDown}
                                className="w-24 px-4 py-3 text-center rounded-2xl bg-black/50 border border-white/10 text-white focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all text-[16px]"
                            />
                            <span className="text-gray-500 text-sm">раз(а)</span>
                          </div>
                        </motion.div>
                    )}

                    <div>
                      <label className="text-xs text-gray-400 uppercase tracking-wider font-medium mb-2 block">
                        Описание (необязательно)
                      </label>
                      <input
                          type="text"
                          value={newHabit.sub}
                          onChange={(e) => setNewHabit({ ...newHabit, sub: e.target.value })}
                          onKeyDown={handleKeyDown}
                          placeholder={newHabit.type === 'multiple' ? `Например: по стакану воды` : "Например: 30 минут"}
                          className="w-full px-4 py-4 rounded-2xl bg-black/50 border border-white/10 text-white placeholder-gray-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all text-[16px]"
                      />
                    </div>

                    <div>
                      <label className="text-xs text-gray-400 uppercase tracking-wider font-medium mb-3 block">
                        Цвет
                      </label>
                      <div className="flex gap-4 flex-wrap">
                        {colors.map(c => (
                            <button
                                key={c}
                                onClick={() => setNewHabit({ ...newHabit, color: c })}
                                className={`w-10 h-10 rounded-full transition-all ${
                                    newHabit.color === c
                                        ? 'scale-125 ring-2 ring-white ring-offset-2 ring-offset-[#141418]'
                                        : 'hover:scale-110 opacity-70'
                                }`}
                                style={{ backgroundColor: c }}
                            />
                        ))}
                      </div>
                    </div>

                    <motion.button
                        whileTap={{ scale: 0.97 }}
                        onClick={addHabit}
                        disabled={!newHabit.title.trim()}
                        className="w-full py-4 rounded-2xl font-bold text-base transition-all disabled:opacity-30 disabled:cursor-not-allowed bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/30 mt-6"
                    >
                      Добавить привычку
                    </motion.button>
                  </div>
                </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* НИЖНЯЯ ПАНЕЛЬ НАВИГАЦИИ (Скрывается при добавлении, чтобы не мешать клавиатуре) */}
        {activePage !== 'add' && (
            <motion.div
                initial={{ y: 100, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2, type: 'spring', damping: 25 }}
                className="fixed bottom-6 left-1/2 -translate-x-1/2 w-[calc(100%-32px)] max-w-[440px] z-40"
            >
              <div className="h-16 bg-[#1a1a20]/90 backdrop-blur-2xl rounded-2xl border border-white/10 flex items-center justify-around px-4 shadow-2xl shadow-black/50">

                <button
                    onClick={() => {
                      if (activePage !== 'quotes') {
                        setCurrentQuote(quotes[Math.floor(Math.random() * quotes.length)]);
                      }
                      setActivePage('quotes');
                    }}
                    className={`flex flex-col items-center gap-1 px-4 py-1 rounded-xl transition-all ${
                        activePage === 'quotes' ? 'text-yellow-400' : 'text-gray-500 hover:text-gray-300'
                    }`}
                >
                  <Sparkles size={20} />
                  <span className="text-[9px] uppercase tracking-wider font-medium">Цитаты</span>
                </button>

                <motion.button
                    whileTap={{ scale: 0.9 }}
                    onClick={() => activePage === 'home' ? setActivePage('add') : setActivePage('home')}
                    className={`w-14 h-14 rounded-2xl flex items-center justify-center -mt-6 shadow-lg border-4 border-[#0a0a0f] transition-all ${
                        activePage === 'home'
                            ? 'bg-gradient-to-br from-cyan-400 to-blue-500 shadow-cyan-500/30 hover:shadow-cyan-500/50'
                            : 'bg-[#2a2a35] text-gray-400 border-[#0a0a0f]'
                    }`}
                >
                  {activePage === 'home' ? (
                      <Plus size={24} className="text-white" strokeWidth={2.5} />
                  ) : (
                      <Home size={22} strokeWidth={2.5} />
                  )}
                </motion.button>

                <button
                    onClick={() => setActivePage('profile')}
                    className={`flex flex-col items-center gap-1 px-4 py-1 rounded-xl transition-all ${
                        activePage === 'profile' ? 'text-cyan-400' : 'text-gray-500 hover:text-gray-300'
                    }`}
                >
                  <User size={20} />
                  <span className="text-[9px] uppercase tracking-wider font-medium">Профиль</span>
                </button>

              </div>
            </motion.div>
        )}
      </div>
  );
}