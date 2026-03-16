import { useState, useRef, useEffect } from 'react';
import { Button, Input, Spin, Tag, Typography } from 'antd';
import { SendOutlined, ClearOutlined, RobotOutlined } from '@ant-design/icons';
import { useChatStore } from '../store';
import { streamChat } from '../services/api';
import type { ChatMessage } from '../types';

const { Text } = Typography;
const { TextArea } = Input;

export default function AIAssistant() {
  const [input, setInput] = useState('');
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const {
    messages,
    isStreaming,
    moduleContext,
    addMessage,
    appendToLastAssistant,
    setStreaming,
    clearMessages,
  } = useChatStore();

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const send = () => {
    if (!input.trim() || isStreaming) return;
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };
    addMessage(userMsg);

    const assistantMsg: ChatMessage = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      toolCalls: [],
    };
    addMessage(assistantMsg);
    setStreaming(true);

    const history = messages
      .filter((m) => m.role === 'user' || m.role === 'assistant')
      .map((m) => ({ role: m.role, content: m.content }));

    abortRef.current = streamChat(
      input.trim(),
      moduleContext,
      history,
      (chunk: unknown) => {
        const c = chunk as { type: string; content?: string; tool?: string };
        if (c.type === 'text' && c.content) {
          appendToLastAssistant(c.content);
        } else if (c.type === 'error' && c.content) {
          appendToLastAssistant('⚠️ ' + c.content);
        }
      },
      () => setStreaming(false),
      () => setStreaming(false)
    );
    setInput('');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: 16 }}>
      {/* Header */}
      <div style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
        <RobotOutlined style={{ fontSize: 18, color: '#1677ff' }} />
        <Text strong>AI 财务助理</Text>
        {moduleContext && <Tag color="blue">{moduleContext}</Tag>}
        <Button
          size="small"
          icon={<ClearOutlined />}
          onClick={clearMessages}
          style={{ marginLeft: 'auto' }}
        >
          清空
        </Button>
      </div>

      {/* Message list */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
          marginBottom: 12,
        }}
      >
        {messages.length === 0 && (
          <Text type="secondary" style={{ textAlign: 'center', marginTop: 40 }}>
            请输入问题，AI助理将为您提供专业财务建议
          </Text>
        )}
        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '85%',
              background: msg.role === 'user' ? '#1677ff' : '#f0f0f0',
              color: msg.role === 'user' ? '#fff' : '#000',
              borderRadius: 8,
              padding: '8px 12px',
              fontSize: 13,
              whiteSpace: 'pre-wrap',
            }}
          >
            {msg.content || (msg.role === 'assistant' && isStreaming ? (
              <Spin size="small" />
            ) : null)}
          </div>
        ))}
      </div>

      {/* Input area */}
      <div style={{ display: 'flex', gap: 8 }}>
        <TextArea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="输入问题…"
          autoSize={{ minRows: 1, maxRows: 4 }}
          onPressEnter={(e) => {
            if (!e.shiftKey) { e.preventDefault(); send(); }
          }}
          disabled={isStreaming}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={send}
          disabled={isStreaming || !input.trim()}
        />
      </div>
    </div>
  );
}
