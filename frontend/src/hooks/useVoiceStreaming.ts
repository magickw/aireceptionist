'use client';
import { useRef, useState, useCallback, useEffect } from 'react';
import { WS_MESSAGE_TYPES, detectBrowserCompatibility, BrowserCompatibility } from '@/types/voice';

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
  browserCompatibility: BrowserCompatibility | null;
}

export function useVoiceStreaming({
  wsRef,
  onPlaybackStart,
  onPlaybackEnd,
  onTranscript,
  onError,
}: UseVoiceStreamingOptions): UseVoiceStreamingReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [micLevel, setMicLevel] = useState(0);
  const [browserCompatibility, setBrowserCompatibility] = useState<BrowserCompatibility | null>(null);

  // Check browser compatibility on mount
  useEffect(() => {
    const compatibility = detectBrowserCompatibility();
    setBrowserCompatibility(compatibility);
    
    if (!compatibility.supported) {
      onError?.('Your browser does not support voice features. Please use Chrome, Firefox, Edge, or Safari.');
    } else if (compatibility.warnings.length > 0) {
      console.warn('[useVoiceStreaming] Browser compatibility warnings:', compatibility.warnings);
    }
  }, [onError]);

  // Refs for mic capture
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const levelTimerRef = useRef<number | null>(null);

  // Pause detection refs
  const silenceStartRef = useRef<number | null>(null);
  const recordingStartRef = useRef<number | null>(null);
  const hasSpeechRef = useRef(false); // Track whether user has spoken during this recording
  const audioBufferRef = useRef<Int16Array[]>([]);
  
  // Dynamic noise floor detection - adapts to environment
  const noiseFloorRef = useRef<number | null>(null); // Measured ambient noise level
  const calibrationSamplesRef = useRef<number[]>([]); // Samples during calibration phase
  const CALIBRATION_CHUNKS = 5; // Number of chunks to sample for noise floor (calibration phase)
  const SPEECH_RATIO = 2.0; // Speech must be 2x above noise floor to be detected
  const SILENCE_RATIO = 1.5; // Below 1.5x noise floor is considered silence
  const SILENCE_DURATION = 3500; // 3.5 seconds of silence after speech before auto-stop (allows for natural pauses)
  const MIN_RECORDING_DURATION = 1000; // 1 second minimum before allowing auto-stop
  const MIN_SPEECH_CHUNKS = 3; // Minimum consecutive chunks above speech threshold
  const MIN_SILENCE_CHUNKS = 5; // Minimum consecutive chunks below silence threshold
  
  const speechChunkCountRef = useRef(0); // Track consecutive speech chunks
  const silenceChunkCountRef = useRef(0); // Track consecutive silence chunks
  const chunkCountRef = useRef(0); // Total chunk count for calibration

  // Playback queue
  const playbackCtxRef = useRef<AudioContext | null>(null);
  const playbackQueueRef = useRef<AudioBuffer[]>([]);
  const isPlayingNextRef = useRef(false);
  const currentSourceRef = useRef<AudioBufferSourceNode | null>(null);
  const nextPlayTimeRef = useRef(0);
  const MAX_PLAYBACK_QUEUE_SIZE = 50;

  const startRecording = useCallback(async () => {
    // Guard: don't start if already recording
    if (processorRef.current || mediaStreamRef.current) {
      console.log('[useVoiceStreaming] startRecording called but already recording, skipping');
      return;
    }
    
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

      // Verify actual sample rate — some browsers (Safari) may ignore the requested rate
      const actualSampleRate = audioCtx.sampleRate;
      const TARGET_SAMPLE_RATE = 16000;
      const needsResampling = actualSampleRate !== TARGET_SAMPLE_RATE;
      const resampleRatio = actualSampleRate / TARGET_SAMPLE_RATE;
      console.log(`[useVoiceStreaming] AudioContext sampleRate: ${actualSampleRate} (requested: ${TARGET_SAMPLE_RATE}, resampling: ${needsResampling})`);
      if (needsResampling) {
        console.warn(`[useVoiceStreaming] Sample rate mismatch! Browser gave ${actualSampleRate}Hz instead of ${TARGET_SAMPLE_RATE}Hz. Will resample audio.`);
      }

      const source = audioCtx.createMediaStreamSource(stream);

      // Send audio_start to backend with actual sample rate info
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        console.log('[useVoiceStreaming] Sending audio_start');
        wsRef.current.send(JSON.stringify({ type: WS_MESSAGE_TYPES.AUDIO_START, sample_rate: actualSampleRate }));
      } else {
        console.log('[useVoiceStreaming] WebSocket not open for audio_start');
      }

      // 2. Audio processing for streaming to backend
      const processor = audioCtx.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;
      let chunkCount = 0;

      processor.onaudioprocess = (e) => {
        // Guard: exit if processor has been disconnected
        if (!processorRef.current) {
          return;
        }
        
        const inputData = e.inputBuffer.getChannelData(0);
        chunkCount++;
        chunkCountRef.current = chunkCount;

        // Calculate audio level using RMS (more accurate for speech detection)
        const windowSize = Math.min(inputData.length, 1600); // 100ms window at 16kHz
        const startIndex = Math.max(0, inputData.length - windowSize);
        let sumSq = 0;
        for (let i = startIndex; i < inputData.length; i++) {
          sumSq += inputData[i] * inputData[i];
        }
        const rmsLevel = Math.sqrt(sumSq / windowSize);

        // === CALIBRATION PHASE ===
        // Collect initial samples to measure ambient noise floor
        if (noiseFloorRef.current === null) {
          calibrationSamplesRef.current.push(rmsLevel);
          
          if (calibrationSamplesRef.current.length >= CALIBRATION_CHUNKS) {
            // Calculate noise floor from calibration samples
            // Use median to filter out any brief sounds during calibration
            const sorted = [...calibrationSamplesRef.current].sort((a, b) => a - b);
            const median = sorted[Math.floor(sorted.length / 2)];
            noiseFloorRef.current = Math.max(median, 0.0005); // Minimum floor of 0.0005
            console.log(`[useVoiceStreaming] Noise floor calibrated: ${noiseFloorRef.current.toFixed(6)}`);
          }
          
          // During calibration, just send audio but don't process speech/silence
          // Continue to resampling section below
        } else {
          // === NORMAL OPERATION WITH DYNAMIC THRESHOLDS ===
          const noiseFloor = noiseFloorRef.current;
          const speechThreshold = noiseFloor * SPEECH_RATIO;
          const silenceThreshold = noiseFloor * SILENCE_RATIO;
          
          // Debug logging (every 10 chunks)
          if (chunkCount % 10 === 0) {
            const silenceDuration = silenceStartRef.current ? Date.now() - silenceStartRef.current : 0;
            console.log(`[useVoiceStreaming] Chunk #${chunkCount}: rms=${rmsLevel.toFixed(6)}, noiseFloor=${noiseFloor.toFixed(6)}, speechThresh=${speechThreshold.toFixed(6)}, silenceThresh=${silenceThreshold.toFixed(6)}, hasSpeech=${hasSpeechRef.current}, silenceMs=${silenceDuration}`);
          }

          // Determine if this chunk is speech or silence based on dynamic thresholds
          const isSpeechChunk = rmsLevel >= speechThreshold;
          const isSilentChunk = rmsLevel < silenceThreshold;
          
          if (isSpeechChunk) {
            // Speech detected - increment speech chunk counter
            speechChunkCountRef.current++;
            silenceChunkCountRef.current = 0;
            
            // Require minimum consecutive speech chunks to confirm speech
            if (speechChunkCountRef.current >= MIN_SPEECH_CHUNKS) {
              if (!hasSpeechRef.current) {
                console.log(`[useVoiceStreaming] Speech confirmed after ${speechChunkCountRef.current} chunks`);
              }
              hasSpeechRef.current = true;
              silenceStartRef.current = null;
            }
          } else if (isSilentChunk) {
            // Silence detected - increment silence chunk counter
            silenceChunkCountRef.current++;
            speechChunkCountRef.current = 0;
            
            if (hasSpeechRef.current) {
              // Speech was detected previously, now tracking silence
              if (silenceChunkCountRef.current >= MIN_SILENCE_CHUNKS) {
                if (silenceStartRef.current === null) {
                  silenceStartRef.current = Date.now();
                  console.log(`[useVoiceStreaming] Silence started (below ${silenceThreshold.toFixed(6)})`);
                } else {
                  const silenceDuration = Date.now() - silenceStartRef.current;
                  const recordingDuration = recordingStartRef.current ? Date.now() - recordingStartRef.current : 0;
                  if (recordingDuration >= MIN_RECORDING_DURATION && silenceDuration > SILENCE_DURATION) {
                    console.log(`[useVoiceStreaming] Auto-stop: ${silenceDuration}ms silence after speech`);
                    stopRecording();
                    return;
                  }
                }
              }
            }
          } else {
            // In between speech and silence thresholds
            // Treat as "soft speech" - reset silence counter to prevent premature stop
            // This handles trailing speech sounds and soft speaking
            if (hasSpeechRef.current) {
              silenceChunkCountRef.current = 0;
              silenceStartRef.current = null;
            }
          }
        }

        // Resample to 16kHz if the AudioContext is at a different rate
        let audioSamples: Float32Array;
        if (needsResampling) {
          const newLength = Math.round(inputData.length / resampleRatio);
          audioSamples = new Float32Array(newLength);
          for (let i = 0; i < newLength; i++) {
            const srcIndex = i * resampleRatio;
            const srcFloor = Math.floor(srcIndex);
            const frac = srcIndex - srcFloor;
            if (srcFloor + 1 < inputData.length) {
              audioSamples[i] = inputData[srcFloor] * (1 - frac) + inputData[srcFloor + 1] * frac;
            } else {
              audioSamples[i] = inputData[srcFloor] || 0;
            }
          }
        } else {
          audioSamples = inputData;
        }

        // Convert Float32 audio to Int16 for backend (always at 16kHz after resampling)
        const int16Data = new Int16Array(audioSamples.length);
        for (let i = 0; i < audioSamples.length; i++) {
          int16Data[i] = Math.max(-1, Math.min(1, audioSamples[i])) * 0x7FFF;
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
            type: WS_MESSAGE_TYPES.AUDIO,
            content: base64
          }));

          if (chunkCount <= 3) {
            console.log(`[useVoiceStreaming] Audio chunk #${chunkCount}: ${int16Data.length} samples, ${uint8View.length} bytes, rmsLevel=${rmsLevel.toFixed(4)}`);
          }
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
      hasSpeechRef.current = false; // Reset speech detection for new recording
      speechChunkCountRef.current = 0; // Reset speech chunk counter
      silenceChunkCountRef.current = 0; // Reset silence chunk counter
      noiseFloorRef.current = null; // Reset noise floor for recalibration
      calibrationSamplesRef.current = []; // Reset calibration samples
      chunkCountRef.current = 0; // Reset chunk count
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
    // Guard against multiple rapid calls
    if (!processorRef.current && !mediaStreamRef.current) {
      console.log('[useVoiceStreaming] stopRecording called but already stopped');
      return;
    }
    
    // Reset silence timer and speech detection state
    silenceStartRef.current = null;
    hasSpeechRef.current = false;
    speechChunkCountRef.current = 0;
    silenceChunkCountRef.current = 0;
    
    // Send audio_stop to backend
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[useVoiceStreaming] Sending audio_stop');
      wsRef.current.send(JSON.stringify({ type: WS_MESSAGE_TYPES.AUDIO_STOP }));
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
      // Stop mic level polling
      if (levelTimerRef.current) {
        cancelAnimationFrame(levelTimerRef.current);
        levelTimerRef.current = null;
      }
      // Stop any active recording
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((t) => t.stop());
        mediaStreamRef.current = null;
      }
      if (processorRef.current) {
        processorRef.current.disconnect();
        processorRef.current = null;
      }
      if (analyserRef.current) {
        analyserRef.current.disconnect();
        analyserRef.current = null;
      }
      // Close audio contexts
      if (audioContextRef.current) {
        audioContextRef.current.close().catch(() => {});
        audioContextRef.current = null;
      }
      if (playbackCtxRef.current) {
        playbackCtxRef.current.close().catch(() => {});
        playbackCtxRef.current = null;
      }
      // Clear playback queue
      playbackQueueRef.current = [];
      currentSourceRef.current = null;
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
    browserCompatibility,
  };
}
