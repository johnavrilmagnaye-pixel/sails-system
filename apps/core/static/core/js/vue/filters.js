Vue.filter('datetime', function (value) {
    if (!value) return '';
    return i18n.formatDate(new moment(value).toDate(), {
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit'
    });
});


Vue.filter('date', function (value) {
    if (!value) return '';
    return i18n.formatDate(new moment(value).toDate(), {
        year: 'numeric', month: '2-digit', day: '2-digit'
    });
});


Vue.filter('time', function (value) {
    if (!value) return '';
    return i18n.formatDate(new moment(value, 'HH:mm').toDate(), {
        hour: '2-digit', minute: '2-digit'
    });
});


Vue.filter('linebreaks', function (value) {
    return value.replace(/(?:\r\n|\r|\n)/g, '<br>');
});


Vue.filter('money', function (value) {
    if (value === null || value === undefined) {
        return '';
    } else if (value === 0) {
        return 0;
    }

    return i18n.formatNumber(value);
});


Vue.filter('pluralize', Utils.pluralize);


Vue.filter('urlize', function (value) {
    value = value.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');

    return urlize(value, {django_compatible: false});
});
