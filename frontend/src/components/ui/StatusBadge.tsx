'use client';

import { Chip, ChipProps, SxProps, Theme } from '@mui/material';
import { Circle as CircleIcon } from '@mui/icons-material';

export type StatusType = 'success' | 'warning' | 'error' | 'info' | 'default' | 'active' | 'inactive' | 'pending' | 'processing';

interface StatusBadgeProps extends Omit<ChipProps, 'color'> {
  status: StatusType;
  label?: string;
  showDot?: boolean;
  variant?: 'filled' | 'outlined';
  size?: 'small' | 'medium';
  sx?: SxProps<Theme>;
}

const statusConfig: Record<
  StatusType,
  { color: ChipProps['color']; label?: string; customColor?: string }
> = {
  success: { color: 'success' as const, label: 'Completed' },
  warning: { color: 'warning' as const, label: 'Warning' },
  error: { color: 'error' as const, label: 'Error' },
  info: { color: 'info' as const, label: 'Info' },
  default: { color: 'default' as const, label: 'Unknown' },
  active: { color: 'success' as const, label: 'Active', customColor: '#10b981' },
  inactive: { color: 'default' as const, label: 'Inactive' },
  pending: { color: 'warning' as const, label: 'Pending' },
  processing: { color: 'info' as const, label: 'Processing' },
};

export function StatusBadge({
  status,
  label,
  showDot = true,
  variant = 'filled',
  size = 'small',
  sx,
  ...props
}: StatusBadgeProps) {
  const config = statusConfig[status] || statusConfig.default;
  const displayLabel = label || config.label || status;

  return (
    <Chip
      label={displayLabel}
      color={config.color}
      variant={variant}
      size={size}
      icon={
        showDot ? (
          <CircleIcon
            sx={{
              fontSize: size === 'small' ? 8 : 10,
              color: config.customColor || 'currentColor',
            }}
          />
        ) : undefined
      }
      sx={{
        fontWeight: 500,
        textTransform: 'capitalize',
        ...(config.customColor && {
          backgroundColor: variant === 'filled' ? `${config.customColor}15` : 'transparent',
          color: config.customColor,
          borderColor: config.customColor,
          '& .MuiChip-icon': {
            color: config.customColor,
          },
        }),
        ...sx,
      }}
      {...props}
    />
  );
}

// Pre-configured status badges for common use cases
export function ActiveBadge(props: Partial<StatusBadgeProps>) {
  return <StatusBadge status="active" {...props} />;
}

export function InactiveBadge(props: Partial<StatusBadgeProps>) {
  return <StatusBadge status="inactive" {...props} />;
}

export function PendingBadge(props: Partial<StatusBadgeProps>) {
  return <StatusBadge status="pending" {...props} />;
}

export function SuccessBadge(props: Partial<StatusBadgeProps>) {
  return <StatusBadge status="success" {...props} />;
}

export function ErrorBadge(props: Partial<StatusBadgeProps>) {
  return <StatusBadge status="error" {...props} />;
}

export function ProcessingBadge(props: Partial<StatusBadgeProps>) {
  return <StatusBadge status="processing" {...props} />;
}