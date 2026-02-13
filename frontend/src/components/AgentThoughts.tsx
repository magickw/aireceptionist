import React, { useState, useEffect } from 'react';

interface Thought {
  step: string;
  message: string;
  timestamp: Date;
}

const AgentThoughts: React.FC<{ thoughts: Thought[] }> = ({ thoughts }) => {
  return (
    <div className="bg-slate-900 text-green-400 p-4 rounded-lg font-mono text-sm h-64 overflow-y-auto border border-slate-700 shadow-xl">
      <div className="mb-2 text-slate-500 uppercase tracking-widest text-xs font-bold">
        {">"} Nova Agent Reasoning Engine
      </div>
      {thoughts.map((thought, index) => (
        <div key={index} className="mb-2 animate-in fade-in slide-in-from-left-2">
          <span className="text-slate-500">[{thought.timestamp.toLocaleTimeString()}]</span>{' '}
          <span className="text-blue-400 font-bold">{thought.step.replace('_', ' ').toUpperCase()}</span>:{' '}
          {thought.message}
        </div>
      ))}
      {thoughts.length > 0 && (
        <div className="animate-pulse inline-block w-2 h-4 bg-green-500 ml-1" />
      )}
    </div>
  );
};

export default AgentThoughts;
