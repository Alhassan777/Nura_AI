// Vapi configuration settings

// These environment variables should be set in your .env.local file
interface VapiConfig {
  apiKey: string;
  publicKey: string;
  defaultAssistantId: string;
}

export const getVapiConfig = (): VapiConfig => {
  const apiKey = process.env.VAPI_API_KEY;
  const publicKey = process.env.NEXT_PUBLIC_VAPI_PUBLIC_KEY;
  const defaultAssistantId = process.env.NEXT_PUBLIC_VAPI_DEFAULT_ASSISTANT_ID;
  
  if (!apiKey) {
    throw new Error('VAPI_API_KEY is not defined in environment variables');
  }
  
  if (!publicKey) {
    throw new Error('NEXT_PUBLIC_VAPI_PUBLIC_KEY is not defined in environment variables');
  }
  
  if (!defaultAssistantId) {
    throw new Error('NEXT_PUBLIC_VAPI_DEFAULT_ASSISTANT_ID is not defined in environment variables');
  }
  
  return {
    apiKey,
    publicKey,
    defaultAssistantId,
  };
};

// Client-side only config
export const getClientVapiConfig = () => {
  const publicKey = process.env.NEXT_PUBLIC_VAPI_PUBLIC_KEY;
  const defaultAssistantId = process.env.NEXT_PUBLIC_VAPI_DEFAULT_ASSISTANT_ID;
  
  if (!publicKey) {
    throw new Error('NEXT_PUBLIC_VAPI_PUBLIC_KEY is not defined in environment variables');
  }
  
  if (!defaultAssistantId) {
    throw new Error('NEXT_PUBLIC_VAPI_DEFAULT_ASSISTANT_ID is not defined in environment variables');
  }
  
  return {
    publicKey,
    defaultAssistantId,
  };
}; 