import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

// API functions (we'll need to create these in the APIs)
const imageGenerationApi = {
  generateImage: async (data: {
    prompt: string;
    style?: string;
    size?: string;
  }) => {
    // This would call your actual API
    // For now, return mock data
    return {
      id: Date.now().toString(),
      prompt: data.prompt,
      style: data.style || "realistic",
      size: data.size || "1024x1024",
      image_url: `https://picsum.photos/1024/1024?random=${Date.now()}`,
      created_at: new Date().toISOString(),
    };
  },

  getHistory: async (limit = 20) => {
    // Mock history data
    return Array.from({ length: 5 }, (_, i) => ({
      id: (Date.now() - i * 1000).toString(),
      prompt: `Generated image ${i + 1}`,
      style: ["realistic", "artistic", "cartoon"][i % 3],
      size: "1024x1024",
      image_url: `https://picsum.photos/1024/1024?random=${
        Date.now() - i * 1000
      }`,
      created_at: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString(),
    }));
  },

  getImage: async (imageId: string) => {
    // Mock single image data
    return {
      id: imageId,
      prompt: "A beautiful landscape",
      style: "realistic",
      size: "1024x1024",
      image_url: `https://picsum.photos/1024/1024?random=${imageId}`,
      created_at: new Date().toISOString(),
    };
  },
};

export const useImageGeneration = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: imageGenerationApi.generateImage,
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
    queryFn: () => imageGenerationApi.getHistory(limit),
  });
};

export const useImage = (imageId: string) => {
  return useQuery({
    queryKey: ["image-generation", "image", imageId],
    queryFn: () => imageGenerationApi.getImage(imageId),
    enabled: !!imageId,
  });
};
