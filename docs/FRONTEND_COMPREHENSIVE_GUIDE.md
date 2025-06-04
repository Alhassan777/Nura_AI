# Nura Frontend Comprehensive Development Guide

Complete documentation for the Nura Next.js frontend application, covering component development, features, API integration, and development patterns.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Tech Stack & Dependencies](#tech-stack--dependencies)
3. [Project Architecture](#project-architecture)
4. [Development Setup](#development-setup)
5. [Component Generation & Patterns](#component-generation--patterns)
6. [Feature Overview](#feature-overview)
7. [API Integration Guide](#api-integration-guide)
8. [Authentication System](#authentication-system)
9. [State Management](#state-management)
10. [Styling & UI Guidelines](#styling--ui-guidelines)
11. [Best Practices](#best-practices)
12. [Testing Guidelines](#testing-guidelines)
13. [Deployment](#deployment)

## 🔍 Overview

Nura is a Next.js-based mental health companion application that provides:

- **Conversational AI interface** for emotional support
- **Memory management system** with privacy controls
- **Gamification features** including badges and progress tracking
- **Safety network** for connecting with trusted contacts
- **Calendar integration** for mood and reflection tracking
- **Real-time chat** with AI assistant

## 🛠 Tech Stack & Dependencies

### Core Framework

- **Next.js 15.3.2** - React framework with App Router
- **React 19** - UI library
- **TypeScript 5** - Type safety
- **Tailwind CSS 4** - Styling framework

### UI Components & Design

- **ShadCN UI** - Base component library
- **Ant Design 5.25.3** - Additional UI components
- **Radix UI** - Headless UI primitives
- **Lucide React** - Icon library
- **Framer Motion** - Animations

### State Management & Data Fetching

- **TanStack Query v5** - Server state management
- **React Context API** - Client state management
- **React Hooks** - Local state management

### Authentication & Backend

- **Supabase** - Authentication and database
- **Axios** - HTTP client
- **JWT** - Token-based authentication

### Development Tools

- **ESLint** - Code linting
- **Prettier** (via ESLint) - Code formatting
- **TypeScript** - Type checking

## 🏗 Project Architecture

```
nura-fe/
├── public/                 # Static assets
├── src/
│   ├── app/                # Next.js App Router (pages & API routes)
│   │   ├── page.tsx        # Dashboard/Home page
│   │   ├── layout.tsx      # Root layout
│   │   ├── globals.css     # Global styles
│   │   ├── api/            # API routes (Next.js API endpoints)
│   │   ├── auth/           # Authentication pages
│   │   ├── badges/         # Gamification badges page
│   │   ├── calendar/       # Calendar/reflection page
│   │   ├── chat/           # Chat interface page
│   │   ├── login/          # Login page
│   │   ├── profile/        # User profile page
│   │   ├── signup/         # Registration page
│   │   └── verify-*/       # Email verification pages
│   ├── components/         # Reusable UI components
│   │   ├── auth/           # Authentication components
│   │   ├── calendar/       # Calendar-related components
│   │   ├── chat-components/ # Chat interface components
│   │   ├── common/         # Shared components
│   │   ├── providers/      # Context providers
│   │   ├── ui/             # ShadCN UI components
│   │   └── *.tsx          # Feature-specific components
│   ├── contexts/          # React Context providers
│   ├── hooks/             # Custom React hooks
│   ├── lib/               # Utility functions
│   ├── services/          # API layer & business logic
│   │   ├── apis/          # API client functions
│   │   ├── hooks/         # TanStack Query hooks
│   │   └── auth.ts        # Authentication service
│   ├── types/             # TypeScript type definitions
│   └── utils/             # Helper utilities
├── .env.local             # Environment variables
├── next.config.ts         # Next.js configuration
├── package.json           # Dependencies
├── tailwind.config.js     # Tailwind configuration
└── tsconfig.json          # TypeScript configuration
```

## 🚀 Development Setup

### Prerequisites

- Node.js 18+ and npm/yarn
- Git
- Access to Supabase project
- Backend API running (default: http://localhost:8000)

### Installation Steps

1. **Clone and install dependencies**

   ```bash
   cd nura-fe
   npm install
   # or
   yarn install
   ```

2. **Environment setup**
   Create `.env.local` file:

   ```env
   # Supabase Configuration
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

   # Backend API
   NEXT_PUBLIC_API_URL=http://localhost:8000

   # Optional: Development flags
   NODE_ENV=development
   ```

3. **Start development server**

   ```bash
   npm run dev
   # or
   yarn dev
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Ensure backend is running on http://localhost:8000

## 🧩 Component Generation & Patterns

### Component Structure Standards

All components should follow this structure:

```typescript
// components/ExampleComponent.tsx
import React from "react";

// Types
interface ExampleComponentProps {
  title: string;
  children?: React.ReactNode;
  className?: string;
}

// Component
export const ExampleComponent: React.FC<ExampleComponentProps> = ({
  title,
  children,
  className,
}) => {
  return (
    <div className={`example-component ${className || ""}`}>
      <h2>{title}</h2>
      {children}
    </div>
  );
};

export default ExampleComponent;
```

### Creating New Components

#### 1. Feature Components

Place feature-specific components in their own directories:

```
components/
├── chat-components/     # Chat-related components
├── auth/               # Authentication components
├── calendar/           # Calendar components
└── [feature]/          # Your new feature components
```

#### 2. UI Components (ShadCN Pattern)

For new UI components, use ShadCN CLI:

```bash
npx shadcn-ui@latest add [component-name]
```

Or create manually in `components/ui/`:

```typescript
// components/ui/my-component.tsx
import * as React from "react";
import { cn } from "@/lib/utils";

interface MyComponentProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "destructive";
}

const MyComponent = React.forwardRef<HTMLDivElement, MyComponentProps>(
  ({ className, variant = "default", ...props }, ref) => {
    return (
      <div
        className={cn(
          "base-styles",
          variant === "destructive" && "destructive-styles",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
MyComponent.displayName = "MyComponent";

export { MyComponent };
```

#### 3. Page Components

Create new pages in the `app/` directory:

```typescript
// app/new-page/page.tsx
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "New Page - Nura",
  description: "Description of the new page",
};

export default function NewPage() {
  return (
    <div>
      <h1>New Page</h1>
      {/* Page content */}
    </div>
  );
}
```

### Component Examples

#### Dashboard Card Component

```typescript
// components/DashboardCard.tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface DashboardCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: React.ReactNode;
  className?: string;
}

export const DashboardCard: React.FC<DashboardCardProps> = ({
  title,
  value,
  description,
  icon,
  className,
}) => {
  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground">{description}</p>
        )}
      </CardContent>
    </Card>
  );
};
```

#### Form Component with Validation

```typescript
// components/forms/ExampleForm.tsx
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface FormData {
  name: string;
  email: string;
}

interface ExampleFormProps {
  onSubmit: (data: FormData) => void;
  loading?: boolean;
}

export const ExampleForm: React.FC<ExampleFormProps> = ({
  onSubmit,
  loading,
}) => {
  const [formData, setFormData] = useState<FormData>({ name: "", email: "" });
  const [errors, setErrors] = useState<Partial<FormData>>({});

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    const newErrors: Partial<FormData> = {};
    if (!formData.name) newErrors.name = "Name is required";
    if (!formData.email) newErrors.email = "Email is required";

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="name">Name</Label>
        <Input
          id="name"
          value={formData.name}
          onChange={(e) =>
            setFormData((prev) => ({ ...prev, name: e.target.value }))
          }
          error={errors.name}
        />
      </div>

      <div>
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          value={formData.email}
          onChange={(e) =>
            setFormData((prev) => ({ ...prev, email: e.target.value }))
          }
          error={errors.email}
        />
      </div>

      <Button type="submit" loading={loading}>
        Submit
      </Button>
    </form>
  );
};
```

## 🎯 Feature Overview

### Current Features

#### 1. Authentication System

- **Location**: `src/app/auth/`, `src/components/auth/`
- **Features**:
  - Email/password registration and login
  - Email verification flow
  - JWT token management
  - Supabase integration
- **Pages**: `/login`, `/signup`, `/verify-email`, `/verify-confirmed`

#### 2. Chat Interface

- **Location**: `src/app/chat/`, `src/components/chat-components/`
- **Features**:
  - Real-time AI conversation
  - Message history
  - Memory integration
  - Privacy controls
- **Components**: `ChatComponent`, `MemoryPrivacyManager`, `MemoryStatistics`

#### 3. Dashboard/Home

- **Location**: `src/app/page.tsx`
- **Features**:
  - Overview cards (mood, stats, streaks)
  - Quick actions (chat, calendar)
  - Progress indicators
  - Gamification elements
- **Components**: `StatsCards`, `TodaysMoodCard`, `StreakStatisticsCard`

#### 4. Gamification System

- **Location**: `src/app/badges/`
- **Features**:
  - Badge system
  - Level progression
  - Achievement tracking
- **Components**: `LevelProgress`, gamification hooks

#### 5. Calendar & Reflections

- **Location**: `src/app/calendar/`, `src/components/calendar/`
- **Features**:
  - Mood tracking
  - Reflection scheduling
  - Progress visualization
- **Components**: `ReflectionCalendarCard`, calendar components

#### 6. User Profile

- **Location**: `src/app/profile/`
- **Features**:
  - Profile management
  - Settings
  - Account information

#### 7. Memory Management

- **Location**: `src/components/chat-components/`
- **Features**:
  - Short-term memory
  - Long-term memory
  - Emotional anchors
  - Privacy controls
- **Components**: `MemoryStatistics`, `EmotionalAnchors`, `MemoryItem`

### Adding New Features

#### Step 1: Plan the Feature

1. Define the feature requirements
2. Design the user interface
3. Identify required API endpoints
4. Plan component structure

#### Step 2: Create the Page Structure

```bash
# Create new feature directory
mkdir -p src/app/new-feature
mkdir -p src/components/new-feature
```

#### Step 3: Implement Components

```typescript
// src/components/new-feature/NewFeatureComponent.tsx
import { useNewFeatureHook } from "@/services/hooks";

export const NewFeatureComponent = () => {
  const { data, loading, error } = useNewFeatureHook();

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return <div>{/* Feature implementation */}</div>;
};
```

#### Step 4: Create API Integration

```typescript
// src/services/apis/newFeatureApi.ts
import { axiosInstance } from "./index";

export const getNewFeatureData = async () => {
  return axiosInstance.get("/new-feature").then((res) => res.data);
};

// src/services/hooks/newFeatureHooks.ts
import { useQuery } from "@tanstack/react-query";
import { getNewFeatureData } from "../apis/newFeatureApi";

export const useNewFeatureHook = () => {
  return useQuery({
    queryKey: ["new-feature"],
    queryFn: getNewFeatureData,
  });
};
```

#### Step 5: Add Navigation

Update navigation components:

```typescript
// Add to Navbar.tsx or MobileBottomNav.tsx
const navigationItems = [
  // ... existing items
  { href: "/new-feature", label: "New Feature", icon: NewFeatureIcon },
];
```

## 🔌 API Integration Guide

### Backend API Structure

The Nura backend provides the following main endpoints:

```
Base URL: http://localhost:8000

Core Services:
├── /health              # Health check
├── /chat               # Chat with AI assistant
├── /memory             # Memory management
├── /privacy            # Privacy & PII detection
├── /assistant          # Mental health assistant
├── /audit              # Audit logging
├── /image-generation   # Image generation
├── /voice              # Voice services
├── /scheduling         # Scheduling
├── /safety_network     # Safety network
├── /safety-invitations # Safety invitations
├── /users              # User management
└── /auth               # Authentication
```

### API Client Setup

The application uses a centralized API client structure:

```typescript
// src/services/apis/index.ts
import axios from "axios";

export const axiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL, // http://localhost:8000
});

// Add auth interceptor
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem("token"); // Or from Supabase
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Creating API Functions

#### Basic API Functions

```typescript
// src/services/apis/exampleApi.ts
import { axiosInstance } from "./index";

// GET request
export const getItems = async () => {
  return axiosInstance.get("/items").then((res) => res.data);
};

// POST request
export interface CreateItemPayload {
  name: string;
  description: string;
}

export const createItem = async (payload: CreateItemPayload) => {
  return axiosInstance.post("/items", payload).then((res) => res.data);
};

// PUT request
export const updateItem = async (
  id: string,
  payload: Partial<CreateItemPayload>
) => {
  return axiosInstance.put(`/items/${id}`, payload).then((res) => res.data);
};

// DELETE request
export const deleteItem = async (id: string) => {
  return axiosInstance.delete(`/items/${id}`).then((res) => res.data);
};
```

### React Query Hooks

#### Query Hooks (GET requests)

```typescript
// src/services/hooks/exampleHooks.ts
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getItems, getItem } from "../apis/exampleApi";

// List items
export const useItems = () => {
  return useQuery({
    queryKey: ["items"],
    queryFn: getItems,
  });
};

// Single item
export const useItem = (id: string) => {
  return useQuery({
    queryKey: ["items", id],
    queryFn: () => getItem(id),
    enabled: !!id, // Only fetch if id exists
  });
};
```

#### Mutation Hooks (POST, PUT, DELETE)

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createItem, updateItem, deleteItem } from "../apis/exampleApi";

// Create item
export const useCreateItem = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createItem,
    onSuccess: () => {
      // Invalidate and refetch items list
      queryClient.invalidateQueries({ queryKey: ["items"] });
    },
  });
};

// Update item
export const useUpdateItem = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      ...payload
    }: { id: string } & Partial<CreateItemPayload>) => updateItem(id, payload),
    onSuccess: (data, variables) => {
      // Update specific item in cache
      queryClient.setQueryData(["items", variables.id], data);
      // Invalidate items list
      queryClient.invalidateQueries({ queryKey: ["items"] });
    },
  });
};

