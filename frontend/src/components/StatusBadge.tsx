import React from 'react';
import { Wind, HeartPulse, Bug, Activity } from 'lucide-react';

interface StatusBadgeProps {
  status: 'GREEN' | 'YELLOW' | 'RED';
  label: string;
  metric?: string;
  iconType?: 'apnea' | 'bradycardia' | 'sepsis' | 'ndi';
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  label,
  metric,
  iconType,
  size = 'md'
}) => {
  const getBadgeStyle = () => {
    switch (status) {
      case 'RED':
        return 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-800/60';
      case 'YELLOW':
        return 'bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border-amber-200 dark:border-amber-800/60';
      case 'GREEN':
      default:
        return 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/60';
    }
  };

  const getDotStyle = () => {
    switch (status) {
      case 'RED':
        return 'bg-rose-500';
      case 'YELLOW':
        return 'bg-amber-500';
      case 'GREEN':
      default:
        return 'bg-emerald-500';
    }
  };

  const renderIcon = () => {
    const iconClass = size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5';
    switch (iconType) {
      case 'apnea':
        return <Wind className={`${iconClass} opacity-80`} />;
      case 'bradycardia':
        return <HeartPulse className={`${iconClass} opacity-80`} />;
      case 'sepsis':
        return <Bug className={`${iconClass} opacity-80`} />;
      case 'ndi':
        return <Activity className={`${iconClass} opacity-80`} />;
      default:
        return null;
    }
  };

  return (
    <div
      className={`inline-flex items-center gap-1.5 rounded-md border font-medium transition ${getBadgeStyle()} ${
        size === 'sm'
          ? 'px-2 py-0.5 text-xs'
          : size === 'lg'
          ? 'px-3 py-1.5 text-sm'
          : 'px-2.5 py-1 text-xs'
      }`}
    >
      {renderIcon()}
      <span className={`w-1.5 h-1.5 rounded-full ${getDotStyle()}`} />
      <span>{label}</span>
      {metric && (
        <span className="font-mono text-[11px] opacity-75 font-normal ml-0.5">
          {metric}
        </span>
      )}
    </div>
  );
};
