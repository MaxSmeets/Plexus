"use client";

import { useState } from "react";

interface Message {
  id: number;
  text: string;
  sender: "user" | "assistant";
  timestamp: Date;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const newMessage: Message = {
      id: Date.now(),
      text: inputValue,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, newMessage]);
    setInputValue("");

    // Simulate assistant response
    setTimeout(() => {
      const assistantMessage: Message = {
        id: Date.now(),
        text: "I'm a placeholder response. Connect me to your AI agent!",
        sender: "assistant",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    }, 1000);
  };

  return (
    <div className='flex flex-col h-screen bg-gray-50 dark:bg-gray-900'>
      {/* Header */}
      <header className='bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4'>
        <h1 className='text-xl font-semibold text-gray-900 dark:text-white'>
          Plexus Chat
        </h1>
      </header>

      {/* Messages Area */}
      <div className='flex-1 overflow-y-auto p-4 space-y-4'>
        {messages.length === 0 ? (
          <div className='flex items-center justify-center h-full text-gray-500 dark:text-gray-400'>
            <p>Start a conversation...</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.sender === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                  message.sender === "user"
                    ? "bg-blue-500 text-white"
                    : "bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700"
                }`}
              >
                <p className='text-sm'>{message.text}</p>
                <p className='text-xs mt-1 opacity-70'>
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Input Area */}
      <div className='bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4'>
        <form onSubmit={handleSendMessage} className='flex gap-2'>
          <input
            type='text'
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder='Type your message...'
            className='flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white'
          />
          <button
            type='submit'
            className='px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50'
            disabled={!inputValue.trim()}
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
