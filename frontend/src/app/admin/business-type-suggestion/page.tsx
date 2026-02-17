"use client";

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Sparkles, Lightbulb, AlertCircle } from 'lucide-react';

interface BusinessTypeSuggestion {
  business_type: string;
  confidence: number;
  name: string;
  icon: string;
}

export default function BusinessTypeSuggestionPage() {
  const [description, setDescription] = useState('');
  const [suggestions, setSuggestions] = useState<BusinessTypeSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSuggest = async () => {
    if (!description.trim()) {
      setError('Please enter a business description');
      return;
    }

    try {
      setLoading(true);
      setError('');
      
      const response = await fetch('/api/v1/admin/templates/suggest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description, top_n: 5 }),
      });

      if (response.ok) {
        const data = await response.json();
        setSuggestions(data);
      } else {
        setError('Failed to get suggestions');
      }
    } catch (error) {
      setError('An error occurred while fetching suggestions');
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-500';
    if (confidence >= 0.5) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.5) return 'Medium';
    return 'Low';
  };

  return (
    <div className="container mx-auto py-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Sparkles className="h-8 w-8" />
          Business Type Suggestion
        </h1>
        <p className="text-muted-foreground mt-2">
          Use AI to suggest the most appropriate business type based on your description
        </p>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Describe Your Business</CardTitle>
          <CardDescription>
            Enter a detailed description of your business to get AI-powered type suggestions
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="description">Business Description</Label>
            <Textarea
              id="description"
              placeholder="e.g., A restaurant serving Italian cuisine with pasta, pizza, and wine. We offer dine-in, takeout, and delivery services..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="min-h-[150px]"
            />
          </div>
          
          {error && (
            <div className="flex items-center gap-2 text-destructive bg-destructive/10 p-3 rounded-lg">
              <AlertCircle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          )}
          
          <Button 
            onClick={handleSuggest} 
            disabled={loading}
            className="w-full"
          >
            {loading ? (
              <>
                <Sparkles className="h-4 w-4 mr-2 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Lightbulb className="h-4 w-4 mr-2" />
                Get Suggestions
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {suggestions.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold">Suggested Business Types</h2>
          {suggestions.map((suggestion, index) => (
            <Card 
              key={suggestion.business_type}
              className={index === 0 ? 'border-primary border-2' : ''}
            >
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-primary/10 rounded-lg">
                      <span className="text-3xl">{suggestion.icon}</span>
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-xl font-semibold">{suggestion.name}</h3>
                        {index === 0 && (
                          <Badge className="bg-primary">
                            Best Match
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        Business Type: <code>{suggestion.business_type}</code>
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-muted-foreground mb-1">Confidence</div>
                    <div className="flex items-center gap-2">
                      <Badge className={`${getConfidenceColor(suggestion.confidence)} text-white`}>
                        {getConfidenceLabel(suggestion.confidence)}
                      </Badge>
                      <span className="text-2xl font-bold">
                        {Math.round(suggestion.confidence * 100)}%
                      </span>
                    </div>
                  </div>
                </div>
                
                {/* Confidence bar */}
                <div className="mt-4">
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${getConfidenceColor(suggestion.confidence)} transition-all duration-500`}
                      style={{ width: `${suggestion.confidence * 100}%` }}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          
          {suggestions.length > 0 && suggestions[0].confidence < 0.5 && (
            <Card className="border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20">
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-yellow-800 dark:text-yellow-200">
                      Low Confidence Results
                    </h4>
                    <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                      The AI couldn't confidently determine your business type. This might be because:
                    </p>
                    <ul className="text-sm text-yellow-700 dark:text-yellow-300 mt-2 list-disc list-inside space-y-1">
                      <li>Your description is too vague or brief</li>
                      <li>Your business type might not be in our system yet</li>
                      <li>You may be describing a unique business model</li>
                    </ul>
                    <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-2">
                      Consider providing more details about your services, products, and business operations.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {description && !loading && suggestions.length === 0 && (
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground">
            <Lightbulb className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>
              Enter a business description above and click "Get Suggestions" to see AI-powered recommendations.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}