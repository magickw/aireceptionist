(globalThis.TURBOPACK = globalThis.TURBOPACK || []).push([typeof document === "object" ? document.currentScript : undefined, {

"[project]/src/services/aiConversationEngine.ts [app-client] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { k: __turbopack_refresh__, m: module } = __turbopack_context__;
{
__turbopack_context__.s({
    "default": ()=>__TURBOPACK__default__export__
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$swc$2f$helpers$2f$esm$2f$_define_property$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@swc/helpers/esm/_define_property.js [app-client] (ecmascript)");
;
class AIConversationEngine {
    processMessage(message, context) {
        const intent = this.detectIntent(message);
        const entities = this.extractEntities(message);
        const confidence = this.calculateConfidence(message, intent, entities);
        // Update context with extracted entities
        this.updateContext(context, entities, intent);
        // Generate appropriate response
        const response = this.generateResponse(message, intent, entities, context);
        const actions = this.determineActions(intent, entities, context);
        return {
            message: response,
            confidence,
            intent,
            entities,
            actions
        };
    }
    detectIntent(message) {
        for (const [intent, patterns] of Object.entries(this.intents)){
            for (const pattern of patterns){
                if (pattern.test(message)) {
                    return intent;
                }
            }
        }
        return 'unknown';
    }
    extractEntities(message) {
        const entities = {};
        for (const [entityType, pattern] of Object.entries(this.entities)){
            const match = message.match(pattern);
            if (match) {
                entities[entityType] = match[1] || match[0];
            }
        }
        return entities;
    }
    calculateConfidence(message, intent, entities) {
        let confidence = 0.5; // Base confidence
        // Increase confidence based on intent detection
        if (intent !== 'unknown') confidence += 0.2;
        // Increase confidence based on entities found
        const entityCount = Object.keys(entities).length;
        confidence += Math.min(entityCount * 0.1, 0.3);
        return Math.min(confidence, 1.0);
    }
    updateContext(context, entities, intent) {
        // Update customer info
        if (entities.name) context.customerInfo.name = entities.name.trim();
        if (entities.phone) context.customerInfo.phone = entities.phone;
        if (entities.email) context.customerInfo.email = entities.email;
        // Update intent if more specific
        if (intent !== 'unknown') context.intent = intent;
        // Update booking info
        if (intent === 'booking') {
            if (!context.bookingInfo) {
                context.bookingInfo = {
                    completed: false
                };
            }
            if (entities.service) context.bookingInfo.service = entities.service;
            if (entities.date) context.bookingInfo.date = entities.date;
            if (entities.time) context.bookingInfo.time = entities.time;
        }
        // Check if booking is complete
        if (context.bookingInfo) {
            context.bookingInfo.completed = !!(context.customerInfo.name && context.customerInfo.phone && context.bookingInfo.service && context.bookingInfo.date && context.bookingInfo.time);
        }
    }
    generateResponse(message, intent, entities, context) {
        const businessType = this.businessContext.type;
        switch(intent){
            case 'booking':
                return this.generateBookingResponse(entities, context, businessType);
            case 'ordering':
                return this.generateOrderingResponse(entities, context, businessType);
            case 'inquiry':
                return this.generateInquiryResponse(message, entities, context, businessType);
            case 'complaint':
                return "I understand your concern and I want to help resolve this issue. Let me connect you with a manager who can assist you better.";
            default:
                return this.generateDefaultResponse(businessType);
        }
    }
    generateBookingResponse(entities, context, businessType) {
        const booking = context.bookingInfo;
        const customer = context.customerInfo;
        if (booking === null || booking === void 0 ? void 0 : booking.completed) {
            return "Perfect! I have all the information I need. Let me book your ".concat(booking.service, " appointment for ").concat(booking.date, " at ").concat(booking.time, " under the name ").concat(customer.name, ". You'll receive a confirmation call at ").concat(customer.phone, ". Is there anything else I can help you with?");
        }
        // Ask for missing information
        if (!customer.name) {
            return "I'd be happy to help you book an appointment! May I start by getting your name?";
        }
        if (!customer.phone) {
            return "Thank you, ".concat(customer.name, "! I'll need your phone number for the appointment.");
        }
        if (!(booking === null || booking === void 0 ? void 0 : booking.service)) {
            const services = this.businessContext.services.map((s)=>s.name).join(', ');
            return "What service would you like to book? We offer: ".concat(services, ".");
        }
        if (!(booking === null || booking === void 0 ? void 0 : booking.date)) {
            return "What date would work best for your appointment?";
        }
        if (!(booking === null || booking === void 0 ? void 0 : booking.time)) {
            return "What time would you prefer for your appointment?";
        }
        return "I'd be happy to help you schedule an appointment. Let me gather some information.";
    }
    generateOrderingResponse(entities, context, businessType) {
        if (businessType !== 'restaurant') {
            return "I'd be happy to help, but we don't currently offer ordering. Would you like to schedule an appointment instead?";
        }
        const order = context.orderInfo;
        const customer = context.customerInfo;
        if (order === null || order === void 0 ? void 0 : order.completed) {
            const total = order.total || 0;
            return "Great! I have your order ready. Your total is $".concat(total.toFixed(2), ". We'll have this ready for pickup. Thank you for your order!");
        }
        if (!customer.name) {
            return "I'd be happy to take your order! May I start by getting your name?";
        }
        if (!customer.phone) {
            return "Thank you, ".concat(customer.name, "! I'll need your phone number for the order.");
        }
        return "What would you like to order today? I can tell you about our menu items if you'd like.";
    }
    generateInquiryResponse(message, entities, context, businessType) {
        const lowerMessage = message.toLowerCase();
        if (lowerMessage.includes('hours') || lowerMessage.includes('open') || lowerMessage.includes('close')) {
            return this.getBusinessHours();
        }
        if (lowerMessage.includes('menu') || lowerMessage.includes('food')) {
            if (businessType === 'restaurant') {
                return "We have a variety of delicious options! Our menu includes appetizers, main courses, and desserts. Would you like me to tell you about any specific category?";
            }
            return "Let me tell you about our services instead. We offer various treatments and consultations.";
        }
        if (lowerMessage.includes('price') || lowerMessage.includes('cost') || lowerMessage.includes('how much')) {
            return "Our pricing varies by service. Would you like me to tell you about pricing for a specific service?";
        }
        if (lowerMessage.includes('services')) {
            const services = this.businessContext.services.map((s)=>s.name).join(', ');
            return "We offer the following services: ".concat(services, ". Would you like more details about any of these?");
        }
        return "I'd be happy to help answer your question. Could you be more specific about what information you need?";
    }
    generateDefaultResponse(businessType) {
        return "Thank you for calling! I'm here to help you with appointments, answer questions about our services, or connect you with the right person. How can I assist you today?";
    }
    getBusinessHours() {
        const hours = this.businessContext.operatingHours;
        if (!hours) {
            return "We're open Monday through Friday. Please call during business hours for specific times.";
        }
        const daysOfWeek = [
            'Sunday',
            'Monday',
            'Tuesday',
            'Wednesday',
            'Thursday',
            'Friday',
            'Saturday'
        ];
        const openDays = [];
        for(let i = 0; i < 7; i++){
            const dayHours = hours[i];
            if (dayHours && !dayHours.closed) {
                openDays.push("".concat(daysOfWeek[i], " ").concat(dayHours.open, ":00 - ").concat(dayHours.close, ":00"));
            }
        }
        return "Our business hours are: ".concat(openDays.join(', '), ".");
    }
    determineActions(intent, entities, context) {
        var _context_bookingInfo, _context_orderInfo;
        const actions = [];
        if (intent === 'booking' && ((_context_bookingInfo = context.bookingInfo) === null || _context_bookingInfo === void 0 ? void 0 : _context_bookingInfo.completed)) {
            actions.push({
                type: 'create_booking',
                data: {
                    customerName: context.customerInfo.name,
                    customerPhone: context.customerInfo.phone,
                    service: context.bookingInfo.service,
                    date: context.bookingInfo.date,
                    time: context.bookingInfo.time
                },
                completed: false
            });
        }
        if (intent === 'ordering' && ((_context_orderInfo = context.orderInfo) === null || _context_orderInfo === void 0 ? void 0 : _context_orderInfo.completed)) {
            actions.push({
                type: 'create_order',
                data: {
                    customerName: context.customerInfo.name,
                    customerPhone: context.customerInfo.phone,
                    items: context.orderInfo.items,
                    total: context.orderInfo.total
                },
                completed: false
            });
        }
        if (intent === 'complaint') {
            actions.push({
                type: 'transfer_call',
                data: {
                    reason: 'complaint',
                    priority: 'high'
                },
                completed: false
            });
        }
        return actions;
    }
    generateCallSummary(messages, context) {
        var _context_bookingInfo, _context_orderInfo;
        const actionsTaken = [];
        let resolved = false;
        if ((_context_bookingInfo = context.bookingInfo) === null || _context_bookingInfo === void 0 ? void 0 : _context_bookingInfo.completed) {
            actionsTaken.push('Appointment booked');
            resolved = true;
        }
        if ((_context_orderInfo = context.orderInfo) === null || _context_orderInfo === void 0 ? void 0 : _context_orderInfo.completed) {
            actionsTaken.push('Order placed');
            resolved = true;
        }
        // Analyze sentiment based on message content
        const customerMessages = messages.filter((m)=>m.sender === 'customer');
        const sentiment = this.analyzeSentiment(customerMessages);
        // Calculate satisfaction score
        const satisfactionScore = this.calculateSatisfactionScore(sentiment, resolved, context.intent);
        // Extract key topics
        const keyTopics = this.extractKeyTopics(messages);
        return {
            satisfactionScore,
            intent: context.intent,
            resolved,
            actionsTaken,
            keyTopics,
            sentiment,
            followUpRequired: !resolved && context.intent !== 'inquiry'
        };
    }
    analyzeSentiment(messages) {
        const positiveWords = [
            'thank',
            'great',
            'good',
            'excellent',
            'perfect',
            'wonderful',
            'amazing'
        ];
        const negativeWords = [
            'bad',
            'terrible',
            'awful',
            'hate',
            'worst',
            'horrible',
            'disappointed'
        ];
        let positiveCount = 0;
        let negativeCount = 0;
        for (const message of messages){
            const content = message.content.toLowerCase();
            positiveWords.forEach((word)=>{
                if (content.includes(word)) positiveCount++;
            });
            negativeWords.forEach((word)=>{
                if (content.includes(word)) negativeCount++;
            });
        }
        if (positiveCount > negativeCount) return 'positive';
        if (negativeCount > positiveCount) return 'negative';
        return 'neutral';
    }
    calculateSatisfactionScore(sentiment, resolved, intent) {
        let score = 3.0; // Base score
        if (sentiment === 'positive') score += 1.5;
        else if (sentiment === 'negative') score -= 1.5;
        if (resolved) score += 1.0;
        if (intent === 'complaint' && !resolved) score -= 1.0;
        return Math.max(1.0, Math.min(5.0, score));
    }
    extractKeyTopics(messages) {
        const topics = new Set();
        const topicKeywords = {
            'Appointment Booking': [
                'appointment',
                'book',
                'schedule',
                'reservation'
            ],
            'Business Hours': [
                'hours',
                'open',
                'close',
                'time'
            ],
            'Services': [
                'service',
                'treatment',
                'procedure'
            ],
            'Pricing': [
                'price',
                'cost',
                'how much',
                'fee'
            ],
            'Menu/Food': [
                'menu',
                'food',
                'order',
                'delivery'
            ],
            'Contact Info': [
                'phone',
                'email',
                'address',
                'contact'
            ]
        };
        for (const message of messages){
            const content = message.content.toLowerCase();
            for (const [topic, keywords] of Object.entries(topicKeywords)){
                if (keywords.some((keyword)=>content.includes(keyword))) {
                    topics.add(topic);
                }
            }
        }
        return Array.from(topics);
    }
    constructor(businessContext){
        (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$swc$2f$helpers$2f$esm$2f$_define_property$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["_"])(this, "businessContext", void 0);
        (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$swc$2f$helpers$2f$esm$2f$_define_property$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["_"])(this, "openRouterService", void 0);
        (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$swc$2f$helpers$2f$esm$2f$_define_property$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["_"])(this, "useAdvancedAI", true); // Toggle for using OpenRouter vs rule-based
        (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$swc$2f$helpers$2f$esm$2f$_define_property$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["_"])(this, "intents", {
            booking: [
                /book.*appointment/i,
                /schedule.*appointment/i,
                /make.*reservation/i,
                /book.*reservation/i,
                /need.*appointment/i,
                /want.*appointment/i
            ],
            ordering: [
                /order/i,
                /buy/i,
                /purchase/i,
                /get.*food/i,
                /delivery/i,
                /takeout/i
            ],
            inquiry: [
                /what.*hours/i,
                /when.*open/i,
                /what.*services/i,
                /how much/i,
                /price/i,
                /cost/i,
                /menu/i
            ],
            complaint: [
                /problem/i,
                /issue/i,
                /complaint/i,
                /unhappy/i,
                /dissatisfied/i
            ]
        });
        (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$swc$2f$helpers$2f$esm$2f$_define_property$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["_"])(this, "entities", {
            name: /(?:my name is|i'm|i am|this is)\s+([a-zA-Z\s]+)/i,
            phone: /(\d{3}[-.\s]?\d{3}[-.\s]?\d{4}|\(\d{3}\)\s*\d{3}[-.\s]?\d{4})/,
            email: /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/,
            date: /(today|tomorrow|next week|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}\/\d{1,2}|\d{1,2}-\d{1,2})/i,
            time: /(\d{1,2}:\d{2}\s*(am|pm)?|\d{1,2}\s*(am|pm)|noon|morning|afternoon|evening)/i,
            service: /(?:for|book|schedule)\s+(.*?)(?:\s+(?:appointment|service|treatment))/i
        });
        this.businessContext = businessContext;
    }
}
const __TURBOPACK__default__export__ = AIConversationEngine;
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(module, globalThis.$RefreshHelpers$);
}
}}),
"[project]/src/app/call-simulator/page.tsx [app-client] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { k: __turbopack_refresh__, m: module } = __turbopack_context__;
{
__turbopack_context__.s({
    "default": ()=>CallSimulator
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = /*#__PURE__*/ __turbopack_context__.i("[project]/node_modules/next/dist/build/polyfills/process.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Container$2f$Container$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/Container/Container.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/Typography/Typography.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Box$2f$Box$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/Box/Box.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Grid$2f$Grid$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/Grid/Grid.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Card$2f$Card$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/Card/Card.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$CardContent$2f$CardContent$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/CardContent/CardContent.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$CardHeader$2f$CardHeader$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/CardHeader/CardHeader.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$TextField$2f$TextField$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/TextField/TextField.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Button$2f$Button$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/Button/Button.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$IconButton$2f$IconButton$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/IconButton/IconButton.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$List$2f$List$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/List/List.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$ListItem$2f$ListItem$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/ListItem/ListItem.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$ListItemText$2f$ListItemText$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/ListItemText/ListItemText.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Avatar$2f$Avatar$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/Avatar/Avatar.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Chip$2f$Chip$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/Chip/Chip.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Paper$2f$Paper$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/Paper/Paper.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$LinearProgress$2f$LinearProgress$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/LinearProgress/LinearProgress.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Dialog$2f$Dialog$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/Dialog/Dialog.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$DialogTitle$2f$DialogTitle$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/DialogTitle/DialogTitle.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$DialogContent$2f$DialogContent$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/DialogContent/DialogContent.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$DialogActions$2f$DialogActions$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/DialogActions/DialogActions.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Tabs$2f$Tabs$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/Tabs/Tabs.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Tab$2f$Tab$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/material/Tab/Tab.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$icons$2d$material$2f$Phone$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/icons-material/Phone.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$icons$2d$material$2f$PhoneDisabled$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/icons-material/PhoneDisabled.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$icons$2d$material$2f$Send$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/icons-material/Send.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$icons$2d$material$2f$SmartToy$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/icons-material/SmartToy.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$icons$2d$material$2f$Person$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/icons-material/Person.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$icons$2d$material$2f$CheckCircle$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/icons-material/CheckCircle.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$icons$2d$material$2f$Event$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/icons-material/Event.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$icons$2d$material$2f$ShoppingCart$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/@mui/icons-material/ShoppingCart.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$services$2f$aiConversationEngine$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/services/aiConversationEngine.ts [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$axios$2f$lib$2f$axios$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/axios/lib/axios.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
'use client';
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
;
function TabPanel(props) {
    const { children, value, index, ...other } = props;
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        role: "tabpanel",
        hidden: value !== index,
        ...other,
        children: value === index && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Box$2f$Box$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
            children: children
        }, void 0, false, {
            fileName: "[project]/src/app/call-simulator/page.tsx",
            lineNumber: 55,
            columnNumber: 27
        }, this)
    }, void 0, false, {
        fileName: "[project]/src/app/call-simulator/page.tsx",
        lineNumber: 54,
        columnNumber: 5
    }, this);
}
_c = TabPanel;
function CallSimulator() {
    _s();
    var _s1 = __turbopack_context__.k.signature();
    const [tabValue, setTabValue] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(0);
    const [currentCall, setCurrentCall] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const [messageInput, setMessageInput] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])('');
    const [isProcessing, setIsProcessing] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [businessContext, setBusinessContext] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const [aiEngine, setAiEngine] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const [completedActions, setCompletedActions] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [callSummaryOpen, setCallSummaryOpen] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const messagesEndRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const testScenarios = [
        {
            id: 'booking-basic',
            title: 'Basic Appointment Booking',
            description: 'Customer wants to book a simple appointment',
            starter: "Hi, I'd like to book an appointment for tomorrow.",
            category: 'Booking'
        },
        {
            id: 'booking-specific',
            title: 'Specific Service Booking',
            description: 'Customer requests a specific service and time',
            starter: "I need to schedule a haircut for this Friday at 2 PM.",
            category: 'Booking'
        },
        {
            id: 'restaurant-order',
            title: 'Restaurant Order',
            description: 'Customer wants to place a food order',
            starter: "I'd like to order some food for delivery.",
            category: 'Ordering'
        },
        {
            id: 'business-hours',
            title: 'Business Hours Inquiry',
            description: 'Customer asks about operating hours',
            starter: "What are your business hours?",
            category: 'Information'
        },
        {
            id: 'services-inquiry',
            title: 'Services Information',
            description: 'Customer wants to know about available services',
            starter: "What services do you offer?",
            category: 'Information'
        },
        {
            id: 'pricing-inquiry',
            title: 'Pricing Information',
            description: 'Customer asks about service pricing',
            starter: "How much does a consultation cost?",
            category: 'Information'
        },
        {
            id: 'complaint',
            title: 'Customer Complaint',
            description: 'Customer has an issue to resolve',
            starter: "I had a terrible experience last time and want to speak to a manager.",
            category: 'Support'
        },
        {
            id: 'complex-booking',
            title: 'Complex Booking Request',
            description: 'Customer with multiple requirements',
            starter: "My name is Sarah Johnson, I need to book a spa treatment for next Tuesday afternoon, preferably around 3 PM. My number is 555-123-4567.",
            category: 'Booking'
        }
    ];
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "CallSimulator.useEffect": ()=>{
            const fetchBusinessContext = {
                "CallSimulator.useEffect.fetchBusinessContext": async ()=>{
                    try {
                        const businessResponse = await __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$axios$2f$lib$2f$axios$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].get("".concat(("TURBOPACK compile-time value", "http://localhost:3001"), "/api/businesses"));
                        if (businessResponse.data.length > 0) {
                            const business = businessResponse.data[0];
                            // Mock services and menu data
                            const context = {
                                ...business,
                                services: [
                                    {
                                        id: '1',
                                        name: 'Consultation',
                                        description: 'Initial consultation',
                                        duration: 30,
                                        price: 50,
                                        category: 'General'
                                    },
                                    {
                                        id: '2',
                                        name: 'Haircut',
                                        description: 'Professional haircut',
                                        duration: 45,
                                        price: 80,
                                        category: 'Hair'
                                    },
                                    {
                                        id: '3',
                                        name: 'Massage',
                                        description: 'Relaxing massage',
                                        duration: 60,
                                        price: 120,
                                        category: 'Wellness'
                                    },
                                    {
                                        id: '4',
                                        name: 'Facial',
                                        description: 'Rejuvenating facial',
                                        duration: 90,
                                        price: 150,
                                        category: 'Skincare'
                                    }
                                ],
                                menu: business.type === 'restaurant' ? [
                                    {
                                        id: '1',
                                        name: 'Caesar Salad',
                                        description: 'Fresh romaine lettuce with parmesan',
                                        price: 12.99,
                                        category: 'Salads',
                                        available: true
                                    },
                                    {
                                        id: '2',
                                        name: 'Grilled Chicken',
                                        description: 'Herb-seasoned grilled chicken breast',
                                        price: 18.99,
                                        category: 'Main Course',
                                        available: true
                                    },
                                    {
                                        id: '3',
                                        name: 'Pasta Carbonara',
                                        description: 'Classic Italian pasta with cream sauce',
                                        price: 16.99,
                                        category: 'Pasta',
                                        available: true
                                    }
                                ] : []
                            };
                            setBusinessContext(context);
                            setAiEngine(new __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$services$2f$aiConversationEngine$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"](context));
                        }
                    } catch (error) {
                        console.error('Error fetching business context:', error);
                    }
                }
            }["CallSimulator.useEffect.fetchBusinessContext"];
            fetchBusinessContext();
        }
    }["CallSimulator.useEffect"], []);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "CallSimulator.useEffect": ()=>{
            scrollToBottom();
        }
    }["CallSimulator.useEffect"], [
        currentCall === null || currentCall === void 0 ? void 0 : currentCall.messages
    ]);
    const scrollToBottom = ()=>{
        var _messagesEndRef_current;
        (_messagesEndRef_current = messagesEndRef.current) === null || _messagesEndRef_current === void 0 ? void 0 : _messagesEndRef_current.scrollIntoView({
            behavior: 'smooth'
        });
    };
    const handleTabChange = (event, newValue)=>{
        setTabValue(newValue);
    };
    const startCall = function() {
        let customerPhone = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : '+1 (555) 123-4567';
        const newCall = {
            id: "call-".concat(Date.now()),
            customerPhone,
            status: 'active',
            startTime: new Date(),
            messages: [],
            context: {
                customerInfo: {},
                intent: 'unknown',
                businessContext: businessContext
            }
        };
        setCurrentCall(newCall);
        setCompletedActions([]);
        // AI greeting
        setTimeout(()=>{
            addAIMessage("Hello! Thank you for calling. I'm your AI assistant. How can I help you today?");
        }, 1000);
    };
    const endCall = ()=>{
        if (!currentCall || !aiEngine) return;
        const updatedCall = {
            ...currentCall,
            status: 'ended',
            endTime: new Date(),
            summary: aiEngine.generateCallSummary(currentCall.messages, currentCall.context)
        };
        setCurrentCall(updatedCall);
        setCallSummaryOpen(true);
    };
    const addMessage = function(content, sender) {
        let type = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : 'text';
        if (!currentCall) return;
        const message = {
            id: "msg-".concat(Date.now()),
            timestamp: new Date(),
            sender,
            content,
            type
        };
        setCurrentCall({
            ...currentCall,
            messages: [
                ...currentCall.messages,
                message
            ]
        });
    };
    const addAIMessage = function(content) {
        let type = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : 'text';
        addMessage(content, 'ai', type);
    };
    const sendMessage = async ()=>{
        if (!messageInput.trim() || !currentCall || !aiEngine) return;
        const userMessage = messageInput.trim();
        setMessageInput('');
        setIsProcessing(true);
        // Add user message
        addMessage(userMessage, 'customer');
        // Process with AI
        try {
            await new Promise((resolve)=>setTimeout(resolve, 1500)); // Simulate processing time
            const aiResponse = aiEngine.processMessage(userMessage, currentCall.context);
            // Add AI response
            addAIMessage(aiResponse.message);
            // Execute actions
            if (aiResponse.actions.length > 0) {
                for (const action of aiResponse.actions){
                    await executeAction(action);
                }
            }
            // Update call context
            setCurrentCall({
                ...currentCall,
                context: currentCall.context
            });
        } catch (error) {
            console.error('Error processing message:', error);
            addAIMessage("I apologize, I'm having trouble processing your request. Let me connect you with a human agent.");
        } finally{
            setIsProcessing(false);
        }
    };
    const executeAction = async (action)=>{
        switch(action.type){
            case 'create_booking':
                await createBooking(action.data);
                break;
            case 'create_order':
                await createOrder(action.data);
                break;
            case 'transfer_call':
                addAIMessage("I'm transferring you to a specialist who can better assist you.", 'system');
                break;
        }
    };
    const createBooking = async (bookingData)=>{
        try {
            // Mock API call
            await new Promise((resolve)=>setTimeout(resolve, 1000));
            const booking = {
                id: Date.now(),
                ...bookingData,
                status: 'confirmed',
                createdAt: new Date()
            };
            setCompletedActions((prev)=>[
                    ...prev,
                    {
                        type: 'booking',
                        data: booking
                    }
                ]);
            addAIMessage("✅ Perfect! I've successfully booked your ".concat(bookingData.service, " appointment for ").concat(bookingData.date, " at ").concat(bookingData.time, ". You'll receive a confirmation shortly."), 'action');
        } catch (error) {
            addAIMessage("I'm sorry, there was an issue creating your booking. Let me connect you with someone who can help.");
        }
    };
    const createOrder = async (orderData)=>{
        try {
            var _orderData_total;
            // Mock API call
            await new Promise((resolve)=>setTimeout(resolve, 1000));
            const order = {
                id: Date.now(),
                ...orderData,
                status: 'confirmed',
                createdAt: new Date()
            };
            setCompletedActions((prev)=>[
                    ...prev,
                    {
                        type: 'order',
                        data: order
                    }
                ]);
            addAIMessage("✅ Great! Your order has been placed. Total: $".concat(((_orderData_total = orderData.total) === null || _orderData_total === void 0 ? void 0 : _orderData_total.toFixed(2)) || '0.00', ". We'll have it ready for you soon!"), 'action');
        } catch (error) {
            addAIMessage("I'm sorry, there was an issue placing your order. Let me connect you with someone who can help.");
        }
    };
    const handleKeyPress = (event)=>{
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    };
    const useTestScenario = (scenario)=>{
        if (!currentCall) {
            startCall();
            setTimeout(()=>{
                setMessageInput(scenario.starter);
            }, 1500);
        } else {
            setMessageInput(scenario.starter);
        }
    };
    const formatDuration = (startTime, endTime)=>{
        const end = endTime || new Date();
        const duration = Math.floor((end.getTime() - startTime.getTime()) / 1000);
        const minutes = Math.floor(duration / 60);
        const seconds = duration % 60;
        return "".concat(minutes, ":").concat(seconds.toString().padStart(2, '0'));
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Container$2f$Container$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
        maxWidth: "xl",
        sx: {
            mt: 4,
            mb: 4
        },
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Box$2f$Box$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                sx: {
                    mb: 4
                },
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                        variant: "h4",
                        component: "h1",
                        gutterBottom: true,
                        sx: {
                            fontWeight: 'bold',
                            color: 'primary.main'
                        },
                        children: "AI Call Simulator"
                    }, void 0, false, {
                        fileName: "[project]/src/app/call-simulator/page.tsx",
                        lineNumber: 357,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                        variant: "body1",
                        color: "text.secondary",
                        children: "Test your AI receptionist with realistic call scenarios"
                    }, void 0, false, {
                        fileName: "[project]/src/app/call-simulator/page.tsx",
                        lineNumber: 360,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/app/call-simulator/page.tsx",
                lineNumber: 356,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Tabs$2f$Tabs$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                value: tabValue,
                onChange: handleTabChange,
                sx: {
                    mb: 3
                },
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Tab$2f$Tab$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                        label: "Call Simulation"
                    }, void 0, false, {
                        fileName: "[project]/src/app/call-simulator/page.tsx",
                        lineNumber: 366,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Tab$2f$Tab$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                        label: "Test Scenarios"
                    }, void 0, false, {
                        fileName: "[project]/src/app/call-simulator/page.tsx",
                        lineNumber: 367,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Tab$2f$Tab$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                        label: "Performance Analytics"
                    }, void 0, false, {
                        fileName: "[project]/src/app/call-simulator/page.tsx",
                        lineNumber: 368,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/app/call-simulator/page.tsx",
                lineNumber: 365,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(TabPanel, {
                value: tabValue,
                index: 0,
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Grid$2f$Grid$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                    container: true,
                    spacing: 3,
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Grid$2f$Grid$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                            item: true,
                            xs: 12,
                            lg: 8,
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Card$2f$Card$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                sx: {
                                    height: '600px',
                                    display: 'flex',
                                    flexDirection: 'column'
                                },
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$CardHeader$2f$CardHeader$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                        avatar: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Avatar$2f$Avatar$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                            sx: {
                                                bgcolor: (currentCall === null || currentCall === void 0 ? void 0 : currentCall.status) === 'active' ? 'success.main' : 'grey.500'
                                            },
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$icons$2d$material$2f$Phone$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {}, void 0, false, {
                                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                                lineNumber: 379,
                                                columnNumber: 21
                                            }, void 0)
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                            lineNumber: 378,
                                            columnNumber: 19
                                        }, void 0),
                                        title: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Box$2f$Box$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                            sx: {
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: 2
                                            },
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                    variant: "h6",
                                                    children: currentCall ? "Call with ".concat(currentCall.customerPhone) : 'No Active Call'
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                                    lineNumber: 384,
                                                    columnNumber: 21
                                                }, void 0),
                                                currentCall && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Chip$2f$Chip$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                    label: currentCall.status.toUpperCase(),
                                                    color: currentCall.status === 'active' ? 'success' : 'default',
                                                    size: "small"
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                                    lineNumber: 388,
                                                    columnNumber: 23
                                                }, void 0)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                            lineNumber: 383,
                                            columnNumber: 19
                                        }, void 0),
                                        subheader: currentCall && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                            variant: "body2",
                                            children: [
                                                "Duration: ",
                                                formatDuration(currentCall.startTime, currentCall.endTime)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                            lineNumber: 398,
                                            columnNumber: 21
                                        }, void 0),
                                        action: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Box$2f$Box$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                            sx: {
                                                display: 'flex',
                                                gap: 1
                                            },
                                            children: !currentCall ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Button$2f$Button$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                variant: "contained",
                                                color: "success",
                                                startIcon: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$icons$2d$material$2f$Phone$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {}, void 0, false, {
                                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                                    lineNumber: 409,
                                                    columnNumber: 36
                                                }, void 0),
                                                onClick: ()=>startCall(),
                                                children: "Start Call"
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                                lineNumber: 406,
                                                columnNumber: 23
                                            }, void 0) : currentCall.status === 'active' ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Button$2f$Button$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                variant: "contained",
                                                color: "error",
                                                startIcon: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$icons$2d$material$2f$PhoneDisabled$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {}, void 0, false, {
                                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                                    lineNumber: 418,
                                                    columnNumber: 36
                                                }, void 0),
                                                onClick: endCall,
                                                children: "End Call"
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                                lineNumber: 415,
                                                columnNumber: 23
                                            }, void 0) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Button$2f$Button$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                variant: "contained",
                                                color: "primary",
                                                startIcon: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$icons$2d$material$2f$Phone$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {}, void 0, false, {
                                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                                    lineNumber: 427,
                                                    columnNumber: 36
                                                }, void 0),
                                                onClick: ()=>startCall(),
                                                children: "New Call"
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                                lineNumber: 424,
                                                columnNumber: 23
                                            }, void 0)
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                            lineNumber: 404,
                                            columnNumber: 19
                                        }, void 0)
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                        lineNumber: 376,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$CardContent$2f$CardContent$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                        sx: {
                                            flexGrow: 1,
                                            display: 'flex',
                                            flexDirection: 'column',
                                            p: 0
                                        },
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Box$2f$Box$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                sx: {
                                                    flexGrow: 1,
                                                    overflow: 'auto',
                                                    p: 2
                                                },
                                                children: !currentCall ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Box$2f$Box$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                    sx: {
                                                        textAlign: 'center',
                                                        py: 8
                                                    },
                                                    children: [
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                            variant: "h6",
                                                            color: "text.secondary",
                                                            gutterBottom: true,
                                                            children: "Start a call to begin testing"
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                                            lineNumber: 442,
                                                            columnNumber: 23
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                            variant: "body2",
                                                            color: "text.secondary",
                                                            children: 'Click "Start Call" to simulate an incoming customer call'
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                                            lineNumber: 445,
                                                            columnNumber: 23
                                                        }, this)
                                                    ]
                                                }, void 0, true, {
                                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                                    lineNumber: 441,
                                                    columnNumber: 21
                                                }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$List$2f$List$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                    sx: {
                                                        p: 0
                                                    },
                                                    children: [
                                                        currentCall.messages.map((message)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$ListItem$2f$ListItem$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                sx: {
                                                                    flexDirection: 'column',
                                                                    alignItems: message.sender === 'customer' ? 'flex-end' : 'flex-start',
                                                                    p: 1
                                                                },
                                                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Paper$2f$Paper$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                    sx: {
                                                                        p: 2,
                                                                        maxWidth: '80%',
                                                                        bgcolor: message.sender === 'customer' ? 'primary.main' : message.type === 'action' ? 'success.light' : message.type === 'system' ? 'warning.light' : 'grey.100',
                                                                        color: message.sender === 'customer' ? 'primary.contrastText' : 'text.primary'
                                                                    },
                                                                    children: [
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Box$2f$Box$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                            sx: {
                                                                                display: 'flex',
                                                                                alignItems: 'center',
                                                                                gap: 1,
                                                                                mb: 1
                                                                            },
                                                                            children: [
                                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Avatar$2f$Avatar$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                                    sx: {
                                                                                        width: 24,
                                                                                        height: 24
                                                                                    },
                                                                                    children: message.sender === 'customer' ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$icons$2d$material$2f$Person$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {}, void 0, false, {
                                                                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                                        lineNumber: 472,
                                                                                        columnNumber: 66
                                                                                    }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$icons$2d$material$2f$SmartToy$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {}, void 0, false, {
                                                                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                                        lineNumber: 472,
                                                                                        columnNumber: 83
                                                                                    }, this)
                                                                                }, void 0, false, {
                                                                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                                    lineNumber: 471,
                                                                                    columnNumber: 31
                                                                                }, this),
                                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                                    variant: "caption",
                                                                                    children: message.sender === 'customer' ? 'Customer' : 'AI Assistant'
                                                                                }, void 0, false, {
                                                                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                                    lineNumber: 474,
                                                                                    columnNumber: 31
                                                                                }, this),
                                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                                    variant: "caption",
                                                                                    color: "text.secondary",
                                                                                    children: message.timestamp.toLocaleTimeString()
                                                                                }, void 0, false, {
                                                                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                                    lineNumber: 477,
                                                                                    columnNumber: 31
                                                                                }, this)
                                                                            ]
                                                                        }, void 0, true, {
                                                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                            lineNumber: 470,
                                                                            columnNumber: 29
                                                                        }, this),
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                            variant: "body2",
                                                                            children: message.content
                                                                        }, void 0, false, {
                                                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                            lineNumber: 481,
                                                                            columnNumber: 29
                                                                        }, this)
                                                                    ]
                                                                }, void 0, true, {
                                                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                    lineNumber: 460,
                                                                    columnNumber: 27
                                                                }, this)
                                                            }, message.id, false, {
                                                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                lineNumber: 452,
                                                                columnNumber: 25
                                                            }, this)),
                                                        isProcessing && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$ListItem$2f$ListItem$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                            sx: {
                                                                flexDirection: 'column',
                                                                alignItems: 'flex-start',
                                                                p: 1
                                                            },
                                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Paper$2f$Paper$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                sx: {
                                                                    p: 2,
                                                                    bgcolor: 'grey.100'
                                                                },
                                                                children: [
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Box$2f$Box$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                        sx: {
                                                                            display: 'flex',
                                                                            alignItems: 'center',
                                                                            gap: 1
                                                                        },
                                                                        children: [
                                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Avatar$2f$Avatar$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                                sx: {
                                                                                    width: 24,
                                                                                    height: 24
                                                                                },
                                                                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$icons$2d$material$2f$SmartToy$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {}, void 0, false, {
                                                                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                                    lineNumber: 490,
                                                                                    columnNumber: 33
                                                                                }, this)
                                                                            }, void 0, false, {
                                                                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                                lineNumber: 489,
                                                                                columnNumber: 31
                                                                            }, this),
                                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                                variant: "caption",
                                                                                children: "AI Assistant is thinking..."
                                                                            }, void 0, false, {
                                                                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                                lineNumber: 492,
                                                                                columnNumber: 31
                                                                            }, this)
                                                                        ]
                                                                    }, void 0, true, {
                                                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                        lineNumber: 488,
                                                                        columnNumber: 29
                                                                    }, this),
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$LinearProgress$2f$LinearProgress$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                        sx: {
                                                                            mt: 1,
                                                                            width: 200
                                                                        }
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                        lineNumber: 494,
                                                                        columnNumber: 29
                                                                    }, this)
                                                                ]
                                                            }, void 0, true, {
                                                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                lineNumber: 487,
                                                                columnNumber: 27
                                                            }, this)
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                                            lineNumber: 486,
                                                            columnNumber: 25
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                            ref: messagesEndRef
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                                            lineNumber: 498,
                                                            columnNumber: 23
                                                        }, this)
                                                    ]
                                                }, void 0, true, {
                                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                                    lineNumber: 450,
                                                    columnNumber: 21
                                                }, this)
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                                lineNumber: 439,
                                                columnNumber: 17
                                            }, this),
                                            (currentCall === null || currentCall === void 0 ? void 0 : currentCall.status) === 'active' && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Box$2f$Box$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                sx: {
                                                    p: 2,
                                                    borderTop: 1,
                                                    borderColor: 'divider'
                                                },
                                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Box$2f$Box$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                    sx: {
                                                        display: 'flex',
                                                        gap: 1
                                                    },
                                                    children: [
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$TextField$2f$TextField$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                            fullWidth: true,
                                                            variant: "outlined",
                                                            placeholder: "Type your message as the customer...",
                                                            value: messageInput,
                                                            onChange: (e)=>setMessageInput(e.target.value),
                                                            onKeyPress: handleKeyPress,
                                                            disabled: isProcessing,
                                                            multiline: true,
                                                            maxRows: 3
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                                            lineNumber: 507,
                                                            columnNumber: 23
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$IconButton$2f$IconButton$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                            color: "primary",
                                                            onClick: sendMessage,
                                                            disabled: !messageInput.trim() || isProcessing,
                                                            sx: {
                                                                alignSelf: 'flex-end'
                                                            },
                                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$icons$2d$material$2f$Send$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {}, void 0, false, {
                                                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                lineNumber: 524,
                                                                columnNumber: 25
                                                            }, this)
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                                            lineNumber: 518,
                                                            columnNumber: 23
                                                        }, this)
                                                    ]
                                                }, void 0, true, {
                                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                                    lineNumber: 506,
                                                    columnNumber: 21
                                                }, this)
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                                lineNumber: 505,
                                                columnNumber: 19
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                        lineNumber: 438,
                                        columnNumber: 15
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                lineNumber: 375,
                                columnNumber: 13
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/src/app/call-simulator/page.tsx",
                            lineNumber: 374,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Grid$2f$Grid$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                            item: true,
                            xs: 12,
                            lg: 4,
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Grid$2f$Grid$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                container: true,
                                spacing: 2,
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Grid$2f$Grid$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                        item: true,
                                        xs: 12,
                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Card$2f$Card$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$CardHeader$2f$CardHeader$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                    title: "Call Context"
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                                    lineNumber: 539,
                                                    columnNumber: 19
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$CardContent$2f$CardContent$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                    children: currentCall ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Box$2f$Box$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                variant: "subtitle2",
                                                                gutterBottom: true,
                                                                children: "Customer Info:"
                                                            }, void 0, false, {
                                                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                lineNumber: 543,
                                                                columnNumber: 25
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Box$2f$Box$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                sx: {
                                                                    mb: 2
                                                                },
                                                                children: [
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                        variant: "body2",
                                                                        children: [
                                                                            "Name: ",
                                                                            currentCall.context.customerInfo.name || 'Not provided'
                                                                        ]
                                                                    }, void 0, true, {
                                                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                        lineNumber: 545,
                                                                        columnNumber: 27
                                                                    }, this),
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                        variant: "body2",
                                                                        children: [
                                                                            "Phone: ",
                                                                            currentCall.context.customerInfo.phone || 'Not provided'
                                                                        ]
                                                                    }, void 0, true, {
                                                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                        lineNumber: 548,
                                                                        columnNumber: 27
                                                                    }, this),
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                        variant: "body2",
                                                                        children: [
                                                                            "Email: ",
                                                                            currentCall.context.customerInfo.email || 'Not provided'
                                                                        ]
                                                                    }, void 0, true, {
                                                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                        lineNumber: 551,
                                                                        columnNumber: 27
                                                                    }, this)
                                                                ]
                                                            }, void 0, true, {
                                                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                lineNumber: 544,
                                                                columnNumber: 25
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                variant: "subtitle2",
                                                                gutterBottom: true,
                                                                children: "Intent:"
                                                            }, void 0, false, {
                                                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                lineNumber: 556,
                                                                columnNumber: 25
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Chip$2f$Chip$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                label: currentCall.context.intent,
                                                                color: "primary",
                                                                size: "small",
                                                                sx: {
                                                                    mb: 2
                                                                }
                                                            }, void 0, false, {
                                                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                lineNumber: 557,
                                                                columnNumber: 25
                                                            }, this),
                                                            currentCall.context.bookingInfo && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Box$2f$Box$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                sx: {
                                                                    mb: 2
                                                                },
                                                                children: [
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                        variant: "subtitle2",
                                                                        gutterBottom: true,
                                                                        children: "Booking Info:"
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                        lineNumber: 561,
                                                                        columnNumber: 29
                                                                    }, this),
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                        variant: "body2",
                                                                        children: [
                                                                            "Service: ",
                                                                            currentCall.context.bookingInfo.service || 'Not specified'
                                                                        ]
                                                                    }, void 0, true, {
                                                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                        lineNumber: 562,
                                                                        columnNumber: 29
                                                                    }, this),
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                        variant: "body2",
                                                                        children: [
                                                                            "Date: ",
                                                                            currentCall.context.bookingInfo.date || 'Not specified'
                                                                        ]
                                                                    }, void 0, true, {
                                                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                        lineNumber: 565,
                                                                        columnNumber: 29
                                                                    }, this),
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                        variant: "body2",
                                                                        children: [
                                                                            "Time: ",
                                                                            currentCall.context.bookingInfo.time || 'Not specified'
                                                                        ]
                                                                    }, void 0, true, {
                                                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                        lineNumber: 568,
                                                                        columnNumber: 29
                                                                    }, this),
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Chip$2f$Chip$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                        label: currentCall.context.bookingInfo.completed ? 'Complete' : 'Incomplete',
                                                                        color: currentCall.context.bookingInfo.completed ? 'success' : 'warning',
                                                                        size: "small",
                                                                        sx: {
                                                                            mt: 1
                                                                        }
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                        lineNumber: 571,
                                                                        columnNumber: 29
                                                                    }, this)
                                                                ]
                                                            }, void 0, true, {
                                                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                lineNumber: 560,
                                                                columnNumber: 27
                                                            }, this)
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                                        lineNumber: 542,
                                                        columnNumber: 23
                                                    }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                        variant: "body2",
                                                        color: "text.secondary",
                                                        children: "Start a call to see context information"
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                                        lineNumber: 581,
                                                        columnNumber: 23
                                                    }, this)
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                                    lineNumber: 540,
                                                    columnNumber: 19
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                            lineNumber: 538,
                                            columnNumber: 17
                                        }, this)
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                        lineNumber: 537,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Grid$2f$Grid$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                        item: true,
                                        xs: 12,
                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Card$2f$Card$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$CardHeader$2f$CardHeader$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                    title: "Actions Completed"
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                                    lineNumber: 592,
                                                    columnNumber: 19
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$CardContent$2f$CardContent$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                    children: completedActions.length === 0 ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                        variant: "body2",
                                                        color: "text.secondary",
                                                        children: "No actions completed yet"
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                                        lineNumber: 595,
                                                        columnNumber: 23
                                                    }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$List$2f$List$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                        sx: {
                                                            p: 0
                                                        },
                                                        children: completedActions.map((action, index)=>{
                                                            var _action_data_total;
                                                            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$ListItem$2f$ListItem$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                sx: {
                                                                    p: 1
                                                                },
                                                                children: [
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Avatar$2f$Avatar$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                        sx: {
                                                                            mr: 2,
                                                                            bgcolor: 'success.main'
                                                                        },
                                                                        children: action.type === 'booking' ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$icons$2d$material$2f$Event$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {}, void 0, false, {
                                                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                            lineNumber: 603,
                                                                            columnNumber: 60
                                                                        }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$icons$2d$material$2f$ShoppingCart$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {}, void 0, false, {
                                                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                            lineNumber: 603,
                                                                            columnNumber: 76
                                                                        }, this)
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                        lineNumber: 602,
                                                                        columnNumber: 29
                                                                    }, this),
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$ListItemText$2f$ListItemText$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                        primary: action.type === 'booking' ? "Appointment Booked: ".concat(action.data.service) : "Order Placed: $".concat((_action_data_total = action.data.total) === null || _action_data_total === void 0 ? void 0 : _action_data_total.toFixed(2)),
                                                                        secondary: "Customer: ".concat(action.data.customerName)
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                        lineNumber: 605,
                                                                        columnNumber: 29
                                                                    }, this),
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$icons$2d$material$2f$CheckCircle$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                                        color: "success"
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                        lineNumber: 613,
                                                                        columnNumber: 29
                                                                    }, this)
                                                                ]
                                                            }, index, true, {
                                                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                                                lineNumber: 601,
                                                                columnNumber: 27
                                                            }, this);
                                                        })
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                                        lineNumber: 599,
                                                        columnNumber: 23
                                                    }, this)
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                                    lineNumber: 593,
                                                    columnNumber: 19
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                            lineNumber: 591,
                                            columnNumber: 17
                                        }, this)
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                        lineNumber: 590,
                                        columnNumber: 15
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                lineNumber: 535,
                                columnNumber: 13
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/src/app/call-simulator/page.tsx",
                            lineNumber: 534,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/src/app/call-simulator/page.tsx",
                    lineNumber: 372,
                    columnNumber: 9
                }, this)
            }, void 0, false, {
                fileName: "[project]/src/app/call-simulator/page.tsx",
                lineNumber: 371,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(TabPanel, {
                value: tabValue,
                index: 1,
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Grid$2f$Grid$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                    container: true,
                    spacing: 3,
                    children: [
                        'Booking',
                        'Ordering',
                        'Information',
                        'Support'
                    ].map((category)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Grid$2f$Grid$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                            item: true,
                            xs: 12,
                            md: 6,
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Card$2f$Card$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$CardHeader$2f$CardHeader$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                        title: "".concat(category, " Scenarios")
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                        lineNumber: 632,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$CardContent$2f$CardContent$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$List$2f$List$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                            children: testScenarios.filter((scenario)=>scenario.category === category).map((scenario)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$ListItem$2f$ListItem$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                    divider: true,
                                                    children: [
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$ListItemText$2f$ListItemText$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                            primary: scenario.title,
                                                            secondary: scenario.description
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                                            lineNumber: 639,
                                                            columnNumber: 27
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Button$2f$Button$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                            variant: "outlined",
                                                            size: "small",
                                                            onClick: _s1(()=>{
                                                                _s1();
                                                                return useTestScenario(scenario);
                                                            }, "LwlKLZ9vYnPSaNSS5fID/Gei0Mk=", false, function() {
                                                                return [
                                                                    useTestScenario
                                                                ];
                                                            }),
                                                            children: "Test"
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                                            lineNumber: 643,
                                                            columnNumber: 27
                                                        }, this)
                                                    ]
                                                }, scenario.id, true, {
                                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                                    lineNumber: 638,
                                                    columnNumber: 25
                                                }, this))
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                            lineNumber: 634,
                                            columnNumber: 19
                                        }, this)
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/call-simulator/page.tsx",
                                        lineNumber: 633,
                                        columnNumber: 17
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                lineNumber: 631,
                                columnNumber: 15
                            }, this)
                        }, category, false, {
                            fileName: "[project]/src/app/call-simulator/page.tsx",
                            lineNumber: 630,
                            columnNumber: 13
                        }, this))
                }, void 0, false, {
                    fileName: "[project]/src/app/call-simulator/page.tsx",
                    lineNumber: 628,
                    columnNumber: 9
                }, this)
            }, void 0, false, {
                fileName: "[project]/src/app/call-simulator/page.tsx",
                lineNumber: 626,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(TabPanel, {
                value: tabValue,
                index: 2,
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Card$2f$Card$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$CardHeader$2f$CardHeader$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                            title: "AI Performance Analytics"
                        }, void 0, false, {
                            fileName: "[project]/src/app/call-simulator/page.tsx",
                            lineNumber: 663,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$CardContent$2f$CardContent$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                variant: "body1",
                                color: "text.secondary",
                                sx: {
                                    textAlign: 'center',
                                    py: 4
                                },
                                children: "Performance analytics will show after completing test calls. Metrics include response accuracy, conversation success rate, and customer satisfaction scores."
                            }, void 0, false, {
                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                lineNumber: 665,
                                columnNumber: 13
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/src/app/call-simulator/page.tsx",
                            lineNumber: 664,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/src/app/call-simulator/page.tsx",
                    lineNumber: 662,
                    columnNumber: 9
                }, this)
            }, void 0, false, {
                fileName: "[project]/src/app/call-simulator/page.tsx",
                lineNumber: 660,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Dialog$2f$Dialog$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                open: callSummaryOpen,
                onClose: ()=>setCallSummaryOpen(false),
                maxWidth: "md",
                fullWidth: true,
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$DialogTitle$2f$DialogTitle$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                        children: "Call Summary"
                    }, void 0, false, {
                        fileName: "[project]/src/app/call-simulator/page.tsx",
                        lineNumber: 680,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$DialogContent$2f$DialogContent$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                        children: (currentCall === null || currentCall === void 0 ? void 0 : currentCall.summary) && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Grid$2f$Grid$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                            container: true,
                            spacing: 2,
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Grid$2f$Grid$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                    item: true,
                                    xs: 12,
                                    sm: 6,
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                            variant: "subtitle2",
                                            gutterBottom: true,
                                            children: "Satisfaction Score"
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                            lineNumber: 685,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                            variant: "h4",
                                            color: "primary",
                                            children: [
                                                currentCall.summary.satisfactionScore.toFixed(1),
                                                "/5.0"
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                            lineNumber: 686,
                                            columnNumber: 17
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                    lineNumber: 684,
                                    columnNumber: 15
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Grid$2f$Grid$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                    item: true,
                                    xs: 12,
                                    sm: 6,
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                            variant: "subtitle2",
                                            gutterBottom: true,
                                            children: "Resolution Status"
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                            lineNumber: 691,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Chip$2f$Chip$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                            label: currentCall.summary.resolved ? 'Resolved' : 'Unresolved',
                                            color: currentCall.summary.resolved ? 'success' : 'warning'
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                            lineNumber: 692,
                                            columnNumber: 17
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                    lineNumber: 690,
                                    columnNumber: 15
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Grid$2f$Grid$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                    item: true,
                                    xs: 12,
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                            variant: "subtitle2",
                                            gutterBottom: true,
                                            children: "Actions Taken"
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                            lineNumber: 698,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Box$2f$Box$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                            sx: {
                                                display: 'flex',
                                                gap: 1,
                                                flexWrap: 'wrap'
                                            },
                                            children: currentCall.summary.actionsTaken.map((action, index)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Chip$2f$Chip$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                    label: action,
                                                    variant: "outlined"
                                                }, index, false, {
                                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                                    lineNumber: 701,
                                                    columnNumber: 21
                                                }, this))
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                            lineNumber: 699,
                                            columnNumber: 17
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                    lineNumber: 697,
                                    columnNumber: 15
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Grid$2f$Grid$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                    item: true,
                                    xs: 12,
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Typography$2f$Typography$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                            variant: "subtitle2",
                                            gutterBottom: true,
                                            children: "Key Topics"
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                            lineNumber: 706,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Box$2f$Box$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                            sx: {
                                                display: 'flex',
                                                gap: 1,
                                                flexWrap: 'wrap'
                                            },
                                            children: currentCall.summary.keyTopics.map((topic, index)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Chip$2f$Chip$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                                    label: topic,
                                                    color: "primary",
                                                    variant: "outlined"
                                                }, index, false, {
                                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                                    lineNumber: 709,
                                                    columnNumber: 21
                                                }, this))
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/call-simulator/page.tsx",
                                            lineNumber: 707,
                                            columnNumber: 17
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/call-simulator/page.tsx",
                                    lineNumber: 705,
                                    columnNumber: 15
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/src/app/call-simulator/page.tsx",
                            lineNumber: 683,
                            columnNumber: 13
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/src/app/call-simulator/page.tsx",
                        lineNumber: 681,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$DialogActions$2f$DialogActions$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Button$2f$Button$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                onClick: ()=>setCallSummaryOpen(false),
                                children: "Close"
                            }, void 0, false, {
                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                lineNumber: 717,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f40$mui$2f$material$2f$Button$2f$Button$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                variant: "contained",
                                onClick: ()=>startCall(),
                                children: "Start New Call"
                            }, void 0, false, {
                                fileName: "[project]/src/app/call-simulator/page.tsx",
                                lineNumber: 718,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/src/app/call-simulator/page.tsx",
                        lineNumber: 716,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/app/call-simulator/page.tsx",
                lineNumber: 674,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/src/app/call-simulator/page.tsx",
        lineNumber: 355,
        columnNumber: 5
    }, this);
}
_s(CallSimulator, "JMv/2TeFi/3szYjUDaVuLa0U4fA=");
_c1 = CallSimulator;
var _c, _c1;
__turbopack_context__.k.register(_c, "TabPanel");
__turbopack_context__.k.register(_c1, "CallSimulator");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(module, globalThis.$RefreshHelpers$);
}
}}),
}]);

//# sourceMappingURL=src_3477ba5d._.js.map