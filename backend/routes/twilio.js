const express = require('express');
const router = express.Router();
const VoiceResponse = require('twilio').twiml.VoiceResponse;
const db = require('../database');
const OpenAI = require('openai');
const WebSocket = require('ws');
const actionProcessor = require('../services/actionProcessor');
const crmIntegration = require('../services/crmIntegration');
const axios = require('axios');

const openai = new OpenAI({
  apiKey: process.env.OPENROUTER_API_KEY || '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',
  baseURL: 'https://openrouter.ai/api/v1',
  defaultHeaders: {
    'HTTP-Referer': 'http://localhost:3002',
    'X-Title': 'AI Receptionist Pro',
  }
});

// In-memory store for conversation context (for simplicity, replace with a proper database in production)
const conversations = {}; // Store conversation history and transcript


router.post('/incoming-call', async (req, res) => {
  const twiml = new VoiceResponse();
  const callSid = req.body.CallSid;
  const fromNumber = req.body.From;

  // For now, hardcode business ID. In a real app, this would be determined by the Twilio number called.
  const businessId = 1;
  let business;
  try {
    const { rows } = await db.query('SELECT * FROM businesses WHERE id = $1', [businessId]);
    business = rows[0];
  } catch (error) {
    console.error('Error fetching business:', error);
    twiml.say('I apologize, an error occurred. Please try again later.');
    res.type('text/xml');
    return res.send(twiml.toString());
  }

  if (business && business.operating_hours) {
    const now = new Date();
    const dayOfWeek = now.getDay(); // 0 for Sunday, 1 for Monday, etc.
    const currentHour = now.getHours();

    const operatingHours = business.operating_hours[dayOfWeek];

    if (operatingHours && currentHour >= operatingHours.open && currentHour < operatingHours.close) {
      // Within operating hours
      twiml.say('Please wait while I connect you to our AI receptionist.');
      twiml.connect().stream({ 
      url: `wss://${process.env.WEBSOCKET_HOST || req.headers.host}/twilio/stream?callSid=${callSid}&businessId=${businessId}&fromNumber=${fromNumber}` 
    });
    } else {
      // Outside operating hours
      twiml.say('Thank you for calling. Our business is currently closed. Please call back during operating hours.');
      twiml.hangup();
    }
  } else {
    // No operating hours defined, assume always open or handle as per default policy
    twiml.say('Please wait while I connect you to our AI receptionist.');
    twiml.connect().stream({ 
      url: `wss://${process.env.WEBSOCKET_HOST || req.headers.host}/twilio/stream?callSid=${callSid}&businessId=${businessId}&fromNumber=${fromNumber}` 
    });
  }

  twiml.record({
    transcribe: true,
    transcribeCallback: `/twilio/recording-status?callSid=${callSid}`,
    maxLength: 3600, // Max recording length in seconds (1 hour)
    timeout: 10, // Timeout for silence in seconds
    recordingStatusCallback: `/twilio/recording-status?callSid=${callSid}`,
    recordingStatusCallbackMethod: 'POST',
  });
  twiml.hangup();

  res.type('text/xml');
  res.send(twiml.toString());
});

