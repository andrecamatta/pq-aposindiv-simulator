import React from 'react';
import { StatusBadge } from './Badge';
import { Tooltip } from './Tooltip';

export type ConnectionState = 'connected' | 'disconnected' | 'connecting';

interface ConnectionStatusProps {
  status: ConnectionState;
  lastPing?: Date;
  responseTime?: number;
  onReconnect?: () => void;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  status,
  lastPing,
  responseTime,
  onReconnect
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          variant: 'success' as const,
          icon: '🟢',
          label: 'Conectado',
          className: 'text-green-700 bg-green-50 border-green-200'
        };
      case 'connecting':
        return {
          variant: 'warning' as const,
          icon: '🟡',
          label: 'Conectando...',
          className: 'text-yellow-700 bg-yellow-50 border-yellow-200'
        };
      case 'disconnected':
        return {
          variant: 'destructive' as const,
          icon: '🔴',
          label: 'Desconectado',
          className: 'text-red-700 bg-red-50 border-red-200'
        };
    }
  };

  const config = getStatusConfig();

  const getTooltipContent = () => {
    const lines = [`Status: ${config.label}`];

    if (lastPing) {
      lines.push(`Último ping: ${lastPing.toLocaleTimeString()}`);
    }

    if (responseTime !== undefined) {
      lines.push(`Tempo de resposta: ${responseTime}ms`);
    }

    if (status === 'disconnected') {
      lines.push('', 'Clique para tentar reconectar');
    }

    return lines.join('\n');
  };

  return (
    <Tooltip content={getTooltipContent()}>
      <div
        className={`
          inline-flex items-center gap-2 px-3 py-1.5 rounded-full border cursor-pointer
          transition-all duration-200 hover:shadow-sm
          ${config.className}
          ${status === 'disconnected' ? 'hover:bg-red-100' : ''}
        `}
        onClick={status === 'disconnected' ? onReconnect : undefined}
        role={status === 'disconnected' ? 'button' : undefined}
        tabIndex={status === 'disconnected' ? 0 : undefined}
      >
        <span className="text-sm select-none" aria-hidden="true">
          {config.icon}
        </span>
        <span className="text-sm font-medium select-none">
          {config.label}
        </span>
        {status === 'connecting' && (
          <div className="w-3 h-3 rounded-full border-2 border-current border-t-transparent animate-spin" />
        )}
      </div>
    </Tooltip>
  );
};

export default ConnectionStatus;