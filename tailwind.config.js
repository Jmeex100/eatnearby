module.exports = {
  darkMode: 'class',
  content: [
    './sim/templates/**/*.html',
    './auths/templates/**/*.html',
    './cart/templates/**/*.html',
    './templates/**/*.html',
    './sim/static/js/**/*.js',
    './auths/static/js/**/*.js',
    './cart/static/js/**/*.js',
    './**/static/css/**/*.css',
    './payments/templates/**/*.html',
    './payments/static/js/**/*.js',
    './staffs/templates/**/*.html',
    './staffs/static/js/**/*.js',
    './superadmin/templates/**/*.html',
    './superadmin/static/js/**/*.js',
      './Community/templates/**/*.html',
    './Community/static/js/**/*.js',
      './Community/templates/question/**/*.html',
        './Community/templates/answer/**/*.html',
      './Community/templates/posts/**/*.html',
    './Community/static/js/**/*.js',
    
  ],
  theme: {
    extend: {
      colors: {
        'food-orange': '#FF6B35',
        'food-green': '#4CAF50',
        'food-cream': '#FFF8E1',
        'food-dark': '#1A3C34',
        'food-gray': '#4A5568',
        // Dark mode specific colors
        'dark-background': '#111827',
        'dark-text': '#F3F4F6',
        'dark-card': '#1F2937',
        'dark-border': '#374151',
      }
    }
  },
  variants: {
    extend: {
      backgroundColor: ['dark'],
      textColor: ['dark'],
      borderColor: ['dark'],
      boxShadow: ['dark'],
      opacity: ['dark'],
      gradientColorStops: ['dark'],
    },
  },
  plugins: [],
}