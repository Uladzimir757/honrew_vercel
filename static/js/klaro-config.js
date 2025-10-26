// /app/static/js/klaro-config.js

// Определяем текущий язык (мы передадим его из Flask)
// const currentLang = document.documentElement.lang || 'en'; // Заменится на Jinja в шаблоне

const klaroConfig = {
    // Версия вашей конфигурации. Полезна, если вы меняете настройки,
    // чтобы Klaro! снова показал баннер пользователям со старой версией согласия.
    version: 1,

    // Где хранить согласие: 'cookie' или 'localStorage'. localStorage предпочтительнее.
    storageMethod: 'localStorage',
    // Имя ключа в хранилище
    storageName: 'klaroConsent',

    // Если true, Klaro! будет ждать загрузки DOM перед инициализацией.
    // Рекомендуется оставить true.
    waitForDOM: true,

    // Если true, Klaro! не будет показывать баннер пользователям с включенным Do Not Track.
    // Выбор за вами, но учтите, что DNT не всегда отражает явное согласие по GDPR.
    respectDoNotTrack: false,

    // Если true, баннер не будет показан ботам поисковых систем.
    hideToggleAll: false, // Показывать кнопки "Принять все"/"Отклонить все"

    // Язык по умолчанию, если язык браузера или переданный язык не найден.
    default: true, // Помечаем 'en' как язык по умолчанию
    mustConsent: false, // Если true, пользователь *обязан* взаимодействовать с баннером

    // Определяем языки и переводы интерфейса Klaro!
    translations: {
        // Русский
        ru: {
            consentModal: {
                title: 'Информация о cookie',
                description: 'Этот сайт использует файлы cookie для улучшения вашего опыта. Пожалуйста, выберите, какие типы cookie вы разрешаете использовать.',
                privacyPolicy: 'Подробнее см. нашу <a href="/privacy?lang=ru" target="_blank">Политику конфиденциальности</a>.',
            },
            consentNotice: {
                description: 'Мы используем файлы cookie. Разрешите нам?',
                learnMore: 'Подробнее', // Текст кнопки "Подробнее" в маленьком баннере
            },
            acceptAll: 'Принять все',
            acceptSelected: 'Принять выбранные',
            decline: 'Отклонить',
            close: 'Закрыть',
            purposes: {
                // Названия категорий cookie
                necessary: 'Необходимые',
                analytics: 'Аналитика',
                marketing: 'Маркетинг',
                // Добавьте свои, если нужно
            },
            service: {
                disableAll: {
                    title: "Включить/выключить все",
                    description: "Используйте этот переключатель, чтобы включить или выключить все приложения.",
                },
                optOut: {
                    title: "(отключено)",
                    description: "Это приложение загружено по умолчанию (но вы можете его отключить)",
                },
                required: {
                    title: "(всегда обязательно)",
                    description: "Это приложение необходимо для правильной работы сайта и не может быть отключено.",
                },
                purposes: "Цели",
                purpose: "Цель",
            },
        },
        // Английский
        en: {
            consentModal: {
                title: 'Cookie Information',
                description: 'This website uses cookies to enhance your experience. Please choose which types of cookies you allow.',
                privacyPolicy: 'For more details, see our <a href="/privacy?lang=en" target="_blank">Privacy Policy</a>.',
            },
            consentNotice: {
                description: 'We use cookies. Can we enable them?',
                learnMore: 'Learn More',
            },
            acceptAll: 'Accept All',
            acceptSelected: 'Accept Selected',
            decline: 'Decline',
            close: 'Close',
            purposes: {
                necessary: 'Necessary',
                analytics: 'Analytics',
                marketing: 'Marketing',
            },
             service: {
                disableAll: {
                    title: "Enable/disable all apps",
                    description: "Use this switch to enable or disable all apps.",
                },
                optOut: {
                    title: "(opt-out)",
                    description: "This app is loaded by default (but you can opt out)",
                },
                required: {
                    title: "(always required)",
                    description: "This application is always required for the website to function properly and cannot be disabled.",
                },
                purposes: "Purposes",
                purpose: "Purpose",
            },
        },
        // Польский
        pl: {
            consentModal: {
                title: 'Informacje o plikach cookie',
                description: 'Ta strona używa plików cookie, aby poprawić Twoje wrażenia. Wybierz, które typy plików cookie chcesz zezwolić.',
                privacyPolicy: 'Więcej informacji znajdziesz w naszej <a href="/privacy?lang=pl" target="_blank">Polityce prywatności</a>.',
            },
            consentNotice: {
                description: 'Używamy plików cookie. Czy możemy je włączyć?',
                learnMore: 'Dowiedz się więcej',
            },
            acceptAll: 'Zaakceptuj wszystko',
            acceptSelected: 'Zaakceptuj wybrane',
            decline: 'Odrzuć',
            close: 'Zamknij',
            purposes: {
                necessary: 'Niezbędne',
                analytics: 'Analityka',
                marketing: 'Marketing',
            },
             service: {
                 disableAll: {
                    title: "Włącz/wyłącz wszystkie aplikacje",
                    description: "Użyj tego przełącznika, aby włączyć lub wyłączyć wszystkie aplikacje.",
                },
                optOut: {
                    title: "(rezygnacja)",
                    description: "Ta aplikacja jest domyślnie załadowana (ale możesz z niej zrezygnować)",
                },
                required: {
                    title: "(zawsze wymagane)",
                    description: "Ta aplikacja jest zawsze wymagana do prawidłowego funkcjonowania witryny i nie można jej wyłączyć.",
                },
                purposes: "Cele",
                purpose: "Cel",
            },
        },
    },

    // Описание сервисов (cookie), которые использует ваш сайт
    services: [
        // Пример 1: Строго необходимый cookie (например, сессионный)
        // Klaro! на самом деле не нужно управлять им, но можно описать для информации
        {
            name: 'session',
            default: true, // Включен по умолчанию
            required: true, // Нельзя отключить
            title: 'Сессионный Cookie', // Название для пользователя
            description: 'Используется для поддержания сессии пользователя (например, чтобы вы оставались залогинены).',
            translations: { // Переводы для этого сервиса
                ru: { title: 'Сессионный Cookie', description: 'Используется для поддержания сессии пользователя (например, чтобы вы оставались залогинены).' },
                en: { title: 'Session Cookie', description: 'Used to maintain user session (e.g., keeping you logged in).' },
                pl: { title: 'Plik cookie sesji', description: 'Używany do utrzymania sesji użytkownika (np. utrzymania zalogowania).' },
            },
            purposes: ['necessary'], // Категория
        },

        // Пример 2: Google Analytics (Аналитика)
        {
            name: 'googleAnalytics', // Уникальное имя сервиса
            default: false, // По умолчанию выключен (требует согласия)
            required: false, // Можно отключить
            title: 'Google Analytics',
            description: 'Собирает анонимную статистику посещений сайта для улучшения его работы.',
             translations: { // Переводы для этого сервиса
                ru: { title: 'Google Analytics', description: 'Собирает анонимную статистику посещений сайта для улучшения его работы.' },
                en: { title: 'Google Analytics', description: 'Collects anonymous website usage statistics to improve the site.' },
                pl: { title: 'Google Analytics', description: 'Zbiera anonimowe statystyki użytkowania witryny w celu jej ulepszenia.' },
            },
            cookies: [
                // Имена cookie, которые устанавливает этот сервис (можно найти в инструментах разработчика)
                [/^_ga(_.*)?/, "/"], // Регулярное выражение для _ga, _gid и т.д.
            ],
            purposes: ['analytics'], // Категория
            // onAccept: () => { // Код, который выполнится при согласии (если нужно)
            //     console.log("Analytics accepted");
            // },
            // onDecline: () => { // Код при отказе (если нужно)
            //     console.log("Analytics declined");
            // },
        },

        // Добавьте сюда другие сервисы, которые вы используете
        // (например, Facebook Pixel, другие счетчики, рекламные cookie)
        // {
        //     name: 'facebookPixel',
        //     default: false,
        //     required: false,
        //     title: 'Facebook Pixel',
        //     description: 'Используется для отслеживания эффективности рекламы в Facebook.',
        //     cookies: [/^_fbp/, /^_fbc/],
        //     purposes: ['marketing'],
        // },
    ],
};

// Экспортируем конфигурацию (если вы подключаете ее как модуль, иначе просто используйте klaroConfig)
// В данном случае мы будем вставлять этот файл напрямую, так что экспорт не нужен.
// export default klaroConfig; // Закомментировано