import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Sparkles, Copy, Instagram, MessageCircle, Store, TrendingUp,
  CheckCircle2, Moon, Sun, CalendarDays, Zap
} from 'lucide-react';
import './index.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ===== Types =====
interface GenerateResponse {
  threads_post: string;
  instagram_post: string;
  danggeun_post: string;
  trends_used: string[];
}

interface CalendarDay {
  day: string;
  threads: string;
  instagram: string;
  danggeun: string;
}

interface CalendarResponse {
  calendar: CalendarDay[];
  trends_used: string[];
}

// ===== Skeleton Loading Component =====
function SkeletonCards() {
  return (
    <>
      {[1, 2, 3].map((i) => (
        <div className="skeleton-card" key={i}>
          <div className="skeleton-header">
            <div className="skeleton-circle" />
            <div className="skeleton-line" style={{ width: '45%' }} />
          </div>
          <div className="skeleton-body">
            <div className="skeleton-line" style={{ width: '95%' }} />
            <div className="skeleton-line" style={{ width: '80%' }} />
            <div className="skeleton-line" style={{ width: '88%' }} />
            <div className="skeleton-line" style={{ width: '60%' }} />
          </div>
        </div>
      ))}
    </>
  );
}

// ===== Channel Card Component =====
function ChannelCard({
  icon, label, text, channel, copiedChannel, onCopy
}: {
  icon: React.ReactNode;
  label: string;
  text: string;
  channel: string;
  copiedChannel: string | null;
  onCopy: (text: string, channel: string) => void;
}) {
  const isCopied = copiedChannel === channel;
  return (
    <div className="channel-card card-animate">
      <div className="channel-header">
        <div className="channel-title">{icon}{label}</div>
        <button
          className={`copy-btn ${isCopied ? 'copied' : ''}`}
          onClick={() => onCopy(text, channel)}
        >
          {isCopied ? <CheckCircle2 size={14} /> : <Copy size={14} />}
          {isCopied ? '복사됨!' : '복사'}
        </button>
      </div>
      <div className="channel-content">{text}</div>
    </div>
  );
}

