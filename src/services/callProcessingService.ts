import { v4 as uuidv4 } from 'uuid';
import { CallData, ClientStorageService } from './storageService';
import { EmotionalData, ImageGenerationService } from './imageGenerationService';

export class CallProcessingService {
  /**
   * Process a completed call from Vapi.ai
   * Extract transcript, summary, and emotional data
   */
  static async processCallData(
    vapiResponse: any,
    userId: string
  ): Promise<CallData> {
    try {
      // Extract the transcript
      const transcript = vapiResponse.transcript || '';
      
      // Extract the summary
      const summary = vapiResponse.Analysis || '';
      
      // Extract emotional data
      const emotionalData = this.extractEmotionalData(vapiResponse);
      
      // Generate image based on emotional data
      const imagePrompt = await ImageGenerationService.generateImagePrompt(emotionalData);
      const imageUrl = await ImageGenerationService.generateImage(imagePrompt);
      
      // Create call data object
      const callData: CallData = {
        id: uuidv4(),
        userId,
        date: new Date().toISOString(),
        transcript,
        summary,
        emotionalData,
        generatedImageUrl: imageUrl,
      };
      
      // Store the call data
      ClientStorageService.saveCall(callData);
      
      return callData;
    } catch (error) {
      console.error('Failed to process call data:', error);
      
      // Create minimal call data with error handling
      const callData: CallData = {
        id: uuidv4(),
        userId,
        date: new Date().toISOString(),
        transcript: 'Failed to process transcript',
        summary: 'Failed to process summary',
      };
      
      // Still save the minimal data
      ClientStorageService.saveCall(callData);
      
      return callData;
    }
  }
  
  /**
   * Extract emotional data from Vapi.ai response
   */
  private static extractEmotionalData(vapiResponse: any): EmotionalData {
    try {
      // Try to parse the JSON data if it exists
      let data: Record<string, any> = {};
      
      if (vapiResponse.Data) {
        if (typeof vapiResponse.Data === 'string') {
          try {
            data = JSON.parse(vapiResponse.Data);
          } catch (e) {
            console.error('Failed to parse Data JSON:', e);
          }
        } else if (typeof vapiResponse.Data === 'object') {
          data = vapiResponse.Data;
        }
      }
      
      // Convert temporal_tag to the correct type
      let temporalTag: 'new' | 'familiar' | undefined;
      if (data.temporal_tag === 'new' || data.temporal_tag === 'familiar') {
        temporalTag = data.temporal_tag;
      }
      
      return {
        body_locus: data.body_locus || '',
        scene_title: data.scene_title || '',
        sketch_shape: data.sketch_shape || '',
        temporal_tag: temporalTag,
        color_palette: Array.isArray(data.color_palette) ? data.color_palette : [],
        sketch_motion: data.sketch_motion || '',
        cognitive_load: data.cognitive_load || '',
        ground_emotion: data.ground_emotion || '',
        metaphor_prompt: data.metaphor_prompt || '',
        temp_descriptor: data.temp_descriptor || '',
        scene_description: data.scene_description || '',
        texture_descriptor: data.texture_descriptor || '',
      };
    } catch (error) {
      console.error('Failed to extract emotional data:', error);
      return {};
    }
  }
  
  /**
   * Store raw webhook data for debugging purposes
   */
  static storeRawWebhookData(webhookData: any, userId: string): void {
    try {
      const callData: CallData = {
        id: uuidv4(),
        userId,
        date: new Date().toISOString(),
        transcript: JSON.stringify(webhookData),
        summary: 'Raw webhook data',
      };
      
      ClientStorageService.saveCall(callData);
    } catch (error) {
      console.error('Failed to store raw webhook data:', error);
    }
  }
} 