import axios from 'axios';

export interface EmotionalData {
  scene_title?: string;
  ground_emotion?: string;
  body_locus?: string;
  cognitive_load?: string;
  sketch_motion?: string;
  sketch_shape?: string;
  temp_descriptor?: string;
  texture_descriptor?: string;
  color_palette?: string[];
  temporal_tag?: 'new' | 'familiar';
  scene_description?: string;
  metaphor_prompt?: string;
}

export class ImageGenerationService {
  private static FLUX_API_URL = 'https://black-forest-labs-flux-1-dev.hf.space/run/predict';
  
  static async generateImagePrompt(emotionalData: EmotionalData): Promise<string> {
    try {
      const promptTemplate = `You are a visual storyteller. Your task is to turn a user's internal emotional landscape into a vivid scene prompt suitable for an AI image generation model.

Use the information below to build a grounded, coherent, and poetic image prompt that captures the user's internal state as a metaphorical scene.

---

🪞 User's Reflection Data

- Scene Title: "${emotionalData.scene_title || ''}"
- Emotional Mood: "${emotionalData.ground_emotion || ''}"
- Body Sensation Location: "${emotionalData.body_locus || ''}"
- Cognitive Load: "${emotionalData.cognitive_load || ''}"
- Motion of Emotion: "${emotionalData.sketch_motion || ''}"
- Shape of Emotion: "${emotionalData.sketch_shape || ''}"
- Temperature Descriptor: "${emotionalData.temp_descriptor || ''}"
- Texture Descriptor: "${emotionalData.texture_descriptor || ''}"
- Colors Present: ${JSON.stringify(emotionalData.color_palette || [])}
- Familiarity: "${emotionalData.temporal_tag || ''}"
- Internal Scene Description: "${emotionalData.scene_description || ''}"
- Metaphor Summary: "${emotionalData.metaphor_prompt || ''}"

---

🎨 Task:

Generate a single poetic and coherent sentence (or 2 at most) that describes this internal world as a visual scene.

It should include:
- Landscape or setting
- Emotional tone
- Color usage
- Texture or lighting
- Motion, if any
- Optional metaphorical object or figure

This prompt will be used to generate a visual artwork using an image model. Be expressive, but keep it grounded in the data.

---

🎯 Output Prompt Example:

"A glowing teal orb, rough like stone but warm to the touch, floats in a foggy mountain valley. Wind swirls gently around it, as if carrying whispered thoughts from a storm that passed."

---

✏️ Now generate the scene:`;

      // For now, we'll simulate the FLUX model's behavior
      // In a real implementation, you would make an API call to FLUX.1
      
      // Simplified placeholder prompt based on emotional data
      const basePrompt = `A ${emotionalData.temp_descriptor || 'serene'} landscape with ${emotionalData.color_palette?.[0] || 'blue'} tones, where ${emotionalData.scene_description || 'a scene unfolds'}.`;
      
      return basePrompt;
    } catch (error) {
      console.error('Failed to generate image prompt:', error);
      return 'A serene landscape with soft colors and gentle lighting.';
    }
  }
  
  static async generateImage(prompt: string): Promise<string> {
    try {
      // In a real implementation, you would call the FLUX.1 API
      // Here we're just returning a placeholder image URL
      
      // For now just returning a placeholder URL
      return `https://picsum.photos/seed/${encodeURIComponent(prompt)}/800/600`;
    } catch (error) {
      console.error('Failed to generate image:', error);
      return 'https://picsum.photos/800/600'; // Fallback image
    }
  }
} 