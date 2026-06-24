import React from 'react';
import { Globe, Database, MessageSquare } from 'lucide-react';

export const HowItWorks: React.FC = () => {
  const steps = [
    {
      icon: <Globe className="w-6 h-6 text-indigo-400" />,
      title: "1. Add URL",
      description: "Paste a link to any documentation, blog, or website you want to chat with.",
      color: "bg-indigo-500/10 border-indigo-500/20"
    },
    {
      icon: <Database className="w-6 h-6 text-violet-400" />,
      title: "2. Crawl and index",
      description: "WebMind securely crawls the pages, extracts content, and builds a vector index.",
      color: "bg-violet-500/10 border-violet-500/20"
    },
    {
      icon: <MessageSquare className="w-6 h-6 text-purple-400" />,
      title: "3. Ask questions",
      description: "Chat with the website. Get instant answers backed by citations and sources.",
      color: "bg-purple-500/10 border-purple-500/20"
    }
  ];

  return (
    <div id="how-it-works" className="py-24 relative z-10 border-t border-white/5 bg-slate-900/50">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold mb-4">How WebMind Works</h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            From raw HTML to intelligent conversation in seconds.
          </p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8">
          {steps.map((step, index) => (
            <div 
              key={index} 
              className="p-8 rounded-3xl bg-slate-800/50 border border-white/5 flex flex-col items-center text-center hover:bg-slate-800/80 transition-colors"
            >
              <div className={`p-4 rounded-2xl mb-6 border ${step.color}`}>
                {step.icon}
              </div>
              <h3 className="text-xl font-bold mb-3">{step.title}</h3>
              <p className="text-slate-400 leading-relaxed">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
