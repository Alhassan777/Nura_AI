'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Image from 'next/image';
import { ClientStorageService, CallData } from '@/services/storageService';
import { ImageGenerationService } from '@/services/imageGenerationService';
import { useUser } from '../../../providers';

export default function CallDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { userId } = useUser();
  const [call, setCall] = useState<CallData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'transcript' | 'summary' | 'image' | 'actions'>('summary');

  useEffect(() => {
    // Load call data on component mount
    const callId = params.id as string;
    if (!callId) {
      router.push('/dashboard');
      return;
    }

    const callData = ClientStorageService.getCall(callId);
    
    // Make sure this call belongs to the current user
    if (callData && callData.userId === userId) {
      setCall(callData);
    }
    
    setLoading(false);
  }, [params.id, router, userId]);

  // Function to regenerate image if needed
  const handleRegenerateImage = async () => {
    if (!call?.emotionalData) return;

    setLoading(true);
    try {
      const prompt = await ImageGenerationService.generateImagePrompt(call.emotionalData);
      const imageUrl = await ImageGenerationService.generateImage(prompt);
      
      // Update the call with the new image
      const updatedCall = { ...call, generatedImageUrl: imageUrl };
      ClientStorageService.saveCall(updatedCall);
      setCall(updatedCall);
    } catch (error) {
      console.error('Failed to regenerate image:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <p>Loading call data...</p>
      </div>
    );
  }

  if (!call) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <h1 className="text-2xl font-bold mb-4">Call Not Found</h1>
        <p>Sorry, we couldn't find this call or you don't have permission to access it.</p>
        <button
          onClick={() => router.push('/dashboard')}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">
          {call.emotionalData?.scene_title || 'Call Details'}
        </h1>
        <button
          onClick={() => router.push('/dashboard')}
          className="px-3 py-1 bg-gray-200 rounded-md hover:bg-gray-300"
        >
          Back
        </button>
      </div>
      
      <div className="text-sm text-gray-500 mb-6">
        {new Date(call.date).toLocaleString()}
      </div>
      
      {/* Tabs Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex -mb-px">
          <button
            className={`px-4 py-2 font-medium text-sm border-b-2 ${
              activeTab === 'summary'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('summary')}
          >
            Summary
          </button>
          <button
            className={`px-4 py-2 font-medium text-sm border-b-2 ${
              activeTab === 'transcript'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('transcript')}
          >
            Transcript
          </button>
          <button
            className={`px-4 py-2 font-medium text-sm border-b-2 ${
              activeTab === 'image'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('image')}
          >
            Generated Image
          </button>
          <button
            className={`px-4 py-2 font-medium text-sm border-b-2 ${
              activeTab === 'actions'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('actions')}
          >
            Actions
          </button>
        </nav>
      </div>
      
      {/* Tab Content */}
      <div className="bg-white rounded-lg p-6 shadow-sm">
        {activeTab === 'summary' && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Call Summary</h2>
            <div className="whitespace-pre-wrap">{call.summary}</div>
            
            {call.emotionalData && (
              <div className="mt-6 pt-6 border-t border-gray-200">
                <h3 className="text-md font-semibold mb-3">Emotional Data</h3>
                <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2 text-sm">
                  {Object.entries(call.emotionalData).map(([key, value]) => {
                    if (!value || (Array.isArray(value) && value.length === 0)) return null;
                    
                    return (
                      <div key={key} className="py-1">
                        <dt className="font-medium text-gray-500 capitalize">
                          {key.replace(/_/g, ' ')}
                        </dt>
                        <dd className="mt-1">
                          {Array.isArray(value) ? value.join(', ') : String(value)}
                        </dd>
                      </div>
                    );
                  })}
                </dl>
              </div>
            )}
          </div>
        )}
        
        {activeTab === 'transcript' && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Call Transcript</h2>
            <div className="whitespace-pre-wrap bg-gray-50 p-4 rounded-md">
              {call.transcript || 'No transcript available'}
            </div>
          </div>
        )}
        
        {activeTab === 'image' && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Generated Image</h2>
            {call.generatedImageUrl ? (
              <div className="flex flex-col items-center">
                <div className="relative w-full max-w-lg h-80 mb-4">
                  <Image
                    src={call.generatedImageUrl}
                    alt="Generated from call data"
                    fill
                    style={{ objectFit: 'contain' }}
                  />
                </div>
                <button
                  onClick={handleRegenerateImage}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  disabled={loading}
                >
                  {loading ? 'Regenerating...' : 'Regenerate Image'}
                </button>
              </div>
            ) : (
              <div className="text-center py-10">
                <p className="mb-4">No image has been generated for this call.</p>
                <button
                  onClick={handleRegenerateImage}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  disabled={loading || !call.emotionalData}
                >
                  {loading ? 'Generating...' : 'Generate Image'}
                </button>
              </div>
            )}
          </div>
        )}
        
        {activeTab === 'actions' && (
          <div>
            <h2 className="text-lg font-semibold mb-4">Actions</h2>
            <div className="space-y-4">
              <button
                onClick={() => {
                  if (window.confirm('Are you sure you want to export this call data?')) {
                    const dataStr = JSON.stringify(call, null, 2);
                    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
                    
                    const linkElement = document.createElement('a');
                    linkElement.setAttribute('href', dataUri);
                    linkElement.setAttribute('download', `call-${call.id}.json`);
                    linkElement.click();
                  }
                }}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Export Call Data
              </button>
              
              {/* Additional actions can be added here */}
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 