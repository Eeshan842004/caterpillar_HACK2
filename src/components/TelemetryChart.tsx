'use client';

import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
} from 'recharts';
import { TelemetryPoint } from '@/domain/types';
import { OPERATIONAL_THRESHOLDS } from '@/domain/constants';

interface TelemetryChartProps {
  telemetryPoints: TelemetryPoint[];
  parameterName: string;
}

export const TelemetryChart: React.FC<TelemetryChartProps> = ({
  telemetryPoints,
  parameterName,
}) => {
  const threshold = OPERATIONAL_THRESHOLDS[parameterName];
  const chartData = telemetryPoints
    .filter((p) => p.parameter === parameterName)
    .sort((a, b) => new Date(a.observed_at).getTime() - new Date(b.observed_at).getTime())
    .map((p) => {
      const timeStr = new Date(p.observed_at).toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Asia/Calcutta',
      });
      return {
        time: timeStr,
        value: p.value,
        quality: p.quality,
      };
    });

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '8px',
        padding: '1.25rem',
        marginBottom: '1.5rem',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            Engine Coolant Temperature Trajectory
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Warning Threshold: {threshold?.warning_max}°C | Critical: {threshold?.critical_max}°C
          </p>
        </div>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          ISO 15143-3 Stream (5-min intervals)
        </span>
      </div>

      <div style={{ width: '100%', height: 260 }}>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" opacity={0.5} />
              <XAxis dataKey="time" stroke="var(--text-muted)" fontSize={12} />
              <YAxis
                domain={[70, 120]}
                stroke="var(--text-muted)"
                fontSize={12}
                unit="°C"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--bg-primary)',
                  borderColor: 'var(--border-subtle)',
                  borderRadius: '6px',
                  color: 'var(--text-primary)',
                }}
              />
              {threshold && (
                <ReferenceLine
                  y={threshold.warning_max}
                  label={{ value: `Warning (${threshold.warning_max}°C)`, fill: 'var(--color-warning)', fontSize: 11 }}
                  stroke="var(--color-warning)"
                  strokeDasharray="4 4"
                />
              )}
              {threshold && (
                <ReferenceLine
                  y={threshold.critical_max}
                  label={{ value: `Critical (${threshold.critical_max}°C)`, fill: 'var(--color-danger)', fontSize: 11 }}
                  stroke="var(--color-danger)"
                  strokeDasharray="4 4"
                />
              )}
              <Line
                type="monotone"
                dataKey="value"
                name="Coolant Temp"
                stroke="var(--color-brand)"
                strokeWidth={2.5}
                dot={{ r: 4, fill: 'var(--color-brand)' }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div
            style={{
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-muted)',
              fontSize: '0.9rem',
            }}
          >
            No telemetry series recorded for this parameter
          </div>
        )}
      </div>
    </div>
  );
};
