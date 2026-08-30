import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceArea,
  ReferenceLine,
  CartesianGrid
} from 'recharts';
import { WaveformPoint, ApneaEvent, BradycardiaSpell } from '../types';

interface WaveformChartProps {
  type: 'respiration' | 'heart_rate';
  data: WaveformPoint[];
  apneaEvents?: ApneaEvent[];
  bradycardiaSpells?: BradycardiaSpell[];
  title: string;
  subtitle?: string;
  unit: string;
  isDark?: boolean;
}

export const WaveformChart: React.FC<WaveformChartProps> = ({
  type,
  data,
  apneaEvents = [],
  bradycardiaSpells = [],
  title,
  subtitle,
  unit,
  isDark = false
}) => {
  const chartData = data.map((pt) => ({
    time: pt.time_sec,
    value: pt.value,
  }));

  const minTime = chartData.length > 0 ? chartData[0].time : 0;
  const maxTime = chartData.length > 0 ? chartData[chartData.length - 1].time : 180;

  // Theme-aware chart colors
  const strokeColor = type === 'respiration' 
    ? (isDark ? '#38bdf8' : '#0284c7') 
    : (isDark ? '#fb7185' : '#e11d48');

  const gridColor = isDark ? '#1e293b' : '#f1f5f9';
  const axisTextColor = isDark ? '#64748b' : '#94a3b8';
  const shadedOpacity = isDark ? 0.22 : 0.12;

  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm transition-colors duration-200">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 mb-2 border-b border-slate-100 dark:border-slate-800 gap-2">
        <div>
          <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${type === 'respiration' ? 'bg-sky-600 dark:bg-sky-400' : 'bg-rose-500 dark:bg-rose-400'}`} />
            {title}
          </h4>
          {subtitle && <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{subtitle}</p>}
        </div>

        <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
          {type === 'respiration' && (
            <span className="flex items-center gap-1.5 bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60">
              <span className="w-2.5 h-2.5 rounded-xs bg-amber-500/40 border border-amber-600 inline-block" />
              Apnea Pause Region
            </span>
          )}
          {type === 'heart_rate' && (
            <>
              <span className="flex items-center gap-1.5 text-rose-700 dark:text-rose-300 bg-rose-50 dark:bg-rose-950/40 px-2 py-0.5 rounded border border-rose-200 dark:border-rose-800/60">
                <span className="w-3 h-0.5 border-t-2 border-dashed border-rose-500 inline-block" />
                100 BPM Threshold
              </span>
              <span className="flex items-center gap-1.5 text-rose-700 dark:text-rose-300 bg-rose-50 dark:bg-rose-950/40 px-2 py-0.5 rounded border border-rose-200 dark:border-rose-800/60">
                <span className="w-2.5 h-2.5 rounded-xs bg-rose-500/30 border border-rose-600 inline-block" />
                Bradycardia Spell
              </span>
            </>
          )}
        </div>
      </div>

      <div className="h-64 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 15, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
            <XAxis
              dataKey="time"
              type="number"
              domain={[minTime, maxTime]}
              tickFormatter={(t) => `${t.toFixed(0)}s`}
              stroke={axisTextColor}
              fontSize={11}
              tickLine={false}
            />
            <YAxis
              stroke={axisTextColor}
              fontSize={11}
              domain={type === 'heart_rate' ? [50, 190] : ['auto', 'auto']}
              tickFormatter={(v) => `${v}${unit}`}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: isDark ? '#0f172a' : '#ffffff',
                borderColor: isDark ? '#334155' : '#e2e8f0',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                fontSize: '12px',
                color: isDark ? '#f8fafc' : '#0f172a'
              }}
              labelFormatter={(t) => `Time: ${Number(t).toFixed(1)}s`}
              formatter={(value: any) => [`${value} ${unit}`, title]}
            />

            {/* Shaded Apnea Event Zones */}
            {type === 'respiration' &&
              apneaEvents.map((evt) => (
                <ReferenceArea
                  key={evt.id}
                  x1={Math.max(minTime, evt.start_sec)}
                  x2={Math.min(maxTime, evt.end_sec)}
                  fill="#f59e0b"
                  fillOpacity={shadedOpacity}
                  stroke="#d97706"
                  strokeOpacity={0.6}
                  strokeDasharray="3 3"
                />
              ))}

            {/* Bradycardia 100 BPM Reference Line & Spell Zones */}
            {type === 'heart_rate' && (
              <>
                <ReferenceLine
                  y={100}
                  stroke="#f43f5e"
                  strokeDasharray="4 4"
                  strokeWidth={1.5}
                  label={{ value: '100 BPM Limit', fill: '#fb7185', fontSize: 10, position: 'insideTopRight' }}
                />
                {bradycardiaSpells.map((spell) => (
                  <ReferenceArea
                    key={spell.id}
                    x1={Math.max(minTime, spell.start_sec)}
                    x2={Math.min(maxTime, spell.end_sec)}
                    fill="#f43f5e"
                    fillOpacity={shadedOpacity}
                    stroke="#e11d48"
                    strokeOpacity={0.6}
                  />
                ))}
              </>
            )}

            <Line
              type="monotone"
              dataKey="value"
              stroke={strokeColor}
              strokeWidth={1.8}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
