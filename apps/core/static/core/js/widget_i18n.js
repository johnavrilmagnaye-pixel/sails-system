(function (global, $, moment) {
    'use strict';

    var _ = global.i18n.gettext;
    var localeKey = 'crm';
    var weekdays = [
        _('Sunday'), _('Monday'), _('Tuesday'), _('Wednesday'),
        _('Thursday'), _('Friday'), _('Saturday')
    ];
    var weekdaysShort = [
        _('Sun'), _('Mon'), _('Tue'), _('Wed'), _('Thu'), _('Fri'), _('Sat')
    ];
    var months = [
        _('January'), _('February'), _('March'), _('April'), _('May'), _('June'),
        _('July'), _('August'), _('September'), _('October'), _('November'), _('December')
    ];
    var monthsShort = [
        _('Jan'), _('Feb'), _('Mar'), _('Apr'), _('May'), _('Jun'),
        _('Jul'), _('Aug'), _('Sep'), _('Oct'), _('Nov'), _('Dec')
    ];

    global.CRMWidgetI18n = {
        localeKey: localeKey,
        datePickerLanguage: localeKey,
        select2Language: {
            errorLoading: function () { return _('The results could not be loaded.'); },
            inputTooLong: function () { return _('Please delete some characters.'); },
            inputTooShort: function () { return _('Please enter more characters.'); },
            loadingMore: function () { return _('Loading more results...'); },
            maximumSelected: function () { return _('You can only select a limited number of items.'); },
            noResults: function () { return _('No results found.'); },
            searching: function () { return _('Searching...'); }
        },
        dateRangeLocale: {
            format: 'DD.MM.YYYY',
            applyLabel: _('Apply'),
            cancelLabel: _('Cancel'),
            fromLabel: '',
            toLabel: '',
            customRangeLabel: _('Custom range'),
            daysOfWeek: weekdaysShort,
            monthNames: monthsShort,
            firstDay: 1
        }
    };

    if (moment && moment.defineLocale) {
        moment.defineLocale(localeKey, {
            months: months,
            monthsShort: monthsShort,
            weekdays: weekdays,
            weekdaysShort: weekdaysShort,
            weekdaysMin: weekdaysShort,
            longDateFormat: {
                LT: 'HH:mm',
                LTS: 'HH:mm:ss',
                L: 'DD.MM.YYYY',
                LL: 'D MMMM YYYY',
                LLL: 'D MMMM YYYY HH:mm',
                LLLL: 'dddd, D MMMM YYYY HH:mm'
            },
            week: {dow: 1, doy: 4}
        });
        moment.locale(localeKey);
    }

    if ($.fn.datetimepicker && $.fn.datetimepicker.dates) {
        $.fn.datetimepicker.dates[localeKey] = {
            days: weekdays,
            daysShort: weekdaysShort,
            daysMin: weekdaysShort,
            months: months,
            monthsShort: monthsShort,
            // Required by bootstrap-datetimepicker even when using a 24-hour format.
            meridiem: [],
            today: _('Today'),
            clear: _('Clear'),
            format: 'dd.mm.yyyy',
            weekStart: 1
        };
    }

    if ($.fullCalendar && $.fullCalendar.lang) {
        $.fullCalendar.lang(localeKey, {
            monthNames: months,
            monthNamesShort: monthsShort,
            dayNames: weekdays,
            dayNamesShort: weekdaysShort,
            buttonText: {
                today: _('Today'),
                month: _('Month'),
                week: _('Week'),
                day: _('Day'),
                list: _('List')
            },
            allDayText: _('All day'),
            noEventsMessage: _('No events to display')
        });
    }
}(window, window.jQuery, window.moment));
