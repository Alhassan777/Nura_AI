"use client";
import { Bot, MessageCircle } from "lucide-react";
import { Button } from "antd";
import { useRouter } from "next/navigation";

export default function ChatWithNuraCard() {
  const { push } = useRouter();

  return (
    <div className="bg-white rounded-md shadow-xs border border-gray-200 p-0 w-full flex flex-col items-center py-10 px-6">
      <div className="flex flex-col items-center mb-6">
        <div className="w-20 h-20 rounded-full bg-gray-200 flex items-center justify-center mb-4">
          <Bot size={48} color="#a3a3a3" strokeWidth={2} />
        </div>
        <div className="text-2xl font-bold text-gray-900 mb-2 text-center">
          Chat with Nura
        </div>
        <div className="text-gray-600 text-base text-center mb-4">
          Your AI Reflection Assistant
        </div>
      </div>
      <Button
        type="primary"
        size="large"
        className="flex items-center gap-2 !rounded-xl !px-8 !py-2 text-base"
        icon={<MessageCircle size={20} />}
        onClick={() => push("/chat")}
      >
        Start Chat
      </Button>
    </div>
  );
}
