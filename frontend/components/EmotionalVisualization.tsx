'use client';

import React from 'react';
import Image from 'next/image';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { motion } from 'framer-motion';

const MotionCard = motion(Card);

interface EmotionalVisualizationProps {
  imageUrl: string | null;
  prompt: string | null;
  isLoading: boolean;
}

const EmotionalVisualization: React.FC<EmotionalVisualizationProps> = ({
  imageUrl,
  prompt,
  isLoading
}) => {
  return (
    <MotionCard 
      className="w-full max-w-lg mx-auto overflow-hidden backdrop-blur-sm bg-background/80 dark:bg-card/90 border-neutral-200/20 dark:border-neutral-800/50"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      whileHover={{ 
        boxShadow: "0 8px 30px rgba(0, 0, 0, 0.12)",
        y: -5
      }}
    >
      <CardHeader className="pb-2 bg-gradient-to-r from-background/80 to-background via-primary/5 dark:from-card/90 dark:to-card/90 dark:via-primary/10">
        <CardTitle className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-primary/80 dark:from-primary dark:to-primary/80">
          Emotional Visualization
        </CardTitle>
        {prompt && (
          <CardDescription className="italic text-foreground/80 dark:text-foreground/60">
            "{prompt}"
          </CardDescription>
        )}
      </CardHeader>
      
      <CardContent className="p-0">
        <div className="relative aspect-square w-full">
          {isLoading ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-muted dark:bg-muted/20">
              <motion.div 
                className="h-12 w-12"
                animate={{ 
                  rotate: 360,
                  borderRadius: ["20%", "20%", "50%", "50%", "20%"],
                }}
                transition={{ 
                  duration: 2,
                  ease: "linear",
                  repeat: Infinity 
                }}
              >
                <div className="w-full h-full rounded-full border-t-2 border-l-2 border-primary animate-spin"></div>
              </motion.div>
              <motion.p 
                className="mt-4 text-muted-foreground text-sm"
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                Creating visualization...
              </motion.p>
            </div>
          ) : imageUrl ? (
            <motion.div
              className="w-full h-full"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.7 }}
            >
              <Image
                src={imageUrl}
                alt="Emotional visualization"
                fill
                className="object-cover"
              />
            </motion.div>
          ) : (
            <div className="absolute inset-0 flex items-center justify-center bg-muted/30 dark:bg-muted/10">
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="text-center p-6"
              >
                <div className="mb-4 opacity-60">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <p className="text-muted-foreground dark:text-muted-foreground/80 text-sm">
                  No visualization generated yet
                </p>
                <p className="text-muted-foreground/60 dark:text-muted-foreground/50 text-xs mt-2">
                  Start a conversation to create your emotional landscape
                </p>
              </motion.div>
            </div>
          )}
        </div>
      </CardContent>
    </MotionCard>
  );
};

export default EmotionalVisualization; 