// ===== Main App =====
function App() {
  const [dailyNote, setDailyNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copiedChannel, setCopiedChannel] = useState<string | null>(null);

  // Dark mode
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('bakery-theme');
    return saved === 'dark';
  });

  // Tabs: 'generate' | 'calendar'
  const [activeTab, setActiveTab] = useState<'generate' | 'calendar'>('generate');

  // Calendar
  const [calendarNote, setCalendarNote] = useState('');
  const [calendarLoading, setCalendarLoading] = useState(false);
  const [calendarResult, setCalendarResult] = useState<CalendarResponse | null>(null);
  const [calendarError, setCalendarError] = useState<string | null>(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    localStorage.setItem('bakery-theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  // ===== Handlers =====
  const handleGenerate = async () => {
    if (!dailyNote.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/generate`, { daily_note: dailyNote });
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || '게시물 생성 중 오류가 발생했습니다. 백엔드 서버가 켜져 있는지 확인해주세요.');
    } finally {
      setLoading(false);
    }
  };

  const handleCalendarGenerate = async () => {
    if (!calendarNote.trim()) return;
    setCalendarLoading(true);
    setCalendarError(null);
    setCalendarResult(null);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/calendar`, { weekly_note: calendarNote });
      setCalendarResult(response.data);
    } catch (err: any) {
      setCalendarError(err.response?.data?.detail || '캘린더 생성 중 오류가 발생했습니다.');
    } finally {
      setCalendarLoading(false);
    }
  };

  const handleCopy = (text: string, channel: string) => {
    navigator.clipboard.writeText(text);
    setCopiedChannel(channel);
    setTimeout(() => setCopiedChannel(null), 2000);
  };

  const DAY_EMOJIS: Record<string, string> = {
    '월요일': '🌙', '화요일': '🔥', '수요일': '💧',
    '목요일': '🪵', '금요일': '💰', '토요일': '🌤️', '일요일': '☀️'
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>🥐 베이커리란 AI 매니저</h1>
        <p>오늘의 소식 한 줄로, 3개 채널 SNS 글을 순식간에 뚝딱!</p>
        <button className="theme-toggle" onClick={() => setIsDark(!isDark)} title="다크모드 전환">
          {isDark ? <Sun size={20} /> : <Moon size={20} />}
        </button>
      </header>

      {/* Tab Navigation */}
      <nav className="tab-nav">
        <button className={`tab-btn ${activeTab === 'generate' ? 'active' : ''}`} onClick={() => setActiveTab('generate')}>
          <Zap size={16} /> SNS 글 생성
        </button>
        <button className={`tab-btn ${activeTab === 'calendar' ? 'active' : ''}`} onClick={() => setActiveTab('calendar')}>
          <CalendarDays size={16} /> 주간 캘린더
        </button>
      </nav>

      {/* ===== TAB 1: SNS 글 생성 ===== */}
      {activeTab === 'generate' && (
        <main className="main-content">
          <section className="input-section">
            <div className="input-group">
              <label htmlFor="dailyNote">사장님의 오늘 하루 📝</label>
              <p className="help-text">예: 구름이 뭉게뭉게 너무 예쁜 오후. 갓 구운 소금빵 냄새가 가게에 가득하다!</p>
              <textarea
                id="dailyNote"
                value={dailyNote}
                onChange={(e) => setDailyNote(e.target.value)}
                placeholder="오늘 어떤 특별한 일이 있었나요? 빵 자랑, 일상 등 자유롭게 적어주세요!"
              />
            </div>

            {error && <div className="error-message">{error}</div>}

            <button
              className={`generate-btn ${loading ? 'loading' : ''}`}
              onClick={handleGenerate}
              disabled={loading || !dailyNote.trim()}
            >
              {loading ? (
                <>
                  <Sparkles className="animate-spin" size={18} />
                  원기옥 모으는 중... (트렌드 분석 &amp; 글 작성)
                </>
              ) : (
                <>
                  <Sparkles size={18} />
                  SNS 초안 동시 생성하기
                </>
              )}
            </button>
          </section>

          <section className="results-section">
            {!result && !loading && (
              <div className="empty-state">
                <Sparkles size={48} style={{ opacity: 0.15 }} />
                <h3>아직 작성된 초안이 없어요</h3>
                <p>좌측에 오늘 하루를 적고 생성 버튼을 눌러보세요!</p>
              </div>
            )}

            {loading && <SkeletonCards />}

            {result && (
              <>
                {result.trends_used?.length > 0 && (
                  <div className="trends-banner card-animate">
                    <TrendingUp size={18} color="var(--primary)" />
                    <div>
                      <span>오늘의 트렌드:</span>
                      {result.trends_used.map((t, i) => (
                        <span className="trend-tag" key={i}>{t}</span>
                      ))}
                    </div>
                  </div>
                )}

                <ChannelCard
                  icon={<MessageCircle size={18} />}
                  label="스레드 (Threads)"
                  text={result.threads_post}
                  channel="threads"
                  copiedChannel={copiedChannel}
                  onCopy={handleCopy}
                />
                <ChannelCard
                  icon={<Instagram size={18} color="#E1306C" />}
                  label="인스타그램 (Instagram)"
                  text={result.instagram_post}
                  channel="insta"
                  copiedChannel={copiedChannel}
                  onCopy={handleCopy}
                />
                <ChannelCard
                  icon={<Store size={18} color="#FF7E36" />}
                  label="당근마켓 (비즈프로필)"
                  text={result.danggeun_post}
                  channel="danggeun"
                  copiedChannel={copiedChannel}
                  onCopy={handleCopy}
                />
              </>
            )}
          </section>
        </main>
      )}

      {/* ===== TAB 2: 주간 캘린더 ===== */}
      {activeTab === 'calendar' && (
        <div>
          <section className="calendar-input-section">
            <div className="input-group">
              <label htmlFor="calendarNote">이번 주 특이사항 📅</label>
              <p className="help-text">예: 수요일 신메뉴(말차 소금빵) 출시, 토요일 관광객 많을 예정, 금요일 휴무</p>
              <textarea
                id="calendarNote"
                value={calendarNote}
                onChange={(e) => setCalendarNote(e.target.value)}
                placeholder="이번 주에 특별한 이벤트나 계획이 있나요?"
              />
            </div>

            {calendarError && <div className="error-message">{calendarError}</div>}

            <button
              className={`generate-btn ${calendarLoading ? 'loading' : ''}`}
              onClick={handleCalendarGenerate}
              disabled={calendarLoading || !calendarNote.trim()}
            >
              {calendarLoading ? (
                <>
                  <CalendarDays className="animate-spin" size={18} />
                  주간 캘린더 생성 중...
                </>
              ) : (
                <>
                  <CalendarDays size={18} />
                  주간 콘텐츠 캘린더 생성
                </>
              )}
            </button>
          </section>

          {calendarLoading && (
            <div className="calendar-grid">
              {[1, 2, 3, 4, 5, 6, 7].map((i) => (
                <div className="skeleton-card" key={i}>
                  <div className="skeleton-header">
                    <div className="skeleton-line" style={{ width: '35%' }} />
                  </div>
                  <div className="skeleton-body">
                    <div className="skeleton-line" style={{ width: '90%' }} />
                    <div className="skeleton-line" style={{ width: '75%' }} />
                    <div className="skeleton-line" style={{ width: '85%' }} />
                  </div>
                </div>
              ))}
            </div>
          )}

          {calendarResult && (
            <>
              {calendarResult.trends_used?.length > 0 && (
                <div className="trends-banner card-animate" style={{ maxWidth: 700, margin: '1.5rem auto 0' }}>
                  <TrendingUp size={18} color="var(--primary)" />
                  <div>
                    <span>이번 주 트렌드:</span>
                    {calendarResult.trends_used.map((t, i) => (
                      <span className="trend-tag" key={i}>{t}</span>
                    ))}
                  </div>
                </div>
              )}
              <div className="calendar-grid">
                {calendarResult.calendar.map((day, i) => (
                  <div className="calendar-day-card" key={i}>
                    <div className="calendar-day-header">
                      {DAY_EMOJIS[day.day] || '📌'} {day.day}
                    </div>
                    <div className="calendar-day-body">
                      <div className="calendar-channel">
                        <div className="calendar-channel-label">🧵 스레드</div>
                        <div className="calendar-channel-text">{day.threads}</div>
                      </div>
                      <div className="calendar-channel">
                        <div className="calendar-channel-label">📸 인스타</div>
                        <div className="calendar-channel-text">{day.instagram}</div>
                      </div>
                      <div className="calendar-channel">
                        <div className="calendar-channel-label">🥕 당근</div>
                        <div className="calendar-channel-text">{day.danggeun}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
