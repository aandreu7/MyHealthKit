const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

config.resolver.alias = {
  '@': './',
  '@components': './components',
  '@assets': './assets',
  '@constants': './constants',
  '@hooks': './hooks',
};

module.exports = config;