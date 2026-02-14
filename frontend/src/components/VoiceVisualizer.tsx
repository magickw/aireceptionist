'use client';
import React, { useRef, useEffect, useState } from 'react';
import { Box, Typography } from '@mui/material';

interface VoiceVisualizerProps {
  isActive: boolean;
  isSpeaking?: boolean;
}

const VoiceVisualizer: React.FC<VoiceVisualizerProps> = ({ isActive, isSpeaking = false }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const [bars] = useState(() => 
    Array.from({ length: 32 }, () => Math.random() * 0.4 + 0.1)
  );
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const draw = () => {
      const { width, height } = canvas;
      ctx.clearRect(0, 0, width, height);
      
      if (!isActive) {
        // Draw idle state - flat bars
        const barWidth = width / bars.length;
        bars.forEach((bar, i) => {
          const barHeight = height * bar * 0.2;
          const x = i * barWidth;
          const y = (height - barHeight) / 2;
          
          ctx.fillStyle = 'rgba(100, 100, 100, 0.5)';
          ctx.fillRect(x + 1, y, barWidth - 2, barHeight);
        });
      } else if (isSpeaking) {
        // Animate bars when speaking
        bars.forEach((bar, i) => {
          // Randomize height for animation
          const randomFactor = Math.random() * 0.6 + 0.2;
          const barHeight = height * bar * randomFactor;
          
          // Gradient color based on height
          const intensity = randomFactor;
          const r = Math.floor(96 + intensity * 80);
          const g = Math.floor(165 + intensity * 90);
          const b = Math.floor(250);
          
          const barWidth = width / bars.length;
          const x = i * barWidth;
          const y = (height - barHeight) / 2;
          
          // Create gradient
          const gradient = ctx.createLinearGradient(0, y, 0, y + barHeight);
          gradient.addColorStop(0, `rgba(${r}, ${g}, ${b}, 0.9)`);
          gradient.addColorStop(0.5, `rgba(${r}, ${g}, ${b}, 0.6)`);
          gradient.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0.3)`);
          
          ctx.fillStyle = gradient;
          ctx.fillRect(x + 1, y, barWidth - 2, barHeight);
          
          // Round the tops
          ctx.beginPath();
          ctx.arc(x + barWidth / 2, y, (barWidth - 2) / 2, Math.PI, 0);
          ctx.fill();
        });
      } else {
        // Listening state - subtle animation
        const time = Date.now() / 1000;
        bars.forEach((bar, i) => {
          const wave = Math.sin(time * 2 + i * 0.3) * 0.15 + 0.5;
          const barHeight = height * bar * wave;
          
          const barWidth = width / bars.length;
          const x = i * barWidth;
          const y = (height - barHeight) / 2;
          
          ctx.fillStyle = 'rgba(96, 165, 250, 0.6)';
          ctx.fillRect(x + 1, y, barWidth - 2, barHeight);
        });
      }
      
      animationRef.current = requestAnimationFrame(draw);
    };
    
    draw();
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isActive, isSpeaking, bars]);
  
  return (
    <Box
      sx={{
        position: 'relative',
        width: '100%',
        height: 80,
        borderRadius: 2,
        overflow: 'hidden',
        background: isActive 
          ? 'linear-gradient(180deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%)'
          : 'rgba(30, 41, 59, 0.5)',
        border: '1px solid',
        borderColor: isActive ? 'primary.main' : 'divider',
        transition: 'all 0.3s ease',
      }}
    >
      <canvas
        ref={canvasRef}
        width={300}
        height={80}
        style={{
          width: '100%',
          height: '100%',
        }}
      />
      {!isActive && (
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            textAlign: 'center',
          }}
        >
          <Typography variant="caption" color="text.secondary">
            Voice Inactive
          </Typography>
        </Box>
      )}
      {isActive && !isSpeaking && (
        <Box
          sx={{
            position: 'absolute',
            top: 4,
            right: 8,
          }}
        >
          <Typography 
            variant="caption" 
            sx={{ 
              color: '#60a5fa',
              fontSize: '0.65rem',
              letterSpacing: 1,
              textTransform: 'uppercase'
            }}
          >
            Listening...
          </Typography>
        </Box>
      )}
      {isSpeaking && (
        <Box
          sx={{
            position: 'absolute',
            top: 4,
            right: 8,
          }}
        >
          <Typography 
            variant="caption" 
            sx={{ 
              color: '#34d399',
              fontSize: '0.65rem',
              letterSpacing: 1,
              textTransform: 'uppercase',
              fontWeight: 'bold'
            }}
          >
            Speaking
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default VoiceVisualizer;
