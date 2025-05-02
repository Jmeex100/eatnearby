module.exports = {
  darkMode: 'class', // or 'media' for system preference
  content: [
    './sim/templates/**/*.html',
    './sim/static/js/**/*.js',
    './auths/templates/**/*.html',
    './auths/static/js/**/*.js',
    './cart/templates/**/*.html', // Added cart templates
    './cart/static/js/**/*.js',
    './templates/**/*.html', // Include the base templates directory
    './templates/js/**/*.js',
    './**/templates/**/*.html', // Catch all templates in subdirectories
    './**/static/js/**/*.js', // Catch all js in subdirectories
    './**/static/css/**/*.css', // In case you have tailwind classes in css files
    './*.html', // if you have html files in root
    './*.js', // if you have js files in root
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}