module.exports = {
  darkMode: 'class',
  content: [
    './sim/templates/**/*.html',
    './auths/templates/**/*.html',
    './cart/templates/**/*.html',
    './templates/**/*.html',
    './**/*.html',
    './**/*.js',
    './**/static/css/**/*.css'
  ],
  theme: {
    extend: {
      colors: {
        'food-orange': '#FF6B35',
        'food-green': '#4CAF50',
        'food-cream': '#FFF8E1',
        'food-dark': '#1A3C34',
        'food-gray': '#4A5568'
      }
    }
  },
  plugins: []
}