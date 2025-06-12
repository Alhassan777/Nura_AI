# Nura: Your Personal Mental Health Companion

Nura is a Next.js application designed as a personal mental health companion. It provides a chat interface for users to express themselves, tracks conversation history, manages memories (short-term, long-term, and emotional anchors), and includes features for privacy management of sensitive information (PII).

## Key Features

- **Conversational Interface**: Allows users to chat with an AI assistant.
- **Memory Management**: Stores and retrieves different types of memories:
  - Short-term: For immediate context in conversations.
  - Long-term: For persistent information and insights.
  - Emotional Anchors: Significant memories or concepts that provide emotional grounding.
- **PII Detection & Privacy**: Identifies potentially sensitive information in memories and allows users to manage how it's stored.
- **Authentication**: Manages user sessions and secures API communication (via Supabase and an AuthProvider).
- **Modular UI**: Utilizes ShadCN UI components for a modern and consistent user interface, and Ant Design components where applicable.
- **API Abstraction**: Centralizes API call logic, particularly for chat and memory services.

## Technology Stack

- **Framework**: [Next.js](https://nextjs.org/)
- **Language**: [TypeScript](https://www.typescriptlang.org/)
- **UI Components**: [ShadCN UI](https://ui.shadcn.com/), [Ant Design](https://ant.design/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Authentication**: [Supabase](https://supabase.io/)
- **API Communication**: [Axios](https://axios-http.com/)
- **State Management**: React Context API, React Query (implied by `useSendMessage` hook)

## Project Structure Overview

```
nura-fe/
├── public/                 # Static assets
├── src/
│   ├── app/                # Next.js App Router (pages, layouts)
│   ├── components/         # UI components (ShadCN, custom)
│   │   ├── chat-components/  # Specific components for the chat interface
│   │   └── ui/             # ShadCN UI installed components
│   ├── contexts/           # React Context providers (e.g., AuthContext.tsx)
│   ├── lib/                # Utility functions (e.g., ShadCN's utils.ts)
│   ├── services/           # API interaction layer (see details below)
│   └── utils/              # Utility functions (e.g., Supabase client setup)
├── .env.local              # Environment variables (ensure NEXT_PUBLIC_API_URL is set)
├── next.config.js          # Next.js configuration
├── package.json
├── tsconfig.json
└── README.md
```

### Focus on `src/services` Folder

The `src/services` folder plays a crucial role in abstracting and managing communication with your backend APIs. Its primary purpose is to keep API call logic clean, reusable, and separate from the UI components.

**Key characteristics and contents:**

1.  **API Client Configuration (Implicit)**:

    - While not explicitly shown as a file in `services`, the `AuthContext` (`src/contexts/AuthContext.tsx`) configures `axios` defaults, including `baseURL` (from `process.env.NEXT_PUBLIC_API_URL`) and the `Authorization` header using the user's session token. This global `axios` instance is then used by hooks within the `services` folder.

2.  **Custom Hooks for API Calls (e.g., `useSendMessage`)**:

    - The folder likely contains custom React hooks that wrap `axios` calls or use libraries like React Query (`@tanstack/react-query`) for data fetching, mutations, caching, and state synchronization.
    - **Example**: The `useSendMessage` hook (as seen imported in `ChatComponent`) is a prime example. It probably handles the POST request to the chat API endpoint.
      - It abstracts the actual API endpoint, request method (POST, GET, etc.), and body construction.
      - It might use React Query's `useMutation` for sending messages, providing loading states, error handling, and onSuccess/onError callbacks.
    - Other hooks might exist for fetching memory statistics (`useMemoryStats`), loading memories (`useLoadMemories`), clearing memories (`useClearMemories`), managing privacy choices, etc.

3.  **Type Definitions**:
    - This folder might also contain TypeScript type definitions for API request payloads and response data to ensure type safety throughout the API interaction layer.

**Benefits of this structure:**

- **Separation of Concerns**: UI components remain focused on presentation and user interaction, while data fetching logic resides in the services layer.
- **Reusability**: Hooks like `useSendMessage` can be used by any component that needs to send a message, without duplicating API call logic.
- **Maintainability**: If API endpoints or data structures change, modifications are centralized in the services folder, making updates easier.
- **Testability**: API interaction logic can be tested more easily in isolation.
- **Developer Experience**: Provides a clear and consistent way to interact with the backend.

**To fully understand the `services` folder, you would typically look for:**

- Files defining custom hooks (e.g., `useSendMessage.ts`, `memoryHooks.ts`).
- Any utility functions specifically for formatting API requests or responses.
- A potential `apiClient.ts` or similar if a dedicated `axios` instance with more specific interceptors (beyond what `AuthContext` sets up) is used, though the current setup seems to rely on the global `axios` defaults.

## Getting Started

1.  **Clone the repository.**
2.  **Install dependencies**:
    ```bash
    npm install
    # or
    yarn install
    ```
3.  **Set up environment variables**:
    - Create a `.env.local` file in the root of the project.
    - Add your Supabase URL, an anon key, and your API base URL:
      ```
      NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
      NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
      NEXT_PUBLIC_API_URL=your_backend_api_base_url # e.g., http://localhost:8000/api
      ```
4.  **Run the development server**:
    ```bash
    npm run dev
    # or
    yarn dev
    ```
5.  Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Learn More

To learn more about the technologies used, refer to their respective documentation:

- [Next.js Documentation](https://nextjs.org/docs)
- [Supabase Documentation](https://supabase.io/docs)
- [ShadCN UI Documentation](https://ui.shadcn.com/)
- [Ant Design Documentation](https://ant.design/docs/react/introduce)
- [Axios Documentation](https://axios-http.com/docs/intro)
- [React Query Documentation](https://tanstack.com/query/latest/docs/react/overview)

This project structure provides a solid foundation for building a scalable and maintainable web application.
