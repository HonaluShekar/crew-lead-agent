import { Inbox } from 'lucide-react';

export function EmptyState({ title, message, icon: Icon = Inbox }: { title: string; message?: string; icon?: React.ElementType }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="h-12 w-12 rounded-full bg-console-800 border border-console-700 flex items-center justify-center mb-3">
        <Icon size={20} className="text-slate-500" />
      </div>
      <p className="text-sm font-medium text-slate-300">{title}</p>
      {message && <p className="text-xs text-slate-500 mt-1 max-w-sm">{message}</p>}
    </div>
  );
}

export function LoadingState({ message = 'Loading…' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="h-8 w-8 rounded-full border-2 border-console-700 border-t-accent animate-spin mb-3" />
      <p className="text-sm text-slate-400">{message}</p>
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="h-12 w-12 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center mb-3">
        <span className="text-red-400 text-xl">!</span>
      </div>
      <p className="text-sm font-medium text-slate-300">Something went wrong</p>
      <p className="text-xs text-slate-500 mt-1">{message}</p>
    </div>
  );
}
