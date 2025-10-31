import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import useFeatureAccess from '@/hooks/useFeatureAccess';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { sendAIMessage, getAIUsage } from '@/api';
import { X, Send, Loader2, Bot, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

const AIAssistant = ({ onClose }) => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const { currentPlan } = useFeatureAccess();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [model, setModel] = useState('gpt-4o');
  const [provider, setProvider] = useState('openai');
  const [sessionId] = useState(() => Math.random().toString(36).substring(7));
  const [usage, setUsage] = useState({ used: 0, limit: 0, remaining: 0 });
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch AI usage on mount
  useEffect(() => {
    fetchUsage();
  }, []);

  const fetchUsage = async () => {
    try {
      const response = await getAIUsage();
      setUsage(response.data);
    } catch (error) {
      console.error('Error fetching AI usage:', error);
    }
  };

  const models = {
    openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-5'],
    anthropic: ['claude-3-7-sonnet-20250219', 'claude-4-sonnet-20250514'],
    gemini: ['gemini-2.0-flash', 'gemini-2.5-pro']
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    // Check if limit reached
    if (usage.limit !== -1 && usage.remaining <= 0) {
      toast.error('Limite d\'utilisation atteinte. Passez au plan BUSINESS pour un accès illimité.');
      return;
    }

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await sendAIMessage(input, model, provider, sessionId);
      const assistantMessage = { role: 'assistant', content: response.data.response };
      setMessages(prev => [...prev, assistantMessage]);
      
      // Update usage
      setUsage({
        used: response.data.usage_count,
        limit: response.data.limit,
        remaining: response.data.remaining
      });
    } catch (error) {
      console.error('AI error:', error);
      const errorMsg = error.response?.data?.detail || 'Erreur lors de la communication avec l\'assistant IA';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      data-testid="ai-assistant-modal"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-red-500 to-orange-500 rounded-t-2xl">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center">
              <Bot className="w-6 h-6 text-red-500" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white" style={{ fontFamily: 'EB Garamond, serif' }}>
                {t('aiAssistant')}
              </h2>
              <p className="text-xs text-red-100">Beyond Express AI</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="text-white hover:bg-white/20"
            data-testid="ai-close-button"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Model Selector */}
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="flex gap-3">
            <div className="flex-1">
              <Select value={provider} onValueChange={setProvider}>
                <SelectTrigger className="h-10" data-testid="provider-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="openai">OpenAI</SelectItem>
                  <SelectItem value="anthropic">Anthropic</SelectItem>
                  <SelectItem value="gemini">Gemini</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1">
              <Select value={model} onValueChange={setModel}>
                <SelectTrigger className="h-10" data-testid="model-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {models[provider].map(m => (
                    <SelectItem key={m} value={m}>{m}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4" style={{ minHeight: '400px' }}>
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <Bot className="w-16 h-16 text-gray-300 mb-4" />
              <p className="text-gray-500 mb-2">Comment puis-je vous aider aujourd'hui?</p>
              <p className="text-sm text-gray-400">Posez des questions sur vos commandes, stock, livraisons...</p>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                data-testid={`message-${index}`}
              >
                <div
                  className={`max-w-[80%] p-3 rounded-2xl ${
                    msg.role === 'user'
                      ? 'bg-red-500 text-white rounded-br-none'
                      : 'bg-gray-100 text-gray-900 rounded-bl-none'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 p-3 rounded-2xl rounded-bl-none">
                <Loader2 className="w-5 h-5 animate-spin text-gray-500" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={t('typeMessage')}
              className="flex-1"
              disabled={loading}
              data-testid="ai-input"
            />
            <Button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="bg-red-500 hover:bg-red-600"
              data-testid="ai-send-button"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIAssistant;