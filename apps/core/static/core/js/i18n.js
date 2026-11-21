(function (global) {
    'use strict';

    function fallbackGettext(message) {
        return message;
    }

    function fallbackNgettext(singular, plural, count) {
        return count === 1 ? singular : plural;
    }

    function interpolate(message, values) {
        return message.replace(/%\(([^)]+)\)s/g, function (match, key) {
            return Object.prototype.hasOwnProperty.call(values, key) ? values[key] : match;
        });
    }

    function getDocumentLocale() {
        var locale = document.documentElement.getAttribute('lang');
        return locale || 'en';
    }

    var adapter = {
        gettext: function (message) {
            return (global.gettext || fallbackGettext)(message);
        },

        pgettext: function (context, message) {
            if (global.pgettext) {
                return global.pgettext(context, message);
            }
            return adapter.gettext(message);
        },

        ngettext: function (singular, plural, count) {
            return (global.ngettext || fallbackNgettext)(singular, plural, count);
        },

        interpolate: interpolate,

        plural: function (count, singular, plural) {
            return adapter.ngettext(singular, plural, count);
        },

        formatNumber: function (value, options) {
            if (global.Intl && global.Intl.NumberFormat) {
                return new global.Intl.NumberFormat(adapter.locale, options).format(value);
            }
            return String(value);
        },

        formatCurrency: function (value, currency) {
            return adapter.formatNumber(value, {style: 'currency', currency: currency});
        },

        formatDate: function (value, options) {
            if (global.Intl && global.Intl.DateTimeFormat) {
                return new global.Intl.DateTimeFormat(adapter.locale, options).format(value);
            }
            return String(value);
        },

        locale: getDocumentLocale()
    };

    global.i18n = adapter;
}(window));
