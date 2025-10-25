import React, { useState, useEffect } from 'react';
import { MessageCircle, RefreshCw, Filter, Bell } from 'lucide-react';
import { toast } from 'sonner';
import ConversationList from '../components/ConversationList';
import ChatInterface from '../components/ChatInterface';
import {
  getWhatsAppConversations,
  getConversationMessages,
  sendWhatsAppMessage,
  assignConversationToHuman,
  markConversationRead
} from '../api';

const WhatsAppDashboard = () => {
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  // Fetch conversations
  const fetchConversations = async (showToast = false) => {
    try {
      setRefreshing(true);
      const response = await getWhatsAppConversations(statusFilter);
      setConversations(response.data.conversations || []);
      
      if (showToast) {
        toast.success('Conversations actualisées');
      }
    } catch (error) {
      console.error('Error fetching conversations:', error);
      toast.error('Erreur lors du chargement des conversations');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Fetch messages for selected conversation
  const fetchMessages = async (conversationId) => {
    try {
      setMessagesLoading(true);
      const response = await getConversationMessages(conversationId);
      setMessages(response.data.messages || []);
      
      // Mark as read
      await markConversationRead(conversationId);
      
      // Update unread count in conversations list
      setConversations(prev =>
        prev.map(conv =>
          conv.conversation_id === conversationId
            ? { ...conv, unread_count: 0 }
            : conv
        )
      );
    } catch (error) {
      console.error('Error fetching messages:', error);
      toast.error('Erreur lors du chargement des messages');
    } finally {
      setMessagesLoading(false);
    }
  };

  // Select conversation
  const handleSelectConversation = (conversation) => {
    setSelectedConversation(conversation);
    fetchMessages(conversation.conversation_id);
  };

  // Send message
  const handleSendMessage = async (messageBody) => {
    if (!selectedConversation) return;

    try {
      await sendWhatsAppMessage({
        to_phone: selectedConversation.customer_phone,
        message_body: messageBody
      });

      // Refresh messages
      await fetchMessages(selectedConversation.conversation_id);
      
      toast.success('Message envoyé');
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Erreur lors de l\'envoi du message');
      throw error;
    }
  };

  // Take over conversation from AI
  const handleTakeOver = async () => {
    if (!selectedConversation) return;

    try {
      await assignConversationToHuman(selectedConversation.conversation_id);
      
      // Update conversation status locally
      setSelectedConversation(prev => ({
        ...prev,
        status: 'human_handling'
      }));
      
      // Update in conversations list
      setConversations(prev =>
        prev.map(conv =>
          conv.conversation_id === selectedConversation.conversation_id
            ? { ...conv, status: 'human_handling' }
            : conv
        )
      );
      
      toast.success('✅ Vous gérez maintenant cette conversation');
    } catch (error) {
      console.error('Error taking over conversation:', error);
      toast.error('Erreur lors de la prise en charge');
    }
  };

  // Filter conversations
  const handleFilterChange = (newFilter) => {
    setStatusFilter(newFilter);
  };

  // Initial load
  useEffect(() => {
    fetchConversations();
  }, [statusFilter]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchConversations(false);
      
      // Refresh messages if conversation is selected
      if (selectedConversation) {
        fetchMessages(selectedConversation.conversation_id);
      }
    }, 30000); // 30 seconds

    return () => clearInterval(interval);
  }, [selectedConversation, statusFilter]);

  // Count conversations by status
  const waitingCount = conversations.filter(c => c.status === 'waiting').length;
  const aiHandlingCount = conversations.filter(c => c.status === 'ai_handling').length;
  const humanHandlingCount = conversations.filter(c => c.status === 'human_handling').length;

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-red-500 to-orange-500 text-white p-6 shadow-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <MessageCircle className="w-8 h-8" />
            <div>
              <h1 className="text-2xl font-bold">WhatsApp Dashboard</h1>
              <p className="text-sm text-white/80">Gérez vos conversations clients</p>
            </div>
          </div>
          
          <button
            onClick={() => fetchConversations(true)}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Actualiser
          </button>
        </div>
        
        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mt-6">
          <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
            <div className="text-xs text-white/70 mb-1">En attente</div>
            <div className="text-2xl font-bold flex items-center gap-2">
              {waitingCount}
              {waitingCount > 0 && <Bell className="w-5 h-5 animate-pulse" />}
            </div>
          </div>
          
          <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
            <div className="text-xs text-white/70 mb-1">Géré par IA</div>
            <div className="text-2xl font-bold">🤖 {aiHandlingCount}</div>
          </div>
          
          <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
            <div className="text-xs text-white/70 mb-1">Géré par humain</div>
            <div className="text-2xl font-bold">👤 {humanHandlingCount}</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white border-b px-6 py-3 flex items-center gap-2">
        <Filter className="w-4 h-4 text-gray-500" />
        <span className="text-sm font-medium text-gray-700">Filtrer:</span>
        
        <button
          onClick={() => handleFilterChange(null)}
          className={`px-3 py-1 rounded-full text-sm transition-colors ${
            statusFilter === null
              ? 'bg-red-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Toutes
        </button>
        
        <button
          onClick={() => handleFilterChange('waiting')}
          className={`px-3 py-1 rounded-full text-sm transition-colors ${
            statusFilter === 'waiting'
              ? 'bg-yellow-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          En attente ({waitingCount})
        </button>
        
        <button
          onClick={() => handleFilterChange('ai_handling')}
          className={`px-3 py-1 rounded-full text-sm transition-colors ${
            statusFilter === 'ai_handling'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          IA ({aiHandlingCount})
        </button>
        
        <button
          onClick={() => handleFilterChange('human_handling')}
          className={`px-3 py-1 rounded-full text-sm transition-colors ${
            statusFilter === 'human_handling'
              ? 'bg-green-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Humain ({humanHandlingCount})
        </button>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Conversations List */}
        <div className="w-96 border-r bg-white overflow-hidden flex flex-col">
          <ConversationList
            conversations={conversations}
            selectedConversation={selectedConversation}
            onSelectConversation={handleSelectConversation}
            loading={loading}
          />
        </div>

        {/* Chat Interface */}
        <div className="flex-1 overflow-hidden">
          <ChatInterface
            conversation={selectedConversation}
            messages={messages}
            onSendMessage={handleSendMessage}
            onTakeOver={handleTakeOver}
            loading={messagesLoading}
          />
        </div>
      </div>
    </div>
  );
};

export default WhatsAppDashboard;
