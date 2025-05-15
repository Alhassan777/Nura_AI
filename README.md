# Nura - Mental Health Care Assistant

Nura is a mental health support assistant that provides emotional reflection sessions using the power of voice AI through Vapi.ai. The application helps users process their emotions, generates visual representations of their emotional state, and provides personalized action plans.

## Features

- **Voice Conversations**: Talk naturally with Nura using Vapi.ai's voice assistant technology
- **Emotional Processing**: Nura captures emotional metadata during the conversation
- **Visualization**: Generates artistic representations of your emotional state using Hugging Face's FLUX image model
- **Action Plans**: Provides personalized next steps based on your emotional reflection
- **Dashboard**: View your call history and explore past emotional visualizations
- **Notion Integration**: Save session summaries directly to Notion for future reference

## Technologies Used

- **Next.js**: React framework for the web application
- **Vapi.ai**: Voice AI platform for natural conversations
- **LangChain**: Orchestration of language models and processing
- **OpenAI**: GPT-4o for processing emotional data and generating action plans
- **Hugging Face**: FLUX image model for emotional visualizations
- **Notion**: API integration for saving session summaries

## Setup

### Prerequisites

- Node.js 18+ installed
- API keys for:
  - Vapi.ai (public key, API key, and assistant ID)
  - OpenAI
  - Hugging Face
  - Notion (API key and database ID)

### Installation

1. Clone the repository
   ```
   git clone https://github.com/yourusername/nura-app.git
   cd nura-app
   ```

2. Install dependencies
   ```
   npm install
   ```

3. Copy the `env.example` file to `.env.local` and fill in your API keys:
   ```
   cp env.example .env.local
   ```

4. Update the `.env.local` file with your API keys and credentials:
   ```
   # Vapi.ai Configuration
   VAPI_API_KEY=your_vapi_api_key_here
   NEXT_PUBLIC_VAPI_PUBLIC_KEY=your_vapi_public_key_here
   NEXT_PUBLIC_VAPI_DEFAULT_ASSISTANT_ID=your_default_assistant_id_here
   
   # OpenAI API key for processing service
   NEXT_PUBLIC_OPENAI_API_KEY=your_openai_api_key_here
   
   # Hugging Face API key for image generation
   NEXT_PUBLIC_HF_API_KEY=your_huggingface_api_key_here
   
   # Notion integration for saving summaries
   NEXT_PUBLIC_NOTION_API_KEY=your_notion_api_key_here
   NEXT_PUBLIC_NOTION_DATABASE_ID=your_notion_database_id_here
   
   # Default user ID and app URL
   DEFAULT_USER_ID=demo-user-123
   APP_BASE_URL=http://localhost:3000
   ```

5. Run the development server
   ```
   npm run dev
   ```

6. Open [http://localhost:3000](http://localhost:3000) in your browser

## Using the Dashboard

Nura includes a call history dashboard that allows you to:

1. View all past reflection sessions
2. See detailed call summaries and emotional metadata
3. Explore generated visualizations based on your emotional state
4. Export call data for your records

To access the dashboard:
- Navigate to `/dashboard` in your browser
- For testing purposes, you can import demo data by clicking "Import Demo Data" button
- Click on any call in the history to see its details

## Vapi.ai Assistant Configuration

To set up your Vapi.ai assistant:

1. Create an account at [Vapi.ai](https://vapi.ai)
2. Create a new assistant with the instructions provided in the project documentation
3. Configure the assistant to use GPT-4o as the model
4. Set up function calling to capture emotional metadata in the format described in the `EmotionalMetadata` interface
5. Configure webhooks to point to your app's webhook endpoint: `https://your-domain.com/api/vapi/webhooks`

## Notion Setup

1. Create a new database in Notion
2. Set up columns for:
   - Title (title)
   - Date (date)
   - Summary (text)
   - Emotional Data (JSON)
   - Image URL (URL)
3. Get your database ID from the URL
4. Create an integration at [Notion Developers](https://developers.notion.com) and connect it to your database

## Learn More

To learn more about Next.js and the other technologies used:

- [Next.js Documentation](https://nextjs.org/docs)
- [Vapi.ai Documentation](https://docs.vapi.ai)
- [LangChain Documentation](https://js.langchain.com/docs)
- [Notion API Documentation](https://developers.notion.com)
- [Hugging Face FLUX.1 Model](https://huggingface.co/spaces/black-forest-labs/FLUX.1-dev)

## Authentication (Future Implementation)

The app is currently set up for demo usage with a static user ID. For a production deployment, you would:

1. Uncomment and configure the Auth0 environment variables in `.env.local`
2. Update the Auth0 integration in `/src/app/api/auth/[...auth0]/route.ts`
3. Use the Auth0 UserProvider instead of the custom Provider in `/src/app/providers.tsx`

## License

This project is licensed under the MIT License.

## Acknowledgements

- [Vapi.ai](https://vapi.ai) for the voice AI platform
- [LangChain](https://langchain.com) for the LLM orchestration framework
- [Hugging Face](https://huggingface.co) for the FLUX image model
- [Notion](https://developers.notion.com) for the API integration
