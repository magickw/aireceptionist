'use client';
import { useRef, useState, useCallback, useEffect } from 'react';

// -- TypeScript declarations for Web Speech API --
interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}
interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}
interface SpeechRecognitionResult {
  isFinal: boolean;
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
}
interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}
interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((ev: SpeechRecognitionEvent) => void) | null;
  onerror: ((ev: Event & { error: string }) => void) | null;
  onend: (() => void) | null;
  onstart: (() => void) | null;
}
declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

interface UseVoiceStreamingOptions {
  wsRef: React.RefObject<WebSocket | null>;
  onPlaybackStart?: () => void;
  onPlaybackEnd?: () => void;
  onTranscript?: (text: string, isFinal: boolean) => void;
}

interface UseVoiceStreamingReturn {
  isRecording: boolean;
  isPlaying: boolean;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  playAudioChunk: (base64Audio: string, sampleRate?: number) => void;
  stopPlayback: () => void;
  micLevel: number;
  interimTranscript: string;
}

export function useVoiceStreaming({
  wsRef,
  onPlaybackStart,
  onPlaybackEnd,
  onTranscript,
}: UseVoiceStreamingOptions): UseVoiceStreamingReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [micLevel, setMicLevel] = useState(0);
  const [interimTranscript, setInterimTranscript] = useState('');

  // Refs for mic capture
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const levelTimerRef = useRef<number | null>(null);

  // Refs for SpeechRecognition
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const finalTranscriptRef = useRef('');
  const onTranscriptRef = useRef(onTranscript);
  onTranscriptRef.current = onTranscript;

  // Playback queue
  const playbackCtxRef = useRef<AudioContext | null>(null);
  const playbackQueueRef = useRef<AudioBuffer[]>([]);
  const isPlayingNextRef = useRef(false);
  const currentSourceRef = useRef<AudioBufferSourceNode | null>(null);
  const nextPlayTimeRef = useRef(0);

  // Mic level polling cleanup
  useEffect(() => {
    return () => {
      if (levelTimerRef.current) cancelAnimationFrame(levelTimerRef.current);
    };
  }, []);

  const startRecording = useCallback(async () => {
    finalTranscriptRef.current = '';
    setInterimTranscript('');

    try {
      // 1. Mic capture for visual level meter
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      mediaStreamRef.current = stream;

      const audioCtx = new AudioContext();
      audioContextRef.current = audioCtx;
      if (audioCtx.state === 'suspended') await audioCtx.resume();

      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const pollLevel = () => {
        analyser.getByteTimeDomainData(dataArray);
        let sum = 0;
        for (const v of dataArray) {
          const floatV = (v - 128) / 128;
          sum += floatV * floatV;
        }
        const rms = Math.sqrt(sum / dataArray.length);
        setMicLevel(Math.min(1, rms * 3));
        levelTimerRef.current = requestAnimationFrame(pollLevel);
      };
      levelTimerRef.current = requestAnimationFrame(pollLevel);

      // 2. Browser-side STT via Web Speech API
      const SpeechRecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;

      if (SpeechRecognitionCtor) {
        const recognition = new SpeechRecognitionCtor();
        recognitionRef.current = recognition;
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onresult = (event: SpeechRecognitionEvent) => {
          let interim = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              finalTranscriptRef.current += event.results[i][0].transcript;
            } else {
              interim += event.results[i][0].transcript;
            }
          }
          setInterimTranscript(finalTranscriptRef.current + interim);
        };

        recognition.onerror = (ev) => {
          if ((ev as any).error !== 'no-speech' && (ev as any).error !== 'aborted') {
            console.error('[useVoiceStreaming] SpeechRecognition error:', (ev as any).error);
          }
        };
        
        recognition.onend = () => {
            // The 'end' event can fire unexpectedly. If we are still in 'recording' state,
            // it means it was not a user-initiated stop, so we should restart.
            if (recognitionRef.current) {
                try {
                    recognition.start();
                } catch (e) {
                    console.error('[useVoiceStreaming] Recognition restart failed:', e);
                }
            }
        };

        recognition.start();
        setIsRecording(true);
      } else {
        console.warn('[useVoiceStreaming] SpeechRecognition not supported in this browser.');
      }
    } catch (err) {
      console.error('[useVoiceStreaming] Microphone access denied:', err);
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.onend = null; // Prevent automatic restart on manual stop
      recognitionRef.current.stop();
      recognitionRef.current = null;
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

    const finalTranscript = interimTranscript.trim();
    if (finalTranscript) {
      onTranscriptRef.current?.(finalTranscript, true);
    }

    setMicLevel(0);
    setIsRecording(false);
    // Do not clear interimTranscript here so it remains visible until the next recording starts
  }, [interimTranscript]);

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
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
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
    interimTranscript,
  };
}
