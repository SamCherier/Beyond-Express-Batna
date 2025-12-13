import React from 'react';
import { Check, CheckCheck } from 'lucide-react';

const PhonePreview = ({ message, recipientName = 'Client' }) => {
  const currentTime = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });

  return (
    <div className="sticky top-24">
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-4 text-center">Aperçu du message</p>
      
      {/* iPhone Frame */}
      <div className="bg-gray-900 rounded-[3rem] p-3 shadow-2xl w-full max-w-[320px] mx-auto">
        {/* iPhone Notch */}
        <div className="bg-black rounded-[2.5rem] overflow-hidden">
          <div className="h-6 bg-black flex items-center justify-center">
            <div className="w-24 h-5 bg-black rounded-b-2xl"></div>
          </div>
          
          {/* WhatsApp Header */}
          <div className="bg-[#075E54] px-4 py-3 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 font-bold">
              {recipientName.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1">
              <p className="text-white font-semibold text-sm">{recipientName}</p>
              <p className="text-gray-300 text-xs">en ligne</p>
            </div>
          </div>

          {/* Chat Area */}
          <div className="bg-[#ECE5DD] h-[500px] p-4 overflow-y-auto">
            {/* WhatsApp Background Pattern */}
            <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg width="100" height="100" xmlns="http://www.w3.org/2000/svg"%3E%3Cpath d="M0 0h100v100H0z" fill="%23fff"/%3E%3Cpath d="M50 0L0 50l50 50 50-50z" fill="%23000" fill-opacity=".05"/%3E%3C/svg%3E")' }}></div>
            
            {/* Message Bubble */}
            <div className="flex justify-end mb-4 relative">
              <div className="bg-[#DCF8C6] rounded-lg p-3 max-w-[260px] shadow-sm">
                <p className="text-gray-800 text-sm whitespace-pre-wrap break-words">
                  {message || 'Votre message apparaîtra ici...'}
                </p>
                <div className="flex items-center justify-end gap-1 mt-1">
                  <span className="text-[10px] text-gray-500">{currentTime}</span>
                  <CheckCheck className="w-3 h-3 text-blue-500" />
                </div>
              </div>
              {/* Tail */}
              <div className="absolute right-0 top-0 w-0 h-0 border-l-[10px] border-l-transparent border-t-[10px] border-t-[#DCF8C6]"></div>
            </div>
          </div>

          {/* WhatsApp Input (disabled) */}
          <div className="bg-[#F0F0F0] px-4 py-2 flex items-center gap-2">
            <div className="flex-1 bg-white rounded-full px-4 py-2 text-sm text-gray-400">
              Tapez un message
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PhonePreview;
