'use client';

import { Box, Skeleton, Card, CardContent, Typography } from '@mui/material';

interface LoadingSkeletonProps {
  variant?: 'text' | 'rectangular' | 'circular' | 'card' | 'list';
  count?: number;
  height?: number | string;
  width?: number | string;
}

export function LoadingSkeleton({
  variant = 'text',
  count = 1,
  height,
  width,
}: LoadingSkeletonProps) {
  if (variant === 'card') {
    return (
      <Card sx={{ height: '100%' }}>
        <CardContent>
          <Skeleton variant="rectangular" width="100%" height={200} sx={{ mb: 2 }} />
          <Skeleton variant="text" width="60%" height={32} sx={{ mb: 1 }} />
          <Skeleton variant="text" width="90%" />
          <Skeleton variant="text" width="80%" />
        </CardContent>
      </Card>
    );
  }

  if (variant === 'list') {
    return (
      <Box>
        {Array.from({ length: count }).map((_, index) => (
          <Box key={index} sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Skeleton variant="circular" width={40} height={40} sx={{ mr: 2 }} />
            <Box sx={{ flex: 1 }}>
              <Skeleton variant="text" width="40%" height={24} sx={{ mb: 0.5 }} />
              <Skeleton variant="text" width="60%" height={18} />
            </Box>
          </Box>
        ))}
      </Box>
    );
  }

  return (
    <Box>
      {Array.from({ length: count }).map((_, index) => (
        <Skeleton
          key={index}
          variant={variant}
          height={height}
          width={width}
          sx={{ mb: index < count - 1 ? 1 : 0 }}
        />
      ))}
    </Box>
  );
}

export function MetricCardSkeleton() {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Skeleton variant="text" width="40%" height={20} sx={{ mb: 2 }} />
        <Skeleton variant="text" width="50%" height={40} sx={{ mb: 1 }} />
        <Skeleton variant="text" width="70%" height={18} />
      </CardContent>
    </Card>
  );
}

export function TableSkeleton({ rows = 5, columns = 4 }: { rows?: number; columns?: number }) {
  return (
    <Box>
      <Box sx={{ display: 'flex', mb: 2, px: 2 }}>
        {Array.from({ length: columns }).map((_, index) => (
          <Skeleton key={index} variant="text" width={`${100 / columns}%`} sx={{ mr: 2 }} />
        ))}
      </Box>
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <Box key={rowIndex} sx={{ display: 'flex', mb: 1.5, px: 2 }}>
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton key={colIndex} variant="rectangular" width={`${100 / columns}%`} height={40} sx={{ mr: 2 }} />
          ))}
        </Box>
      ))}
    </Box>
  );
}