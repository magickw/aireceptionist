'use client';
import { useRef, useState, useCallback, useEffect } from 'react';

/**
 * Hook for bidirectional voice streaming over WebSocket.
 *
 * - Captures microphone audio as PCM16 @ 16kHz mono
 * - Sends audio_start / audio (base64 chunks) / audio_stop over WS
 * - Plays back PCM audio received from the server via AudioContext
 * - Supports both 16kHz (batch) and 24kHz (streaming) playback
 */

interface UseVoiceStreamingOptions {
  /** Active WebSocket ref */
  wsRef: React.RefObject<WebSocket | null>;
  /** Called when playback starts */
  onPlaybackStart?: () => void;
  /** Called when playback ends */
  onPlaybackEnd?: () => void;
}

interface UseVoiceStreamingReturn {
  isRecording: boolean;
  isPlaying: boolean;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  playAudioChunk: (base64Audio: string, sampleRate?: number) => void;
  stopPlayback: () => void;
  micLevel: number; // 0-1 for visualizer
}

// Convert Float32 samples [-1, 1] to Int16 PCM
function float32ToInt16(float32Array: Float32Array): Int16Array {
  const int16 = new Int16Array(float32Array.length);
  for (let i = 0; i < float32Array.length; i++) {
    const s = Math.max(-1, Math.min(1, float32Array[i]));
    int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return int16;
}

// Downsample from source rate to target rate
function downsample(buffer: Float32Array, fromRate: number, toRate: number): Float32Array {
  if (fromRate === toRate) return buffer;
  const ratio = fromRate / toRate;
  const newLength = Math.round(buffer.length / ratio);
  const result = new Float32Array(newLength);
  for (let i = 0; i < newLength; i++) {
    const srcIndex = i * ratio;
    const low = Math.floor(srcIndex);
    const high = Math.min(low + 1, buffer.length - 1);
    const frac = srcIndex - low;
    result[i] = buffer[low] * (1 - frac) + buffer[high] * frac;
  }
  return result;
}

export function useVoiceStreaming({
  wsRef,
  onPlaybackStart,
  onPlaybackEnd,
}: UseVoiceStreamingOptions): UseVoiceStreamingReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [micLevel, setMicLevel] = useState(0);

  const mediaStreamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const levelTimerRef = useRef<number | null>(null);

  // Playback queue
  const playbackCtxRef = useRef<AudioContext | null>(null);
  const playbackQueueRef = useRef<AudioBuffer[]>([]);
  const isPlayingNextRef = useRef(false);
  const currentSourceRef = useRef<AudioBufferSourceNode | null>(null);
  const nextPlayTimeRef = useRef(0);

  // Mic level polling
  useEffect(() => {
    return () => {
      if (levelTimerRef.current) cancelAnimationFrame(levelTimerRef.current);
    };
  }, []);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      mediaStreamRef.current = stream;

      const audioCtx = new AudioContext({ sampleRate: 16000 });
      audioContextRef.current = audioCtx;

      // Resume if suspended (browser autoplay policy)
      if (audioCtx.state === 'suspended') {
        await audioCtx.resume();
      }

      // If browser forced a different sample rate, we'll downsample
      const actualRate = audioCtx.sampleRate;

      const source = audioCtx.createMediaStreamSource(stream);

      // Analyser for mic level
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      // ScriptProcessor to get raw PCM (4096 samples per chunk)
      const processor = audioCtx.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      const ws = wsRef.current;

      // Send audio_start
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'audio_start' }));
      }

      processor.onaudioprocess = (e) => {
        if (!ws || ws.readyState !== WebSocket.OPEN) return;
        const rawSamples = e.inputBuffer.getChannelData(0);

        // Downsample if needed
        const samples = actualRate !== 16000
          ? downsample(rawSamples, actualRate, 16000)
          : rawSamples;

        const pcm16 = float32ToInt16(samples);
        const bytes = new Uint8Array(pcm16.buffer);

        // Chunk-safe base64 encoding (avoid stack overflow from spread on large arrays)
        let binary = '';
        for (let i = 0; i < bytes.length; i++) {
          binary += String.fromCharCode(bytes[i]);
        }
        const b64 = btoa(binary);

        ws.send(JSON.stringify({ type: 'audio', content: b64 }));
      };

      source.connect(processor);
      processor.connect(audioCtx.destination); // required for ScriptProcessor to fire

      // Poll mic level
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const pollLevel = () => {
        analyser.getByteTimeDomainData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          const v = (dataArray[i] - 128) / 128;
          sum += v * v;
        }
        const rms = Math.sqrt(sum / dataArray.length);
        setMicLevel(Math.min(1, rms * 3)); // amplify for visibility
        if (isRecording) {
          levelTimerRef.current = requestAnimationFrame(pollLevel);
        }
      };
      levelTimerRef.current = requestAnimationFrame(pollLevel);

      setIsRecording(true);
    } catch (err) {
      console.error('[useVoiceStreaming] Microphone access denied:', err);
    }
  }, [wsRef, isRecording]);

  const stopRecording = useCallback(() => {
    // Send audio_stop
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'audio_stop' }));
    }

    // Cleanup processor
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }

    // Stop mic tracks
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
    }

    // Close capture context
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

  // ---- Playback ----

  const getPlaybackCtx = useCallback(() => {
    if (!playbackCtxRef.current || playbackCtxRef.current.state === 'closed') {
      playbackCtxRef.current = new AudioContext();
    }
    // Resume if suspended (browser autoplay policy)
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
    const source = ctx.createBufferSource();
    source.buffer = buf;
    source.connect(ctx.destination);
    currentSourceRef.current = source;

    // Schedule seamlessly
    const startTime = Math.max(ctx.currentTime, nextPlayTimeRef.current);
    source.start(startTime);
    nextPlayTimeRef.current = startTime + buf.duration;

    source.onended = () => {
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

        // Decode PCM16 to Float32
        const int16 = new Int16Array(bytes.buffer);
        const float32 = new Float32Array(int16.length);
        for (let i = 0; i < int16.length; i++) {
          float32[i] = int16[i] / 32768;
        }

        const ctx = getPlaybackCtx();
        const audioBuffer = ctx.createBuffer(1, float32.length, sampleRate);
        audioBuffer.getChannelData(0).set(float32);

        playbackQueueRef.current.push(audioBuffer);

        if (!isPlaying) {
          setIsPlaying(true);
          onPlaybackStart?.();
        }
        scheduleNext();
      } catch (err) {
        console.error('[useVoiceStreaming] playAudioChunk error:', err);
      }
    },
    [getPlaybackCtx, isPlaying, onPlaybackStart, scheduleNext]
  );

  const stopPlayback = useCallback(() => {
    playbackQueueRef.current = [];
    nextPlayTimeRef.current = 0;
    if (currentSourceRef.current) {
      try {
        currentSourceRef.current.stop();
      } catch {
        // already stopped
      }
      currentSourceRef.current = null;
    }
    isPlayingNextRef.current = false;
    setIsPlaying(false);
    onPlaybackEnd?.();
  }, [onPlaybackEnd]);

  // Cleanup on unmount
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