// Delete item
export const useDeleteItem = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteItem,
    onSuccess: (_, deletedId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: ["items", deletedId] });
      // Invalidate items list
      queryClient.invalidateQueries({ queryKey: ["items"] });
    },
  });
};
```

### Using API Hooks in Components

```typescript
// components/ItemsList.tsx
import {
  useItems,
  useCreateItem,
  useDeleteItem,
} from "@/services/hooks/exampleHooks";

export const ItemsList = () => {
  const { data: items, loading, error } = useItems();
  const createItemMutation = useCreateItem();
  const deleteItemMutation = useDeleteItem();

  const handleCreate = (name: string) => {
    createItemMutation.mutate({ name, description: "" });
  };

  const handleDelete = (id: string) => {
    deleteItemMutation.mutate(id);
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {items?.map((item) => (
        <div key={item.id}>
          <span>{item.name}</span>
          <button onClick={() => handleDelete(item.id)}>Delete</button>
        </div>
      ))}
    </div>
  );
};
```

### Existing API Endpoints Reference

#### Chat API

```typescript
// Send message to chat
const sendMessage = async (body: {
  message?: string;
  include_memory?: boolean;
  endpoint?: string;
  method?: string;
  body?: any;
}) => {
  return axiosInstance.post("/chat", body);
};
```

#### Memory API

```typescript
// Get privacy review
const getPrivacyReview = async (userId: string) => {
  return axiosInstance.get(`/memory/privacy-review/${userId}`);
};