// WebSocket stream endpoint - temporarily disabled
/* 
router.ws('/stream', (ws, req) => {
  console.log('New WebSocket Connection');

  const callSid = req.query.callSid;
  const businessId = req.query.businessId;
  const fromNumber = req.query.fromNumber;
  let streamSid;

  ws.on('message', async function message(msg) {
    const data = JSON.parse(msg);

    if (data.event === 'start') {
      streamSid = data.start.streamSid;
      console.log(`Twilio is sending ${streamSid}`);
      conversations[streamSid] = {
        callSid: callSid,
        businessId: businessId,
        fromNumber: fromNumber,
        messages: [{
          role: 'system',
          content: 'You are an AI receptionist for a business. Your goal is to assist callers with their inquiries, book appointments, take messages, and screen leads. When screening leads, try to collect the caller\'s name, email, and the reason for their call. If a user asks to book an appointment, respond with a JSON object in the format: { "action": "book_appointment", "customer_name": "[name]", "customer_phone": "[phone]", "appointment_time": "[ISO 8601 datetime]", "service_type": "[service]" }. Otherwise, respond naturally.'
        }]
      }; // Initialize conversation history with a system message
    } else if (data.event === 'media') {
      const audio = data.media.payload;
      // Only process audio if it\'s not an empty payload
      if (audio && audio !== '') {
        try {
          // Convert base64 audio to a buffer
          const audioBuffer = Buffer.from(audio, 'base64');

          // Send to OpenAI Whisper for transcription
          const transcription = await openai.audio.transcriptions.create({
            file: audioBuffer,
            model: "whisper-1",
            response_format: "verbose_json", // Request verbose JSON to get language detection
          });

          const userMessage = transcription.text;
          const detectedLanguage = transcription.language;
          console.log(`User (${detectedLanguage}): ${userMessage}`);

          if (userMessage) {
            // Update system message with detected language
            if (detectedLanguage && conversations[streamSid].messages[0].role === 'system') {
              conversations[streamSid].messages[0].content =
                `You are an AI receptionist for a business. Your goal is to assist callers with their inquiries, book appointments, take messages, and screen leads. Respond in ${detectedLanguage}. When screening leads, try to collect the caller\'s name, email, and the reason for their call. If a user asks to book an appointment, respond with a JSON object in the format: { "action": "book_appointment", "customer_name": "[name]", "customer_phone": "[phone]", "appointment_time": "[ISO 8601 datetime]", "service_type": "[service]" }. Otherwise, respond naturally.`;
            }
            conversations[streamSid].messages.push({ role: 'user', content: userMessage });

            // Send to GPT-4o for response
            const chatCompletion = await openai.chat.completions.create({
              model: "gpt-4o",
              messages: conversations[streamSid].messages,
            });

            const aiResponse = chatCompletion.choices[0].message.content;
            console.log(`AI: ${aiResponse}`);
            conversations[streamSid].messages.push({ role: 'assistant', content: aiResponse });

            const say = async (text) => {
              // In a real scenario, this would call a TTS service and get audio.
              // For now, we\'ll just log and simulate sending data.
              console.log(`Simulating TTS for: ${text}`);
              // Simulate sending a small audio chunk
              ws.send(JSON.stringify({
                streamSid,
                event: 'media',
                media: {
                  payload: Buffer.from(text).toString('base64'), // Placeholder: actual audio would be base64 encoded
                  contentType: 'audio/x-mulaw',
                  sampleRate: 8000,
                },
              }));
            };

            // Check for actions in AI response
            try {
              const action = JSON.parse(aiResponse);
              if (action.action === 'book_appointment') {
                // For now, we\'ll use a hardcoded business ID. In a real app, this would come from the call context.
                const businessId = 1;
                const result = await actionProcessor.bookAppointment(
                  businessId,
                  action.customer_name,
                  action.customer_phone,
                  action.appointment_time,
                  action.service_type
                );
                if (result.success) {
                  await say('Your appointment has been booked successfully.');
                } else {
                  await say('I apologize, but I was unable to book the appointment. Please try again later.');
                }
              } else {
                await say(aiResponse);
              }
            } catch (e) {
              // Not a JSON action, just a regular AI response
              await say(aiResponse);
            }
          }
        } catch (error) {
          console.error('Error processing audio:', error);
        }
      }
    } else if (data.event === 'stop') {
      console.log('Call has ended');
      // Save the full transcript to the database
      const fullTranscript = conversations[streamSid].messages
        .filter(msg => msg.role === 'user' || msg.role === 'assistant')
        .map(msg => `${msg.role === 'user' ? 'Caller' : 'AI'}: ${msg.content}`)
        .join('\n');

      // For now, we\'ll use a hardcoded business ID. In a real app, this would come from the call context.
      const businessId = conversations[streamSid].businessId;
      const customerPhone = conversations[streamSid].fromNumber;

      try {
        await db.query(
          'INSERT INTO call_logs (business_id, customer_phone, call_sid, transcript) VALUES ($1, $2, $3, $4)',
          [businessId, customerPhone, callSid, fullTranscript]
        );
        console.log('Call log saved to database.');

        // Simulate lead screening and send to CRM
        const leadData = {
          phone: customerPhone,
          transcript: fullTranscript,
          // You would extract more structured lead data here from the conversation history
        };
        await crmIntegration.sendLeadToCRM(leadData);

      } catch (error) {
        console.error('Error saving call log or sending to CRM:', error);
      }

      delete conversations[streamSid]; // Clean up conversation history
    }
  });

  ws.on('close', () => {
    console.log('WebSocket connection closed');
    if (streamSid) {
      delete conversations[streamSid];
    }
  });

  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
  });
});
*/

router.post('/recording-status', async (req, res) => {
  const { CallSid, RecordingUrl, TranscriptionText, From } = req.body;
  console.log(`Recording Status Callback for CallSid: ${CallSid}`);
  console.log(`RecordingUrl: ${RecordingUrl}`);
  console.log(`TranscriptionText: ${TranscriptionText}`);

  try {
    // Find the call log entry and update it with the recording URL and full transcript
    // For now, we\'ll assume a hardcoded business ID and customer phone if not found in DB
    const businessId = 1; // This should be dynamically determined
    const customerPhone = From; // From the Twilio webhook

    // Check if a call log already exists for this CallSid (from the WebSocket stream)
    const existingCallLog = await db.query('SELECT * FROM call_logs WHERE call_sid = $1', [CallSid]);

    if (existingCallLog.rows.length > 0) {
      // Update existing call log
      await db.query(
        'UPDATE call_logs SET recording_url = $1, transcript = $2 WHERE call_sid = $3',
        [RecordingUrl, TranscriptionText || existingCallLog.rows[0].transcript, CallSid]
      );
      console.log('Updated existing call log with recording and transcription.');
    } else {
      // Create a new call log if it doesn\'t exist (e.g., if the WebSocket connection was interrupted)
      await db.query(
        'INSERT INTO call_logs (business_id, customer_phone, call_sid, transcript, recording_url) VALUES ($1, $2, $3, $4, $5)',
        [businessId, customerPhone, CallSid, TranscriptionText, RecordingUrl]
      );
      console.log('Created new call log from recording status callback.');
    }

    res.status(200).send();
  } catch (error) {
    console.error('Error processing recording status callback:', error);
    res.status(500).send();
  }
});

module.exports = router;