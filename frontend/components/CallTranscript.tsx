'use client';

import React, { useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { motion } from 'framer-motion';

const MotionCard = motion(Card);

interface CallTranscriptProps {
  transcript: string;
  isCallActive: boolean;
}

const CallTranscript: React.FC<CallTranscriptProps> = ({
  transcript,
  isCallActive
}) => {
  const transcriptRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the bottom when transcript updates
  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [transcript]);

  const container = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05
      }
    }
  };

  const textAnimation = {
    hidden: { opacity: 0, y: 5 },
    visible: { opacity: 1, y: 0 }
  };

  // Split transcript into lines for animation
  const transcriptLines = transcript.split(/\n+/).filter(line => line.trim());

  return (
    <MotionCard 
      className="w-full max-w-lg mx-auto backdrop-blur-sm bg-background/80 dark:bg-card/90 border-neutral-200/20 dark:border-neutral-800/50"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      whileHover={{ 
        boxShadow: "0 8px 30px rgba(0, 0, 0, 0.12)",
      }}
    >
      <CardHeader className="pb-2 bg-gradient-to-r from-background/80 to-background via-primary/5 dark:from-card/90 dark:to-card/90 dark:via-primary/10">
        <CardTitle className="flex items-center text-transparent bg-clip-text bg-gradient-to-r from-primary to-primary/80 dark:from-primary dark:to-primary/80">
          Call Transcript
          {isCallActive && (
            <motion.div
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 1.5, repeat: Infinity }}
            >
              <Badge variant="outline" className="ml-2 bg-green-100 text-green-800 border-green-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-700">
                <motion.span 
                  className="mr-1 h-2 w-2 rounded-full bg-green-500 dark:bg-emerald-400 inline-block"
                  animate={{ 
                    opacity: [1, 0.5, 1],
                    scale: [1, 1.2, 1] 
                  }}
                  transition={{ 
                    duration: 1.5, 
                    repeat: Infinity,
                    repeatType: "loop" 
                  }}
                ></motion.span>
                Live
              </Badge>
            </motion.div>
          )}
        </CardTitle>
      </CardHeader>
      
      <CardContent>
        <div 
          ref={transcriptRef}
          className="h-64 overflow-y-auto pr-1 custom-scrollbar"
        >
          {transcriptLines.length > 0 ? (
            <motion.div
              variants={container}
              initial="hidden"
              animate="visible"
              className="space-y-2"
            >
              {transcriptLines.map((line, index) => (
                <motion.p 
                  key={index}
                  variants={textAnimation}
                  className="text-foreground dark:text-foreground/90"
                >
                  {line}
                </motion.p>
              ))}
            </motion.div>
          ) : (
            <motion.div 
              className="flex items-center justify-center h-full"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
            >
              <div className="text-center">
                {isCallActive ? (
                  <motion.div
                    animate={{ 
                      opacity: [0.7, 1, 0.7] 
                    }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 mx-auto mb-3 text-muted-foreground/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    </svg>
                    <p className="text-muted-foreground">
                      Waiting for conversation...
                    </p>
                  </motion.div>
                ) : (
                  <div>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 mx-auto mb-3 text-muted-foreground/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                    <p className="text-muted-foreground">
                      No transcript available
                    </p>
                    <p className="text-muted-foreground/60 text-xs mt-2">
                      Start a conversation with Nura
                    </p>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </div>
      </CardContent>
    </MotionCard>
  );
};

// Add a style tag for custom scrollbar
const styleTag = document.createElement('style');
styleTag.textContent = `
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background-color: rgba(155, 155, 155, 0.5);
    border-radius: 20px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background-color: rgba(155, 155, 155, 0.7);
  }
`;
if (typeof document !== 'undefined') {
  document.head.appendChild(styleTag);
}

export default CallTranscript; 