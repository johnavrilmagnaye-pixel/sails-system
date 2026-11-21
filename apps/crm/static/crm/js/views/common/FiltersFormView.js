//(function() {
    Views.common.FiltersFormView = Vue.extend({
        template: '#filters-form-tmpl',
        replace: true,

        mixins: [Mixins.CommonMixin],
        components: {
            textEditor: Views.editors.TextEditor,
            selectEditor: Views.editors.SelectEditor,
            dateRangeEditor: Views.editors.DateRangeEditor,
            numberRangeEditor: Views.editors.NumberRangeEditor,
            listEditor: Views.editors.ListEditor
        },

        ready: function () {
            var self = this;

            this.$watch('form', function () {
                var filtersOptions = {};

                _.forOwn(self.form, function (fieldData, field) {
                    if (fieldData.editor === 'select-editor') {
                        if (!_.isEmpty(fieldData.value) && fieldData.value !== fieldData.defaultValue) {
                            var $options = $(self.$el).find('select[name="' + field + '"] option'),
                                $selectedOption = _.find($options, function ($option) {
                                    return $option.value === fieldData.value;
                                });

                            filtersOptions[field] = [{
                                id: fieldData.value,
                                text: $selectedOption.text
                            }];
                        }
                    } else if (fieldData.editor === 'number-range-editor') {
                        fieldData.value = fieldData.valueStart + ' - ' + fieldData.valueEnd;
                    }

                    self.$set('filters.' + field, fieldData.value);
                });

                Storage.save('filters', self.filters);
                Storage.save('filtersOptions', filtersOptions);
            }, {
                deep: true
            });
        },

        methods: {
            resetFilters: function () {
                var $form = $('.filters-form');

                $form.find('input, select').not('select[name="status"]').val('').trigger('change');
                $form.find('select[name="status"]').val('False').trigger('change');
            },

            initFilterExtraFields: function(form, extraFields) {
                _.each(extraFields, function(extraField) {
                    var fieldData = {
                        name: extraField.codename,
                        label: extraField.name,
                        defaultValue: '',
                        value: Storage.fetchProperty('filters', extraField.codename, ''),
                        error: ''
                    };

                    switch (extraField.type) {
                        case Const.EXTRA_FIELD_TYPES.STRING:
                            fieldData.editor = 'text-editor';
                            break;
                        case Const.EXTRA_FIELD_TYPES.TEXT:
                            fieldData.editor = 'text-editor';
                            break;
                        case Const.EXTRA_FIELD_TYPES.SELECT:
                            fieldData.editor = 'select-editor';
                            fieldData.options = extraField.options;
                            fieldData.allowClear = true;
                            break;
                        case Const.EXTRA_FIELD_TYPES.DATE:
                            fieldData.editor = 'date-range-editor';
                            fieldData.allowClear = true;
                            break;
                        case Const.EXTRA_FIELD_TYPES.DATETIME:
                            fieldData.editor = 'date-range-editor';
                            fieldData.allowClear = true;
                            break;
                        case Const.EXTRA_FIELD_TYPES.NUMBER:
                            fieldData.editor = 'number-range-editor';

                            if (!!fieldData.value) {
                                fieldData.valueStart = fieldData.value.split(' - ')[0];
                                fieldData.valueEnd = fieldData.value.split(' - ')[1];
                            } else {
                                fieldData.valueStart = '';
                                fieldData.valueEnd = '';
                            }

                            break;
                        case Const.EXTRA_FIELD_TYPES.PHONES:
                            fieldData.editor = 'text-editor';
                            break;
                        case Const.EXTRA_FIELD_TYPES.EMAILS:
                            fieldData.editor = 'text-editor';
                            fieldData.inputType = 'email';
                            fieldData.defaultValue = [''];
                            fieldData.value = [''];
                            fieldData.items = [{id: 0, value: ''}];
                            fieldData.inputType = 'email';
                            break;
                    }

                    form[extraField.codename] = fieldData;
                });
            },

            initFilterCommonFields: function (form) {
                form = _.extend(form, {
                    tags: {
                        name: 'tags',
                        label: i18n.gettext('Tags'),
                        editor: 'select-editor',
                        optionType: 'tag',
                        options: _.union(
                            [{id: '', text: ''}, {'id': 'isnull', 'text': i18n.gettext('No tags')}],
                            Storage.fetchProperty('filtersOptions', 'tags', [])
                        ),
                        allowClear: true,
                        defaultValue: '',
                        value: Storage.fetchProperty('filters', 'tags', ''),
                        error: ''
                    },
                    responsibles: {
                        name: 'responsibles',
                        label: i18n.gettext('Assignees'),
                        editor: 'select-editor',
                        optionType: 'user',
                        options: _.union(
                            [{id: '', text: ''}, {'id': 'isnull', 'text': i18n.gettext('No assignees')}],
                            Storage.fetchProperty('filtersOptions', 'responsibles', [])
                        ),
                        allowClear: true,
                        defaultValue: '',
                        value: Storage.fetchProperty('filters', 'responsibles', ''),
                        error: ''
                    },
                    user: {
                        name: 'user',
                        label: i18n.gettext('Created by'),
                        editor: 'select-editor',
                        optionType: 'user',
                        options: _.union([{id: '', text: ''}], Storage.fetchProperty('filtersOptions', 'user', [])),
                        allowClear: true,
                        defaultValue: '',
                        value: Storage.fetchProperty('filters', 'user', ''),
                        error: ''
                    },
                    created_at: {
                        name: 'created_at',
                        label: i18n.gettext('Date created'),
                        editor: 'date-range-editor',
                        maxDate: moment(),
                        allowClear: true,
                        defaultValue: '',
                        value: Storage.fetchProperty('filters', 'created_at', ''),
                        error: ''
                    }
                });
            }
        }

    });

//})();
