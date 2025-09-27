import { theme } from 'antd';

// Light theme configuration
export const lightTheme = {
  algorithm: theme.defaultAlgorithm,
  token: {
    colorPrimary: '#1890ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    colorInfo: '#1890ff',
    borderRadius: 6,
    wireframe: false,
  },
  components: {
    Layout: {
      bodyBg: '#ffffff',
      siderBg: '#ffffff',
      headerBg: '#ffffff',
    },
    Menu: {
      itemBg: 'transparent',
      itemSelectedBg: '#e6f7ff',
      itemHoverBg: '#f5f5f5',
    },
    Button: {
      borderRadius: 6,
    },
    Input: {
      borderRadius: 6,
    },
    Card: {
      borderRadius: 8,
    },
  },
};

// Dark theme configuration
export const darkTheme = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: '#1890ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    colorInfo: '#1890ff',
    borderRadius: 6,
    wireframe: false,
  },
  components: {
    Layout: {
      bodyBg: '#141414',
      siderBg: '#1f1f1f',
      headerBg: '#1f1f1f',
    },
    Menu: {
      itemBg: 'transparent',
      itemSelectedBg: '#111b26',
      itemHoverBg: '#262626',
    },
    Button: {
      borderRadius: 6,
    },
    Input: {
      borderRadius: 6,
    },
    Card: {
      borderRadius: 8,
    },
  },
};

export type ThemeMode = 'light' | 'dark';

export const getThemeConfig = (mode: ThemeMode) => {
  return mode === 'dark' ? darkTheme : lightTheme;
};