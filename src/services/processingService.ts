import { HfInference } from '@huggingface/inference';
import { ChatOpenAI } from '@langchain/openai';
import { PromptTemplate } from '@langchain/core/prompts';
import { EmotionalMetadata } from './vapiService';

class ProcessingService {
  private hf: HfInference;
  
  constructor(openaiApiKey: string, hfApiKey: string) {
    // We don't need OpenAI key as Vapi already provides this functionality
    // this.geminiModel = new ChatOpenAI({
    //   modelName: 'gpt-4o',
    //   openAIApiKey: openaiApiKey,
    //   temperature: 0.7
    // });
    
    this.hf = new HfInference(hfApiKey);
  }

  /**
   * Process emotional metadata to generate a scene description for image generation
   */
  async generateScenePrompt(metadata: EmotionalMetadata): Promise<string> {
    // For now, just return the metaphor prompt directly from the metadata
    // since we're not using OpenAI to generate a custom prompt
    return metadata.metaphor_prompt || 
      `A scene representing ${metadata.ground_emotion} emotion with ${metadata.scene_title}`;
  }

  /**
   * Generate an image using Hugging Face's FLUX model
   */
  async generateImage(scenePrompt: string): Promise<string> {
    try {
      const response = await this.hf.textToImage({
        model: 'black-forest-labs/FLUX.1-dev',
        inputs: scenePrompt,
        parameters: {
          guidance_scale: 7,
          num_inference_steps: 30,
        }
      });
      
      // Different environments return different types
      // In browser, we get a Blob, in Node.js we get a Buffer or string
      if (typeof response === 'string') {
        return response; // Already a data URL in some configurations
      } 
      
      // For Node.js environment
      if (Buffer.isBuffer(response)) {
        const base64 = Buffer.from(response as Buffer).toString('base64');
        return `data:image/jpeg;base64,${base64}`;
      }
      
      // For browser environment or other blob-like objects with arrayBuffer method
      // @ts-ignore - Handle Blob type which may not be recognized in all environments
      if (response && typeof response.arrayBuffer === 'function') {
        // @ts-ignore
        const buffer = await response.arrayBuffer();
        const base64 = Buffer.from(buffer).toString('base64');
        return `data:image/jpeg;base64,${base64}`;
      }
      
      // Fallback for unknown response type
      console.error('Unknown response type from Hugging Face:', response);
      throw new Error('Unable to process image response from Hugging Face');
    } catch (error) {
      console.error('Error generating image:', error);
      throw error;
    }
  }

  /**
   * Generate action plans based on user's choice
   */
  async generateActionPlan(metadata: EmotionalMetadata, planType: 'action' | 'awareness' | 'reminder' | 'release' | 'other'): Promise<string> {
    // Simplified plan generation without OpenAI
    const planMessages = {
      'action': `Based on your feeling of ${metadata.ground_emotion}, try these steps: 1) Take a deep breath 2) Identify what triggered this feeling 3) Consider what small action you can take today`,
      'awareness': `Remember: Your ${metadata.ground_emotion} does not define you`,
      'reminder': `How are you feeling compared to when you experienced ${metadata.ground_emotion}?`,
      'release': `Close your eyes, breathe deeply, and imagine your ${metadata.ground_emotion} dissolving into light`,
      'other': `Notice how ${metadata.ground_emotion} feels in your body at ${metadata.body_locus || 'different points'}`
    };
    
    return planMessages[planType] || 'Take a moment to sit with this feeling and observe it without judgment.';
  }

  /**
   * Generate a summary for Notion - currently not used
   */
  async generateNotionSummary(metadata: EmotionalMetadata, actionPlans: Record<string, string>): Promise<string> {
    // This function is currently commented out in the main code
    return '';
  }
}

export default ProcessingService; 