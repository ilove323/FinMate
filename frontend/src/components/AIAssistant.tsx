import { useState, useRef, useEffect } from 'react';
import { Button, Input, Space, Spin, Tag, Typography } from 'antd';
import { SendOutlined, ClearOutlined, RobotOutlined } from '@ant-design/icons';
import { useChatStore, usePeriodStore } from '../store';
import { streamChat } from '../services/api';
import type { ActionButton, ChatMessage } from '../types';

const { Text } = Typography;
const { TextArea } = Input;

const PROACTIVE_MESSAGES: Record<string, string> = {
  reconciliation: '请简要告知当前期间银行对账状态（匹配率、未匹配数量），并建议下一步操作。',
  tax: '请简要告知当前期间税务数据状态（预估税额、合规性），并建议下一步操作。',
  reports: '请简要告知当前期间财务报表核心指标（资产总额、净利润），并建议下一步操作。',
  cost_alloc: '请简要告知当前期间成本分摊状态（总待分摊金额、已分摊进度），并建议下一步操作。',
};

function getModuleActions(module: string, period: string): ActionButton[] {
  switch (module) {
    case 'reconciliation':
      return [{ label: '🤖 模拟自动对账', message: `请帮我对 ${period} 的银行流水执行自动对账，先给我模拟预览` }];
    case 'tax':
      return [
        { label: '🤖 模拟生成增值税申报表', message: `请帮我生成 ${period} 增值税（vat_general）申报表，先给我模拟预览` },
        { label: '🤖 模拟生成企业所得税申报表', message: `请帮我生成 ${period} 企业所得税（cit_quarterly）申报表，先给我模拟预览` },
      ];
    case 'cost_alloc':
      return [{ label: '🤖 模拟执行成本分摊', message: `请帮我计算 ${period} 的成本分摊，先给我模拟预览` }];
    default:
      return [];
  }
}

export default function AIAssistant() {
  const [input, setInput] = useState('');
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const prevModuleRef = useRef<string | null>(null);

  const {
    messages,
    isStreaming,
    moduleContext,
    addMessage,
    appendToLastAssistant,
    setStreaming,
    clearMessages,
    setRefreshTrigger,
    addActionsToLastMessage,
  } = useChatStore();

  const { period } = usePeriodStore();

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  // Proactive greeting on module switch
  useEffect(() => {
    if (moduleContext && moduleContext !== prevModuleRef.current) {
      prevModuleRef.current = moduleContext;
      sendGreeting(moduleContext);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [moduleContext]);

  const sendGreeting = (ctx: string) => {
    const greetingText = PROACTIVE_MESSAGES[ctx];
    if (!greetingText) return;

    const assistantMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isProactive: true,
    };
    addMessage(assistantMsg);
    setStreaming(true);

    const history = useChatStore.getState().messages
      .filter((m) => m.role === 'user' || m.role === 'assistant')
      .map((m) => ({ role: m.role, content: m.content }));

    abortRef.current = streamChat(
      greetingText,
      ctx,
      history,
      (chunk: unknown) => {
        const c = chunk as { type: string; content?: string; module?: string };
        if (c.type === 'text' && c.content) appendToLastAssistant(c.content);
        if (c.type === 'page_refresh' && c.module) setRefreshTrigger({ module: c.module, ts: Date.now() });
      },
      () => {
        setStreaming(false);
        addActionsToLastMessage(getModuleActions(ctx, usePeriodStore.getState().period));
      },
      () => setStreaming(false)
    );
  };

  const sendMessage = (text: string) => {
    if (!text.trim() || isStreaming) return;
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text.trim(),
      timestamp: new Date(),
    };
    addMessage(userMsg);

    const assistantMsg: ChatMessage = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };
    addMessage(assistantMsg);
    setStreaming(true);

    const history = useChatStore.getState().messages
      .filter((m) => m.role === 'user' || m.role === 'assistant')
      .map((m) => ({ role: m.role, content: m.content }));

    abortRef.current = streamChat(
      text.trim(),
      moduleContext,
      history,
      (chunk: unknown) => {
        const c = chunk as { type: string; content?: string; module?: string };
        if (c.type === 'text' && c.content) appendToLastAssistant(c.content);
        if (c.type === 'error' && c.content) appendToLastAssistant('⚠️ ' + c.content);
        if (c.type === 'page_refresh' && c.module) setRefreshTrigger({ module: c.module, ts: Date.now() });
      },
      () => setStreaming(false),
      () => setStreaming(false)
    );
  };

  const send = () => {
    sendMessage(input.trim());
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
            {msg.actions && msg.actions.length > 0 && (
              <Space style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap' }}>
                {msg.actions.map((action: ActionButton, i: number) => (
                  <Button
                    key={i}
                    size="small"
                    type="primary"
                    ghost
                    style={{ borderColor: '#1677ff', color: '#1677ff' }}
                    onClick={() => sendMessage(action.message)}
                  >
                    {action.label}
                  </Button>
                ))}
              </Space>
            )}
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