// Apply privacy choices
const applyPrivacyChoices = async (userId: string, choices: any) => {
  return axiosInstance.post(`/memory/apply-privacy-choices/${userId}`, choices);
};
```

#### User API

```typescript
// Get user profile
const getUserProfile = async () => {
  return axiosInstance.get("/users/profile");
};

// Update user profile
const updateUserProfile = async (data: any) => {
  return axiosInstance.put("/users/profile", data);
};
```

#### Gamification API

```typescript
// Get user badges
const getUserBadges = async () => {
  return axiosInstance.get("/gamification/badges");
};

// Get user stats
const getUserStats = async () => {
  return axiosInstance.get("/gamification/stats");
};
```

## 🔐 Authentication System

### Supabase Authentication

The app uses Supabase for authentication with JWT tokens:

```typescript
// src/utils/supabase/client.ts
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
```

### Auth Context

```typescript
// src/contexts/AuthContext.tsx
import { createContext, useContext, useEffect, useState } from "react";
import { supabase } from "@/utils/supabase/client";

interface AuthContextType {
  user: any;
  session: any;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const login = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (error) throw error;
  };

  const logout = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
  };

  const signup = async (email: string, password: string) => {
    const { error } = await supabase.auth.signUp({ email, password });
    if (error) throw error;
  };

  return (
    <AuthContext.Provider
      value={{ user, session, loading, login, logout, signup }}
    >
      {children}
    </AuthContext.Provider>
  );
};
```

### Protected Routes

```typescript
// components/ProtectedRoute.tsx
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return null;
  }

  return <>{children}</>;
};
```

### Using Authentication in Components

```typescript
// Example usage in a component
import { useAuth } from "@/contexts/AuthContext";

