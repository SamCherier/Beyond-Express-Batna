import React from 'react';
import { MessageCircle, Clock, User, CheckCircle2 } from 'lucide-react';

const ConversationList = ({ conversations, selectedConversation, onSelectConversation, loading }) => {
  const getStatusBadge = (status) => {
    const badges = {
      ai_handling: { color: 'bg-blue-100 text-blue-800', label: 'IA', icon: '🤖' },
      human_handling: { color: 'bg-green-100 text-green-800', label: 'Humain', icon: '👤' },
      waiting: { color: 'bg-yellow-100 text-yellow-800', label: 'En attente', icon: '⏳' },
      closed: { color: 'bg-gray-100 text-gray-800', label: 'Fermé', icon: '✓' }
    };
    
    return badges[status] || badges.ai_handling;
  };

  const formatPhone = (phone) => {
    // Format phone number for display
    return phone.replace('whatsapp:', '').replace('+', '+');
  };

  const formatTime = (timestamp) => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffInHours = (now - date) / (1000 * 60 * 60);
      
      if (diffInHours < 1) {
        return `${Math.floor(diffInHours * 60)}m`;
      } else if (diffInHours < 24) {
        return `${Math.floor(diffInHours)}h`;
      } else {
        return date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' });
      }
    } catch (e) {
      return '';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
      </div>
    );
  }

  if (!conversations || conversations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500 p-8">
        <MessageCircle className="w-16 h-16 mb-4 text-gray-300" />
        <p className="text-lg font-medium">Aucune conversation</p>
        <p className="text-sm text-gray-400 mt-2">Les conversations WhatsApp apparaîtront ici</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      {conversations.map((conv) => {
        const badge = getStatusBadge(conv.status);
        const isSelected = selectedConversation?.conversation_id === conv.conversation_id;
        
        return (
          <div
            key={conv.conversation_id}
            onClick={() => onSelectConversation(conv)}
            className={`
              p-4 border-b border-gray-200 cursor-pointer transition-colors
              ${isSelected ? 'bg-white border-l-4 border-l-red-500' : 'bg-gray-50 hover:bg-white'}
            `}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2 flex-1">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center text-white font-bold">
                  {conv.customer_name ? conv.customer_name.charAt(0).toUpperCase() : '👤'}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-gray-900 truncate">
                    {conv.customer_name || formatPhone(conv.customer_phone)}
                  </div>
                  <div className="text-sm text-gray-500 truncate">
                    {formatPhone(conv.customer_phone)}
                  </div>
                </div>
              </div>
              
              <div className="flex flex-col items-end gap-1 ml-2">
                <span className="text-xs text-gray-500">
                  {formatTime(conv.last_message_at)}
                </span>
                {conv.unread_count > 0 && (
                  <span className="bg-red-500 text-white text-xs rounded-full px-2 py-0.5 min-w-[20px] text-center">
                    {conv.unread_count}
                  </span>
                )}
              </div>
            </div>
            
            <div className="flex items-center justify-between mt-2">
              <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${badge.color}`}>
                <span>{badge.icon}</span>
                {badge.label}
              </span>
              
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <MessageCircle className="w-3 h-3" />
                <span>{conv.message_count || 0}</span>
              </div>
            </div>
            
            {conv.assigned_agent && (
              <div className="flex items-center gap-1 mt-2 text-xs text-gray-600">
                <User className="w-3 h-3" />
                <span>Assigné: {conv.assigned_agent}</span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default ConversationList;
