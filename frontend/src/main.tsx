import React, { useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Bot,
  CheckCircle2,
  Globe2,
  Loader2,
  MessageSquare,
  PanelLeft,
  Plus,
  Search,
  Send,
  Sparkles,
  UserRound
} from 'lucide-react';
import './styles.css';

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api/v1';
const REQUEST_TIMEOUT_MS = 20000;

type ChatResponse = {
  answer: string;
  confidence_score: number;
  sources: Array<{ url: string; title?: string; confidence_score: number }>;
};

type Message = {
  id: string;
  role: 'assistant' | 'user';
  content: string;
  confidence?: number;
  sources?: ChatResponse['sources'];
};

type Conversation = {
  id: string;
  title: string;
  messages: Message[];
  updatedAt: number;
};

const starterPrompts = [
  'Which companies manufacture 5G antenna modules?',
  'Find Open RAN radio unit suppliers',
  'Compare Massive MIMO vendors',
  'What is Switzerland doing in 5G and Open RAN?'
];

function initialMessage(): Message {
  return {
    id: crypto.randomUUID(),
    role: 'assistant',
    content:
      'Hi, I am Wireless IQ. Ask a market, vendor, component, Open RAN, 5G, 6G, or telecom research question. I will search sources and answer with citations.'
  };
}

function newConversation(): Conversation {
  return {
    id: crypto.randomUUID(),
    title: 'New chat',
    messages: [initialMessage()],
    updatedAt: Date.now()
  };
}

