import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Clock, CheckCircle, AlertCircle } from 'lucide-react';

const ChatInterface = ({ conversation, messages, onSendMessage, onTakeOver, loading }) => {
  const [newMessage, setNewMessage] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!newMessage.trim() || sending) return;
    
    setSending(true);
    try {
      await onSendMessage(newMessage);
      setNewMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setSending(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (timestamp) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      return '';
    }
  };

  const getStatusIcon = (status) => {
    const icons = {
      sent: <CheckCircle className="w-3 h-3 text-gray-400" />,
      delivered: <CheckCircle className="w-3 h-3 text-blue-500" />,
      read: <CheckCircle className="w-3 h-3 text-green-500" />,
      failed: <AlertCircle className="w-3 h-3 text-red-500" />
    };
    return icons[status] || icons.sent;
  };

  if (!conversation) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-gray-50 text-gray-500">
        <Bot className="w-20 h-20 mb-4 text-gray-300" />
        <p className="text-lg font-medium">Sélectionnez une conversation</p>
        <p className="text-sm text-gray-400 mt-2">Choisissez une conversation pour commencer</p>
      </div>
    );
  }

  const isAIHandling = conversation.status === 'ai_handling';
  const isWaiting = conversation.status === 'waiting';

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-gradient-to-r from-red-500 to-orange-500 text-white">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center font-bold">
            {conversation.customer_name ? conversation.customer_name.charAt(0).toUpperCase() : '👤'}
          </div>
          <div>
            <div className="font-semibold">
              {conversation.customer_name || conversation.customer_phone}
            </div>
            <div className="text-xs text-white/80 flex items-center gap-2">
              {isAIHandling && (
                <>
                  <Bot className="w-3 h-3" />
                  <span>Géré par IA</span>
                </>
              )}
              {isWaiting && (
                <>
                  <Clock className="w-3 h-3" />
                  <span>En attente d'un agent</span>
                </>
              )}
              {conversation.status === 'human_handling' && (
                <>
                  <User className="w-3 h-3" />
                  <span>Agent humain</span>
                </>
              )}
            </div>
          </div>
        </div>
        
        {isAIHandling || isWaiting ? (
          <button
            onClick={onTakeOver}
            className="px-4 py-2 bg-white text-red-600 rounded-lg font-medium hover:bg-gray-100 transition-colors flex items-center gap-2"
          >
            <User className="w-4 h-4" />
            Prendre le relais
          </button>
        ) : (
          <div className="px-4 py-2 bg-white/20 rounded-lg text-sm">
            Vous gérez cette conversation
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p>Aucun message dans cette conversation</p>
          </div>
        ) : (
          messages.map((msg, index) => {
            const isOutbound = msg.direction === 'outbound';
            
            return (
              <div
                key={msg.message_sid || index}
                className={`flex ${isOutbound ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-[70%] ${isOutbound ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
                  <div
                    className={`
                      rounded-2xl px-4 py-2 shadow-sm
                      ${isOutbound
                        ? 'bg-gradient-to-r from-red-500 to-orange-500 text-white rounded-br-none'
                        : 'bg-white text-gray-900 border border-gray-200 rounded-bl-none'
                      }
                    `}
                  >
                    <p className="text-sm whitespace-pre-wrap break-words">{msg.body}</p>
                  </div>
                  
                  <div className={`flex items-center gap-1 text-xs text-gray-500 px-2`}>
                    <span>{formatTime(msg.timestamp)}</span>
                    {isOutbound && getStatusIcon(msg.status)}
                  </div>
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t bg-white">
        <div className="flex items-end gap-2">
          <textarea
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Tapez votre message..."
            rows={3}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
            disabled={sending}
          />
          <button
            onClick={handleSend}
            disabled={!newMessage.trim() || sending}
            className={`
              p-3 rounded-xl font-medium transition-all flex items-center justify-center
              ${!newMessage.trim() || sending
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-red-500 to-orange-500 text-white hover:shadow-lg transform hover:-translate-y-0.5'
              }
            `}
          >
            {sending ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
        
        {isAIHandling && (
          <div className="mt-2 text-xs text-gray-500 flex items-center gap-1">
            <Bot className="w-3 h-3" />
            <span>Cette conversation est gérée par l'IA. Prenez le relais pour envoyer des messages manuellement.</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatInterface;
