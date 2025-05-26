'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Shield, 
  Trash2, 
  Lock, 
  CheckCircle, 
  AlertTriangle, 
  Eye,
  EyeOff,
  Clock,
  Database,
  Heart
} from 'lucide-react';

interface PIIItem {
  id: string;
  text: string;
  type: string;
  risk_level: 'high' | 'medium' | 'low';
  description: string;
  confidence: number;
}

interface MemoryWithPII {
  id: string;
  content: string;
  type: string;
  storage_type: 'short_term' | 'long_term';
  timestamp: string;
  memory_type: string;
  is_emotional_anchor?: boolean;
  pii_detected: PIIItem[];
  pii_summary: {
    types: string[];
    high_risk_count: number;
    medium_risk_count: number;
    low_risk_count: number;
  };
}

interface PrivacyOption {
  label: string;
  description: string;
  icon: string;
}

interface PrivacyReviewData {
  memories_with_pii: MemoryWithPII[];
  total_count: number;
  privacy_options: {
    remove_entirely: PrivacyOption;
    remove_pii_only: PrivacyOption;
    keep_original: PrivacyOption;
  };
}

const MemoryPrivacyManager: React.FC<{ userId: string }> = ({ userId }) => {
  const [privacyData, setPrivacyData] = useState<PrivacyReviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [choices, setChoices] = useState<Record<string, string>>({});
  const [showPIIDetails, setShowPIIDetails] = useState<Record<string, boolean>>({});
  const [results, setResults] = useState<any>(null);

  useEffect(() => {
    fetchPrivacyReview();
  }, [userId]);

  const fetchPrivacyReview = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/memory/privacy-review/${userId}`);
      const data = await response.json();
      setPrivacyData(data);
      
      // Initialize choices to 'keep_original' by default
      const initialChoices: Record<string, string> = {};
      data.memories_with_pii.forEach((memory: MemoryWithPII) => {
        initialChoices[memory.id] = 'keep_original';
      });
      setChoices(initialChoices);
    } catch (error) {
      console.error('Error fetching privacy review:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChoiceChange = (memoryId: string, choice: string) => {
    setChoices(prev => ({
      ...prev,
      [memoryId]: choice
    }));
  };

  const togglePIIDetails = (memoryId: string) => {
    setShowPIIDetails(prev => ({
      ...prev,
      [memoryId]: !prev[memoryId]
    }));
  };

  const applyPrivacyChoices = async () => {
    try {
      setProcessing(true);
      const response = await fetch(`/api/memory/apply-privacy-choices/${userId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(choices),
      });
      
      const results = await response.json();
      setResults(results);
      
      // Refresh the data
      await fetchPrivacyReview();
    } catch (error) {
      console.error('Error applying privacy choices:', error);
    } finally {
      setProcessing(false);
    }
  };

  const getRiskBadgeColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStorageIcon = (storageType: string, isAnchor?: boolean) => {
    if (isAnchor) return <Heart className="w-4 h-4 text-pink-500" />;
    if (storageType === 'short_term') return <Clock className="w-4 h-4 text-blue-500" />;
    return <Database className="w-4 h-4 text-purple-500" />;
  };

  const getChoiceIcon = (choice: string) => {
    switch (choice) {
      case 'remove_entirely': return <Trash2 className="w-4 h-4" />;
      case 'remove_pii_only': return <Lock className="w-4 h-4" />;
      case 'keep_original': return <CheckCircle className="w-4 h-4" />;
      default: return null;
    }
  };

  const getChoiceColor = (choice: string) => {
    switch (choice) {
      case 'remove_entirely': return 'border-red-200 bg-red-50 hover:bg-red-100';
      case 'remove_pii_only': return 'border-yellow-200 bg-yellow-50 hover:bg-yellow-100';
      case 'keep_original': return 'border-green-200 bg-green-50 hover:bg-green-100';
      default: return 'border-gray-200 bg-gray-50 hover:bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading privacy review...</span>
      </div>
    );
  }

  if (!privacyData || privacyData.total_count === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-green-600" />
            Privacy Review
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>
              No memories with sensitive information found. Your privacy is protected!
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-blue-600" />
            Memory Privacy Manager
          </CardTitle>
          <p className="text-sm text-gray-600">
            Review and manage {privacyData.total_count} memories containing sensitive information
          </p>
        </CardHeader>
      </Card>

      {results && (
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>
            Privacy choices applied successfully! 
            Removed: {results.summary.removed_entirely}, 
            PII Cleaned: {results.summary.pii_removed}, 
            Kept Original: {results.summary.kept_original}
          </AlertDescription>
        </Alert>
      )}

      <div className="space-y-4">
        {privacyData.memories_with_pii.map((memory) => (
          <Card key={memory.id} className="border-l-4 border-l-orange-400">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    {getStorageIcon(memory.storage_type, memory.is_emotional_anchor)}
                    <span className="text-sm font-medium">
                      {memory.is_emotional_anchor ? 'Emotional Anchor' : 
                       memory.storage_type === 'short_term' ? 'Short-term Memory' : 'Long-term Memory'}
                    </span>
                    <Badge variant="outline" className="text-xs">
                      {memory.memory_type}
                    </Badge>
                  </div>
                  
                  <p className="text-sm text-gray-700 mb-3">
                    {memory.content}
                  </p>

                  <div className="flex items-center gap-2 mb-3">
                    <AlertTriangle className="w-4 h-4 text-orange-500" />
                    <span className="text-sm font-medium">Sensitive Information Detected:</span>
                    {memory.pii_summary.high_risk_count > 0 && (
                      <Badge className={getRiskBadgeColor('high')}>
                        {memory.pii_summary.high_risk_count} High Risk
                      </Badge>
                    )}
                    {memory.pii_summary.medium_risk_count > 0 && (
                      <Badge className={getRiskBadgeColor('medium')}>
                        {memory.pii_summary.medium_risk_count} Medium Risk
                      </Badge>
                    )}
                    {memory.pii_summary.low_risk_count > 0 && (
                      <Badge className={getRiskBadgeColor('low')}>
                        {memory.pii_summary.low_risk_count} Low Risk
                      </Badge>
                    )}
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => togglePIIDetails(memory.id)}
                      className="ml-auto"
                    >
                      {showPIIDetails[memory.id] ? (
                        <>
                          <EyeOff className="w-4 h-4 mr-1" />
                          Hide Details
                        </>
                      ) : (
                        <>
                          <Eye className="w-4 h-4 mr-1" />
                          Show Details
                        </>
                      )}
                    </Button>
                  </div>

                  {showPIIDetails[memory.id] && (
                    <div className="bg-gray-50 p-3 rounded-md mb-3">
                      <h4 className="text-sm font-medium mb-2">Detected Sensitive Information:</h4>
                      <div className="space-y-2">
                        {memory.pii_detected.map((pii, index) => (
                          <div key={index} className="flex items-center justify-between text-sm">
                            <span className="font-mono bg-white px-2 py-1 rounded">
                              "{pii.text}"
                            </span>
                            <div className="flex items-center gap-2">
                              <Badge className={getRiskBadgeColor(pii.risk_level)}>
                                {pii.type}
                              </Badge>
                              <span className="text-gray-500">
                                {Math.round(pii.confidence * 100)}% confidence
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </CardHeader>

            <CardContent className="pt-0">
              <div className="space-y-3">
                <h4 className="text-sm font-medium">Choose how to handle this memory:</h4>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {Object.entries(privacyData.privacy_options).map(([key, option]) => (
                    <button
                      key={key}
                      type="button"
                      onClick={() => handleChoiceChange(memory.id, key)}
                      className={`w-full cursor-pointer p-3 border-2 rounded-lg text-left transition-all duration-200 ${
                        choices[memory.id] === key 
                          ? `${getChoiceColor(key)} border-current ring-2 ring-offset-2 ring-opacity-50 ring-${key === 'remove_entirely' ? 'red' : key === 'remove_pii_only' ? 'yellow' : 'green'}-400` 
                          : 'border-gray-200 bg-white hover:bg-gray-50 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        {getChoiceIcon(key)}
                        <span className="font-medium text-sm">{option.label}</span>
                      </div>
                      <p className="text-xs text-gray-600">{option.description}</p>
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="flex justify-center pt-4">
        <Button 
          onClick={applyPrivacyChoices}
          disabled={processing}
          className="px-8"
        >
          {processing ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Applying Choices...
            </>
          ) : (
            <>
              <Shield className="w-4 h-4 mr-2" />
              Apply Privacy Choices
            </>
          )}
        </Button>
      </div>
    </div>
  );
};

export default MemoryPrivacyManager; 