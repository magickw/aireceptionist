'use client';

import { Box, Typography, Breadcrumbs, BreadcrumbItem, Button, useTheme, SxProps, Theme } from '@mui/material';
import { Home as HomeIcon, NavigateNext as NavigateNextIcon } from '@mui/icons-material';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  breadcrumbs?: Array<{ label: string; href?: string }>;
  action?: {
    label: string;
    onClick: () => void;
    icon?: React.ReactNode;
    variant?: 'contained' | 'outlined' | 'text';
  };
  sx?: SxProps<Theme>;
}

export function PageHeader({
  title,
  subtitle,
  breadcrumbs,
  action,
  sx,
}: PageHeaderProps) {
  const theme = useTheme();

  return (
    <Box sx={{ mb: { xs: 3, sm: 4 }, ...sx }}>
      {breadcrumbs && breadcrumbs.length > 0 && (
        <Breadcrumbs
          separator={<NavigateNextIcon fontSize="small" />}
          sx={{ mb: 2 }}
          aria-label="breadcrumb"
        >
          <BreadcrumbItem
            component="a"
            href="/"
            sx={{
              display: 'flex',
              alignItems: 'center',
              color: 'text.secondary',
              textDecoration: 'none',
              '&:hover': {
                color: 'primary.main',
              },
            }}
          >
            <HomeIcon sx={{ mr: 0.5, fontSize: 20 }} />
            Home
          </BreadcrumbItem>
          {breadcrumbs.map((crumb, index) => (
            <BreadcrumbItem
              key={index}
              component={crumb.href ? 'a' : 'span'}
              href={crumb.href}
              sx={{
                color: index === breadcrumbs.length - 1 ? 'text.primary' : 'text.secondary',
                textDecoration: 'none',
                fontWeight: index === breadcrumbs.length - 1 ? 600 : 400,
                '&:hover': crumb.href ? {
                  color: 'primary.main',
                } : {},
              }}
            >
              {crumb.label}
            </BreadcrumbItem>
          ))}
        </Breadcrumbs>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, flexDirection: { xs: 'column', sm: 'row' }, gap: 2 }}>
        <Box sx={{ flex: 1 }}>
          <Typography
            variant="h4"
            component="h1"
            sx={{
              fontWeight: 700,
              color: 'text.primary',
              mb: subtitle ? 1 : 0,
              fontSize: { xs: '1.75rem', sm: '2.125rem' },
            }}
          >
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="body1" color="text.secondary">
              {subtitle}
            </Typography>
          )}
        </Box>

        {action && (
          <Button
            variant={action.variant || 'contained'}
            onClick={action.onClick}
            startIcon={action.icon}
            sx={{ minWidth: 'auto', flexShrink: 0 }}
          >
            {action.label}
          </Button>
        )}
      </Box>
    </Box>
  );
}