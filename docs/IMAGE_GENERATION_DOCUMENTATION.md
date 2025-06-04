# Image Generation Feature Documentation

## Overview

This document outlines the implementation of the AI-powered image generation feature for the Nura app, which allows users to create visual representations of their emotions and thoughts using AI image generation.

## Features Implemented

### 1. **Database Model**

- **New Table**: `generated_images`
- **Purpose**: Store generated images with metadata for each user
- **Security**: User-scoped access only (users can only access their own images)

### 2. **Image Generation Pipeline**

- **AI Integration**: Uses Hugging Face FLUX.1-dev model for image generation
- **Context-Aware**: Leverages user's short-term and long-term memory for richer context
- **Emotion Analysis**: Automatically detects emotion types and optimizes generation parameters
- **Auto-Naming**: Gemini LLM suggests descriptive names for generated images

### 3. **API Endpoints**

Comprehensive REST API for image management with full CRUD operations and advanced search.

### 4. **Authentication & Security**

- JWT-based authentication for all endpoints
- User-scoped access control
- Resource ownership validation

## Database Schema Changes

### New Table: `generated_images`

```sql
CREATE TABLE generated_images (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR NULL,
    prompt TEXT NOT NULL,
    image_data TEXT NOT NULL, -- base64 or URL to file
    image_format VARCHAR DEFAULT 'png',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_generated_images_user ON generated_images(user_id);
CREATE INDEX idx_generated_images_created ON generated_images(created_at);
CREATE INDEX idx_generated_images_name ON generated_images(name);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_generated_images_updated_at
    BEFORE UPDATE ON generated_images
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### Metadata Structure

The `metadata` JSONB field stores:

```json
{
  "emotion_type": "calm|energetic|mysterious|hopeful|melancholic",
  "generation_params": {
    "guidance_scale": 7.5,
    "num_inference_steps": 50,
    "width": 1024,
    "height": 1024
  },
  "context_analysis": {
    "richness_score": 2,
    "visual_keywords": ["..."],
    "emotional_keywords": ["..."]
  },
  "model_used": "FLUX.1-dev"
}
```

## API Endpoints

### Base URL: `/image-generation`

#### 1. **Generate Image**

- **Endpoint**: `POST /generate`
- **Authentication**: Required
- **Purpose**: Generate a new image from user input

**Request Body**:

```json
{
  "user_input": "I'm feeling peaceful, like a sunset over calm waters",
  "include_long_term_memory": false,
  "save_locally": false,
  "identified_emotion": "calm",
  "name": "My Peaceful Sunset" // Optional
}
```

**Response**:

```json
{
    "success": true,
    "image_data": "base64_encoded_image_data",
    "image_format": "png",
    "visual_prompt": "A serene sunset over calm waters...",
    "emotion_type": "calm",
    "context_analysis": {...},
    "created_at": "2024-01-01T12:00:00Z"
}
```

#### 2. **List Images**

- **Endpoint**: `GET /images`
- **Authentication**: Required
- **Purpose**: List user's generated images with advanced search

**Query Parameters**:

- `name`: Fuzzy search by image name
- `prompt`: Fuzzy search by generation prompt
- `emotion_type`: Filter by emotion type
- `created_from`: Date filter (YYYY-MM-DD)
- `created_to`: Date filter (YYYY-MM-DD)

**Example**:

```
GET /images?name=sunset dream&emotion_type=calm&created_from=2024-06-01
```

#### 3. **Get Specific Image**

- **Endpoint**: `GET /images/{image_id}`
- **Authentication**: Required
- **Purpose**: Retrieve a specific image by ID

#### 4. **Update Image Name**

- **Endpoint**: `PATCH /images/{image_id}/name`
- **Authentication**: Required
- **Body**: `{"name": "New Image Name"}`

#### 5. **Update Image Metadata**

- **Endpoint**: `PATCH /images/{image_id}/metadata`
- **Authentication**: Required
- **Body**: `{"metadata": {...}}`

#### 6. **Delete Image**

- **Endpoint**: `DELETE /images/{image_id}`
- **Authentication**: Required
- **Response**: `{"success": true, "message": "Image deleted."}`

#### 7. **Validate Input**

- **Endpoint**: `POST /validate`
- **Authentication**: Required
- **Purpose**: Check if user input is suitable for image generation

#### 8. **Get Generation Status**

- **Endpoint**: `GET /status/{user_id}`
- **Authentication**: Required
- **Purpose**: Check service availability and estimated generation times

## Technical Implementation

### 1. **Image Generation Pipeline**

```python
# Flow:
1. Build context from user input + memory
2. Generate visual prompt + suggested name using Gemini LLM
3. Analyze emotion type for optimal generation parameters
4. Generate image using FLUX.1-dev model
5. Store in database with metadata
6. Return result to user
```

### 2. **Context Building**

- **Short-term memory**: Recent conversation messages
- **Long-term memory**: Important user memories and preferences
- **Emotional anchors**: Key emotional themes
- **Input analysis**: Richness score and keyword extraction

### 3. **Emotion Detection**

Automatically detects emotion types based on keywords:

- **Calm**: peaceful, serene, quiet, gentle
- **Energetic**: excited, dynamic, vibrant, active
- **Mysterious**: unknown, hidden, fog, shadow
- **Hopeful**: bright, light, sunrise, future
- **Melancholic**: sad, gray, heavy, nostalgic

### 4. **Advanced Search Features**

- **Fuzzy Search**: Handles partial matches and word order variations
- **Date Filtering**: Precise date range queries
- **Metadata Filtering**: Filter by emotion type and other metadata
- **Performance**: Indexed queries for fast retrieval

## Security & Privacy

### 1. **Access Control**

- All endpoints require JWT authentication
- Users can only access their own images
- Resource ownership verified on every request

### 2. **Data Storage**

- Images stored as base64 in database (configurable to file storage)
- User-scoped data with CASCADE DELETE on user removal
- Metadata stored in structured JSONB format

### 3. **Input Validation**

- Comprehensive input validation on all endpoints
- Date format validation for search parameters
- Content validation for image generation

## Usage Examples

### 1. **Generate an Image**

```bash
curl -X POST "/image-generation/generate" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "I feel like I am floating in a dream",
    "name": "Floating Dream"
  }'
```

### 2. **Search Images**

```bash
# Find all calm images from June 2024 with "sunset" in name
curl -X GET "/image-generation/images?emotion_type=calm&name=sunset&created_from=2024-06-01&created_to=2024-06-30" \
  -H "Authorization: Bearer <jwt_token>"
```

### 3. **Update Image Name**

```bash
curl -X PATCH "/image-generation/images/{image_id}/name" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "My New Image Name"}'
```

## Performance Considerations

### 1. **Database Indexes**

- User ID index for fast user-scoped queries
- Creation date index for date range filtering
- Name index for fuzzy search performance

### 2. **Image Generation**

- Asynchronous processing for non-blocking API responses
- Retry logic for model loading scenarios
- Configurable generation parameters per emotion type

### 3. **Memory Usage**

- Efficient context building with configurable memory limits
- Large context support leveraging Gemini's million-token capacity

## Future Enhancements

### 1. **Potential Features**

- Image variations and regeneration
- Style transfer options
- Batch image generation
- Image sharing and social features
- Export to different formats

### 2. **Performance Optimizations**

- File storage for images (vs. base64 in DB)
- CDN integration for image delivery
- Caching for frequently accessed images
- Pagination for large image lists

### 3. **AI Enhancements**

- Multiple AI model support
- Custom style training
- Enhanced emotion detection
- Collaborative filtering for recommendations
