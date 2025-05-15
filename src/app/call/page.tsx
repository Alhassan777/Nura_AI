'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { MicOffIcon, MicIcon, PhoneOffIcon } from 'lucide-react';

// Simulate a voice waveform
function VoiceWaveform() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  
  // Set up canvas dimensions
  useEffect(() => {
    const handleResize = () => {
      setDimensions({
        width: window.innerWidth,
        height: window.innerHeight
      });
    };
    
    window.addEventListener('resize', handleResize);
    handleResize();
    
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  // Draw waveform
  useEffect(() => {
    if (!canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    canvas.width = dimensions.width;
    canvas.height = dimensions.height;
    
    let animationId: number;
    let points: { x: number; y: number; originY: number; intensity: number; }[] = [];
    
    // Initialize points for the wave
    const initializePoints = () => {
      points = [];
      const numberOfPoints = Math.floor(dimensions.width / 30);
      const spacing = dimensions.width / numberOfPoints;
      
      for (let i = 0; i < numberOfPoints; i++) {
        points.push({
          x: i * spacing,
          y: dimensions.height / 2,
          originY: dimensions.height / 2,
          intensity: Math.random() * 0.5 + 0.3,
        });
      }
    };
    
    // Draw wave function
    const drawWave = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Update points
      points.forEach(point => {
        const randomY = (Math.random() - 0.5) * 50 * point.intensity;
        point.y = point.originY + randomY;
      });
      
      // Create gradient
      const gradient = ctx.createLinearGradient(0, 0, dimensions.width, 0);
      gradient.addColorStop(0, 'rgba(110, 231, 183, 0.4)');  // Light teal (adjust colors as needed)
      gradient.addColorStop(0.5, 'rgba(79, 70, 229, 0.4)');  // Indigo (adjust colors as needed)
      gradient.addColorStop(1, 'rgba(236, 72, 153, 0.4)');   // Pink (adjust colors as needed)
      
      // Draw wave
      ctx.beginPath();
      ctx.moveTo(0, dimensions.height / 2);
      
      // Draw first point
      ctx.lineTo(points[0].x, points[0].y);
      
      // Draw curve through points
      for (let i = 0; i < points.length - 1; i++) {
        const xc = (points[i].x + points[i + 1].x) / 2;
        const yc = (points[i].y + points[i + 1].y) / 2;
        ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
      }
      
      // Draw last point
      ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
      ctx.lineTo(dimensions.width, dimensions.height / 2);
      
      // Close path and fill
      ctx.lineTo(dimensions.width, dimensions.height);
      ctx.lineTo(0, dimensions.height);
      ctx.closePath();
      
      ctx.fillStyle = gradient;
      ctx.fill();
      
      // Create line gradient
      const lineGradient = ctx.createLinearGradient(0, 0, dimensions.width, 0);
      lineGradient.addColorStop(0, 'rgba(110, 231, 183, 0.8)');
      lineGradient.addColorStop(0.5, 'rgba(79, 70, 229, 0.8)');
      lineGradient.addColorStop(1, 'rgba(236, 72, 153, 0.8)');
      
      // Draw line on top
      ctx.beginPath();
      ctx.moveTo(0, dimensions.height / 2);
      
      // Draw first point for line
      ctx.lineTo(points[0].x, points[0].y);
      
      // Draw curve through points for line
      for (let i = 0; i < points.length - 1; i++) {
        const xc = (points[i].x + points[i + 1].x) / 2;
        const yc = (points[i].y + points[i + 1].y) / 2;
        ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
      }
      
      // Draw last point for line
      ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
      ctx.lineTo(dimensions.width, dimensions.height / 2);
      
      ctx.strokeStyle = lineGradient;
      ctx.lineWidth = 2;
      ctx.stroke();
      
      animationId = requestAnimationFrame(drawWave);
    };
    
    initializePoints();
    drawWave();
    
    return () => {
      cancelAnimationFrame(animationId);
    };
  }, [dimensions]);
  
  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 z-0"
    />
  );
}

export default function CallPage() {
  const router = useRouter();
  const [isMuted, setIsMuted] = useState(false);
  const [callDuration, setCallDuration] = useState(0);
  const [isCallEnding, setIsCallEnding] = useState(false);
  
  // Simulate call duration
  useEffect(() => {
    const timer = setInterval(() => {
      setCallDuration(prev => prev + 1);
    }, 1000);
    
    return () => clearInterval(timer);
  }, []);
  
  // Format time as mm:ss
  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };
  
  // Handle call ending
  const handleEndCall = () => {
    setIsCallEnding(true);
    
    // Generate a random call ID - in a real app this would be from the real call
    const callId = Math.random().toString(36).substring(2, 15);
    
    // Simulate ending delay
    setTimeout(() => {
      router.push(`/dashboard/call/${callId}`);
    }, 1000);
  };
  
  return (
    <div className="relative min-h-screen overflow-hidden bg-background dark:bg-card">
      {/* Wave visualization background */}
      <VoiceWaveform />
      
      {/* Overlay with call status */}
      <div className="absolute inset-0 z-10 flex flex-col items-center">
        {/* Call info */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mt-20 text-center"
        >
          <h1 className="text-4xl font-bold mb-2 text-primary">Nura</h1>
          <p className="text-muted-foreground">Call in progress</p>
          <div className="mt-4 px-4 py-1 rounded-full bg-primary/10 text-primary inline-block">
            {formatTime(callDuration)}
          </div>
        </motion.div>
        
        {/* Call controls */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mt-auto mb-20 flex items-center space-x-8"
        >
          <Button 
            variant="outline" 
            size="icon" 
            className="h-16 w-16 rounded-full border-2 border-primary/20 bg-background/80 backdrop-blur-sm shadow-lg"
            onClick={() => setIsMuted(!isMuted)}
          >
            {isMuted ? (
              <MicOffIcon size={24} className="text-red-500" />
            ) : (
              <MicIcon size={24} className="text-primary" />
            )}
          </Button>
          
          <Button 
            variant="destructive" 
            size="icon" 
            className="h-16 w-16 rounded-full shadow-lg hover:bg-red-600 transition-colors"
            onClick={handleEndCall}
            disabled={isCallEnding}
          >
            <PhoneOffIcon size={24} />
          </Button>
        </motion.div>
      </div>
      
      {/* Status message for ending call */}
      {isCallEnding && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 z-20 bg-background/80 backdrop-blur-sm flex items-center justify-center"
        >
          <div className="text-center">
            <div className="mb-4 w-12 h-12 border-t-4 border-primary rounded-full animate-spin mx-auto"></div>
            <p className="text-xl">Ending call...</p>
          </div>
        </motion.div>
      )}
    </div>
  );
} 