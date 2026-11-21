Vue.directive('tags', {
    params: ['initialValue'],

    bind: function () {
        var self = this,
            view = this.vm,
            initialValue = this.params.initialValue;

        $.ajax({
            type: 'GET',
            url: API.tags,
            contentType: 'application/json',
            dataType: 'json'
        }).done(function(res) {
            $(self.el).editable({
                type: 'select2',
                pk: 1,
                name: 'tags',
                url: view.itemsApiUrl + view.itemId + '/edit_tags/',
                highlight: false,
                placement: 'top',
                display: false,
                success: function (data) {
                    if (data['success']) {
                        view.item.tags = data['tags'];
                    } else {
                        return data['message'];
                    }
                },
                select2: {
                    theme: 'bootstrap',
                    language: CRMWidgetI18n.select2Language,
                    width: '250px',
                    tags: true,
                    data: res
                },
                value: _.pluck(initialValue, 'name')
            });
        });


    },
    unbind: function () {
        $(this.el).editable('destroy');
    }
});


Vue.directive('responsibles', {
    params: ['initialValue'],
    bind: function () {
        var self = this,
            view = this.vm,
            initialValue = this.params.initialValue;

        $.ajax({
            type: 'GET',
            url: API.options.user,
            dataType: 'json'
        }).done(function(res) {
            $(self.el).editable({
                type: 'select2',
                pk: 1,
                name: 'responsibles',
                url: view.itemsApiUrl + view.itemId + '/edit_responsibles/',
                highlight: false,
                placement: 'top',
                display: false,
                success: function (data) {
                    if (data['success']) {
                        view.item.responsibles = data['responsibles'];
                    } else {
                        return data['message'];
                    }
                },
                select2: {
                    theme: 'bootstrap',
                    language: CRMWidgetI18n.select2Language,
                    width: '250px',
                    data: res
                },
                value: _.pluck(initialValue, 'id')
            });
        });


    },
    unbind: function () {
        $(this.el).editable('destroy');
    }
});


Vue.directive('editable', {
    params: ['pk', 'value', 'url'],

    bind: function () {
        var params = this.params;

        $(this.el).editable({
            validate: function(value) {
                if (!value) {
                    return i18n.gettext('Required field');
                }
            },
            url: params.url,
            pk: params.pk,
            value: params.value,
            type: 'text',
            tpl: '<input type="text" maxlength="200">',
            inputclass: '',
            highlight: false,
            success: function () {
                $(this).hide().fadeIn("slow");
            },
            error: function (response) {
                return response.responseJSON.error;
            }
        });
    },

    unbind: function () {
        $(this.el).editable('destroy');
    }
});


Vue.directive('sortable', {
    bind: function () {
        var tbody = this.el.querySelector('tbody');

        this.sortable = new Sortable(tbody, {
            draggable: 'tr',
            handle: '.drag',
            ghostClass: 'sortable-ghost',
            onEnd: function () {
                var ids = Array.prototype.map.call(
                    tbody.querySelectorAll('tr[data-id]'),
                    function (row) {
                        return row.getAttribute('data-id');
                    }
                );

                $.post('/update_deal_stages_positions/', {'data[]': ids});
            }
        });
    },
    unbind: function () {
        this.sortable.destroy();
        this.sortable = null;
    }
});


Vue.directive('popover', {
    params: ['title', 'content', 'trigger', 'placement', 'container'],
    bind: function () {
        var $el = $(this.el),
            params = this.params;

        $el.popover({
            container: params.container || 'body',
            placement: params.placement || 'top',
            trigger: params.trigger || 'hover',
            title: params.title || '',
            content: params.content,
            html: true
        });
    },
    unbind: function () {
        $(this.el).popover('destroy');
    }
});


Vue.directive('tooltip', {
    bind: function () {
        var $el = $(this.el);

        $el.tooltip({
            container: $el.data('container') || 'body',
            placement: $el.data('placement') || 'top',
            trigger: $el.data('trigger') || 'hover'
        });
    },
    unbind: function () {
        $(this.el).tooltip('destroy');
    }
});


Vue.directive('select2', {
    twoWay: true,
    params: ['allow-clear', 'option-type', 'placeholder', 'options', 'min-input', 'tags', 'query-params'],
    bind: function () {
        var self = this,
            params = this.params,
            select2Options = {
                theme: 'bootstrap',
                    language: CRMWidgetI18n.select2Language,
                width: '100%',
                placeholder: params.placeholder !== undefined ? params.placeholder : '',
                minimumInputLength: params.minInput !== undefined ? params.minInput : 0,
                minimumResultsForSearch: 10,
                allowClear: !!params.allowClear
            };

        if (!!params.tags) {
            select2Options.tags = true;
        }

        var url = '';
        switch (params.optionType) {
            case 'deal_stage':
                url = API.dealStages;
                break;
            case 'deal_currency':
                url = API.dealCurrencies;
                break;
            case 'disabled_deal_currency':
                url = API.dealCurrencies;
                break;
            case 'tag':
                url = API.tags;
                break;
            default:
                url = API.options[params.optionType];
                break;
        }

        if (!!params.optionType) {
            select2Options.ajax = {
                type: 'GET',
                url: url,
                dataType: 'json',
                delay: 250,
                data: function (search) {
                    var query = {
                        search: search.term || ''
                    };

                    if (params.optionType === 'disabled_deal_currency') {
                        query.disabled = true;
                    }

                    if (!_.isEmpty(params.queryParams)) {
                        query = _.extend(query, params.queryParams)
                    }

                    return query;
                },
                processResults: function (res) {
                    return {
                        results: res
                    };
                }
            };
        }

        $(this.el).select2(select2Options).on('change', function (a, b) {
            self.set($(this).val());
        });
    },
    update: function (value) {
        $(this.el).val(value).trigger('change')
    },
    unbind: function () {
        var $select = $(this.el);

        if ($select.data('select2')) {
            $(this.el).select2('destroy');
        }
    }
});


