"use client";

import React, { useState } from "react";
import {
  Card,
  Button,
  Input,
  Select,
  Image,
  Modal,
  Typography,
  Space,
  Row,
  Col,
  Tag,
  Empty,
} from "antd";
import {
  Heart,
  Palette,
  Download,
  Eye,
  Sparkles,
  Camera,
  BookOpen,
} from "lucide-react";
import {
  useImageGeneration,
  useImageHistory,
} from "@/services/hooks/use-image-generation";

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;

export default function SoulGalleryPage() {
  const [prompt, setPrompt] = useState("");
  const [style, setStyle] = useState("emotional");
  const [selectedImage, setSelectedImage] = useState<any>(null);
  const [showImageModal, setShowImageModal] = useState(false);

  const { mutate: generateImage, isPending: isGenerating } =
    useImageGeneration();
  const { data: imageHistory, isLoading: isLoadingHistory } = useImageHistory();

  const handleGenerateImage = () => {
    if (prompt.trim()) {
      generateImage({
        prompt: `Emotional visualization of: ${prompt}`,
        style,
        size: "1024x1024",
      });
    }
  };

  const emotionalStyles = [
    {
      value: "emotional",
      label: "Emotional Abstract",
      description: "Flowing colors representing feelings",
    },
    {
      value: "symbolic",
      label: "Symbolic Imagery",
      description: "Metaphorical representations",
    },
    {
      value: "peaceful",
      label: "Peaceful Landscapes",
      description: "Calming, serene environments",
    },
    {
      value: "inner-light",
      label: "Inner Light",
      description: "Luminous, spiritual imagery",
    },
    {
      value: "growth",
      label: "Personal Growth",
      description: "Imagery of transformation and healing",
    },
    {
      value: "memories",
      label: "Memory Fragments",
      description: "Dreamlike, nostalgic scenes",
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
        Transform your inner emotions, thoughts, and reflections into beautiful
        visual art. Create symbolic representations of your mental and emotional
        journey.
      </Paragraph>

      {/* Creation Section */}
      <Card
        title={
          <div className="flex items-center gap-2">
            <Palette className="h-5 w-5" />
            <span>Visualize Your Inner World</span>
          </div>
        }
      >
        <Space direction="vertical" className="w-full" size="large">
          <div>
            <Text strong>
              Describe your current emotion, thought, or reflection:
            </Text>
            <TextArea
              placeholder="e.g., 'I feel like a butterfly emerging from a cocoon' or 'My anxiety feels like storm clouds with silver linings'"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={3}
              className="mt-2"
            />
          </div>

          <div>
            <Text strong>Artistic Style:</Text>
            <Select
              value={style}
              onChange={setStyle}
              className="w-full mt-2"
              placeholder="Choose how to visualize your inner state"
            >
              {emotionalStyles.map((styleOption) => (
                <Option key={styleOption.value} value={styleOption.value}>
                  <div>
                    <div className="font-medium">{styleOption.label}</div>
                    <div className="text-xs text-gray-500">
                      {styleOption.description}
                    </div>
                  </div>
                </Option>
              ))}
            </Select>
          </div>

          <Button
            type="primary"
            size="large"
            icon={<Sparkles className="h-4 w-4" />}
            onClick={handleGenerateImage}
            loading={isGenerating}
            disabled={!prompt.trim()}
            className="w-full"
          >
            {isGenerating
              ? "Creating Your Soul Art..."
              : "Visualize My Inner State"}
          </Button>
        </Space>
      </Card>

      {/* Gallery Section */}
      <Card
        title={
          <div className="flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            <span>Your Soul Gallery</span>
          </div>
        }
      >
        {isLoadingHistory ? (
          <div className="text-center py-8">Loading your gallery...</div>
        ) : !imageHistory || imageHistory.length === 0 ? (
          <Empty
            description="Your soul gallery is empty. Create your first emotional visualization above."
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
                        alt={image.prompt}
                        className="w-full h-48 object-cover"
                        preview={false}
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
                          View
                        </Button>
                      </div>
                    </div>
                  }
                  size="small"
                >
                  <div className="space-y-2">
                    <Text className="text-sm line-clamp-2">{image.prompt}</Text>
                    <div className="flex items-center justify-between">
                      <Tag color="purple" className="text-xs">
                        {emotionalStyles.find((s) => s.value === image.style)
                          ?.label || image.style}
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
          <Button key="download" icon={<Download className="h-4 w-4" />}>
            Save to Device
          </Button>,
          <Button key="close" onClick={() => setShowImageModal(false)}>
            Close
          </Button>,
        ]}
        width={800}
      >
        {selectedImage && (
          <div className="space-y-4">
            <Image
              src={selectedImage.image_url}
              alt={selectedImage.prompt}
              className="w-full"
            />
            <div>
              <Title level={4}>Emotional Reflection</Title>
              <Paragraph>{selectedImage.prompt}</Paragraph>
              <div className="flex gap-2">
                <Tag color="purple">{selectedImage.style}</Tag>
                <Tag color="blue">
                  {new Date(selectedImage.created_at).toLocaleString()}
                </Tag>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
