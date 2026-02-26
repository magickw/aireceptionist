'use client';

import { Box, Typography, Button, Card, CardContent, useTheme, alpha, SxProps, Theme } from '@mui/material';
import {
  Inbox as InboxIcon,
  SearchOff as SearchOffIcon,
  ErrorOutline as ErrorOutlineIcon,
  CheckCircle as CheckCircleIcon,
  SentimentDissatisfied as SentimentDissatisfiedIcon,
} from '@mui/icons-material';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
    variant?: 'contained' | 'outlined' | 'text';
  };
  variant?: 'default' | 'search' | 'error' | 'success' | 'no-data';
  sx?: SxProps<Theme>;
}

const defaultIcons = {
  default: <InboxIcon />,
  search: <SearchOffIcon />,
  error: <ErrorOutlineIcon />,
  success: <CheckCircleIcon />,
  'no-data': <SentimentDissatisfiedIcon />,
};

const variantColors = {
  default: 'primary',
  search: 'info',
  error: 'error',
  success: 'success',
  'no-data': 'secondary',
} as const;

export function EmptyState({
  icon,
  title,
  description,
  action,
  variant = 'default',
  sx,
}: EmptyStateProps) {
  const theme = useTheme();
  const displayIcon = icon || defaultIcons[variant];
  const color = variantColors[variant];

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        py: 8,
        px: 3,
        ...sx,
      }}
    >
      <Box
        sx={{
          display: 'inline-flex',
          p: 3,
          borderRadius: '50%',
          bgcolor: alpha(theme.palette[color].main, 0.1),
          color: theme.palette[color].main,
          mb: 3,
          animation: 'fadeInUp 0.3s ease-out',
          '@keyframes fadeInUp': {
            from: {
              opacity: 0,
              transform: 'translateY(10px)',
            },
            to: {
              opacity: 1,
              transform: 'translateY(0)',
            },
          },
        }}
      >
        {displayIcon}
      </Box>

      <Typography
        variant="h6"
        gutterBottom
        sx={{
          fontWeight: 600,
          color: 'text.primary',
          animation: 'fadeInUp 0.3s ease-out 0.1s both',
        }}
      >
        {title}
      </Typography>

      {description && (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            maxWidth: 400,
            mb: 3,
            animation: 'fadeInUp 0.3s ease-out 0.2s both',
          }}
        >
          {description}
        </Typography>
      )}

      {action && (
        <Button
          variant={action.variant || 'contained'}
          onClick={action.onClick}
          sx={{
            animation: 'fadeInUp 0.3s ease-out 0.3s both',
          }}
        >
          {action.label}
        </Button>
      )}
    </Box>
  );
}

export function EmptyCardState({ title, description, action }: Omit<EmptyStateProps, 'variant'>) {
  return (
    <Card sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <CardContent>
        <EmptyState title={title} description={description} action={action} />
      </CardContent>
    </Card>
  );
}