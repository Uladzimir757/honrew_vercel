/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/templates/**/*.html',
    './app/static/js/**/*.js',
  ],
  theme: {
    extend: {},
  },
  // ИЗМЕНЕНИЕ: Добавляем плагин для красивого форматирования текста
  plugins: [
    require('@tailwindcss/typography'),
  ],
}