Vue.directive('datepicker', {
    params: ['picker-position'],

    bind: function () {
        var params = this.params;

        $(this.el).datetimepicker({
            language: CRMWidgetI18n.datePickerLanguage,
            format: 'dd.mm.yyyy',
            weekStart: 1,
            autoclose: true,
            startView: 2,
            minView: 2,
            maxView: 3,
            pickerPosition: params.pickerPosition || 'bottom-right',
            zIndex: 1060
        });

        var $datetimepicker = $('.datetimepicker');
        $datetimepicker.find('.glyphicon-arrow-left').addClass('fa fa-arrow-left');
        $datetimepicker.find('.glyphicon-arrow-right').addClass('fa fa-arrow-right');
    },

    unbind: function () {
        $(this.el).datetimepicker('remove');
    }
});


Vue.directive('datetimepicker', {
    params: ['picker-position', 'min-view', 'fixed-time'],

    bind: function () {
        var self = this,
            params = this.params;

        $(this.el).datetimepicker({
            language: CRMWidgetI18n.datePickerLanguage,
            format: 'dd.mm.yyyy hh:ii',
            weekStart: 1,
            autoclose: true,
            startView: 2,
            minView: params.minView || 0,
            maxView: 3,
            minuteStep: 15,
            pickerPosition: params.pickerPosition || 'bottom-right',
            zIndex: 1060
        }).on('changeDate', function (event) {
            if (!!params.fixedTime) {
                setTimeout(function(){
                    var $el = $(self.el),
                        val = $el.val();

                    $el.val(val.slice(0, -5) + params.fixedTime);
                }, 100);
            }
        });

        var $datetimepicker = $('.datetimepicker');
        $datetimepicker.find('.glyphicon-arrow-left').addClass('fa fa-arrow-left');
        $datetimepicker.find('.glyphicon-arrow-right').addClass('fa fa-arrow-right');
    },

    unbind: function () {
        $(this.el).datetimepicker('remove');
    }
});


Vue.directive('timepicker', {
    params: ['picker-position'],

    bind: function () {
        var self = this,
            params = this.params;

        $(this.el).datetimepicker({
            language: CRMWidgetI18n.datePickerLanguage,
            format: 'hh:ii',
            autoclose: true,
            startView: 1,
            minView: 0,
            maxView: 1,
            minuteStep: 15,
            pickerPosition: params.pickerPosition || 'bottom-right',
            zIndex: 1060
        });

        var $datetimepicker = $('.datetimepicker');
        $datetimepicker.find('.glyphicon-arrow-left').addClass('fa fa-arrow-left');
        $datetimepicker.find('.glyphicon-arrow-right').addClass('fa fa-arrow-right');
    },

    unbind: function () {
        $(this.el).datetimepicker('remove');
    }
});


Vue.directive('daterangepicker', {
    params: ['start-date', 'end-date', 'max-date', 'allow-clear'],
    bind: function () {
        var $el = $(this.el),
            startDate = this.params.startDate || moment().subtract(29, 'days').format('DD.MM.YYYY'),
            endDate = this.params.endDate || moment().format('DD.MM.YYYY'),
            maxDate = this.params.maxDate || null,
            allowClear = this.params.allowClear,
            ranges = {};

        ranges[i18n.gettext('Yesterday')] = [moment().subtract(1, 'days'), moment().subtract(1, 'days')];
        ranges[i18n.gettext('Today')] = [moment(), moment()];
        ranges[i18n.gettext('Tomorrow')] = [moment().add(1, 'days'), moment().add(1, 'days')];
        ranges[i18n.gettext('Last 7 days')] = [moment().subtract(6, 'days'), moment()];
        ranges[i18n.gettext('Last 30 days')] = [moment().subtract(29, 'days'), moment()];
        ranges[i18n.gettext('Last 90 days')] = [moment().subtract(89, 'days'), moment()];
        ranges[i18n.gettext('This week')] = [moment().startOf('isoWeek'), moment().endOf('isoWeek')];
        ranges[i18n.gettext('Previous week')] = [moment().subtract(7, 'days').startOf('isoWeek'), moment().subtract(7, 'days').endOf('isoWeek')];
        ranges[i18n.gettext('This month')] = [moment().startOf('month'), moment().endOf('month')];
        ranges[i18n.gettext('Previous month')] = [moment().subtract(1, 'months').startOf('month'), moment().subtract(1, 'months').endOf('month')];

        $el.daterangepicker({
            locale: CRMWidgetI18n.dateRangeLocale,
            ranges: ranges,
            startDate: startDate,
            endDate: endDate,
            maxDate: maxDate,
            linkedCalendars: false,
            opens: 'left',
            buttonClasses: ['btn btn-sm'],
            applyClass: 'btn-success pull-right',
            cancelClass: 'btn-default pull-left'
        }).on('show.daterangepicker', function () {
            $el.prop('disabled', true);
        }).on('hide.daterangepicker', function () {
            $el.prop('disabled', false);
        }).on('cancel.daterangepicker', function () {
            if (allowClear) {
                $el.val('').trigger('change');
            }
        });
    },
    unbind: function () {
        $(this.el).data('daterangepicker').remove();
    }
});

Vue.directive('phone', {
    bind: function () {
        var PHONE_MASK = i18n.gettext('+7 999 999 99 99? ext. 9999999999');
        $(this.el).mask(PHONE_MASK);
    },

    unbind: function () {
        $(this.el).unmask();
    }
});
