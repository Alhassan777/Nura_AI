'use client';

import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { motion, AnimatePresence } from 'framer-motion';

interface PhoneButtonProps {
  onStartCall: () => void;
  onEndCall: () => void;
  isCallActive: boolean;
  volume?: number;
}

const PhoneButton: React.FC<PhoneButtonProps> = ({
  onStartCall,
  onEndCall,
  isCallActive,
  volume = 0
}) => {
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (isCallActive) {
      const interval = setInterval(() => {
        setIsAnimating(prev => !prev);
      }, 1000);
      return () => clearInterval(interval);
    } else {
      setIsAnimating(false);
    }
  }, [isCallActive]);

  const handleClick = () => {
    if (isCallActive) {
      onEndCall();
    } else {
      onStartCall();
    }
  };

  const volumeSize = Math.max(20, Math.min(100, volume * 100)) + '%';

  return (
    <div className="relative flex items-center justify-center p-10">
      <AnimatePresence>
        {isCallActive && (
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ 
              scale: [1, 1.2, 1], 
              opacity: [0.2, 0.3, 0.2],
              rotate: [0, 5, 0, -5, 0]
            }}
            exit={{ scale: 0, opacity: 0 }}
            transition={{ 
              duration: 2, 
              repeat: Infinity,
              repeatType: "reverse" 
            }}
            className="absolute rounded-full bg-primary/20 dark:bg-primary/30 backdrop-blur-sm"
            style={{ 
              width: volumeSize, 
              height: volumeSize 
            }}
          />
        )}
      </AnimatePresence>
      
      <motion.div
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        transition={{ type: "spring", stiffness: 400, damping: 17 }}
      >
        <Button
          variant={isCallActive ? "destructive" : "default"}
          size="lg"
          className={`rounded-full w-20 h-20 transition-all duration-300 transform relative shadow-[0_0_15px_rgba(0,0,0,0.2)] dark:shadow-[0_0_20px_rgba(255,255,255,0.1)] 
            ${isCallActive ? 'bg-red-500 hover:bg-red-600 dark:bg-red-600 dark:hover:bg-red-700' : 
            'bg-emerald-500 hover:bg-emerald-600 dark:bg-emerald-600 dark:hover:bg-emerald-700'}`}
          onClick={handleClick}
          aria-label={isCallActive ? "End call" : "Start call"}
        >
          <motion.div
            animate={isAnimating ? {
              scale: [1, 1.1, 1],
            } : { scale: 1 }}
            transition={{ duration: 0.5, repeat: isAnimating ? Infinity : 0 }}
          >
            {isCallActive ? (
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                className="h-8 w-8" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M6 18L18 6M6 6l12 12" 
                />
              </svg>
            ) : (
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                className="h-8 w-8" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 7V5z"
                />
              </svg>
            )}
          </motion.div>
        </Button>
      </motion.div>
    </div>
  );
};

export default PhoneButton; 