function App() {
  const [conversations, setConversations] = useState<Conversation[]>([newConversation()]);
  const [activeConversationId, setActiveConversationId] = useState(() => conversations[0].id);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('Ready');
  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  const activeConversation = conversations.find((conversation) => conversation.id === activeConversationId) ?? conversations[0];
  const messages = activeConversation.messages;

  const latestSources = useMemo(() => {
    const sources = messages.flatMap((message) => message.sources ?? []);
    const seen = new Set<string>();
    return sources.filter((source) => {
      if (seen.has(source.url)) return false;
      seen.add(source.url);
      return true;
    }).slice(0, 5);
  }, [messages]);

  function updateActiveConversation(updater: (conversation: Conversation) => Conversation) {
    setConversations((current) =>
      current.map((conversation) => (conversation.id === activeConversationId ? updater(conversation) : conversation))
    );
  }

  function startNewChat() {
    const conversation = newConversation();
    setConversations((current) => [conversation, ...current]);
    setActiveConversationId(conversation.id);
    setInput('');
    requestAnimationFrame(() => inputRef.current?.focus());
  }

  async function submit(value = input) {
    const question = value.trim();
    if (!question || loading) return;

    setInput('');
    setLoading(true);
    setStatus('Searching sources');
    updateActiveConversation((conversation) => ({
      ...conversation,
      title: conversation.title === 'New chat' ? question.slice(0, 52) : conversation.title,
      updatedAt: Date.now(),
      messages: [...conversation.messages, { id: crypto.randomUUID(), role: 'user', content: question }]
    }));

    try {
      await fetchWithTimeout(`${API_BASE}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: question, max_results: 8, persist: true })
      });

      setStatus('Writing answer');
      const response = await fetchWithTimeout(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, top_k: 6 })
      }, 30000);
      if (!response.ok) throw new Error('Chat request failed');
      const payload = (await response.json()) as ChatResponse;
      updateActiveConversation((conversation) => ({
        ...conversation,
        updatedAt: Date.now(),
        messages: [
          ...conversation.messages,
          {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: payload.answer,
            confidence: payload.confidence_score,
            sources: payload.sources
          }
        ]
      }));
      setStatus('Ready');
    } catch {
      updateActiveConversation((conversation) => ({
        ...conversation,
        updatedAt: Date.now(),
        messages: [
          ...conversation.messages,
          {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: 'I could not reach the knowledge API. Please check backend status and try again.'
          }
        ]
      }));
      setStatus('API unavailable');
    } finally {
      setLoading(false);
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }

  return (
    <main className="chat-shell">
      <aside className="history-sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Sparkles size={18} />
          </div>
          <div>
            <strong>Wireless IQ</strong>
            <span>Source-backed telecom intelligence</span>
          </div>
        </div>

        <button className="new-chat-button" onClick={startNewChat}>
          <Plus size={16} />
          New chat
        </button>

        <div className="history-section">
          <span className="history-label">History</span>
          <div className="history-list">
            {conversations.map((conversation) => (
              <button
                className={`history-item ${conversation.id === activeConversationId ? 'active' : ''}`}
                key={conversation.id}
                onClick={() => setActiveConversationId(conversation.id)}
              >
                <MessageSquare size={15} />
                <span>{conversation.title}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="sidebar-footer">
          <PanelLeft size={15} />
          <span>{conversations.length} chat{conversations.length === 1 ? '' : 's'}</span>
        </div>
      </aside>

      <section className="chat-main">
        <header className="chat-header">
          <div>
            <strong>{activeConversation.title}</strong>
            <span>Wireless communication assistant</span>
          </div>
          <div className={`status ${status === 'Ready' ? 'ready' : ''}`}>
            {loading ? <Loader2 size={15} className="spin" /> : <CheckCircle2 size={15} />}
            <span>{status}</span>
          </div>
        </header>

        <section className="chat-body">
          {messages.map((message) => (
            <article className={`message ${message.role}`} key={message.id}>
              <div className="avatar">{message.role === 'assistant' ? <Bot size={18} /> : <UserRound size={18} />}</div>
              <div className="bubble">
                <div className="message-text">{message.content}</div>
                {message.role === 'assistant' && message.sources?.length ? (
                  <div className="source-list">
                    <div className="source-title">
                      <Globe2 size={14} />
                      Sources
                      {typeof message.confidence === 'number' ? <em>{Math.round(message.confidence * 100)}%</em> : null}
                    </div>
                    {message.sources.slice(0, 6).map((source) => (
                      <a href={source.url} target="_blank" rel="noreferrer" key={source.url}>
                        <span>{source.title || hostname(source.url)}</span>
                        <small>{hostname(source.url)}</small>
                      </a>
                    ))}
                  </div>
                ) : null}
              </div>
            </article>
          ))}

          {loading ? (
            <article className="message assistant">
              <div className="avatar"><Bot size={18} /></div>
              <div className="bubble typing">
                <span />
                <span />
                <span />
              </div>
            </article>
          ) : null}
        </section>

        <footer className="composer-wrap">
          {messages.length <= 1 ? (
            <div className="starter-grid">
              {starterPrompts.map((prompt) => (
                <button key={prompt} onClick={() => submit(prompt)}>
                  <Search size={14} />
                  {prompt}
                </button>
              ))}
            </div>
          ) : null}

          {latestSources.length ? (
            <div className="recent-sources">
              {latestSources.slice(0, 3).map((source) => (
                <a href={source.url} target="_blank" rel="noreferrer" key={source.url}>
                  {hostname(source.url)}
                </a>
              ))}
            </div>
          ) : null}

          <form
            className="composer"
            onSubmit={(event) => {
              event.preventDefault();
              submit();
            }}
          >
            <button type="button" className="icon-button" aria-label="New chat" onClick={startNewChat}>
              <Plus size={18} />
            </button>
            <textarea
              ref={inputRef}
              value={input}
              placeholder="Ask anything about wireless communication..."
              rows={1}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  submit();
                }
              }}
            />
            <button className="send-button" disabled={!input.trim() || loading} type="submit" aria-label="Send message">
              {loading ? <Loader2 size={18} className="spin" /> : <Send size={18} />}
            </button>
          </form>
        </footer>
      </section>
    </main>
  );
}

function hostname(url: string) {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return url;
  }
}

async function fetchWithTimeout(input: RequestInfo | URL, init: RequestInit = {}, timeoutMs = REQUEST_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } finally {
    window.clearTimeout(timeout);
  }
}

createRoot(document.getElementById('root')!).render(<App />);
