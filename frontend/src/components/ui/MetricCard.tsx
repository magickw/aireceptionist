'use client';

import { Card, CardContent, Typography, Box, useTheme, alpha, SxProps, Theme } from '@mui/material';
import { TrendingUp, TrendingDown, TrendingFlat } from '@mui/icons-material';

interface MetricCardProps {
  title: string;
  value: string | number;
  trend?: {
    value: number;
    isPositive?: boolean;
    isNeutral?: boolean;
  };
  icon?: React.ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  loading?: boolean;
  sx?: SxProps<Theme>;
}

export function MetricCard({
  title,
  value,
  trend,
  icon,
  color = 'primary',
  loading = false,
  sx,
}: MetricCardProps) {
  const theme = useTheme();

  const getTrendIcon = () => {
    if (trend?.isNeutral) return <TrendingFlat fontSize="small" />;
    return trend?.isPositive ? <TrendingUp fontSize="small" /> : <TrendingDown fontSize="small" />;
  };

  const getTrendColor = () => {
    if (trend?.isNeutral) return 'text.secondary';
    return trend?.isPositive ? 'success.main' : 'error.main';
  };

  return (
    <Card
      sx={{
        height: '100%',
        transition: 'all 200ms cubic-bezier(0.4, 0, 0.2, 1)',
        position: 'relative',
        overflow: 'hidden',
        background: 'linear-gradient(145deg, #ffffff 0%, #f8fafc 100%)',
        ...sx,
      }}
    >
      {icon && (
        <Box
          sx={{
            position: 'absolute',
            top: -10,
            right: -10,
            opacity: 0.05,
            fontSize: 100,
            color: theme.palette[color].main,
            transform: 'rotate(-15deg)',
          }}
        >
          {icon}
        </Box>
      )}

      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Typography variant="overline" sx={{ fontWeight: 600, color: 'text.secondary', letterSpacing: '0.5px' }}>
            {title}
          </Typography>
          {icon && (
            <Box
              sx={{
                p: 1,
                borderRadius: 2,
                bgcolor: alpha(theme.palette[color].main, 0.1),
                color: theme.palette[color].main,
              }}
            >
              {icon}
            </Box>
          )}
        </Box>

        {loading ? (
          <Box>
            <Box sx={{ height: 40, width: '60%', bgcolor: 'grey.200', borderRadius: 1, mb: 1 }} />
            <Box sx={{ height: 16, width: '40%', bgcolor: 'grey.200', borderRadius: 1 }} />
          </Box>
        ) : (
          <>
            <Typography
              variant="h4"
              sx={{
                fontWeight: 700,
                color: 'text.primary',
                mb: 1,
                fontSize: { xs: '1.75rem', sm: '2rem' },
              }}
            >
              {value}
            </Typography>

            {trend && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                {getTrendIcon()}
                <Typography
                  variant="body2"
                  sx={{
                    color: getTrendColor(),
                    fontWeight: 600,
                  }}
                >
                  {trend.isPositive ? '+' : ''}{trend.value}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  from last period
                </Typography>
              </Box>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}