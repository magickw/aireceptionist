const express = require('express');
const app = express();
const port = process.env.PORT || 3001;
const db = require('./database.js');
const twilio = require('twilio');
const axios = require('axios');
require('dotenv').config();
const fs = require('fs');
const FormData = require('form-data');

app.use(express.json());

app.get('/api/businesses', async (req, res) => {
  try {
    const result = await db.query('SELECT * FROM businesses', []);
    res.json({ businesses: result.rows });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/businesses', async (req, res) => {
  const { name, phone } = req.body;
  if (!name || !phone) {
    return res.status(400).json({ error: 'Name and phone are required' });
  }
  try {
    const result = await db.query(
      'INSERT INTO businesses (name, phone) VALUES ($1, $2) RETURNING *',
      [name, phone]
    );
    res.status(201).json({ business: result.rows[0] });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/bookings', async (req, res) => {
  const { business_id, customer_name, customer_phone, time } = req.body;
  if (!business_id || !customer_name || !customer_phone || !time) {
    return res.status(400).json({ error: 'business_id, customer_name, customer_phone, and time are required' });
  }
  try {
    const result = await db.query(
      'INSERT INTO bookings (business_id, customer_name, customer_phone, time) VALUES ($1, $2, $3, $4) RETURNING *',
      [business_id, customer_name, customer_phone, time]
    );
    res.status(201).json({ booking: result.rows[0] });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Placeholder for AI receptionist logic
// 1. Receive call (already handled by Twilio webhook)
// 2. Transcribe speech (STT)
// 3. Generate response (OpenAI)
// 4. Synthesize speech (TTS)
// 5. Respond to Twilio with audio

app.post('/api/twilio/voice', express.urlencoded({ extended: false }), async (req, res) => {
  console.log('Incoming call from Twilio:', req.body);
  const twiml = new twilio.twiml.VoiceResponse();
  twiml.say('Hello, this is your AI receptionist. Please state your request after the beep.');
  twiml.record({
    action: '/api/twilio/recording',
    method: 'POST',
    maxLength: 30,
    transcribe: false
  });
  twiml.say('We did not receive any input. Goodbye!');
  res.type('text/xml');
  res.send(twiml.toString());
});

// Helper: Transcribe audio with OpenAI Whisper
async function transcribeWithWhisper(audioBuffer) {
  const form = new FormData();
  form.append('file', audioBuffer, { filename: 'audio.wav' });
  form.append('model', 'whisper-1');
  try {
    const response = await axios.post('https://api.openai.com/v1/audio/transcriptions', form, {
      headers: {
        ...form.getHeaders(),
        'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`
      }
    });
    return response.data.text;
  } catch (err) {
    console.error('Whisper transcription error:', err.response?.data || err.message);
    return null;
  }
}

// Helper: Generate AI response with GPT-4o
async function generateAIResponse(transcript) {
  try {
    const response = await axios.post('https://api.openai.com/v1/chat/completions', {
      model: 'gpt-4o',
      messages: [
        { role: 'system', content: 'You are an AI receptionist for a business. Help callers with bookings and information.' },
        { role: 'user', content: transcript }
      ]
    }, {
      headers: {
        'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
        'Content-Type': 'application/json'
      }
    });
    return response.data.choices[0].message.content;
  } catch (err) {
    console.error('GPT-4o error:', err.response?.data || err.message);
    return 'Sorry, I am having trouble understanding your request.';
  }
}

// Helper: Synthesize speech with ElevenLabs
async function synthesizeSpeechElevenLabs(text) {
  try {
    const response = await axios.post(
      'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}', // Replace {voice_id} with your ElevenLabs voice ID
      {
        text,
        model_id: 'eleven_multilingual_v2',
        voice_settings: { stability: 0.5, similarity_boost: 0.5 }
      },
      {
        headers: {
          'xi-api-key': process.env.ELEVENLABS_API_KEY,
          'Content-Type': 'application/json'
        },
        responseType: 'arraybuffer'
      }
    );
    // Save audio to a file (or serve from memory)
    const audioPath = `./tmp/tts_${Date.now()}.mp3`;
    fs.writeFileSync(audioPath, response.data);
    return audioPath;
  } catch (err) {
    console.error('ElevenLabs TTS error:', err.response?.data || err.message);
    return null;
  }
}

// New endpoint to handle recording callback
app.post('/api/twilio/recording', express.urlencoded({ extended: false }), async (req, res) => {
  const recordingUrl = req.body.RecordingUrl;
  console.log('Received recording:', recordingUrl);

  try {
    // 1. Download the audio file from Twilio (add .wav extension)
    const audioResponse = await axios.get(`${recordingUrl}.wav`, { responseType: 'arraybuffer' });
    const audioBuffer = audioResponse.data;

    // 2. Transcribe with Whisper
    const transcript = await transcribeWithWhisper(audioBuffer);
    if (!transcript) throw new Error('Transcription failed');

    // 3. Generate AI response with GPT-4o
    const aiResponse = await generateAIResponse(transcript);

    // 4. Synthesize speech with ElevenLabs
    const audioPath = await synthesizeSpeechElevenLabs(aiResponse);

    const twiml = new twilio.twiml.VoiceResponse();
    if (audioPath) {
      // Serve the audio file via a public URL (you need to implement static serving for /tmp)
      const publicUrl = `${process.env.PUBLIC_URL}/tmp/${audioPath.split('/').pop()}`;
      twiml.play(publicUrl);
    } else {
      // Fallback to <Say>
      twiml.say(aiResponse);
    }
    res.type('text/xml');
    res.send(twiml.toString());
  } catch (err) {
    console.error('AI receptionist error:', err.message);
    const twiml = new twilio.twiml.VoiceResponse();
    twiml.say('Sorry, there was an error processing your request.');
    res.type('text/xml');
    res.send(twiml.toString());
  }
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
