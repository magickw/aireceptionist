'use client';
import { useRef, useState, useCallback, useEffect } from 'react';

interface UseVoiceStreamingOptions {
  wsRef: React.RefObject<WebSocket | null>;
  onPlaybackStart?: () => void;
  onPlaybackEnd?: () => void;
  onTranscript?: (text: string, isFinal: boolean) => void;
  onError?: (message: string) => void;
}

interface UseVoiceStreamingReturn {
  isRecording: boolean;
  isPlaying: boolean;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  playAudioChunk: (base64Audio: string, sampleRate?: number) => void;
  stopPlayback: () => void;
  micLevel: number;
}

export function useVoiceStreaming({
  wsRef,
  onPlaybackStart,
  onPlaybackEnd,
  onTranscript,
  onError,
  isStreamingReady = false,
}: UseVoiceStreamingOptions): UseVoiceStreamingReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [micLevel, setMicLevel] = useState(0);

  // Refs for mic capture
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const levelTimerRef = useRef<number | null>(null);

  // Pause detection refs
  const silenceStartRef = useRef<number | null>(null);
  const recordingStartRef = useRef<number | null>(null);
  const audioBufferRef = useRef<Int16Array[]>([]);
  const SILENCE_THRESHOLD = 0.008; // Lower threshold — only true silence triggers, not soft speech
  const SILENCE_DURATION = 2500; // 2.5 seconds of continuous silence before auto-stop
  const MIN_RECORDING_DURATION = 3000; // Minimum 3 seconds before allowing auto-stop
  const AUTO_STOP_ENABLED = true; // Enabled for natural voice interaction

  // Playback queue
  const playbackCtxRef = useRef<AudioContext | null>(null);
  const playbackQueueRef = useRef<AudioBuffer[]>([]);
  const isPlayingNextRef = useRef(false);
  const currentSourceRef = useRef<AudioBufferSourceNode | null>(null);
  const nextPlayTimeRef = useRef(0);
  const MAX_PLAYBACK_QUEUE_SIZE = 50;

  // Mic level polling cleanup
  useEffect(() => {
    return () => {
      if (levelTimerRef.current) cancelAnimationFrame(levelTimerRef.current);
    };
  }, []);

  const startRecording = useCallback(async () => {
    try {
      // 1. Mic capture
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000, // Request 16kHz from browser if possible
        },
      });
      mediaStreamRef.current = stream;

      const audioCtx = new AudioContext({ sampleRate: 16000 }); // Force 16kHz
      audioContextRef.current = audioCtx;
      if (audioCtx.state === 'suspended') await audioCtx.resume();

      const source = audioCtx.createMediaStreamSource(stream);
      
      // Send audio_start to backend
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        console.log('[useVoiceStreaming] Sending audio_start');
        wsRef.current.send(JSON.stringify({ type: 'audio_start' }));
      } else {
        console.log('[useVoiceStreaming] WebSocket not open for audio_start');
      }

      // 2. Audio processing for streaming to backend
      const processor = audioCtx.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;
      
      processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        // Convert Float32 audio to Int16 for backend
        const int16Data = new Int16Array(inputData.length);
        
        // Calculate audio level for silence detection
        let sum = 0;
        for (let i = 0; i < inputData.length; i++) {
          const sample = inputData[i];
          int16Data[i] = Math.max(-1, Math.min(1, sample)) * 0x7FFF;
          sum += Math.abs(sample);
        }
        const avgLevel = sum / inputData.length;
        
        // Silence detection
        if (avgLevel < SILENCE_THRESHOLD) {
          if (silenceStartRef.current === null) {
            silenceStartRef.current = Date.now();
          } else {
            const silenceDuration = Date.now() - silenceStartRef.current;
            const recordingDuration = recordingStartRef.current ? Date.now() - recordingStartRef.current : 0;
            // Only auto-stop if we've recorded enough AND silence has lasted long enough
            if (recordingDuration >= MIN_RECORDING_DURATION && silenceDuration > SILENCE_DURATION) {
              console.log('[useVoiceStreaming] Silence detected, auto-stopping');
              stopRecording();
              return;
            }
          }
        } else {
          // Reset silence timer when sound is detected
          silenceStartRef.current = null;
        }
        
        // Send to WebSocket
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          // Convert Int16Array to base64 without spread operator
          const uint8View = new Uint8Array(int16Data.buffer);
          let binary = '';
          for (let i = 0; i < uint8View.length; i++) {
            binary += String.fromCharCode(uint8View[i]);
          }
          const base64 = btoa(binary);
          wsRef.current.send(JSON.stringify({ 
            type: 'audio', 
            content: base64 
          }));
        }
      };

      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      
      source.connect(analyser);
      analyser.connect(processor);
      processor.connect(audioCtx.destination);
      analyserRef.current = analyser;

      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const pollLevel = () => {
        analyser.getByteTimeDomainData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          const floatV = (dataArray[i] - 128) / 128;
          sum += floatV * floatV;
        }
        const rms = Math.sqrt(sum / dataArray.length);
        setMicLevel(Math.min(1, rms * 3));
        levelTimerRef.current = requestAnimationFrame(pollLevel);
      };
      levelTimerRef.current = requestAnimationFrame(pollLevel);

      setIsRecording(true);
      recordingStartRef.current = Date.now();
    } catch (err: any) {
      console.error('[useVoiceStreaming] Microphone access denied:', err);
      if (err?.name === 'NotAllowedError') {
        onError?.('Microphone access denied. Please allow microphone permission in your browser settings.');
      } else if (err?.name === 'NotFoundError') {
        onError?.('No microphone found. Please connect a microphone and try again.');
      } else {
        onError?.(`Microphone error: ${err?.message || 'Unknown error'}`);
      }
    }
  }, [wsRef]);

  const stopRecording = useCallback(() => {
    // Reset silence timer
    silenceStartRef.current = null;
    
    // Send audio_stop to backend
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[useVoiceStreaming] Sending audio_stop');
      wsRef.current.send(JSON.stringify({ type: 'audio_stop' }));
    } else {
      console.log('[useVoiceStreaming] WebSocket not open, cannot send audio_stop');
    }

    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }

    if (levelTimerRef.current) {
      cancelAnimationFrame(levelTimerRef.current);
      levelTimerRef.current = null;
    }

    setMicLevel(0);
    setIsRecording(false);
  }, [wsRef]);

  const getPlaybackCtx = useCallback(() => {
    if (!playbackCtxRef.current || playbackCtxRef.current.state === 'closed') {
      playbackCtxRef.current = new AudioContext();
    }
    if (playbackCtxRef.current.state === 'suspended') {
      playbackCtxRef.current.resume().catch(() => {});
    }
    return playbackCtxRef.current;
  }, []);

  const scheduleNext = useCallback(() => {
    if (isPlayingNextRef.current) return;
    const buf = playbackQueueRef.current.shift();
    if (!buf) {
      setIsPlaying(false);
      onPlaybackEnd?.();
      return;
    }

    isPlayingNextRef.current = true;
    const ctx = getPlaybackCtx();
    const src = ctx.createBufferSource();
    src.buffer = buf;
    src.connect(ctx.destination);
    currentSourceRef.current = src;

    const startTime = Math.max(ctx.currentTime, nextPlayTimeRef.current);
    src.start(startTime);
    nextPlayTimeRef.current = startTime + buf.duration;

    src.onended = () => {
      isPlayingNextRef.current = false;
      currentSourceRef.current = null;
      scheduleNext();
    };
  }, [getPlaybackCtx, onPlaybackEnd]);

  const playAudioChunk = useCallback(
    (base64Audio: string, sampleRate: number = 24000) => {
      try {
        const binary = atob(base64Audio);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
          bytes[i] = binary.charCodeAt(i);
        }

        const int16 = new Int16Array(bytes.buffer);
        const float32 = new Float32Array(int16.length);
        for (let i = 0; i < int16.length; i++) {
          float32[i] = int16[i] / 32768;
        }

        const ctx = getPlaybackCtx();
        const audioBuffer = ctx.createBuffer(1, float32.length, sampleRate);
        audioBuffer.getChannelData(0).set(float32);

        // Trim queue from front if exceeding limit
        if (playbackQueueRef.current.length >= MAX_PLAYBACK_QUEUE_SIZE) {
          playbackQueueRef.current = playbackQueueRef.current.slice(-Math.floor(MAX_PLAYBACK_QUEUE_SIZE / 2));
        }
        playbackQueueRef.current.push(audioBuffer);

        if (!isPlaying) {
          setIsPlaying(true);
          onPlaybackStart?.();
          scheduleNext();
        }
      } catch (err) {
        console.error('[useVoiceStreaming] playAudioChunk error:', err);
      }
    },
    [getPlaybackCtx, isPlaying, onPlaybackStart, scheduleNext],
  );

  const stopPlayback = useCallback(() => {
    playbackQueueRef.current = [];
    nextPlayTimeRef.current = 0;
    if (currentSourceRef.current) {
      try {
        currentSourceRef.current.stop();
      } catch {}
      currentSourceRef.current = null;
    }
    isPlayingNextRef.current = false;
    setIsPlaying(false);
    onPlaybackEnd?.();
  }, [onPlaybackEnd]);

  useEffect(() => {
    return () => {
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      }
      if (audioContextRef.current) {
        audioContextRef.current.close().catch(() => {});
      }
      if (playbackCtxRef.current) {
        playbackCtxRef.current.close().catch(() => {});
      }
    };
  }, []);

  return {
    isRecording,
    isPlaying,
    startRecording,
    stopRecording,
    playAudioChunk,
    stopPlayback,
    micLevel,
  };
}
