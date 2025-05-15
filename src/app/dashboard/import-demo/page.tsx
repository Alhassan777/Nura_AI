'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ClientStorageService, CallData } from '@/services/storageService';
import { v4 as uuidv4 } from 'uuid';
import { useUser } from '../../providers';

// Example call data based on the sample in the request
const DEMO_CALL_DATA = {
  transcript: "Hello? Yeah. My my pronouns are she, her. I don't have anything right now. Yeah. Just the c. You kn...",
  Analysis: `# Session Summary 
  
  This was a brief, tentative interaction where the user engaged minimally. The user identified with she/her pronouns and expressed physical discomfort ("my butt hurts"). The session had a hesitant quality, with the user seeming uncertain or perhaps not fully ready to engage in deeper reflection. The conversation remained at a surface level, with the user ultimately deciding to conclude the session after minimal exploration.`,
  Data: {
    body_locus: "lower body",
    transcript: "Hello? Yeah. My my pronouns are she, her. I don't have anything right now. Yeah. Just the c. You kn...",
    scene_title: "Momentary Pause",
    sketch_shape: "curved lines with slight disruption",
    temporal_tag: "new",
    color_palette: [
      "muted blue",
      "soft gray",
      "pale beige"
    ],
    sketch_motion: "gentle rippling",
    cognitive_load: "low",
    ground_emotion: "discomfort",
    metaphor_prompt: "A foggy shoreline where small waves lap against the sand, with a figure sitting briefly before moving on",
    temp_descriptor: "cool",
    scene_description: "A person pausing briefly on a bench, slightly uncomfortable, before continuing on their journey",
    texture_descriptor: "slightly rough"
  }
};

export default function ImportDemoPage() {
  const router = useRouter();
  const { userId } = useUser();
  const [importing, setImporting] = useState(false);
  const [imported, setImported] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const handleImport = async () => {
    setImporting(true);
    setError(null);
    
    try {
      // Create a few demo calls with different timestamps
      const now = new Date();
      
      // First call - just now
      await importDemoCall(now, DEMO_CALL_DATA);
      
      // Second call - 1 day ago
      const yesterday = new Date(now);
      yesterday.setDate(yesterday.getDate() - 1);
      await importDemoCall(yesterday, {
        ...DEMO_CALL_DATA,
        Data: {
          ...DEMO_CALL_DATA.Data,
          scene_title: "Brief Hesitation",
          ground_emotion: "uncertainty",
          color_palette: ["deep blue", "muted gray", "soft green"]
        }
      });
      
      // Third call - 3 days ago
      const threeDaysAgo = new Date(now);
      threeDaysAgo.setDate(threeDaysAgo.getDate() - 3);
      await importDemoCall(threeDaysAgo, {
        ...DEMO_CALL_DATA,
        Data: {
          ...DEMO_CALL_DATA.Data,
          scene_title: "Quiet Reflection",
          ground_emotion: "contemplation",
          body_locus: "chest",
          color_palette: ["warm amber", "deep purple", "forest green"]
        }
      });
      
      setImported(true);
      setTimeout(() => {
        router.push('/dashboard');
      }, 2000);
    } catch (err) {
      console.error('Failed to import demo data:', err);
      setError('Failed to import demo data. See console for details.');
    } finally {
      setImporting(false);
    }
  };
  
  // Helper function to import a single demo call
  const importDemoCall = async (date: Date, callData: any) => {
    // Extract data from the Vapi response format
    const { transcript, Analysis, Data } = callData;
    
    // Create an image URL for demo purposes
    const imageUrl = `https://picsum.photos/seed/${encodeURIComponent(Data.scene_title || '')}/800/600`;
    
    // Determine the temporal tag value correctly
    let temporalTag: 'new' | 'familiar' | undefined;
    if (Data.temporal_tag === 'new') {
      temporalTag = 'new';
    } else if (Data.temporal_tag === 'familiar') {
      temporalTag = 'familiar';
    }
    
    // Create the call data object
    const call: CallData = {
      id: uuidv4(),
      userId: userId,
      date: date.toISOString(),
      transcript,
      summary: Analysis,
      emotionalData: {
        body_locus: Data.body_locus || '',
        scene_title: Data.scene_title || '',
        sketch_shape: Data.sketch_shape || '',
        temporal_tag: temporalTag,
        color_palette: Array.isArray(Data.color_palette) ? Data.color_palette : [],
        sketch_motion: Data.sketch_motion || '',
        cognitive_load: Data.cognitive_load || '',
        ground_emotion: Data.ground_emotion || '',
        metaphor_prompt: Data.metaphor_prompt || '',
        temp_descriptor: Data.temp_descriptor || '',
        scene_description: Data.scene_description || '',
        texture_descriptor: Data.texture_descriptor || '',
      },
      generatedImageUrl: imageUrl,
    };
    
    // Save to storage
    ClientStorageService.saveCall(call);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Import Demo Data</h1>
      
      <div className="bg-white rounded-lg p-6 shadow-sm max-w-lg mx-auto">
        <p className="mb-4">
          This utility will import some demo call data into your dashboard for testing purposes.
        </p>
        
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-md mb-4">
            {error}
          </div>
        )}
        
        {imported ? (
          <div className="bg-green-50 border border-green-200 text-green-700 p-4 rounded-md">
            Demo data imported successfully! Redirecting to dashboard...
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <button
              onClick={handleImport}
              disabled={importing}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-blue-300"
            >
              {importing ? 'Importing...' : 'Import Demo Data'}
            </button>
            
            <button
              onClick={() => router.push('/dashboard')}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  );
} 