export const ProfileComponent = () => {
  const { user, logout } = useAuth();

  return (
    <div>
      <h1>Welcome, {user?.email}</h1>
      <button onClick={logout}>Logout</button>
    </div>
  );
};
```

## 🗃 State Management

### React Query for Server State

React Query handles all server state management:

```typescript
// src/app/layout.tsx - Query Client Setup
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      cacheTime: 1000 * 60 * 10, // 10 minutes
    },
  },
});

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  );
}
```

### Context for Global Client State

For global client state that needs to be shared across components:

```typescript
// src/contexts/AppContext.tsx
import { createContext, useContext, useReducer } from "react";

interface AppState {
  theme: "light" | "dark";
  sidebarOpen: boolean;
  notifications: any[];
}

type AppAction =
  | { type: "SET_THEME"; payload: "light" | "dark" }
  | { type: "TOGGLE_SIDEBAR" }
  | { type: "ADD_NOTIFICATION"; payload: any };

const initialState: AppState = {
  theme: "light",
  sidebarOpen: false,
  notifications: [],
};

const appReducer = (state: AppState, action: AppAction): AppState => {
  switch (action.type) {
    case "SET_THEME":
      return { ...state, theme: action.payload };
    case "TOGGLE_SIDEBAR":
      return { ...state, sidebarOpen: !state.sidebarOpen };
    case "ADD_NOTIFICATION":
      return {
        ...state,
        notifications: [...state.notifications, action.payload],
      };
    default:
      return state;
  }
};

const AppContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
}>({} as any);

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
};

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
};
```

## 🎨 Styling & UI Guidelines

### Design System

The app uses a combination of:

- **Tailwind CSS** for utility-first styling
- **ShadCN UI** for base components
- **Ant Design** for complex components
- **CSS Variables** for theming

### Color Palette

```css
/* src/app/globals.css */
:root {
  /* Primary colors */
  --primary: 220 70% 50%;
  --primary-foreground: 0 0% 98%;

  /* Secondary colors */
  --secondary: 220 14.3% 95.9%;
  --secondary-foreground: 220.9 39.3% 11%;

  /* Accent colors */
  --accent: 220 14.3% 95.9%;
  --accent-foreground: 220.9 39.3% 11%;

  /* Neutral colors */
  --background: 0 0% 100%;
  --foreground: 220.9 39.3% 11%;

  /* Border and input */
  --border: 220 13% 91%;
  --input: 220 13% 91%;
  --ring: 220 70% 50%;
}

.dark {
  --background: 220.9 39.3% 11%;
  --foreground: 0 0% 98%;
  /* ... dark theme colors */
}
```

### Component Styling Patterns

#### Using Tailwind Classes

```typescript
// Good: Consistent spacing and responsive design
<div className="p-4 md:p-6 lg:p-8 space-y-4">
  <h1 className="text-2xl md:text-3xl font-bold text-foreground">Title</h1>
  <p className="text-muted-foreground">Description</p>
