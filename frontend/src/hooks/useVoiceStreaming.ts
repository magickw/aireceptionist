'use client';
import { useRef, useState, useCallback, useEffect } from 'react';

/**
 * Hook for voice input (browser-side STT) and audio playback.
 *
 * STT:  Uses the Web Speech API (SpeechRecognition) built into
 *        Chrome / Edge / Safari.  No server-side transcription needed.
 *
 * Mic:  Captures microphone audio purely for the visual level meter.
 *        Audio is NOT sent to the server.
 *
 * Playback: Plays back PCM audio received from the server via AudioContext.
 */

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
  /** Active WebSocket ref */
  wsRef: React.RefObject<WebSocket | null>;
  /** Called when playback starts */
  onPlaybackStart?: () => void;
  /** Called when playback ends */
  onPlaybackEnd?: () => void;
  /** Called when speech is recognised by the browser */
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

  // Refs for mic capture (visual only)
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const levelTimerRef = useRef<number | null>(null);

  // Ref for SpeechRecognition
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const onTranscriptRef = useRef(onTranscript);
  onTranscriptRef.current = onTranscript;

  // Refs for sentence completion detection
  const accumulatedTranscriptRef = useRef('');
  const finalTranscriptTimerRef = useRef<number | null>(null);
  const lastSpeechTimeRef = useRef<number>(0);
  const silenceThreshold = 1200; // ms of silence before sending
  const minTranscriptLength = 2; // minimum words to send

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

  // ---- Recording (mic capture + browser STT) ----

  /**
   * Check if transcript forms a complete sentence
   * Detects sentence boundaries: . ! ? and common completion patterns
   */
  const isCompleteSentence = useCallback((text: string): boolean => {
    const trimmed = text.trim();
    if (trimmed.length < minTranscriptLength) return false;

    // Check for sentence-ending punctuation
    const sentenceEnders = /[.!?]\s*$/;
    if (sentenceEnders.test(trimmed)) return true;

    // Check for question words at end (common in queries)
    const questionPatterns = /\b(what|where|when|why|how|who|which|whose)\b.*\?$/i;
    if (questionPatterns.test(trimmed)) return true;

    // Check for command patterns (imperatives)
    const commandPatterns = /^(please|can you|could you|I need|I want|I would like|book|order|schedule|cancel|help)/i;
    if (commandPatterns.test(trimmed) && trimmed.length > 10) return true;

    return false;
  }, []);

  /**
   * Check if we should send the transcript based on silence or sentence completion
   */
  const sendTranscriptIfReady = useCallback(() => {
    const transcript = accumulatedTranscriptRef.current.trim();
    if (!transcript) {
      return;
    }

    const timeSinceLastSpeech = Date.now() - lastSpeechTimeRef.current;
    const isSilenceDetected = timeSinceLastSpeech >= silenceThreshold;

    // Send if we have a complete sentence OR significant silence
    if (isCompleteSentence(transcript) || isSilenceDetected) {
      // Only send if we have enough content
      const wordCount = transcript.split(/\s+/).length;
      if (wordCount >= minTranscriptLength) {
        console.log('[useVoiceStreaming] Sending transcript:', transcript);
        setInterimTranscript('');
        accumulatedTranscriptRef.current = '';
        onTranscriptRef.current?.(transcript, true);
      }
    }
  }, [isCompleteSentence]);

  const startRecording = useCallback(async () => {
    // Reset transcript state
    accumulatedTranscriptRef.current = '';
    lastSpeechTimeRef.current = 0;
    if (finalTranscriptTimerRef.current) {
      clearTimeout(finalTranscriptTimerRef.current);
      finalTranscriptTimerRef.current = null;
    }

    try {
      // 1. Mic capture (for visual level meter only)
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

      // Analyser for mic level
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      // ScriptProcessor to keep analyser alive (no audio sent to server)
      const processor = audioCtx.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;
      processor.onaudioprocess = () => {}; // noop — just keeps node alive
      source.connect(processor);
      processor.connect(audioCtx.destination);

      // Poll mic level for visualiser
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const pollLevel = () => {
        analyser.getByteTimeDomainData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          const v = (dataArray[i] - 128) / 128;
          sum += v * v;
        }
        const rms = Math.sqrt(sum / dataArray.length);
        setMicLevel(Math.min(1, rms * 3));
        levelTimerRef.current = requestAnimationFrame(pollLevel);
      };
      levelTimerRef.current = requestAnimationFrame(pollLevel);

      // 2. Browser-side STT via Web Speech API
      const SpeechRecognitionCtor =
        typeof window !== 'undefined'
          ? window.SpeechRecognition || window.webkitSpeechRecognition
          : null;

      if (SpeechRecognitionCtor) {
        const recognition = new SpeechRecognitionCtor();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onresult = (event: SpeechRecognitionEvent) => {
          let interim = '';
          let hasFinalResult = false;

          for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];
            const transcript = result[0].transcript;

            if (result.isFinal) {
              // Browser marked this as final, but we'll use our own completion detection
              hasFinalResult = true;
            }
            // Always accumulate transcript (both final and interim)
            interim += transcript;
          }

          // Update interim display
          if (interim) {
            setInterimTranscript(interim);
            accumulatedTranscriptRef.current = interim;
            lastSpeechTimeRef.current = Date.now();
          }

          // Clear any pending send timer
          if (finalTranscriptTimerRef.current) {
            clearTimeout(finalTranscriptTimerRef.current);
            finalTranscriptTimerRef.current = null;
          }

          // Start silence detection timer
          finalTranscriptTimerRef.current = window.setTimeout(() => {
            sendTranscriptIfReady();
          }, silenceThreshold);
        };

        recognition.onerror = (ev) => {
          // 'no-speech' is normal when user pauses; ignore it
          if ((ev as any).error !== 'no-speech') {
            console.error('[useVoiceStreaming] SpeechRecognition error:', (ev as any).error);
          }
        };

        recognition.onend = () => {
          // If still recording, restart recognition (it auto-stops on silence)
          if (mediaStreamRef.current) {
            try {
              recognition.start();
            } catch {
              // already started
            }
          }
        };

        recognition.start();
        recognitionRef.current = recognition;
      } else {
        console.warn('[useVoiceStreaming] SpeechRecognition not supported in this browser');
      }

      setIsRecording(true);
    } catch (err) {
      console.error('[useVoiceStreaming] Microphone access denied:', err);
    }
  }, []);

  const stopRecording = useCallback(() => {
    // Send any pending transcript before stopping
    if (accumulatedTranscriptRef.current.trim()) {
      const transcript = accumulatedTranscriptRef.current.trim();
      const wordCount = transcript.split(/\s+/).length;
      if (wordCount >= minTranscriptLength) {
        onTranscriptRef.current?.(transcript, true);
      }
    }

    // Clear pending timer
    if (finalTranscriptTimerRef.current) {
      clearTimeout(finalTranscriptTimerRef.current);
      finalTranscriptTimerRef.current = null;
    }

    // Reset transcript state
    accumulatedTranscriptRef.current = '';
    lastSpeechTimeRef.current = 0;

    // Stop SpeechRecognition
    if (recognitionRef.current) {
      try {
        recognitionRef.current.onend = null; // prevent auto-restart
        recognitionRef.current.stop();
      } catch {
        // already stopped
      }
      recognitionRef.current = null;
    }

    // Cleanup mic processor
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
    setInterimTranscript('');
    setIsRecording(false);
  }, []);

  // ---- Playback ----

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
        }
        scheduleNext();
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
      if (finalTranscriptTimerRef.current) {
        clearTimeout(finalTranscriptTimerRef.current);
      }
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch { /* */ }
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
