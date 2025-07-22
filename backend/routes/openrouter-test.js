const express = require('express');
const router = express.Router();

// Test OpenRouter integration
router.post('/openrouter', async (req, res) => {
  try {
    const { message } = req.body;
    
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.OPENROUTER_API_KEY}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'http://localhost:3002',
        'X-Title': 'AI Receptionist Pro',
      },
      body: JSON.stringify({
        model: 'openai/gpt-3.5-turbo',
        messages: [
          {
            role: 'system',
            content: 'You are a helpful AI receptionist. Respond briefly and professionally.'
          },
          {
            role: 'user',
            content: message || 'Hello, can you help me?'
          }
        ],
        temperature: 0.7,
        max_tokens: 150,
      }),
    });

    if (!response.ok) {
      throw new Error(`OpenRouter API error: ${response.statusText}`);
    }

    const data = await response.json();
    res.json({
      success: true,
      response: data.choices[0]?.message?.content || 'No response generated',
      usage: data.usage
    });
    
  } catch (error) {
    console.error('OpenRouter test error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

module.exports = router;