</div>
```

#### Using CSS Variables

```typescript
// Good: Using design system colors
<div className="bg-background text-foreground border border-border rounded-lg">
  Content
</div>
```

#### Component Variants with Class Variance Authority

```typescript
// components/ui/button.tsx
import { cva, type VariantProps } from "class-variance-authority";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline:
          "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);
```

### Responsive Design

Use Tailwind's responsive prefixes:

```typescript
<div
  className="
  grid grid-cols-1 gap-4
  md:grid-cols-2 md:gap-6
  lg:grid-cols-3 lg:gap-8
  xl:grid-cols-4
"
>
  {/* Responsive grid */}
</div>
```

### Accessibility

Ensure components are accessible:

```typescript
// Good: Proper ARIA labels and keyboard navigation
<button
  className="btn"
  aria-label="Close dialog"
  onClick={handleClose}
  onKeyDown={(e) => e.key === "Enter" && handleClose()}
>
  <span aria-hidden="true">&times;</span>
</button>
```

## ✅ Best Practices

### Code Organization

1. **File Naming**

   - Use PascalCase for components: `MyComponent.tsx`
   - Use camelCase for utilities: `apiHelpers.ts`
   - Use kebab-case for pages: `my-page/page.tsx`

2. **Import Organization**

   ```typescript
   // 1. React and Next.js imports
   import React from "react";
   import { useRouter } from "next/navigation";

   // 2. Third-party library imports
   import { useQuery } from "@tanstack/react-query";
   import { Button } from "@/components/ui/button";

   // 3. Internal imports (relative to @/ alias)
   import { useAuth } from "@/contexts/AuthContext";
   import { MyComponent } from "@/components/MyComponent";

   // 4. Relative imports
   import "./styles.css";
   ```

3. **Type Definitions**

   ```typescript
   // Define types close to usage or in separate type files
   interface ComponentProps {
     title: string;
     optional?: boolean;
   }

   // Use meaningful names
   type UserStatus = "active" | "inactive" | "pending";
   ```

### Performance Optimization

1. **Code Splitting**

   ```typescript
   // Lazy load heavy components
   const HeavyComponent = dynamic(() => import("./HeavyComponent"), {
     loading: () => <p>Loading...</p>,
   });
   ```

2. **Memoization**

   ```typescript
   // Memoize expensive calculations
   const expensiveValue = useMemo(() => {
     return heavyCalculation(data);
   }, [data]);

   // Memoize callbacks
   const handleClick = useCallback(() => {
     onAction(id);
   }, [onAction, id]);
   ```

3. **React Query Optimization**
   ```typescript
   // Use proper stale times and cache times
   const { data } = useQuery({
     queryKey: ["data", id],
     queryFn: () => fetchData(id),
     staleTime: 1000 * 60 * 5, // 5 minutes
     cacheTime: 1000 * 60 * 10, // 10 minutes
   });
   ```

### Error Handling

1. **Component Error Boundaries**

   ```typescript
   // components/ErrorBoundary.tsx
   import React, { ErrorInfo, ReactNode } from "react";

   interface Props {
     children: ReactNode;
     fallback?: ReactNode;
   }

   interface State {
     hasError: boolean;
   }

   class ErrorBoundary extends React.Component<Props, State> {
     constructor(props: Props) {
       super(props);
       this.state = { hasError: false };
     }

     static getDerivedStateFromError(): State {
       return { hasError: true };
     }

     componentDidCatch(error: Error, errorInfo: ErrorInfo) {
       console.error("Error caught by boundary:", error, errorInfo);
     }

     render() {
       if (this.state.hasError) {
         return this.props.fallback || <h1>Something went wrong.</h1>;
       }

       return this.props.children;
     }
   }
   ```

2. **API Error Handling**
   ```typescript
   // services/apis/index.ts
   axiosInstance.interceptors.response.use(
     (response) => response,
     (error) => {
       if (error.response?.status === 401) {
         // Handle unauthorized
         window.location.href = "/login";
       }
       return Promise.reject(error);
     }
   );
   ```

### Security Best Practices

1. **Environment Variables**

   - Never commit sensitive data
   - Use `NEXT_PUBLIC_` prefix only for client-side variables
   - Validate environment variables at startup

2. **Input Validation**

   ```typescript
   // Always validate and sanitize inputs
   const sanitizedInput = input.trim().toLowerCase();
   if (!emailRegex.test(sanitizedInput)) {
     throw new Error("Invalid email format");
   }
   ```

3. **XSS Prevention**

   ```typescript
   // Use dangerouslySetInnerHTML sparingly and sanitize content
   import DOMPurify from "dompurify";

   <div
     dangerouslySetInnerHTML={{
       __html: DOMPurify.sanitize(htmlContent),
     }}
   />;
   ```

## 🧪 Testing Guidelines

### Testing Strategy

1. **Unit Tests** - Test individual components and functions
2. **Integration Tests** - Test component interactions
3. **E2E Tests** - Test complete user workflows

### Setting Up Testing

```bash
# Install testing dependencies
npm install -D @testing-library/react @testing-library/jest-dom jest jest-environment-jsdom
```

### Component Testing Example

```typescript
// __tests__/components/Button.test.tsx
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { Button } from "@/components/ui/button";

