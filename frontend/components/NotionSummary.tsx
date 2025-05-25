'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';

interface NotionSummaryProps {
  summary: string | null;
  onSaveToNotion: () => Promise<string>;
  disabled: boolean;
}

const NotionSummary: React.FC<NotionSummaryProps> = ({
  summary,
  onSaveToNotion,
  disabled
}) => {
  const [isSaving, setIsSaving] = useState(false);
  const [notionUrl, setNotionUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSaveToNotion = async () => {
    if (!summary) return;
    
    setIsSaving(true);
    setError(null);
    
    try {
      const url = await onSaveToNotion();
      setNotionUrl(url);
    } catch (err) {
      console.error('Error saving to Notion:', err);
      setError('Failed to save to Notion. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Card className="w-full max-w-lg mx-auto">
      <CardHeader>
        <CardTitle>Session Summary</CardTitle>
        <CardDescription>
          A complete summary of your reflection session
        </CardDescription>
      </CardHeader>
      
      <CardContent className="max-h-64 overflow-y-auto">
        {summary ? (
          <div className="prose prose-sm max-w-none">
            <div dangerouslySetInnerHTML={{ __html: summary.replace(/\n/g, '<br/>') }} />
          </div>
        ) : (
          <div className="flex items-center justify-center h-32">
            <p className="text-muted-foreground text-sm">
              No summary available yet
            </p>
          </div>
        )}
      </CardContent>
      
      <CardFooter className="flex-col items-stretch gap-3 bg-muted/50 border-t">
        {notionUrl ? (
          <div className="flex flex-col space-y-3">
            <Badge variant="outline" className="bg-green-100 text-green-800 border-green-200 self-start">
              Successfully saved to Notion!
            </Badge>
            <Button 
              variant="outline"
              size="sm"
              className="text-primary flex items-center gap-2"
              asChild
            >
              <a 
                href={notionUrl} 
                target="_blank" 
                rel="noopener noreferrer"
              >
                <svg 
                  xmlns="http://www.w3.org/2000/svg" 
                  className="h-4 w-4" 
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke="currentColor"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" 
                  />
                </svg>
                View in Notion
              </a>
            </Button>
          </div>
        ) : (
          <Button
            onClick={handleSaveToNotion}
            disabled={disabled || isSaving || !summary}
            className="w-full"
            variant={disabled || isSaving || !summary ? "secondary" : "default"}
          >
            {isSaving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                <span>Saving to Notion...</span>
              </>
            ) : (
              <>
                <svg className="h-5 w-5 mr-2" viewBox="0 0 40 40" fill="currentColor">
                  <path d="M33.5,40h-27C2.9,40,0,37.1,0,33.5v-27C0,2.9,2.9,0,6.5,0h27C37.1,0,40,2.9,40,6.5v27C40,37.1,37.1,40,33.5,40z M6.5,2 C4,2,2,4,2,6.5v27C2,36,4,38,6.5,38h27c2.5,0,4.5-2,4.5-4.5v-27C38,4,36,2,33.5,2H6.5z" />
                  <path d="M31.9,10.1l-10-0.9c-0.2,0-0.5,0-0.7,0.1l-3.8,1.3l-7.7,0.5c-1.3,0.1-2.4,1.1-2.6,2.4L6.1,21c-0.1,0.7,0.4,1.5,1.2,1.5 c0.6,0,1.1-0.4,1.2-1l0.2-1.1l1,0.1l-0.4,6.6c-0.1,1.2,0.6,2.3,1.8,2.7l5.1,1.4c0.2,0.1,0.5,0.1,0.7,0.1c0.4,0,0.8-0.1,1.2-0.3 l15.2-8.3c0.5-0.3,0.8-0.8,0.8-1.4l-0.1-9.8C34.1,10.8,33.1,10.2,31.9,10.1z M29.3,21.5l-7,3.9c-0.2,0.1-0.4,0.2-0.6,0.2 c-0.1,0-0.3,0-0.4,0c-1.1-0.3-2.9-1-5.1-1.9L29.2,13V21.5z" />
                </svg>
                <span>Save to Notion</span>
              </>
            )}
          </Button>
        )}
        
        {error && (
          <p className="text-destructive text-sm">{error}</p>
        )}
      </CardFooter>
    </Card>
  );
};

export default NotionSummary; 