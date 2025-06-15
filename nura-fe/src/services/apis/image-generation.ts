import { axiosInstance } from "./index";

export interface ImageGenerationRequest {
  user_input: string;
  include_long_term_memory?: boolean;
  save_locally?: boolean;
  identified_emotion?: string;
  name?: string;
}

export interface ImageGenerationResponse {
  success: boolean;
  message?: string;
  image_data?: string; // Base64 encoded image
  image_format?: string;
  visual_prompt?: string;
  emotion_type?: string;
  context_analysis?: any;
  created_at?: string;
  needs_more_input?: boolean;
}

export interface GeneratedImage {
  id: string;
  user_id: string;
  name?: string;
  prompt: string;
  image_format: string;
  image_data?: string;
  image_metadata?: {
    emotion_type?: string;
    generation_params?: any;
    context_analysis?: any;
    model_used?: string;
  };
  created_at: string;
  updated_at: string;
}

export interface ImageListParams {
  name?: string;
  prompt?: string;
  emotion_type?: string;
  created_from?: string; // YYYY-MM-DD
  created_to?: string; // YYYY-MM-DD
}

export const imageGenerationApi = {
  // Generate a new image
  generateImage: async (
    data: ImageGenerationRequest
  ): Promise<ImageGenerationResponse> => {
    const response = await axiosInstance.post(
      "/image-generation/generate",
      data
    );
    return response.data;
  },

  // Get list of generated images with optional filters
  getImages: async (params?: ImageListParams): Promise<GeneratedImage[]> => {
    const response = await axiosInstance.get("/image-generation/images", {
      params,
    });
    return response.data;
  },

  // Get a specific image by ID
  getImage: async (imageId: string): Promise<GeneratedImage> => {
    const response = await axiosInstance.get(
      `/image-generation/images/${imageId}`
    );
    return response.data;
  },

  // Update image name
  updateImageName: async (
    imageId: string,
    name: string
  ): Promise<GeneratedImage> => {
    const response = await axiosInstance.patch(
      `/image-generation/images/${imageId}/name`,
      { name }
    );
    return response.data;
  },

  // Update image metadata
  updateImageMetadata: async (
    imageId: string,
    metadata: any
  ): Promise<GeneratedImage> => {
    const response = await axiosInstance.patch(
      `/image-generation/images/${imageId}/metadata`,
      {
        image_metadata: metadata,
      }
    );
    return response.data;
  },

  // Delete an image
  deleteImage: async (
    imageId: string
  ): Promise<{ success: boolean; message: string }> => {
    const response = await axiosInstance.delete(
      `/image-generation/images/${imageId}`
    );
    return response.data;
  },

  // Validate input for visualization
  validateInput: async (
    userInput: string
  ): Promise<{
    suitable: boolean;
    confidence: string;
    analysis: any;
    recommendation: string;
    error?: string;
  }> => {
    const response = await axiosInstance.post("/image-generation/validate", {
      user_id: "current", // Will be handled by auth middleware
      user_input: userInput,
    });
    return response.data;
  },

  // Get generation status
  getStatus: async (): Promise<{
    user_id: string;
    service_available: boolean;
    estimated_generation_time: string;
  }> => {
    const response = await axiosInstance.get(
      "/image-generation/status/current"
    );
    return response.data;
  },

  // Quick generate (for testing)
  quickGenerate: async (
    userInput: string
  ): Promise<{
    success: boolean;
    image_data?: string;
    visual_prompt?: string;
    emotion_type?: string;
    message?: string;
  }> => {
    const response = await axiosInstance.post(
      "/image-generation/quick-generate",
      null,
      {
        params: { user_input: userInput },
      }
    );
    return response.data;
  },
};