describe("Button Component", () => {
  it("renders with correct text", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText("Click me")).toBeInTheDocument();
  });

  it("calls onClick handler when clicked", () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    fireEvent.click(screen.getByText("Click me"));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("applies custom className", () => {
    render(<Button className="custom-class">Button</Button>);
    expect(screen.getByText("Button")).toHaveClass("custom-class");
  });
});
```

### Hook Testing

```typescript
// __tests__/hooks/useCounter.test.ts
import { renderHook, act } from "@testing-library/react";
import { useCounter } from "@/hooks/useCounter";

describe("useCounter Hook", () => {
  it("should initialize with default value", () => {
    const { result } = renderHook(() => useCounter());
    expect(result.current.count).toBe(0);
  });

  it("should increment count", () => {
    const { result } = renderHook(() => useCounter());

    act(() => {
      result.current.increment();
    });

    expect(result.current.count).toBe(1);
  });
});
```

## 🚀 Deployment

### Build Process

```bash
# Build the application
npm run build

# Start production server
npm run start
```

### Environment Variables

Ensure all required environment variables are set:

```bash
# Production environment variables
NEXT_PUBLIC_SUPABASE_URL=your_production_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_production_supabase_anon_key
NEXT_PUBLIC_API_URL=your_production_api_url
```

### Performance Checklist

- [ ] Bundle size optimization
- [ ] Image optimization (Next.js Image component)
- [ ] Code splitting implemented
- [ ] Proper caching strategies
- [ ] SEO optimization (metadata, sitemap)
- [ ] Accessibility compliance
- [ ] Error monitoring setup

## 📚 Additional Resources

### Documentation Links

- [Next.js Documentation](https://nextjs.org/docs)
- [React Query Documentation](https://tanstack.com/query/latest)
- [Supabase Documentation](https://supabase.io/docs)
- [ShadCN UI Documentation](https://ui.shadcn.com/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

### Development Tools

- **VS Code Extensions**: ES7+ React/Redux/React-Native snippets, Tailwind CSS IntelliSense
- **Browser Extensions**: React Developer Tools, TanStack Query Devtools

### Common Patterns

- Custom hooks for reusable logic
- Higher-order components for common functionality
- Context providers for global state
- Error boundaries for error handling
- Loading and error states for async operations

This comprehensive guide should help developers understand the Nura frontend architecture, component patterns, and best practices for extending and maintaining the application.
