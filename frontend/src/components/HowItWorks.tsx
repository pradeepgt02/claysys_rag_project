import React from 'react';
import { Globe, Database, MessageSquare } from 'lucide-react';

export const HowItWorks: React.FC = () => {
  const steps = [
    {
      icon: <Globe className="w-6 h-6 text-sky-400" />,
      title: "1. Add URL",
      description: "Paste a link to any documentation, blog, or website you want to chat with.",
      color: "bg-sky-500/10 border-sky-500/20"
    },
    {
      icon: <Database className="w-6 h-6 text-blue-400" />,
      title: "2. Crawl and index",
      description: "WebMind securely crawls the pages, extracts content, and builds a vector index.",
      color: "bg-blue-500/10 border-blue-500/20"
    },
    {
      icon: <MessageSquare className="w-6 h-6 text-blue-400" />,
      title: "3. Ask questions",
      description: "Chat with the website. Get instant answers backed by citations and sources.",
      color: "bg-blue-500/10 border-blue-500/20"
    }
  ];

  return (
    <div id="how-it-works" className="py-24 relative z-10 border-t border-slate-200 dark:border-white/5 bg-slate-50/50 dark:bg-slate-900/50">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold mb-4 text-slate-900 dark:text-white">How WebMind Works</h2>
          <p className="text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
            From raw HTML to intelligent conversation in seconds.
          </p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8">
          {steps.map((step, index) => (
            <div 
              key={index} 
              className="p-8 rounded-3xl bg-white dark:bg-slate-800/50 border border-slate-200 dark:border-white/5 flex flex-col items-center text-center hover:bg-slate-50 dark:hover:bg-slate-800/80 transition-colors shadow-sm dark:shadow-none"
            >
              <div className={`p-4 rounded-2xl mb-6 border ${step.color}`}>
                {step.icon}
              </div>
              <h3 className="text-xl font-bold mb-3 text-slate-900 dark:text-white">{step.title}</h3>
              <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
