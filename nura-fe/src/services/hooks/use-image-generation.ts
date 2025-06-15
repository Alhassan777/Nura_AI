import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  imageGenerationApi,
  type GeneratedImage,
  type ImageGenerationRequest,
} from "../apis/image-generation";

// Transform backend data to frontend format
const transformImageData = (image: GeneratedImage) => ({
  id: image.id,
  prompt: image.prompt,
  style: image.image_metadata?.emotion_type || "emotional",
  size: "1024x1024", // Default size
  image_url: image.image_data
    ? `data:image/${image.image_format || "png"};base64,${image.image_data}`
    : "",
  created_at: image.created_at,
  name: image.name,
  emotion_type: image.image_metadata?.emotion_type,
  visual_prompt: image.prompt,
  metadata: image.image_metadata,
});

export const useImageGeneration = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: {
      prompt: string;
      style?: string;
      size?: string;
    }) => {
      // Transform frontend data to backend format
      const request: ImageGenerationRequest = {
        user_input: data.prompt,
        identified_emotion: data.style,
        include_long_term_memory: false,
        save_locally: false,
      };

      const response = await imageGenerationApi.generateImage(request);

      if (!response.success) {
        throw new Error(response.message || "Failed to generate image");
      }

      // Transform response to frontend format
      return {
        id: Date.now().toString(), // Temporary ID
        prompt: data.prompt,
        style: response.emotion_type || data.style || "emotional",
        size: "1024x1024",
        image_url: response.image_data
          ? `data:image/${response.image_format || "png"};base64,${
              response.image_data
            }`
          : "",
        created_at: response.created_at || new Date().toISOString(),
        visual_prompt: response.visual_prompt,
        emotion_type: response.emotion_type,
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["image-generation", "history"],
      });
    },
  });
};

export const useImageHistory = (limit = 20) => {
  return useQuery({
    queryKey: ["image-generation", "history", limit],
    queryFn: async () => {
      const images = await imageGenerationApi.getImages();
      return images.slice(0, limit).map(transformImageData);
    },
  });
};

export const useImage = (imageId: string) => {
  return useQuery({
    queryKey: ["image-generation", "image", imageId],
    queryFn: async () => {
      const image = await imageGenerationApi.getImage(imageId);
      return transformImageData(image);
    },
    enabled: !!imageId,
  });
};
