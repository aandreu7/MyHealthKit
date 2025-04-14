const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

config.resolver.alias = {
  '@': './',
  '@components': './components',
  '@assets': './assets',
  '@services': './services',
  '@constants': './constants',
  '@hooks': './hooks',
};

module.exports = config;