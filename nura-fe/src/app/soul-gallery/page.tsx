"use client";

import React, { useState, useEffect } from "react";
import {
  Card,
  Button,
  Image,
  Modal,
  Typography,
  Row,
  Col,
  Tag,
  Empty,
  message,
  Spin,
} from "antd";
import { Heart, Download, Eye, BookOpen, RefreshCw } from "lucide-react";
import { useImageHistory } from "@/services/hooks/use-image-generation";

const { Title, Text, Paragraph } = Typography;

export default function SoulGalleryPage() {
  const [selectedImage, setSelectedImage] = useState<any>(null);
  const [showImageModal, setShowImageModal] = useState(false);

  const {
    data: imageHistory,
    isLoading: isLoadingHistory,
    error: historyError,
    refetch: refetchHistory,
    isError: hasHistoryError,
  } = useImageHistory(50); // Fetch up to 50 images

  // Show error notification if there's an issue loading the gallery
  useEffect(() => {
    if (hasHistoryError && historyError) {
      message.error(
        `Failed to load your gallery: ${
          historyError.message || "Unknown error"
        }`
      );
    }
  }, [hasHistoryError, historyError]);

  const emotionalStyles = [
    {
      value: "calm",
      label: "Calm & Peaceful",
      description: "Serene, tranquil imagery with soft colors",
    },
    {
      value: "energetic",
      label: "Energetic & Dynamic",
      description: "Vibrant, powerful imagery with bold colors",
    },
    {
      value: "mysterious",
      label: "Mysterious & Abstract",
      description: "Enigmatic, symbolic representations",
    },
    {
      value: "hopeful",
      label: "Hopeful & Bright",
      description: "Uplifting imagery with light and possibility",
    },
    {
      value: "melancholic",
      label: "Melancholic & Reflective",
      description: "Introspective, contemplative scenes",
    },
    {
      value: "emotional",
      label: "General Emotional",
      description: "Let AI detect and visualize your emotions",
    },
  ];

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <Heart className="h-8 w-8 text-purple-600" />
        <Title level={2} className="!mb-0">
          Soul Gallery
        </Title>
      </div>

      <Paragraph className="text-gray-600 mb-6">
        Explore your collection of emotional visualizations - beautiful visual
        art created from your inner thoughts, feelings, and reflections.
      </Paragraph>

      {/* Gallery Section */}
      <Card
        title={
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              <span>Your Soul Gallery</span>
              {imageHistory && imageHistory.length > 0 && (
                <Tag color="blue">{imageHistory.length} images</Tag>
              )}
            </div>
            <Button
              icon={<RefreshCw className="h-4 w-4" />}
              onClick={() => refetchHistory()}
              loading={isLoadingHistory}
              size="small"
            >
              Refresh
            </Button>
          </div>
        }
      >
        {isLoadingHistory ? (
          <div className="text-center py-8">
            <Spin size="large" />
            <div className="mt-4">Loading your gallery...</div>
          </div>
        ) : hasHistoryError ? (
          <div className="text-center py-8">
            <Empty
              description={
                <div className="space-y-2">
                  <div>Failed to load your gallery. Please try refreshing.</div>
                  {process.env.NODE_ENV === "development" && historyError && (
                    <div className="text-xs text-red-500 mt-2">
                      Debug: {historyError.message || String(historyError)}
                    </div>
                  )}
                </div>
              }
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              <Button
                type="primary"
                onClick={() => refetchHistory()}
                icon={<RefreshCw className="h-4 w-4" />}
              >
                Try Again
              </Button>
            </Empty>
          </div>
        ) : !imageHistory || imageHistory.length === 0 ? (
          <Empty
            description="Your soul gallery is empty. Start creating emotional visualizations through your conversations with Nura to see them appear here."
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <Row gutter={[16, 16]}>
            {imageHistory.map((image: any) => (
              <Col xs={24} sm={12} md={8} lg={6} key={image.id}>
                <Card
                  hoverable
                  cover={
                    <div className="relative group">
                      <Image
                        src={image.image_url}
                        alt={
                          image.name ||
                          image.prompt ||
                          "Generated emotional visualization"
                        }
                        className="w-full h-48 object-cover"
                        preview={false}
                        fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMIAAADDCAYAAADQvc6UAAABRWlDQ1BJQ0MgUHJvZmlsZQAAKJFjYGASSSwoyGFhYGDIzSspCnJ3UoiIjFJgf8LAwSDCIMogwMCcmFxc4BgQ4ANUwgCjUcG3awyMIPqyLsis7PPOq3QdDFcvjV3jOD1boQVTPQrgSkktTgbSf4A4LbmgqISBgTEFyFYuLykAsTuAbJEioKOA7DkgdjqEvQHEToKwj4DVhAQ5A9k3gGyB5IxEoBmML4BsnSQk8XQkNtReEOBxcfXxUQg1Mjc0dyHgXNJBSWpFCYh2zi+oLMpMzyhRcASGUqqCZ16yno6CkYGRAQMDKMwhqj/fAIcloxgHQqxAjIHBEugw5sUIsSQpBobtQPdLciLEVJYzMPBHMDBsayhILEqEO4DxG0txmrERhM29nYGBddr//5/DGRjYNRkY/l7////39v///y4Dmn+LgeHANwDrkl1AuO+pmgAAADhlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAAqACAAQAAAABAAAAwqADAAQAAAABAAAAwwAAAAD9b/HnAAAHlklEQVR4Ae3dP3Ik1RnG4W+FgYxN"
                      />
                      <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 transition-all duration-200 flex items-center justify-center">
                        <Button
                          type="primary"
                          icon={<Eye className="h-4 w-4" />}
                          className="opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={() => {
                            setSelectedImage(image);
                            setShowImageModal(true);
                          }}
                        >
                          View Details
                        </Button>
                      </div>
                    </div>
                  }
                  size="small"
                >
                  <div className="space-y-2">
                    <Text className="text-sm line-clamp-2 font-medium">
                      {image.name || "Untitled Visualization"}
                    </Text>
                    {image.visual_prompt && (
                      <Text className="text-xs text-gray-600 line-clamp-2">
                        {image.visual_prompt}
                      </Text>
                    )}
                    <div className="flex items-center justify-between">
                      <Tag color="purple" className="text-xs">
                        {emotionalStyles.find(
                          (s) => s.value === image.emotion_type
                        )?.label ||
                          image.emotion_type ||
                          image.style ||
                          "Emotional"}
                      </Tag>
                      <Text className="text-xs text-gray-500">
                        {new Date(image.created_at).toLocaleDateString()}
                      </Text>
                    </div>
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </Card>

      {/* Image Detail Modal */}
      <Modal
        open={showImageModal}
        onCancel={() => setShowImageModal(false)}
        footer={[
          <Button
            key="download"
            icon={<Download className="h-4 w-4" />}
            onClick={() => {
              if (selectedImage?.image_url) {
                const link = document.createElement("a");
                link.href = selectedImage.image_url;
                link.download = `${
                  selectedImage.name || "emotional-visualization"
                }.png`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
              }
            }}
          >
            Save to Device
          </Button>,
          <Button key="close" onClick={() => setShowImageModal(false)}>
            Close
          </Button>,
        ]}
        width={800}
        title={selectedImage?.name || "Emotional Visualization"}
      >
        {selectedImage && (
          <div className="space-y-4">
            <Image
              src={selectedImage.image_url}
              alt={
                selectedImage.name ||
                selectedImage.prompt ||
                "Emotional visualization"
              }
              className="w-full"
            />
            <div className="space-y-3">
              {selectedImage.visual_prompt && (
                <div>
                  <Title level={5}>Visual Description</Title>
                  <Paragraph>{selectedImage.visual_prompt}</Paragraph>
                </div>
              )}

              {selectedImage.prompt &&
                selectedImage.prompt !== selectedImage.visual_prompt && (
                  <div>
                    <Title level={5}>Original Input</Title>
                    <Paragraph>{selectedImage.prompt}</Paragraph>
                  </div>
                )}

              <div className="flex flex-wrap gap-2">
                {selectedImage.emotion_type && (
                  <Tag color="purple">
                    {emotionalStyles.find(
                      (s) => s.value === selectedImage.emotion_type
                    )?.label || selectedImage.emotion_type}
                  </Tag>
                )}
                <Tag color="blue">
                  {new Date(selectedImage.created_at).toLocaleString()}
                </Tag>
                {selectedImage.metadata?.model_used && (
                  <Tag color="green">{selectedImage.metadata.model_used}</Tag>
                )}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
